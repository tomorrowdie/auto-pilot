"""
SaaS Core — AuthManager Facade (V6)

The single interface for ALL credential operations across the app.

Key responsibilities:
  1. save_api_key / get_api_key — LLM key CRUD via unified_credentials
  2. _validate_key              — Live HTTP ping before saving (Verify & Save)
  3. render_sidebar_key_manager — Compact Streamlit sidebar UI (global, keys only)
  4. render_tab_model_selector  — Per-tab model picker (contextual, in main panel)
  5. wipe_all                   — Security reset

LLM calls: handled by byok_llm.LLMRouter in each source analyzer.
           AuthManager only stores/retrieves keys — it no longer builds LLM objects.

V5 Split-Panel Rule:
  Sidebar  → render_sidebar_key_manager()   (security / global)
  Main     → render_tab_model_selector()    (task context / per-tab)
"""
import logging

import requests
import streamlit as st

from V2_Engine.saas_core.db.database import Database
from byok_llm.models import PROVIDER_CATALOG, PROVIDER_BY_ID

logger = logging.getLogger(__name__)

# Providers that never need an API key (derived from catalog — currently just ollama)
_NO_KEY_PROVIDERS: set[str] = {
    p["id"] for p in PROVIDER_CATALOG if not p["requires_key"]
}

# Live validation endpoints per provider
_VALIDATE_URLS: dict[str, str] = {
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "google":     "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
    "openai":     "https://api.openai.com/v1/chat/completions",
    "anthropic":  "https://api.anthropic.com/v1/messages",
    "deepseek":   "https://api.deepseek.com/v1/chat/completions",
    "qwen":       "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
}


class AuthManager:
    """Facade class — the single import for all credential + LLM operations."""

    def __init__(self, db_path: str | None = None):
        self.db = Database(db_path)

    # ══════════════════════════════════════════════════════════════════
    #  VALIDATION  (Verify & Save pattern)
    # ══════════════════════════════════════════════════════════════════

    def _validate_key(self, provider: str, key: str, model: str) -> tuple[bool, str]:
        """
        Ping the provider API with the key before saving.
        Returns (success, message).
        """
        if not key or len(key) < 8:
            return False, "Key too short"

        try:
            if provider == "google":
                url = _VALIDATE_URLS["google"].format(model=model, key=key)
                resp = requests.post(
                    url,
                    json={"contents": [{"parts": [{"text": "hi"}]}]},
                    timeout=10,
                )
                if resp.status_code == 200:
                    return True, "Connected"
                msg = resp.json().get("error", {}).get("message", resp.text[:100])
                return False, msg

            elif provider == "anthropic":
                resp = requests.post(
                    _VALIDATE_URLS["anthropic"],
                    headers={
                        "x-api-key": key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={"model": model, "max_tokens": 1, "messages": [{"role": "user", "content": "hi"}]},
                    timeout=10,
                )
                if resp.status_code == 200:
                    return True, "Connected"
                return False, resp.json().get("error", {}).get("message", resp.text[:100])

            elif provider in ("openrouter", "openai", "deepseek", "qwen"):
                resp = requests.post(
                    _VALIDATE_URLS[provider],
                    headers={"Authorization": f"Bearer {key}"},
                    json={"model": model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1},
                    timeout=10,
                )
                if resp.status_code == 200:
                    return True, "Connected"
                return False, resp.json().get("error", {}).get("message", resp.text[:100])

            elif provider in _NO_KEY_PROVIDERS:
                return True, "Local (no validation needed)"

            return True, "No validation endpoint"

        except requests.Timeout:
            return False, "Connection timed out"
        except requests.ConnectionError:
            return False, "Cannot reach API"
        except Exception as e:
            return False, str(e)[:100]

    # ══════════════════════════════════════════════════════════════════
    #  CRUD
    # ══════════════════════════════════════════════════════════════════

    def save_api_key(
        self,
        user_id: str,
        provider: str,
        key: str,
        model: str | None = None,
    ) -> tuple[bool, str]:
        """
        Validate key, then persist to vault.
        Returns (success, message).
        """
        spec = PROVIDER_BY_ID.get(provider, {})
        models = spec.get("models", [])
        default_model = models[0]["id"] if models else ""
        resolved_model = model or default_model

        if provider not in _NO_KEY_PROVIDERS:
            ok, msg = self._validate_key(provider, key, resolved_model)
            if not ok:
                return False, msg

        self.db.save_credential(
            user_id, provider, "api_key",
            payload_dict={"key": key},
            meta_dict={"model": resolved_model},
        )
        return True, "Connected"

    def get_api_key(self, user_id: str, provider: str) -> str | None:
        """Fetch the decrypted API key string. Returns None if not stored."""
        cred = self.db.get_credential(user_id, provider, "api_key")
        return cred.get("key") if cred else None

    def delete_api_key(self, user_id: str, provider: str) -> None:
        self.db.delete_credential(user_id, provider, "api_key")

    def wipe_all(self, user_id: str) -> None:
        """Security reset — removes ALL stored API keys."""
        self.db.wipe_all_credentials(user_id)

    def get_active_providers(self, user_id: str) -> set[str]:
        """Return set of provider keys that have a stored api_key."""
        rows = self.db.list_credentials(user_id)
        return {r["provider"] for r in rows if r["credential_type"] == "api_key"}

    # ══════════════════════════════════════════════════════════════════
    #  STREAMLIT UI — SIDEBAR  (Global Credentials)
    # ══════════════════════════════════════════════════════════════════

    def render_sidebar_key_manager(self, user_id: str) -> None:
        """
        Compact sidebar widget for managing API keys globally.
        Enforces Split-Panel Rule: sidebar handles CREDENTIALS only.
        """
        with st.expander("API Keys", expanded=False):
            # ── Provider + model selectors ──
            keyed = [p for p in PROVIDER_CATALOG if p["requires_key"]]
            provider_ids = [p["id"] for p in keyed]
            provider = st.selectbox(
                "Provider",
                options=provider_ids,
                format_func=lambda k: PROVIDER_BY_ID[k]["label"],
                key="akm_provider_select",
            )
            spec = PROVIDER_BY_ID[provider]
            model_ids    = [m["id"]    for m in spec.get("models", [])]
            model_labels = {m["id"]: m["label"] for m in spec.get("models", [])}
            model = st.selectbox(
                "Default Model",
                options=model_ids,
                format_func=lambda mid: model_labels.get(mid, mid),
                key="akm_model_select",
            )

            # ── Stored-key status for the currently selected provider ──
            _current_key = self.get_api_key(user_id, provider)
            _is_saved = bool(_current_key)
            if _is_saved:
                st.caption(f"✅ **{spec['label']}** key saved")
            else:
                st.caption(f"No key saved for **{spec['label']}** yet.")

            # ── API key input — provider-scoped key so it resets on switch ──
            key_url = spec.get("key_url")
            placeholder = f"Paste your {spec['label']} API key"
            key_input = st.text_input(
                "API Key",
                type="password",
                value=_current_key or "",
                placeholder=placeholder,
                key=f"akm_{provider}_key_input",
            )
            if key_url:
                st.caption(f"[Get API key ↗]({key_url})")

            col_save, col_del = st.columns([3, 1])
            with col_save:
                if st.button("Verify & Save", key="akm_save_btn", use_container_width=True):
                    if not key_input.strip():
                        st.warning("Paste your API key first.")
                    else:
                        with st.spinner("Validating..."):
                            ok, msg = self.save_api_key(user_id, provider, key_input.strip(), model)
                        if ok:
                            st.success(f"Saved! {msg}")
                            st.rerun()
                        else:
                            st.error(f"Rejected: {msg}")
            with col_del:
                if _is_saved:
                    if st.button("Remove", key="akm_del_btn", use_container_width=True):
                        self.delete_api_key(user_id, provider)
                        st.toast(f"Removed {spec['label']} key", icon="🗑️")
                        st.rerun()

            # ── Local Ollama (always available) ──
            st.divider()
            st.caption("Ollama (Local) — no key needed")

            # ── Security reset ──
            st.divider()
            if st.button(
                "Reset / Clear All Keys",
                key="akm_wipe_btn",
                use_container_width=True,
                type="secondary",
            ):
                self.wipe_all(user_id)
                st.success("All keys wiped.")
                st.rerun()

    # ══════════════════════════════════════════════════════════════════
    #  STREAMLIT UI — MAIN PANEL  (Per-Tab Model Selection)
    # ══════════════════════════════════════════════════════════════════

    def render_tab_model_selector(
        self,
        user_id: str,
        tab_key: str,
        label: str = "Select Model",
    ) -> tuple[str, str]:
        """
        Contextual model dropdown for a specific task/tab.
        Only shows models for providers with stored keys (+ ollama always).
        Returns (provider_key, model_id).

        Args:
            user_id:  The current user.
            tab_key:  Unique key per usage site (e.g. "rufus_audit", "review_analysis").
            label:    Display label above the dropdown.
        """
        active = self.get_active_providers(user_id) | _NO_KEY_PROVIDERS

        # Build flat list from PROVIDER_CATALOG for active providers only
        flat: list[dict] = []
        for pspec in PROVIDER_CATALOG:
            pid = pspec["id"]
            if pid not in active:
                continue
            plabel = pspec["label"]
            for m in pspec["models"]:
                flat.append({
                    "provider": pid,
                    "model":    m["id"],
                    "label":    f"{plabel} — {m['label']}",
                })

        if not flat:
            st.warning("No API keys stored. Add one in the API Keys sidebar.")
            ollama_spec = PROVIDER_BY_ID.get("ollama", {})
            fallback_model = (ollama_spec.get("models") or [{"id": "llama3"}])[0]["id"]
            return "ollama", fallback_model

        options = [m["label"] for m in flat]
        # Prefer openrouter first, then google flash
        default_idx = 0
        for i, m in enumerate(flat):
            if m["provider"] == "openrouter":
                default_idx = i
                break
            if m["provider"] == "google" and "flash" in m["model"]:
                default_idx = i
                break

        selected_label = st.selectbox(
            label,
            options=options,
            index=default_idx,
            key=f"tab_model_{tab_key}",
        )
        selected = flat[options.index(selected_label)]
        return selected["provider"], selected["model"]
