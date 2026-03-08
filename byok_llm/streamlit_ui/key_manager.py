"""
render_key_manager() — drop-in Streamlit widget for BYOK key management.

Completely decoupled from storage: the caller provides three callbacks
so this widget works with any backend (SQLite, JSON, env vars, etc.).

Usage (Auto-Pilot example):

    from byok_llm.streamlit_ui.key_manager import render_key_manager

    provider, model = render_key_manager(
        storage_get    = lambda p: auth_manager.get_api_key(user_id, p),
        storage_set    = lambda p, m, k: auth_manager.save_api_key(user_id, p, k, m),
        storage_delete = lambda p: auth_manager.delete_api_key(user_id, p),
        namespace      = "main",   # unique prefix to avoid widget key collisions
    )
    # provider / model are the currently active selection (or None, None)

Usage (simple dict-based storage for prototypes):

    _keys: dict = {}
    provider, model = render_key_manager(
        storage_get    = lambda p: _keys.get(p),
        storage_set    = lambda p, m, k: _keys.update({p: k}),
        storage_delete = lambda p: _keys.pop(p, None),
    )
"""

from __future__ import annotations

from typing import Callable

import streamlit as st

from byok_llm.models import PROVIDER_CATALOG, PROVIDER_BY_ID
from byok_llm.router import LLMRouter

_router = LLMRouter()


def render_key_manager(
    *,
    storage_get: Callable[[str], str | None],
    storage_set: Callable[[str, str, str], None],
    storage_delete: Callable[[str], None],
    namespace: str = "byok",
    show_title: bool = True,
) -> tuple[str | None, str | None]:
    """
    Render the BYOK key manager widget.

    Args:
        storage_get:    fn(provider_id) → api_key or None
        storage_set:    fn(provider_id, model_id, api_key) → None
        storage_delete: fn(provider_id) → None
        namespace:      Prefix for all Streamlit widget keys (avoid collisions
                        when embedding multiple instances on the same page).
        show_title:     Whether to render the "🔑 LLM API Keys" heading.

    Returns:
        (provider_id, model_id) of the currently saved + active config,
        or (None, None) if nothing is stored yet.
    """
    if show_title:
        st.markdown("### 🔑 LLM API Keys")

    # ── Provider selectbox ────────────────────────────────────────────
    _provider_labels = [p["label"] for p in PROVIDER_CATALOG]
    _provider_ids    = [p["id"]    for p in PROVIDER_CATALOG]

    _sel_label = st.selectbox(
        "Provider",
        options=_provider_labels,
        key=f"{namespace}_provider_select",
    )
    _provider_id = _provider_ids[_provider_labels.index(_sel_label)]
    _provider     = PROVIDER_BY_ID[_provider_id]

    # ── Current stored state for selected provider ────────────────────
    _stored_key = storage_get(_provider_id)
    _is_saved   = bool(_stored_key)

    if _is_saved:
        st.success(f"✅ **{_sel_label}** key saved")
    else:
        st.info(f"No key saved for **{_sel_label}** yet.")

    # ── Model selectbox ───────────────────────────────────────────────
    _model_entries  = _provider["models"]
    _model_labels   = [m["label"] for m in _model_entries]
    _model_ids      = [m["id"]    for m in _model_entries]

    _sel_model_label = st.selectbox(
        "Model",
        options=_model_labels,
        key=f"{namespace}_model_select",
    )
    _model_id = _model_ids[_model_labels.index(_sel_model_label)]

    # ── API key input (hidden for Ollama) ─────────────────────────────
    _requires_key = _provider["requires_key"]

    if _requires_key:
        _key_url = _provider.get("key_url")
        _label   = "API Key"
        if _key_url:
            _label = f"API Key  ([get key ↗]({_key_url}))"

        _raw_key = st.text_input(
            _label,
            type="password",
            placeholder="Paste your key here…",
            key=f"{namespace}_key_input",
        )

        col_save, col_del = st.columns([3, 1])

        with col_save:
            if st.button(
                "Validate & Save",
                key=f"{namespace}_btn_save",
                use_container_width=True,
                type="primary",
            ):
                _k = _raw_key.strip()
                if not _k:
                    st.warning("Paste your API key first.")
                else:
                    with st.spinner("Validating…"):
                        _ok = _router.validate(_provider_id, _k, _model_id)
                    if _ok:
                        storage_set(_provider_id, _model_id, _k)
                        st.success("✅ Key validated and saved!")
                        st.rerun()
                    else:
                        st.error(
                            "❌ Validation failed. "
                            "Check that the key is correct and the model is available."
                        )

        with col_del:
            if _is_saved:
                if st.button(
                    "Remove",
                    key=f"{namespace}_btn_del",
                    use_container_width=True,
                ):
                    storage_delete(_provider_id)
                    st.toast(f"Removed {_sel_label} key", icon="🗑️")
                    st.rerun()

    else:
        # Ollama — no key needed, just validate server is up
        if st.button(
            "Test Connection",
            key=f"{namespace}_btn_test_ollama",
            use_container_width=True,
        ):
            with st.spinner("Connecting to Ollama…"):
                _ok = _router.validate("ollama", "", _model_id)
            if _ok:
                st.success("✅ Ollama is running locally.")
            else:
                st.error(
                    "❌ Cannot reach Ollama at localhost:11434. "
                    "Make sure Ollama is installed and running."
                )

    # ── Tagline / hint ────────────────────────────────────────────────
    _tagline = _provider.get("tagline", "")
    if _tagline:
        st.caption(_tagline)

    # ── Return active config ──────────────────────────────────────────
    # If a key is saved for the selected provider, return it as active.
    # Callers use this to pre-populate model selectors elsewhere.
    if _is_saved or not _requires_key:
        return _provider_id, _model_id
    return None, None


# ---------------------------------------------------------------------------
# Convenience: compact inline selector (for pages that just need to pick
# the model, assuming a key has already been saved via render_key_manager)
# ---------------------------------------------------------------------------

def render_model_selector(
    *,
    storage_get: Callable[[str], str | None],
    namespace: str = "byok_sel",
    label: str = "LLM Model",
) -> tuple[str | None, str | None, str | None]:
    """
    Compact provider + model selector. Assumes keys are already saved.
    Returns (provider_id, model_id, api_key) or (None, None, None).

    Use this on analysis pages (e.g. Source 2, 3, 5) instead of the full
    key manager — it's just two dropdowns with a saved-key status badge.
    """
    _provider_labels   = [p["label"] for p in PROVIDER_CATALOG]
    _provider_ids      = [p["id"]    for p in PROVIDER_CATALOG]

    _sel_label = st.selectbox(label, options=_provider_labels, key=f"{namespace}_provider")
    _provider_id = _provider_ids[_provider_labels.index(_sel_label)]
    _provider    = PROVIDER_BY_ID[_provider_id]

    _stored_key = storage_get(_provider_id)
    _requires   = _provider["requires_key"]

    if _requires and not _stored_key:
        st.warning(f"No key saved for {_sel_label}. Add one in ⚙️ Settings.")
        return None, None, None

    _model_entries = _provider["models"]
    _model_labels  = [m["label"] for m in _model_entries]
    _model_ids     = [m["id"]    for m in _model_entries]

    _sel_model = st.selectbox("Model", options=_model_labels, key=f"{namespace}_model")
    _model_id  = _model_ids[_model_labels.index(_sel_model)]

    return _provider_id, _model_id, _stored_key or ""
