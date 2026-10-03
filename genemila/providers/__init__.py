"""Replaceable LLM providers behind one interface (see base.AgentProvider)."""

from __future__ import annotations

from .base import AgentProvider, LLMResponse, ProviderError, Usage


def make_provider(kind: str, model: str, cfg: dict | None = None) -> AgentProvider:
    cfg = cfg or {}
    if kind == "deepseek":
        from .openai_compat import DeepSeekProvider
        return DeepSeekProvider(model=model, timeout_s=cfg.get("timeout_s", 120))
    if kind == "openai_compat":
        from .openai_compat import OpenAICompatProvider
        return OpenAICompatProvider(model=model, base_url=cfg["base_url"], api_key_env=cfg["api_key_env"],
                                    timeout_s=cfg.get("timeout_s", 120), name=cfg.get("name", "openai_compat"))
    if kind == "claude_cli":
        from .claude_cli import ClaudeCLIProvider
        return ClaudeCLIProvider(model=model, timeout_s=cfg.get("timeout_s", 300))
    if kind == "anthropic":
        from .anthropic_api import AnthropicProvider
        return AnthropicProvider(model=model, timeout_s=cfg.get("timeout_s", 300))
    if kind == "mock":
        from .mock import MockProvider
        return MockProvider(model=model or "mock", **{k: v for k, v in cfg.items() if k in ("fail_rate", "seed")})
    if kind == "scripted":
        from .mock import ScriptedPlanner
        return ScriptedPlanner()
    raise ValueError(f"unknown provider {kind!r}")


__all__ = ["AgentProvider", "LLMResponse", "ProviderError", "Usage", "make_provider"]
