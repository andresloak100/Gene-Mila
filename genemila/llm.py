"""LLM gateway: the only path from the lab to any LLM provider.

It enforces, before every call:
  * per-run spend caps per role (worker / planner) and cumulative per-provider
    caps across runs (persistent ledger), using a worst-case cost reservation,
  * per-experiment and per-worker token limits,
  * a bounded number of API retries and a circuit breaker,
and records input / output / cached tokens, latency and estimated cost for
every call in the experiment database and the cumulative ledger.
"""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path

from .db import Database
from .providers.base import AgentProvider, LLMResponse, ProviderError, Usage


class BudgetExceeded(RuntimeError):
    pass


class TokenLimitExceeded(RuntimeError):
    pass


class SpendLedger:
    """Cumulative spend across runs (survives restarts)."""

    def __init__(self, path: str | Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = str(path)
        self._lock = threading.Lock()
        with self._conn() as c:
            c.execute("CREATE TABLE IF NOT EXISTS spend (ts REAL, run_id TEXT, provider TEXT, model TEXT, "
                      "role TEXT, input_tokens INTEGER, output_tokens INTEGER, cached_tokens INTEGER, cost_usd REAL)")

    def _conn(self):
        return sqlite3.connect(self.path, timeout=30)

    def total(self, provider: str) -> float:
        with self._lock, self._conn() as c:
            return float(c.execute("SELECT COALESCE(SUM(cost_usd),0) FROM spend WHERE provider=?",
                                   (provider,)).fetchone()[0])

    def add(self, run_id, provider, model, role, usage: Usage, cost: float) -> None:
        with self._lock, self._conn() as c:
            c.execute("INSERT INTO spend VALUES (?,?,?,?,?,?,?,?,?)",
                      (time.time(), run_id, provider, model, role, usage.input_tokens, usage.output_tokens,
                       usage.cached_tokens, cost))


class LLMGateway:
    def __init__(self, db: Database, cfg: dict, run_id: str, ledger: SpendLedger | None = None):
        b = cfg["budget"]
        self.db = db
        self.run_id = run_id
        self.pricing = cfg.get("pricing", {})
        self.role_caps = {"worker": float(b["max_total_usd"]), "planner": float(b["max_planner_usd"])}
        self.cumulative_caps = {k: float(v) for k, v in b.get("cumulative_usd", {}).items()}
        self.max_tokens_experiment = int(b["max_tokens_per_experiment"])
        self.max_tokens_worker = int(b["max_tokens_per_worker"])
        self.api_retries = int(b.get("api_retries", 1))
        self.breaker_limit = int(b.get("circuit_breaker_failures", 5))
        self.ledger = ledger
        self._lock = threading.Lock()
        self.spent = {"worker": 0.0, "planner": 0.0}
        self.reserved = {"worker": 0.0, "planner": 0.0}
        self.provider_spent_run: dict[str, float] = {}
        self.provider_reserved: dict[str, float] = {}
        self.tokens_by_worker: dict[str, int] = {}
        self.tokens_by_experiment: dict[str, int] = {}
        self.consecutive_failures: dict[str, int] = {}
        self.halted: dict[str, str] = {}  # role or provider -> reason
        self._ledger_base = {p: (ledger.total(p) if ledger else 0.0) for p in self.cumulative_caps}

    # ----------------------------------------------------------------- pricing
    def price(self, model: str) -> dict:
        return self.pricing.get(model) or self.pricing.get("default") or {
            "input_cache_hit": 3.0, "input_cache_miss": 3.0, "output": 15.0}

    def cost(self, model: str, usage: Usage) -> float:
        if usage.cost_usd is not None:
            return float(usage.cost_usd)
        p = self.price(model)
        miss = max(0, usage.input_tokens - usage.cached_tokens)
        return (usage.cached_tokens * p["input_cache_hit"] + miss * p["input_cache_miss"]
                + usage.output_tokens * p["output"]) / 1e6

    def worst_case(self, model: str, est_input_tokens: int, max_tokens: int) -> float:
        p = self.price(model)
        return (est_input_tokens * p["input_cache_miss"] + max_tokens * p["output"]) / 1e6

    # ------------------------------------------------------------------- checks
    def remaining(self, role: str) -> float:
        with self._lock:
            return self.role_caps[role] - self.spent[role] - self.reserved[role]

    def is_halted(self, role: str, provider: str) -> str | None:
        return self.halted.get(role) or self.halted.get(provider)

    def _reserve(self, role, provider_name, model, est_in, max_tokens, worker_id, experiment_id) -> float:
        with self._lock:
            why = self.is_halted(role, provider_name)
            if why:
                raise BudgetExceeded(why)
            if experiment_id and self.tokens_by_experiment.get(experiment_id, 0) + est_in > self.max_tokens_experiment:
                raise TokenLimitExceeded(f"experiment {experiment_id} token limit {self.max_tokens_experiment} reached")
            if worker_id and self.tokens_by_worker.get(worker_id, 0) + est_in > self.max_tokens_worker:
                raise TokenLimitExceeded(f"worker {worker_id} token limit {self.max_tokens_worker} reached")
            wc = self.worst_case(model, est_in, max_tokens)
            if self.spent[role] + self.reserved[role] + wc > self.role_caps[role]:
                self.halted[role] = (f"{role} budget ${self.role_caps[role]:.4f} reached "
                                     f"(spent ${self.spent[role]:.4f}); no new {role} API calls")
                raise BudgetExceeded(self.halted[role])
            if provider_name in self.cumulative_caps:
                cum = (self._ledger_base[provider_name] + self.provider_spent_run.get(provider_name, 0.0)
                       + self.provider_reserved.get(provider_name, 0.0) + wc)
                if cum > self.cumulative_caps[provider_name]:
                    self.halted[provider_name] = (f"cumulative {provider_name} budget "
                                                  f"${self.cumulative_caps[provider_name]:.4f} reached")
                    raise BudgetExceeded(self.halted[provider_name])
            self.reserved[role] += wc
            self.provider_reserved[provider_name] = self.provider_reserved.get(provider_name, 0.0) + wc
            return wc

    def _settle(self, role, provider_name, wc, cost, tokens, worker_id, experiment_id) -> None:
        with self._lock:
            self.reserved[role] -= wc
            self.provider_reserved[provider_name] -= wc
            self.spent[role] += cost
            self.provider_spent_run[provider_name] = self.provider_spent_run.get(provider_name, 0.0) + cost
            if worker_id:
                self.tokens_by_worker[worker_id] = self.tokens_by_worker.get(worker_id, 0) + tokens
            if experiment_id:
                self.tokens_by_experiment[experiment_id] = self.tokens_by_experiment.get(experiment_id, 0) + tokens

    # --------------------------------------------------------------------- call
    def call(self, provider: AgentProvider, op: str, *, role: str, max_tokens: int, est_input_tokens: int,
             experiment_id: str | None = None, worker_id: str | None = None, **kwargs) -> LLMResponse:
        pname = provider.name
        attempts = 0
        while True:
            attempts += 1
            wc = self._reserve(role, pname, provider.model, est_input_tokens, max_tokens, worker_id, experiment_id)
            t0 = time.monotonic()
            try:
                resp = getattr(provider, op)(max_tokens=max_tokens, **kwargs)
            except ProviderError as exc:
                self._settle(role, pname, wc, 0.0, 0, worker_id, experiment_id)
                self._record(role, pname, provider.model, experiment_id, worker_id, op, Usage(
                    latency_s=time.monotonic() - t0), 0.0, ok=False, error=str(exc))
                with self._lock:
                    n = self.consecutive_failures[pname] = self.consecutive_failures.get(pname, 0) + 1
                    if n >= self.breaker_limit:
                        self.halted[pname] = f"circuit breaker: {n} consecutive {pname} failures"
                if exc.retryable and attempts <= self.api_retries:
                    time.sleep(min(8.0, 2.0 * attempts))
                    continue
                raise
            except Exception:
                self._settle(role, pname, wc, 0.0, 0, worker_id, experiment_id)
                raise
            cost = self.cost(resp.model or provider.model, resp.usage)
            tokens = resp.usage.input_tokens + resp.usage.output_tokens
            self._settle(role, pname, wc, cost, tokens, worker_id, experiment_id)
            with self._lock:
                self.consecutive_failures[pname] = 0
            self._record(role, pname, resp.model or provider.model, experiment_id, worker_id, op, resp.usage, cost,
                         ok=True)
            return resp

    def _record(self, role, provider, model, experiment_id, worker_id, purpose, usage: Usage, cost, ok, error=None):
        self.db.log_llm_call(role=role, provider=provider, model=model, experiment_id=experiment_id,
                             worker_id=worker_id, purpose=purpose, input_tokens=usage.input_tokens,
                             output_tokens=usage.output_tokens, cached_tokens=usage.cached_tokens, cost_usd=cost,
                             latency_s=usage.latency_s, ok=int(ok), error=(error or None) and error[:500])
        if self.ledger and ok:
            self.ledger.add(self.run_id, provider, model, role, usage, cost)
