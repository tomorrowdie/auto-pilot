"""
Google Gemini provider — direct REST API (no SDK dependency).

API: generativelanguage.googleapis.com/v1beta
Docs: https://ai.google.dev/api/generate-content

Auth: API key as a query parameter (?key=...)
"""

import httpx

from byok_llm.providers.base import BaseProvider

_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
_TIMEOUT  = 120


class GoogleProvider(BaseProvider):

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
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}

        resp = httpx.post(
            f"{_BASE_URL}/{model}:generateContent",
            params={"key": api_key},
            json=payload,
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    def validate(self, api_key: str, model: str) -> bool:
        try:
            resp = httpx.post(
                f"{_BASE_URL}/{model}:generateContent",
                params={"key": api_key},
                json={
                    "contents": [{"parts": [{"text": "hi"}]}],
                    "generationConfig": {"maxOutputTokens": 1},
                },
                timeout=15,
            )
            return resp.status_code == 200
        except Exception:
            return False
