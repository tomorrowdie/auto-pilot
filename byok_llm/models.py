"""
Provider + model registry for BYOK-LLM.

Consumed by:
    - LLMRouter._registry  → knows which class handles which provider key
    - streamlit_ui/key_manager.py → populates provider + model dropdowns

Adding a new provider: add an entry to PROVIDER_CATALOG and register the
class in router.py._build_registry().
"""

# ---------------------------------------------------------------------------
# Canonical provider catalog
# Each entry:
#   id          → key used in LLMRouter.call(provider=...)
#   label       → display name for Streamlit UI
#   requires_key → False only for local providers (Ollama)
#   models      → list of {id, label} dicts for the model dropdown
# ---------------------------------------------------------------------------

PROVIDER_CATALOG: list[dict] = [
    {
        "id": "openrouter",
        "label": "OpenRouter",
        "tagline": "One key — Claude, GPT-4, Gemini, Llama & more",
        "requires_key": True,
        "key_url": "https://openrouter.ai/keys",
        "models": [
            {"id": "anthropic/claude-sonnet-4-5",            "label": "Claude Sonnet 4.5"},
            {"id": "anthropic/claude-opus-4",                "label": "Claude Opus 4"},
            {"id": "anthropic/claude-haiku-4-5",             "label": "Claude Haiku 4.5"},
            {"id": "google/gemini-2.5-flash",                "label": "Gemini 2.5 Flash"},
            {"id": "google/gemini-2.5-pro",                  "label": "Gemini 2.5 Pro"},
            {"id": "openai/gpt-4o",                          "label": "GPT-4o"},
            {"id": "openai/gpt-4o-mini",                     "label": "GPT-4o Mini"},
            {"id": "meta-llama/llama-3.3-70b-instruct",      "label": "Llama 3.3 70B"},
            {"id": "deepseek/deepseek-chat",                 "label": "DeepSeek Chat"},
            {"id": "deepseek/deepseek-r1",                   "label": "DeepSeek R1"},
            {"id": "qwen/qwen-max",                          "label": "Qwen Max"},
            {"id": "mistralai/mistral-large",                "label": "Mistral Large"},
        ],
    },
    {
        "id": "google",
        "label": "Google Gemini",
        "tagline": "Direct Google AI Studio key",
        "requires_key": True,
        "key_url": "https://aistudio.google.com/app/apikey",
        "models": [
            {"id": "gemini-3.1-pro-preview", "label": "Gemini 3.1 Pro (Preview)"},
            {"id": "gemini-3-flash-preview", "label": "Gemini 3 Flash (Preview)"},
            {"id": "gemini-2.5-flash",       "label": "Gemini 2.5 Flash"},
            {"id": "gemini-2.5-pro",         "label": "Gemini 2.5 Pro"},
        ],
    },
    {
        "id": "openai",
        "label": "OpenAI",
        "tagline": "GPT-4o, o3 via platform.openai.com",
        "requires_key": True,
        "key_url": "https://platform.openai.com/api-keys",
        "models": [
            {"id": "gpt-4o",       "label": "GPT-4o"},
            {"id": "gpt-4o-mini",  "label": "GPT-4o Mini"},
            {"id": "o3-mini",      "label": "o3 Mini"},
            {"id": "o4-mini",      "label": "o4 Mini"},
        ],
    },
    {
        "id": "anthropic",
        "label": "Anthropic Claude",
        "tagline": "Direct Anthropic API key",
        "requires_key": True,
        "key_url": "https://console.anthropic.com/settings/keys",
        "models": [
            {"id": "claude-sonnet-4-6",         "label": "Claude Sonnet 4.6"},
            {"id": "claude-opus-4-6",           "label": "Claude Opus 4.6"},
            {"id": "claude-haiku-4-5-20251001", "label": "Claude Haiku 4.5"},
        ],
    },
    {
        "id": "deepseek",
        "label": "DeepSeek",
        "tagline": "Cost-efficient reasoning via platform.deepseek.com",
        "requires_key": True,
        "key_url": "https://platform.deepseek.com/api_keys",
        "models": [
            {"id": "deepseek-chat",     "label": "DeepSeek Chat (V3)"},
            {"id": "deepseek-reasoner", "label": "DeepSeek Reasoner (R1)"},
        ],
    },
    {
        "id": "qwen",
        "label": "Alibaba Qwen",
        "tagline": "Qwen models via DashScope international",
        "requires_key": True,
        "key_url": "https://bailian.console.alibabacloud.com",
        "models": [
            {"id": "qwen-max",   "label": "Qwen Max"},
            {"id": "qwen-plus",  "label": "Qwen Plus"},
            {"id": "qwen-turbo", "label": "Qwen Turbo"},
        ],
    },
    {
        "id": "ollama",
        "label": "Ollama (Local)",
        "tagline": "Run models locally — no API key required",
        "requires_key": False,
        "key_url": None,
        "models": [
            {"id": "llama3",   "label": "Llama 3"},
            {"id": "llama3.1", "label": "Llama 3.1"},
            {"id": "mistral",  "label": "Mistral"},
            {"id": "gemma2",   "label": "Gemma 2"},
            {"id": "phi3",     "label": "Phi 3"},
            {"id": "qwen2",    "label": "Qwen 2"},
        ],
    },
]

# ---------------------------------------------------------------------------
# Convenience lookups
# ---------------------------------------------------------------------------

# provider_id → full catalog entry
PROVIDER_BY_ID: dict[str, dict] = {p["id"]: p for p in PROVIDER_CATALOG}

# provider_id → list of model IDs (str)
MODELS_BY_PROVIDER: dict[str, list[str]] = {
    p["id"]: [m["id"] for m in p["models"]] for p in PROVIDER_CATALOG
}

# provider_id → {model_id: model_label}
MODEL_LABELS_BY_PROVIDER: dict[str, dict[str, str]] = {
    p["id"]: {m["id"]: m["label"] for m in p["models"]}
    for p in PROVIDER_CATALOG
}

# Providers that need a key (excludes ollama)
KEYED_PROVIDERS: set[str] = {p["id"] for p in PROVIDER_CATALOG if p["requires_key"]}
