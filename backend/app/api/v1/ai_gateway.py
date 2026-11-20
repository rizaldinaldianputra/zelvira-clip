import time
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.crypto import decrypt_api_key
from app.core.rate_limit import check_rate_limit
from app.core.logging import logger
from app.models.user import User
from app.models.key import UserAIKey
from app.models.usage import UsageLog
from app.schemas.ai_gateway import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatChoice,
    ChatChoiceMessage,
    UsageMetrics,
    ModelRegistryItem,
    ProviderStatus,
    UsageHistoryResponse,
    UsageLogItem,
)
from app.core.llm_gateway import (
    MODEL_REGISTRY,
    execute_gateway_completion,
    format_gateway_model,
)

router = APIRouter(prefix="/ai", tags=["Unified AI Gateway"])

# List of official supported providers for status cards
SUPPORTED_PROVIDERS = [
    {"id": "openai", "name": "OpenAI", "category": "GPT Models"},
    {"id": "anthropic", "name": "Anthropic", "category": "Claude Models"},
    {"id": "gemini", "name": "Google Gemini", "category": "Gemini Models"},
    {"id": "nvidia", "name": "NVIDIA", "category": "NVIDIA NIM"},
    {"id": "deepseek", "name": "DeepSeek", "category": "DeepSeek Models"},
    {"id": "mistral", "name": "Mistral", "category": "Mistral Models"},
    {"id": "custom", "name": "Custom / Self-Hosted", "category": "OpenAI-Compatible"},
]

@router.get("/providers", response_model=List[ProviderStatus])
async def get_providers_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns connection status for all AI providers for the authenticated user.
    """
    stmt = select(UserAIKey).where(UserAIKey.user_id == current_user.id)
    user_keys = (await db.execute(stmt)).scalars().all()
    user_key_map = {k.provider.lower(): k for k in user_keys}

    results: List[ProviderStatus] = []
    for p in SUPPORTED_PROVIDERS:
        pid = p["id"]
        key_entry = user_key_map.get(pid)
        model_count = len([m for m in MODEL_REGISTRY if m.provider == pid])

        results.append(
            ProviderStatus(
                id=pid,
                name=p["name"],
                category=p["category"],
                connected=key_entry is not None,
                key_hint=key_entry.key_hint if key_entry else None,
                base_url=key_entry.base_url if key_entry else None,
                model_count=model_count,
            )
        )
    return results

@router.get("/models", response_model=List[ModelRegistryItem])
async def list_registry_models(
    provider: Optional[str] = Query(None, description="Filter models by provider name"),
    current_user: User = Depends(get_current_user)
):
    """
    Returns available models from the dynamic model registry.
    """
    if provider:
        return [m for m in MODEL_REGISTRY if m.provider.lower() == provider.lower()]
    return MODEL_REGISTRY

@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def unified_chat_completion(
    request: Request,
    payload: ChatCompletionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Unified AI Gateway Endpoint (OpenAI-compatible)
    Translates incoming requests across OpenAI, Anthropic, Gemini, NVIDIA, DeepSeek, Mistral.
    Uses authenticated user's encrypted BYOK credentials.
    """
    # 1. Rate Limiting (per user bucket)
    await check_rate_limit(request, current_user.id)

    # 2. Determine target provider
    target_provider = payload.provider
    if not target_provider:
        # Infer provider from model name if omitted
        match = next((m for m in MODEL_REGISTRY if m.id.lower() == payload.model.lower()), None)
        if match:
            target_provider = match.provider
        else:
            target_provider = "openai"
    target_provider = target_provider.lower()

    # 3. Resolve user BYOK Credential securely
    user_key_obj: Optional[UserAIKey] = None
    if payload.key_id:
        stmt = select(UserAIKey).where(and_(UserAIKey.id == payload.key_id, UserAIKey.user_id == current_user.id))
        user_key_obj = (await db.execute(stmt)).scalar_one_or_none()
    else:
        stmt = select(UserAIKey).where(and_(UserAIKey.provider == target_provider, UserAIKey.user_id == current_user.id))
        user_key_obj = (await db.execute(stmt)).scalar_one_or_none()

    if not user_key_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tidak ditemukan API Key untuk provider '{target_provider}'. Silakan tambahkan API Key Anda di menu Pengaturan / AI Gateway."
        )

    # 4. Decrypt credential (never logged, stays in memory only)
    try:
        raw_api_key = decrypt_api_key(user_key_obj.encrypted_key)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Gagal mendekripsi API Key.")

    base_url = payload.custom_base_url or user_key_obj.base_url

    # 5. Format messages
    formatted_messages = [{"role": msg.role, "content": msg.content} for msg in payload.messages]

    # 6. Execute completion via LiteLLM
    try:
        litellm_resp, metrics = execute_gateway_completion(
            api_key=raw_api_key,
            provider=target_provider,
            model=payload.model,
            messages=formatted_messages,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
            json_mode=payload.json_mode or False,
            base_url=base_url,
        )

        # 7. Audit & Usage Logging (Success)
        usage_log = UsageLog(
            user_id=current_user.id,
            job_id=None,
            provider=target_provider,
            agent_name="unified_gateway",
            model=payload.model,
            tokens_in=metrics["tokens_in"],
            tokens_out=metrics["tokens_out"],
            cost_usd=metrics["cost_usd"],
            latency_ms=metrics["latency_ms"],
            status="success",
            error_message=None
        )
        db.add(usage_log)
        await db.commit()

        # 8. Build OpenAI-compatible response
        content_out = ""
        if hasattr(litellm_resp, "choices") and litellm_resp.choices:
            choice = litellm_resp.choices[0]
            if hasattr(choice, "message"):
                content_out = getattr(choice.message, "content", "") or ""

        resp_id = getattr(litellm_resp, "id", f"chatcmpl-{uuid.uuid4().hex[:12]}")

        return ChatCompletionResponse(
            id=resp_id,
            object="chat.completion",
            created=int(time.time()),
            model=payload.model,
            provider=target_provider,
            choices=[
                ChatChoice(
                    index=0,
                    message=ChatChoiceMessage(role="assistant", content=content_out),
                    finish_reason="stop",
                )
            ],
            usage=UsageMetrics(
                prompt_tokens=metrics["tokens_in"],
                completion_tokens=metrics["tokens_out"],
                total_tokens=metrics["total_tokens"],
                cost_usd=metrics["cost_usd"],
                latency_ms=metrics["latency_ms"],
            )
        )

    except Exception as exc:
        err_msg = str(exc)
        # Sanitized error message without leaking secret
        sanitized_err = "LLM invocation error: Provider returned an error."
        if "401" in err_msg or "authentication" in err_msg.lower():
            sanitized_err = f"Autentikasi gagal untuk provider {target_provider}. Kunci API salah atau tidak valid."
        elif "429" in err_msg or "rate limit" in err_msg.lower() or "quota" in err_msg.lower():
            sanitized_err = f"Rate limit atau kuota habis pada provider {target_provider}."

        # Audit & Usage Logging (Failed)
        usage_log = UsageLog(
            user_id=current_user.id,
            job_id=None,
            provider=target_provider,
            agent_name="unified_gateway",
            model=payload.model,
            tokens_in=0,
            tokens_out=0,
            cost_usd=0.0,
            latency_ms=0,
            status="error",
            error_message=sanitized_err
        )
        db.add(usage_log)
        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=sanitized_err
        )

@router.get("/usage", response_model=UsageHistoryResponse)
async def get_user_usage_history(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the user's AI request and token consumption audit logs.
    """
    stmt = (
        select(UsageLog)
        .where(UsageLog.user_id == current_user.id)
        .order_by(desc(UsageLog.created_at))
        .limit(limit)
    )
    logs = (await db.execute(stmt)).scalars().all()

    # Aggregate summaries
    sum_stmt = select(
        func.count(UsageLog.id),
        func.sum(UsageLog.tokens_in + UsageLog.tokens_out),
        func.sum(UsageLog.cost_usd)
    ).where(UsageLog.user_id == current_user.id)

    total_req, total_tok, total_cost = (await db.execute(sum_stmt)).one()

    items = [
        UsageLogItem(
            id=log.id,
            provider=log.provider or "openai",
            model=log.model,
            agent_name=log.agent_name,
            tokens_in=log.tokens_in,
            tokens_out=log.tokens_out,
            total_tokens=log.tokens_in + log.tokens_out,
            cost_usd=round(log.cost_usd or 0.0, 6),
            latency_ms=log.latency_ms,
            status=log.status or "success",
            error_message=log.error_message,
            created_at=log.created_at.isoformat() if log.created_at else "",
        )
        for log in logs
    ]

    return UsageHistoryResponse(
        total_requests=total_req or 0,
        total_tokens=total_tok or 0,
        total_cost_usd=round(total_cost or 0.0, 6),
        items=items
    )
