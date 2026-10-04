#!/usr/bin/env python3
"""Efficiency comparison across worker counts, with spread and a noise check.

    python scaling_report.py --runs runs/scale_* [--out docs/results/scaling.md]

Groups runs by arm (planner/worker providers) and worker count, reports every
efficiency measure as mean ± sd over repeats, and says which differences
between worker counts exceed run-to-run noise (Welch's t-test on the sealed
gain, plus the spread of the free no-LLM control arm as the timing-noise
reference). Reads each run's summary.json (and analysis.json from
analyze_run.py when present).
"""

import argparse
import json
import math
from pathlib import Path

from genemila import REPO_ROOT
from genemila.benchmark.table import run_arm

MEASURES = [  # key, label, how to read it from (summary, analysis)
    ("best_visible", "best visible", lambda s, a: _visible(s, "best")),
    ("best_visible_single", "best visible (single model)", lambda s, a: (s.get("best") or {}).get("score")),
    ("best_sealed", "best sealed", lambda s, a: _sealed(s, "best")),
    ("best_sealed_single", "best sealed (single model)", lambda s, a: _sealed(s, "single")),
    ("gain_visible", "gain over start (visible)", lambda s, a: s.get("improvement_over_baseline")),
    ("gain_sealed", "gain over start (sealed)", lambda s, a: _gain_sealed(s)),
    ("completed", "experiments completed", lambda s, a: s.get("experiments_completed")),
    ("completed_planner", "completed, planner-proposed", lambda s, a: _planner_count(s)),
    ("exploit_share", "share proposed by the exploit engine", lambda s, a: _exploit_share(s)),
    ("failed", "failed", lambda s, a: s.get("experiments_failed")),
    ("unique", "unique hypotheses", lambda s, a: s.get("unique_hypotheses")),
    ("unique_planner", "unique hypotheses, planner-proposed", lambda s, a: s.get("unique_hypotheses_planner", s.get("unique_hypotheses"))),
    ("duplicates", "duplicates skipped", lambda s, a: s.get("duplicate_experiments")),
    ("cpu_hours", "CPU hours", lambda s, a: s.get("cpu_hours")),
    ("wall_min", "wall minutes", lambda s, a: (s.get("duration_s") or 0) / 60),
    ("tokens_k", "LLM tokens (k, in+out)", lambda s, a: _tokens(s)),
    ("cached_share", "cached input share", lambda s, a: _cached(s)),
    ("cost_worker", "worker $ (DeepSeek)", lambda s, a: (s.get("llm_usage", {}).get("worker") or {}).get("cost_usd")),
    ("cost_planner", "planner $ (CLI estimate)", lambda s, a: (s.get("llm_usage", {}).get("planner") or {}).get("cost_usd")),
    ("exp_per_hour", "experiments / hour", lambda s, a: s.get("compute_efficiency", {}).get("experiments_per_hour")),
    ("planner_exp_per_hour", "planner-proposed experiments / hour",
     lambda s, a: s.get("compute_efficiency", {}).get("planner_experiments_per_hour", s.get("compute_efficiency", {}).get("experiments_per_hour"))),
    ("gain_per_usd", "gain per $", lambda s, a: s.get("compute_efficiency", {}).get("gain_per_usd")),
    ("gain_per_cpu_h", "gain per CPU-hour", lambda s, a: s.get("compute_efficiency", {}).get("gain_per_cpu_hour")),
    ("utilisation", "worker utilisation", lambda s, a: (a or {}).get("worker_utilisation")),
    ("llm_share", "LLM share of worker time", lambda s, a: (a or {}).get("llm_share_of_worker_time")),
]


def _row(s, which):
    rows = s.get("generalization_query_only") or []
    if which == "best":
        return next((g for g in rows if g.get("kind") != "baseline"), None)
    if which == "single":
        return next((g for g in rows if g.get("kind") not in ("baseline", "ensemble")), None)
    return next((g for g in rows if g.get("kind") == "baseline"), None)


def _sealed(s, which):
    r = _row(s, which)
    return None if r is None else r.get("query_only_score")


def _visible(s, which):
    """Visible score of the headline row (the same model whose sealed score is reported, ensemble included)."""
    r = _row(s, which)
    return (s.get("best") or {}).get("score") if r is None else r.get("visible_score")


def _planner_count(s):
    if "experiments_completed_planner" in s:
        return s["experiments_completed_planner"]
    return s.get("experiments_completed")  # runs before the exploit engine existed: everything was planner-proposed


def _exploit_share(s):
    done = s.get("experiments_completed") or 0
    by = s.get("completed_by_proposer") or {}
    return None if not done else by.get("python:exploit", 0) / done


def _gain_sealed(s):
    b, base = _sealed(s, "best"), _sealed(s, "baseline")
    return None if b is None or base is None else b - base


def _tokens(s):
    u = s.get("llm_usage", {}).get("all") or {}
    return ((u.get("input_tokens") or 0) + (u.get("output_tokens") or 0)) / 1000


def _cached(s):
    u = s.get("llm_usage", {}).get("all") or {}
    return None if not u.get("input_tokens") else (u.get("cached_tokens") or 0) / u["input_tokens"]


def load_runs(dirs):
    runs = []
    for d in dirs:
        d = Path(d)
        if not (d / "summary.json").exists():
            continue
        s = json.loads((d / "summary.json").read_text())
        a = json.loads((d / "analysis.json").read_text()) if (d / "analysis.json").exists() else None
        cfg = json.loads((d / "config.json").read_text()) if (d / "config.json").exists() else {}
        runs.append({"dir": d.name, "arm": run_arm(cfg), "workers": s.get("workers") or cfg.get("run", {}).get("workers"),
                     "values": {k: f(s, a) for k, _, f in MEASURES}})
    return runs


def stats(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    m = sum(vals) / len(vals)
    sd = math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1)) if len(vals) > 1 else 0.0
    return {"mean": m, "sd": sd, "n": len(vals)}


def welch(a, b):
    """Two-sided Welch t-test p-value (None when either side has fewer than 2 runs)."""
    a, b = [v for v in a if v is not None], [v for v in b if v is not None]
    if len(a) < 2 or len(b) < 2:
        return None
    try:
        from scipy.stats import ttest_ind
        return float(ttest_ind(a, b, equal_var=False).pvalue)
    except Exception:
        return None


def fmt(st, digits=3):
    if st is None:
        return "–"
    s = f"{st['mean']:.{digits}f}"
    return s + (f" ± {st['sd']:.{digits}f}" if st["n"] > 1 else "")


def render(runs):
    groups = {}
    for r in runs:
        groups.setdefault((r["arm"], r["workers"]), []).append(r)
    keys = sorted(groups, key=lambda k: (k[0] != "scripted control (no LLM)", k[0], k[1] or 0))
    L = ["# Efficiency across worker counts", "",
         "Same dataset, split and time budget for every run; mean ± sd over repeats (n in the header). "
         "Gain is best model minus the starting model (best linear model on built-in features); "
         "sealed = query-only held-out perturbations. Planner dollars are the Claude CLI's usage estimate. "
         "'best' rows take the headline finalist (an ensemble when one was kept); 'single model' rows the best "
         "single model. Counts marked planner-proposed exclude the deterministic exploit engine's follow-ups, "
         "which run without an LLM whenever workers would otherwise idle (their share is listed).", "",
         "| measure | " + " | ".join(f"{k[0]}, {k[1]} workers (n={len(groups[k])})" for k in keys) + " |",
         "|---|" + "---|" * len(keys)]
    for key, label, _ in MEASURES:
        digits = 0 if key in ("completed", "completed_planner", "failed", "unique", "unique_planner", "duplicates") else (
            1 if key in ("wall_min", "tokens_k", "exp_per_hour", "planner_exp_per_hour") else 3)
        L.append(f"| {label} | " + " | ".join(fmt(stats([r["values"][key] for r in groups[k]]), digits) for k in keys) + " |")
    L += ["", "Runs: " + "; ".join(f"{k[0]}, {k[1]} workers: " + ", ".join(r["dir"] for r in groups[k]) for k in keys), ""]

    # noise: the control's spread and pairwise tests on the sealed gain between worker counts of the LLM arm
    L += ["## Is the ordering real?", ""]
    ctrl = [k for k in keys if k[0] == "scripted control (no LLM)"]
    for k in ctrl:
        st = stats([r["values"]["gain_sealed"] for r in groups[k]])
        stv = stats([r["values"]["gain_visible"] for r in groups[k]])
        if st:
            L.append(f"- No-LLM control ({st['n']} runs, the same scripted hypotheses every time; what varies is "
                     f"timing, scheduling order and the exploit follow-ups that order produces): sealed gain "
                     f"{fmt(st, 4)}, visible gain {fmt(stv, 4)}. Differences between worker counts smaller than about "
                     f"2 x this sd ({2 * st['sd']:.4f}) are within that noise.")
    llm = [k for k in keys if k[0] != "scripted control (no LLM)"]
    for i, ka in enumerate(llm):
        for kb in llm[i + 1:]:
            if ka[0] != kb[0]:
                continue
            a = [r["values"]["gain_sealed"] for r in groups[ka]]
            b = [r["values"]["gain_sealed"] for r in groups[kb]]
            sa, sb = stats(a), stats(b)
            if not sa or not sb:
                continue
            p = welch(a, b)
            diff = sb["mean"] - sa["mean"]
            verdict = ("not testable with one run per side" if p is None else
                       f"p = {p:.2f} (Welch), {'exceeds' if p < 0.05 else 'does not exceed'} run-to-run noise")
            L.append(f"- {ka[1]} vs {kb[1]} workers ({ka[0]}): sealed gain {fmt(sa, 4)} vs {fmt(sb, 4)}, "
                     f"difference {diff:+.4f}; {verdict}.")
    if llm:
        L.append("- A difference that does not exceed noise with two repeats needs more runs before any ordering is "
                 "claimed; each extra 20-minute repeat costs about the worker $ shown above in DeepSeek spend.")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--out", default=str(REPO_ROOT / "docs" / "results" / "scaling.md"))
    args = ap.parse_args()
    runs = load_runs(args.runs)
    if not runs:
        raise SystemExit("no run directory with summary.json among --runs")
    md = render(runs)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md)
    out.with_suffix(".json").write_text(json.dumps(runs, indent=1, default=str))
    print(md)
    print(f"written to {out}")


if __name__ == "__main__":
    main()
