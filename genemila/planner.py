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


class Planner:
    def __init__(self, lab: Lab, provider: AgentProvider, fallback: AgentProvider | None = None):
        self.lab = lab
        self.provider = provider
        self.fallback = fallback
        self.cfg = lab.cfg
        self.rounds = 0
        self.last_call = 0.0
        self.last_queued = -1
        self.empty_rounds = 0  # consecutive rounds that queued nothing

    def mix(self) -> dict:
        s = self.cfg["schedule"]
        total = s["explore"] + s["exploit"] + s["risky"]
        return {k: s[k] / total for k in ("explore", "exploit", "risky")}

    # ------------------------------------------------------------------ round
    def refill(self, n: int) -> list[str]:
        """Ask for ~n hypotheses and queue the resulting experiments. Returns queued ids."""
        state = build_state(self.lab)
        text = render_state(state)
        self.rounds += 1
        self.last_call = time.time()
        (self.lab.run_dir / "planner").mkdir(exist_ok=True)
        (self.lab.run_dir / "planner" / f"state_{self.rounds:03d}.txt").write_text(text)
        provider = self.provider
        try:
            resp = self.lab.gateway.call(provider, "propose", role="planner",
                                         max_tokens=int(self.cfg["planner"]["max_output_tokens"]),
                                         est_input_tokens=len(text) // 3 + 1500,
                                         research_state=text, n=n, mix=self.mix())
            plan = parse_json(resp.text)
        except (ProviderError, BudgetExceeded, ValueError, json.JSONDecodeError) as exc:
            self.lab.db.event("planner_error", f"{provider.name}: {exc}"[:500], level="warning")
            if self.fallback is None:
                return []
            provider = self.fallback
            resp = provider.propose(research_state=text, n=n, mix=self.mix(), max_tokens=0)
            plan = parse_json(resp.text)
        (self.lab.run_dir / "planner" / f"plan_{self.rounds:03d}.json").write_text(json.dumps(plan, indent=1))
        specs = self.to_specs(plan.get("hypotheses", []), proposer=f"{provider.name}:{provider.model}")
        queued = []
        for spec in specs:
            eid, status = self.lab.queue(spec)
            if status == "queued":
                queued.append(eid)
        self.lab.db.execute(
            "INSERT INTO planner_rounds (ts, provider, model, state_chars, n_proposed, n_queued, synthesis, raw_path) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (time.time(), provider.name, provider.model, len(text), len(specs), len(queued),
             str(plan.get("synthesis", ""))[:2000], f"planner/plan_{self.rounds:03d}.json"))
        self.last_queued = len(queued)
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

    def to_specs(self, hypotheses: list[dict], proposer: str) -> list[ExperimentSpec]:
        ecfg = self.cfg["experiment"]
        best = self.lab.best()
        prio = self._priorities()
        known = self.lab.known_features()
        specs = []
        for h in hypotheses:
            if not isinstance(h, dict):
                continue
            parent = self.lab.db.get_experiment(h["parent"]) if h.get("parent") else None
            if parent is None or parent.get("status") != "completed":
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
                reps = max(1, min(int(h.get("replicates", 1) or 1), int(self.cfg["schedule"]["replicates_max"])))
                group = f"G_{self.rounds:03d}_{len(specs):03d}"
                for _ in range(reps):
                    name = str(nf.get("name", "feature"))
                    specs.append(ExperimentSpec(
                        kind="new_feature", feature_set=base_set + [name], hypothesis_group=group,
                        proposed_feature={"name": name, "description": str(nf.get("description", "")),
                                          "implementation_hint": str(nf.get("implementation_hint", "")),
                                          "params": nf.get("params", {})}, **common))
            elif action in ("combine", "ablate"):
                add = [f for f in h.get("add_features", []) if f in known and f not in base_set]
                remove = set(h.get("remove_features", []))
                fs = [f for f in base_set if f not in remove] + add
                specs.append(ExperimentSpec(kind="config", feature_set=fs, **common))
            elif action == "sweep" and isinstance(h.get("sweep"), dict):
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
