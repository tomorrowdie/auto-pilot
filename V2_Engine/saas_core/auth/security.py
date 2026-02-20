"""
SaaS Core — Security & Encryption Utilities

Handles Fernet key management for encrypting OAuth tokens and API credentials.
Ported from _archive/009-GSC-SAAS auth/oauth.py encryption logic.

Usage:
    from V2_Engine.saas_core.auth.security import get_fernet, encrypt, decrypt

Key Management:
    - TOKEN_ENC_KEY must be set in .env for production.
    - If missing, a dev-mode warning is logged and values pass through unencrypted.
    - NEVER rotate TOKEN_ENC_KEY without migrating existing encrypted data.
"""
import os
import logging

logger = logging.getLogger(__name__)

_fernet_instance = None
_initialized = False


def get_fernet():
    """
    Return a Fernet instance from TOKEN_ENC_KEY env var.
    Returns None if the key is not set (dev mode — no encryption).
    Caches the instance after first call.
    """
    global _fernet_instance, _initialized

    if _initialized:
        return _fernet_instance

    _initialized = True
    key = os.environ.get("TOKEN_ENC_KEY", "")

    if not key:
        logger.warning(
            "TOKEN_ENC_KEY not set — encryption DISABLED. "
            "Tokens and secrets will be stored in PLAINTEXT. "
            "Set TOKEN_ENC_KEY in .env for production."
        )
        _fernet_instance = None
        return None

    try:
        from cryptography.fernet import Fernet
        _fernet_instance = Fernet(key.encode() if isinstance(key, str) else key)
        logger.info("Fernet encryption initialized successfully.")
        return _fernet_instance
    except ImportError:
        logger.warning(
            "cryptography package not installed — encryption DISABLED. "
            "Run: pip install cryptography"
        )
        _fernet_instance = None
        return None
    except Exception as e:
        logger.warning("Failed to initialize Fernet: %s — encryption DISABLED.", e)
        _fernet_instance = None
        return None


def encrypt(plaintext: str) -> str:
    """Encrypt a string. Returns plaintext unchanged if Fernet is unavailable."""
    f = get_fernet()
    if f is None:
        return plaintext
    return f.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a string. Returns ciphertext unchanged if Fernet is unavailable."""
    f = get_fernet()
    if f is None:
        return ciphertext
    return f.decrypt(ciphertext.encode()).decode()


def generate_key() -> str:
    """
    Generate a new Fernet key (base64-encoded string).
    Use this to create a TOKEN_ENC_KEY for .env.
    """
    from cryptography.fernet import Fernet
    return Fernet.generate_key().decode()
