import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class Clip(Base):
    __tablename__ = "clips"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    start_sec = Column(Float, nullable=False)
    end_sec = Column(Float, nullable=False)
    score = Column(Float, default=0.0, nullable=False, index=True)
    category = Column(String(100), nullable=True)
    hook = Column(Text, nullable=True)
    reason = Column(Text, nullable=True)
    title = Column(String(255), nullable=True)
    caption = Column(Text, nullable=True)
    hashtags = Column(JSON, default=list, nullable=False)
    file_path = Column(String(500), nullable=True)
    thumbnail_path = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    job = relationship("Job", back_populates="clips")
