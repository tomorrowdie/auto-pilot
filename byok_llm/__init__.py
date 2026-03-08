"""
byok_llm — Bring Your Own Key LLM router.

Lightweight, dependency-minimal package for routing LLM calls across
multiple providers via raw httpx.  Zero LangChain required.

Quick start:

    from byok_llm import LLMRouter

    router = LLMRouter()
    text = router.call(
        prompt="Summarise this review...",
        provider="openrouter",          # or "google", "openai", "anthropic", ...
        api_key="sk-or-...",
        model="anthropic/claude-sonnet-4-5",
        system="You are a concise analyst.",
        temperature=0.3,
    )

Supported providers:
    openrouter  — one key, 100s of models (recommended for new projects)
    google      — Gemini 2.5 Flash/Pro
    openai      — GPT-4o, o3/o4
    anthropic   — Claude Sonnet/Opus/Haiku
    deepseek    — DeepSeek Chat / R1
    qwen        — Alibaba Qwen (DashScope international)
    ollama      — local models, no key required

Streamlit UI (optional):

    from byok_llm.streamlit_ui import render_key_manager, render_model_selector

Standalone GitHub setup:
    Copy this folder to a new repo, add pyproject.toml with:
        [project]
        name = "byok-llm"
        version = "0.1.0"
        dependencies = ["httpx>=0.27"]
    Then: pip install -e .
"""

from byok_llm.router import LLMRouter

__all__ = ["LLMRouter"]
__version__ = "0.1.0"
