import time
import socket
import ipaddress
import json
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional, Tuple
import litellm
from litellm import completion, completion_cost
from app.core.logging import logger

# Disable litellm telemetry and set global defaults
litellm.telemetry = False
litellm.drop_params = True

def normalize_custom_base_url(url: Optional[str]) -> Optional[str]:
    """
    Normalizes custom OpenAI-compatible base URL.
    Ensures that trailing /v1 is present if omitted, or keeps it cleanly formatted.
    """
    if not url:
        return None
    clean = url.strip().rstrip("/")
    if not clean.endswith("/v1"):
        clean = f"{clean}/v1"
    return clean

def validate_custom_base_url(url: str) -> None:
    if not url:
        return
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Invalid URL scheme. Only HTTP and HTTPS are permitted.")
    
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Invalid URL: missing hostname.")

    # Check for direct localhost string
    if hostname.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        raise ValueError("Access to localhost or loopback addresses is forbidden.")

    try:
        # Resolve hostname to IPv4/IPv6 address
        addr_info = socket.getaddrinfo(hostname, None)
        for item in addr_info:
            ip_str = item[4][0]
            ip = ipaddress.ip_address(ip_str)
            if (
                ip.is_loopback or
                ip.is_private or
                ip.is_link_local or
                ip.is_reserved or
                ip.is_unspecified
            ):
                raise ValueError(f"Access to internal/private IP address is forbidden.")
    except socket.gaierror:
        raise ValueError(f"Unable to resolve hostname: {hostname}")

def format_model_for_provider(provider: str, model_name: str) -> str:
    """
    Formats the model string properly for LiteLLM based on the provider.
    """
    provider = provider.lower()
    clean_name = model_name.strip()
    
    # If the model already contains provider prefix (e.g. 'openai/gpt-4o'), keep it
    if "/" in clean_name:
        return clean_name
        
    if provider == "openai":
        return f"openai/{clean_name}"
    elif provider == "anthropic":
        return f"anthropic/{clean_name}"
    elif provider == "gemini":
        return f"gemini/{clean_name}"
    elif provider == "deepseek":
        return f"deepseek/{clean_name}"
    elif provider == "openrouter":
        return f"openrouter/{clean_name}"
    elif provider == "nvidia":
        return f"openai/{clean_name}"
    elif provider == "custom":
        return f"openai/{clean_name}"
    return clean_name

def call_llm(
    user_key: str,
    model: str,
    messages: List[Dict[str, str]],
    provider: str = "openai",
    base_url: Optional[str] = None,
    json_mode: bool = True,
    timeout: int = 90,
    num_retries: int = 2,
    fallback_key: Optional[str] = None,
    fallback_model: Optional[str] = None,
    fallback_provider: Optional[str] = None,
    fallback_base_url: Optional[str] = None,
) -> Tuple[Dict[str, Any] | str, Dict[str, Any]]:
    """
    Invokes LiteLLM with the user's BYOK credentials.
    Returns:
        (parsed_output, metrics_dict)
        where metrics_dict contains: tokens_in, tokens_out, cost_usd, latency_ms, model_used
    """
    if provider.lower() == "nvidia":
        if not base_url:
            base_url = "https://integrate.api.nvidia.com/v1"
        validate_custom_base_url(base_url)

    if provider.lower() == "custom" and base_url:
        validate_custom_base_url(base_url)
        base_url = normalize_custom_base_url(base_url)

    target_model = format_model_for_provider(provider, model)
    kwargs: Dict[str, Any] = {
        "model": target_model,
        "messages": messages,
        "api_key": user_key,
        "timeout": timeout,
        "num_retries": num_retries,
    }

    if base_url:
        kwargs["api_base"] = base_url

    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    start_time = time.time()
    response = None
    last_error = None

    try:
        response = completion(**kwargs)
    except Exception as exc:
        last_error = exc
        logger.warning("Primary LLM call failed. Attempting fallback if configured...")

        # Fallback handling
        if fallback_key and fallback_model:
            fb_provider = fallback_provider or "openai"
            if fb_provider.lower() == "custom" and fallback_base_url:
                validate_custom_base_url(fallback_base_url)
                fallback_base_url = normalize_custom_base_url(fallback_base_url)

            fb_target_model = format_model_for_provider(fb_provider, fallback_model)
            fb_kwargs = {
                "model": fb_target_model,
                "messages": messages,
                "api_key": fallback_key,
                "timeout": timeout,
                "num_retries": num_retries,
            }
            if fallback_base_url:
                fb_kwargs["api_base"] = fallback_base_url
            if json_mode:
                fb_kwargs["response_format"] = {"type": "json_object"}

            try:
                response = completion(**fb_kwargs)
                target_model = fb_target_model
            except Exception as fb_exc:
                logger.error("Fallback LLM call also failed.")
                # Never include user key in error message
                err_msg = str(fb_exc)
                if user_key in err_msg or (fallback_key and fallback_key in err_msg):
                    err_msg = "[Redacted error: authentication failed]"
                raise RuntimeError(f"LLM call failed (primary & fallback): {err_msg}") from None
        else:
            err_msg = str(last_error)
            if "Invalid proxy server token passed" in err_msg or "Authentication Error" in err_msg:
                err_msg = "API Key tidak valid atau salah dimasukkan. Pastikan Anda menyalin seluruh key dari dashboard SumoPod (format: sk-...)."
            elif user_key in err_msg:
                err_msg = "[Authentication failed: invalid API key]"
            raise RuntimeError(f"LLM call failed: {err_msg}") from None

    latency_ms = int((time.time() - start_time) * 1000)

    # Extract usage metrics
    usage = getattr(response, "usage", None)
    tokens_in = getattr(usage, "prompt_tokens", 0) if usage else 0
    tokens_out = getattr(usage, "completion_tokens", 0) if usage else 0

    try:
        cost = completion_cost(completion_response=response)
    except Exception:
        cost = 0.0

    raw_content = ""
    if response and getattr(response, "choices", None) and len(response.choices) > 0:
        msg = response.choices[0].message
        raw_content = getattr(msg, "content", "") or ""
        # Support reasoning models (DeepSeek-R1 / NVIDIA Nemotron thinking)
        if not raw_content and hasattr(msg, "reasoning_content"):
            raw_content = getattr(msg, "reasoning_content", "") or ""

    parsed_result: Dict[str, Any] | str = raw_content
    if json_mode:
        try:
            parsed_result = json.loads(raw_content)
        except json.JSONDecodeError:
            # Try to strip markdown code blocks if LLM wrapped JSON in ```json ... ```
            cleaned = raw_content.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned = "\n".join(lines).strip()
            try:
                parsed_result = json.loads(cleaned)
            except Exception:
                parsed_result = {"raw_response": raw_content}

    metrics = {
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": float(cost or 0.0),
        "latency_ms": latency_ms,
        "model_used": target_model,
    }

    return parsed_result, metrics
