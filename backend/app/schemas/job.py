from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from app.schemas.clip import ClipResponse

class JobSettings(BaseModel):
    clip_count: int = Field(default=5, ge=1, le=10)
    target_duration: int = Field(default=60, ge=15, le=120) # seconds
    layout: Literal["focus", "split"] = "focus"
    subtitle_preset: Literal["bold_yellow", "classic", "neon"] = "bold_yellow"
    language: str = "auto" # 'auto', 'id', 'en'

class JobCreate(BaseModel):
    source_url: Optional[str] = None
    settings: Optional[JobSettings] = Field(default_factory=JobSettings)

class JobResponse(BaseModel):
    id: str
    user_id: str
    source_type: str
    source_url: Optional[str] = None
    title: Optional[str] = None
    duration_sec: Optional[float] = None
    status: str
    progress: int
    error: Optional[str] = None
    failed_step: Optional[str] = None
    settings: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class JobDetailResponse(JobResponse):
    clips: List[ClipResponse] = []
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    transcript_preview: Optional[str] = None
    step_history: List[Dict[str, Any]] = []
