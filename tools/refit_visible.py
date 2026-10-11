#!/usr/bin/env python3
"""Refit every model a finished run already scored on the sealed set on all visible labels, then score each
refit once on the sealed set through the lab's oracle. A pre-specified protocol replayed over finished runs,
free of any LLM.

A run trains every model on the training perturbations only and uses the visible validation perturbations to
select among them; the labels of those validation perturbations are visible to the controller but never enter
a fit. This tool asks what the run's finalists are worth once they are fitted on every label the controller may
see: for each run, every model the run scored on the sealed set (its top single finalists, its ensemble when one
was kept, and its starting baseline) is refitted on the training perturbations plus the visible validation
perturbations, with exactly the same feature set, feature parameters, model type, chosen alpha and seed, and
the refit is scored once on the sealed perturbations. The report puts the original sealed metrics next to the
refit ones. The protocol was fixed before any sealed result under it was read and it is reported whatever it
shows; nothing is selected, tuned or chosen by a sealed score. The run directories are read only: the tool
never writes into a run, its database, its cache or its query log, and uses an oracle instance of its own.

The run's plugins are computed in this process, so from the command line the tool re-executes itself under
PYTHONHASHSEED=0, the seed of every experiment process of the lab (genemila.sandbox.HASH_SEED): a plugin that follows
str hashes (the order of a set of names, or hash() in a past run's plugin) then computes what the lab computed, and
the same in every invocation, rather than refitting another model under every shell's own seed. The JSON's protocol
records the seed the refits ran under and whether the tool re-executed.

    python tools/refit_visible.py --runs runs/a runs/b --out docs/results/refit_visible.md [--arm-ensembles]
    python tools/refit_visible.py --from-json docs/results/refit_visible.json --out docs/results/refit_visible.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from genemila.benchmark.oracle import QueryOracle  # noqa: E402  (the only sealed read: one query per refit)
from genemila.benchmark.table import run_arm  # noqa: E402
from genemila.features import registry  # noqa: E402
from genemila.features.api import REGISTRY, FeatureContext  # noqa: E402
from genemila.features.registry import ALL_BUILTIN_FEATURES  # noqa: E402
from genemila.lab import additive_delta, open_run  # noqa: E402
from genemila.pipeline import build_matrix, make_model  # noqa: E402
from genemila.sandbox import python_hash_seed, reexec_under_hash_seed, reexecuted_under_hash_seed  # noqa: E402
from genemila.spec import ExperimentSpec  # noqa: E402

METRICS = ["pearson_delta", "cellforge_mse_de", "cellforge_pcc_de", "cellforge_r2_de"]
HEAD = {"pearson_delta": "pearson_delta", "cellforge_mse_de": "MSE_DE", "cellforge_pcc_de": "PCC_DE",
        "cellforge_r2_de": "R²_DE"}
LOWER_IS_BETTER = {"cellforge_mse_de"}
PRIMARY = "pearson_delta"


# ------------------------------------------------------------------ the fit, as pipeline.run does it
def training_context(lab, cache_dir: Path, augment: bool = True) -> FeatureContext:
    """The feature context of a refit: the run's public data with its own cache directory (never the run's).
    With augment=True the training set is the public training perturbations plus the visible validation
    perturbations with their labels; with augment=False it is the public training set alone, which reproduces
    the run's own fits (an internal check, not a reporting option)."""
    ctx = FeatureContext(lab.public_dir, Path(cache_dir) / "shared")
    if not augment:
        return ctx
    extra = lab._val1  # the visible validation labels, visible to the controller throughout the run
    return ctx.with_extra_train(extra.perts, extra.means - lab.control_mean)


def _load_run_plugins(store: Path) -> list[str]:
    """Load the run's feature plugins afresh: features of a previous run must not survive by name."""
    for name in list(REGISTRY):
        if name not in ALL_BUILTIN_FEATURES:
            del REGISTRY[name]
    return registry.load_plugins(store)


def _bundle_key(public_dir: Path, dataset: str, split_id: str) -> str:
    """Names the cache directory of a run's refits by what the cached contents depend on: the public data
    (its genes, perturbations, control cells and training labels), never the run directory. Runs on one bundle
    share their feature blocks and gene correlation; runs on different bundles, even run directories of the
    same name, never read each other's."""
    z = np.load(Path(public_dir) / "public.npz", allow_pickle=False)
    h = hashlib.sha256()
    for k in ("genes", "perts", "train_perts", "control_cells", "train_means"):
        h.update(np.ascontiguousarray(z[k]).tobytes())
    return f"{dataset}__{split_id}__{h.hexdigest()[:12]}"


def fit_predict(ctx: FeatureContext, feature_set: list[str], feature_params: dict, model_type: str, alpha: float,
                seeds: list[int], feature_cache: Path | None, perts_out: list[str],
                plugin_dir: Path | None = None) -> np.ndarray:
    """Predicted deltas (len(perts_out), n_genes) of one model fitted as genemila.pipeline.run fits it: feature
    blocks for the context's training perturbations and for every perturbation outside the training set,
    standardised with the training mean and standard deviation (a zero deviation becomes 1), one linear model
    on the flattened training deltas, predictions stored at single precision. With several seeds the whole
    computation is repeated under each seed (the run's plugins re-executed from plugin_dir so module-level
    state starts fresh, the features recomputed without the disk cache, the model refitted) and the predicted
    deltas averaged; the model types are deterministic given the features, so only feature code that draws
    random numbers can make the seeds differ. The first seed uses the disk cache, as the pipeline does."""
    train = list(ctx.train_perts)
    evals = [p for p in ctx.perts if p not in set(train)]
    missing = [p for p in perts_out if p not in set(evals)]
    if missing:
        raise ValueError(f"perturbations {missing[:3]} are not outside the training set")
    preds = []
    for i, seed in enumerate(seeds):
        np.random.seed(int(seed))
        view, cache = ctx, feature_cache
        if i > 0:
            if plugin_dir is not None:
                _load_run_plugins(plugin_dir)
            view, cache = ctx.without_train([]), None  # same training set, fresh memo caches, no cached block
        timings: dict = {}
        X_tr, _ = build_matrix(view, feature_set, feature_params, train, timings, cache)
        X_ev, _ = build_matrix(view, feature_set, feature_params, evals, timings, cache)
        _, d_train = view.train_delta()
        y = d_train.reshape(-1)
        mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)
        sd[sd == 0] = 1.0
        X_tr = (X_tr - mu) / sd
        X_ev = (X_ev - mu) / sd
        model = make_model(model_type, float(alpha), int(seed))
        model.fit(X_tr, y)
        p = model.predict(X_ev).reshape(len(evals), ctx.n_genes)
        if not np.all(np.isfinite(p)):
            raise ValueError(f"model produced non-finite predictions at alpha={alpha}")
        preds.append(p.astype(np.float32).astype(np.float64))
    delta = np.mean(preds, axis=0)
    idx = {p: i for i, p in enumerate(evals)}
    return delta[[idx[p] for p in perts_out]]


def _analytic_delta(ctx: FeatureContext, group: str, perts: list[str]) -> np.ndarray:
    """The analytic baselines have no code: no change, the mean training delta, or (a bundle with pairs) the lab's
    additive rule, genemila.lab.additive_delta, each over the context's training set, so a refit on the visible
    labels counts the visible validation singles as training singles. Any other group is refused rather than
    refitted as something it is not."""
    if group == "baseline_unchanged":
        return np.zeros((len(perts), ctx.n_genes))
    train, d = ctx.train_delta()
    if group == "baseline_mean_response":
        return np.tile(d.mean(axis=0), (len(perts), 1))
    if group == "baseline_additive":
        return additive_delta(perts, {p: ctx.target_genes(p) for p in [*train, *perts]}, train, d)
    raise ValueError(f"unknown analytic baseline {group!r}")


def _model_of(rec: dict) -> tuple[str, float, int]:
    spec = ExperimentSpec.from_record(rec)
    alpha = 0.0 if spec.model_type == "ols" else rec.get("best_alpha")
    if alpha is None:
        alpha = spec.hyperparameters.get("alpha", 1.0)
    return spec.model_type, float(alpha), int(spec.seed)


# ------------------------------------------------------------------ one run
def _finalists(lab) -> dict:
    """Every model the run scored on the sealed set: single finalists, the kept ensemble, the starting baseline."""
    db = lab.db
    singles = db.query("SELECT * FROM experiments WHERE status='completed' AND query_metrics_json IS NOT NULL "
                       "AND COALESCE(kind, '') NOT IN ('baseline', 'ensemble') ORDER BY primary_score DESC, experiment_id")
    ens = db.query("SELECT * FROM experiments WHERE status='completed' AND kind='ensemble' "
                   "AND query_metrics_json IS NOT NULL ORDER BY experiment_id LIMIT 1")
    base = lab.best_baseline()
    return {"singles": singles, "ensemble": ens[0] if ens else None, "baseline": base}


def _metrics(m: dict | None) -> dict:
    return {k: (None if m is None or m.get(k) is None else float(m[k])) for k in METRICS}


def _difference(orig: dict, refit: dict) -> dict:
    return {k: (None if orig.get(k) is None or refit.get(k) is None else float(refit[k] - orig[k])) for k in METRICS}


def refit_run(run_dir: Path, cache_dir: Path, seed_repeats: int = 1, augment: bool = True) -> dict:
    """Refit and score every sealed-scored model of one run. Returns the report row (JSON-ready) and, under
    "_arrays", the selected finalist's original and refit sealed predictions for arm ensembles."""
    run_dir = Path(run_dir).resolve()
    lab = open_run(run_dir)
    try:
        cfg = json.loads((run_dir / "config.json").read_text()) if (run_dir / "config.json").exists() else lab.cfg
        summary = json.loads((run_dir / "summary.json").read_text()) if (run_dir / "summary.json").exists() else {}
        fin = _finalists(lab)
        singles, ens, base = fin["singles"], fin["ensemble"], fin["baseline"]
        if base is not None and not base.get("query_metrics_json"):
            base = None
        n_queries = len(singles) + (1 if ens else 0) + (1 if base else 0)
        oracle = QueryOracle(lab.data_dir, max_queries=n_queries, used=None, selection=lab.selection)
        perts = oracle.perts  # sealed perturbation ids only
        cache = Path(cache_dir) / _bundle_key(lab.public_dir, lab.dataset, lab.split_id)
        feature_cache = cache / "features"
        _load_run_plugins(lab.store)
        public = FeatureContext(lab.public_dir, cache / "shared")
        ctx = training_context(lab, cache, augment=augment)
        scored = [s for s in singles] + ([ens] if ens else [])
        selected = max(scored, key=lambda r: (r.get("primary_score") or 0.0))["experiment_id"] if scored else None
        refits: dict[str, np.ndarray] = {}  # experiment_id -> predicted delta on the sealed perturbations

        def refit_delta(rec: dict) -> np.ndarray:
            eid = rec["experiment_id"]
            if eid not in refits:
                if rec.get("kind") == "ensemble":
                    members = (rec.get("diagnostics_json") or {}).get("members") or []
                    refits[eid] = np.mean([refit_delta(lab.db.get_experiment(m)) for m in members], axis=0)
                elif rec.get("kind") == "baseline" and not rec.get("artifact_dir"):
                    refits[eid] = _analytic_delta(ctx, rec.get("hypothesis_group") or "", perts)
                else:
                    spec = ExperimentSpec.from_record(rec)
                    model_type, alpha, seed = _model_of(rec)
                    refits[eid] = fit_predict(ctx, spec.feature_set, spec.feature_params, model_type, alpha,
                                              [seed + i for i in range(int(seed_repeats))], feature_cache, perts,
                                              plugin_dir=lab.store)
            return refits[eid]

        rows, arrays = [], {}
        for role, recs in (("single", singles), ("ensemble", [ens] if ens else []), ("baseline", [base] if base else [])):
            for rec in recs:
                eid = rec["experiment_id"]
                if role == "ensemble":
                    model_type, alpha, seed = "ensemble", None, None
                elif rec.get("artifact_dir"):
                    model_type, alpha, seed = _model_of(rec)
                else:
                    model_type, alpha, seed = rec.get("model_type"), None, None
                delta = refit_delta(rec)
                pred = delta + lab.control_mean
                q = oracle.query(eid, pred, perts, lab.control_mean)
                orig, refit = _metrics(rec.get("query_metrics_json")), _metrics(q["metrics"])
                rows.append({
                    "experiment_id": eid, "role": role, "kind": rec.get("kind"), "selected": eid == selected,
                    "model": model_type, "alpha": alpha, "seed": seed,
                    "features": list(rec.get("feature_set_json") or []),
                    "feature_params": rec.get("feature_params_json") or {},
                    "members": ((rec.get("diagnostics_json") or {}).get("members") if role == "ensemble" else None),
                    "visible_score": (None if rec.get("primary_score") is None else float(rec["primary_score"])),
                    "original": orig, "refit": refit, "difference": _difference(orig, refit)})
                if eid == selected:
                    orig_pred, orig_perts = lab._predict(rec, perts)
                    order = {p: i for i, p in enumerate(orig_perts)}
                    arrays = {"perts": list(perts), "original": orig_pred[[order[p] for p in perts]], "refit": pred,
                              "data_dir": lab.data_dir, "control_mean": lab.control_mean, "selection": lab.selection}
        return {
            "run_id": summary.get("run_id", run_dir.name), "dir": run_dir.name, "path": str(run_dir),
            "arm": run_arm(cfg, summary), "workers": summary.get("workers") or cfg.get("run", {}).get("workers"),
            "code": (summary.get("base_commit") or lab.base_commit or "")[:7],
            "dataset": lab.dataset, "split_id": lab.split_id, "selection_rule": lab.selection,
            "n_train": len(public.train_perts), "n_visible_validation": len(lab._val1.perts),
            "n_train_refit": len(ctx.train_perts), "n_sealed": len(perts), "augmented": bool(augment),
            "train_signature": {"original": public.train_signature, "refit": ctx.train_signature},
            "seeds_per_fit": int(seed_repeats), "selected": selected, "finalists": rows,
            "n_queries": len(oracle.queries), "_arrays": arrays,
        }
    finally:
        lab.close()
        lab.db.close_thread_conn()


# ------------------------------------------------------------------ across runs
def _stats(vals: list) -> dict | None:
    vals = [float(v) for v in vals if v is not None]
    if not vals:
        return None
    a = np.asarray(vals, dtype=float)
    return {"n": len(a), "mean": float(a.mean()), "sd": float(a.std(ddof=1)) if len(a) > 1 else 0.0,
            "min": float(a.min()), "max": float(a.max())}


def _selected_row(r: dict) -> dict | None:
    return next((f for f in r["finalists"] if f["selected"]), None)


def _arm_key(r: dict) -> tuple:
    return (r["dataset"], r["split_id"], r["arm"], r["workers"])


def _arm_label(key: tuple, multi_dataset: bool) -> str:
    dataset, split_id, arm, workers = key
    return f"{arm}, {workers} workers" + (f" on {dataset}" if multi_dataset else "")


def arm_ensemble(runs: list[dict], label: str) -> dict:
    """Average the selected finalists' sealed predictions over an arm's runs, once for the original predictions
    and once for the refit predictions, and score each average once. Every run of the arm takes part."""
    first = runs[0]
    perts = first["_arrays"]["perts"]
    orig, refit = [], []
    for r in runs:
        a = r["_arrays"]
        if a["perts"] != perts:
            raise ValueError(f"{r['dir']} predicts other sealed perturbations than {first['dir']}")
        orig.append(a["original"])
        refit.append(a["refit"])
    a = first["_arrays"]
    oracle = QueryOracle(a["data_dir"], max_queries=2, used=None, selection=a["selection"])
    if oracle.perts != perts:
        raise ValueError("the arm's sealed perturbations do not match the oracle's")
    qo = oracle.query(f"arm:{label}:original", np.mean(orig, axis=0), perts, a["control_mean"])
    qr = oracle.query(f"arm:{label}:refit", np.mean(refit, axis=0), perts, a["control_mean"])
    o, f = _metrics(qo["metrics"]), _metrics(qr["metrics"])
    return {"original": o, "refit": f, "difference": _difference(o, f), "n_queries": len(oracle.queries)}


def analyse(run_dirs: list[Path], cache_dir: Path, seed_repeats: int = 1, arm_ensembles: bool = False) -> dict:
    runs = [refit_run(Path(d), cache_dir, seed_repeats) for d in run_dirs]
    codes = {r["code"] for r in runs if r["code"]}
    if len(codes) > 1:  # runs on different code are different arms, as the results tables treat them
        for r in runs:
            r["arm"] = f"{r['arm']} @ {r['code'] or 'unknown code'}"
    groups: dict[tuple, list[dict]] = {}
    for r in runs:
        groups.setdefault(_arm_key(r), []).append(r)
    multi = len({k[0] for k in groups}) > 1
    arms = []
    for key, rs in sorted(groups.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][2]), kv[0][3] or 0)):
        sel = [(r, _selected_row(r)) for r in rs]
        sel = [(r, s) for r, s in sel if s is not None]
        label = _arm_label(key, multi)
        diffs = [s["difference"][PRIMARY] for _, s in sel]
        arm = {"label": label, "arm": key[2], "workers": key[3], "dataset": key[0], "split_id": key[1],
               "n": len(rs), "run_ids": [r["dir"] for r in rs],
               "original": _stats([s["original"][PRIMARY] for _, s in sel]),
               "refit": _stats([s["refit"][PRIMARY] for _, s in sel]),
               "difference": _stats(diffs),
               "improved": sum(1 for d in diffs if d is not None and d > 0),
               "ensemble": None}
        if arm_ensembles and len(rs) >= 2 and all(r["_arrays"] for r in rs):
            arm["ensemble"] = arm_ensemble(rs, label)
        arms.append(arm)
    diffs = [s["difference"][PRIMARY] for r in runs for s in [_selected_row(r)] if s and s["difference"][PRIMARY] is not None]
    reading = {"n_runs": len(runs), "n_compared": len(diffs), "improved": sum(1 for d in diffs if d > 0),
               "worsened": sum(1 for d in diffs if d < 0), "difference": _stats(diffs)}
    for r in runs:
        r.pop("_arrays", None)
    return {"protocol": {"metrics": METRICS, "seeds_per_fit": int(seed_repeats), "arm_ensembles": bool(arm_ensembles),
                         "multi_dataset": multi,
                         # the str hash seed the plugins ran under: '0' from the command line, which re-executes
                         # itself under the lab's seed (and whether it did); a call from Python keeps its own
                         "python_hash_seed": python_hash_seed(), "hash_seed_reexec": reexecuted_under_hash_seed()},
            "runs": runs, "arms": arms, "reading": reading}


# ------------------------------------------------------------------ rendering
def _f(x, nd=4):
    return "n/a" if x is None else f"{x:.{nd}f}"


def _d(x, nd=4):
    return "n/a" if x is None else f"{x:+.{nd}f}"


def _a(x):
    return "n/a" if x is None else f"{x:g}"


def _ms(st, nd=4):
    return "n/a" if st is None else (f"{st['mean']:.{nd}f}" + (f" ± {st['sd']:.{nd}f}" if st["n"] > 1 else ""))


def _mds(st, nd=4):
    return "n/a" if st is None else (f"{st['mean']:+.{nd}f}" + (f" ± {st['sd']:.{nd}f}" if st["n"] > 1 else ""))


def _arrow(row: dict, k: str) -> str:
    return f"{_f(row['original'].get(k))} -> {_f(row['refit'].get(k))}"


def render(rep: dict) -> str:
    runs, arms, rd = rep["runs"], rep["arms"], rep["reading"]
    n_tr = sorted({r["n_train"] for r in runs})
    n_v = sorted({r["n_visible_validation"] for r in runs})
    seeds = rep["protocol"].get("seeds_per_fit", 1)
    L = ["# Refit on all visible labels, scored once on the sealed set", "",
         "Protocol, fixed before any sealed result under it was read and reported whatever it shows. For each "
         "finished run, every model the run already scored on the sealed set (its top single finalists, its "
         "ensemble when one was kept, and its starting baseline) is refitted on all visible labels: the "
         f"{', '.join(map(str, n_tr))} training perturbations the run trained on plus the {', '.join(map(str, n_v))} "
         "visible validation perturbations it only ever used for selection. The refit keeps exactly the same "
         "feature set, feature parameters, model type, chosen alpha and seed, is fitted as the pipeline fits "
         "(features for the training rows and the held-out rows, standardised by the training mean and standard "
         "deviation, one linear model on the flattened deltas), and is scored once on the sealed perturbations "
         "through the lab's oracle; the ensemble's refit is the mean of its members' refits. Nothing is selected, "
         "tuned or chosen by a sealed score: the finalists are the ones the run chose under its own protocol, "
         "the selected finalist of a run is its highest visible score among them, and every refit is reported. "
         "The run directories are read only (own oracle instance, own feature cache, no event and no query "
         "charged to the run)."
         + (f" Each fit is repeated under {seeds} consecutive seeds, the run's plugins re-executed and the features "
            "recomputed under each, and the predicted deltas averaged; the model fits are deterministic given the "
            "features, so only feature code that draws random numbers can make the seeds differ." if seeds > 1 else ""),
         "",
         "Read the numbers as one more look at a sealed set that is no longer fresh: before this protocol was "
         "written, the sealed perturbations had already been scored for dozens of finalists across about thirty "
         "runs, and that history shaped which models exist to be refitted. A refit gain here is evidence that "
         "the extra labels help, not a clean held-out confirmation; the untouched tests are the Norman bundle "
         "and any new split.",
         "", "## Selected finalist per run", "",
         "| run | arm | workers | selected | kind | model | alpha | sealed pearson_delta: original | refit | "
         "difference | MSE_DE original -> refit | PCC_DE original -> refit | R²_DE original -> refit |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in runs:
        s = _selected_row(r)
        if s is None:
            L.append(f"| {r['dir']} | {r['arm']} | {r['workers']} | none scored on the sealed set | | | | | | | | | |")
            continue
        L.append(f"| {r['dir']} | {r['arm']} | {r['workers']} | {s['experiment_id']} | {s['kind']} | {s['model']} | "
                 f"{_a(s['alpha'])} | {_f(s['original'][PRIMARY])} | "
                 f"{_f(s['refit'][PRIMARY])} | {_d(s['difference'][PRIMARY])} | "
                 + " | ".join(_arrow(s, k) for k in METRICS[1:]) + " |")
    L += ["", "## Every refit finalist", "",
          "Singles, the kept ensemble and the starting baseline of each run; the selected finalist is marked with *. "
          "Original = the run's own sealed score of the model fitted on the training perturbations; refit = the same "
          "model fitted on all visible labels.", "",
          "| run | finalist | kind | model | alpha | visible score | " + " | ".join(
              f"{HEAD[k]} original | refit | diff" for k in METRICS) + " |",
          "|---|---|---|---|---|---|" + "---|" * (3 * len(METRICS))]
    for r in runs:
        for s in r["finalists"]:
            L.append(f"| {r['dir']} | {s['experiment_id']}{'*' if s['selected'] else ''} | {s['kind']} | {s['model']} | "
                     f"{_a(s['alpha'])} | {_f(s['visible_score'])} | "
                     + " | ".join(f"{_f(s['original'].get(k))} | {_f(s['refit'].get(k))} | {_d(s['difference'].get(k))}"
                                  for k in METRICS) + " |")
    L += ["", "## By arm", "",
          "Mean ± sd over the arm's runs of the selected finalist's sealed pearson_delta, original and refit, and of "
          "their difference (refit minus original).", "",
          "| arm | workers | n | original | refit | difference | runs improved |", "|---|---|---|---|---|---|---|"]
    for a in arms:
        n_cmp = a["difference"]["n"] if a["difference"] else 0
        arm = a["arm"] + (f" on {a['dataset']}" if rep["protocol"].get("multi_dataset") else "")
        L.append(f"| {arm} | {a['workers']} | {a['n']} | {_ms(a['original'])} | {_ms(a['refit'])} | "
                 f"{_mds(a['difference'])} | {a['improved']} of {n_cmp} |")
    if rep["protocol"].get("arm_ensembles"):
        L += ["", "## Arm ensembles", "",
              "For each arm with at least two runs, the mean of the selected finalists' sealed predictions over all of "
              "the arm's runs (no run chosen by score), once from the original predictions and once from the refit "
              "predictions, each scored once.", "",
              "| arm | workers | n | pearson_delta: original ensemble | refit ensemble | difference | "
              "MSE_DE original -> refit | PCC_DE original -> refit | R²_DE original -> refit |",
              "|---|---|---|---|---|---|---|---|---|"]
        shown = 0
        for a in arms:
            e = a["ensemble"]
            if e is None:
                continue
            shown += 1
            arm = a["arm"] + (f" on {a['dataset']}" if rep["protocol"].get("multi_dataset") else "")
            L.append(f"| {arm} | {a['workers']} | {a['n']} | {_f(e['original'][PRIMARY])} | {_f(e['refit'][PRIMARY])} | "
                     f"{_d(e['difference'][PRIMARY])} | " + " | ".join(_arrow(e, k) for k in METRICS[1:]) + " |")
        if not shown:
            L.append("| no arm has two or more runs | | | | | | | | |")
    L += ["", "## Reading", ""]
    st = rd["difference"]
    if st is None:
        L.append("No run had a finalist scored on the sealed set, so there is nothing to compare.")
    else:
        L.append(f"The refit on all visible labels raised the selected finalist's sealed pearson_delta in {rd['improved']} "
                 f"of {rd['n_compared']} runs and lowered it in {rd['worsened']}; the difference (refit minus original) "
                 f"averages {st['mean']:+.4f}" + (f" ± {st['sd']:.4f}" if st["n"] > 1 else "")
                 + f" and ranges from {st['min']:+.4f} to {st['max']:+.4f}. "
                 "Caution: this is one split, scored on the same sealed perturbations the original finalists were "
                 "scored on, under a protocol written after those scores were known, and every run's finalist was "
                 "chosen under the original protocol (selected on the very perturbations the refit now trains on), "
                 "so the comparison says what more labels buy for the models the runs found, not which protocol "
                 "selects better.")
    return "\n".join(L) + "\n"


def _plain(obj):
    """JSON-ready copy: numpy scalars and arrays become Python numbers and lists, so the JSON twin renders the
    markdown byte for byte."""
    if isinstance(obj, dict):
        return {str(k): _plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_plain(v) for v in obj]
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def main(argv=None) -> int:
    """The command line (argv None: re-executed under PYTHONHASHSEED=0, the lab's seed, unless it already is that),
    or a call from Python with its arguments (argv), which runs in this process under whatever hash seed it has."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--runs", nargs="*", default=[], help="run directories (lab.db, config.json, summary.json, feature_store/)")
    ap.add_argument("--out", required=True, help="markdown report")
    ap.add_argument("--json", default=None, help="JSON twin (default: the report's path with .json)")
    ap.add_argument("--cache", default=None, help="feature cache directory for the refits (default: a temporary one)")
    ap.add_argument("--arm-ensembles", action="store_true", help="also average the selected finalists over each arm's runs")
    ap.add_argument("--from-json", default=None, help="re-render the markdown from a JSON twin; no run is opened")
    ap.add_argument("--seed-repeats", type=int, default=1,
                    help="repeat every fit under N consecutive seeds (features recomputed under each) and average "
                         "the predicted deltas; only feature code that draws random numbers can differ (default 1)")
    args = ap.parse_args(argv)
    if argv is None and not args.from_json:
        reexec_under_hash_seed("refit_visible")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.from_json:
        rep = json.loads(Path(args.from_json).read_text())
    else:
        if not args.runs:
            ap.error("--runs is required unless --from-json is given")
        if args.seed_repeats < 1:
            ap.error("--seed-repeats must be at least 1")
        if args.cache:
            rep = analyse([Path(r) for r in args.runs], Path(args.cache), args.seed_repeats, args.arm_ensembles)
        else:
            with tempfile.TemporaryDirectory(prefix="refit_visible_") as tmp:
                rep = analyse([Path(r) for r in args.runs], Path(tmp), args.seed_repeats, args.arm_ensembles)
        rep = _plain(rep)
        Path(args.json or out.with_suffix(".json")).write_text(json.dumps(rep, indent=1))
    md = render(rep)
    out.write_text(md)
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
