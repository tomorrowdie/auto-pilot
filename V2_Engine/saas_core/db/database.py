"""
SaaS Core — Unified Vault Database (V5)

Single table `unified_credentials` stores all credential types:
  credential_type='api_key'     — LLM API keys (Gemini, OpenAI, etc.)
  credential_type='oauth_app'   — OAuth2 Client ID/Secret (GSC, Bing)
  credential_type='oauth_token' — OAuth2 Access/Refresh Tokens

Backward-compatible wrapper methods keep oauth_manager.py unchanged.

DB location: data/saas_user_data.db
"""
import json
import os
import sqlite3
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"
_PROJECT_ROOT = Path(__file__).resolve().parents[3]   # 008-Auto-Pilot/
_DEFAULT_DB_PATH = str(_PROJECT_ROOT / "data" / "saas_user_data.db")


def _load_fernet():
    """Load Fernet from env. Auto-generates + writes key if missing."""
    key = os.environ.get("TOKEN_ENC_KEY", "")
    if not key:
        try:
            from cryptography.fernet import Fernet
            new_key = Fernet.generate_key().decode()
            os.environ["TOKEN_ENC_KEY"] = new_key
            env_path = _PROJECT_ROOT / ".env"
            if env_path.exists():
                with open(env_path, "a", encoding="utf-8") as f:
                    f.write(f"\nTOKEN_ENC_KEY={new_key}\n")
                logger.info("TOKEN_ENC_KEY auto-generated and written to .env")
            else:
                logger.warning(
                    "TOKEN_ENC_KEY not set and no .env found. "
                    "Key is runtime-only and will change on restart."
                )
            return Fernet(new_key.encode())
        except ImportError:
            logger.warning("cryptography not installed — credentials stored unencrypted.")
            return None
    try:
        from cryptography.fernet import Fernet
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as e:
        logger.warning("Failed to initialize Fernet: %s", e)
        return None


class Database:
    """Unified SQLite vault — V5 schema with unified_credentials table."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or _DEFAULT_DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._fernet = _load_fernet()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    # ── Setup ──────────────────────────────────────────────────────────

    def _init_schema(self):
        schema_sql = _SCHEMA_PATH.read_text(encoding="utf-8")
        self.conn.executescript(schema_sql)
        self.conn.commit()

    # ── Encryption ─────────────────────────────────────────────────────

    def _encrypt(self, plaintext: str) -> str:
        if self._fernet is None:
            return plaintext
        return self._fernet.encrypt(plaintext.encode()).decode()

    def _decrypt(self, ciphertext: str) -> str:
        if self._fernet is None:
            return ciphertext
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except Exception:
            return ciphertext  # key changed — return raw

    # Legacy aliases (used by security.py)
    def encrypt(self, plaintext: str) -> str:
        return self._encrypt(plaintext)

    def decrypt(self, ciphertext: str) -> str:
        return self._decrypt(ciphertext)

    # ── Users ───────────────────────────────────────────────────────────

    def upsert_user(self, user_id: str, email: str | None = None):
        self.conn.execute(
            """INSERT INTO users (user_id, email) VALUES (?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                   email = COALESCE(excluded.email, email)""",
            (user_id, email),
        )
        self.conn.commit()

    def get_user(self, user_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None

    # ── Projects ────────────────────────────────────────────────────────

    def add_project(self, user_id: str, provider: str, site_url: str, label: str | None = None):
        self.conn.execute(
            """INSERT INTO projects (user_id, provider, site_url, label) VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id, provider, site_url) DO UPDATE SET
                   label = COALESCE(excluded.label, label)""",
            (user_id, provider, site_url, label),
        )
        self.conn.commit()

    def get_projects(self, user_id: str, provider: str | None = None) -> list[dict]:
        if provider:
            rows = self.conn.execute(
                "SELECT * FROM projects WHERE user_id = ? AND provider = ? ORDER BY created_at",
                (user_id, provider),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM projects WHERE user_id = ? ORDER BY provider, created_at",
                (user_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    def remove_project(self, user_id: str, provider: str, site_url: str):
        self.conn.execute(
            "DELETE FROM projects WHERE user_id = ? AND provider = ? AND site_url = ?",
            (user_id, provider, site_url),
        )
        self.conn.commit()

    # ── OAuth State (CSRF) ──────────────────────────────────────────────

    def save_oauth_state(self, state: str, user_id: str, provider: str):
        self.conn.execute(
            "INSERT INTO oauth_states (state, user_id, provider) VALUES (?, ?, ?)",
            (state, user_id, provider),
        )
        self.conn.commit()

    def consume_oauth_state(self, state: str) -> dict | None:
        row = self.conn.execute(
            "SELECT user_id, provider FROM oauth_states WHERE state = ?", (state,)
        ).fetchone()
        if not row:
            return None
        self.conn.execute("DELETE FROM oauth_states WHERE state = ?", (state,))
        self.conn.commit()
        return dict(row)

    # ════════════════════════════════════════════════════════════════════
    #  UNIFIED CREDENTIALS  (V5 Core API)
    # ════════════════════════════════════════════════════════════════════

    def save_credential(
        self,
        user_id: str,
        provider: str,
        credential_type: str,
        payload_dict: dict,
        meta_dict: dict | None = None,
    ) -> None:
        """Encrypt payload and upsert into unified_credentials."""
        encrypted = self._encrypt(json.dumps(payload_dict))
        meta_json = json.dumps(meta_dict) if meta_dict else None
        self.conn.execute(
            """INSERT INTO unified_credentials
                   (user_id, provider, credential_type, encrypted_payload, metadata)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(user_id, provider, credential_type) DO UPDATE SET
                   encrypted_payload = excluded.encrypted_payload,
                   metadata          = COALESCE(excluded.metadata, metadata),
                   is_active         = 1,
                   updated_at        = datetime('now')""",
            (user_id, provider, credential_type, encrypted, meta_json),
        )
        self.conn.commit()

    def get_credential(
        self, user_id: str, provider: str, credential_type: str
    ) -> dict | None:
        """Fetch and decrypt a credential. Returns the payload dict or None."""
        row = self.conn.execute(
            """SELECT encrypted_payload, metadata FROM unified_credentials
               WHERE user_id = ? AND provider = ? AND credential_type = ? AND is_active = 1""",
            (user_id, provider, credential_type),
        ).fetchone()
        if not row:
            return None
        try:
            payload = json.loads(self._decrypt(row["encrypted_payload"]))
        except (json.JSONDecodeError, Exception):
            return None
        if row["metadata"]:
            payload["_meta"] = json.loads(row["metadata"])
        return payload

    def delete_credential(
        self, user_id: str, provider: str, credential_type: str
    ) -> None:
        """Soft-delete a credential (sets is_active=0)."""
        self.conn.execute(
            """UPDATE unified_credentials
               SET is_active = 0, updated_at = datetime('now')
               WHERE user_id = ? AND provider = ? AND credential_type = ?""",
            (user_id, provider, credential_type),
        )
        self.conn.commit()

    def list_credentials(self, user_id: str) -> list[dict]:
        """List all active credentials (provider + type + metadata only — no decryption)."""
        rows = self.conn.execute(
            """SELECT provider, credential_type, metadata, updated_at
               FROM unified_credentials
               WHERE user_id = ? AND is_active = 1
               ORDER BY provider, credential_type""",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def has_credential(
        self, user_id: str, provider: str, credential_type: str
    ) -> bool:
        row = self.conn.execute(
            """SELECT 1 FROM unified_credentials
               WHERE user_id = ? AND provider = ? AND credential_type = ? AND is_active = 1""",
            (user_id, provider, credential_type),
        ).fetchone()
        return row is not None

    def wipe_all_credentials(self, user_id: str) -> None:
        """Security reset — soft-delete ALL credentials for a user."""
        self.conn.execute(
            "UPDATE unified_credentials SET is_active = 0 WHERE user_id = ?",
            (user_id,),
        )
        self.conn.commit()

    # ════════════════════════════════════════════════════════════════════
    #  BACKWARD-COMPAT WRAPPERS  (keeps oauth_manager.py unchanged)
    # ════════════════════════════════════════════════════════════════════

    # -- oauth_token --

    def save_token(
        self,
        user_id: str,
        provider: str,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        scope: str | None = None,
    ) -> None:
        payload = {
            "access_token":  access_token,
            "refresh_token": refresh_token,
            "expires_at":    int(time.time()) + expires_in,
            "scope":         scope,
        }
        self.save_credential(user_id, provider, "oauth_token", payload)

    def get_token(self, user_id: str, provider: str) -> dict | None:
        cred = self.get_credential(user_id, provider, "oauth_token")
        if not cred:
            return None
        return {
            "access_token":  cred.get("access_token", ""),
            "refresh_token": cred.get("refresh_token", ""),
            "expires_at":    cred.get("expires_at", 0),
            "scope":         cred.get("scope"),
        }

    def update_access_token(
        self, user_id: str, provider: str, access_token: str, expires_in: int
    ) -> None:
        existing = self.get_token(user_id, provider) or {}
        payload = {
            "access_token":  access_token,
            "refresh_token": existing.get("refresh_token", ""),
            "expires_at":    int(time.time()) + expires_in,
            "scope":         existing.get("scope"),
        }
        self.save_credential(user_id, provider, "oauth_token", payload)

    def delete_token(self, user_id: str, provider: str) -> None:
        self.delete_credential(user_id, provider, "oauth_token")

    def is_connected(self, user_id: str, provider: str) -> bool:
        return self.has_credential(user_id, provider, "oauth_token")

    def token_is_expired(
        self, user_id: str, provider: str, buffer_seconds: int = 30
    ) -> bool:
        cred = self.get_credential(user_id, provider, "oauth_token")
        if not cred:
            return True
        return cred.get("expires_at", 0) <= int(time.time()) + buffer_seconds

    # -- oauth_app --

    def save_api_credentials(
        self,
        user_id: str,
        provider: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str | None = None,
    ) -> None:
        payload = {
            "client_id":     client_id,
            "client_secret": client_secret,
            "redirect_uri":  redirect_uri,
        }
        self.save_credential(user_id, provider, "oauth_app", payload)

    def get_api_credentials(self, user_id: str, provider: str) -> dict | None:
        cred = self.get_credential(user_id, provider, "oauth_app")
        if not cred:
            return None
        return {
            "client_id":     cred.get("client_id", ""),
            "client_secret": cred.get("client_secret", ""),
            "redirect_uri":  cred.get("redirect_uri"),
        }

    def has_api_credentials(self, user_id: str, provider: str) -> bool:
        return self.has_credential(user_id, provider, "oauth_app")

    def delete_api_credentials(self, user_id: str, provider: str) -> None:
        self.delete_credential(user_id, provider, "oauth_app")

    # ── Cleanup ─────────────────────────────────────────────────────────

    def close(self):
        self.conn.close()
