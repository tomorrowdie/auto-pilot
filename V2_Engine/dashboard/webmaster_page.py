"""
Source 5 — Webmaster Dashboard (GSC + Bing)

Provides:
    1. OAuth Redirect Trap (handles ?code=...&state=... callback)
    2. 2-column credential UI — inline on the main panel (no sidebar dependency)
       - Google: Client ID + Client Secret → OAuth flow → GSC property selectbox
       - Bing:   API Key → Bing Webmaster API → verified site selectbox
    3. Analysis tabs triggered by the selected domain dropdowns

Redirect URI is hardcoded to https://auto-pilot.zeabur.app (_REDIRECT_BASE).
    Update _REDIRECT_BASE directly if the production domain changes.

Called from app.py via:
    from V2_Engine.dashboard.webmaster_page import render_webmaster_page
    render_webmaster_page()
"""

import json
import logging
import os
from datetime import date

import pandas as pd
import requests
import streamlit as st

logger = logging.getLogger(__name__)

# Allow HTTP redirects for localhost dev (Google OAuth requires HTTPS in prod)
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")

# Single source of truth for the redirect base — read once at import time
_REDIRECT_BASE = "https://auto-pilot.zeabur.app"


# ===========================================================================
#  MAIN ENTRY POINT
# ===========================================================================

def render_webmaster_auth(db=None, oauth=None, user_id: str | None = None):
    """
    Standalone auth flow — callable from the onboarding wizard OR the main page.

    Handles:
        1. Session guard + DB/OAuth initialization (self-initialising when args are None)
        2. OAuth redirect trap (runs before any UI is drawn)
        3. Pre-warm site caches on fresh session
        4. 2-column credential UI (Google left, Bing right)

    Returns:
        (db, oauth, user_id) on success.
        None if there is no valid user session (caller should return immediately).
    """
    from V2_Engine.saas_core.db.database import Database
    from V2_Engine.saas_core.auth.oauth_manager import OAuthManager

    # ── Session guard ───────────────────────────────────────────────────
    if user_id is None:
        if "user_id" not in st.session_state:
            st.error("No user session. Please restart the app.")
            return None
        user_id = st.session_state["user_id"]

    # ── DB + OAuth init ─────────────────────────────────────────────────
    if db is None:
        db = st.session_state.get("_webmaster_db")
        if db is None:
            db = Database()
            st.session_state["_webmaster_db"] = db

    if oauth is None:
        oauth = OAuthManager(db, user_id)

    # ── OAuth redirect trap (must run BEFORE any UI is drawn) ───────────
    _handle_oauth_callback(db, oauth, user_id)

    # ── Pre-warm site caches on fresh session ────────────────────────────
    # On browser refresh session_state is cleared but DB credentials survive.
    # Re-fetch site lists silently so dropdowns appear immediately.
    if oauth.is_connected("google") and "google_sites" not in st.session_state:
        st.session_state["google_sites"] = _fetch_gsc_sites_cached(oauth)
    _bing_cred = db.get_credential(user_id, "bing", "api_key")
    _bing_key_prewarm = (_bing_cred or {}).get("api_key", "")
    if _bing_key_prewarm and "bing_sites" not in st.session_state:
        st.session_state["bing_sites"], _ = _fetch_bing_sites(_bing_key_prewarm)

    # ── 2-column credential UI ──────────────────────────────────────────
    col_google, col_bing = st.columns(2)
    with col_google:
        _render_google_section(db, oauth, user_id)
    with col_bing:
        _render_bing_section(db, user_id)

    return db, oauth, user_id


def render_webmaster_page():
    """Main entry point — called by app.py when nav == 'Webmaster'."""

    # ── Page header ─────────────────────────────────────────────────────
    st.header("Webmaster — SEO & GEO Analytics")
    st.caption(
        "Enter your credentials below to connect Google Search Console "
        "and Bing Webmaster, then select a verified property to run analysis."
    )

    # ── Auth block (credential UI + OAuth flow + cache pre-warm) ────────
    auth_result = render_webmaster_auth()
    if auth_result is None:
        return
    db, oauth, user_id = auth_result

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
            _render_gsc_analysis_tab(db, oauth, user_id, google_site)
        else:
            st.info("Connect Google Search Console above to begin.")

    with tab_bing_tab:
        if bing_site:
            _render_bing_analysis_tab(db, user_id, bing_site)
        else:
            st.info("Connect Bing Webmaster above to begin.")


# ===========================================================================
#  GOOGLE SECTION
# ===========================================================================

def _render_google_section(db, oauth, user_id: str):
    """Credential form + OAuth flow + GSC property selectbox."""

    st.subheader("Google Search Console")

    has_creds = oauth.has_credentials("google")

    # ── Pre-populate Client ID from DB on fresh session load ─────────────
    # Re-tries whenever the key is missing OR empty (e.g. after a Zeabur restart
    # with an ephemeral encryption key that couldn't decrypt on the last attempt).
    _saved_client_id = ""
    if has_creds:
        if not st.session_state.get("wm_google_client_id"):
            _saved_creds = db.get_api_credentials(user_id, "google") or {}
            _saved_client_id = _saved_creds.get("client_id", "")
            if _saved_client_id:
                st.session_state["wm_google_client_id"] = _saved_client_id
        else:
            _saved_client_id = st.session_state["wm_google_client_id"]

    # ── Credential inputs ────────────────────────────────────────────────
    _cid_preview = f"  ·  `{_saved_client_id[:28]}…`" if _saved_client_id else ""
    expander_label = (
        f"OAuth App Credentials — ✅ Saved{_cid_preview}" if has_creds
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
                    # Bust the site cache — the widget already owns
                    # wm_google_client_id so we must NOT write it here
                    # (Streamlit raises StreamlitAPIException if you modify
                    # a widget-bound key after the widget is instantiated).
                    # st.rerun() preserves the widget's current value automatically.
                    st.session_state.pop("google_sites", None)
                    st.session_state.pop("google_sites_debug", None)
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
                _fetched_sites, _debug_info = _fetch_gsc_sites(oauth)
                st.session_state["google_sites"] = _fetched_sites
                st.session_state["google_sites_debug"] = _debug_info

        sites = st.session_state.get("google_sites", [])

        if sites:
            st.selectbox(
                "Verified Property",
                options=sites,
                key="selected_google_site",
            )
        else:
            st.warning("No verified properties found in this account.")
            _debug = st.session_state.get("google_sites_debug", "")
            if _debug:
                with st.expander("Debug: Raw API Response"):
                    st.code(_debug, language="json")
            if st.button("Retry", key="retry_gsc"):
                st.session_state.pop("google_sites", None)
                st.session_state.pop("google_sites_debug", None)
                st.rerun()

        if st.button("Disconnect Google", key="dc_google"):
            oauth.disconnect("google")
            st.session_state.pop("google_sites", None)
            st.session_state.pop("selected_google_site", None)
            st.rerun()

    # ── Not connected: show Sign In link button ───────────────────────────
    else:
        st.warning("Not connected")
        try:
            # Generate auth URL once at render time — pass _REDIRECT_BASE so
            # auth URL and callback both use the same URI.
            auth_url = oauth.get_google_auth_url(redirect_uri=_REDIRECT_BASE)
            # st.link_button redirects immediately without triggering a rerun,
            # which prevents session_state (and the PKCE verifier) from being wiped.
            st.link_button("Sign in with Google", auth_url, type="primary")
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
                st.session_state.pop("bing_sites", None)       # force re-fetch
                st.session_state.pop("bing_fetch_error", None) # clear stale error
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

    # ── Fetch and cache verified sites ────────────────────────────────────
    if "bing_sites" not in st.session_state:
        cred = db.get_credential(user_id, "bing", "api_key")
        api_key = (cred or {}).get("api_key", "")
        with st.spinner("Fetching verified sites..."):
            fetched, fetch_err = _fetch_bing_sites(api_key)
            st.session_state["bing_sites"] = fetched
            if fetch_err:
                st.session_state["bing_fetch_error"] = fetch_err
            else:
                st.session_state.pop("bing_fetch_error", None)

    sites = st.session_state.get("bing_sites", [])

    if sites:
        st.selectbox(
            "Verified Site",
            options=sites,
            key="selected_bing_site",
        )
    else:
        fetch_err = st.session_state.get("bing_fetch_error", "")
        if fetch_err:
            st.error(f"Bing API error — check your key and try again:\n\n```\n{fetch_err}\n```")
        else:
            st.warning("No verified sites found. Check your API key.")
        if st.button("Retry", key="retry_bing"):
            st.session_state.pop("bing_sites", None)
            st.session_state.pop("bing_fetch_error", None)
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


def _fetch_gsc_sites(oauth) -> tuple[list[str], str]:
    """
    Fetch the user's verified properties from Google Search Console.

    Scope: https://www.googleapis.com/auth/webmasters.readonly

    Returns:
        (sites, debug_info) — sites is [] on failure.
        debug_info is the raw JSON response string on success,
        or the error message string on failure.
    """
    try:
        from googleapiclient.discovery import build
        creds = oauth.google_get_credentials()
        service = build("webmasters", "v3", credentials=creds)
        response = service.sites().list().execute()
        raw_debug = json.dumps(response, indent=2, default=str)
        sites = [s["siteUrl"] for s in response.get("siteEntry", [])]
        logger.info("GSC sites fetched: %d properties found", len(sites))
        return sites, raw_debug
    except Exception as e:
        err_msg = f"GSC site fetch error: {e}"
        logger.warning(err_msg)
        return [], err_msg


def _fetch_bing_sites(api_key: str) -> tuple[list[str], str]:
    """
    Fetch verified sites from the Bing Webmaster API.

    Tries endpoints in order (most current first):
      1. ssl.bing.com — key as query param
      2. api.webmaster.bing.com — key as query param
      3. ssl.bing.com — key as Authorization Bearer header
      4. api.webmaster.live.com — legacy fallback

    Returns:
        (sites, error_msg) — sites is [] on failure; error_msg is "" on success.
    """
    if not api_key:
        return [], "No API key provided."

    _ENDPOINTS = [
        ("https://ssl.bing.com/webmaster/api.svc/json/GetUserSites",
         {"apikey": api_key}, {}),
        ("https://api.webmaster.bing.com/webmaster/api.svc/json/GetUserSites",
         {"apikey": api_key}, {}),
        ("https://ssl.bing.com/webmaster/api.svc/json/GetUserSites",
         {}, {"Authorization": f"Bearer {api_key}"}),
        ("https://api.webmaster.live.com/webmaster/api.svc/json/GetUserSites",
         {"apikey": api_key}, {}),
    ]

    last_error = ""
    for url, params, headers in _ENDPOINTS:
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                sites = [s["Url"] for s in data.get("d", []) if "Url" in s]
                if sites:
                    logger.info(f"Bing sites fetched from {url}: {len(sites)} sites")
                    return sites, ""
                # 200 but empty — not an error, user just has no verified sites
                return [], ""
            last_error = (
                f"HTTP {resp.status_code} from {url}\n"
                f"Response: {resp.text[:500]}"
            )
            logger.warning(f"Bing endpoint {url}: {last_error}")
        except Exception as exc:
            last_error = f"Connection error to {url}: {exc}"
            logger.warning(last_error)

    return [], last_error


def _fetch_gsc_sites_cached(oauth) -> list[str]:
    """Pre-warm helper — fetches GSC sites and discards debug info."""
    sites, _ = _fetch_gsc_sites(oauth)
    return sites


# ===========================================================================
#  GSC ANALYSIS TAB
# ===========================================================================

def _render_gsc_analysis_tab(db, oauth, user_id: str, google_site: str):
    """Full GSC analysis UI: period selector → run → 5 sub-tabs + KB save."""
    from V2_Engine.saas_core.auth import auth_manager
    from V2_Engine.processors.source_5_webmaster.gsc_processor import (
        fetch_gsc_comparison, process_gsc_rows, is_low_traffic,
    )
    from V2_Engine.processors.source_5_webmaster.webmaster_analyzer import (
        generate_gsc_report, generate_content_suggestions,
    )

    st.success(f"Active property: `{google_site}`")

    # ── Controls row ─────────────────────────────────────────────────────
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        window_days = st.radio(
            "Comparison window", [7, 28], horizontal=True, key="gsc_window_days"
        )
    with c2:
        provider, model = auth_manager.render_tab_model_selector(
            user_id, "webmaster_gsc"
        )
    with c3:
        run_btn = st.button("Run GSC Analysis", type="primary", key="run_gsc")

    # ── Run / cache ───────────────────────────────────────────────────────
    result_key = f"gsc_result_{google_site}_{window_days}"
    ai_key = f"gsc_ai_{google_site}_{window_days}"

    if run_btn:
        with st.spinner("Fetching data and generating AI report (30–60 s)..."):
            try:
                from googleapiclient.discovery import build
                creds = oauth.google_get_credentials()
                service = build("webmasters", "v3", credentials=creds)
                rows = fetch_gsc_comparison(service, google_site, window_days)
                processed = process_gsc_rows(rows)
                st.session_state[result_key] = processed

                # Auto-generate AI report immediately after fetch
                low_traffic_now = is_low_traffic(processed)
                api_key_now = auth_manager.get_api_key(user_id, provider)
                if api_key_now or provider == "local_ollama":
                    if low_traffic_now:
                        suggestions = generate_content_suggestions(
                            processed, provider, api_key_now or "", model, google_site
                        )
                        st.session_state[ai_key] = {"type": "content", "data": suggestions}
                    else:
                        gsc_report_text = generate_gsc_report(
                            processed, provider, api_key_now or "", model, google_site
                        )
                        st.session_state[ai_key] = {"type": "report", "data": gsc_report_text}
                else:
                    st.session_state.pop(ai_key, None)

            except Exception as exc:
                st.error(f"GSC analysis failed: {exc}")
                return

    processed = st.session_state.get(result_key)
    if processed is None:
        st.info("Click **Run GSC Analysis** to fetch data.")
        return

    summary = processed["summary"]
    low_traffic = is_low_traffic(processed)

    # ── Sub-tabs ──────────────────────────────────────────────────────────
    t_sum, t_rise, t_new, t_p2, t_ai = st.tabs(
        ["Summary", "Rising / Declining", "New / Lost", "Page 2", "AI Report"]
    )

    with t_sum:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Impressions (A)", summary["total_impr_a"],
                    delta=summary["total_impr_a"] - summary["total_impr_b"])
        col2.metric("Clicks (A)", summary["total_clicks_a"],
                    delta=summary["total_clicks_a"] - summary["total_clicks_b"])
        col3.metric("New Keywords", summary["new_keyword_count"])
        col4.metric("Lost Keywords", summary["lost_keyword_count"])

        c5, c6, c7 = st.columns(3)
        c5.metric("Rising", summary["rising_keyword_count"])
        c6.metric("Declining", summary["declining_keyword_count"])
        c7.metric("Page 2 Opps", summary["page_two_opportunities_count"])

        st.caption(
            f"Period A: {summary['range_a'].get('startDate')} → "
            f"{summary['range_a'].get('endDate')}  |  "
            f"Period B: {summary['range_b'].get('startDate')} → "
            f"{summary['range_b'].get('endDate')}"
        )
        if low_traffic:
            st.warning(
                "Low traffic detected (< 100 impressions or 0 new keywords). "
                "AI report will generate **Content Suggestions** instead of a full SEO analysis."
            )

    with t_rise:
        rising = processed.get("rising_keywords", [])
        declining = processed.get("declining_keywords", [])

        st.subheader("Rising Keywords")
        if rising:
            cols = [c for c in ["query", "total_impr_a", "total_impr_b", "impr_diff",
                                 "total_clicks_a", "avg_pos_a", "pos_diff"] if c in pd.DataFrame(rising).columns]
            st.dataframe(pd.DataFrame(rising)[cols].head(20), use_container_width=True)
        else:
            st.info("No rising keywords in this period.")

        st.subheader("Declining Keywords")
        if declining:
            cols = [c for c in ["query", "total_impr_a", "total_impr_b", "impr_diff",
                                 "total_clicks_a", "avg_pos_a", "pos_diff"] if c in pd.DataFrame(declining).columns]
            st.dataframe(pd.DataFrame(declining)[cols].head(20), use_container_width=True)
        else:
            st.info("No declining keywords in this period.")

    with t_new:
        new_kw = processed.get("new_keywords", [])
        lost_kw = processed.get("lost_keywords", [])

        st.subheader("New Keywords")
        if new_kw:
            cols = [c for c in ["query", "total_impr_a", "avg_pos_a", "total_clicks_a"]
                    if c in pd.DataFrame(new_kw).columns]
            st.dataframe(pd.DataFrame(new_kw)[cols].head(20), use_container_width=True)
        else:
            st.info("No new keywords in this period.")

        st.subheader("Lost Keywords")
        if lost_kw:
            cols = [c for c in ["query", "total_impr_b", "avg_pos_b", "total_clicks_b"]
                    if c in pd.DataFrame(lost_kw).columns]
            st.dataframe(pd.DataFrame(lost_kw)[cols].head(20), use_container_width=True)
        else:
            st.info("No lost keywords in this period.")

    with t_p2:
        page2 = processed.get("page_two_opportunities", [])
        st.subheader("Page 2 Opportunities (Positions 10–20)")
        if page2:
            cols = [c for c in ["query", "avg_pos_a", "total_impr_a", "total_clicks_a"]
                    if c in pd.DataFrame(page2).columns]
            st.dataframe(pd.DataFrame(page2)[cols].head(30), use_container_width=True)
            st.caption(
                "These keywords are within striking distance of Page 1. "
                "Add internal links and optimize title/meta."
            )
        else:
            st.info("No page 2 opportunities found.")

    with t_ai:
        if st.button("Regenerate AI Report", key="gen_gsc_ai"):
            api_key = auth_manager.get_api_key(user_id, provider)
            if not api_key and provider != "local_ollama":
                st.error(f"No API key stored for '{provider}'. Add it in the sidebar.")
            else:
                with st.spinner("Regenerating AI report..."):
                    if low_traffic:
                        suggestions = generate_content_suggestions(
                            processed, provider, api_key or "", model, google_site
                        )
                        st.session_state[ai_key] = {"type": "content", "data": suggestions}
                    else:
                        gsc_report_text = generate_gsc_report(
                            processed, provider, api_key or "", model, google_site
                        )
                        st.session_state[ai_key] = {"type": "report", "data": gsc_report_text}

        ai_result = st.session_state.get(ai_key)
        if ai_result:
            if ai_result["type"] == "report":
                st.markdown(ai_result["data"])
                if st.button("Save to Knowledge Base", key="gsc_kb_save"):
                    _save_gsc_to_kb(processed, ai_result["data"], google_site, window_days)

            elif ai_result["type"] == "content":
                st.subheader("Content Suggestions (Low Traffic Mode)")
                for i, item in enumerate(ai_result["data"], 1):
                    with st.expander(f"{i}. {item.get('blog_title', 'Untitled')}"):
                        st.write(f"**Target Keyword:** {item.get('target_keyword', '')}")
                        st.write(f"**Intent:** {item.get('intent', '')}")
                if st.button("Save to Knowledge Base", key="gsc_kb_save_content"):
                    _save_gsc_to_kb(
                        processed,
                        json.dumps(ai_result["data"], indent=2, ensure_ascii=False),
                        google_site,
                        window_days,
                    )
        else:
            st.info("Run analysis above to auto-generate the AI report.")


# ===========================================================================
#  BING ANALYSIS TAB
# ===========================================================================

def _render_bing_analysis_tab(db, user_id: str, bing_site: str):
    """Full Bing analysis UI: run → 4 sub-tabs (Query, Page, GEO, AI) + KB save."""
    from V2_Engine.saas_core.auth import auth_manager
    from V2_Engine.processors.source_5_webmaster.bing_processor import (
        fetch_bing_query_stats, fetch_bing_page_stats,
        build_bing_report, categorize_bing_strategy,
    )
    from V2_Engine.processors.source_5_webmaster.webmaster_analyzer import (
        generate_bing_report,
    )

    st.success(f"Active site: `{bing_site}`")

    # ── Controls row ─────────────────────────────────────────────────────
    c1, c2 = st.columns([2, 1])
    with c1:
        provider, model = auth_manager.render_tab_model_selector(
            user_id, "webmaster_bing"
        )
    with c2:
        run_btn = st.button("Run Bing Analysis", type="primary", key="run_bing")

    result_key = f"bing_result_{bing_site}"
    ai_key = f"bing_ai_{bing_site}"

    if run_btn:
        cred = db.get_credential(user_id, "bing", "api_key")
        bing_api_key = (cred or {}).get("api_key", "")
        if not bing_api_key:
            st.error("Bing API key not found. Please save it above.")
            return
        with st.spinner("Fetching data and generating AI report (30–60 s)..."):
            try:
                query_rows = fetch_bing_query_stats(bing_api_key, bing_site)
                page_rows = fetch_bing_page_stats(bing_api_key, bing_site)
                report = build_bing_report(query_rows, page_rows)
                strategy = categorize_bing_strategy(report)
                st.session_state[result_key] = {"report": report, "strategy": strategy}

                # Auto-generate AI report immediately after fetch
                api_key_now = auth_manager.get_api_key(user_id, provider)
                if api_key_now or provider == "local_ollama":
                    bing_ai_text = generate_bing_report(
                        strategy, provider, api_key_now or "", model, bing_site
                    )
                    st.session_state[ai_key] = bing_ai_text
                else:
                    st.session_state.pop(ai_key, None)

            except Exception as exc:
                st.error(f"Bing analysis failed: {exc}")
                return

    cached = st.session_state.get(result_key)
    if cached is None:
        st.info("Click **Run Bing Analysis** to fetch data.")
        return

    report = cached["report"]
    strategy = cached["strategy"]

    # ── Sub-tabs ──────────────────────────────────────────────────────────
    t_q, t_p, t_geo, t_ai = st.tabs(
        ["Query Report", "Page Report", "GEO Strategy", "AI Report"]
    )

    with t_q:
        for label, key in [("7-Day Queries", "query_7d"), ("28-Day Queries", "query_28d")]:
            st.subheader(label)
            rows = report.get(key, {}).get("scored", [])
            if rows:
                df = pd.DataFrame(rows)
                show = [c for c in ["query", "growth_score", "ai_citation_tier",
                                     "impr_a", "clicks_a", "avg_pos_a"] if c in df.columns]
                st.dataframe(df[show].head(20), use_container_width=True)
            else:
                st.info(f"No {label.lower()} available.")

    with t_p:
        for label, key in [("7-Day Pages", "page_7d"), ("28-Day Pages", "page_28d")]:
            st.subheader(label)
            rows = report.get(key, {}).get("scored", [])
            if rows:
                df = pd.DataFrame(rows)
                show = [c for c in ["page", "growth_score", "impr_a", "clicks_a"] if c in df.columns]
                st.dataframe(df[show].head(20), use_container_width=True)
            else:
                st.info(f"No {label.lower()} available.")

    with t_geo:
        geo = strategy.get("geo_opportunities", [])
        st.subheader("GEO Opportunities (Zero Click — AI may be answering)")
        if geo:
            st.dataframe(pd.DataFrame(geo).head(20), use_container_width=True)
        else:
            st.info("No GEO opportunities found.")

        comm = strategy.get("commercial_wins", [])
        st.subheader("Commercial Intent Signals")
        if comm:
            st.dataframe(pd.DataFrame(comm).head(20), use_container_width=True)
        else:
            st.info("No commercial signals found.")

        early = strategy.get("early_signals", [])
        st.subheader("All Early Signals")
        if early:
            st.dataframe(pd.DataFrame(early).head(30), use_container_width=True)
        else:
            st.info("No early signals detected.")

    with t_ai:
        if st.button("Regenerate AI Report", key="gen_bing_ai"):
            api_key = auth_manager.get_api_key(user_id, provider)
            if not api_key and provider != "local_ollama":
                st.error(f"No API key stored for '{provider}'. Add it in the sidebar.")
            else:
                with st.spinner("Regenerating Bing AI report..."):
                    ai_report = generate_bing_report(
                        strategy, provider, api_key or "", model, bing_site
                    )
                    st.session_state[ai_key] = ai_report

        ai_report = st.session_state.get(ai_key)
        if ai_report:
            st.markdown(ai_report)
            if st.button("Save to Knowledge Base", key="bing_kb_save"):
                _save_bing_to_kb(strategy, report, ai_report, bing_site)
        else:
            st.info("Run analysis above to auto-generate the AI report.")


# ===========================================================================
#  KB SAVE HELPERS
# ===========================================================================

def _save_gsc_to_kb(processed: dict, ai_report: str, site_url: str, window_days: int):
    """Triple-File Protocol: save GSC result to 5_webmaster/ subfolder.

    Produces: {filename}.md  +  {filename}.csv  +  {filename}.json
    The .json file contains the full processed dict for Source 6 ingestion.
    """
    from V2_Engine.knowledge_base.manager import KnowledgeManager

    rows = []
    for cat, kws in [
        ("rising",    processed.get("rising_keywords", [])),
        ("new",       processed.get("new_keywords", [])),
        ("declining", processed.get("declining_keywords", [])),
        ("lost",      processed.get("lost_keywords", [])),
    ]:
        for kw in kws:
            rows.append({**kw, "category": cat})

    df = pd.DataFrame(rows) if rows else pd.DataFrame()
    site_clean = (
        site_url.replace("https://", "").replace("http://", "")
        .replace("/", "_").rstrip("_")
    )
    filename = f"{site_clean}_gsc_{window_days}d_{date.today().isoformat()}"

    km = KnowledgeManager()
    km.save_insight(
        subfolder="5_webmaster",
        filename=filename,
        content=ai_report,
        dataframe=df if not df.empty else None,
        raw_json=json.dumps(processed, indent=2, default=str),
    )
    st.success(f"Saved to Knowledge Base: `{filename}` (.md + .csv + .json)")


def _save_bing_to_kb(strategy: dict, report: dict, ai_report: str, site_url: str):
    """Triple-File Protocol: save Bing result to 5_webmaster/ subfolder.

    Produces: {filename}.md  +  {filename}.csv  +  {filename}.json
    The .json file contains full report + strategy dicts for Source 6 ingestion.
    """
    from V2_Engine.knowledge_base.manager import KnowledgeManager

    rows = (
        [{"type": "geo",        **r} for r in strategy.get("geo_opportunities", [])] +
        [{"type": "commercial", **r} for r in strategy.get("commercial_wins",   [])] +
        [{"type": "signal",     **r} for r in strategy.get("early_signals",     [])]
    )
    df = pd.DataFrame(rows) if rows else pd.DataFrame()
    site_clean = (
        site_url.replace("https://", "").replace("http://", "")
        .replace("/", "_").rstrip("_")
    )
    filename = f"{site_clean}_bing_{date.today().isoformat()}"

    km = KnowledgeManager()
    km.save_insight(
        subfolder="5_webmaster",
        filename=filename,
        content=ai_report,
        dataframe=df if not df.empty else None,
        raw_json=json.dumps({"report": report, "strategy": strategy}, indent=2, default=str),
    )
    st.success(f"Saved to Knowledge Base: `{filename}` (.md + .csv + .json)")
