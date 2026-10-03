"""Provider abstraction.

The scientific pipeline only ever talks to AgentProvider. A provider needs
one primitive, complete(system, user, max_tokens); the four research
operations (propose / implement / diagnose / summarize) are built from it with
the prompts in genemila.prompts, so adding Grok, OpenAI, a local model or any
other backend means implementing complete() and nothing else. Providers that
are not LLMs (mock, scripted planner) override the operations directly.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .. import prompts


class ProviderError(RuntimeError):
    def __init__(self, message: str, retryable: bool = True):
        super().__init__(message)
        self.retryable = retryable


@dataclass
class Usage:
    input_tokens: int = 0          # total prompt tokens (including cached)
    output_tokens: int = 0
    cached_tokens: int = 0         # prompt tokens served from cache
    cost_usd: float | None = None  # provider-reported cost, if any
    latency_s: float = 0.0


@dataclass
class LLMResponse:
    text: str
    usage: Usage = field(default_factory=Usage)
    provider: str = ""
    model: str = ""


class AgentProvider(ABC):
    name: str = "base"

    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def complete(self, system: str, user: str, max_tokens: int) -> LLMResponse:
        ...

    # -- research operations ------------------------------------------------------
    def propose(self, research_state: str, n: int, mix: dict, max_tokens: int) -> LLMResponse:
        return self.complete(prompts.PLANNER_SYSTEM, prompts.planner_user(research_state, n, mix), max_tokens)

    def implement(self, task: dict, max_tokens: int) -> LLMResponse:
        return self.complete(prompts.WORKER_SYSTEM, prompts.worker_implement(task), max_tokens)

    def diagnose(self, task: dict, code: str, error: str, max_tokens: int) -> LLMResponse:
        return self.complete(prompts.WORKER_SYSTEM, prompts.worker_diagnose(task, code, error), max_tokens)

    def summarize(self, research_state: str, max_tokens: int) -> LLMResponse:
        return self.complete(prompts.SUMMARY_SYSTEM, research_state, max_tokens)


def extract_code(text: str) -> str:
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text, flags=re.S)
    if blocks:
        return max(blocks, key=len).strip() + "\n"
    return text.strip() + "\n"
