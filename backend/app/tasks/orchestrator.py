import os
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import redis
from celery import shared_task
from app.core.celery_app import celery_app
from app.core.config import settings
from app.core.logging import logger
from app.core.database import get_sync_db
from app.core.crypto import decrypt_api_key
from app.core.storage import storage
from app.models.job import Job
from app.models.clip import Clip
from app.models.key import UserAIKey, UserAgentModel
from app.models.usage import UsageLog
from app.agents.ingest import IngestAgent, IngestOutput
from app.agents.transcribe import TranscribeAgent
from app.agents.chunker import ChunkerAgent
from app.agents.moment_finder import MomentFinderAgent
from app.agents.ranker import RankerAgent
from app.agents.boundary_refiner import BoundaryRefinerAgent
from app.agents.clip_cutter import ClipCutterAgent
from app.agents.reframe import ReframeAgent
from app.agents.subtitle import SubtitleAgent
from app.agents.metadata import MetadataAgent
from app.schemas.agent import (
    TranscriptData,
    TranscriptChunk,
    MomentCandidate,
    RefinedClip,
)

# Redis client for publishing SSE events
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

def publish_event(job_id: str, status: str, progress: int, message: str, error: Optional[str] = None):
    event_data = {
        "job_id": job_id,
        "status": status,
        "progress": progress,
        "message": message,
        "error": error,
        "timestamp": time.time()
    }
    try:
        redis_client.publish(f"job_events:{job_id}", json.dumps(event_data))
        # Also cache the latest event for 1 hour
        redis_client.set(f"job_latest:{job_id}", json.dumps(event_data), ex=3600)
    except Exception as e:
        logger.warning(f"Could not publish Redis event for job {job_id}: {e}")

def update_job_status(db, job_id: str, status: str, progress: int, error: Optional[str] = None, failed_step: Optional[str] = None):
    job = db.query(Job).filter(Job.id == job_id).first()
    if job:
        job.status = status
        job.progress = progress
        if error is not None:
            job.error = error
        if failed_step is not None:
            job.failed_step = failed_step
        db.commit()
    publish_event(job_id, status, progress, f"Job {status}: {progress}%", error)

def get_agent_config(db, user_id: str, agent_name: str) -> tuple[Optional[str], str, str, Optional[str]]:
    """
    Returns (decrypted_api_key, model, provider, base_url) for a specific agent.
    Falls back to user's first available key if specific agent model is not configured.
    """
    agent_setting = db.query(UserAgentModel).filter(
        UserAgentModel.user_id == user_id,
        UserAgentModel.agent_name == agent_name
    ).first()

    key_record = None
    model_name = "gpt-4o-mini" # Default fallback model

    if agent_setting:
        model_name = agent_setting.model
        if agent_setting.key_id:
            key_record = db.query(UserAIKey).filter(UserAIKey.id == agent_setting.key_id).first()

    if not key_record:
        # Fallback to any saved key for the user
        key_record = db.query(UserAIKey).filter(UserAIKey.user_id == user_id).first()

    if not key_record:
        return None, model_name, "openai", None

    decrypted_key = decrypt_api_key(key_record.encrypted_key)
    return decrypted_key, model_name, key_record.provider, key_record.base_url

@celery_app.task(name="app.tasks.orchestrator.run_pipeline", bind=True)
def run_pipeline(self, job_id: str, from_step: Optional[str] = None):
    logger.info(f"[{job_id}] Starting pipeline execution (from_step: {from_step or 'start'})...")
    
    with get_sync_db() as db:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found in database.")
            return

        user_id = job.user_id
        job_settings = job.settings or {}
        job_dir = Path(storage.get_full_path(f"jobs/{job_id}"))
        job_dir.mkdir(parents=True, exist_ok=True)

        current_step = from_step or "ingest"

        try:
            # -------------------------------------------------------------
            # STEP 1: INGEST (Download / Process Upload)
            # -------------------------------------------------------------
            raw_video_path = str(job_dir / "raw.mp4")
            ingest_meta_path = str(job_dir / "ingest_meta.json")

            if current_step == "ingest" or not os.path.exists(raw_video_path):
                current_step = "ingest"
                update_job_status(db, job_id, "downloading", 10)
                
                ingest_agent = IngestAgent()
                upload_file = str(job_dir / "uploaded_input") if job.source_type == "upload" else None
                ingest_out = ingest_agent.run(
                    job_id=job_id,
                    source_type=job.source_type,
                    source_url=job.source_url,
                    uploaded_file_path=upload_file
                )
                
                job.title = ingest_out.title
                job.duration_sec = ingest_out.duration_sec
                db.commit()

                with open(ingest_meta_path, "w", encoding="utf-8") as f:
                    json.dump(ingest_out.model_dump(), f)
            else:
                with open(ingest_meta_path, "r", encoding="utf-8") as f:
                    ingest_meta = json.load(f)
                    job.duration_sec = ingest_meta.get("duration_sec", job.duration_sec)

            # -------------------------------------------------------------
            # STEP 2: TRANSCRIBE
            # -------------------------------------------------------------
            transcript_json_path = str(job_dir / "transcript.json")
            if current_step in ("ingest", "transcribe") or not os.path.exists(transcript_json_path):
                current_step = "transcribe"
                update_job_status(db, job_id, "transcribing", 25)

                transcribe_agent = TranscribeAgent()
                lang_pref = job_settings.get("language", "auto")
                transcript_data = transcribe_agent.run(job_id, raw_video_path, language_hint=lang_pref)
            else:
                with open(transcript_json_path, "r", encoding="utf-8") as f:
                    transcript_data = TranscriptData.model_validate(json.load(f))

            # -------------------------------------------------------------
            # STEP 3: CHUNKER
            # -------------------------------------------------------------
            chunks_json_path = str(job_dir / "chunks.json")
            if current_step in ("ingest", "transcribe", "chunk") or not os.path.exists(chunks_json_path):
                current_step = "chunk"
                update_job_status(db, job_id, "analyzing", 40)

                chunker_agent = ChunkerAgent(target_chunk_sec=480.0, overlap_sec=30.0)
                chunks = chunker_agent.run(transcript_data)
                with open(chunks_json_path, "w", encoding="utf-8") as f:
                    json.dump([c.model_dump() for c in chunks], f)
            else:
                with open(chunks_json_path, "r", encoding="utf-8") as f:
                    chunks = [TranscriptChunk.model_validate(c) for c in json.load(f)]

            # -------------------------------------------------------------
            # STEP 4: MOMENT FINDER (LLM)
            # -------------------------------------------------------------
            candidates_json_path = str(job_dir / "candidates.json")
            if current_step in ("ingest", "transcribe", "chunk", "find_moments") or not os.path.exists(candidates_json_path):
                current_step = "find_moments"
                update_job_status(db, job_id, "analyzing", 50)

                key, model, provider, base_url = get_agent_config(db, user_id, "moment_finder")
                if not key:
                    raise ValueError("No AI API key found. Please configure an API key in AI Settings before running jobs.")

                finder_agent = MomentFinderAgent()
                target_dur = job_settings.get("target_duration", 60)
                candidates, usages = finder_agent.run(
                    chunks=chunks,
                    target_duration=target_dur,
                    user_key=key,
                    model=model,
                    provider=provider,
                    base_url=base_url,
                    job_id=job_id
                )
                
                # Record usages
                for u in usages:
                    db.add(UsageLog(**u))
                db.commit()

                with open(candidates_json_path, "w", encoding="utf-8") as f:
                    json.dump([c.model_dump() for c in candidates], f)
            else:
                with open(candidates_json_path, "r", encoding="utf-8") as f:
                    candidates = [MomentCandidate.model_validate(c) for c in json.load(f)]

            if not candidates:
                raise ValueError("AI could not detect any engaging highlight moments from this video.")

            # -------------------------------------------------------------
            # STEP 5: RANKER (LLM)
            # -------------------------------------------------------------
            ranked_json_path = str(job_dir / "ranked_moments.json")
            if current_step in ("ingest", "transcribe", "chunk", "find_moments", "rank") or not os.path.exists(ranked_json_path):
                current_step = "rank"
                update_job_status(db, job_id, "analyzing", 65)

                key, model, provider, base_url = get_agent_config(db, user_id, "ranker")
                ranker_agent = RankerAgent()
                desired_count = job_settings.get("clip_count", 5)

                ranked_moments, ranker_usages = ranker_agent.run(
                    candidates=candidates,
                    top_n=desired_count,
                    user_key=key,
                    model=model,
                    provider=provider,
                    base_url=base_url,
                    job_id=job_id
                )

                for u in ranker_usages:
                    db.add(UsageLog(**u))
                db.commit()

                with open(ranked_json_path, "w", encoding="utf-8") as f:
                    json.dump([m.model_dump() for m in ranked_moments], f)
            else:
                with open(ranked_json_path, "r", encoding="utf-8") as f:
                    ranked_moments = [MomentCandidate.model_validate(m) for m in json.load(f)]

            # -------------------------------------------------------------
            # STEP 6: BOUNDARY REFINER
            # -------------------------------------------------------------
            refined_json_path = str(job_dir / "refined_clips.json")
            if current_step in ("ingest", "transcribe", "chunk", "find_moments", "rank", "refine_boundary") or not os.path.exists(refined_json_path):
                current_step = "refine_boundary"
                update_job_status(db, job_id, "analyzing", 72)

                refiner_agent = BoundaryRefinerAgent()
                refined_clips = refiner_agent.run(
                    moments=ranked_moments,
                    transcript=transcript_data,
                    video_duration=job.duration_sec or 0.0
                )
                with open(refined_json_path, "w", encoding="utf-8") as f:
                    json.dump([r.model_dump() for r in refined_clips], f)
            else:
                with open(refined_json_path, "r", encoding="utf-8") as f:
                    refined_clips = [RefinedClip.model_validate(r) for r in json.load(f)]

            # -------------------------------------------------------------
            # STEP 7: CLIP CUTTER (Accurate re-encode)
            # -------------------------------------------------------------
            cut_clips_json_path = str(job_dir / "cut_clips.json")
            if current_step in ("ingest", "transcribe", "chunk", "find_moments", "rank", "refine_boundary", "cut") or not os.path.exists(cut_clips_json_path):
                current_step = "cut"
                update_job_status(db, job_id, "rendering", 78)

                cutter_agent = ClipCutterAgent()
                cut_paths = cutter_agent.run(job_id, raw_video_path, refined_clips)
                with open(cut_clips_json_path, "w", encoding="utf-8") as f:
                    json.dump(cut_paths, f)
            else:
                with open(cut_clips_json_path, "r", encoding="utf-8") as f:
                    cut_paths = json.load(f)

            # -------------------------------------------------------------
            # STEP 8: REFRAME (9:16 MediaPipe face tracking)
            # -------------------------------------------------------------
            reframed_json_path = str(job_dir / "reframed_clips.json")
            if current_step in ("ingest", "transcribe", "chunk", "find_moments", "rank", "refine_boundary", "cut", "reframe") or not os.path.exists(reframed_json_path):
                current_step = "reframe"
                update_job_status(db, job_id, "rendering", 85)

                layout = job_settings.get("layout", "focus")
                custom_header = job_settings.get("custom_header_text")
                reframe_agent = ReframeAgent()
                reframed_paths = reframe_agent.run(job_id, cut_paths, layout=layout, banner_text=custom_header)
                with open(reframed_json_path, "w", encoding="utf-8") as f:
                    json.dump(reframed_paths, f)
            else:
                with open(reframed_json_path, "r", encoding="utf-8") as f:
                    reframed_paths = json.load(f)

            # -------------------------------------------------------------
            # STEP 9: SUBTITLE (ASS TikTok style highlight)
            # -------------------------------------------------------------
            subtitled_json_path = str(job_dir / "subtitled_clips.json")
            if current_step in ("ingest", "transcribe", "chunk", "find_moments", "rank", "refine_boundary", "cut", "reframe", "subtitle") or not os.path.exists(subtitled_json_path):
                current_step = "subtitle"
                update_job_status(db, job_id, "rendering", 92)

                preset = job_settings.get("subtitle_preset", "bold_yellow")
                subtitle_agent = SubtitleAgent()
                subtitled_paths = subtitle_agent.run(
                    job_id=job_id,
                    reframed_paths=reframed_paths,
                    refined_clips=refined_clips,
                    transcript=transcript_data,
                    preset=preset
                )
                with open(subtitled_json_path, "w", encoding="utf-8") as f:
                    json.dump(subtitled_paths, f)
            else:
                with open(subtitled_json_path, "r", encoding="utf-8") as f:
                    subtitled_paths = json.load(f)

            # -------------------------------------------------------------
            # STEP 10: METADATA & THUMBNAILS (LLM)
            # -------------------------------------------------------------
            current_step = "metadata"
            update_job_status(db, job_id, "rendering", 96)

            key, model, provider, base_url = get_agent_config(db, user_id, "metadata")
            meta_agent = MetadataAgent()
            clip_metas, meta_usages = meta_agent.run(
                job_id=job_id,
                clip_paths=subtitled_paths,
                refined_clips=refined_clips,
                transcript=transcript_data,
                user_key=key,
                model=model,
                provider=provider,
                base_url=base_url
            )

            for u in meta_usages:
                db.add(UsageLog(**u))

            # -------------------------------------------------------------
            # STEP 11: SAVE CLIPS TO DATABASE & DELIVERY
            # -------------------------------------------------------------
            current_step = "delivery"
            
            # Clear any previously existing clips for this job (e.g. if retried)
            db.query(Clip).filter(Clip.job_id == job_id).delete()

            for idx, (sub_path, r_clip, meta) in enumerate(zip(subtitled_paths, refined_clips, clip_metas)):
                # Relative paths for storage
                rel_video = f"jobs/{job_id}/clips/" + Path(sub_path).name
                rel_thumb = f"jobs/{job_id}/clips/" + Path(meta["thumbnail_path"]).name

                clip_row = Clip(
                    job_id=job_id,
                    start_sec=r_clip.refined_start,
                    end_sec=r_clip.refined_end,
                    score=r_clip.score,
                    category=r_clip.category,
                    hook=r_clip.hook,
                    reason=r_clip.reason,
                    title=meta.get("title", f"Clip #{idx+1}"),
                    caption=meta.get("caption", ""),
                    hashtags=meta.get("hashtags", []),
                    file_path=rel_video,
                    thumbnail_path=rel_thumb
                )
                db.add(clip_row)

            # Cleanup temporary audio files to save disk space
            temp_audio = job_dir / "audio.wav"
            if temp_audio.exists():
                try:
                    temp_audio.unlink()
                except Exception:
                    pass

            update_job_status(db, job_id, "done", 100, error=None, failed_step=None)
            logger.info(f"[{job_id}] Pipeline completed successfully. {len(subtitled_paths)} clips ready.")

        except Exception as exc:
            error_msg = str(exc)
            logger.error(f"[{job_id}] Pipeline failed at step '{current_step}': {error_msg}")
            update_job_status(db, job_id, "failed", job.progress, error=error_msg, failed_step=current_step)
            raise exc
