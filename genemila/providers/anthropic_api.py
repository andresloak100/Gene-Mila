"""Claude via the Anthropic Messages API (needs ANTHROPIC_API_KEY)."""

from __future__ import annotations

import os
import time

import requests

from .base import AgentProvider, LLMResponse, ProviderError, Usage


class AnthropicProvider(AgentProvider):
    name = "anthropic"

    def __init__(self, model: str = "claude-opus-5-5", timeout_s: float = 300):
        super().__init__(model)
        self.timeout_s = timeout_s

    def complete(self, system: str, user: str, max_tokens: int) -> LLMResponse:
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ProviderError("ANTHROPIC_API_KEY is not set", retryable=False)
        t0 = time.monotonic()
        try:
            r = requests.post("https://api.anthropic.com/v1/messages", timeout=self.timeout_s, headers={
                "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": self.model, "max_tokens": max_tokens, "system": system,
                      "messages": [{"role": "user", "content": user}]})
        except requests.RequestException as exc:
            raise ProviderError(f"anthropic request failed: {type(exc).__name__}") from None
        if r.status_code != 200:
            raise ProviderError(f"anthropic HTTP {r.status_code}: {r.text[:300]}",
                                retryable=r.status_code in (429, 500, 529))
        data = r.json()
        u = data.get("usage", {})
        cached = int(u.get("cache_read_input_tokens", 0) or 0)
        text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        return LLMResponse(text=text, provider=self.name, model=self.model, usage=Usage(
            input_tokens=int(u.get("input_tokens", 0)) + cached + int(u.get("cache_creation_input_tokens", 0) or 0),
            output_tokens=int(u.get("output_tokens", 0)), cached_tokens=cached, latency_s=time.monotonic() - t0))
