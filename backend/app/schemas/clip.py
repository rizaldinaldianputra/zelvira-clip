from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ClipResponse(BaseModel):
    id: str
    job_id: str
    start_sec: float
    end_sec: float
    score: float
    category: Optional[str] = None
    hook: Optional[str] = None
    reason: Optional[str] = None
    title: Optional[str] = None
    caption: Optional[str] = None
    hashtags: List[str] = []
    file_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
