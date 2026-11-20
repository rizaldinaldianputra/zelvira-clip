import time
import uuid
from typing import List, Dict, Optional, Tuple, Any
import litellm
from litellm import completion, completion_cost

from app.core.logging import logger
from app.core.llm import validate_custom_base_url, normalize_custom_base_url
from app.schemas.ai_gateway import ModelRegistryItem, ProviderStatus

# Global litellm configurations
litellm.telemetry = False
litellm.drop_params = True

# Dynamic Model Registry
# Configurable registry for all supported providers: OpenAI, Claude, Gemini, NVIDIA, DeepSeek, Mistral, Custom
MODEL_REGISTRY: List[ModelRegistryItem] = [
    # 1. OpenAI
    ModelRegistryItem(
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        provider="openai",
        original_model_id="gpt-4o-mini",
        context_window=128000,
        max_output_tokens=16384,
        supports_vision=True,
        supports_tools=True,
        supports_streaming=True,
        description="Fast, cost-efficient model for lightweight tasks",
        recommended_for="Fast Inference & General Tasks"
    ),
    ModelRegistryItem(
        id="gpt-4o",
        name="GPT-4o",
        provider="openai",
        original_model_id="gpt-4o",
        context_window=128000,
        max_output_tokens=16384,
        supports_vision=True,
        supports_tools=True,
        supports_streaming=True,
        description="Flagship multimodal intelligence for high-reasoning",
        recommended_for="Deep Analysis & Ranker"
    ),
    ModelRegistryItem(
        id="o3-mini",
        name="o3-mini",
        provider="openai",
        original_model_id="o3-mini",
        context_window=200000,
        max_output_tokens=100000,
        supports_vision=False,
        supports_tools=True,
        supports_streaming=True,
        description="High-speed reasoning model specialized in math & coding",
        recommended_for="Complex Logic"
    ),

    # 2. Anthropic Claude
    ModelRegistryItem(
        id="claude-3-5-sonnet-latest",
        name="Claude 3.5 Sonnet",
        provider="anthropic",
        original_model_id="claude-3-5-sonnet-20241022",
        context_window=200000,
        max_output_tokens=8192,
        supports_vision=True,
        supports_tools=True,
        supports_streaming=True,
        description="Industry-leading frontier reasoning and nuance",
        recommended_for="Creative Analysis & Nuanced Curation"
    ),
    ModelRegistryItem(
        id="claude-3-5-haiku-latest",
        name="Claude 3.5 Haiku",
        provider="anthropic",
        original_model_id="claude-3-5-haiku-20241022",
        context_window=200000,
        max_output_tokens=8192,
        supports_vision=True,
        supports_tools=True,
        supports_streaming=True,
        description="Next-generation high-speed intelligence from Anthropic",
        recommended_for="Fast Summaries & Metadata"
    ),
    ModelRegistryItem(
        id="claude-3-opus-latest",
        name="Claude 3 Opus",
        provider="anthropic",
        original_model_id="claude-3-opus-20240229",
        context_window=200000,
        max_output_tokens=4096,
        supports_vision=True,
        supports_tools=True,
        supports_streaming=True,
        description="Powerful deep thinking and complex context comprehension",
        recommended_for="Deep Evaluation"
    ),

    # 3. Google Gemini
    ModelRegistryItem(
        id="gemini-1.5-flash",
        name="Gemini 1.5 Flash",
        provider="gemini",
        original_model_id="gemini-1.5-flash",
        context_window=1000000,
        max_output_tokens=8192,
        supports_vision=True,
        supports_tools=True,
        supports_streaming=True,
        description="Fast multimodal model with 1 Million token context window",
        recommended_for="Long Video Contexts & Transcripts"
    ),
    ModelRegistryItem(
        id="gemini-1.5-pro",
        name="Gemini 1.5 Pro",
        provider="gemini",
        original_model_id="gemini-1.5-pro",
        context_window=2000000,
        max_output_tokens=8192,
        supports_vision=True,
        supports_tools=True,
        supports_streaming=True,
        description="Frontier reasoning across huge multimodal datasets",
        recommended_for="Ultra-Long Audio & Video Search"
    ),
    ModelRegistryItem(
        id="gemini-2.0-flash-exp",
        name="Gemini 2.0 Flash (Experimental)",
        provider="gemini",
        original_model_id="gemini-2.0-flash-exp",
        context_window=1048576,
        max_output_tokens=8192,
        supports_vision=True,
        supports_tools=True,
        supports_streaming=True,
        description="Google's next-gen multimodal speed demon",
        recommended_for="Next-Gen Fast Processing"
    ),

    # 4. NVIDIA NIM
    ModelRegistryItem(
        id="meta/llama-3.1-70b-instruct",
        name="Llama 3.1 70B (NVIDIA NIM)",
        provider="nvidia",
        original_model_id="meta/llama-3.1-70b-instruct",
        context_window=128000,
        max_output_tokens=4096,
        supports_vision=False,
        supports_tools=True,
        supports_streaming=True,
        description="High-performance open weights accelerated via NVIDIA NIM",
        recommended_for="Cost-Effective High Performance"
    ),
    ModelRegistryItem(
        id="meta/llama-3.1-8b-instruct",
        name="Llama 3.1 8B (NVIDIA NIM)",
        provider="nvidia",
        original_model_id="meta/llama-3.1-8b-instruct",
        context_window=128000,
        max_output_tokens=4096,
        supports_vision=False,
        supports_tools=True,
        supports_streaming=True,
        description="Ultra-low latency open model hosted on NVIDIA infrastructure",
        recommended_for="Fast Inference"
    ),
    ModelRegistryItem(
        id="nvidia/nemotron-4-340b-instruct",
        name="Nemotron-4 340B (NVIDIA NIM)",
        provider="nvidia",
        original_model_id="nvidia/nemotron-4-340b-instruct",
        context_window=4096,
        max_output_tokens=4096,
        supports_vision=False,
        supports_tools=True,
        supports_streaming=True,
        description="NVIDIA flagship enterprise synthetic & reasoning LLM",
        recommended_for="Enterprise Logic"
    ),

    # 5. DeepSeek
    ModelRegistryItem(
        id="deepseek-chat",
        name="DeepSeek-V3",
        provider="deepseek",
        original_model_id="deepseek-chat",
        context_window=64000,
        max_output_tokens=8192,
        supports_vision=False,
        supports_tools=True,
        supports_streaming=True,
        description="High-capability open architecture with ultra-competitive pricing",
        recommended_for="High Volume & General Agent Tasks"
    ),
    ModelRegistryItem(
        id="deepseek-reasoner",
        name="DeepSeek-R1",
        provider="deepseek",
        original_model_id="deepseek-reasoner",
        context_window=64000,
        max_output_tokens=8192,
        supports_vision=False,
        supports_tools=False,
        supports_streaming=True,
        description="Chain-of-thought deep reasoning architecture from DeepSeek",
        recommended_for="Complex Step-by-Step Reasoning"
    ),

    # 6. Mistral
    ModelRegistryItem(
        id="mistral-large-latest",
        name="Mistral Large 2",
        provider="mistral",
        original_model_id="mistral-large-latest",
        context_window=128000,
        max_output_tokens=8192,
        supports_vision=False,
        supports_tools=True,
        supports_streaming=True,
        description="Mistral AI's flagship high-reasoning model",
        recommended_for="Multilingual & Complex Tasks"
    ),
    ModelRegistryItem(
        id="mistral-small-latest",
        name="Mistral Small",
        provider="mistral",
        original_model_id="mistral-small-latest",
        context_window=32000,
        max_output_tokens=8192,
        supports_vision=False,
        supports_tools=True,
        supports_streaming=True,
        description="Fast, low-latency and economical Mistral model",
        recommended_for="Quick Responses"
    ),

    # 7. Custom / OpenRouter
    ModelRegistryItem(
        id="custom/openai-compatible",
        name="Custom OpenAI-Compatible",
        provider="custom",
        original_model_id="custom",
        context_window=128000,
        max_output_tokens=4096,
        supports_vision=True,
        supports_tools=True,
        supports_streaming=True,
        description="Self-hosted vLLM, Ollama, Groq, or custom proxy endpoint",
        recommended_for="Self-Hosted / Private Endpoints"
    ),
]

def format_gateway_model(provider: str, model_id: str) -> str:
    """
    Ensures the model prefix follows LiteLLM convention:
    openai/..., anthropic/..., gemini/..., deepseek/..., mistral/...
    """
    p = provider.lower()
    m = model_id.strip()

    if "/" in m:
        return m

    if p == "openai":
        return f"openai/{m}"
    elif p == "anthropic":
        return f"anthropic/{m}"
    elif p == "gemini":
        return f"gemini/{m}"
    elif p == "deepseek":
        return f"deepseek/{m}"
    elif p == "mistral":
        return f"mistral/{m}"
    elif p == "nvidia":
        return f"openai/{m}"
    elif p == "openrouter":
        return f"openrouter/{m}"
    elif p == "custom":
        return f"openai/{m}"
    return m

def execute_gateway_completion(
    api_key: str,
    provider: str,
    model: str,
    messages: List[Dict[str, Any]],
    temperature: Optional[float] = 0.7,
    max_tokens: Optional[int] = None,
    json_mode: bool = False,
    base_url: Optional[str] = None,
    timeout: int = 60,
) -> Tuple[Any, Dict[str, Any]]:
    """
    Executes an LLM completion via LiteLLM using BYOK credential.
    Returns: (litellm_response_obj, metrics_dict)
    """
    # 1. URL validation for custom or NVIDIA NIM
    if provider.lower() == "nvidia":
        if not base_url:
            base_url = "https://integrate.api.nvidia.com/v1"
        validate_custom_base_url(base_url)

    if provider.lower() == "custom" and base_url:
        validate_custom_base_url(base_url)
        base_url = normalize_custom_base_url(base_url)

    target_model = format_gateway_model(provider, model)

    kwargs: Dict[str, Any] = {
        "model": target_model,
        "messages": messages,
        "api_key": api_key,
        "timeout": timeout,
        "temperature": temperature if temperature is not None else 0.7,
    }

    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    if base_url:
        kwargs["api_base"] = base_url

    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    start_time = time.time()
    try:
        response = completion(**kwargs)
    except Exception as exc:
        latency_ms = int((time.time() - start_time) * 1000)
        logger.error(f"[AI Gateway] Request to {provider}/{model} failed: {str(exc)}")
        raise exc

    latency_ms = int((time.time() - start_time) * 1000)

    # Calculate tokens & cost
    tokens_in = 0
    tokens_out = 0
    if hasattr(response, "usage") and response.usage:
        tokens_in = getattr(response.usage, "prompt_tokens", 0) or 0
        tokens_out = getattr(response.usage, "completion_tokens", 0) or 0

    cost_usd = 0.0
    try:
        cost_usd = float(completion_cost(completion_response=response))
    except Exception:
        cost_usd = 0.0

    metrics = {
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "total_tokens": tokens_in + tokens_out,
        "cost_usd": cost_usd,
        "latency_ms": latency_ms,
        "target_model": target_model,
    }

    return response, metrics
