"""
Ollama provider — local inference, no API key required.

API: http://localhost:11434  (default; configurable via OLLAMA_HOST)
Docs: https://github.com/ollama/ollama/blob/main/docs/api.md

The validate() method only checks if the Ollama server is running.
It does NOT check if the specific model is pulled — that's a runtime concern.
"""

import os

import httpx

from byok_llm.providers.base import BaseProvider

_DEFAULT_HOST = "http://localhost:11434"
_TIMEOUT      = 300   # local models can be slow on first load


def _host() -> str:
    return os.environ.get("OLLAMA_HOST", _DEFAULT_HOST).rstrip("/")


class OllamaProvider(BaseProvider):

    def call(
        self,
        prompt: str,
        api_key: str,          # ignored — Ollama needs no key
        model: str,
        *,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = httpx.post(
            f"{_host()}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]

    def validate(self, api_key: str, model: str) -> bool:
        """Returns True if the Ollama server is reachable (regardless of model)."""
        try:
            resp = httpx.get(f"{_host()}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
