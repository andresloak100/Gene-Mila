"""Experiment specifications and the scientific guardrails applied to them."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any

PLUGIN_DIR = "genemila/features/plugins"
ALLOWED_MODELS = ("ridge", "lasso", "elasticnet", "ols")
KINDS = ("baseline", "new_feature", "config")
CATEGORIES = ("baseline", "explore", "exploit", "risky")

# Paths agents may never modify. Enforced on the worktree diff, not via prompts.
PROTECTED_PATHS = (
    "genemila/benchmark/", "genemila/data/", "genemila/pipeline.py", "genemila/features/api.py",
    "genemila/features/registry.py", "genemila/features/builtin.py", "configs/", "tests/",
    "genemila/controller.py", "genemila/worker.py", "genemila/guard.py", "genemila/spec.py",
)

_CHEAT_PATTERNS = [
    r"\bval(idation)?[ _-]?2\b", r"query[- ]only", r"hidden (validation )?labels?", r"test labels?",
    r"(modify|change|edit|alter|replace)\s+(the\s+)?(evaluator|metric|benchmark|split)",
    r"(re-?split|resplit|new split)", r"private/", r"val1\.npz", r"val2\.npz",
]


@dataclass
class ExperimentSpec:
    hypothesis: str
    scientific_rationale: str
    kind: str = "config"
    category: str = "explore"
    experiment_id: str | None = None
    parent_experiment_id: str | None = None
    proposed_feature: dict | None = None      # {name, description, implementation_hint, params}
    feature_set: list[str] = field(default_factory=list)
    feature_params: dict = field(default_factory=dict)
    allowed_files: list[str] = field(default_factory=list)
    model_type: str = "ridge"
    hyperparameters: dict = field(default_factory=dict)
    seed: int = 0
    cpu_limit_s: float = 600
    ram_limit_mb: float = 4096
    timeout_s: float = 300
    hypothesis_group: str | None = None
    proposer: str = "unknown"
    priority: float = 0.0
    status: str = "queued"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ExperimentSpec":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})

    @classmethod
    def from_record(cls, rec: dict) -> "ExperimentSpec":
        return cls(
            hypothesis=rec["hypothesis"], scientific_rationale=rec["rationale"], kind=rec["kind"],
            category=rec["category"], experiment_id=rec["experiment_id"], parent_experiment_id=rec["parent_id"],
            proposed_feature=rec.get("proposed_feature_json"), feature_set=rec.get("feature_set_json") or [],
            feature_params=rec.get("feature_params_json") or {}, allowed_files=rec.get("allowed_files_json") or [],
            model_type=rec["model_type"], hyperparameters=rec.get("hyperparameters_json") or {},
            seed=rec.get("seed") or 0, cpu_limit_s=rec.get("cpu_limit_s") or 600,
            ram_limit_mb=rec.get("ram_limit_mb") or 4096, timeout_s=rec.get("timeout_s") or 300,
            hypothesis_group=rec.get("hypothesis_group"), proposer=rec.get("proposer") or "unknown",
            priority=rec.get("priority") or 0.0, status=rec["status"])

    def to_record(self, dataset: str, split_id: str, run_id: str) -> dict:
        return {
            "experiment_id": self.experiment_id, "run_id": run_id, "parent_id": self.parent_experiment_id,
            "status": self.status, "priority": self.priority, "kind": self.kind, "category": self.category,
            "hypothesis": self.hypothesis, "rationale": self.scientific_rationale,
            "hypothesis_group": self.hypothesis_group or hypothesis_key(self.hypothesis),
            "proposed_feature_json": self.proposed_feature, "feature_set_json": self.feature_set,
            "feature_params_json": self.feature_params, "allowed_files_json": self.allowed_files,
            "new_feature": (self.proposed_feature or {}).get("name") if self.kind == "new_feature" else None,
            "model_type": self.model_type, "hyperparameters_json": self.hyperparameters, "seed": self.seed,
            "cpu_limit_s": self.cpu_limit_s, "ram_limit_mb": self.ram_limit_mb, "timeout_s": self.timeout_s,
            "dataset": dataset, "split_id": split_id, "proposer": self.proposer,
        }

    def run_spec(self) -> dict:
        """The subset of the spec the experiment subprocess needs."""
        return {"experiment_id": self.experiment_id, "feature_set": self.feature_set,
                "feature_params": self.feature_params, "model_type": self.model_type,
                "hyperparameters": self.hyperparameters, "seed": self.seed}


def hypothesis_key(text: str) -> str:
    norm = re.sub(r"[^a-z0-9 ]", "", text.lower())
    norm = " ".join(sorted(set(norm.split())))
    return "H_" + hashlib.sha256(norm.encode()).hexdigest()[:10]


def config_hash(spec: ExperimentSpec, feature_code_hashes: dict[str, str], split_id: str) -> str:
    payload = {
        "features": sorted((n, feature_code_hashes.get(n, "builtin")) for n in spec.feature_set),
        "feature_params": spec.feature_params, "model_type": spec.model_type,
        "hyperparameters": spec.hyperparameters, "seed": spec.seed, "split_id": split_id,
    }
    return "C_" + hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


class GuardrailViolation(ValueError):
    pass


def validate_spec(spec: ExperimentSpec, known_features: set[str], limits: dict, parent: dict | None = None,
                  ) -> list[str]:
    """Raise GuardrailViolation for hard violations; return soft flags."""
    flags: list[str] = []
    if len((spec.hypothesis or "").strip()) < 15:
        raise GuardrailViolation("experiment cannot state its scientific hypothesis")
    if len((spec.scientific_rationale or "").strip()) < 15:
        raise GuardrailViolation("experiment lacks a scientific rationale")
    if spec.kind not in KINDS:
        raise GuardrailViolation(f"unknown experiment kind {spec.kind!r}")
    if spec.category not in CATEGORIES:
        raise GuardrailViolation(f"unknown category {spec.category!r}")
    if spec.model_type not in ALLOWED_MODELS:
        raise GuardrailViolation(f"model {spec.model_type!r} not allowed; use one of {ALLOWED_MODELS}")
    text = " ".join([spec.hypothesis, spec.scientific_rationale, json.dumps(spec.proposed_feature or {})]).lower()
    for pat in _CHEAT_PATTERNS:
        if re.search(pat, text):
            raise GuardrailViolation(f"spec references protected benchmark components (matched {pat!r})")
    for f in spec.allowed_files:
        if not f.startswith(PLUGIN_DIR + "/") or ".." in f or not f.endswith(".py"):
            raise GuardrailViolation(f"file {f!r} is outside the feature plugin directory")
    if spec.cpu_limit_s > limits["cpu_limit_s"] or spec.ram_limit_mb > limits["ram_limit_mb"] \
            or spec.timeout_s > limits["timeout_s"]:
        raise GuardrailViolation("experiment requests more compute than allowed")
    for k, v in spec.hyperparameters.items():
        if k not in ("alpha", "alpha_grid"):
            raise GuardrailViolation(f"unknown hyperparameter {k!r}")
    grid = spec.hyperparameters.get("alpha_grid", [])
    if len(grid) > 12:
        raise GuardrailViolation("alpha grid larger than 12 values")

    new = (spec.proposed_feature or {}).get("name") if spec.kind == "new_feature" else None
    if spec.kind == "new_feature":
        if not new or not re.fullmatch(r"[a-z][a-z0-9_]{2,60}", new):
            raise GuardrailViolation("new_feature experiments must name the feature (snake_case)")
        if spec.allowed_files != [f"{PLUGIN_DIR}/{new}.py"]:
            raise GuardrailViolation("a new_feature experiment may change exactly one plugin file")
        if new in known_features:
            raise GuardrailViolation(f"feature {new!r} already exists")
        if new not in spec.feature_set:
            raise GuardrailViolation("the new feature must be part of the experiment's feature set")
    elif spec.allowed_files:
        raise GuardrailViolation("config experiments may not change code")
    unknown = [f for f in spec.feature_set if f not in known_features and f != new]
    if unknown:
        raise GuardrailViolation(f"unknown features {unknown}")
    if len(set(spec.feature_set)) != len(spec.feature_set) or not spec.feature_set:
        raise GuardrailViolation("feature set must be non-empty and without duplicates")

    if parent is not None:
        p_set = set(parent.get("feature_set_json") or [])
        added, removed = set(spec.feature_set) - p_set, p_set - set(spec.feature_set)
        changes = len(added) + len(removed)
        changes += int(spec.model_type != parent.get("model_type"))
        changes += int(spec.feature_params != (parent.get("feature_params_json") or {}))
        if changes == 0 and spec.hyperparameters == (parent.get("hyperparameters_json") or {}):
            flags.append("no_change_vs_parent")
        if changes > 3:
            raise GuardrailViolation(f"{changes} simultaneous changes vs parent; test one idea at a time")
        if changes > 1:
            flags.append(f"multiple_changes:{changes}")
    return flags
