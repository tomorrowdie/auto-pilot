"""
Source 5 — Webmaster Dashboard (GSC + Bing)

Provides:
    1. OAuth Redirect Trap (handles ?code=...&state=... callback)
    2. Connect / Disconnect buttons (dynamic per provider)
    3. Placeholder for future analysis tabs (GSC + Bing engines)

OAuth credentials (Client ID / Secret) are managed globally via
the "API Keys" expander in the sidebar (auth_manager V5).

Called from app.py via:
    from V2_Engine.dashboard.webmaster_page import render_webmaster_page
    render_webmaster_page()

Ported from: _archive/009-GSC-SAAS/app.py (refactored to BYOK pattern)
"""
import os
import logging

import streamlit as st

logger = logging.getLogger(__name__)

# Allow HTTP redirect for localhost dev (Google OAuth requires this)
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")


def render_webmaster_page():
    """Main entry point — called by app.py when nav == 'Webmaster'."""

    # Late imports to avoid circular / heavy import at module level
    from V2_Engine.saas_core.db.database import Database
    from V2_Engine.saas_core.auth.oauth_manager import OAuthManager

    # ── Session guards ────────────────────────
    if "user_id" not in st.session_state:
        st.error("No user session. Please restart the app.")
        return

    db: Database = st.session_state.get("_webmaster_db")
    if db is None:
        db = Database()
        st.session_state["_webmaster_db"] = db

    user_id: str = st.session_state["user_id"]
    oauth = OAuthManager(db, user_id)

    # ==================================================================
    # 1. OAUTH REDIRECT TRAP  (must be FIRST — before any UI)
    # ==================================================================
    _handle_oauth_callback(db, oauth, user_id)

    # ==================================================================
    # 2. PAGE HEADER
    # ==================================================================
    st.header("Webmaster — SEO & GEO Analytics")
    st.caption("Connect your Google Search Console and Bing Webmaster accounts to begin.")

    # ==================================================================
    # 3. PROVIDER CONNECTION STATUS + CONNECT / DISCONNECT
    # ==================================================================
    col_google, col_bing = st.columns(2)

    with col_google:
        _render_provider_section(oauth, "google", "Google Search Console")

    with col_bing:
        _render_provider_section(oauth, "bing", "Bing Webmaster")

    st.divider()

    # ==================================================================
    # 5. ANALYSIS PLACEHOLDER
    # ==================================================================
    google_connected = oauth.is_connected("google")
    bing_connected = oauth.is_connected("bing")

    if not google_connected and not bing_connected:
        st.info(
            "Connect at least one provider above to unlock analysis. "
            "First add your OAuth Client ID and Secret via the **API Keys** panel in the sidebar, "
            "then click the Sign In button here."
        )
        return

    tab_gsc, tab_bing = st.tabs(["Google Search Console", "Bing Webmaster"])

    with tab_gsc:
        if google_connected:
            st.success("Google Search Console is connected.")
            st.info("GSC analysis engine will be wired in Phase D.")
        else:
            st.info("Connect Google Search Console from above to begin.")

    with tab_bing:
        if bing_connected:
            st.success("Bing Webmaster is connected.")
            st.info("Bing GEO analysis engine will be wired in Phase D.")
        else:
            st.info("Connect Bing Webmaster from above to begin.")


# ======================================================================
#  PRIVATE HELPERS
# ======================================================================

def _handle_oauth_callback(db, oauth, user_id: str):
    """
    The Redirect Trap — parse ?code=...&state=... from URL query params.
    Routes to Google or Bing based on the stored state record in the DB.
    """
    params = st.query_params
    code = params.get("code")
    state = params.get("state")

    if not code or not state:
        return

    try:
        # Consume state to determine which provider this callback is for
        state_data = db.consume_oauth_state(state)
        if not state_data:
            st.error("OAuth callback failed: invalid or expired state token.")
            st.query_params.clear()
            return

        provider = state_data["provider"]
        callback_user = state_data["user_id"]

        if provider == "google":
            # Re-save state so callback_google() can consume it internally
            db.save_oauth_state(state, callback_user, "google")
            # Build the full callback URL that google-auth-oauthlib expects
            redirect_uri = f"http://localhost:8501/?code={code}&state={state}"
            oauth.callback_google(redirect_uri)
            st.success("Connected to Google Search Console!")

        elif provider == "bing":
            # Re-save state so callback_bing() can consume it internally
            db.save_oauth_state(state, callback_user, "bing")
            oauth.callback_bing(code, state)
            st.success("Connected to Bing Webmaster!")

        st.query_params.clear()
        st.rerun()

    except (ValueError, ConnectionError) as e:
        logger.exception("OAuth callback error")
        st.error(f"OAuth error: {e}")
        st.query_params.clear()


def _render_provider_section(oauth, provider: str, display_name: str):
    """Render connect/disconnect UI for a single provider."""

    st.subheader(display_name)
    connected = oauth.is_connected(provider)
    has_creds = oauth.has_credentials(provider)

    if connected:
        st.success("Connected")
        if st.button(f"Disconnect {display_name}", key=f"dc_{provider}"):
            oauth.disconnect(provider)
            # Clear cached site lists on disconnect
            st.session_state.pop(f"{provider}_sites", None)
            st.session_state.pop(f"selected_{provider}_site", None)
            st.rerun()
    elif has_creds:
        st.warning("Not connected")
        if st.button(f"Sign in with {display_name}", key=f"cn_{provider}", type="primary"):
            try:
                if provider == "google":
                    auth_url = oauth.get_google_auth_url()
                else:
                    auth_url = oauth.get_bing_auth_url()
                st.markdown(f"[Authorize {display_name}]({auth_url})")
            except Exception as e:
                st.error(f"Failed to generate auth URL: {e}")
    else:
        st.warning("No OAuth credentials configured")
        st.caption("Add your Google/Bing Client ID and Secret via the API Keys panel in the sidebar.")
