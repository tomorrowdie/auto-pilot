"""
LLMRouter — the single entry point for all BYOK-LLM calls.

Usage (any project):

    from byok_llm import LLMRouter

    router = LLMRouter()

    # Call an LLM
    text = router.call(
        prompt="Summarise this product review...",
        provider="openrouter",
        api_key="sk-or-...",
        model="anthropic/claude-sonnet-4-5",
        system="You are a concise analyst.",
        temperature=0.3,
    )

    # Validate a key before saving it
    ok = router.validate(provider="google", api_key="AIza...", model="gemini-2.5-flash-preview-05-20")

Provider IDs (see models.py for full list):
    "openrouter"  → OpenRouter gateway  (recommended)
    "google"      → Google Gemini
    "openai"      → OpenAI GPT
    "anthropic"   → Anthropic Claude
    "deepseek"    → DeepSeek
    "qwen"        → Alibaba Qwen (DashScope international)
    "ollama"      → Local Ollama (no key required)
"""

from byok_llm.providers.anthropic import AnthropicProvider
from byok_llm.providers.base import BaseProvider
from byok_llm.providers.google import GoogleProvider
from byok_llm.providers.ollama import OllamaProvider
from byok_llm.providers.openai_compat import OpenAICompatProvider
from byok_llm.providers.openrouter import OpenRouterProvider
from byok_llm.providers.qwen import QwenProvider


def _build_registry() -> dict[str, BaseProvider]:
    _qwen   = QwenProvider()
    _ollama = OllamaProvider()
    return {
        "openrouter":  OpenRouterProvider(),
        "google":      GoogleProvider(),
        "openai":      OpenAICompatProvider("https://api.openai.com/v1"),
        "anthropic":   AnthropicProvider(),
        "deepseek":    OpenAICompatProvider("https://api.deepseek.com/v1"),
        "qwen":        _qwen,
        "ollama":      _ollama,
        # Backward-compat aliases (old registry.py used these IDs)
        "alibaba":     _qwen,    # legacy name for Qwen/DashScope
        "local_ollama": _ollama, # legacy name for Ollama
    }


class LLMRouter:
    """
    Stateless router that dispatches LLM calls to the correct provider.

    Create one instance per application (or per call — it holds no state).
    """

    def __init__(self) -> None:
        self._registry: dict[str, BaseProvider] = _build_registry()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def call(
        self,
        prompt: str,
        provider: str,
        api_key: str,
        model: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """
        Send a prompt to an LLM and return the response as a plain string.

        Args:
            prompt:      The user message / main prompt text.
            provider:    Provider ID (e.g. "openrouter", "google", "anthropic").
            api_key:     API key for the provider (empty string for Ollama).
            model:       Model ID in the provider's format.
            system:      Optional system instruction / persona.
            temperature: Sampling temperature (0.0–2.0). Default 0.7.
            max_tokens:  Maximum tokens to generate. Default 4096.

        Returns:
            Response text as a plain string.

        Raises:
            ValueError: If the provider ID is not recognised.
            httpx.HTTPStatusError: On 4xx/5xx from the provider.
            httpx.TimeoutException: On network timeout.
        """
        adapter = self._get_adapter(provider)
        return adapter.call(
            prompt,
            api_key,
            model,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def validate(self, provider: str, api_key: str, model: str) -> bool:
        """
        Lightweight connectivity check for a provider key + model pair.

        Makes a minimal API call (max_tokens=1) and returns True on success.
        Safe to call before saving a key — never raises, only returns bool.

        Args:
            provider: Provider ID.
            api_key:  API key to test.
            model:    Model ID to test.

        Returns:
            True if the key is valid and the model is reachable, else False.
        """
        try:
            adapter = self._get_adapter(provider)
            return adapter.validate(api_key, model)
        except ValueError:
            return False

    def providers(self) -> list[str]:
        """Return all registered provider IDs."""
        return list(self._registry.keys())

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_adapter(self, provider: str) -> BaseProvider:
        adapter = self._registry.get(provider)
        if adapter is None:
            known = ", ".join(sorted(self._registry))
            raise ValueError(
                f"Unknown provider '{provider}'. Known providers: {known}"
            )
        return adapter
