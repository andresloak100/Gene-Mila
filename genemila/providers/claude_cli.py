"""Claude via the Claude Code CLI in non-interactive mode (`claude -p`).

Uses whatever authentication the local CLI already has (subscription or API
key). Tools are disabled: the planner only reasons over the text it is given.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import time

from .base import AgentProvider, LLMResponse, ProviderError, Usage


class ClaudeCLIProvider(AgentProvider):
    name = "claude_cli"

    def __init__(self, model: str = "opus", timeout_s: float = 300, binary: str = "claude"):
        super().__init__(model)
        self.timeout_s = timeout_s
        self.binary = binary

    def available(self) -> bool:
        return shutil.which(self.binary) is not None

    def complete(self, system: str, user: str, max_tokens: int) -> LLMResponse:
        cmd = [self.binary, "-p", "--output-format", "json", "--model", self.model, "--tools", "",
               "--system-prompt", system, "--no-session-persistence", "--strict-mcp-config"]
        t0 = time.monotonic()
        with tempfile.TemporaryDirectory() as tmp:
            try:
                r = subprocess.run(cmd, input=user, capture_output=True, text=True, timeout=self.timeout_s, cwd=tmp)
            except subprocess.TimeoutExpired:
                raise ProviderError("claude CLI timed out") from None
            except FileNotFoundError:
                raise ProviderError("claude CLI not installed", retryable=False) from None
        try:
            data = json.loads(r.stdout)
        except json.JSONDecodeError:
            raise ProviderError(f"claude CLI returned non-JSON output (exit {r.returncode}): "
                                f"{(r.stderr or r.stdout)[:300]}") from None
        if data.get("is_error") or r.returncode != 0:
            raise ProviderError(f"claude CLI error: {str(data.get('result'))[:300]}")
        u = data.get("usage", {})
        cached = int(u.get("cache_read_input_tokens", 0))
        usage = Usage(
            input_tokens=int(u.get("input_tokens", 0)) + int(u.get("cache_creation_input_tokens", 0)) + cached,
            output_tokens=int(u.get("output_tokens", 0)), cached_tokens=cached,
            cost_usd=data.get("total_cost_usd"), latency_s=time.monotonic() - t0)
        return LLMResponse(text=data.get("result", ""), usage=usage, provider=self.name, model=self.model)
