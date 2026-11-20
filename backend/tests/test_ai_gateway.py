import pytest
from unittest.mock import patch, MagicMock
from app.core.crypto import encrypt_api_key, decrypt_api_key, create_key_hint
from app.core.llm import validate_custom_base_url
from app.core.llm_gateway import format_gateway_model, MODEL_REGISTRY, execute_gateway_completion

def test_credential_encryption_and_hint():
    secret_key = "sk-proj-supersecret123456789"
    encrypted = encrypt_api_key(secret_key)
    assert encrypted != secret_key

    decrypted = decrypt_api_key(encrypted)
    assert decrypted == secret_key

    hint = create_key_hint(secret_key)
    assert hint.startswith("sk-p")
    assert hint.endswith("6789")
    assert "..." in hint

def test_model_formatting_per_provider():
    assert format_gateway_model("openai", "gpt-4o") == "openai/gpt-4o"
    assert format_gateway_model("anthropic", "claude-3-5-sonnet") == "anthropic/claude-3-5-sonnet"
    assert format_gateway_model("gemini", "gemini-1.5-flash") == "gemini/gemini-1.5-flash"
    assert format_gateway_model("deepseek", "deepseek-chat") == "deepseek/deepseek-chat"
    assert format_gateway_model("mistral", "mistral-large") == "mistral/mistral-large"
    assert format_gateway_model("nvidia", "meta/llama-3.1-70b-instruct") == "meta/llama-3.1-70b-instruct"

def test_model_registry_contains_required_providers():
    providers = {m.provider for m in MODEL_REGISTRY}
    assert "openai" in providers
    assert "anthropic" in providers
    assert "gemini" in providers
    assert "nvidia" in providers
    assert "deepseek" in providers
    assert "mistral" in providers
    assert "custom" in providers

def test_ssrf_prevention():
    with pytest.raises(ValueError):
        validate_custom_base_url("http://127.0.0.1:8000/v1")
    with pytest.raises(ValueError):
        validate_custom_base_url("http://localhost:11434")
    with pytest.raises(ValueError):
        validate_custom_base_url("http://169.254.169.254/latest/meta-data")

@patch("app.core.llm_gateway.completion")
def test_execute_gateway_completion_success(mock_completion):
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Halo dari AI Gateway!"
    mock_resp.choices = [mock_choice]
    mock_resp.usage.prompt_tokens = 20
    mock_resp.usage.completion_tokens = 10

    mock_completion.return_value = mock_resp

    resp, metrics = execute_gateway_completion(
        api_key="sk-test-key",
        provider="anthropic",
        model="claude-3-5-sonnet-latest",
        messages=[{"role": "user", "content": "Hello"}],
    )

    assert resp.choices[0].message.content == "Halo dari AI Gateway!"
    assert metrics["tokens_in"] == 20
    assert metrics["tokens_out"] == 10
    assert metrics["total_tokens"] == 30
    assert "latency_ms" in metrics
