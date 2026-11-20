import os
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.storage import storage
from app.models.user import User
from app.models.clip import Clip
from app.models.job import Job

router = APIRouter(prefix="/clips", tags=["Clips"])

@router.get("/{clip_id}/download")
async def download_clip(
    clip_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Clip)
        .join(Job, Clip.job_id == Job.id)
        .where(and_(Clip.id == clip_id, Job.user_id == current_user.id))
    )
    clip = (await db.execute(stmt)).scalar_one_or_none()
    if not clip or not clip.file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found")

    full_path = storage.get_full_path(clip.file_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video file not found on server")

    filename = f"{clip.title or 'clip'}_{clip_id[:8]}.mp4"
    # Clean filename of unsafe characters
    safe_filename = "".join(c for c in filename if c.isalnum() or c in ("-", "_", ".")).strip()

    return FileResponse(
        path=full_path,
        media_type="video/mp4",
        filename=safe_filename,
        headers={"Content-Disposition": f'attachment; filename="{safe_filename}"'}
    )

@router.get("/{clip_id}/stream")
async def stream_clip(
    clip_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Clip)
        .join(Job, Clip.job_id == Job.id)
        .where(and_(Clip.id == clip_id, Job.user_id == current_user.id))
    )
    clip = (await db.execute(stmt)).scalar_one_or_none()
    if not clip or not clip.file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found")

    full_path = storage.get_full_path(clip.file_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video file not found on server")

    return FileResponse(path=full_path, media_type="video/mp4")

@router.get("/{clip_id}/thumbnail")
async def get_clip_thumbnail(
    clip_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Clip)
        .join(Job, Clip.job_id == Job.id)
        .where(and_(Clip.id == clip_id, Job.user_id == current_user.id))
    )
    clip = (await db.execute(stmt)).scalar_one_or_none()
    if not clip or not clip.thumbnail_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thumbnail not found")

    full_path = storage.get_full_path(clip.thumbnail_path)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thumbnail file not found")

    return FileResponse(path=full_path, media_type="image/jpeg")

from pydantic import BaseModel
from app.agents.clip_cutter import ClipCutterAgent
from app.agents.reframe import ReframeAgent
from app.agents.subtitle import SubtitleAgent
from app.schemas.agent import RefinedClip, TranscriptData
from app.schemas.clip import ClipResponse
import json
import uuid

class ManualClipCreate(BaseModel):
    start_sec: float
    end_sec: float
    title: Optional[str] = "Manual Clip"
    layout: Optional[str] = "focus"
    custom_header_text: Optional[str] = None
    subtitle_preset: Optional[str] = "bold_yellow"
    font_size: Optional[int] = 48
    font_family: Optional[str] = "Arial"
    font_color: Optional[str] = None

@router.post("/jobs/{job_id}/manual", response_model=ClipResponse, status_code=status.HTTP_201_CREATED)
async def create_manual_clip(
    job_id: str,
    payload: ManualClipCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Job).where(and_(Job.id == job_id, Job.user_id == current_user.id))
    job = (await db.execute(stmt)).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    job_dir = Path(storage.get_full_path(f"jobs/{job_id}"))
    raw_video = job_dir / "raw.mp4"
    if not raw_video.exists():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Raw video file not available for this job")

    if payload.end_sec <= payload.start_sec:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="end_sec must be greater than start_sec")

    clip_uuid = str(uuid.uuid4())
    refined_obj = RefinedClip(
        original_start=payload.start_sec,
        original_end=payload.end_sec,
        refined_start=payload.start_sec,
        refined_end=payload.end_sec,
        score=10.0,
        category="manual",
        hook=payload.title or "Manual Highlight",
        reason="Manual user created clip"
    )

    # 1. Cut
    cutter = ClipCutterAgent()
    cut_paths = cutter.run(job_id, str(raw_video), [refined_obj])
    cut_path = cut_paths[0]

    # 2. Reframe
    reframe = ReframeAgent()
    reframed_paths = reframe.run(
        job_id,
        [cut_path],
        layout=payload.layout or "focus",
        banner_text=payload.custom_header_text,
        font_size=payload.font_size or 48,
        font_family=payload.font_family or "Arial",
        font_color=payload.font_color
    )
    reframed_path = reframed_paths[0]

    # 3. Subtitles (if transcript exists)
    final_video = reframed_path
    transcript_file = job_dir / "transcript.json"
    if transcript_file.exists():
        try:
            with open(transcript_file, "r", encoding="utf-8") as f:
                tdata = TranscriptData.model_validate(json.load(f))
            sub_agent = SubtitleAgent()
            sub_paths = sub_agent.run(
                job_id,
                [reframed_path],
                [refined_obj],
                tdata,
                preset=payload.subtitle_preset or "bold_yellow"
            )
            final_video = sub_paths[0]
        except Exception:
            pass

    # 4. Thumbnail (extract at 0.5s)
    thumb_path = final_video.replace(".mp4", "_thumb.jpg")
    try:
        import subprocess
        subprocess.run([
            "ffmpeg", "-y", "-ss", "0.5", "-i", final_video, "-vframes", "1", "-q:v", "2", thumb_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except Exception:
        pass

    rel_video = f"jobs/{job_id}/clips/" + Path(final_video).name
    rel_thumb = f"jobs/{job_id}/clips/" + Path(thumb_path).name if os.path.exists(thumb_path) else None

    new_clip = Clip(
        id=clip_uuid,
        job_id=job_id,
        start_sec=payload.start_sec,
        end_sec=payload.end_sec,
        score=10.0,
        category="manual",
        hook=payload.title,
        reason="User custom clip",
        title=payload.title,
        caption=f"Highlight klip ({payload.start_sec:.1f}s - {payload.end_sec:.1f}s)",
        hashtags=["#shorts", "#viral", "#clip"],
        file_path=rel_video,
        thumbnail_path=rel_thumb
    )
    db.add(new_clip)
    await db.commit()
    await db.refresh(new_clip)

    return ClipResponse.model_validate(new_clip)

@router.delete("/{clip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clip(
    clip_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Clip)
        .join(Job, Clip.job_id == Job.id)
        .where(and_(Clip.id == clip_id, Job.user_id == current_user.id))
    )
    clip = (await db.execute(stmt)).scalar_one_or_none()
    if not clip:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found")

    if clip.file_path:
        storage.delete_file(clip.file_path)
    if clip.thumbnail_path:
        storage.delete_file(clip.thumbnail_path)

    await db.delete(clip)
    await db.commit()
    return None
