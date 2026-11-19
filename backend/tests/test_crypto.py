import pytest
from app.core.crypto import encrypt_api_key, decrypt_api_key, create_key_hint

def test_encryption_and_decryption_cycle():
    raw_key = "sk-proj-1234567890abcdefghijklmnopqrstuvwxyz"
    encrypted = encrypt_api_key(raw_key)

    assert encrypted != raw_key
    assert isinstance(encrypted, str)

    decrypted = decrypt_api_key(encrypted)
    assert decrypted == raw_key

def test_empty_key_fails():
    with pytest.raises(ValueError, match="cannot be empty"):
        encrypt_api_key("")

    with pytest.raises(ValueError, match="cannot be empty"):
        decrypt_api_key("")

def test_tampered_key_fails():
    with pytest.raises(ValueError, match="invalid token"):
        decrypt_api_key("invalid_corrupted_token_string")

def test_create_key_hint():
    hint = create_key_hint("sk-1234567890abcdef")
    assert hint == "...cdef"

    short_hint = create_key_hint("abc")
    assert short_hint == "...abc"
