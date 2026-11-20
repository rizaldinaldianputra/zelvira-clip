from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.crypto import encrypt_api_key, decrypt_api_key, create_key_hint
from app.core.llm import call_llm, validate_custom_base_url
from app.core.rate_limit import check_rate_limit
from app.models.user import User
from app.models.key import UserAIKey, UserAgentModel
from app.schemas.settings import (
    KeyCreate,
    KeyResponse,
    KeyTestRequest,
    KeyTestResponse,
    ModelSuggestion,
    AgentModelsUpdate,
    AgentModelResponse,
)

router = APIRouter(prefix="/settings", tags=["AI Settings"])

SUGGESTED_MODELS: Dict[str, List[ModelSuggestion]] = {
    "openai": [
        ModelSuggestion(id="gpt-4o-mini", name="GPT-4o Mini", description="Fast, low-cost model, recommended for Moment Finder & Metadata", provider="openai", recommended_for="Moment Finder & Metadata"),
        ModelSuggestion(id="gpt-4o", name="GPT-4o", description="High-intelligence flagship model, recommended for Ranker", provider="openai", recommended_for="Ranker"),
        ModelSuggestion(id="gpt-4.1-turbo", name="GPT-4.1 Turbo", description="High-speed frontier intelligence", provider="openai", recommended_for="Ranker"),
        ModelSuggestion(id="o1-preview", name="o1 Preview", description="Advanced reasoning model", provider="openai", recommended_for="Ranker"),
        ModelSuggestion(id="o1-mini", name="o1 Mini", description="Faster reasoning model", provider="openai", recommended_for="Moment Finder"),
    ],
    "anthropic": [
        ModelSuggestion(id="claude-3-5-sonnet-latest", name="Claude 3.5 Sonnet", description="Top tier reasoning and curation", provider="anthropic", recommended_for="Ranker"),
        ModelSuggestion(id="claude-3-5-haiku-latest", name="Claude 3.5 Haiku", description="Fast and economical", provider="anthropic", recommended_for="Moment Finder & Metadata"),
        ModelSuggestion(id="claude-3-opus-latest", name="Claude 3 Opus", description="Deep nuance and complex analysis", provider="anthropic", recommended_for="Ranker"),
        ModelSuggestion(id="claude-3-sonnet-20240229", name="Claude 3 Sonnet", description="Balanced general purpose model", provider="anthropic", recommended_for="All Tasks"),
        ModelSuggestion(id="claude-3-haiku-20240307", name="Claude 3 Haiku", description="High throughput, ultra low latency", provider="anthropic", recommended_for="Moment Finder"),
    ],
    "gemini": [
        ModelSuggestion(id="gemini-1.5-flash", name="Gemini 1.5 Flash", description="Extremely fast, cheap, and large context", provider="gemini", recommended_for="Moment Finder & Metadata"),
        ModelSuggestion(id="gemini-1.5-flash-8b", name="Gemini 1.5 Flash 8B", description="Ultra lightweight and fastest response", provider="gemini", recommended_for="Metadata"),
        ModelSuggestion(id="gemini-1.5-pro", name="Gemini 1.5 Pro", description="Strong reasoning capabilities", provider="gemini", recommended_for="Ranker"),
        ModelSuggestion(id="gemini-2.0-flash-exp", name="Gemini 2.0 Flash (Experimental)", description="Next-generation multimodal model", provider="gemini", recommended_for="Moment Finder"),
    ],
    "deepseek": [
        ModelSuggestion(id="deepseek-chat", name="DeepSeek-V3", description="Powerful open-weights model, very low cost", provider="deepseek", recommended_for="All Tasks"),
        ModelSuggestion(id="deepseek-reasoner", name="DeepSeek-R1", description="Reasoning model for complex curation", provider="deepseek", recommended_for="Ranker"),
    ],
    "openrouter": [
        ModelSuggestion(id="meta-llama/llama-3.1-8b-instruct", name="Llama 3.1 8B", description="Fast and open-source", provider="openrouter", recommended_for="Moment Finder"),
        ModelSuggestion(id="meta-llama/llama-3.1-70b-instruct", name="Llama 3.1 70B", description="High accuracy open weights", provider="openrouter", recommended_for="Ranker"),
        ModelSuggestion(id="anthropic/claude-3.5-sonnet", name="Claude 3.5 Sonnet (via OpenRouter)", description="Curated quality", provider="openrouter", recommended_for="Ranker"),
        ModelSuggestion(id="google/gemini-flash-1.5", name="Gemini Flash 1.5 (via OpenRouter)", description="Fast multimodal", provider="openrouter", recommended_for="Moment Finder"),
        ModelSuggestion(id="qwen/qwen-2.5-72b-instruct", name="Qwen 2.5 72B", description="Top benchmark multilingual model", provider="openrouter", recommended_for="All Tasks"),
    ],
    "nvidia": [
        ModelSuggestion(id="meta/llama-3.1-70b-instruct", name="Llama 3.1 70B Instruct", description="High performance open-weights via NVIDIA NIM", provider="nvidia", recommended_for="Moment Finder & Ranker"),
        ModelSuggestion(id="meta/llama-3.1-8b-instruct", name="Llama 3.1 8B Instruct", description="Ultra fast inference via NVIDIA NIM", provider="nvidia", recommended_for="Moment Finder & Metadata"),
        ModelSuggestion(id="nvidia/nemotron-4-340b-instruct", name="Nemotron-4 340B", description="Flagship NVIDIA reasoning model", provider="nvidia", recommended_for="Ranker"),
        ModelSuggestion(id="nvidia/nemotron-3.5-super-vl-120b-a12b", name="Nemotron-3.5 Super VL 120B", description="NVIDIA Super Vision-Language Reasoning Model", provider="nvidia", recommended_for="Ranker & Video"),
        ModelSuggestion(id="mistralai/mistral-large-2-instruct", name="Mistral Large 2", description="High-reasoning multilingual model", provider="nvidia", recommended_for="Ranker"),
        ModelSuggestion(id="google/gemma-2-27b-it", name="Gemma 2 27B", description="Google Gemma on NVIDIA NIM", provider="nvidia", recommended_for="Moment Finder"),
    ],
    "custom": [
        ModelSuggestion(id="gpt-4o-mini", name="GPT-4o Mini (OpenAI-compatible)", description="Standard proxy model endpoint", provider="custom", recommended_for="All Tasks"),
        ModelSuggestion(id="gpt-4o", name="GPT-4o (OpenAI-compatible)", description="Flagship proxy model", provider="custom", recommended_for="Ranker"),
        ModelSuggestion(id="claude-3-haiku", name="Claude 3 Haiku (Proxy)", description="Fast proxy response", provider="custom", recommended_for="Moment Finder"),
        ModelSuggestion(id="deepseek-chat", name="DeepSeek Chat (Proxy)", description="DeepSeek endpoint via proxy", provider="custom", recommended_for="All Tasks"),
    ]
}

@router.post("/keys", response_model=KeyResponse, status_code=status.HTTP_201_CREATED)
async def add_key(
    payload: KeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    provider = payload.provider.lower().strip()
    valid_providers = ("openai", "anthropic", "gemini", "deepseek", "openrouter", "nvidia", "custom")
    if provider not in valid_providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider. Choose from: {', '.join(valid_providers)}"
        )

    # Validate SSRF on custom base_url
    if provider == "nvidia" and not payload.base_url:
        payload.base_url = "https://integrate.api.nvidia.com/v1"

    if provider in ("custom", "nvidia") and payload.base_url:
        try:
            validate_custom_base_url(payload.base_url)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    encrypted = encrypt_api_key(payload.api_key)
    hint = create_key_hint(payload.api_key)

    new_key = UserAIKey(
        user_id=current_user.id,
        provider=provider,
        encrypted_key=encrypted,
        key_hint=hint,
        base_url=payload.base_url.strip() if payload.base_url else None
    )
    db.add(new_key)
    await db.commit()
    await db.refresh(new_key)

    return new_key

@router.get("/keys", response_model=List[KeyResponse])
async def list_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(UserAIKey).where(UserAIKey.user_id == current_user.id).order_by(UserAIKey.created_at.desc())
    keys = (await db.execute(stmt)).scalars().all()
    return keys

@router.delete("/keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_key(
    key_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(UserAIKey).where(and_(UserAIKey.id == key_id, UserAIKey.user_id == current_user.id))
    key = (await db.execute(stmt)).scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Key not found")

    await db.delete(key)
    await db.commit()
    return None

@router.post("/keys/test", response_model=KeyTestResponse)
async def test_key_connection(
    payload: KeyTestRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Enforce rate limit (10 tests per minute per IP)
    check_rate_limit(request, max_requests=10, window_seconds=60)

    plain_key = None
    provider = payload.provider.lower()
    base_url = payload.base_url

    if payload.key_id:
        stmt = select(UserAIKey).where(and_(UserAIKey.id == payload.key_id, UserAIKey.user_id == current_user.id))
        key_rec = (await db.execute(stmt)).scalar_one_or_none()
        if not key_rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specified key not found")
        plain_key = decrypt_api_key(key_rec.encrypted_key)
        provider = key_rec.provider
        base_url = key_rec.base_url or base_url
    elif payload.api_key:
        plain_key = payload.api_key
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Either api_key or key_id must be provided")

    if provider == "nvidia" and not base_url:
        base_url = "https://integrate.api.nvidia.com/v1"

    if provider in ("custom", "nvidia") and base_url:
        try:
            validate_custom_base_url(base_url)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Send a tiny ping test message
    test_messages = [
        {"role": "user", "content": "Respond strictly with valid JSON: {\"status\": \"ok\"}"}
    ]

    try:
        _, metrics = call_llm(
            user_key=plain_key,
            model=payload.model,
            messages=test_messages,
            provider=provider,
            base_url=base_url,
            json_mode=True,
            timeout=25
        )
        return KeyTestResponse(
            success=True,
            message="Connection test succeeded! Key and model are ready to use.",
            latency_ms=metrics.get("latency_ms", 0),
            model_tested=metrics.get("model_used", payload.model)
        )
    except Exception as e:
        # Scrub any secret from error message
        err_msg = str(e)
        if plain_key and plain_key in err_msg:
            err_msg = "Authentication failed: invalid API key or permission denied."
        return KeyTestResponse(
            success=False,
            message=f"Connection test failed: {err_msg}",
            model_tested=payload.model
        )

@router.get("/models", response_model=List[ModelSuggestion])
async def get_models(provider: Optional[str] = Query(None)):
    import urllib.request, json

    # If provider is openrouter, fetch live list of openrouter models
    if provider == "openrouter":
        try:
            req = urllib.request.Request("https://openrouter.ai/api/v1/models", headers={"User-Agent": "ZelvuraClipper/1.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                live_models = []
                for item in data.get("data", []):
                    m_id = item.get("id")
                    m_name = item.get("name") or m_id
                    m_desc = item.get("description", "") or "OpenRouter Model"
                    if len(m_desc) > 100:
                        m_desc = m_desc[:97] + "..."
                    live_models.append(ModelSuggestion(
                        id=m_id,
                        name=m_name,
                        description=m_desc,
                        provider="openrouter",
                        recommended_for="OpenRouter Community"
                    ))
                if live_models:
                    return live_models
        except Exception:
            pass  # Fallback to predefined list
        return SUGGESTED_MODELS.get("openrouter", [])

    # If provider is nvidia, fetch live list from NVIDIA NIM
    if provider == "nvidia":
        try:
            req = urllib.request.Request("https://integrate.api.nvidia.com/v1/models", headers={"User-Agent": "ZelvuraClipper/1.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                live_models = []
                for item in data.get("data", []):
                    m_id = item.get("id")
                    live_models.append(ModelSuggestion(
                        id=m_id,
                        name=m_id,
                        description="NVIDIA NIM Accelerated Model",
                        provider="nvidia",
                        recommended_for="NVIDIA NIM"
                    ))
                if live_models:
                    return live_models
        except Exception:
            pass
        return SUGGESTED_MODELS.get("nvidia", [])

    if not provider:
        all_models = []
        for p_models in SUGGESTED_MODELS.values():
            all_models.extend(p_models)
        return all_models
    return SUGGESTED_MODELS.get(provider.lower(), [])

@router.get("/agent-models", response_model=List[AgentModelResponse])
async def get_agent_models(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(UserAgentModel, UserAIKey.key_hint, UserAIKey.provider)
        .outerjoin(UserAIKey, UserAgentModel.key_id == UserAIKey.id)
        .where(UserAgentModel.user_id == current_user.id)
    )
    rows = (await db.execute(stmt)).all()
    
    # Defaults if not configured
    defaults = {
        "moment_finder": {"model": "gpt-4o-mini"},
        "ranker": {"model": "gpt-4o"},
        "metadata": {"model": "gpt-4o-mini"}
    }
    
    results = {}
    for row in rows:
        agent_model, key_hint, provider = row
        results[agent_model.agent_name] = AgentModelResponse(
            agent_name=agent_model.agent_name,
            key_id=agent_model.key_id,
            key_hint=key_hint,
            provider=provider,
            model=agent_model.model
        )

    for agent_name, d_val in defaults.items():
        if agent_name not in results:
            results[agent_name] = AgentModelResponse(
                agent_name=agent_name,
                key_id=None,
                key_hint=None,
                provider=None,
                model=d_val["model"]
            )

    return list(results.values())

@router.put("/agent-models", response_model=List[AgentModelResponse])
async def update_agent_models(
    payload: AgentModelsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    valid_agents = ("moment_finder", "ranker", "metadata")

    for item in payload.mappings:
        if item.agent_name not in valid_agents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid agent name '{item.agent_name}'. Must be one of: {', '.join(valid_agents)}"
            )

        # Check key belongs to user if specified
        if item.key_id:
            stmt_key = select(UserAIKey).where(and_(UserAIKey.id == item.key_id, UserAIKey.user_id == current_user.id))
            key_exists = (await db.execute(stmt_key)).scalar_one_or_none()
            if not key_exists:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Key {item.key_id} not found")

        # Upsert mapping
        stmt = select(UserAgentModel).where(
            and_(UserAgentModel.user_id == current_user.id, UserAgentModel.agent_name == item.agent_name)
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            existing.key_id = item.key_id
            existing.model = item.model
        else:
            new_mapping = UserAgentModel(
                user_id=current_user.id,
                agent_name=item.agent_name,
                key_id=item.key_id,
                model=item.model
            )
            db.add(new_mapping)

    await db.commit()
    return await get_agent_models(current_user=current_user, db=db)
