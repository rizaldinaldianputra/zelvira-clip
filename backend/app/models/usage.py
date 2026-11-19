import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True, index=True)
    agent_name = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    tokens_in = Column(Integer, default=0, nullable=False)
    tokens_out = Column(Integer, default=0, nullable=False)
    cost_usd = Column(Float, default=0.0, nullable=False)
    latency_ms = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    job = relationship("Job", back_populates="usage_logs")
