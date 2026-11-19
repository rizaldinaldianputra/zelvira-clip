import pytest
from unittest.mock import patch, MagicMock
from app.core.llm import validate_custom_base_url, call_llm

def test_ssrf_blocks_localhost_and_private_ips():
    dangerous_urls = [
        "http://localhost:8000/v1",
        "http://127.0.0.1:11434/v1",
        "http://10.0.0.1:8080",
        "http://172.16.0.5:8000",
        "http://192.168.1.1:5000",
        "http://169.254.169.254/latest/meta-data",
        "ftp://external.com",
    ]

    for url in dangerous_urls:
        with pytest.raises(ValueError):
            validate_custom_base_url(url)

def test_ssrf_allows_public_urls():
    # Should not raise
    validate_custom_base_url("https://api.together.xyz/v1")
    validate_custom_base_url("https://openrouter.ai/api/v1")

@patch("app.core.llm.completion")
def test_call_llm_with_mock(mock_completion):
    # Mock LiteLLM completion response
    mock_resp = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = '{"moments": [{"start_sec": 10.0, "end_sec": 45.0, "score": 9.0}]}'
    mock_resp.choices = [mock_choice]
    mock_resp.usage.prompt_tokens = 150
    mock_resp.usage.completion_tokens = 50
    mock_completion.return_value = mock_resp

    res, metrics = call_llm(
        user_key="sk-test-key",
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "find highlights"}],
        provider="openai",
        json_mode=True
    )

    assert isinstance(res, dict)
    assert "moments" in res
    assert metrics["tokens_in"] == 150
    assert metrics["tokens_out"] == 50
    assert "latency_ms" in metrics
