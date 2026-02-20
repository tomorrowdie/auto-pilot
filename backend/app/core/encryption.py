"""
Encryption utilities for sensitive data like API tokens
Uses Fernet (symmetric encryption) from cryptography library
"""

import logging
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

from app.core.config import settings

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Custom exception for encryption errors"""
    pass


class TokenEncryption:
    """
    Handles encryption and decryption of sensitive tokens using Fernet
    Uses the SECRET_KEY from settings as the encryption key
    """

    def __init__(self):
        """Initialize encryption with SECRET_KEY from settings"""
        self._cipher = self._initialize_cipher()

    def _initialize_cipher(self) -> Fernet:
        """
        Initialize Fernet cipher with SECRET_KEY

        Returns:
            Fernet cipher instance
        """
        try:
            secret_key = settings.SECRET_KEY

            if not secret_key or len(secret_key) < 16:
                raise EncryptionError("SECRET_KEY is not configured or too short")

            # Derive a 32-byte key from SECRET_KEY using PBKDF2
            # This ensures consistent encryption/decryption
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'shopify_seo_analyzer',  # Static salt for consistency
                iterations=100000,
            )

            key_bytes = kdf.derive(secret_key.encode())
            key_b64 = base64.urlsafe_b64encode(key_bytes)

            cipher = Fernet(key_b64)
            logger.info("Encryption cipher initialized successfully")
            return cipher

        except Exception as e:
            logger.error(f"Failed to initialize encryption cipher: {e}")
            raise EncryptionError(f"Encryption initialization failed: {e}")

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string

        Args:
            plaintext: String to encrypt

        Returns:
            Encrypted string (bytes encoded as UTF-8)
        """
        try:
            if not plaintext:
                raise EncryptionError("Cannot encrypt empty string")

            encrypted_bytes = self._cipher.encrypt(plaintext.encode())
            return encrypted_bytes.decode('utf-8')

        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise EncryptionError(f"Failed to encrypt data: {e}")

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext string

        Args:
            ciphertext: Encrypted string to decrypt

        Returns:
            Decrypted plaintext string
        """
        try:
            if not ciphertext:
                raise EncryptionError("Cannot decrypt empty string")

            decrypted_bytes = self._cipher.decrypt(ciphertext.encode())
            return decrypted_bytes.decode('utf-8')

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise EncryptionError(f"Failed to decrypt data: {e}")

    def encrypt_token(self, token: str) -> str:
        """
        Encrypt an API token

        Args:
            token: API token to encrypt

        Returns:
            Encrypted token
        """
        return self.encrypt(token)

    def decrypt_token(self, encrypted_token: str) -> Optional[str]:
        """
        Decrypt an API token

        Args:
            encrypted_token: Encrypted token

        Returns:
            Decrypted token or None if decryption fails
        """
        try:
            return self.decrypt(encrypted_token)
        except EncryptionError:
            return None


# Global encryption instance
encryption = TokenEncryption()


def encrypt_token(token: str) -> str:
    """
    Convenience function to encrypt a token

    Args:
        token: Token to encrypt

    Returns:
        Encrypted token
    """
    return encryption.encrypt_token(token)


def decrypt_token(encrypted_token: str) -> Optional[str]:
    """
    Convenience function to decrypt a token

    Args:
        encrypted_token: Encrypted token

    Returns:
        Decrypted token or None if decryption fails
    """
    return encryption.decrypt_token(encrypted_token)
