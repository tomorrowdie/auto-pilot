"""
SaaS Core — AuthManager Facade (V5)

The single interface for ALL credential operations across the app.

Key responsibilities:
  1. save_api_key / get_api_key — LLM key CRUD via unified_credentials
  2. _validate_key              — Live HTTP ping before saving (Verify & Save)
  3. render_sidebar_key_manager — Compact Streamlit sidebar UI (global, keys only)
  4. render_tab_model_selector  — Per-tab model picker (contextual, in main panel)
  5. get_llm                    — Delegates to registry.build_llm()
  6. wipe_all                   — Security reset

V5 Split-Panel Rule:
  Sidebar  → render_sidebar_key_manager()   (security / global)
  Main     → render_tab_model_selector()    (task context / per-tab)
"""
import logging
import requests
import streamlit as st

from V2_Engine.saas_core.db.database import Database
from V2_Engine.saas_core.auth.registry import (
    PROVIDER_SPECS,
    build_llm,
    get_all_models_flat,
)

logger = logging.getLogger(__name__)

# Providers that never need an API key
_NO_KEY_PROVIDERS = {"local_ollama"}

# Live validation endpoints per provider
_VALIDATE_URLS: dict[str, str] = {
    "google":    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
    "openai":    "https://api.openai.com/v1/chat/completions",
    "anthropic": "https://api.anthropic.com/v1/messages",
    "deepseek":  "https://api.deepseek.com/v1/chat/completions",
    "alibaba":   "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
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

            elif provider == "openai":
                resp = requests.post(
                    _VALIDATE_URLS["openai"],
                    headers={"Authorization": f"Bearer {key}"},
                    json={"model": model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1},
                    timeout=10,
                )
                if resp.status_code == 200:
                    return True, "Connected"
                return False, resp.json().get("error", {}).get("message", resp.text[:100])

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

            elif provider in ("deepseek", "alibaba"):
                url = _VALIDATE_URLS[provider]
                resp = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {key}"},
                    json={"model": model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1},
                    timeout=10,
                )
                if resp.status_code == 200:
                    return True, "Connected"
                return False, resp.text[:100]

            elif provider == "local_ollama":
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
        spec = PROVIDER_SPECS.get(provider, {})
        resolved_model = model or spec.get("default_model", "")

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
    #  LLM FACTORY
    # ══════════════════════════════════════════════════════════════════

    def get_llm(
        self,
        user_id: str,
        provider: str,
        model: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.7,
        **kwargs,
    ):
        """
        Fetch API key from vault (or use override) and return an LLM object.
        Delegates to registry.build_llm().
        """
        key = api_key or self.get_api_key(user_id, provider)
        if key is None and provider not in _NO_KEY_PROVIDERS:
            raise ValueError(
                f"No API key stored for provider '{provider}'. "
                f"Save a key first via render_sidebar_key_manager()."
            )
        return build_llm(
            provider=provider,
            api_key=key or "local",
            model=model,
            temperature=temperature,
            **kwargs,
        )

    # ══════════════════════════════════════════════════════════════════
    #  STREAMLIT UI — SIDEBAR  (Global Credentials)
    # ══════════════════════════════════════════════════════════════════

    def render_sidebar_key_manager(self, user_id: str) -> None:
        """
        Compact sidebar widget for managing API keys globally.
        Enforces Split-Panel Rule: sidebar handles CREDENTIALS only.
        """
        with st.expander("API Keys", expanded=False):
            active = self.get_active_providers(user_id)

            # ── Active connections summary ──
            if active:
                st.caption("**Stored Keys**")
                for p in sorted(active):
                    label = PROVIDER_SPECS.get(p, {}).get("label", p)
                    col_label, col_del = st.columns([4, 1])
                    with col_label:
                        st.caption(f"OK  {label}")
                    with col_del:
                        if st.button("X", key=f"del_key_{p}", help=f"Remove {label}"):
                            self.delete_api_key(user_id, p)
                            st.rerun()
                st.divider()

            # ── Add / Edit key form ──
            st.caption("**Add / Edit Key**")
            provider_options = [k for k in PROVIDER_SPECS if k != "local_ollama"]
            provider = st.selectbox(
                "Provider",
                options=provider_options,
                format_func=lambda k: PROVIDER_SPECS[k]["label"],
                key="akm_provider_select",
            )
            spec = PROVIDER_SPECS[provider]
            model_options = spec.get("models", [])
            model = st.selectbox(
                "Default Model",
                options=model_options,
                index=model_options.index(spec["default_model"]) if spec["default_model"] in model_options else 0,
                key="akm_model_select",
            )
            key_input = st.text_input(
                "API Key",
                type="password",
                placeholder=f"{spec['env_var']} — validates on save",
                key="akm_key_input",
            )
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

            # ── Local Ollama (always available) ──
            st.divider()
            st.caption("Local / Ollama — no key needed")

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
        Only shows models for providers with stored keys (+ local_ollama always).
        Returns (provider_key, model_id).

        Args:
            user_id:  The current user.
            tab_key:  Unique key per usage site (e.g. "rufus_audit", "review_analysis").
            label:    Display label above the dropdown.
        """
        active = self.get_active_providers(user_id) | {"local_ollama"}
        flat = get_all_models_flat(providers=active)

        if not flat:
            st.warning("No API keys stored. Add one in the API Keys sidebar.")
            return "local_ollama", PROVIDER_SPECS["local_ollama"]["default_model"]

        options = [f"{m['label']}" for m in flat]
        # Determine default index — prefer google/gemini-2.5-flash if available
        default_idx = 0
        for i, m in enumerate(flat):
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
