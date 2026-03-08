"""
BaseProvider — abstract contract every LLM provider must satisfy.

Each provider implements two methods:
    call()     → returns the LLM response as a plain string
    validate() → returns True if the key + model pair is reachable

All network I/O uses raw httpx (no LangChain dependency).
"""

from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Abstract base for all BYOK-LLM provider adapters."""

    @abstractmethod
    def call(
        self,
        prompt: str,
        api_key: str,
        model: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """
        Send a prompt to the provider and return the response text.

        Args:
            prompt:      User message / main prompt.
            api_key:     Provider API key (empty string for Ollama).
            model:       Model ID string (provider-specific format).
            system:      Optional system instruction.
            temperature: Sampling temperature (0.0–2.0).
            max_tokens:  Maximum output tokens.

        Returns:
            Response text as a plain string.

        Raises:
            httpx.HTTPStatusError: On 4xx/5xx responses.
            httpx.TimeoutException: On timeout.
        """

    @abstractmethod
    def validate(self, api_key: str, model: str) -> bool:
        """
        Lightweight check that the key + model are reachable.

        Makes a minimal API call (max_tokens=1) to confirm credentials.
        Returns True on success, False on any error.
        """
