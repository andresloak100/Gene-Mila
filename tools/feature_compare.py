#!/usr/bin/env python3
"""Feature-level comparison of research systems: what does each system's feature set, and each of its single
features, add to one fixed linear model? (Claim issue #41; docs/PAPER_FRAMEWORK_PROPOSAL.md.)

Every system under comparison (the lab, an autoresearch-style coding agent, Biomni, a person translating CellForge or
STATE ideas) hands in feature plugins written against genemila/features/api.py. This tool scores them all the same
way, so that "feature + linear model = result" is one table: a parent model (the lab's start, or a run's selected
model) is refitted with ridge, alone, with each candidate feature added (add-one rows) and with all of a source's
features added (one set row per source), on out-of-fold predictions of the training perturbations under fold seeds
no run used, and optionally on the visible validation perturbations (--with-val1).

Why each step is the way it is:
- Foreign code never runs in this process. Every file is checked statically first (the lab's plugin guard, and the
  literal caps of tools/task_package/literal.py so a file cannot paste a table of training labels); a file that fails
  never reaches a directory any plugin loader reads. Each passing candidate is smoke-tested in a limited subprocess
  (the hidden "_smoke" command) with the params it will be scored with, and all feature blocks are computed in
  limited child processes of this script (the hidden "_blocks" command), every feature recomputed in every fold
  view, nothing sliced, as the lab's cross_validate does for features that read labels. Both load plugin files one
  at a time, so a file that raises on import costs only its own row. This process only fits and scores arrays.
- The ridge penalty is chosen honestly, on out-of-fold scores only: chosen on one fold seed, reported on another,
  over every ordered pair of seeds. The lab itself also chooses on the visible validation set; a tool that did so
  would leave no held-out tier for package arms.
- A gain is compared with a matched null: the candidate's columns permuted across genes within bins of control
  expression (one permutation for every perturbation, fold, seed and the validation block), refitted with the full
  procedure. Moving values between genes within one perturbation's row never moves another perturbation's label
  into it, so the null is label-safe for label-dependent features too.
- The paired standard error is widened by the target-gene overlap of the perturbations (tools/sealed_reading.py),
  which matters on a bundle with pairs.
- A --source file is scored with its own class params only: a params file next to it would be a channel for training
  labels that neither the guard nor the literal caps see. A --source-run feature uses the params the run recorded.
- OOF scores are not held out for any system that selected features on these labels, which every system has; the
  report says so whenever OOF is the deciding tier. The visible validation set is not held out for lab runs either
  (the lab selects on it): their rows carry exposure "val1+oof" and, when val1 decides, an "optimistic" verdict.
- A candidate that is, within every perturbation's row, a per-perturbation scalar times one parent column (such
  as additive_response times a property of the perturbation's targets) gets a second null, because the gene null
  cannot fail it: permuting that candidate across genes scrambles the parent factor the model already holds, so
  every replicate is worthless and the null is a spike at zero (block F's stage 2,
  docs/results/norman_f_stage2/feature_compare.json: null sd 1e-5 against an observed gain of 0.00056). The
  perturbation null keeps every parent column in place and permutes the per-perturbation scalars across the
  training perturbations within deciles of the targets' mean control expression (perturbations without a measured
  target in their own bin). Such a row carries proportional=true, parent_column, and null_pert beside null; it must
  pass both nulls. A non-proportional candidate passes the gene null only and records proportional=false.
- Family-wise correction is a max-gain step-down permutation test (Westfall and Young) over one source's add-one
  rows (one family per system, so a system's verdicts do not depend on how many candidates the others sent): the
  permutation of replicate b is a function of (null seed, b) alone, shared by every row of the call, so the joint
  null keeps the dependence between candidates; each row stores its B null gains (null.gains, null_pert.gains) and
  p_fwer is the step-down p, with the Holm p of the raw null p kept as p_holm for comparison. The verdict uses
  p_fwer. The floor is 1/(B+1); the default B is 999 (floor 0.001), and a family of more than one row with fewer
  than 999 replicates is reported as "null too coarse", not blamed on the feature.
- Before the correction, add-one rows of one source with an identical prediction hash (the OOF predictions over
  all reports rounded to 1e-9, and the candidate's feature matrix) collapse to one: the first in order is kept and
  lists the others under "duplicates"; the others get status "duplicate" and are not family members, so three
  copies of one column count once.
- The standardised add-one coefficient of the candidate column (columns standardised by the training mean and sd,
  as the lab's pipeline does) is saved per report (fold-seed pair) as coef_candidate_std with its mean and sign, so
  a sign can be read on the common parent.
- The verdict ("meaningful (development, ...)") needs, on the deciding tier: the mean M1 gain above twice its
  overlap-adjusted SE and above the minimum effect of interest MIN_GAIN (0.002, docs/ROADMAP.md D3) with wins on
  more than half the perturbations; p_fwer of the gene null at most 0.05, and of the perturbation null too when the
  row is proportional; the family not too coarse; a mean M2 gain; mse_top not significantly worse; every OOF
  report gaining; and more than one fold seed.

Labels read: training labels through FeatureContext of a public copy (public.npz, knowledge/, manifest.json), and,
only with --with-val1, the visible validation labels (val1.npz) in one function, load_val1. Nothing else.

    python tools/feature_compare.py --data data/adamson --out out/fc --source astra=pkg_astra/features
    python tools/feature_compare.py --data data/norman --out out/fc --parent-run <parent_run_dir> \
        --source-run lab=<source_run_dir> --with-val1
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "tools"))

import feature_audit as fa  # noqa: E402  (read_run, plugin loading, standardise, ridge_weight_grid, pearson_rows)
from genemila import pipeline, sandbox  # noqa: E402
from genemila.benchmark.evaluator import evaluate, metric_values, paired_summary  # noqa: E402
from genemila.data.bundle import LabelSet, added_knowledge  # noqa: E402  (LabelSet: load_val1 only)
from genemila.features import registry  # noqa: E402
from genemila.features.api import FeatureContext  # noqa: E402
from genemila.features.registry import ALL_BUILTIN_FEATURES, BUILTIN_FEATURES  # noqa: E402
from genemila.guard import CodeViolation, check_plugin_source  # noqa: E402
from genemila.pipeline import cv_fold_targets, cv_folds_of, feature_blocks  # noqa: E402
from task_package.literal import literal_check  # noqa: E402

PER_PERT = ["pearson_delta", "pearson_delta_nontarget", "mse_top", "r2_top", "pearson_delta_top", "direction_acc_top"]
LOWER_IS_BETTER = {"mse_top"}  # its paired difference is parent minus candidate, so verdict "a" is always a gain
LABEL = {"pearson_delta": "M1", "pearson_delta_nontarget": "M2", "mse": "M3", "mse_top": "M4", "r2_top": "M5",
         "pearson_delta_top": "M6", "direction_acc_top": "M7", "delta_scale_ratio": "M12"}
P_MAX = 0.05
MIN_GAIN = 0.002  # the minimum M1 gain of practical interest (docs/ROADMAP.md D3, the task package's noise rule)
MIN_REPS_FAMILY = 999  # replicates a family of more than one row needs before the step-down p is read (floor 0.001)
OOF_CAVEAT = "OOF only: every system has selected on these labels; not held out"
TOP_CAVEAT = ("M4-M7 use each perturbation's top 20 genes by |true delta| (genemila.benchmark.evaluator), not "
              "CellForge's Wilcoxon DE top 20")


class Unusable(Exception):
    """Inputs the tool cannot score (exit 2); a rejected candidate is a row instead."""


def alpha_grid() -> list[float]:
    """The lab's default grid and feature_audit's fixed one, so a strong feature is not capped by a small grid."""
    cfg = tomllib.loads((REPO_ROOT / "configs" / "default.toml").read_text())
    return sorted({float(a) for a in cfg["experiment"]["default_alpha_grid"]} | set(fa.FIXED_ALPHAS))


# ================================================================== blocks, computed in limited child processes
def compute_blocks(public: Path, plugin_dir: Path | None, features: list[str], params: dict, seeds: list[int],
                   k: int, groups: str | None, with_eval: bool) -> dict:
    """Every feature's blocks: full training (rows ctx.train_perts), with_eval the full-context batch of every
    non-training perturbation (as pipeline.run predicts it), and per fold seed and fold a fresh view without the
    fold's hidden perturbations (rows view.train_perts + predict), plugins re-executed before each fold. Runs only in
    the "_blocks" child (and in tests on built-ins); a feature that fails is recorded and the others go on."""
    np.random.seed(0)  # as pipeline.run seeds before it loads plugins
    load_errors = fa.load_run_plugins(plugin_dir) if plugin_dir else {}
    errors = fa.missing_feature_errors(features, plugin_dir, load_errors) if plugin_dir else {}
    ctx = FeatureContext(public)

    def blocks(view, perts):
        got = {}
        for f in features:
            if f in errors:
                continue
            try:
                got[f] = feature_blocks(view, [f], params, perts, {})[f]
            except Exception as exc:  # noqa: BLE001  (a plugin's failure is its own row's status)
                errors[f] = fa._err(exc)
        return got

    eval_perts = [p for p in ctx.perts if p not in set(ctx.train_perts)]
    out = {"full": blocks(ctx, ctx.train_perts), "eval_perts": eval_perts if with_eval else [], "folds": {}}
    out["eval"] = blocks(ctx, eval_perts) if with_eval else {}
    for s in seeds:
        out["folds"][s] = []
        for predict, hide in cv_folds_of(ctx.train_perts, k, s, cv_fold_targets(ctx, groups)):
            for f, why in fa.reload_run_plugins().items():
                errors.setdefault(f, why)
            view = ctx.without_train(hide)
            rows = view.train_perts + predict
            out["folds"][s].append({"predict": predict, "rows": rows, "blocks": blocks(view, rows)})
    for part in [out["full"], out["eval"]] + [fd["blocks"] for fs in out["folds"].values() for fd in fs]:
        for f in errors:
            part.pop(f, None)
    out["errors"] = errors
    return out


def save_blocks(res: dict, path: Path) -> None:
    arrays = {f"full|{f}": a for f, a in res["full"].items()} | {f"eval|{f}": a for f, a in res["eval"].items()}
    index = {"errors": res["errors"], "eval_perts": res["eval_perts"], "folds": {}}
    for s, folds in res["folds"].items():
        index["folds"][str(s)] = [{"predict": fd["predict"], "rows": fd["rows"]} for fd in folds]
        for i, fd in enumerate(folds):
            arrays.update({f"fold|{s}|{i}|{f}": a for f, a in fd["blocks"].items()})
    np.savez(path.with_suffix(".npz"), **arrays)
    path.with_suffix(".json").write_text(json.dumps(index))


def load_blocks(path: Path) -> dict:
    index = json.loads(path.with_suffix(".json").read_text())
    res = {"errors": index["errors"], "eval_perts": index["eval_perts"], "full": {}, "eval": {},
           "folds": {int(s): [{**fd, "blocks": {}} for fd in folds] for s, folds in index["folds"].items()}}
    with np.load(path.with_suffix(".npz"), allow_pickle=False) as z:
        for key in z.files:
            part = key.split("|")
            if part[0] == "fold":
                res["folds"][int(part[1])][int(part[2])]["blocks"][part[3]] = z[key]
            else:
                res[part[0]][part[1]] = z[key]
    return res


def child_main(job_path: str) -> int:
    job = json.loads(Path(job_path).read_text())
    res = compute_blocks(Path(job["public"]), Path(job["plugins"]), job["features"], job["params"], job["seeds"],
                         job["k"], job["groups"], job["with_eval"])
    save_blocks(res, Path(job["out"]))
    return 0


def run_child(d: Path, public: Path, plugins: Path, features: list[str], params: dict, a) -> dict:
    """compute_blocks in a limited child process (sandbox.run_limited, PYTHONHASHSEED=0), working in its own new
    directory d. Returns the blocks, or {"failed": reason} when the child itself died (time-out, memory, crash)."""
    d.mkdir(parents=True)
    job = {"public": str(public), "plugins": str(plugins), "features": features, "params": params, "seeds": a.seeds,
           "k": a.k, "groups": a.groups, "with_eval": a.with_val1, "out": str(d / "blocks")}
    (d / "job.json").write_text(json.dumps(job))
    r = sandbox.run_limited([sys.executable, str(Path(__file__).resolve()), "_blocks", str(d / "job.json")],
                            cwd=REPO_ROOT, log_dir=d, timeout_s=a.timeout_s, ram_mb=a.ram_mb, cpu_s=a.timeout_s,
                            env={"PYTHONHASHSEED": "0"}, name="child")
    if r.returncode != 0 or not (d / "blocks.json").exists():
        why = r.killed_reason or ("timed out" if r.timed_out else f"exit {r.returncode}")
        return {"failed": f"block computation failed ({why}): {r.stderr_tail[-300:].strip()}"}
    return load_blocks(d / "blocks")


def smoke_main(job_path: str) -> int:
    """pipeline.smoke on one candidate, with two changes. The plugin directory is loaded one file at a time
    (feature_audit.load_run_plugins), so another file of the source that raises on import costs only its own row,
    not every candidate's; and the candidate runs with the params it will be scored with, so the shape, determinism
    and own-label leakage checks see those params. Exit codes and output files are pipeline main's."""
    job = json.loads(Path(job_path).read_text())
    out, f = Path(job["out"]), job["feature"]
    try:
        errors = fa.load_run_plugins(Path(job["plugins"]))
        if f in errors:
            raise ImportError(f"{f}.py failed to import: {errors[f]}")
        get = registry.get

        def with_params(name):
            cls = get(name)
            if name == f:
                cls.params = {**cls.params, **job["params"]}
            return cls

        registry.load_plugins, registry.get = (lambda _dir: []), with_params  # loaded above, file by file
        return 0 if pipeline.smoke(f, Path(job["public"]), Path(job["plugins"]), out)["status"] == "ok" else 3
    except Exception as exc:  # noqa: BLE001  (reported as the row's reason)
        out.mkdir(parents=True, exist_ok=True)
        (out / "error.json").write_text(json.dumps({"error_type": type(exc).__name__, "error": str(exc)[:2000]}))
        return 2


def smoke(name: str, params: dict, public: Path, plugins: Path, o: Path, a) -> tuple[str, str] | None:
    """smoke_main (shape, finiteness, determinism, own-label leakage, pair order) in a limited subprocess: None
    when it passed, else (status, reason): "smoke" for the smoke test's problems, "error" when importing or computing
    the feature raised (a dependency that was rejected, say) or the process died."""
    o.mkdir(parents=True)
    (o / "job.json").write_text(json.dumps({"feature": name, "params": params, "public": str(public),
                                            "plugins": str(plugins), "out": str(o)}))
    r = sandbox.run_limited([sys.executable, str(Path(__file__).resolve()), "_smoke", str(o / "job.json")],
                            cwd=REPO_ROOT, log_dir=o, timeout_s=a.timeout_s, ram_mb=a.ram_mb, cpu_s=a.timeout_s,
                            env={"PYTHONHASHSEED": "0"}, name="smoke")
    if r.returncode == 0:
        return None
    if (o / "smoke.json").exists():
        return "smoke", "; ".join(json.loads((o / "smoke.json").read_text()).get("problems") or ["smoke failed"])
    if (o / "error.json").exists():
        e = json.loads((o / "error.json").read_text())
        return "error", f"{e.get('error_type')}: {e.get('error')}"
    return "error", r.killed_reason or ("timed out" if r.timed_out else r.stderr_tail[-300:].strip() or "died")


# ================================================================== static checks (before any execution)
def static_check(path: Path, data, *, imported: bool, enforce_literal: bool, taken=()) -> dict:
    """The guard (with the registry's convention: file <name>.py registers feature <name>), the literal caps, and a
    name collision with the parent or a built-in. A file whose status is not ok is never copied anywhere a plugin
    loader reads."""
    out = {"file": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "status": "ok", "reason": ""}
    try:
        src = path.read_text()
        check_plugin_source(src, path.stem, imported=imported)
    except (CodeViolation, UnicodeDecodeError) as exc:
        return {**out, "status": "guard", "reason": str(exc)[:500]}
    lit = literal_check(src, data.pair_ids, data.names)
    out["literal"] = {"ok": lit["ok"], "problems": lit["problems"], **lit["stats"]}
    if enforce_literal and not lit["ok"]:
        return {**out, "status": "literal", "reason": "; ".join(lit["problems"])}
    if path.stem in taken:
        return {**out, "status": "collision", "reason": f"{path.stem} is a parent or built-in feature"}
    return out


def copy_files(paths, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for p in paths:
        shutil.copyfile(p, dest / p.name)


# ================================================================== inputs
@dataclass
class Data:
    """The public data the parent process scores with, and the visible validation labels when requested."""
    ctx: FeatureContext
    train: list[str]
    pos: dict
    Y: np.ndarray          # (n_train, n_genes) training deltas
    cm: np.ndarray
    tidx: dict             # perturbation -> its target columns (pearson_delta_nontarget)
    genes_of: dict         # perturbation -> set of target genes (overlap SE)
    pair_ids: list[str]
    names: list[str]
    val1: LabelSet | None = None
    val1_rows: list[int] | None = None
    folds: dict | None = None

    @property
    def n_genes(self) -> int:
        return self.ctx.n_genes


def public_copy(data_dir: Path, dest: Path) -> dict:
    """Copy only public.npz, knowledge/ and the manifest (without file hashes) into dest; return the manifest."""
    if not (data_dir / "public.npz").exists() or not (data_dir / "knowledge" / "targets.json").exists():
        raise Unusable(f"{data_dir} has no public.npz and knowledge/targets.json")
    copy_files([data_dir / "public.npz"], dest)
    copy_files(sorted(f for f in (data_dir / "knowledge").glob("*") if f.is_file()), dest / "knowledge")
    manifest = {}
    if (data_dir / "manifest.json").exists():
        manifest = {k: v for k, v in json.loads((data_dir / "manifest.json").read_text()).items()
                    if k != "file_sha256"}
        (dest / "manifest.json").write_text(json.dumps(manifest, indent=1))
    return manifest


def load_val1(data_dir: Path, ctx: FeatureContext) -> LabelSet:
    """The one read of held-out labels: the visible validation set, refused when missing, overlapping training or
    not matching the public data."""
    path = data_dir / "private" / "val1.npz"
    if not path.exists():
        raise Unusable(f"--with-val1: {path} is missing")
    val1 = LabelSet.load(path)
    train, known = set(ctx.train_perts), set(ctx.perts)
    if any(p in train for p in val1.perts) or any(p not in known for p in val1.perts):
        raise Unusable("the visible validation perturbations overlap training or are not in the public data")
    if val1.means.shape != (len(val1.perts), ctx.n_genes):
        raise Unusable("the visible validation labels do not match the public gene list")
    return val1


def make_data(public: Path) -> Data:
    ctx = FeatureContext(public)
    _, Y = ctx.train_delta()
    targets = {p: ctx.target_genes(p) for p in ctx.perts}
    return Data(ctx=ctx, train=list(ctx.train_perts), pos={p: i for i, p in enumerate(ctx.train_perts)},
                Y=np.array(Y, dtype=np.float64), cm=ctx.control_mean,
                tidx={p: ctx.target_indices(p) for p in ctx.perts},
                genes_of={p: set(t) or {p} for p, t in targets.items()},
                pair_ids=sorted(p for p, t in targets.items() if len(set(t)) > 1),
                names=list(ctx.genes) + list(ctx.perts))


def read_selected(run_dir: Path) -> dict:
    """A finished run's selected single model, read only (feature_audit.read_run), with its fold grouping when the
    run recorded one."""
    if not (run_dir / "feature_store").is_dir():
        raise Unusable(f"{run_dir} has no feature_store")
    with tempfile.TemporaryDirectory(prefix="feature_compare_db_") as scratch:
        try:
            meta = fa.read_run(run_dir, Path(scratch))
        except fa.Skip as exc:
            raise Unusable(f"{run_dir}: {exc}") from exc
    sel = meta["selected"]
    if sel is None:
        raise Unusable(f"{run_dir}: no completed single experiment with a score")
    hp = sel.get("hyperparameters_json") or {}
    return {"run": str(run_dir), "run_id": meta["run_id"], "split_id": meta["split_id"],
            "experiment_id": sel["experiment_id"], "features": list(sel["feature_set_json"]),
            "params": sel.get("feature_params_json") or {},
            "cv_groups": ("cv_folds" in hp, hp.get("cv_groups"))}


def resolve_groups(flag: str, data: Data, manifest: dict, recorded: tuple | None) -> str | None:
    """auto: "gene" on a bundle with a multi-target perturbation or a gene split, as the lab groups its folds; a
    parent run's recorded grouping wins, and an explicit flag that contradicts it is refused."""
    want = {"none": None, "gene": "gene"}.get(flag)
    if recorded and recorded[0]:
        if flag != "auto" and want != recorded[1]:
            raise Unusable(f"--groups {flag} contradicts the parent run's cv_groups {recorded[1]!r}")
        return recorded[1]
    if flag != "auto":
        return want
    gene_split = manifest.get("split_mode") == "gene" or manifest.get("mode") == "gene"
    return "gene" if data.pair_ids or gene_split else None


# ================================================================== fitting and scoring (arrays only)
def ridge_fit(Xtr: np.ndarray, ytr: np.ndarray, Xout: np.ndarray, alphas) -> tuple[np.ndarray, np.ndarray]:
    """Ridge with intercept on columns standardised by the training rows (sd 0 becomes 1): sklearn Ridge on
    pipeline's standardised design, in closed form for every alpha. Returns ((n_alpha, n_out_rows) predictions,
    (n_columns, n_alpha) standardised weights)."""
    Xs, (Xo,), _, _ = fa.standardise(np.asarray(Xtr, dtype=np.float64), np.asarray(Xout, dtype=np.float64))
    ybar = float(ytr.mean())
    W = fa.ridge_weight_grid(Xs.T @ Xs, Xs.T @ (ytr - ybar), np.arange(Xs.shape[1]), alphas)
    return (Xo @ W).T + ybar, W


def ridge_predict(Xtr: np.ndarray, ytr: np.ndarray, Xout: np.ndarray, alphas) -> np.ndarray:
    """(n_alpha, n_out_rows) predictions of ridge_fit."""
    return ridge_fit(Xtr, ytr, Xout, alphas)[0]


def design(parts, where) -> np.ndarray:
    """(n_rows, n_genes, C) design of parts [(blocks, features, gene permutation or None)] at where: ("fold", s, i),
    ("full",) or ("eval",)."""
    cols = []
    for res, feats, perm in parts:
        src = res["folds"][where[1]][where[2]]["blocks"] if where[0] == "fold" else res[where[0]]
        for f in feats:
            cols.append(src[f] if perm is None else src[f][:, perm, :])
    return np.concatenate(cols, axis=2)


def oof_predictions(parts, data: Data, seeds, alphas, with_weights: bool = False):
    """Per fold seed the (n_alpha, n_train, n_genes) out-of-fold predictions; with_weights also returns, per seed,
    the list over folds of each fold's (n_columns, n_alpha) standardised ridge weights."""
    out, weights = {}, {}
    for s in seeds:
        O, weights[s] = np.zeros((len(alphas), len(data.train), data.n_genes)), []
        for i, fold in enumerate(data.folds[s]):
            X = design(parts, ("fold", s, i))
            n_tr, C = len(fold["rows"]) - len(fold["predict"]), X.shape[2]
            y = data.Y[[data.pos[p] for p in fold["rows"][:n_tr]]].reshape(-1)
            pred, W = ridge_fit(X[:n_tr].reshape(-1, C), y, X[n_tr:].reshape(-1, C), alphas)
            O[:, [data.pos[p] for p in fold["predict"]]] = pred.reshape(len(alphas), -1, data.n_genes)
            weights[s].append(W)
        out[s] = O
    return (out, weights) if with_weights else out


def score(parts, data: Data, seeds, alphas, keep: bool = True) -> dict:
    """Per tier: the reports (alpha chosen on one seed's OOF mean pearson_delta, the other seed's OOF reported; one
    seed: itself, not honest), each report's per-perturbation pearson_delta and, with keep, its predicted deltas
    and "coef", the (n_reports, n_columns) standardised ridge weights of the report seed's folds at the report's
    alpha, averaged over the folds. The val1 tier fits all training rows at the alpha best on the mean OOF score
    over all seeds."""
    O, Wf = oof_predictions(parts, data, seeds, alphas, with_weights=True)
    P = {s: fa.pearson_rows(O[s], data.Y) for s in seeds}
    reports, m1, pick, pairs = _honest_reports(P, seeds, alphas)
    out = {"oof": {"reports": reports, "m1": m1}}
    if keep:
        out["oof"]["preds"] = [O[b][pick[a]] for a, b in pairs]
        out["oof"]["coef"] = np.array([np.mean([W[:, pick[a]] for W in Wf[b]], axis=0) for a, b in pairs])
    if data.val1 is not None:
        k = int(np.argmax(np.mean([P[s].mean(axis=1) for s in seeds], axis=0)))
        Xtr, Xev = design(parts, ("full",)), design(parts, ("eval",))[data.val1_rows]
        C = Xtr.shape[2]
        V = ridge_predict(Xtr.reshape(-1, C), data.Y.reshape(-1), Xev.reshape(-1, C), [alphas[k]])[0]
        V = V.reshape(len(data.val1_rows), data.n_genes)
        out["val1"] = {"reports": [{"alpha": alphas[k]}], "m1": [fa.pearson_rows(V, data.val1.means - data.cm)]}
        if keep:
            out["val1"]["preds"] = [V]
    return out


def tier_perts(data: Data, tier: str):
    """(perturbations, true expression) of a tier."""
    return (data.train, data.Y + data.cm) if tier == "oof" else (data.val1.perts, data.val1.means)


def tier_metrics(sc: dict, data: Data, tier: str) -> dict:
    """The evaluator's per-perturbation metrics averaged over the tier's reports, their means, pooled mse (M3) and
    the delta scale ratio (M12, mean |predicted delta| over mean |true delta|, unrounded)."""
    perts, truth = tier_perts(data, tier)
    per = {p: {} for p in perts}
    mse, ratio = [], []
    for pred in sc[tier]["preds"]:
        r = evaluate(pred + data.cm, truth, data.cm, perts, targets=data.tidx)
        for p in perts:
            for m in PER_PERT:
                per[p][m] = per[p].get(m, 0.0) + r["per_perturbation"][p][m] / len(sc[tier]["preds"])
        mse.append(r["metrics"]["mse"])
        ratio.append(float(np.mean(np.abs(pred)) / max(1e-12, np.mean(np.abs(truth - data.cm)))))
    means = {m: float(np.mean([per[p][m] for p in perts])) for m in PER_PERT}
    return {"n": len(perts), "per_pert": per, "metrics": {**means, "mse": float(np.mean(mse)),
                                                         "delta_scale_ratio": float(np.mean(ratio))}}


def report_deltas(cand: dict, parent: dict, tier: str) -> list[float]:
    return [float(c.mean() - p.mean()) for c, p in zip(cand[tier]["m1"], parent[tier]["m1"])]


def overlap_ratio(diff: np.ndarray, genes_of: list[set]) -> float | None:
    """sqrt(e'Oe / e'e) with e the centred per-perturbation differences and O[p, q] = 1 when p and q share a target
    gene (p = q included): the overlap-robust variance of a mean difference over the plain one, the core of
    tools/sealed_reading.py _cluster_ratio. 1 when no two perturbations share a gene."""
    e = diff - diff.mean()
    plain = float(e @ e)
    if len(diff) < 3 or plain <= 0:
        return None
    O = np.array([[bool(a & b) for b in genes_of] for a in genes_of], dtype=np.float64)
    return float(np.sqrt(max(0.0, float(e @ O @ e)) / plain))


def paired(cand: dict, parent: dict, data: Data, tier: str) -> dict:
    """evaluator.paired_summary per metric (mse_top sign-flipped, so "a" is always the candidate better), with the
    standard error widened by target-gene overlap and the reading rule re-applied with it."""
    perts, _ = tier_perts(data, tier)
    out = {}
    for m in PER_PERT:
        sign = -1.0 if m in LOWER_IS_BETTER else 1.0
        a = {p: sign * v for p, v in metric_values(cand["per_pert"], m).items()}
        b = {p: sign * v for p, v in metric_values(parent["per_pert"], m).items()}
        s = paired_summary(a, b)
        if "se" in s:
            ratio = overlap_ratio(np.array([a[p] - b[p] for p in perts]), [data.genes_of[p] for p in perts])
            se_adj = s["se"] * max(1.0, ratio or 1.0)
            n = s["n"]
            s.update(overlap_ratio=ratio, se_adj=se_adj, verdict_adj=(
                "a" if s["mean_diff"] > 2 * se_adj and s["wins_a"] > n / 2 else
                "b" if -s["mean_diff"] > 2 * se_adj and s["wins_b"] > n / 2 else "none"))
        out[m] = s
    return out


def permutation_within_bins(bins: np.ndarray, seed: int) -> np.ndarray:
    """A permutation of range(len(bins)) that moves an index only within its bin, fixed by the seed alone (so one
    seed gives one permutation whatever candidate it is applied to)."""
    rng = np.random.default_rng(seed)
    perm = np.arange(len(bins))
    for b in np.unique(bins):
        idx = np.flatnonzero(bins == b)
        perm[idx] = rng.permutation(idx)
    return perm


def gene_permutation(control_mean: np.ndarray, n_bins: int, seed: int) -> np.ndarray:
    """A permutation of the genes within bins of control expression (quantile bins of the public control mean):
    feature values move only between genes of similar expression, which keeps the feature's relation to expression
    level and destroys its alignment with each gene's response."""
    edges = np.quantile(control_mean, np.linspace(0, 1, n_bins + 1)[1:-1])
    return permutation_within_bins(np.digitize(control_mean, edges), seed)


def pert_bins(data: Data, n_bins: int) -> np.ndarray:
    """The bin of every training perturbation for the perturbation null: quantile bins (deciles by default) of the
    mean control expression of its measured target genes (for a pair, the mean over both); a perturbation without a
    measured target gets its own bin, n_bins."""
    m = np.array([float(np.mean(data.cm[data.tidx[p]])) if data.tidx[p] else np.nan for p in data.train])
    bins = np.full(len(m), n_bins)
    ok = ~np.isnan(m)
    if ok.any():
        edges = np.quantile(m[ok], np.linspace(0, 1, n_bins + 1)[1:-1])
        bins[ok] = np.digitize(m[ok], edges)
    return bins


def pert_permutation(bins: np.ndarray, seed: int) -> np.ndarray:
    """A permutation of the training perturbations within pert_bins, fixed by the seed alone."""
    return permutation_within_bins(bins, seed)


def parent_column_names(fixed) -> list[str]:
    """The names of the columns of design(fixed, ...), in order: the feature's name, or name[j] for a feature of
    several columns."""
    names = []
    for res, feats, _ in fixed:
        for f in feats:
            k = res["full"][f].shape[2]
            names += [f] if k == 1 else [f"{f}[{j}]" for j in range(k)]
    return names


def proportional_to_parent(cand: np.ndarray, parent_full: np.ndarray, rtol: float = 1e-9):
    """Whether every column j of the candidate's full-training block cand (n, n_genes, k) is, within every
    perturbation row i, a scalar c[i, j] times one parent column q of parent_full (n, n_genes, C): the least-squares
    scalar per row, accepted when the residual norm is at most rtol times the row's norm (c[i, j] = 0 is allowed; a
    row where q is all zero gets c[i, j] = 0, so the candidate must be zero there too). The first parent column
    that fits every row is taken. Returns (parent column index per candidate column, c of shape (n, k)), or None
    when some candidate column fits no parent column."""
    n, _, k = cand.shape
    idx, c = [], np.zeros((n, k))
    for j in range(k):
        x = cand[:, :, j]
        nx = np.linalg.norm(x, axis=1)
        for q in range(parent_full.shape[2]):
            Q = parent_full[:, :, q]
            qq = np.einsum("ig,ig->i", Q, Q)
            cj = np.zeros(n)
            cj[qq > 0] = np.einsum("ig,ig->i", x[qq > 0], Q[qq > 0]) / qq[qq > 0]
            if np.all(np.linalg.norm(x - cj[:, None] * Q, axis=1) <= rtol * nx):
                idx.append(q)
                c[:, j] = cj
                break
        else:
            return None
    return idx, c


def prediction_hash(preds, full: np.ndarray) -> str:
    """sha256 of the candidate's OOF predictions over every report, concatenated and rounded to 1e-9, and of its
    full-training feature matrix rounded the same way: rows whose hash is identical are one column."""
    h = hashlib.sha256()
    for arr in (np.concatenate([np.asarray(p, dtype=np.float64).ravel() for p in preds]), full.ravel()):
        h.update((np.round(np.asarray(arr, dtype=np.float64), 9) + 0.0).tobytes())
    return h.hexdigest()


def max_gain_step_down(observed, gains) -> list[float]:
    """Westfall and Young's max-gain step-down p over a family: observed (m,) gains and gains (m, B) null gains of
    the same B replicates (the permutation of replicate b shared by every row). Rows are ordered by observed gain,
    largest first; the p of the row at position j is (1 + the number of b where the largest null gain among the
    rows at positions j and later is at least its observed gain) / (B + 1), then made non-decreasing down the
    order. The floor is 1/(B + 1)."""
    obs, G = np.asarray(observed, dtype=np.float64), np.asarray(gains, dtype=np.float64)
    m = len(obs)
    if m == 0:
        return []
    if G.ndim != 2 or G.shape[0] != m:
        raise ValueError("every row needs the same number of null gains")
    order = np.argsort(-obs, kind="stable")
    B = G.shape[1]
    p, running = [0.0] * m, 0.0
    for j in range(m):
        tail = order[j:]
        top = np.max(G[tail], axis=0) if B else np.zeros(0)
        running = max(running, (1 + int(np.sum(top >= obs[order[j]]))) / (B + 1))
        p[order[j]] = running
    return p


FAST_NULL = True  # the NullEngine below; False refits every replicate from scratch (the reference the tests compare)


class NullEngine:
    """The honest refit of score() for a permuted candidate, computing only what a gene permutation changes.

    Permuting genes within every perturbation's row leaves the multiset of a candidate column's training values
    unchanged, so its standardisation (mean, sd) and its own Gram block c'c are the same for every replicate, and the
    fixed columns (the parent) do not change at all. Per fold only the cross terms P'c and c'(y - ybar) and the
    prediction c_fold @ w are recomputed: milliseconds instead of a full design rebuild. The result equals score()
    on the permuted parts up to floating-point summation order (tests pin it).

    With parent_cols (indices into the columns of design(fixed, ...)) the engine also keeps those raw parent
    columns per fit, so score_pert can rebuild a proportional candidate as a permuted per-perturbation scalar times
    the parent column in every fold view (the perturbation null); there the candidate's standardisation and c'c
    change with the replicate and are recomputed."""

    def __init__(self, fixed, res: dict, feats: list[str], data: Data, seeds, alphas, parent_cols=None):
        self.data, self.seeds, self.alphas, self.parent_cols = data, list(seeds), list(alphas), parent_cols
        self.folds = {s: [self._fit(fixed, res, feats, data, ("fold", s, i), fold["rows"],
                                    len(fold["rows"]) - len(fold["predict"]), [data.pos[p] for p in fold["predict"]])
                          for i, fold in enumerate(data.folds[s])] for s in self.seeds}
        self.full = None
        if data.val1 is not None:
            self.full = self._fit(fixed, res, feats, data, ("full",), data.train, len(data.train), None,
                                  eval_rows=data.val1_rows)

    @staticmethod
    def _std(Xtr: np.ndarray):
        mu, sd = Xtr.mean(axis=0), Xtr.std(axis=0)
        sd[sd == 0] = 1.0
        return mu, sd

    def _fit(self, fixed, res, feats, data, where, rows, n_tr, out_rows, eval_rows=None):
        """Everything constant across replicates for one fit: the standardised fixed columns of the training and
        predicted rows, their Gram and label products, and the candidate's raw blocks with its standardisation."""
        n_g = data.n_genes
        Xf = design(fixed, where) if fixed else np.zeros((len(rows), n_g, 0))
        if eval_rows is None:
            Xf_tr, Xf_out = Xf[:n_tr].reshape(-1, Xf.shape[2]), Xf[n_tr:].reshape(-1, Xf.shape[2])
        else:
            Xf_tr = Xf.reshape(-1, Xf.shape[2])
            Xe = design(fixed, ("eval",))[eval_rows] if fixed else np.zeros((len(eval_rows), n_g, 0))
            Xf_out = Xe.reshape(-1, Xe.shape[2])
        mu_f, sd_f = self._std(Xf_tr)
        Ps_tr, Ps_out = (Xf_tr - mu_f) / sd_f, (Xf_out - mu_f) / sd_f
        src = res["folds"][where[1]][where[2]]["blocks"] if where[0] == "fold" else res["full"]
        C = np.concatenate([src[f] for f in feats], axis=2)
        if eval_rows is None:
            C_tr, C_out = C[:n_tr], C[n_tr:]
        else:
            C_tr, C_out = C, np.concatenate([res["eval"][f][eval_rows] for f in feats], axis=2)
        k = C.shape[2]
        mu_c, sd_c = self._std(C_tr.reshape(-1, k))
        y = data.Y[[data.pos[p] for p in rows[:n_tr]]].reshape(-1) if eval_rows is None else data.Y.reshape(-1)
        ybar = float(y.mean())
        yc = y - ybar
        cs = ((C_tr - mu_c) / sd_c).reshape(-1, k)
        fit = {"Ps_tr": Ps_tr, "Ps_out": Ps_out, "Gpp": Ps_tr.T @ Ps_tr, "bp": Ps_tr.T @ yc, "yc": yc,
               "ybar": ybar, "C_tr": C_tr, "C_out": C_out, "mu_c": mu_c, "sd_c": sd_c, "Gcc": cs.T @ cs,
               "out_rows": out_rows, "n_out": C_out.shape[0]}
        if self.parent_cols is not None and eval_rows is None:
            fit["Q_tr"], fit["Q_out"] = Xf[:n_tr][:, :, self.parent_cols], Xf[n_tr:][:, :, self.parent_cols]
            fit["pos"] = np.array([data.pos[p] for p in rows])
        return fit

    def _predict(self, fit: dict, perm: np.ndarray, alphas) -> np.ndarray:
        """(n_alpha, n_out_rows) predictions of the fixed columns plus the candidate permuted across genes."""
        return self._predict_columns(fit, fit["C_tr"][:, perm, :], fit["C_out"][:, perm, :], fit["mu_c"],
                                     fit["sd_c"], fit["Gcc"], alphas)

    @staticmethod
    def _predict_columns(fit: dict, C_tr, C_out, mu_c, sd_c, Gcc, alphas) -> np.ndarray:
        """(n_alpha, n_out_rows) predictions of the fixed columns plus a candidate block (training and predicted
        rows) with the given standardisation and Gram block."""
        k = C_tr.shape[2]
        cs = ((C_tr - mu_c) / sd_c).reshape(-1, k)
        co = ((C_out - mu_c) / sd_c).reshape(-1, k)
        Gpc = fit["Ps_tr"].T @ cs
        G = np.block([[fit["Gpp"], Gpc], [Gpc.T, Gcc]])
        b = np.concatenate([fit["bp"], cs.T @ fit["yc"]])
        W = fa.ridge_weight_grid(G, b, np.arange(G.shape[0]), alphas)
        cp = fit["Gpp"].shape[0]
        return (fit["Ps_out"] @ W[:cp] + co @ W[cp:]).T + fit["ybar"]

    def _predict_pert(self, fit: dict, c: np.ndarray, alphas) -> np.ndarray:
        """The candidate rebuilt as c[row] times the kept parent column in this fit's rows, standardised afresh."""
        C_tr, C_out = c[fit["pos"][:len(fit["Q_tr"])]][:, None, :] * fit["Q_tr"], \
            c[fit["pos"][len(fit["Q_tr"]):]][:, None, :] * fit["Q_out"]
        k = C_tr.shape[2]
        mu_c, sd_c = self._std(C_tr.reshape(-1, k))
        cs = ((C_tr - mu_c) / sd_c).reshape(-1, k)
        return self._predict_columns(fit, C_tr, C_out, mu_c, sd_c, cs.T @ cs, alphas)

    def score(self, perm: np.ndarray) -> dict:
        """score(..., keep=False) for the candidate permuted across genes by perm."""
        return self._score(lambda fit, alphas: self._predict(fit, perm, alphas), perm)

    def score_pert(self, c: np.ndarray) -> dict:
        """score(..., keep=False) on the OOF tier for the candidate rebuilt as the per-perturbation scalars c
        (n_train, k) times the kept parent column; needs parent_cols."""
        return self._score(lambda fit, alphas: self._predict_pert(fit, c, alphas), None)

    def _score(self, predict, perm) -> dict:
        data, alphas = self.data, self.alphas
        O = {}
        for s in self.seeds:
            O[s] = np.zeros((len(alphas), len(data.train), data.n_genes))
            for fit in self.folds[s]:
                O[s][:, fit["out_rows"]] = predict(fit, alphas).reshape(len(alphas), -1, data.n_genes)
        P = {s: fa.pearson_rows(O[s], data.Y) for s in self.seeds}
        out = {"oof": {"m1": _honest_reports(P, self.seeds, alphas)[1]}}
        if self.full is not None and perm is not None:
            k = int(np.argmax(np.mean([P[s].mean(axis=1) for s in self.seeds], axis=0)))
            V = self._predict(self.full, perm, [alphas[k]])[0].reshape(len(data.val1_rows), data.n_genes)
            out["val1"] = {"m1": [fa.pearson_rows(V, data.val1.means - data.cm)]}
        return out


def _honest_reports(P: dict, seeds, alphas):
    """The reports of score(): alpha chosen on one seed's mean OOF pearson_delta, the other seed's scores reported
    (one seed: itself). Returns (reports, per-report per-perturbation scores, the chosen alpha index per seed)."""
    pick = {s: int(np.argmax(P[s].mean(axis=1))) for s in seeds}
    pairs = [(a, b) for a in seeds for b in seeds if a != b] or [(seeds[0], seeds[0])]
    reports = [{"select_seed": a, "report_seed": b, "alpha": alphas[pick[a]]} for a, b in pairs]
    return reports, [P[b][pick[a]] for a, b in pairs], pick, pairs


def null_summary(replicate, a, parent_sc: dict, observed: dict) -> dict:
    """Per tier of observed {tier: observed mean gain}: the B = a.null_reps replicate gains of replicate(b), their
    mean, sd, 95th percentile, the raw p (1 + the number at or above the observed) / (B + 1), the excess of the
    observed over the null mean, and the gains themselves (for the family-wise step-down). The first replicate of
    a source is timed and a wall-time estimate for the source's a.null_members null runs is printed."""
    got = {t: [] for t in observed}
    for b in range(a.null_reps):
        t0 = time.perf_counter()
        sc = replicate(b)
        if b == 0 and not getattr(a, "null_timed", True):
            dt, members = time.perf_counter() - t0, getattr(a, "null_members", 1)
            print(f"feature_compare: null estimate {members} members x {a.null_reps} replicates x {dt:.3f} s = "
                  f"{members * a.null_reps * dt / 60:.1f} min (measured on the first replicate)", flush=True)
            a.null_timed = True
        for t in observed:
            got[t].append(float(np.mean(report_deltas(sc, parent_sc, t))))
    out = {}
    for t, obs in observed.items():
        d = np.array(got[t])
        out[t] = {"reps": len(d), "mean": float(d.mean()), "sd": float(d.std(ddof=1)) if len(d) > 1 else 0.0,
                  "p95": float(np.quantile(d, 0.95)), "p": float((1 + np.sum(d >= obs)) / (len(d) + 1)),
                  "excess": float(obs - d.mean()), "observed": float(obs), "gains": d.tolist()}
    return out


def gene_null(fixed, res: dict, feats: list[str], data: Data, a, parent_sc: dict, observed: dict) -> dict:
    """The matched null per tier: replicate b permutes the candidate's genes (gene_permutation, seed null_seed + b,
    the same permutation for every candidate of the call) identically everywhere, refits with the full honest
    procedure and records the mean pearson_delta gain."""
    if a.null_reps < 1 or not feats:
        return {t: None for t in observed}
    engine = NullEngine(fixed, res, feats, data, a.seeds, a.alphas) if FAST_NULL else None

    def replicate(b):
        perm = gene_permutation(data.cm, a.null_bins, a.null_seed + b)
        return engine.score(perm) if engine else score(fixed + [(res, feats, perm)], data, a.seeds, a.alphas, keep=False)

    return null_summary(replicate, a, parent_sc, observed)


def pert_parts(fixed, res: dict, f: str, data: Data, parent_cols: list[int], c: np.ndarray) -> dict:
    """The candidate f rebuilt in every view as c[row] times the parent columns parent_cols of design(fixed, view),
    as a blocks record score() can read: the reference the fast perturbation null is tested against."""
    def build(where, rows):
        return c[[data.pos[p] for p in rows]][:, None, :] * design(fixed, where)[:, :, parent_cols]
    return {"full": {f: build(("full",), data.train)}, "eval": {},
            "folds": {s: [{**fd, "blocks": {f: build(("fold", s, i), fd["rows"])}} for i, fd in enumerate(folds)]
                      for s, folds in data.folds.items()}}


def pert_null(fixed, res: dict, f: str, data: Data, a, parent_sc: dict, observed: float, parent_cols: list[int],
              c: np.ndarray) -> dict | None:
    """The perturbation-level null of a proportional candidate (OOF tier): replicate b permutes the per-perturbation
    scalars c across the training perturbations within pert_bins (pert_permutation, seed null_seed + b, the same
    permutation for every candidate of the call), keeps every parent column in place, rebuilds the candidate as the
    permuted scalar times the parent column in every fold view and scores it with the full honest procedure."""
    if a.null_reps < 1:
        return None
    bins = pert_bins(data, a.null_bins)
    engine = NullEngine(fixed, res, [f], data, a.seeds, a.alphas, parent_cols=parent_cols) if FAST_NULL else None
    oof_only = replace(data, val1=None)  # the slow reference scores the OOF tier only, as the engine does

    def replicate(b):
        cb = c[pert_permutation(bins, a.null_seed + b)]
        return (engine.score_pert(cb) if engine
                else score(fixed + [(pert_parts(fixed, res, f, data, parent_cols, cb), [f], None)], oof_only,
                           a.seeds, a.alphas, keep=False))

    return null_summary(replicate, a, parent_sc, {"oof": observed})["oof"]


def holm(ps: list[float]) -> list[float]:
    order = np.argsort(ps, kind="stable")
    adj, running = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = running
    return adj


def evaluate_row(row: dict, parent_tiers: dict, parent_sc: dict, fixed, res, feats, data: Data, a) -> dict:
    """Every number of an add-one or set row except the nulls: per-tier metrics, paired gains over the parent,
    report deltas, and for an add-one row the standardised coefficient of the candidate's columns per report
    (coef_candidate_std, its mean and sign; one column: floats, several: lists) and the prediction hash. The row's
    model is fixed (the parent, or the part of it a run kept) plus feats of res. Returns the observed mean gain per
    tier, for null_row."""
    sc = score(fixed + ([(res, feats, None)] if feats else []), data, a.seeds, a.alphas)
    row["tiers"], observed = {}, {}
    for t in a.tiers:
        tm = tier_metrics(sc, data, t)
        deltas = report_deltas(sc, parent_sc, t)
        observed[t] = float(np.mean(deltas))
        row["tiers"][t] = {"n": tm["n"], "honest": len(a.seeds) > 1 or t != "oof", "metrics": tm["metrics"],
                           "delta": paired(tm, parent_tiers[t], data, t), "report_deltas": deltas,
                           "alphas": [r["alpha"] for r in sc[t]["reports"]]}
    if row["kind"] == "add_one" and feats:
        k = res["full"][feats[0]].shape[2]
        coef = sc["oof"]["coef"][:, -k:]
        mean = coef.mean(axis=0)
        sign = ["+" if m > 0 else "-" if m < 0 else "0" for m in mean]
        row["coef_candidate_std"] = coef[:, 0].tolist() if k == 1 else coef.tolist()
        row["coef_candidate_mean"] = float(mean[0]) if k == 1 else mean.tolist()
        row["coef_candidate_sign"] = sign[0] if k == 1 else sign
        row["prediction_hash"] = prediction_hash(sc["oof"]["preds"], res["full"][feats[0]])
    del sc
    return observed


def null_row(row: dict, observed: dict, parent_sc: dict, fixed, res, feats, data: Data, a, prop=None) -> None:
    """The row's nulls: the gene null per tier (tiers[t].null), and for an add-one row proportional to a parent
    column (prop = (parent column indices, c) from proportional_to_parent) the perturbation null on the OOF tier
    (tiers.oof.null_pert; None for every other row)."""
    for t, nul in gene_null(fixed, res, feats, data, a, parent_sc, observed).items():
        row["tiers"][t]["null"] = nul
    row["tiers"]["oof"]["null_pert"] = (pert_null(fixed, res, feats[0], data, a, parent_sc, observed["oof"], *prop)
                                        if prop and row["kind"] == "add_one" else None)
    if row["tiers"]["oof"]["null_pert"]:
        row["tiers"]["oof"]["null_pert"]["parent_column"] = row.get("parent_column")


def feature_facts(res: dict, f: str, parent_full: np.ndarray, data: Data) -> dict:
    """Columns; label dependence (a fold block differs from the full-training block on the same rows: the feature
    read training labels); the largest |correlation| with a parent column over the full-training rows."""
    full = res["full"][f]
    dep = any(np.max(np.abs(fd["blocks"][f] - full[[data.pos[p] for p in fd["rows"]]]), initial=0.0) > 1e-12
              for folds in res["folds"].values() for fd in folds)
    X = np.concatenate([full.reshape(-1, full.shape[2]), parent_full.reshape(-1, parent_full.shape[2])], axis=1)
    sd = X.std(axis=0)
    Z = (X - X.mean(axis=0)) / np.where(sd > 0, sd, 1.0)
    R = (Z.T @ Z) / len(Z)
    r = np.abs(R[:full.shape[2], full.shape[2]:])
    return {"n_columns": int(full.shape[2]), "label_dependent": bool(dep), "max_abs_r_parent": float(r.max())}


def null_too_coarse(family: int, reps: int) -> int | None:
    """The replicates a family needs before its step-down p can be read, when reps falls short: MIN_REPS_FAMILY
    (999, floor 0.001) for a family of more than one row, else enough for the floor 1/(B+1) to reach P_MAX (19).
    None when reps suffice."""
    need = MIN_REPS_FAMILY if family > 1 else int(np.ceil(1 / P_MAX)) - 1
    return need if reps < need else None


def verdict(row: dict, deciding: str, family: int, a) -> None:
    """Meaningful (development) iff, on the deciding tier: mean M1 gain > max(2 SE_adj, MIN_GAIN) with wins > n/2,
    the family-wise step-down p (p_fwer) of the gene null <= 0.05 and, for a candidate proportional to a parent
    column, of the perturbation null too, a mean M2 gain > 0 and mse_top not significantly worse; every OOF report
    gains; and the alpha was chosen honestly (more than one fold seed). A null too coarse for the family (fewer
    than 999 replicates for a family of more than one row) is said so, not blamed on the feature."""
    t = row["tiers"][deciding]
    m1, m2, m4 = (t["delta"][m] for m in ("pearson_delta", "pearson_delta_nontarget", "mse_top"))
    failed = []
    if "se_adj" not in m1 or not (m1["mean_diff"] > 2 * m1["se_adj"] and m1["wins_a"] > m1["n"] / 2):
        failed.append("M1 gain not above 2 SE_adj with wins > n/2")
    if "mean_diff" in m1 and not m1["mean_diff"] > MIN_GAIN:
        failed.append(f"M1 gain not above the minimum effect {MIN_GAIN}")
    if not all(d > 0 for d in row["tiers"]["oof"]["report_deltas"]):
        failed.append("an OOF report does not gain")
    need = null_too_coarse(family, a.null_reps)
    if t.get("null") is None:
        failed.append("no null (--null-reps 0, or nothing beyond the parent to permute)")
    elif need:
        failed.append(f"null too coarse for a family of {family} (need --null-reps >= {need})")
    elif not t["null"]["p_fwer"] <= P_MAX:
        failed.append(f"null p (FWER) > {P_MAX}")
    if row.get("proportional"):
        np_ = row["tiers"]["oof"].get("null_pert")
        if np_ is None:
            failed.append("proportional to a parent column but no perturbation null")
        elif not need and not np_["p_fwer"] <= P_MAX:
            failed.append(f"perturbation null p (FWER) > {P_MAX}")
    if len(a.seeds) == 1:
        failed.append("one fold seed: alpha chosen and reported on the same OOF predictions")
    if not m2.get("mean_diff", -1.0) > 0:
        failed.append("no M2 gain")
    if "se_adj" in m4 and m4["mean_diff"] < -2 * m4["se_adj"]:
        failed.append("mse_top significantly worse")
    row["failed_criteria"], row["meaningful"] = failed, not failed
    # how far a pass can be trusted: OOF is never held out; val1 is not held out for a run that selected on it
    how = ("OOF only, not held out" if deciding == "oof" else
           "optimistic: source selected on val1" if row.get("exposure") == "val1+oof" else "val1")
    row["verdict"] = f"meaningful (development, {how})" if not failed else "not: " + "; ".join(failed)


# ================================================================== the run
def parse(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", required=True, help="bundle or public directory (public.npz, knowledge/)")
    ap.add_argument("--out", required=True)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--parent", choices=["builtin"], default="builtin")
    g.add_argument("--parent-run", help="finished run: its selected single model is the parent")
    ap.add_argument("--source", action="append", default=[], metavar="NAME=DIR",
                    help="every *.py in DIR, each with its own class params")
    ap.add_argument("--source-run", action="append", default=[], metavar="NAME=RUN_DIR",
                    help="add-one rows: the run's selected features that the parent lacks; set row: the run's "
                         "selected model with its recorded params")
    ap.add_argument("--fold-seeds", default="101,102,103")
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--groups", choices=["auto", "none", "gene"], default="auto")
    ap.add_argument("--null-reps", type=int, default=MIN_REPS_FAMILY,
                    help="null replicates B; the p floor is 1/(B+1), a family of more than one row needs >= 999")
    ap.add_argument("--null-seed", type=int, default=0)
    ap.add_argument("--null-bins", type=int, default=10)
    ap.add_argument("--with-val1", action="store_true", help="also score the visible validation set (val1.npz)")
    ap.add_argument("--timeout-s", type=float, default=1800)
    ap.add_argument("--ram-mb", type=float, default=8192)
    a = ap.parse_args(argv)
    a.seeds = list(dict.fromkeys(int(s) for s in a.fold_seeds.split(",") if s.strip()))
    if not a.seeds or a.k < 2:
        raise Unusable("need at least one fold seed and --k >= 2")
    a.alphas = alpha_grid()
    a.tiers = ["oof"] + (["val1"] if a.with_val1 else [])
    return a


def named(items, what) -> list[tuple[str, Path]]:
    out = []
    for item in items:
        name, _, path = item.partition("=")
        if not name.replace("-", "_").isidentifier() or not path or not Path(path).is_dir():
            raise Unusable(f"{what} {item!r}: expected NAME=existing directory, NAME of letters, digits, _ and -")
        out.append((name, Path(path)))
    if len({n for n, _ in out}) != len(out):
        raise Unusable(f"duplicate {what} names")
    return out


def main(argv=None) -> int:
    try:
        return run(parse(argv))
    except Unusable as exc:
        print(f"feature_compare: {exc}", file=sys.stderr)
        return 2


def run(a) -> int:
    t0 = time.perf_counter()
    data_dir, out_dir = Path(a.data), Path(a.out)
    from_runs = named(a.source_run, "--source-run")
    sources, run_sources = named(a.source, "--source") + from_runs, {n for n, _ in from_runs}
    if len({n for n, _ in sources}) != len(sources):
        raise Unusable("a source name is used twice")
    with tempfile.TemporaryDirectory(prefix="feature_compare_") as tmp:
        work = Path(tmp)
        pub = work / "public"
        manifest = public_copy(data_dir, pub)
        data = make_data(pub)
        pr = read_selected(Path(a.parent_run)) if a.parent_run else None
        if pr:
            same_split(pr, manifest, "the parent run")
        a.groups = resolve_groups(a.groups, data, manifest, pr["cv_groups"] if pr else None)
        if a.with_val1:
            data.val1 = load_val1(data_dir, data.ctx)
            ev = [p for p in data.ctx.perts if p not in set(data.train)]
            data.val1_rows = [ev.index(p) for p in data.val1.perts]

        # ---- the parent: built-ins, or a run's selected model with its guard-passing plugin files
        parent_files = {}
        pdir = work / "parent" / "exec"
        pdir.mkdir(parents=True)
        if pr:
            p_feats, p_params = pr["features"], {f: dict(v) for f, v in pr["params"].items()}
            for f in sorted((Path(a.parent_run) / "feature_store").glob("*.py")):
                parent_files[f.stem] = static_check(f, data, imported=True, enforce_literal=False)
            copy_files([Path(c["file"]) for c in parent_files.values() if c["status"] == "ok"], pdir)
        else:
            p_feats = list(BUILTIN_FEATURES) + (["additive_response"] if data.pair_ids else [])
            p_params = {}
        p_res = run_child(work / "parent" / "blocks", pub, pdir, p_feats, p_params, a)
        if "failed" in p_res or p_res["errors"]:
            raise Unusable(f"the parent cannot be computed: {p_res.get('failed') or p_res['errors']}")
        data.folds = {s: [{"predict": fd["predict"], "rows": fd["rows"]} for fd in fs]
                      for s, fs in p_res["folds"].items()}
        fixed = [(p_res, p_feats, None)]
        parent_sc = score(fixed, data, a.seeds, a.alphas)
        parent_tiers = {t: tier_metrics(parent_sc, data, t) for t in a.tiers}
        parent_full = design(fixed, ("full",))
        for sc_t in parent_sc.values():
            sc_t.pop("preds", None)

        rows = []
        for name, src_dir in sources:
            rows += score_source(name, src_dir, name in run_sources, data, a, work, pub, pdir, p_feats, p_params,
                                 fixed, parent_sc, parent_tiers, parent_full, manifest)

    # the family-wise correction within each source's add-one rows (duplicates already collapsed, status
    # "duplicate"); a source's set row is a family of one: the max-gain step-down (p_fwer, the verdict's), and Holm
    # on the raw p kept beside it for comparison (p_holm)
    deciding = "val1" if a.with_val1 else "oof"
    families = {}
    for name, _ in sources:
        for kind in ("add_one", "set"):
            fam = [r for r in rows if r["source"] == name and r["kind"] == kind and r["status"] == "ok"]
            families.setdefault(name, {})[kind] = len(fam)
            for t in a.tiers:
                for key in ("null", "null_pert"):
                    with_p = [r for r in fam if r["tiers"][t].get(key)]
                    nulls = [r["tiers"][t][key] for r in with_p]
                    for nul, ph, pf in zip(nulls, holm([x["p"] for x in nulls]),
                                           max_gain_step_down([x["observed"] for x in nulls],
                                                              [x["gains"] for x in nulls])):
                        nul["p_holm"], nul["p_fwer"] = ph, pf
            for r in fam:
                verdict(r, deciding, len(fam), a)
    caveats = [TOP_CAVEAT, "ridge on the tool's alpha grid with an honest OOF alpha; a parent run's own model type "
               "and alpha are not reused", "the literal caps make pasting labels into a file expensive, not impossible"]
    if deciding == "oof":
        caveats.insert(0, OOF_CAVEAT)
    elif pr or run_sources:
        caveats.insert(0, "val1 decides, but a lab run selected its model on val1: rows of a --source-run are marked "
                          "optimistic" + (", and the parent's own val1 scores are optimistic too" if pr else ""))
    if len(a.seeds) == 1:
        caveats.append("one fold seed: alpha selected and reported on the same OOF predictions (not honest)")
    result = {
        "tool": "feature_compare", "format": 1, "lab_commit": _commit(),
        "data": data_record(data_dir, manifest), "split_id": manifest.get("split_id"),
        "settings": {"model": "ridge", "alphas": a.alphas, "alpha_rule": "honest_oof", "fold_seeds": a.seeds,
                     "k": a.k, "groups": a.groups, "null": "gene permutation within control-mean bins",
                     "null_pert": "per-perturbation scalar of a candidate proportional to a parent column permuted "
                                  "within bins of the targets' mean control expression, parent columns in place",
                     "correction": "max-gain step-down permutation (p_fwer) within each source's add-one rows, "
                                   "duplicates by prediction hash collapsed first; Holm on the raw p kept as p_holm",
                     "p_floor": 1 / (a.null_reps + 1), "min_gain": MIN_GAIN,
                     "null_reps": a.null_reps, "null_seed": a.null_seed, "null_bins": a.null_bins,
                     "tiers": a.tiers, "deciding_tier": deciding, "families": families,
                     "labels_read": ["training labels (public.npz)"]
                                    + (["visible validation labels (val1.npz)"] if a.with_val1 else []),
                     "timeout_s": a.timeout_s, "ram_mb": a.ram_mb},
        "caveats": caveats,
        "parent": {"source": pr["run"] if pr else "builtin", "exposure": "val1+oof" if pr else "none",
                   **({"run_id": pr["run_id"], "split_id": pr["split_id"], "experiment_id": pr["experiment_id"]}
                      if pr else {}),
                   "features": p_feats, "params": p_params, "n_columns": int(parent_full.shape[2]),
                   "files": parent_files,
                   "tiers": {t: {"n": parent_tiers[t]["n"], "metrics": parent_tiers[t]["metrics"],
                                 "alphas": [r["alpha"] for r in parent_sc[t]["reports"]]} for t in a.tiers}},
        "rows": rows, "wall_s": round(time.perf_counter() - t0, 1),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "feature_compare.json").write_text(json.dumps(result, indent=1, default=float))
    (out_dir / "feature_compare.md").write_text(markdown(result))
    print(f"feature_compare: {len(rows)} rows -> {out_dir / 'feature_compare.md'}")
    return 0


def same_split(sel: dict, manifest: dict, who: str) -> None:
    """A run's features were selected on its split's labels: refuse a run from another split of the data (its
    visible validation perturbations may be training ones here, or the reverse). AGENTS.md: compare runs only
    within the same bundle and split. A side without a split_id cannot be checked; the output records both."""
    if sel["split_id"] and manifest.get("split_id") and sel["split_id"] != manifest["split_id"]:
        raise Unusable(f"{who} used split {sel['split_id']}, --data holds {manifest['split_id']}")


def data_record(data_dir: Path, manifest: dict) -> dict:
    """What the numbers were computed on: the bundle's name, knowledge files added after it was built, and the
    hashes of the public files read, so two outputs on the same directory name can be told apart."""
    h = {"public.npz": hashlib.sha256((data_dir / "public.npz").read_bytes()).hexdigest()}
    for f in sorted(x for x in (data_dir / "knowledge").glob("*") if x.is_file()):
        h[f"knowledge/{f.name}"] = hashlib.sha256(f.read_bytes()).hexdigest()
    added = added_knowledge(data_dir) if manifest else None
    return {"name": data_dir.name, "added_knowledge": added, "sha256": h}


def score_source(name, src_dir, from_run, data, a, work, pub, pdir, p_feats, p_params, fixed, parent_sc,
                 parent_tiers, parent_full, manifest) -> list[dict]:
    """One source's rows: static checks of every file, smoke of each candidate, its blocks in one child, then an
    add-one row per candidate and one set row. For a --source the set row is the parent plus every candidate that
    passed; for a --source-run it is the run's selected model: the parent features it kept, its own features, and
    the parent features it retuned (recomputed with its recorded params). The source's blocks are dropped when its
    rows are done."""
    home = work / "sources" / name
    edir = home / "exec"
    shutil.copytree(pdir, edir)
    p_res, kept, retuned, info, files = fixed[0][0], list(p_feats), [], {"exposure": "oof"}, {}
    if from_run:
        sel = read_selected(src_dir)
        same_split(sel, manifest, f"--source-run {name}")
        cands = [f for f in sel["features"] if f not in p_feats]
        params = {f: dict(sel["params"].get(f, {})) for f in sel["features"]}
        retuned = [f for f in p_feats if f in params and params[f] != p_params.get(f, {})]
        kept = [f for f in p_feats if f in params and f not in retuned]
        info = {"exposure": "val1+oof", "run": sel["run"], "run_id": sel["run_id"], "split_id": sel["split_id"],
                "experiment_id": sel["experiment_id"], "selected": sel["features"],
                "dropped_parent": [f for f in p_feats if f not in params], "retuned_parent": retuned}
        for f in sorted((src_dir / "feature_store").glob("*.py")):
            c = static_check(f, data, imported=True, enforce_literal=False)
            if c["status"] == "ok" and (edir / f.name).exists() and (edir / f.name).read_bytes() != f.read_bytes():
                c.update(status="collision", reason=f"{f.name} differs from the parent's file of that name")
            files[f.stem] = c
        rows = {}
        for f in cands:
            c = files.get(f) or ({"status": "ok", "reason": "", "file": "builtin"} if f in ALL_BUILTIN_FEATURES
                                 else {"status": "error", "reason": "no plugin file in the run's feature_store"})
            rows[f] = {"source": name, "kind": "add_one", "feature": f, **c}
        copy_files([Path(c["file"]) for f, c in files.items()
                    if c["status"] == "ok" and not (edir / f"{f}.py").exists()], edir)
    else:
        taken = set(p_feats) | set(ALL_BUILTIN_FEATURES) | {p.stem for p in pdir.glob("*.py")}
        rows = {f.stem: {"source": name, "kind": "add_one", "feature": f.stem,
                         **static_check(f, data, imported=False, enforce_literal=True, taken=taken)}
                for f in sorted(src_dir.glob("*.py"))}
        params = {f: {} for f in rows}
        copy_files([Path(r["file"]) for r in rows.values() if r["status"] == "ok"], edir)
    for f, r in rows.items():
        if r["status"] == "ok" and r["file"] != "builtin":
            failed = smoke(f, params[f], pub, edir, home / "smoke" / f, a)
            if failed:
                r.update(status=failed[0], reason=failed[1][:500])
                (edir / f"{f}.py").unlink()  # nothing that failed its smoke test is executed again
    live = [f for f, r in rows.items() if r["status"] == "ok"]
    res = (run_child(home / "blocks", pub, edir, live + retuned, {**p_params, **params}, a) if live + retuned
           else {"errors": {}})
    errors = res.get("errors", {})
    for f in live:
        if "failed" in res or f in errors:
            rows[f].update(status="error", reason=(res.get("failed") or errors[f])[:500])
    live = [f for f in live if rows[f]["status"] == "ok"]
    for f in rows:
        rows[f]["exposure"] = info["exposure"]
    pcols, prop, observed = parent_column_names(fixed), {}, {}
    for f in live:
        rows[f].update(feature_facts(res, f, parent_full, data))
        rows[f]["params"] = params.get(f, {})
        prop[f] = proportional_to_parent(res["full"][f], parent_full)
        rows[f]["proportional"] = prop[f] is not None
        rows[f]["parent_column"] = ", ".join(pcols[q] for q in prop[f][0]) if prop[f] else None
        observed[f] = evaluate_row(rows[f], parent_tiers, parent_sc, fixed, res, [f], data, a)
    # rows with one prediction hash are one column: the first in order is kept, the others are not family members
    first = {}
    for f in live:
        kept_f = first.setdefault(rows[f]["prediction_hash"], f)
        if kept_f == f:
            rows[f]["duplicates"] = []
        else:
            rows[kept_f]["duplicates"].append(f)
            rows[f].update(status="duplicate", reason=f"duplicate of {kept_f}: identical OOF predictions and "
                                                     "feature matrix", meaningful=False,
                           failed_criteria=[f"duplicate of {kept_f}"], verdict=f"duplicate of {kept_f}")
    unique = [f for f in live if rows[f]["status"] == "ok"]
    a.null_members, a.null_timed = len(unique) + sum(1 for f in unique if prop[f]) + 1, False
    for f in unique:
        null_row(rows[f], observed[f], parent_sc, fixed, res, [f], data, a, prop[f])
    out = list(rows.values())
    set_row = {"source": name, "kind": "set", "feature": "(set)", "features": live, **info, "status": "ok",
               "reason": ""}
    # a run's model is rebuilt exactly or not at all: every own feature passed, every parent feature it uses is the
    # parent's file (not a different one of the same name) and every retuned one computes with the run's params
    lost = ([f for f in rows if f not in live] + [f for f in retuned if f in errors]
            + [f for f in kept + retuned if from_run and f in files and files[f]["status"] != "ok"])
    if "failed" in res:
        set_row.update(status="error", reason=res["failed"][:500])
    elif from_run and lost:
        set_row.update(status="error", reason=f"the run's model cannot be rebuilt: {', '.join(lost)} failed a "
                                              "check, could not be computed or differs from the parent's file")
    elif not live and not from_run:
        set_row.update(status="error", reason="no feature of this source passed the checks")
    else:
        own = live + retuned
        set_row["model"] = kept + own
        set_row["n_columns"] = int(sum(p_res["full"][f].shape[2] for f in kept)
                                   + sum(res["full"][f].shape[2] for f in own))
        set_fixed = [(p_res, kept, None)] if kept else []
        obs = evaluate_row(set_row, parent_tiers, parent_sc, set_fixed, res, own, data, a)
        null_row(set_row, obs, parent_sc, set_fixed, res, own, data, a)
    del res
    return out + [set_row]


def _commit() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, capture_output=True,
                              text=True, timeout=10).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


# ================================================================== the report
def _f(x, nd=4) -> str:
    return "" if x is None else f"{x:.{nd}f}"


def _gain(d: dict) -> str:
    return f"{d['mean_diff']:+.4f} ± {d['se_adj']:.4f}" if "se_adj" in d else f"n={d['n']}"


def _wins(d: dict) -> str:
    return f"{d['wins_a']}/{d['n']}" if "wins_a" in d else ""


def markdown(r: dict) -> str:
    s, p, dd = r["settings"], r["parent"], r["data"]
    L = [f"# Feature comparison: {dd['name']}", "",
         f"- data: `{dd['name']}`" + (f", split `{r['split_id']}`" if r["split_id"] else "")
         + f", knowledge added after the build: {', '.join(dd['added_knowledge'] or []) or 'none'}"
         + f" (public.npz sha256 {dd['sha256']['public.npz'][:12]}); lab commit `{r['lab_commit']}`",
         f"- parent: `{p['source']}`" + (f" ({p['experiment_id']})" if p.get("experiment_id") else "")
         + f", {len(p['features'])} features, {p['n_columns']} columns: {', '.join(p['features'])}",
         f"- fold seeds {s['fold_seeds']}, k = {s['k']}, groups {s['groups']}; ridge, alpha grid {s['alphas']}, "
         "alpha chosen on one seed's OOF and reported on another",
         f"- tiers: {', '.join(s['tiers'])}; deciding tier: {s['deciding_tier']}; labels read: "
         + "; ".join(s["labels_read"]),
         f"- null: {s['null']}, {s['null_reps']} replicates (seed {s['null_seed']}, {s['null_bins']} bins; p floor "
         f"{s.get('p_floor', 1 / (s['null_reps'] + 1)):.4g}); a candidate proportional to a parent column also gets "
         f"the perturbation null ({s.get('null_pert', 'none')}) and must pass both; family-wise correction: "
         f"{s.get('correction', 'Holm')}; minimum effect {s.get('min_gain', MIN_GAIN)}; family sizes after "
         "deduplication: " + (", ".join(f"{k} {v['add_one']}" for k, v in s["families"].items()) or "none"),
         "- metrics: M1 pearson_delta, M2 pearson_delta_nontarget, M3 mse, M4 mse_top, M5 r2_top, M6 "
         "pearson_delta_top, M7 direction_acc_top, M12 delta scale ratio; gains are candidate minus parent (M4: "
         "parent minus candidate), ± the overlap-adjusted paired SE", ""]
    L += [f"**Caveat:** {c}." for c in r["caveats"]] + [""]
    L += ["## Table 1. Systems: feature set + linear model", "",
          _md(["row", "tier", "n features", "n columns", *LABEL.values(), "ΔM1 ± SE_adj", "wins/n",
               "null p (FWER)", "verdict"]), "|" + "---|" * 16]
    for t in s["tiers"]:
        m = p["tiers"][t]["metrics"]
        L.append(_md(["parent", t, len(p["features"]), p["n_columns"], *(_f(m[k]) for k in LABEL), "", "", "", ""]))
    for row in (x for x in r["rows"] if x["kind"] == "set"):
        if row["status"] != "ok":
            L.append(_md([f"{row['source']} (set)", "", "", "", *[""] * 11, row["reason"]]))
            continue
        for t in s["tiers"]:
            tt = row["tiers"][t]
            m, d1, nul = tt["metrics"], tt["delta"]["pearson_delta"], tt.get("null") or {}
            L.append(_md([f"{row['source']} (set)", t, len(row["model"]), row["n_columns"], *(_f(m[k]) for k in LABEL),
                          _gain(d1), _wins(d1), _f(nul.get("p_fwer"), 3), _verdict(row, t, s)]))
    for row in (x for x in r["rows"] if x["kind"] == "set" and "run" in x):
        L.append(f"\n`{row['source']} (set)` is run `{row['run']}`, {row['experiment_id']}, split "
                 f"`{row['split_id']}`: {', '.join(row['selected'])}; parent features it dropped: "
                 f"{', '.join(row['dropped_parent']) or 'none'}; recomputed with its own params: "
                 f"{', '.join(row['retuned_parent']) or 'none'}.")
    L += ["", "## Table 2. Single features added to the parent", "",
          _md(["source", "feature", "tier", "status", "ΔM1 ± SE_adj", "wins/n", "ΔM2", "ΔM4", "ΔM5", "ΔM7",
               "null p raw / Holm / FWER", "excess", "pert null p raw / FWER (parent column)", "coef sign",
               "max abs r", "label-dependent", "literal (numbers, string bytes, names)", "verdict"]),
          "|" + "---|" * 18]
    for row in (x for x in r["rows"] if x["kind"] == "add_one"):
        lit = row.get("literal") or {}
        lit_s = (f"{lit['numeric_constants']}, {lit['string_bytes']}, {lit['name_literals']}"
                 + ("" if lit.get("ok", True) else " (over caps)")) if "numeric_constants" in lit else ""
        if row["status"] != "ok":
            L.append(_md([row["source"], row["feature"], "", row["status"], *[""] * 12, lit_s, row["reason"][:160]]))
            continue
        for t in s["tiers"]:
            d, nul = row["tiers"][t]["delta"], row["tiers"][t].get("null") or {}
            pn = row["tiers"][t].get("null_pert") or {}
            L.append(_md([row["source"], row["feature"], t, "ok", _gain(d["pearson_delta"]), _wins(d["pearson_delta"]),
                          *(_f(d[m].get("mean_diff")) for m in ("pearson_delta_nontarget", "mse_top", "r2_top",
                                                                "direction_acc_top")),
                          f"{_f(nul.get('p'), 3)} / {_f(nul.get('p_holm'), 3)} / {_f(nul.get('p_fwer'), 3)}",
                          _f(nul.get("excess")),
                          f"{_f(pn.get('p'), 3)} / {_f(pn.get('p_fwer'), 3)} ({pn.get('parent_column')})" if pn
                          else ("not proportional" if row.get("proportional") is False else ""),
                          _coef_sign(row), _f(row["max_abs_r_parent"], 3), "yes" if row["label_dependent"] else "no",
                          lit_s, _verdict(row, t, s)]))
    return "\n".join(L) + "\n"


def _coef_sign(row: dict) -> str:
    """The sign of the candidate's mean standardised coefficient and how many reports agree with it (one column);
    the signs per column for several."""
    coef, sign = row.get("coef_candidate_std"), row.get("coef_candidate_sign")
    if coef is None:
        return ""
    if isinstance(sign, list):
        return "".join(sign)
    agree = sum(1 for c in coef if (c > 0) == (sign == "+") and c != 0)
    return f"{sign} ({agree}/{len(coef)} reports)"


def _md(cells) -> str:
    return "| " + " | ".join(str(c).replace("|", "/").replace("\n", " ") for c in cells) + " |"


def _verdict(row: dict, tier: str, s: dict) -> str:
    if tier != s["deciding_tier"]:
        return "(deciding tier: " + s["deciding_tier"] + ")"
    return row["verdict"]


if __name__ == "__main__":
    sandbox.reexec_under_hash_seed("feature_compare")
    if len(sys.argv) == 3 and sys.argv[1] in ("_blocks", "_smoke"):
        sys.exit((child_main if sys.argv[1] == "_blocks" else smoke_main)(sys.argv[2]))
    sys.exit(main())
