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
    ("best_visible", "best visible (selection score)", lambda s, a: _visible(s, "best")),
    ("best_visible_single", "best visible (single model, selection score)", lambda s, a: (s.get("best") or {}).get("score")),
    ("best_val1", "best visible (validation set only)", lambda s, a: ((s.get("best") or {}).get("metrics") or {}).get("pearson_delta")),
    ("best_sealed", "best sealed pearson_delta", lambda s, a: _sealed(s, "best")),
    ("best_sealed_single", "best sealed pearson_delta (single model)", lambda s, a: _sealed(s, "single")),
    ("gain_visible", "gain over start (visible)", lambda s, a: _gain_visible(s)),
    ("gain_sealed", "gain over start (sealed pearson_delta)", lambda s, a: _gain_sealed(s)),
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
    ("cost_planner", "planner $ (API spend, or the Claude CLI's usage estimate)", lambda s, a: (s.get("llm_usage", {}).get("planner") or {}).get("cost_usd")),
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
    """Sealed pearson_delta of the row: the selection score itself under the default rule; a run under another
    rule (experiment.selection) reports it by name, so arms stay comparable on the same metric."""
    r = _row(s, which)
    return None if r is None else r.get("query_only_pearson_delta", r.get("query_only_score"))


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


def _gain_visible(s):
    """Visible gain on the pearson_delta scale: the run's own improvement when it selected by pearson_delta;
    for another selection rule, validation-set pearson_delta of best minus start when the summary carries both
    (summaries since the rule exists do), else None rather than a number on another scale."""
    if ((s.get("selection") or {}).get("rule") or "pearson_delta") == "pearson_delta":
        return s.get("improvement_over_baseline")
    b = ((s.get("best") or {}).get("metrics") or {}).get("pearson_delta")
    st = ((s.get("baseline") or {}).get("metrics") or {}).get("pearson_delta")
    return None if b is None or st is None else b - st


def _gain_sealed(s):
    b, base = _sealed(s, "best"), _sealed(s, "baseline")
    return None if b is None or base is None else b - base


def _is_control(arm: str) -> bool:
    return arm.startswith("scripted control (no LLM)")


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
        runs.append({"dir": d.name, "arm": run_arm(cfg, s), "workers": s.get("workers") or cfg.get("run", {}).get("workers"),
                     "code": (s.get("base_commit") or "")[:7], "values": {k: f(s, a) for k, _, f in MEASURES}})
    # runs on different code versions are different arms, however alike their configs
    if len({r["code"] for r in runs if r["code"]}) > 1:
        for r in runs:
            r["arm"] = f"{r['arm']} @ {r['code'] or 'unknown code'}"
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
    keys = sorted(groups, key=lambda k: (not _is_control(k[0]), k[0], k[1] or 0))
    L = ["# Efficiency across worker counts", "",
         "Same dataset, split and time budget for every run; mean ± sd over repeats (n in the header). "
         "Gain is best model minus the starting model (best linear model on built-in features); "
         "sealed = query-only held-out perturbations, always reported as pearson_delta whatever selection rule the run used. Planner dollars are real API spend for an API planner (DeepSeek) and the Claude CLI's usage estimate for a Claude planner. "
         "'best' rows take the headline finalist (an ensemble when one was kept); 'single model' rows the best "
         "single model. The selection score is what each run optimised: on code with cross-validated selection it "
         "averages the validation set and out-of-fold training perturbations, so it is lower than, and not "
         "comparable with, the validation-only score of earlier code; 'validation set only' is comparable across "
         "code versions, and a run that selected by another score shows its visible gain on the pearson_delta scale "
         "or not at all. Counts marked planner-proposed exclude the deterministic exploit engine's follow-ups, "
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
    ctrl = [k for k in keys if _is_control(k[0])]
    llm = [k for k in keys if not _is_control(k[0])]
    llm_wall = stats([r["values"]["wall_min"] for k in llm for r in groups[k]])
    for k in ctrl:
        st = stats([r["values"]["gain_sealed"] for r in groups[k]])
        stv = stats([r["values"]["gain_visible"] for r in groups[k]])
        wall = stats([r["values"]["wall_min"] for r in groups[k]])
        if not st:
            continue
        short = wall and llm_wall and wall["mean"] < 0.5 * llm_wall["mean"]
        name = f"{k[0]}, {k[1]} workers"
        if st["n"] > 1 and st["sd"] < 1e-9 and (stv is None or stv["sd"] < 1e-9):  # identical to rounding
            L.append(f"- {name} ({st['n']} run{'' if st['n'] == 1 else 's'}): identical results every time, sealed gain {st['mean']:.4f}, "
                     f"visible gain {stv['mean']:.4f}. The scripted recipe is deterministic on this dataset, so this "
                     "control is a fixed-recipe reference, not a noise reference.")
        elif short:
            L.append(f"- {name} ({st['n']} run{'' if st['n'] == 1 else 's'}, the same scripted hypotheses every time; what varies is timing, "
                     f"scheduling order and the exploit follow-ups that order produces): sealed gain {fmt(st, 4)}, "
                     f"visible gain {fmt(stv, 4)}. Its spread bounds the timing noise of a short deterministic run, "
                     "not that of the agent arms, whose own repeats are the yardstick below.")
        else:
            L.append(f"- {name} ({st['n']} run{'' if st['n'] == 1 else 's'}, the same scripted hypotheses every time; what varies is timing, "
                     f"scheduling order and the exploit follow-ups that order produces): sealed gain {fmt(st, 4)}, "
                     f"visible gain {fmt(stv, 4)}. This is the equal-time no-LLM reference: the agents' gain over it "
                     "is what the LLMs add to the search.")
        if short:
            L.append(f"- {name} ended after {wall['mean']:.1f} min on average (its hypotheses ran out) against "
                     f"{llm_wall['mean']:.1f} min for the agent arms, so it is not an equal-time arm: it shows what "
                     "the fixed template features give, not what a no-LLM search of the same length gives.")
    for k in ctrl:  # each control against the agent arms at its worker count: is the agents' gain over it established?
        st = stats([r["values"]["gain_sealed"] for r in groups[k]])
        peers = [(kb, stats([r["values"]["gain_sealed"] for r in groups[kb]])) for kb in llm if kb[1] == k[1]]
        peers = [(kb, s) for kb, s in peers if s]
        if not st or not peers:
            continue
        lo, hi = min(s["mean"] for _, s in peers), max(s["mean"] for _, s in peers)
        where = ("above every agent arm" if st["mean"] > hi else
                 "below every agent arm" if st["mean"] < lo else "within the agents' range")
        tail = "" if where == "below every agent arm" else (
            ", so the agents' gain over this control on sealed pearson_delta is not established")
        L.append(f"- {k[0]}, {k[1]} workers against the agent arms at {k[1]} workers: sealed gain {fmt(st, 4)} vs " +
                 ", ".join(f"{fmt(s, 4)} ({kb[0]})" for kb, s in peers) + f": {where}{tail}.")
    for i, ka in enumerate(llm):
        for kb in llm[i + 1:]:
            same_arm, same_workers = ka[0] == kb[0], ka[1] == kb[1]
            if not (same_arm or same_workers):
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
            # same arm across worker counts (the scaling question), or two arms at the same worker count
            # (code versions, or planners): both are pairwise tests on the sealed gain
            head = (f"{ka[1]} vs {kb[1]} workers ({ka[0]})" if same_arm else
                    f"{ka[0]} vs {kb[0]} ({ka[1]} workers)")
            ahead = "tie" if abs(diff) < 5e-5 else ("second ahead" if diff > 0 else "first ahead")
            L.append(f"- {head}: sealed gain {fmt(sa, 4)} vs {fmt(sb, 4)}, difference {diff:+.4f} "
                     f"(second minus first; {ahead}); {verdict}.")
    if llm:
        L.append("- A difference that does not exceed noise with two repeats needs more runs before any ordering is "
                 "claimed; each extra 20-minute repeat costs about the worker $ shown above in DeepSeek spend.")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", nargs="+", help="run directories (each with summary.json)")
    ap.add_argument("--from-json", help="re-render from a scaling.json written by an earlier call, when the run "
                                        "directories are not at hand (the .json twin is then left as it is)")
    ap.add_argument("--out", default=str(REPO_ROOT / "docs" / "results" / "scaling.md"))
    args = ap.parse_args()
    if bool(args.runs) == bool(args.from_json):
        ap.error("give --runs or --from-json, not both")
    runs = load_runs(args.runs) if args.runs else json.loads(Path(args.from_json).read_text())
    if not runs:
        raise SystemExit("no run directory with summary.json among --runs")
    md = render(runs)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md)
    if args.runs:
        out.with_suffix(".json").write_text(json.dumps(runs, indent=1, default=str))
    print(md)
    print(f"written to {out}")


if __name__ == "__main__":
    main()
