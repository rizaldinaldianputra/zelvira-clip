from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str # user, assistant, system
    content: str

class ChatCompletionRequest(BaseModel):
    provider: Optional[str] = Field(None, description="Target provider: openai, anthropic, gemini, nvidia, deepseek, mistral, custom")
    model: str = Field(..., description="Model identifier e.g. gpt-4o, claude-3-5-sonnet-latest, gemini-1.5-flash")
    messages: List[ChatMessage] = Field(..., min_length=1)
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    json_mode: Optional[bool] = False
    custom_base_url: Optional[str] = None
    key_id: Optional[str] = None

class ChatChoiceMessage(BaseModel):
    role: str = "assistant"
    content: Optional[str] = None

class ChatChoice(BaseModel):
    index: int = 0
    message: ChatChoiceMessage
    finish_reason: Optional[str] = "stop"

class UsageMetrics(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: Optional[float] = 0.0
    latency_ms: Optional[int] = 0

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    provider: str
    choices: List[ChatChoice]
    usage: UsageMetrics

class ModelRegistryItem(BaseModel):
    id: str
    name: str
    provider: str
    original_model_id: str
    context_window: Optional[int] = None
    max_output_tokens: Optional[int] = None
    supports_vision: bool = False
    supports_tools: bool = True
    supports_streaming: bool = True
    is_active: bool = True
    description: Optional[str] = None
    recommended_for: Optional[str] = None

class ProviderStatus(BaseModel):
    id: str
    name: str
    category: str
    connected: bool
    key_hint: Optional[str] = None
    base_url: Optional[str] = None
    model_count: int = 0

class UsageLogItem(BaseModel):
    id: str
    provider: Optional[str]
    model: str
    agent_name: str
    tokens_in: int
    tokens_out: int
    total_tokens: int
    cost_usd: float
    latency_ms: int
    status: str
    error_message: Optional[str]
    created_at: str

class UsageHistoryResponse(BaseModel):
    total_requests: int
    total_tokens: int
    total_cost_usd: float
    items: List[UsageLogItem]
