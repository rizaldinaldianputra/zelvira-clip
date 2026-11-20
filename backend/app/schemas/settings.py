from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class KeyCreate(BaseModel):
    provider: str = Field(..., description="openai, anthropic, gemini, deepseek, openrouter, custom")
    api_key: str = Field(..., min_length=1)
    base_url: Optional[str] = None

class KeyResponse(BaseModel):
    id: str
    provider: str
    key_hint: str
    base_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class KeyTestRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None
    key_id: Optional[str] = None
    model: str
    base_url: Optional[str] = None

class KeyTestResponse(BaseModel):
    success: bool
    message: str
    latency_ms: Optional[int] = None
    model_tested: Optional[str] = None

class ModelSuggestion(BaseModel):
    id: str
    name: str
    description: str
    provider: Optional[str] = None
    recommended_for: Optional[str] = None

class AgentModelItem(BaseModel):
    agent_name: str # moment_finder, ranker, metadata
    key_id: Optional[str] = None
    model: str

class AgentModelsUpdate(BaseModel):
    mappings: List[AgentModelItem]

class AgentModelResponse(BaseModel):
    agent_name: str
    key_id: Optional[str] = None
    key_hint: Optional[str] = None
    provider: Optional[str] = None
    model: str
