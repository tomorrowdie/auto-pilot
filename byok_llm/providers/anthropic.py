"""
Anthropic Claude provider — direct Messages API (no SDK dependency).

API: api.anthropic.com/v1/messages
Docs: https://docs.anthropic.com/en/api/messages

Note: system prompt is a top-level field, not a message role.
"""

import httpx

from byok_llm.providers.base import BaseProvider

_BASE_URL        = "https://api.anthropic.com/v1/messages"
_API_VERSION     = "2023-06-01"
_TIMEOUT         = 120


class AnthropicProvider(BaseProvider):

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
        payload: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system

        resp = httpx.post(
            _BASE_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": _API_VERSION,
                "content-type": "application/json",
            },
            json=payload,
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]

    def validate(self, api_key: str, model: str) -> bool:
        try:
            resp = httpx.post(
                _BASE_URL,
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": _API_VERSION,
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "hi"}],
                },
                timeout=15,
            )
            # 400 = bad request (e.g. invalid model) but key was accepted
            return resp.status_code in (200, 400)
        except Exception:
            return False
