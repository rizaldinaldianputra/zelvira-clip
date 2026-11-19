import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(20), nullable=False) # 'youtube', 'tiktok', 'upload'
    source_url = Column(Text, nullable=True)
    title = Column(String(255), nullable=True)
    duration_sec = Column(Float, nullable=True)
    status = Column(String(30), default="queued", nullable=False, index=True)
    progress = Column(Integer, default=0, nullable=False)
    error = Column(Text, nullable=True)
    failed_step = Column(String(50), nullable=True)
    settings = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="jobs")
    clips = relationship("Clip", back_populates="job", cascade="all, delete-orphan", order_by="desc(Clip.score)")
    usage_logs = relationship("UsageLog", back_populates="job", cascade="all, delete-orphan")
