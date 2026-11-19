import os
import subprocess
from pathlib import Path
from typing import List
from app.agents.base import BaseAgent
from app.schemas.agent import RefinedClip
from app.core.logging import logger
from app.core.storage import storage

class ClipCutterAgent(BaseAgent):
    def __init__(self):
        super().__init__("clip_cutter")

    def run(
        self,
        job_id: str,
        source_video_path: str,
        clips: List[RefinedClip]
    ) -> List[str]:
        clips_dir = Path(storage.get_full_path(f"jobs/{job_id}/clips"))
        clips_dir.mkdir(parents=True, exist_ok=True)

        cut_paths: List[str] = []

        for idx, clip in enumerate(clips):
            output_file = str(clips_dir / f"clip_{idx}_raw.mp4")
            duration = clip.refined_end - clip.refined_start

            logger.info(f"[{job_id}] Cutting clip #{idx}: [{clip.refined_start:.2f}s -> {clip.refined_end:.2f}s] ({duration:.2f}s)...")

            # Accurate re-encode with fast seek
            # Placing -ss before -i with accurate fast re-encoding ensures keyframe accuracy
            cmd = [
                "ffmpeg", "-y",
                "-ss", str(clip.refined_start),
                "-to", str(clip.refined_end),
                "-i", source_video_path,
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "22",
                "-c:a", "aac",
                "-b:a", "128k",
                "-avoid_negative_ts", "make_zero",
                output_file
            ]

            try:
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                cut_paths.append(output_file)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed cutting clip #{idx}: {e.stderr.decode('utf-8', errors='ignore')}")
                raise RuntimeError(f"FFmpeg cutting failed for clip #{idx}") from None

        return cut_paths
