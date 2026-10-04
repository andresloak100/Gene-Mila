"""Planner / principal investigator loop.

The LLM proposes hypotheses from the compressed research state. Python turns
them into validated experiment specifications: it expands sweeps without any
LLM, fans out replicates for implementation diversity, resolves parents, and
prioritises according to the configured exploration/exploitation mix.
"""

from __future__ import annotations

import copy
import json
import re
import threading
import time

from .lab import Lab
from .llm import BudgetExceeded
from .providers.base import AgentProvider, ProviderError
from .research_state import build_state, render_state
from .spec import ExperimentSpec


def parse_json(text: str) -> dict:
    text = text.strip()
    m = re.search(r"```(?:json)?\s*\n(.*?)```", text, flags=re.S)
    if m:
        text = m.group(1)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError("planner response contains no JSON object")
    return json.loads(text[start:end + 1])


PARSE_FAILURES_BEFORE_SWITCH = 3  # unparseable plans in a row before the planner is treated as down


class Planner:
    """One planner provider at a time, with an ordered chain of fallbacks. A provider that fails (usage
    limit, API error, budget halt) is replaced by the next one in the chain for the rest of the run: the
    switch is sticky, logged as a `planner_switch` event, and the summary and the results tables label the
    run as a mixed-planner arm. When the chain is exhausted the run goes on without a planner (the queue
    drains and the deterministic exploit engine keeps proposing) and a `planner_exhausted` event says so;
    an LLM arm never degrades silently to the scripted planner."""

    def __init__(self, lab: Lab, provider: AgentProvider, fallback=None):
        self.lab = lab
        self.provider = provider
        self.primary = provider
        self.fallbacks: list[AgentProvider] = list(fallback) if isinstance(fallback, (list, tuple)) else (
            [fallback] if fallback is not None else [])
        self.cfg = lab.cfg
        self.rounds = 0
        self.last_call = 0.0
        self.last_queued = -1
        self.last_failed = False
        self.empty_rounds = 0  # consecutive rounds that queued nothing
        self.parse_failures = 0  # consecutive rounds whose response held no usable plan
        self.switches: list[dict] = []
        self.exhausted = False
        self._lock = threading.Lock()  # several planner rounds may run concurrently
        if hasattr(provider, "available") and not provider.available():
            self._switch(provider, "not usable here")

    @property
    def fallback(self) -> AgentProvider | None:
        return self.fallbacks[0] if self.fallbacks else None

    def backing_off(self, min_interval_s: float) -> bool:
        """Wait min_interval_s after a round that failed or produced nothing new (never hammer the planner)."""
        with self._lock:
            return (self.rounds > 0 and (self.last_queued == 0 or self.last_failed)
                    and time.time() - self.last_call < min_interval_s)

    def dry(self) -> bool:
        """The planner will produce nothing more: every provider in the chain failed, or a deterministic
        planner returned nothing three rounds in a row. A working LLM planner is never considered dry."""
        if self.exhausted:
            return True
        llm_usable = self.provider.name not in ("scripted",) and not self.lab.gateway.is_halted("planner",
                                                                                              self.provider.name)
        return self.empty_rounds >= 3 and not llm_usable

    def _switch(self, failed: AgentProvider, reason: str) -> AgentProvider | None:
        """Replace `failed` by the next provider in the chain, for this and every later round. Returns the
        provider to use now, or None when the chain is exhausted. A concurrent round may have switched
        already; then its choice is followed."""
        with self._lock:
            if self.provider is not failed:
                return self.provider
            self.parse_failures = 0
            while self.fallbacks:
                nxt = self.fallbacks.pop(0)
                if hasattr(nxt, "available") and not nxt.available():
                    self.lab.db.event("planner_switch", f"{nxt.name}:{nxt.model} skipped: not usable here",
                                      level="warning")
                    continue
                self.provider = nxt
                self.switches.append({"ts": time.time(), "from": f"{failed.name}:{failed.model}",
                                      "to": f"{nxt.name}:{nxt.model}", "reason": reason[:300]})
                self.lab.db.event("planner_switch", f"{failed.name}:{failed.model} -> {nxt.name}:{nxt.model} "
                                  f"({reason})"[:500], level="warning")
                return nxt
            if not self.exhausted:
                self.exhausted = True
                self.lab.db.event("planner_exhausted", f"{failed.name}:{failed.model} failed ({reason}) and no "
                                  "fallback planner is left; the run continues without a planner"[:500],
                                  level="error")
            return None

    def _ask(self, provider: AgentProvider, text: str, n: int) -> dict:
        if provider.name == "scripted":  # deterministic and free: not metered
            return parse_json(provider.propose(research_state=text, n=n, mix=self.mix(), max_tokens=0).text)
        resp = self.lab.gateway.call(provider, "propose", role="planner",
                                     max_tokens=int(self.cfg["planner"]["max_output_tokens"]),
                                     est_input_tokens=len(text) // 3 + 1500,
                                     research_state=text, n=n, mix=self.mix())
        return parse_json(resp.text)

    def mix(self) -> dict:
        s = self.cfg["schedule"]
        total = s["explore"] + s["exploit"] + s["risky"]
        return {k: s[k] / total for k in ("explore", "exploit", "risky")}

    # ------------------------------------------------------------------ round
    def refill(self, n: int, focus: str | None = None) -> list[str]:
        """Ask for ~n hypotheses and queue the resulting experiments. Returns queued ids."""
        state = build_state(self.lab)
        text = render_state(state)
        if focus:
            text += f"\n## YOUR FOCUS FOR THIS ROUND\n{focus}\n(Other planner rounds run in parallel with other focuses.)"
        with self._lock:
            self.rounds += 1
            rnd = self.rounds
            self.last_call = time.time()
        (self.lab.run_dir / "planner").mkdir(exist_ok=True)
        (self.lab.run_dir / "planner" / f"state_{rnd:03d}.txt").write_text(text)
        provider = self.provider
        failed = False
        if self.exhausted:
            with self._lock:
                self.last_failed, self.last_queued = True, 0
            return []
        while True:
            try:
                plan = self._ask(provider, text, n)
                with self._lock:
                    self.parse_failures = 0
                break
            except (ProviderError, BudgetExceeded, ValueError, json.JSONDecodeError) as exc:
                self.lab.db.event("planner_error", f"{provider.name}:{provider.model}: {exc}"[:500], level="warning")
                failed = True
                if isinstance(exc, (ValueError, json.JSONDecodeError)) and not isinstance(exc, BudgetExceeded):
                    with self._lock:  # a malformed answer is not an outage: switch only when it repeats
                        self.parse_failures += 1
                        repeated = self.parse_failures >= PARSE_FAILURES_BEFORE_SWITCH
                    if not repeated:
                        with self._lock:
                            self.last_failed, self.last_queued = True, 0
                        return []
                nxt = self._switch(provider, f"{type(exc).__name__}: {exc}")
                if nxt is None:
                    with self._lock:
                        self.last_failed, self.last_queued = True, 0
                    return []
                provider = nxt
        (self.lab.run_dir / "planner" / f"plan_{rnd:03d}.json").write_text(json.dumps(plan, indent=1))
        specs = self.to_specs(plan.get("hypotheses", []), proposer=f"{provider.name}:{provider.model}", rnd=rnd)
        queued = []
        for spec in specs:
            eid, status = self.lab.queue(spec)
            if status == "queued":
                queued.append(eid)
        self.lab.db.execute(
            "INSERT INTO planner_rounds (ts, provider, model, state_chars, n_proposed, n_queued, synthesis, raw_path) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (time.time(), provider.name, provider.model, len(text), len(specs), len(queued),
             str(plan.get("synthesis", ""))[:2000], f"planner/plan_{rnd:03d}.json"))
        with self._lock:
            self.last_queued = len(queued)
            self.last_failed = failed
            self.empty_rounds = 0 if queued else self.empty_rounds + 1
        return queued

    # ------------------------------------------------------- hypotheses -> specs
    def _priorities(self) -> dict:
        """Higher priority for categories under-represented relative to the target mix."""
        rows = self.lab.db.query("SELECT category, COUNT(*) n FROM experiments WHERE category IN "
                                 "('explore','exploit','risky') AND status!='rejected' GROUP BY category")
        counts = {r["category"]: r["n"] for r in rows}
        total = sum(counts.values()) or 1
        return {c: 10.0 * (target - counts.get(c, 0) / total) for c, target in self.mix().items()}

    def to_specs(self, hypotheses: list[dict], proposer: str, rnd: int | None = None) -> list[ExperimentSpec]:
        ecfg = self.cfg["experiment"]
        # the analytic baselines have no feature set, so they cannot be parents of a feature experiment
        modelled = self.lab.db.query("SELECT * FROM experiments WHERE status='completed' AND model_type!='none' "
                                     "AND primary_score IS NOT NULL ORDER BY primary_score DESC LIMIT 1")
        best = modelled[0] if modelled else None
        prio = self._priorities()
        known = self.lab.known_features()
        specs = []
        for h in hypotheses:
            if not isinstance(h, dict):
                continue
            try:
                specs += self._hypothesis_specs(h, best, prio, known, ecfg, proposer, len(specs),
                                                rnd or self.rounds)
            except Exception as exc:  # one malformed hypothesis must not discard the round
                self.lab.db.event("planner_hypothesis_skipped", f"{type(exc).__name__}: {exc}: "
                                  f"{json.dumps(h, default=str)[:300]}", level="warning")
        return specs

    def _hypothesis_specs(self, h: dict, best, prio, known, ecfg, proposer: str, n_before: int,
                          rnd: int) -> list[ExperimentSpec]:
        specs: list[ExperimentSpec] = []
        parent = self.lab.db.get_experiment(h["parent"]) if h.get("parent") else None
        if parent is None or parent.get("status") != "completed" or not parent.get("feature_set_json"):
            parent = best
        base_set = list((parent or {}).get("feature_set_json") or ["control_mean", "mean_response", "is_target"])
        category = h.get("category") if h.get("category") in ("explore", "exploit", "risky") else "explore"
        model = h.get("model_type") or (parent or {}).get("model_type") or ecfg["default_model"]
        if model not in ("ridge", "lasso", "elasticnet", "ols"):
            model = ecfg["default_model"]
        grid = list(ecfg["default_alpha_grid"])
        if model in ("lasso", "elasticnet"):
            grid = [a / 1000 for a in grid]
        common = dict(
            hypothesis=str(h.get("hypothesis", "")), scientific_rationale=str(h.get("rationale", "")),
            category=category, parent_experiment_id=(parent or {}).get("experiment_id"), model_type=model,
            hyperparameters={"alpha_grid": grid} if model != "ols" else {},
            feature_params=copy.deepcopy((parent or {}).get("feature_params_json") or {}),
            seed=int(self.cfg["run"].get("seed", 0)), cpu_limit_s=ecfg["cpu_limit_s"],
            ram_limit_mb=ecfg["ram_limit_mb"], timeout_s=ecfg["timeout_s"], proposer=proposer,
            priority=prio.get(category, 0.0))
        action = h.get("action", "new_feature")
        if action == "new_feature" and isinstance(h.get("new_feature"), dict):
            nf = h["new_feature"]
            try:
                reps = int(h.get("replicates", 1) or 1)
            except (TypeError, ValueError):
                reps = 1
            reps = max(1, min(reps, int(self.cfg["schedule"]["replicates_max"])))
            group = f"G_{rnd:03d}_{n_before + len(specs):03d}"
            for _ in range(reps):
                name = str(nf.get("name", "feature"))
                specs.append(ExperimentSpec(
                    kind="new_feature", feature_set=base_set + [name], hypothesis_group=group,
                    proposed_feature={"name": name, "description": str(nf.get("description", "")),
                                      "implementation_hint": str(nf.get("implementation_hint", "")),
                                      "params": nf.get("params", {})}, **common))
        elif action in ("combine", "ablate"):
            add = [f for f in (h.get("add_features") or []) if f in known and f not in base_set]
            remove = set(h.get("remove_features") or [])
            fs = [f for f in base_set if f not in remove] + add
            specs.append(ExperimentSpec(kind="config", feature_set=fs, **common))
        elif action == "sweep" and isinstance(h.get("sweep"), dict) and isinstance(h["sweep"].get("values"), list):
            specs += self.expand_sweep(h["sweep"], base_set, common)
        return specs

    @staticmethod
    def expand_sweep(sweep: dict, base_set: list[str], common: dict) -> list[ExperimentSpec]:
        """Deterministic expansion: one config experiment per value, no LLM involved."""
        target, values = str(sweep.get("target", "")), list(sweep.get("values", []))[:8]
        out = []
        for v in values:
            c = copy.deepcopy(common)
            c["proposer"] = f"sweep({c['proposer']})"
            if target == "alpha_grid":
                c["hyperparameters"] = {"alpha_grid": v if isinstance(v, list) else [v]}
            elif target.startswith("feature_params."):
                parts = target.split(".")
                if len(parts) != 3 or parts[1] not in base_set:
                    continue
                c["feature_params"].setdefault(parts[1], {})[parts[2]] = v
            else:
                continue
            c["hypothesis"] = f"{c['hypothesis']} [sweep {target}={v}]"
            out.append(ExperimentSpec(kind="config", feature_set=list(base_set), **c))
        return out
