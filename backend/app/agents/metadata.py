import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.agents.base import BaseAgent
from app.schemas.agent import RefinedClip, TranscriptData, ClipMetadataOutput
from app.core.llm import call_llm
from app.core.logging import logger

PROMPT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "metadata.md"

class MetadataAgent(BaseAgent):
    def __init__(self):
        super().__init__("metadata")
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read()

    def _extract_thumbnail(self, video_path: str, thumbnail_path: str) -> None:
        cmd = [
            "ffmpeg", "-y",
            "-ss", "0.5",
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            thumbnail_path
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except Exception as e:
            logger.warning(f"Thumbnail extraction failed for {video_path}: {e}")

    def run(
        self,
        job_id: str,
        clip_paths: List[str],
        refined_clips: List[RefinedClip],
        transcript: TranscriptData,
        user_key: str,
        model: str,
        provider: str,
        base_url: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        results: List[Dict[str, Any]] = []
        all_usages: List[Dict[str, Any]] = []

        for idx, (v_path, clip_meta) in enumerate(zip(clip_paths, refined_clips)):
            thumb_path = v_path.replace(".mp4", "_thumb.jpg")
            self._extract_thumbnail(v_path, thumb_path)

            # Get text for this clip
            clip_text_segments = [
                seg.text for seg in transcript.segments
                if seg.start >= clip_meta.refined_start and seg.end <= clip_meta.refined_end
            ]
            clip_text = " ".join(clip_text_segments) if clip_text_segments else clip_meta.hook

            prompt = self.prompt_template.format(
                clip_transcript=clip_text,
                language=transcript.language
            )

            messages = [
                {"role": "system", "content": "You are a professional social media metadata generator. Output strictly valid JSON."},
                {"role": "user", "content": prompt}
            ]

            meta_data = {
                "title": clip_meta.hook[:60],
                "caption": f"{clip_meta.hook} - {clip_meta.reason}",
                "hashtags": ["#viral", "#streamer", "#clip", "#shorts", "#fyp"],
                "thumbnail_path": thumb_path
            }

            try:
                output, metrics = call_llm(
                    user_key=user_key,
                    model=model,
                    messages=messages,
                    provider=provider,
                    base_url=base_url,
                    json_mode=True
                )
                all_usages.append({
                    "agent_name": self.name,
                    "model": metrics.get("model_used", model),
                    "tokens_in": metrics.get("tokens_in", 0),
                    "tokens_out": metrics.get("tokens_out", 0),
                    "cost_usd": metrics.get("cost_usd", 0.0),
                    "latency_ms": metrics.get("latency_ms", 0),
                    "job_id": job_id
                })

                if isinstance(output, str):
                    output = json.loads(output)

                validated = ClipMetadataOutput.model_validate(output)
                meta_data["title"] = validated.title[:60]
                meta_data["caption"] = validated.caption
                meta_data["hashtags"] = validated.hashtags[:5]

            except Exception as e:
                logger.warning(f"MetadataAgent LLM call failed for clip #{idx}: {e}. Using fallback metadata.")

            results.append(meta_data)

        return results, all_usages
