from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings
from app.core.logging import logger

def _get_fernet() -> Fernet:
    secret = settings.KEY_ENCRYPTION_SECRET
    try:
        return Fernet(secret.encode() if isinstance(secret, str) else secret)
    except Exception as e:
        logger.error("Failed to initialize Fernet with KEY_ENCRYPTION_SECRET")
        raise ValueError("Invalid KEY_ENCRYPTION_SECRET configuration. Must be a 32-byte url-safe base64 key.") from None

def encrypt_api_key(plain_key: str) -> str:
    """
    Encrypts a user API key using Fernet.
    """
    if not plain_key or not plain_key.strip():
        raise ValueError("API key cannot be empty")
    fernet = _get_fernet()
    encrypted_bytes = fernet.encrypt(plain_key.strip().encode("utf-8"))
    return encrypted_bytes.decode("utf-8")

def decrypt_api_key(encrypted_key: str) -> str:
    """
    Decrypts an encrypted API key using Fernet.
    Raises ValueError if decryption fails, without leaking the key.
    """
    if not encrypted_key:
        raise ValueError("Encrypted key cannot be empty")
    fernet = _get_fernet()
    try:
        decrypted_bytes = fernet.decrypt(encrypted_key.encode("utf-8"))
        return decrypted_bytes.decode("utf-8")
    except InvalidToken:
        logger.error("Failed to decrypt user API key: InvalidToken")
        raise ValueError("Failed to decrypt API key: invalid token or secret key") from None
    except Exception as e:
        logger.error("Decryption error occurred")
        raise ValueError("Decryption failed") from None

def create_key_hint(plain_key: str) -> str:
    """
    Extracts the last 4 characters of an API key for safe display (e.g., '...a1b2').
    Never exposes more than 4 characters.
    """
    clean_key = plain_key.strip()
    if len(clean_key) <= 4:
        return f"...{clean_key}"
    return f"...{clean_key[-4:]}"
