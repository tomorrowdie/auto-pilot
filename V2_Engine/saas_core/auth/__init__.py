"""SaaS Core — Auth module (V6 BYOK)."""
from .security import encrypt, decrypt, get_fernet, generate_key
from .oauth_manager import OAuthManager
from .auth_manager import AuthManager

# Singleton — import this in app.py and all page modules
auth_manager = AuthManager()

__all__ = [
    "encrypt", "decrypt", "get_fernet", "generate_key",
    "OAuthManager",
    "AuthManager",
    "auth_manager",
]
