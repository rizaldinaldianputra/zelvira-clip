import os
import json
import asyncio
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.storage import storage
from app.core.rate_limit import validate_video_url, validate_video_file_extension
from app.models.user import User
from app.models.job import Job
from app.models.clip import Clip
from app.models.usage import UsageLog
from app.schemas.job import JobResponse, JobDetailResponse, JobSettings, JobCreate
from app.schemas.clip import ClipResponse
from app.tasks.orchestrator import run_pipeline

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    source_url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    clip_count: int = Form(5),
    target_duration: int = Form(60),
    layout: str = Form("focus"),
    custom_header_text: Optional[str] = Form(None),
    subtitle_preset: str = Form("bold_yellow"),
    language: str = Form("auto"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Check user parallel running jobs limit
    stmt_active = select(func.count(Job.id)).where(
        and_(
            Job.user_id == current_user.id,
            Job.status.in_(["queued", "downloading", "transcribing", "analyzing", "rendering"])
        )
    )
    active_count = (await db.execute(stmt_active)).scalar() or 0
    if active_count >= settings.MAX_PARALLEL_JOBS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"You already have {active_count} active jobs. Maximum allowed parallel jobs is {settings.MAX_PARALLEL_JOBS_PER_USER}."
        )

    # 2. Determine source type and validate
    if file and file.filename:
        validate_video_file_extension(file.filename)
        source_type = "upload"
        clean_url = None
    elif source_url:
        clean_url = validate_video_url(source_url)
        source_type = "tiktok" if "tiktok.com" in clean_url else "youtube"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either a valid YouTube/TikTok source_url or an uploaded video file must be provided."
        )

    job_settings = {
        "clip_count": clip_count,
        "target_duration": target_duration,
        "layout": layout if layout in ("focus", "split", "header_banner") else "focus",
        "custom_header_text": custom_header_text,
        "subtitle_preset": subtitle_preset if subtitle_preset in ("bold_yellow", "classic", "neon") else "bold_yellow",
        "language": language
    }

    # 3. Create Job database record
    new_job = Job(
        user_id=current_user.id,
        source_type=source_type,
        source_url=clean_url,
        title="Processing video...",
        status="queued",
        progress=0,
        settings=job_settings
    )
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)

    # 4. If uploaded file, save it to job directory
    if source_type == "upload" and file:
        job_dir = Path(storage.get_full_path(f"jobs/{new_job.id}"))
        job_dir.mkdir(parents=True, exist_ok=True)
        dest_path = job_dir / "uploaded_input"

        # Read in chunks to enforce MAX_FILE_SIZE_MB
        total_size = 0
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        with open(dest_path, "wb") as f_out:
            while chunk := await file.read(1024 * 1024): # 1MB chunk
                total_size += len(chunk)
                if total_size > max_bytes:
                    dest_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB."
                    )
                f_out.write(chunk)

    # 5. Dispatch Celery task
    run_pipeline.delay(new_job.id)

    return new_job

@router.get("", response_model=List[JobResponse])
async def list_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Job).where(Job.user_id == current_user.id).order_by(Job.created_at.desc())
    jobs = (await db.execute(stmt)).scalars().all()
    return jobs

@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Job).where(and_(Job.id == job_id, Job.user_id == current_user.id))
    job = (await db.execute(stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Load clips
    stmt_clips = select(Clip).where(Clip.job_id == job_id).order_by(Clip.score.desc())
    clips = (await db.execute(stmt_clips)).scalars().all()

    # Calculate token usage and cost summary
    stmt_usage = select(
        func.sum(UsageLog.tokens_in + UsageLog.tokens_out),
        func.sum(UsageLog.cost_usd)
    ).where(UsageLog.job_id == job_id)
    usage_res = (await db.execute(stmt_usage)).first()
    total_tokens = usage_res[0] or 0 if usage_res else 0
    total_cost = usage_res[1] or 0.0 if usage_res else 0.0

    # Load transcript preview & step history from job storage directory
    transcript_preview = None
    step_history = []
    job_dir = Path(storage.get_full_path(f"jobs/{job_id}"))

    # Check transcript
    transcript_file = job_dir / "transcript.json"
    if transcript_file.exists():
        try:
            with open(transcript_file, "r", encoding="utf-8") as f:
                tdata = json.load(f)
                segs = tdata.get("segments", [])
                lines = [f"[{int(s.get('start', 0)//60):02d}:{int(s.get('start', 0)%60):02d}] {s.get('text', '')}" for s in segs[:30]]
                transcript_preview = "\n".join(lines)
                if len(segs) > 30:
                    transcript_preview += f"\n... dan {len(segs)-30} segmen lainnya."
        except Exception:
            pass

    # Build step history
    steps_order = [
        ("ingest", "Unduh & Ingest Video", job_dir / "raw.mp4"),
        ("transcribe", "Transkripsi Audio (faster-whisper)", job_dir / "transcript.json"),
        ("chunk", "Pemecahan Chunk Transkrip", job_dir / "chunks.json"),
        ("find_moments", "Pencarian Momen Viral (AI)", job_dir / "candidates.json"),
        ("rank", "Perankingan Klip Terbaik", job_dir / "ranked_moments.json"),
        ("refine_boundary", "Penyelarasan Batas Kalimat", job_dir / "refined_clips.json"),
        ("cut", "Pemotongan Video (FFmpeg)", job_dir / "cut_clips.json"),
        ("reframe", "Reframe 9:16 & Pelacakan Wajah", job_dir / "reframed_clips.json"),
        ("subtitle", "Bakar Subtitle TikTok", job_dir / "subtitled_clips.json"),
        ("metadata", "Pembuatan Judul & Metadata", job_dir / "clips"),
    ]

    for step_code, step_name, artifact_path in steps_order:
        is_success = artifact_path.exists()
        is_failed = job.failed_step == step_code and job.status == "failed"
        
        status_str = "success" if is_success else ("failed" if is_failed else "pending")
        step_history.append({
            "step": step_code,
            "name": step_name,
            "status": status_str,
            "message": job.error if is_failed else ("Selesai" if is_success else "Belum diproses")
        })

    return JobDetailResponse(
        id=job.id,
        user_id=job.user_id,
        source_type=job.source_type,
        source_url=job.source_url,
        title=job.title,
        duration_sec=job.duration_sec,
        status=job.status,
        progress=job.progress,
        error=job.error,
        failed_step=job.failed_step,
        settings=job.settings,
        created_at=job.created_at,
        updated_at=job.updated_at,
        clips=[ClipResponse.model_validate(c) for c in clips],
        total_tokens=total_tokens,
        estimated_cost_usd=round(total_cost, 5),
        transcript_preview=transcript_preview,
        step_history=step_history
    )

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Job).where(and_(Job.id == job_id, Job.user_id == current_user.id))
    job = (await db.execute(stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Delete storage directory for this job
    storage.delete_directory(f"jobs/{job_id}")

    await db.delete(job)
    await db.commit()
    return None

@router.post("/{job_id}/retry", response_model=JobResponse)
async def retry_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Job).where(and_(Job.id == job_id, Job.user_id == current_user.id))
    job = (await db.execute(stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.status not in ("failed", "done"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only failed or completed jobs can be retried.")

    resume_from_step = job.failed_step or "ingest"
    job.status = "queued"
    job.error = None
    await db.commit()
    await db.refresh(job)

    # Dispatch Celery pipeline resuming from failed_step
    run_pipeline.delay(job.id, from_step=resume_from_step)
    return job

@router.get("/{job_id}/clips", response_model=List[ClipResponse])
async def list_job_clips(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt_job = select(Job).where(and_(Job.id == job_id, Job.user_id == current_user.id))
    job = (await db.execute(stmt_job)).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    stmt_clips = select(Clip).where(Clip.job_id == job_id).order_by(Clip.score.desc())
    clips = (await db.execute(stmt_clips)).scalars().all()
    return clips

@router.get("/{job_id}/events")
async def job_events_stream(
    job_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Server-Sent Events (SSE) streaming real-time job progress events.
    """
    async def event_generator():
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        pubsub = r.pubsub()
        await pubsub.subscribe(f"job_events:{job_id}")

        # Send initial cached event if available
        cached = await r.get(f"job_latest:{job_id}")
        if cached:
            yield f"data: {cached}\n\n"

        try:
            while True:
                msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if msg and msg.get("type") == "message":
                    data = msg.get("data")
                    yield f"data: {data}\n\n"
                    # Check if done or failed to gracefully close stream
                    try:
                        parsed = json.loads(data)
                        if parsed.get("status") in ("done", "failed"):
                            break
                    except Exception:
                        pass
                await asyncio.sleep(0.5)
        finally:
            await pubsub.unsubscribe(f"job_events:{job_id}")
            await r.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")
