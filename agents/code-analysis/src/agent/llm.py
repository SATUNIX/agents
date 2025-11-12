"""Minimal OpenAI-compatible client wrapper."""

from __future__ import annotations

from typing import Any, Dict

try:  # pragma: no cover - import shim for environments without deps installed
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]

from .config import AgentConfig


class LLMClient:
    """Thin convenience layer around the OpenAI SDK."""

    def __init__(self, config: AgentConfig) -> None:
        if OpenAI is None:
            raise RuntimeError(
                "openai package not available. Install dependencies via `pip install -r requirements.txt`."
            )
        self._client = OpenAI(api_key=config.openai_api_key, base_url=config.openai_base_url)
        self._model = config.agent_model

    def complete(self, prompt: str, **overrides: Any) -> str:
        """Request a deterministic completion and return the text body."""

        params: Dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": "You are a helpful planning agent."},
                {"role": "user", "content": prompt},
            ],
            "temperature": overrides.get("temperature", 0.1),
            "max_tokens": overrides.get("max_tokens", 512),
        }
        response = self._client.chat.completions.create(**params)
        text = response.choices[0].message.content or ""
        return text.strip()
