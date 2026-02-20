"""
SaaS Core — Provider Registry & LLM Factory (V5)

PROVIDER_SPECS: Canonical catalog of all supported LLM providers.
build_llm():    The ONLY place LLM client objects are constructed.
                Uses lazy LangChain imports — graceful ImportError if package missing.

Key decisions baked in:
  - Qwen/Alibaba routes through ChatOpenAI + DashScope (ChatTongyi broken: LangChain #30838)
  - Qwen temperature auto-corrected to >= 0.6 (thinking mode requirement)
  - DeepSeek routes through ChatOpenAI + deepseek endpoint (OpenAI-compatible)
  - Local Ollama has no API key requirement
"""

# ── Provider Catalog ────────────────────────────────────────────────────────

PROVIDER_SPECS: dict[str, dict] = {
    "openai": {
        "label":         "OpenAI",
        "env_var":       "OPENAI_API_KEY",
        "default_model": "gpt-5.2",
        "openai_compatible": False,
        "models": [
            "gpt-5.2",
            "gpt-5.2-pro",
            "gpt-5-mini",
            "gpt-5-nano",
            "gpt-5.2-codex",
            "gpt-5.1-codex-max",
        ],
    },
    "anthropic": {
        "label":         "Anthropic (Claude)",
        "env_var":       "ANTHROPIC_API_KEY",
        "default_model": "claude-sonnet-4.5",
        "openai_compatible": False,
        "models": [
            "claude-opus-4.6",
            "claude-opus-4.5",
            "claude-sonnet-4.5",
        ],
    },
    "google": {
        "label":         "Google (Gemini)",
        "env_var":       "GOOGLE_API_KEY",
        "default_model": "gemini-2.5-flash",
        "openai_compatible": False,
        "models": [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-ultra-2.5",
        ],
    },
    "deepseek": {
        "label":         "DeepSeek",
        "env_var":       "DEEPSEEK_API_KEY",
        "default_model": "deepseek-chat",
        "openai_compatible": True,
        "base_url":      "https://api.deepseek.com/v1",
        "models": [
            "deepseek-chat",
            "deepseek-reasoner",
        ],
    },
    "alibaba": {
        "label":         "Alibaba (Qwen)",
        "env_var":       "DASHSCOPE_API_KEY",
        "default_model": "qwen-max",
        "openai_compatible": True,
        "base_url":      "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        "models": [
            "qwen-max",
            "qwen-plus",
            "qwen3-max",
            "qwen-vl-max",
            "qwen-vl-plus",
            "qwen2.5-72b-instruct",
        ],
    },
    "local_ollama": {
        "label":         "Local / Ollama",
        "env_var":       None,          # No API key needed
        "default_model": "llama3",
        "openai_compatible": False,
        "models": [
            "llama3",
            "mistral",
            "phi3",
            "gemma2",
            "qwen2.5",
        ],
    },
}

# Providers that never require an API key
_NO_KEY_PROVIDERS = {"local_ollama"}


def get_all_models_flat(providers: set[str] | None = None) -> list[dict]:
    """
    Return [{provider, model, label}] for UI dropdowns.
    If `providers` is given, filter to only those providers (plus local_ollama always).
    """
    result = []
    for key, spec in PROVIDER_SPECS.items():
        if providers is not None and key not in providers and key not in _NO_KEY_PROVIDERS:
            continue
        for model in spec["models"]:
            result.append({
                "provider": key,
                "model":    model,
                "label":    f"{spec['label']} — {model}",
            })
    return result


def get_model_spec(provider_key: str, model_id: str) -> dict:
    """
    Resolve endpoint config for a specific provider/model combo.
    Returns dict with keys: base_url (optional), openai_compatible, label.
    """
    spec = PROVIDER_SPECS.get(provider_key, {})
    return {
        "base_url":          spec.get("base_url"),
        "openai_compatible": spec.get("openai_compatible", False),
        "label":             f"{spec.get('label', provider_key)} — {model_id}",
    }


def build_llm(
    provider: str,
    api_key: str,
    model: str | None = None,
    temperature: float = 0.7,
    **kwargs,
):
    """
    The ONLY place LLM client objects are constructed.

    Args:
        provider:    Registry key (e.g. 'google', 'openai', 'alibaba').
        api_key:     The user's API key (from VaultDatabase or override).
        model:       Model ID. Defaults to provider's default_model.
        temperature: Float. Qwen forces >= 0.6 if lower (thinking mode).

    Returns:
        An initialized LangChain ChatModel object.
    Raises:
        ImportError: If the required LangChain package is not installed.
        ValueError:  If the provider key is unknown.
    """
    spec = PROVIDER_SPECS.get(provider)
    if spec is None:
        raise ValueError(
            f"Unknown provider: '{provider}'. "
            f"Valid keys: {list(PROVIDER_SPECS.keys())}"
        )

    resolved_model = model or spec["default_model"]

    # Qwen temperature guard (thinking mode requires >= 0.6)
    if provider == "alibaba" and temperature < 0.6:
        temperature = 0.6

    if provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError("pip install langchain-openai")
        return ChatOpenAI(
            api_key=api_key,
            model=resolved_model,
            temperature=temperature,
            **kwargs,
        )

    elif provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ImportError("pip install langchain-anthropic")
        return ChatAnthropic(
            api_key=api_key,
            model=resolved_model,
            temperature=temperature,
            **kwargs,
        )

    elif provider == "google":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ImportError:
            raise ImportError("pip install langchain-google-genai")
        return ChatGoogleGenerativeAI(
            google_api_key=api_key,
            model=resolved_model,
            temperature=temperature,
            **kwargs,
        )

    elif provider in ("deepseek", "alibaba"):
        # Both use ChatOpenAI pointed at their OpenAI-compatible endpoints
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ImportError("pip install langchain-openai")
        return ChatOpenAI(
            api_key=api_key,
            model=resolved_model,
            temperature=temperature,
            base_url=spec["base_url"],
            **kwargs,
        )

    elif provider == "local_ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            raise ImportError("pip install langchain-ollama")
        return ChatOllama(
            model=resolved_model,
            temperature=temperature,
            **kwargs,
        )

    raise ValueError(f"No build path for provider: '{provider}'")
