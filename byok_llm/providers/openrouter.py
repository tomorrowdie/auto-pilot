"""
OpenRouter provider — unified gateway to 100s of models.

API: OpenAI-compatible chat/completions endpoint.
Docs: https://openrouter.ai/docs

Model ID format: "{company}/{model-slug}"
    e.g. "anthropic/claude-sonnet-4-5", "google/gemini-2.5-flash"
"""

import httpx

from byok_llm.providers.base import BaseProvider

_BASE_URL = "https://openrouter.ai/api/v1"
_TIMEOUT  = 120


class OpenRouterProvider(BaseProvider):

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
            f"{_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                # Recommended by OpenRouter for app attribution
                "HTTP-Referer": "https://github.com/byok-llm",
                "X-Title": "BYOK-LLM",
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
                f"{_BASE_URL}/chat/completions",
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
            # 200 = success, 400 = bad request but key is valid
            return resp.status_code in (200, 400)
        except Exception:
            return False
