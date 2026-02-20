"""
Source 5 — Webmaster Dashboard (GSC + Bing)

Provides:
    1. OAuth Redirect Trap (handles ?code=...&state=... callback)
    2. 2-column credential UI — inline on the main panel (no sidebar dependency)
       - Google: Client ID + Client Secret → OAuth flow → GSC property selectbox
       - Bing:   API Key → Bing Webmaster API → verified site selectbox
    3. Analysis tabs triggered by the selected domain dropdowns

Redirect URI is controlled by OAUTH_REDIRECT_BASE env var:
    - Local dev:   http://localhost:8501  (default, no env var needed)
    - Production:  https://auto-pilot.zeabur.app  (set in Zeabur Variables)

Called from app.py via:
    from V2_Engine.dashboard.webmaster_page import render_webmaster_page
    render_webmaster_page()
"""

import logging
import os

import requests
import streamlit as st

logger = logging.getLogger(__name__)

# Allow HTTP redirects for localhost dev (Google OAuth requires HTTPS in prod)
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

# Single source of truth for the redirect base — read once at import time
_REDIRECT_BASE = os.getenv("OAUTH_REDIRECT_BASE", "http://localhost:8501")


# ===========================================================================
#  MAIN ENTRY POINT
# ===========================================================================

def render_webmaster_page():
    """Main entry point — called by app.py when nav == 'Webmaster'."""

    from V2_Engine.saas_core.db.database import Database
    from V2_Engine.saas_core.auth.oauth_manager import OAuthManager

    # ── Session guards ──────────────────────────────────────────────────
    if "user_id" not in st.session_state:
        st.error("No user session. Please restart the app.")
        return

    db: Database = st.session_state.get("_webmaster_db")
    if db is None:
        db = Database()
        st.session_state["_webmaster_db"] = db

    user_id: str = st.session_state["user_id"]
    oauth = OAuthManager(db, user_id)

    # ── OAuth redirect trap (must run BEFORE any UI is drawn) ───────────
    _handle_oauth_callback(db, oauth, user_id)

    # ── Page header ─────────────────────────────────────────────────────
    st.header("Webmaster — SEO & GEO Analytics")
    st.caption(
        "Enter your credentials below to connect Google Search Console "
        "and Bing Webmaster, then select a verified property to run analysis."
    )

    # ── 2-column credential UI ──────────────────────────────────────────
    col_google, col_bing = st.columns(2)

    with col_google:
        _render_google_section(db, oauth, user_id)

    with col_bing:
        _render_bing_section(db, user_id)

    st.divider()

    # ── Analysis gate: require at least one selected domain ─────────────
    google_site = st.session_state.get("selected_google_site")
    bing_site = st.session_state.get("selected_bing_site")

    if not google_site and not bing_site:
        st.info("Select a verified property from the dropdowns above to unlock analysis.")
        return

    # ── Analysis tabs ───────────────────────────────────────────────────
    tab_gsc, tab_bing_tab = st.tabs(["Google Search Console", "Bing Webmaster"])

    with tab_gsc:
        if google_site:
            st.success(f"Active property: `{google_site}`")
            st.info("GSC analysis engine will be wired in Phase D.")
        else:
            st.info("Connect Google Search Console above to begin.")

    with tab_bing_tab:
        if bing_site:
            st.success(f"Active site: `{bing_site}`")
            st.info("Bing analysis engine will be wired in Phase D.")
        else:
            st.info("Connect Bing Webmaster above to begin.")


# ===========================================================================
#  GOOGLE SECTION
# ===========================================================================

def _render_google_section(db, oauth, user_id: str):
    """Credential form + OAuth flow + GSC property selectbox."""

    st.subheader("Google Search Console")

    has_creds = oauth.has_credentials("google")

    # ── Pre-populate Client ID from DB into session state ────────────────
    # This runs only when the key doesn't exist (fresh page load / first visit).
    # Prevents the field from blanking out after a save+rerun cycle.
    if "wm_google_client_id" not in st.session_state and has_creds:
        saved = db.get_api_credentials(user_id, "google") or {}
        st.session_state["wm_google_client_id"] = saved.get("client_id", "")

    # ── Credential inputs ────────────────────────────────────────────────
    expander_label = (
        "OAuth App Credentials — ✅ Saved" if has_creds
        else "OAuth App Credentials — ⚠️ Not configured"
    )
    with st.expander(expander_label, expanded=not has_creds):
        g_id = st.text_input(
            "Client ID",
            key="wm_google_client_id",
            placeholder="123456789-abc.apps.googleusercontent.com",
        )
        g_secret = st.text_input(
            "Client Secret",
            key="wm_google_client_secret",
            type="password",
            placeholder=(
                "Leave blank to keep existing secret"
                if has_creds else "GOCSPX-..."
            ),
        )
        if st.button("Save Google Credentials", key="wm_save_google"):
            if not g_id.strip():
                st.warning("Client ID is required.")
            else:
                # If secret is blank and credentials already exist, keep the
                # existing secret rather than overwriting with an empty string.
                if g_secret.strip():
                    secret_to_save = g_secret.strip()
                elif has_creds:
                    existing = db.get_api_credentials(user_id, "google") or {}
                    secret_to_save = existing.get("client_secret", "")
                else:
                    secret_to_save = ""

                if not secret_to_save:
                    st.warning("Client Secret is required for a new credential.")
                else:
                    db.save_api_credentials(
                        user_id, "google",
                        g_id.strip(), secret_to_save,
                        redirect_uri=_REDIRECT_BASE,   # ← persisted to DB
                    )
                    st.toast("Google credentials saved.", icon="✅")
                    st.rerun()

    # ── Nothing to do without credentials ───────────────────────────────
    if not oauth.has_credentials("google"):
        st.info("Enter your Google OAuth credentials above to enable sign-in.")
        return

    # ── Connected: show property dropdown ────────────────────────────────
    if oauth.is_connected("google"):
        st.success("Connected")

        # Fetch and cache verified properties (avoid hitting API every render)
        if "google_sites" not in st.session_state:
            with st.spinner("Fetching verified properties..."):
                st.session_state["google_sites"] = _fetch_gsc_sites(oauth)

        sites = st.session_state.get("google_sites", [])

        if sites:
            st.selectbox(
                "Verified Property",
                options=sites,
                key="selected_google_site",
            )
        else:
            st.warning("No verified properties found in this account.")
            if st.button("Retry", key="retry_gsc"):
                st.session_state.pop("google_sites", None)
                st.rerun()

        if st.button("Disconnect Google", key="dc_google"):
            oauth.disconnect("google")
            st.session_state.pop("google_sites", None)
            st.session_state.pop("selected_google_site", None)
            st.rerun()

    # ── Not connected: show Sign In button ───────────────────────────────
    else:
        st.warning("Not connected")
        if st.button("Sign in with Google", key="cn_google", type="primary"):
            try:
                # Pass _REDIRECT_BASE explicitly so auth URL and callback
                # flow both use the same URI (fixes token exchange mismatch).
                auth_url = oauth.get_google_auth_url(redirect_uri=_REDIRECT_BASE)
                st.markdown(f"[Authorize Google Search Console]({auth_url})")
            except Exception as e:
                st.error(f"Failed to generate auth URL: {e}")


# ===========================================================================
#  BING SECTION
# ===========================================================================

def _render_bing_section(db, user_id: str):
    """API key form + Bing Webmaster site selectbox (no OAuth)."""

    st.subheader("Bing Webmaster")

    has_key = db.has_credential(user_id, "bing", "api_key")

    # ── API key input ────────────────────────────────────────────────────
    expander_label = (
        "API Key — ✅ Saved" if has_key
        else "API Key — ⚠️ Not configured"
    )
    with st.expander(expander_label, expanded=not has_key):
        bing_key = st.text_input(
            "Bing Webmaster API Key",
            key="wm_bing_api_key",
            type="password",
            placeholder=(
                "Leave blank to keep existing key"
                if has_key else "Paste your Bing Webmaster API key here"
            ),
        )
        if st.button("Save Bing Credentials", key="wm_save_bing"):
            if bing_key.strip():
                db.save_credential(
                    user_id, "bing", "api_key",
                    {"api_key": bing_key.strip()},
                )
                st.session_state.pop("bing_sites", None)   # force re-fetch
                st.toast("Bing API key saved.", icon="✅")
                st.rerun()
            elif has_key:
                # No new key entered and one already exists — nothing to do
                st.info("Existing key is still active.")
            else:
                st.warning("API key cannot be empty.")

    # ── Nothing to do without a key ──────────────────────────────────────
    if not has_key:
        st.info("Enter your Bing API key above to begin.")
        return

    st.success("API Key configured")

    # ── Fetch and cache verified sites (Bing live API, not localhost) ────
    if "bing_sites" not in st.session_state:
        cred = db.get_credential(user_id, "bing", "api_key")
        api_key = (cred or {}).get("api_key", "")
        with st.spinner("Fetching verified sites..."):
            st.session_state["bing_sites"] = _fetch_bing_sites(api_key)

    sites = st.session_state.get("bing_sites", [])

    if sites:
        st.selectbox(
            "Verified Site",
            options=sites,
            key="selected_bing_site",
        )
    else:
        st.warning("No verified sites found. Check your API key.")
        if st.button("Retry", key="retry_bing"):
            st.session_state.pop("bing_sites", None)
            st.rerun()

    if st.button("Remove Bing Key", key="dc_bing"):
        db.delete_credential(user_id, "bing", "api_key")
        st.session_state.pop("bing_sites", None)
        st.session_state.pop("selected_bing_site", None)
        st.rerun()


# ===========================================================================
#  PRIVATE HELPERS
# ===========================================================================

def _handle_oauth_callback(db, oauth, user_id: str):
    """
    OAuth Redirect Trap — parse ?code=...&state=... from URL query params.
    Must run before any UI is drawn so the rerun lands on a clean page.

    The redirect_uri passed to callback_google must match the one used
    when the auth URL was generated (both come from _REDIRECT_BASE).
    """
    params = st.query_params
    code = params.get("code")
    state = params.get("state")

    if not code or not state:
        return

    try:
        state_data = db.consume_oauth_state(state)
        if not state_data:
            st.error("OAuth callback failed: invalid or expired state token.")
            st.query_params.clear()
            return

        provider = state_data["provider"]
        callback_user = state_data["user_id"]

        if provider == "google":
            # Re-save state so callback_google() can re-validate it internally
            db.save_oauth_state(state, callback_user, "google")
            # Reconstruct the exact redirect URI Google sent the user back to.
            # Must use _REDIRECT_BASE so it matches the auth URL that was generated.
            redirect_uri = f"{_REDIRECT_BASE}/?code={code}&state={state}"
            oauth.callback_google(redirect_uri)
            st.session_state.pop("google_sites", None)   # force site re-fetch
            st.success("Connected to Google Search Console!")

        elif provider == "bing":
            db.save_oauth_state(state, callback_user, "bing")
            oauth.callback_bing(code, state)
            st.success("Connected to Bing Webmaster!")

        st.query_params.clear()
        st.rerun()

    except (ValueError, ConnectionError) as e:
        logger.exception("OAuth callback error")
        st.error(f"OAuth error: {e}")
        st.query_params.clear()


def _fetch_gsc_sites(oauth) -> list[str]:
    """
    Fetch the user's verified properties from Google Search Console.
    Returns a list of site URL strings, or [] on any failure.
    """
    try:
        from googleapiclient.discovery import build
        creds = oauth.google_get_credentials()
        service = build("webmasters", "v3", credentials=creds)
        response = service.sites().list().execute()
        return [s["siteUrl"] for s in response.get("siteEntry", [])]
    except Exception as e:
        logger.warning(f"GSC site fetch failed: {e}")
        return []


def _fetch_bing_sites(api_key: str) -> list[str]:
    """
    Fetch verified sites from the Bing Webmaster live API using an API key.
    Endpoint: https://api.webmaster.live.com/webmaster/api.svc/json/GetUserSites
    Returns a list of site URL strings, or [] on any failure.
    """
    if not api_key:
        return []
    try:
        url = "https://api.webmaster.live.com/webmaster/api.svc/json/GetUserSites"
        resp = requests.get(url, params={"apikey": api_key}, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return [s["Url"] for s in data.get("d", [])]
        logger.warning(
            f"Bing Webmaster API returned {resp.status_code}: {resp.text[:200]}"
        )
        return []
    except Exception as e:
        logger.warning(f"Bing site fetch failed: {e}")
        return []
