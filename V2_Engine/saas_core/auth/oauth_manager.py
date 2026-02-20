"""
SaaS Core — BYOK OAuth2 Manager

Handles Google (via google-auth-oauthlib) and Bing (manual flow) authentication.
Tokens are persisted in SQLite via Database.

CRITICAL CHANGE from 009: No .env lookups. All client credentials come from
    db.get_api_credentials(user_id, provider)

Ported from: _archive/009-GSC-SAAS/auth/oauth.py
"""
import os
import secrets
import time
import logging
import urllib.parse

import requests
from google_auth_oauthlib.flow import Flow as GoogleFlow

from V2_Engine.saas_core.db.database import Database

logger = logging.getLogger(__name__)

# ── Bing OAuth Endpoints ──────────────────────
_BING_AUTHORIZE_URL = "https://www.bing.com/webmasters/oauth/authorize"
_BING_TOKEN_URL = "https://www.bing.com/webmasters/oauth/token"

# ── Google OAuth Constants ────────────────────
_GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
]
_DEFAULT_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_BASE", "http://localhost:8501")


class OAuthManager:
    """BYOK OAuth2 manager — credentials loaded from the database, not .env."""

    def __init__(self, db: Database, user_id: str):
        self.db = db
        self.user_id = user_id

    # ══════════════════════════════════════════
    #  CREDENTIAL LOOKUP (BYOK)
    # ══════════════════════════════════════════

    def _get_creds(self, provider: str) -> dict:
        """
        Fetch client_id, client_secret, redirect_uri from the DB.
        Raises ValueError if the user has not configured credentials for this provider.
        """
        creds = self.db.get_api_credentials(self.user_id, provider)
        if not creds:
            raise ValueError(
                f"No API credentials found for user '{self.user_id}', provider '{provider}'. "
                f"Please save your Client ID / Secret first."
            )
        return creds

    # ══════════════════════════════════════════
    #  GOOGLE  (via google-auth-oauthlib)
    # ══════════════════════════════════════════

    def _google_flow(self, redirect_uri: str | None = None) -> GoogleFlow:
        """Create a Google OAuth flow using DB-stored credentials."""
        creds = self._get_creds("google")
        _redirect = redirect_uri or creds.get("redirect_uri") or _DEFAULT_REDIRECT_URI
        client_config = {
            "web": {
                "client_id": creds["client_id"],
                "client_secret": creds["client_secret"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [_redirect],
            }
        }
        flow = GoogleFlow.from_client_config(
            client_config,
            scopes=_GOOGLE_SCOPES,
            redirect_uri=_redirect,
        )
        return flow

    def get_google_auth_url(self, redirect_uri: str | None = None) -> str:
        """
        Generate the Google OAuth authorization URL.
        Stores a CSRF state token in the DB.
        """
        flow = self._google_flow(redirect_uri)
        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        self.db.save_oauth_state(state, self.user_id, "google")
        return auth_url

    def callback_google(self, full_callback_url: str) -> dict:
        """
        Process the Google OAuth callback.
        Exchanges the auth code for tokens and saves them.

        Returns: {"user_id": ..., "provider": "google"} on success.
        Raises ValueError on CSRF mismatch or exchange failure.
        """
        parsed = urllib.parse.urlparse(full_callback_url)
        params = urllib.parse.parse_qs(parsed.query)

        state = params.get("state", [None])[0]
        if not state:
            raise ValueError("Missing 'state' parameter in callback URL")

        state_data = self.db.consume_oauth_state(state)
        if not state_data:
            raise ValueError("Invalid or expired OAuth state (CSRF check failed)")

        user_id = state_data["user_id"]

        flow = self._google_flow()
        flow.fetch_token(authorization_response=full_callback_url)
        credentials = flow.credentials

        self.db.save_token(
            user_id=user_id,
            provider="google",
            access_token=credentials.token,
            refresh_token=credentials.refresh_token or "",
            expires_in=int((credentials.expiry.timestamp() - time.time())) if credentials.expiry else 3600,
            scope=" ".join(credentials.scopes) if credentials.scopes else None,
        )

        self.db.upsert_user(user_id)
        logger.info("Google OAuth completed for user %s", user_id)
        return {"user_id": user_id, "provider": "google"}

    def google_get_credentials(self):
        """
        Return a google.oauth2.credentials.Credentials object for API calls.
        Auto-refreshes if expired.
        """
        from google.oauth2.credentials import Credentials

        token_data = self.db.get_token(self.user_id, "google")
        if not token_data:
            return None

        creds_db = self._get_creds("google")

        creds = Credentials(
            token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=creds_db["client_id"],
            client_secret=creds_db["client_secret"],
            scopes=_GOOGLE_SCOPES,
        )

        if self.db.token_is_expired(self.user_id, "google"):
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            expires_in = int((creds.expiry.timestamp() - time.time())) if creds.expiry else 3600
            self.db.update_access_token(self.user_id, "google", creds.token, expires_in)
            logger.info("Google token refreshed for user %s", self.user_id)

        return creds

    # ══════════════════════════════════════════
    #  BING  (manual OAuth2 flow via requests)
    # ══════════════════════════════════════════

    def get_bing_auth_url(self) -> str:
        """
        Generate the Bing Webmaster OAuth authorization URL.
        Stores a CSRF state token in the DB.
        """
        creds = self._get_creds("bing")
        state = secrets.token_urlsafe(24)
        self.db.save_oauth_state(state, self.user_id, "bing")

        params = {
            "client_id": creds["client_id"],
            "response_type": "code",
            "redirect_uri": creds.get("redirect_uri") or _DEFAULT_REDIRECT_URI,
            "scope": "Webmaster.read",
            "state": state,
        }
        return _BING_AUTHORIZE_URL + "?" + urllib.parse.urlencode(params)

    def callback_bing(self, code: str, state: str) -> dict:
        """
        Process the Bing OAuth callback.
        Exchanges the auth code for tokens and saves them.

        Returns: {"user_id": ..., "provider": "bing"} on success.
        Raises ValueError on CSRF mismatch or exchange failure.
        """
        state_data = self.db.consume_oauth_state(state)
        if not state_data:
            raise ValueError("Invalid or expired OAuth state (CSRF check failed)")

        user_id = state_data["user_id"]
        creds = self._get_creds("bing")

        data = {
            "code": code,
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "redirect_uri": creds.get("redirect_uri") or _DEFAULT_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        resp = requests.post(_BING_TOKEN_URL, data=data, timeout=30)
        if resp.status_code != 200:
            raise ValueError(f"Bing token exchange failed ({resp.status_code}): {resp.text}")

        tok = resp.json()

        self.db.save_token(
            user_id=user_id,
            provider="bing",
            access_token=tok["access_token"],
            refresh_token=tok.get("refresh_token", ""),
            expires_in=int(tok.get("expires_in", 3600)),
        )

        self.db.upsert_user(user_id)
        logger.info("Bing OAuth completed for user %s", user_id)
        return {"user_id": user_id, "provider": "bing"}

    def bing_get_access_token(self) -> str | None:
        """
        Return a valid Bing access token. Auto-refreshes if expired.
        Returns None if user has no Bing connection.
        """
        token_data = self.db.get_token(self.user_id, "bing")
        if not token_data:
            return None

        if not self.db.token_is_expired(self.user_id, "bing"):
            return token_data["access_token"]

        # Refresh
        refresh_token = token_data["refresh_token"]
        if not refresh_token:
            logger.warning("No refresh token for Bing user %s — re-auth needed", self.user_id)
            return None

        creds = self._get_creds("bing")

        data = {
            "client_id": creds["client_id"],
            "client_secret": creds["client_secret"],
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        resp = requests.post(_BING_TOKEN_URL, data=data, timeout=30)
        if resp.status_code != 200:
            logger.error("Bing token refresh failed for user %s: %s", self.user_id, resp.text)
            return None

        new_tok = resp.json()
        self.db.update_access_token(
            self.user_id, "bing",
            new_tok["access_token"],
            int(new_tok.get("expires_in", 3600)),
        )
        logger.info("Bing token refreshed for user %s", self.user_id)
        return new_tok["access_token"]

    # ══════════════════════════════════════════
    #  SHARED HELPERS
    # ══════════════════════════════════════════

    def is_connected(self, provider: str) -> bool:
        return self.db.is_connected(self.user_id, provider)

    def disconnect(self, provider: str):
        """Remove OAuth tokens for a provider (user must re-authenticate)."""
        self.db.delete_token(self.user_id, provider)
        logger.info("Disconnected %s for user %s", provider, self.user_id)

    def has_credentials(self, provider: str) -> bool:
        """Check if user has BYOK credentials configured for a provider."""
        return self.db.has_api_credentials(self.user_id, provider)

    def refresh_if_expired(self, provider: str) -> bool:
        """
        Check if token is expired and auto-refresh. Returns True if token is valid after check.
        This is the Token Refresh Service entry point.
        """
        if not self.is_connected(provider):
            return False

        if not self.db.token_is_expired(self.user_id, provider):
            return True

        if provider == "google":
            creds = self.google_get_credentials()
            return creds is not None
        elif provider == "bing":
            token = self.bing_get_access_token()
            return token is not None

        return False
