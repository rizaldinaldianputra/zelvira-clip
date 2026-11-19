import time
import re
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from app.core.config import settings

# Simple token-bucket or sliding window rate limiter per client IP
_rate_limits: Dict[str, list[float]] = {}

def check_rate_limit(request: Request, max_requests: int = 10, window_seconds: int = 60):
    """
    In-memory rate limiter per IP address.
    """
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    
    # Clean old requests
    timestamps = _rate_limits.get(client_ip, [])
    valid_timestamps = [ts for ts in timestamps if now - ts < window_seconds]
    
    if len(valid_timestamps) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {max_requests} requests per {window_seconds} seconds."
        )
    
    valid_timestamps.append(now)
    _rate_limits[client_ip] = valid_timestamps

# Input validation helpers
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm"}
YOUTUBE_TIKTOK_REGEX = re.compile(
    r"^(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/|tiktok\.com/@[\w.-]+/video/\d+|vm\.tiktok\.com/[\w]+)",
    re.IGNORECASE
)

def validate_video_url(url: str) -> str:
    clean_url = url.strip()
    if not clean_url:
        raise ValueError("URL cannot be empty")
    if not (
        "youtube.com" in clean_url or
        "youtu.be" in clean_url or
        "tiktok.com" in clean_url
    ):
        raise ValueError("Only YouTube (youtube.com, youtu.be) and TikTok (tiktok.com) URLs are supported.")
    return clean_url

def validate_video_file_extension(filename: str) -> None:
    import os
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise ValueError(f"Invalid file extension '{ext}'. Allowed extensions: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}")
