import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class UserAIKey(Base):
    __tablename__ = "user_ai_keys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False) # openai, anthropic, gemini, deepseek, openrouter, custom
    encrypted_key = Column(String(500), nullable=False)
    key_hint = Column(String(20), nullable=False)
    base_url = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="ai_keys")
    agent_models = relationship("UserAgentModel", back_populates="key", cascade="all, delete-orphan")

class UserAgentModel(Base):
    __tablename__ = "user_agent_models"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name = Column(String(50), nullable=False) # moment_finder, ranker, metadata
    key_id = Column(String(36), ForeignKey("user_ai_keys.id", ondelete="SET NULL"), nullable=True)
    model = Column(String(100), nullable=False)

    # Relationships
    user = relationship("User", back_populates="agent_models")
    key = relationship("UserAIKey", back_populates="agent_models")
