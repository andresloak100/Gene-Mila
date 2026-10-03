"""OpenAI-compatible chat-completions providers (DeepSeek, OpenAI, Grok,
vLLM/Ollama/OpenCode-style local servers).

The API key is read from the environment at call time and is never stored on
the object, logged, or included in error messages.
"""

from __future__ import annotations

import os
import time

import requests

from .base import AgentProvider, LLMResponse, ProviderError, Usage


class OpenAICompatProvider(AgentProvider):
    def __init__(self, model: str, base_url: str, api_key_env: str, timeout_s: float = 120,
                 name: str = "openai_compat", temperature: float = 0.7):
        super().__init__(model)
        self.base_url = base_url.rstrip("/")
        self.api_key_env = api_key_env
        self.timeout_s = timeout_s
        self.name = name
        self.temperature = temperature

    def available(self) -> bool:
        return bool(os.environ.get(self.api_key_env))

    def complete(self, system: str, user: str, max_tokens: int) -> LLMResponse:
        key = os.environ.get(self.api_key_env)
        if not key:
            raise ProviderError(f"environment variable {self.api_key_env} is not set", retryable=False)
        body = {"model": self.model, "max_tokens": int(max_tokens), "temperature": self.temperature,
                "stream": False,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
        t0 = time.monotonic()
        try:
            r = requests.post(f"{self.base_url}/chat/completions", json=body, timeout=self.timeout_s,
                              headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        except requests.RequestException as exc:
            raise ProviderError(f"{self.name} request failed: {type(exc).__name__}") from None
        finally:
            del key
        latency = time.monotonic() - t0
        if r.status_code != 200:
            retry = r.status_code in (429, 500, 502, 503, 504)
            try:
                msg = r.json().get("error", {}).get("message", "")[:300]
            except ValueError:
                msg = r.text[:300]
            raise ProviderError(f"{self.name} HTTP {r.status_code}: {msg}", retryable=retry)
        data = r.json()
        u = data.get("usage", {}) or {}
        cached = u.get("prompt_cache_hit_tokens")
        if cached is None:
            cached = (u.get("prompt_tokens_details") or {}).get("cached_tokens", 0) or 0
        usage = Usage(input_tokens=int(u.get("prompt_tokens", 0)), output_tokens=int(u.get("completion_tokens", 0)),
                      cached_tokens=int(cached), latency_s=latency)
        text = data["choices"][0]["message"].get("content") or ""
        return LLMResponse(text=text, usage=usage, provider=self.name, model=data.get("model", self.model))


class DeepSeekProvider(OpenAICompatProvider):
    def __init__(self, model: str = "deepseek-chat", timeout_s: float = 120):
        super().__init__(model=model, base_url="https://api.deepseek.com", api_key_env="DEEPSEEK_API_KEY",
                         timeout_s=timeout_s, name="deepseek")
