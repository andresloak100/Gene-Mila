#!/usr/bin/env python3
"""Replay model-selection rules over finished runs: offline and free (no LLM, no API, no new experiment).

For every completed experiment that kept its artifact (predictions.npz with the chosen alpha; cv.npz when the
run cross-validated), the visible selection score is recomputed under each rule in benchmark.SELECTION_RULES
exactly as the lab computes it, and the sealed metrics come from the bundle's private labels. Per rule the
report shows the single model the rule would have made the run's best, with that model's sealed metrics, next
to the model the run actually picked and its starting model.

It reads the sealed labels directly, so it is an analysis of finished runs and never part of one: no oracle
query is logged and nothing feeds back into a run. The alpha grid inside one experiment cannot be replayed
(only the chosen alpha's predictions are kept), so this answers "which experiment would the rule have picked",
not "which alpha"; alpha variants the exploit engine queued as experiments of their own are covered.

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

SEALED = ["pearson_delta", "r2_top", "mse_top", "cellforge_mse_de", "cellforge_pcc_de", "cellforge_r2_de"]
HEAD = ["sealed pearson_delta", "sealed R²_top", "sealed MSE_top", "MSE_DE", "PCC_DE", "R²_DE"]


def _bundle(run_dir: Path, cfg: dict) -> dict:
    data_dir = Path(cfg["run"]["data_dir"])
    pub = run_dir / "public_data" / "public.npz"
    if not pub.exists():
        pub = data_dir / "public.npz"
    z = np.load(pub, allow_pickle=False)
    return {"control_mean": z["control_cells"].astype(np.float64).mean(axis=0),
            "train": LabelSet([str(p) for p in z["train_perts"]], z["train_means"].astype(np.float64)),
            "val1": LabelSet.load(data_dir / "private" / "val1.npz"),
            "val2": LabelSet.load(data_dir / "private" / "val2.npz"),
            "ref2": reference.load(data_dir, "val2")}


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
    n1, nt = len(d["val1"].perts), len(d["train"].perts)
    cands, skipped = [], []
    for e in exps:
        art = Path(e["artifact_dir"])
        if not (art / "predictions.npz").exists():
            skipped.append(e["experiment_id"])
            continue
        delta, perts = _chosen(art / "predictions.npz", e.get("best_alpha"))
        idx = {p: i for i, p in enumerate(perts)}
        if any(p not in idx for p in d["val1"].perts + d["val2"].perts):
            skipped.append(e["experiment_id"])
            continue
        pred1 = delta[[idx[p] for p in d["val1"].perts]] + d["control_mean"]
        m1 = evaluate(pred1, d["val1"].means, d["control_mean"], d["val1"].perts)["metrics"]
        m_cv = None
        if (art / "cv.npz").exists():
            cdelta, cperts = _chosen(art / "cv.npz", e.get("best_alpha"))
            if cperts == d["train"].perts:
                m_cv = evaluate(cdelta + d["control_mean"], d["train"].means, d["control_mean"],
                                d["train"].perts)["metrics"]
        visible = {}
        for rule in rules:
            comb = {m: (m1[m] if m_cv is None else (n1 * m1[m] + nt * m_cv[m]) / (n1 + nt))
                    for m in SELECTION_RULES[rule]}
            visible[rule] = selection_score(comb, rule)
        pred2 = delta[[idx[p] for p in d["val2"].perts]] + d["control_mean"]
        m2 = evaluate(pred2, d["val2"].means, d["control_mean"], d["val2"].perts)["metrics"]
        m2.update(comparable.score(pred2, d["val2"].means, d["val2"].perts, d["ref2"], d["control_mean"]))
        cands.append({"experiment_id": e["experiment_id"], "features": e.get("feature_set_json") or [],
                      "model": e.get("model_type"), "best_alpha": e.get("best_alpha"),
                      "recorded_visible": e.get("primary_score"), "cross_validated": m_cv is not None,
                      "visible": visible, "sealed": {k: m2.get(k) for k in SEALED}})
    picks = {}
    for rule in rules:
        best = max(cands, key=lambda c: c["visible"][rule], default=None)
        picks[rule] = None if best is None else {**best, "visible_score": best["visible"][rule]}
    summary = json.loads((run_dir / "summary.json").read_text()) if (run_dir / "summary.json").exists() else {}
    actual = {}
    for g in summary.get("generalization_query_only") or []:
        key = "start" if g.get("kind") == "baseline" else "best"
        if key in actual:
            continue
        comp = (g.get("comparable") or {}).get("val2") or {}
        actual[key] = {"experiment_id": g.get("experiment_id"), "kind": g.get("kind"),
                       "visible_score": g.get("visible_score"),
                       "sealed": {"pearson_delta": g.get("query_only_pearson_delta", g.get("query_only_score")),
                                  **{k: comp.get(k) for k in SEALED if k.startswith("cellforge_")}}}
    return {"run_id": summary.get("run_id", run_dir.name), "dir": run_dir.name, "arm": run_arm(cfg, summary),
            "workers": summary.get("workers") or cfg.get("run", {}).get("workers"),
            "code": (summary.get("base_commit") or "")[:7], "rule_used": summary.get("selection", {}).get("rule")
            or cfg.get("experiment", {}).get("selection") or "pearson_delta",
            "n_candidates": len(cands), "skipped": skipped,
            "cross_validated": bool(cands) and all(c["cross_validated"] for c in cands),
            "rules": picks, "actual": actual,
            "top": {rule: sorted(cands, key=lambda c: -c["visible"][rule])[:5] for rule in rules}}


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
    rules = list(next(iter(reports))["rules"]) if reports else list(SELECTION_RULES)
    L = ["# Selection-rule replay over finished runs", "",
         "Offline and free: for every completed experiment that kept its predictions, the visible selection score "
         "is recomputed under each rule exactly as the lab computes it (validation set plus out-of-fold training "
         "perturbations where the run cross-validated), and the sealed metrics come from the private labels. "
         "Each rule's row is the single model it would have made the run's best; 'run's pick' is the finalist the "
         "run reported (an ensemble when one was kept), and 'start' its starting model. Only the chosen alpha of "
         "each experiment survives on disk, so the rule is replayed across experiments, not inside one alpha "
         "grid. No oracle query is made or logged.", ""]
    for r in reports:
        note = "" if r["cross_validated"] else " (no out-of-fold predictions: visible = validation set only)"
        L += [f"## {r['dir']}: {r['arm']}, {r['workers']} workers, code {r['code'] or '?'}", "",
              f"{r['n_candidates']} candidate experiments{note}; the run itself selected by {r['rule_used']}"
              + (f"; {len(r['skipped'])} skipped (artifact missing or incomplete)" if r["skipped"] else "") + ".", "",
              "| rule | picked | model | visible score | " + " | ".join(HEAD) + " |",
              "|---|---|---|---|" + "---|" * len(HEAD)]
        for rule in rules:
            p = r["rules"].get(rule)
            if p is None:
                L.append(f"| {rule} | – | | | " + " | ".join("–" for _ in HEAD) + " |")
                continue
            feats = ", ".join(p["features"][:6]) + (", …" if len(p["features"]) > 6 else "")
            L.append(f"| {rule} | {p['experiment_id']} | {p['model']} on {feats} | {_f(p['visible_score'])} | "
                     + " | ".join(_f(p["sealed"].get(k)) for k in SEALED) + " |")
        for key, label in (("best", "run's pick"), ("start", "start")):
            a = r["actual"].get(key)
            if a:
                L.append(f"| {label} ({a['kind']}) | {a['experiment_id']} | | {_f(a.get('visible_score'))} | "
                         + " | ".join(_f(a["sealed"].get(k)) for k in SEALED) + " |")
        L.append("")
    if len(reports) > 1:
        base = rules[0]
        L += ["## Across runs", "", "| rule | pick differs from the first rule in | " + " | ".join(HEAD) + " |",
              "|---|---|" + "---|" * len(HEAD)]
        for rule in rules:
            picks = [r["rules"].get(rule) for r in reports]
            diff = sum(1 for r, p in zip(reports, picks)
                       if p and r["rules"].get(base) and p["experiment_id"] != r["rules"][base]["experiment_id"])
            L.append(f"| {rule} | {diff} of {len(reports)} runs | "
                     + " | ".join(_ms(_stats([p["sealed"].get(k) for p in picks if p])) for k in SEALED) + " |")
        L.append("")
        for rule in rules[1:]:
            pairs = [(r["rules"][rule]["sealed"], r["rules"][base]["sealed"]) for r in reports
                     if r["rules"].get(rule) and r["rules"].get(base)]
            for k, h in (("pearson_delta", "sealed pearson_delta"), ("cellforge_r2_de", "R²_DE"), ("cellforge_mse_de", "MSE_DE")):
                ds = [a[k] - b[k] for a, b in pairs if a.get(k) is not None and b.get(k) is not None]
                if ds:
                    st = _stats(ds)
                    better = sum(1 for x in ds if (x < 0 if k == "cellforge_mse_de" else x > 0))
                    L.append(f"- {rule} minus {base}, {h}: {st['mean']:+.4f}" + (f" ± {st['sd']:.4f}" if st["n"] > 1 else "")
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
