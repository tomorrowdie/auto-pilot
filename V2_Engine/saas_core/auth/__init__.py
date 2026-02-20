"""SaaS Core — Auth module (V5 Unified BYOK)."""
from .security import encrypt, decrypt, get_fernet, generate_key
from .oauth_manager import OAuthManager
from .registry import PROVIDER_SPECS, build_llm, get_all_models_flat, get_model_spec
from .auth_manager import AuthManager

# Singleton — import this in app.py and all page modules
auth_manager = AuthManager()

__all__ = [
    "encrypt", "decrypt", "get_fernet", "generate_key",
    "OAuthManager",
    "PROVIDER_SPECS", "build_llm", "get_all_models_flat", "get_model_spec",
    "AuthManager",
    "auth_manager",
]
