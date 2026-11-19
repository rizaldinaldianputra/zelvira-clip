import os
from pathlib import Path
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
