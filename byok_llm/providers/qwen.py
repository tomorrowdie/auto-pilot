"""
Alibaba Qwen provider — DashScope international compatible-mode.

Uses the OpenAI-compatible endpoint, so inherits OpenAICompatProvider.
Override only: temperature guard (thinking models require >= 0.6).

Docs: https://www.alibabacloud.com/help/en/model-studio/developer-reference/compatibility-of-openai-with-dashscope
"""

from byok_llm.providers.openai_compat import OpenAICompatProvider

_DASHSCOPE_BASE = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

# Qwen thinking/reasoning models enforce a minimum temperature
_MIN_TEMPERATURE = 0.6


class QwenProvider(OpenAICompatProvider):

    def __init__(self) -> None:
        super().__init__(base_url=_DASHSCOPE_BASE)

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
        # Enforce minimum temperature for Qwen thinking models
        if temperature < _MIN_TEMPERATURE:
            temperature = _MIN_TEMPERATURE
        return super().call(
            prompt,
            api_key,
            model,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
        )
