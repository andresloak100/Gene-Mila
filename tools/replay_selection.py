#!/usr/bin/env python3
"""Replay model-selection rules over finished runs on visible data only: offline and free (no LLM, no API,
no new experiment, and the sealed labels are never read).

The question is whether a selection rule picks models that do better on perturbations the rule did not
select on. Comparing rules by their sealed (query-only) outcome would tune the rule on the test set, so this
tool never opens the sealed labels. Every run that cross-validated (experiment.cv_folds) has two disjoint
visible parts instead: the visible validation set (val1, which also has a DE reference) and the out-of-fold
predictions of the training perturbations (cv.npz, which never saw their own labels). Each rule picks the
run's best experiment on one part, and that pick is scored on the other, in both directions:

    select on out-of-fold training -> score on val1 (pearson_delta, r2_top, mse_top, CellForge's DE metrics)
    select on val1                 -> score on out-of-fold training (pearson_delta, r2_top, mse_top)

Only the chosen alpha of each experiment survives on disk, so the rule is replayed across experiments, not
inside one alpha grid; alpha variants the exploit engine queued as experiments of their own are covered.
Runs without cv.npz have a single visible part and are skipped.

    python tools/replay_selection.py --runs runs/a runs/b --out docs/results/selection_replay.md
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from genemila.benchmark import SELECTION_RULES, comparable, reference, selection_score  # noqa: E402
from genemila.benchmark.evaluator import evaluate  # noqa: E402
from genemila.benchmark.table import run_arm  # noqa: E402
from genemila.data.bundle import LabelSet  # noqa: E402
from genemila.db import Database  # noqa: E402

SCORED = ["pearson_delta", "r2_top", "mse_top", "cellforge_mse_de", "cellforge_pcc_de", "cellforge_r2_de"]
HEAD = ["pearson_delta", "R²_top", "MSE_top", "MSE_DE", "PCC_DE", "R²_DE"]
LOWER_IS_BETTER = {"mse_top", "cellforge_mse_de"}
DIRECTIONS = [("select on out-of-fold training, score on validation", "train_oof", "val1"),
              ("select on validation, score on out-of-fold training", "val1", "train_oof")]


def _bundle(run_dir: Path, cfg: dict) -> dict:
    data_dir = Path(cfg["run"]["data_dir"])
    pub = run_dir / "public_data" / "public.npz"
    if not pub.exists():
        pub = data_dir / "public.npz"
    z = np.load(pub, allow_pickle=False)
    return {"control_mean": z["control_cells"].astype(np.float64).mean(axis=0),
            "train": LabelSet([str(p) for p in z["train_perts"]], z["train_means"].astype(np.float64)),
            "val1": LabelSet.load(data_dir / "private" / "val1.npz"),  # the visible validation set
            "ref1": reference.load(data_dir, "val1")}


def _chosen(path: Path, best_alpha) -> tuple[np.ndarray, list[str]]:
    z = np.load(path, allow_pickle=False)
    alphas = list(map(float, z["alphas"]))
    k = alphas.index(float(best_alpha)) if best_alpha is not None and float(best_alpha) in alphas else 0
    return z["delta"][k].astype(np.float64), [str(p) for p in z["perts"]]


def replay_run(run_dir: Path, rules: list[str] | None = None) -> dict:
    run_dir = Path(run_dir).resolve()
    cfg = json.loads((run_dir / "config.json").read_text())
    d = _bundle(run_dir, cfg)
    rules = list(rules or SELECTION_RULES)
    exps = Database(run_dir / "lab.db").query(
        "SELECT * FROM experiments WHERE status='completed' AND artifact_dir IS NOT NULL "
        "AND COALESCE(kind, '') NOT IN ('baseline', 'ensemble') ORDER BY experiment_id")
    cm = d["control_mean"]
    cands, skipped = [], {"no_artifact": 0, "no_oof": 0}
    for e in exps:
        art = Path(e["artifact_dir"])
        if not (art / "predictions.npz").exists():
            skipped["no_artifact"] += 1
            continue
        delta, perts = _chosen(art / "predictions.npz", e.get("best_alpha"))
        idx = {p: i for i, p in enumerate(perts)}
        if any(p not in idx for p in d["val1"].perts):
            skipped["no_artifact"] += 1
            continue
        if not (art / "cv.npz").exists():
            skipped["no_oof"] += 1
            continue
        cdelta, cperts = _chosen(art / "cv.npz", e.get("best_alpha"))
        if cperts != d["train"].perts:
            skipped["no_oof"] += 1
            continue
        pred1 = delta[[idx[p] for p in d["val1"].perts]] + cm
        m1 = evaluate(pred1, d["val1"].means, cm, d["val1"].perts)["metrics"]
        m1.update(comparable.score(pred1, d["val1"].means, d["val1"].perts, d["ref1"], cm))
        m_oof = evaluate(cdelta + cm, d["train"].means, cm, d["train"].perts)["metrics"]
        parts = {"val1": m1, "train_oof": m_oof}
        cands.append({"experiment_id": e["experiment_id"], "features": e.get("feature_set_json") or [],
                      "model": e.get("model_type"), "best_alpha": e.get("best_alpha"),
                      "parts": {part: {k: m.get(k) for k in SCORED if k in m} for part, m in parts.items()},
                      "scores": {rule: {part: selection_score(m, rule) for part, m in parts.items()} for rule in rules}})
    picks = {}
    for label, sel, score in DIRECTIONS:
        picks[label] = {}
        for rule in rules:
            best = max(cands, key=lambda c: c["scores"][rule][sel], default=None)
            picks[label][rule] = None if best is None else {
                "experiment_id": best["experiment_id"], "features": best["features"], "model": best["model"],
                "best_alpha": best["best_alpha"], "selection_score": best["scores"][rule][sel],
                "scored_on": score, "scored": best["parts"][score]}
    summary = json.loads((run_dir / "summary.json").read_text()) if (run_dir / "summary.json").exists() else {}
    return {"run_id": summary.get("run_id", run_dir.name), "dir": run_dir.name, "arm": run_arm(cfg, summary),
            "workers": summary.get("workers") or cfg.get("run", {}).get("workers"),
            "code": (summary.get("base_commit") or "")[:7],
            "rule_used": (summary.get("selection") or {}).get("rule") or cfg.get("experiment", {}).get("selection")
            or "pearson_delta",
            "n_candidates": len(cands), "skipped": skipped, "n_val1": len(d["val1"].perts),
            "n_train": len(d["train"].perts), "picks": picks}


def _f(x, nd=4):
    return "–" if x is None else f"{x:.{nd}f}"


def _stats(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    a = np.asarray(vals, dtype=float)
    return {"n": len(a), "mean": float(a.mean()), "sd": float(a.std(ddof=1)) if len(a) > 1 else 0.0}


def _ms(st, nd=4):
    return "–" if st is None else (f"{st['mean']:.{nd}f}" + (f" ± {st['sd']:.{nd}f}" if st["n"] > 1 else ""))


def render(reports: list[dict]) -> str:
    rules = list(next(iter(reports))["picks"][DIRECTIONS[0][0]]) if reports else list(SELECTION_RULES)
    L = ["# Selection-rule replay on visible data", "",
         "Offline and free, and the sealed (query-only) labels are never read: comparing rules by their sealed "
         "outcome would tune the rule on the test set. Each run that cross-validated has two disjoint visible "
         "parts, the visible validation set and the out-of-fold predictions of the training perturbations; a rule "
         "picks the run's best experiment on one part and the pick is scored on the other, both ways. Scores on "
         "the validation part include CellForge's top-20 DE metrics (its DE reference exists there); the "
         "out-of-fold part has pearson_delta, R² and MSE on each perturbation's 20 most changed genes. Only the "
         "chosen alpha of each experiment survives on disk, so a rule is replayed across experiments, not inside "
         "one alpha grid. Runs without out-of-fold predictions are skipped.", ""]
    usable = [r for r in reports if r["n_candidates"]]
    for r in reports:
        sk = r["skipped"]
        L += [f"## {r['dir']}: {r['arm']}, {r['workers']} workers, code {r['code'] or '?'}", ""]
        if not r["n_candidates"]:
            L += [f"Skipped: no experiment with out-of-fold predictions ({sk['no_oof']} without cv.npz, "
                  f"{sk['no_artifact']} without an artifact).", ""]
            continue
        L += [f"{r['n_candidates']} candidate experiments ({r['n_val1']} validation and {r['n_train']} out-of-fold "
              f"training perturbations); the run itself selected by {r['rule_used']} on both parts together"
              + (f"; skipped {sk['no_oof']} without out-of-fold predictions and {sk['no_artifact']} without an artifact"
                 if sk["no_oof"] or sk["no_artifact"] else "") + ".", "",
              "| direction | rule | picked | model | selection score | " + " | ".join(HEAD) + " |",
              "|---|---|---|---|---|" + "---|" * len(HEAD)]
        for label, sel, score in DIRECTIONS:
            for rule in rules:
                p = r["picks"][label].get(rule)
                if p is None:
                    continue
                feats = ", ".join(p["features"][:6]) + (", …" if len(p["features"]) > 6 else "")
                L.append(f"| {label} | {rule} | {p['experiment_id']} | {p['model']} on {feats} | "
                         f"{_f(p['selection_score'])} | " + " | ".join(_f(p["scored"].get(k)) for k in SCORED) + " |")
        L.append("")
    if len(usable) > 1:
        base = rules[0]
        L += [f"## Across the {len(usable)} usable runs", ""]
        for label, sel, score in DIRECTIONS:
            L += [f"**{label}**", "", "| rule | pick differs from {} in | ".format(base) + " | ".join(HEAD) + " |",
                  "|---|---|" + "---|" * len(HEAD)]
            for rule in rules:
                ps = [r["picks"][label][rule] for r in usable]
                diff = sum(1 for r, p in zip(usable, ps) if p and p["experiment_id"] != r["picks"][label][base]["experiment_id"])
                L.append(f"| {rule} | {diff} of {len(ps)} runs | "
                         + " | ".join(_ms(_stats([p["scored"].get(k) for p in ps if p])) for k in SCORED) + " |")
            L.append("")
            for rule in rules[1:]:
                for k, h in zip(SCORED, HEAD):
                    ds = [r["picks"][label][rule]["scored"][k] - r["picks"][label][base]["scored"][k] for r in usable
                          if r["picks"][label][rule]["scored"].get(k) is not None
                          and r["picks"][label][base]["scored"].get(k) is not None]
                    if not ds:
                        continue
                    st = _stats(ds)
                    better = sum(1 for x in ds if (x < 0 if k in LOWER_IS_BETTER else x > 0))
                    L.append(f"- {rule} minus {base}, {h}: {st['mean']:+.4f}"
                             + (f" ± {st['sd']:.4f}" if st["n"] > 1 else "")
                             + f" over {st['n']} runs; better in {better} of {st['n']}.")
            L.append("")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--runs", nargs="+", required=True, help="run directories (lab.db, config.json, artifacts/)")
    ap.add_argument("--out", required=True, help="markdown report; a .json twin is written next to it")
    ap.add_argument("--rules", nargs="*", default=None, help=f"rules to replay (default: all of {sorted(SELECTION_RULES)})")
    args = ap.parse_args(argv)
    reports = [replay_run(Path(r), args.rules) for r in args.runs]
    out = Path(args.out)
    out.write_text(render(reports))
    out.with_suffix(".json").write_text(json.dumps(reports, indent=1, default=str))
    print(render(reports))
    return 0


if __name__ == "__main__":
    sys.exit(main())
