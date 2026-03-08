"""
OpenAI-compatible provider — handles OpenAI and DeepSeek.

Both use identical request/response shapes; only base_url differs.
Instantiate with the correct base_url for each provider.

    OpenAI:   OpenAICompatProvider("https://api.openai.com/v1")
    DeepSeek: OpenAICompatProvider("https://api.deepseek.com/v1")

Docs (OpenAI):   https://platform.openai.com/docs/api-reference/chat
Docs (DeepSeek): https://platform.deepseek.com/api-docs/
"""

import httpx

from byok_llm.providers.base import BaseProvider

_TIMEOUT = 120


class OpenAICompatProvider(BaseProvider):
    """OpenAI chat/completions-compatible provider."""

    def __init__(self, base_url: str = "https://api.openai.com/v1") -> None:
        self._base_url = base_url.rstrip("/")

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
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = httpx.post(
            f"{self._base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def validate(self, api_key: str, model: str) -> bool:
        try:
            resp = httpx.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 1,
                },
                timeout=15,
            )
            # 400 = bad request but the key itself was accepted
            return resp.status_code in (200, 400)
        except Exception:
            return False
