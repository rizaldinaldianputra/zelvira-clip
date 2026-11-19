import os
import json
import subprocess
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
import yt_dlp
from app.agents.base import BaseAgent
from app.core.config import settings
from app.core.logging import logger
from app.core.storage import storage

class IngestOutput(BaseModel):
    job_id: str
    video_path: str
    title: str
    duration_sec: float
    source_type: str

class IngestAgent(BaseAgent):
    def __init__(self):
        super().__init__("ingest")

    def run(
        self,
        job_id: str,
        source_type: str,
        source_url: Optional[str] = None,
        uploaded_file_path: Optional[str] = None
    ) -> IngestOutput:
        job_dir = Path(storage.get_full_path(f"jobs/{job_id}"))
        job_dir.mkdir(parents=True, exist_ok=True)
        target_video_path = str(job_dir / "raw.mp4")

        if source_type in ("youtube", "tiktok"):
            if not source_url:
                raise ValueError("source_url is required for YouTube/TikTok jobs")
            return self._download_from_url(job_id, source_url, source_type, target_video_path)
        elif source_type == "upload":
            if not uploaded_file_path or not os.path.exists(uploaded_file_path):
                raise ValueError("Uploaded video file not found")
            return self._process_uploaded_file(job_id, uploaded_file_path, target_video_path)
        else:
            raise ValueError(f"Unsupported source_type: {source_type}")

    def _download_from_url(
        self,
        job_id: str,
        url: str,
        source_type: str,
        output_path: str
    ) -> IngestOutput:
        logger.info(f"[{job_id}] Ingesting video from {source_type}: {url}")

        # yt-dlp configuration with aggressive retry and chunk streaming protection
        ydl_opts = {
            "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]/best",
            "outtmpl": output_path,
            "quiet": True,
            "no_warnings": True,
            "merge_output_format": "mp4",
            "overwrites": True,
            "retries": 10,
            "fragment_retries": 10,
            "file_access_retries": 5,
            "retry_sleep_functions": {"http": lambda n: 2 * n, "fragment": lambda n: 2 * n},
            "http_chunk_size": 10485760,  # 10MB chunking to prevent TCP stream dropping prematurely
            "buffersize": 1024 * 64,
            "socket_timeout": 60,
        }

        # Step 1: Extract info first without downloading to check metadata and limits
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except yt_dlp.utils.DownloadError as e:
                err_msg = str(e)
                if "Private video" in err_msg:
                    raise ValueError("Video is private and cannot be accessed.") from None
                elif "not available in your country" in err_msg or "blocked" in err_msg:
                    raise ValueError("Video is region-locked or unavailable.") from None
                elif "is a live stream" in err_msg or info.get("is_live", False) if 'info' in locals() and info else False:
                    raise ValueError("Live streams currently in progress cannot be clipped. Please wait until stream ends.") from None
                else:
                    raise ValueError(f"Failed to fetch video: {err_msg}") from None

            if not info:
                raise ValueError("Could not extract video metadata.")

            if info.get("is_live", False):
                raise ValueError("Live streams currently in progress cannot be clipped.")

            duration = info.get("duration", 0)
            title = info.get("title", "Untitled Video")
            max_sec = settings.MAX_VIDEO_MINUTES * 60

            if duration and duration > max_sec:
                raise ValueError(
                    f"Video duration ({duration // 60}m) exceeds the maximum allowed limit of {settings.MAX_VIDEO_MINUTES} minutes."
                )

        # Step 2: Download video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if not os.path.exists(output_path):
            # yt-dlp might have written raw.mp4.mp4 or similar if format differed
            possible_files = list(Path(output_path).parent.glob("raw.*"))
            if possible_files:
                output_path = str(possible_files[0])
            else:
                raise RuntimeError("Video download finished but output file was not found.")

        # Probe actual downloaded duration if yt-dlp duration was missing
        if not duration:
            duration = self._probe_duration(output_path)

        return IngestOutput(
            job_id=job_id,
            video_path=output_path,
            title=title,
            duration_sec=float(duration),
            source_type=source_type
        )

    def _process_uploaded_file(
        self,
        job_id: str,
        uploaded_path: str,
        target_path: str
    ) -> IngestOutput:
        logger.info(f"[{job_id}] Processing uploaded video: {uploaded_path}")
        
        # Move or copy uploaded file to target_path
        if uploaded_path != target_path:
            import shutil
            shutil.copy2(uploaded_path, target_path)

        duration = self._probe_duration(target_path)
        max_sec = settings.MAX_VIDEO_MINUTES * 60
        if duration > max_sec:
            raise ValueError(
                f"Uploaded video ({int(duration // 60)}m) exceeds maximum limit of {settings.MAX_VIDEO_MINUTES} minutes."
            )

        title = Path(uploaded_path).stem

        return IngestOutput(
            job_id=job_id,
            video_path=target_path,
            title=title,
            duration_sec=float(duration),
            source_type="upload"
        )

    def _probe_duration(self, file_path: str) -> float:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return float(res.stdout.strip())
        except Exception as e:
            logger.warning(f"Could not probe duration with ffprobe: {e}")
            return 0.0
