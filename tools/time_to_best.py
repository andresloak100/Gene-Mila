"""When did each finished run stop improving?

For every run directory, follow the running best *visible* score (the selection score each experiment was
scored by, `primary_score`) through the run in order of completion, starting from the run's starting model
(the best of its baseline fits), and report the minute of the last improvement, the share of the run's final
gain already reached at 25%, 50% and 75% of its time budget, the gain that arrived in the last half and the
last quarter (a run is "still rising" when the last quarter added at least 0.005), and how many experiments and
planner rounds came after the last improvement. Runs that ended before their final quarter are shown but not
counted; a run that lasted the budget and gained nothing late counts as not rising. This is the free
check behind "longer runs": if the gain of the runs that used their whole budget had largely arrived by the
midpoint, a longer budget alone is unlikely to help; if a meaningful part of it came in the last quarter, a
longer budget is the cheaper next test.

Visible data only: the tool reads each run's lab.db (experiments, planner rounds, the runs row) and its
config.json and summary.json for the arm label. The sealed set is never touched.

    python tools/time_to_best.py --runs runs/scale_* runs/newcode_* --out docs/results/time_to_best.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from statistics import median

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from genemila.benchmark.table import run_arm  # noqa: E402
from genemila.db import Database  # noqa: E402

CHECKPOINTS = (0.25, 0.5, 0.75)
LAST_QUARTER = 0.75
RISING_MIN_ABS = 0.005    # a run is still rising when its last quarter added at least this much


def analyse_run(run_dir: Path) -> dict | None:
    run_dir = Path(run_dir).resolve()
    if not (run_dir / "lab.db").exists():
        return None
    db = Database(run_dir / "lab.db")
    runs = db.query("SELECT * FROM runs ORDER BY started_at LIMIT 1")
    exps = db.query("SELECT experiment_id, kind, proposer, finished_at, primary_score FROM experiments "
                    "WHERE status='completed' AND primary_score IS NOT NULL AND finished_at IS NOT NULL "
                    "AND COALESCE(kind, '') != 'ensemble' ORDER BY finished_at, experiment_id")
    if not exps:
        return None
    run = runs[0] if runs else {}
    start_ts = run.get("started_at") or min(e["finished_at"] for e in exps)
    end_ts = run.get("deadline") or max(e["finished_at"] for e in exps)
    budget_min = max((end_ts - start_ts) / 60.0, 1e-9)
    rounds = [r["ts"] for r in db.query("SELECT ts FROM planner_rounds ORDER BY ts")]

    baselines = [e["primary_score"] for e in exps if e.get("kind") == "baseline"]
    others = [e for e in exps if e.get("kind") != "baseline"]
    # the starting model is the best baseline fit (the first baseline is usually "predict no change")
    start = max(baselines) if baselines else (others[0]["primary_score"] if others else None)
    best = start
    improvements: list[tuple[float, float]] = []  # (minute, new best)
    for e in others:
        if e["primary_score"] > best:
            best = e["primary_score"]
            improvements.append(((e["finished_at"] - start_ts) / 60.0, best))
    final = best
    gain = final - start
    last_min = improvements[-1][0] if improvements else 0.0
    last_ts = start_ts + last_min * 60.0

    def best_at(q: float) -> float:
        b = start
        for minute, score in improvements:
            if minute <= q * budget_min:
                b = score
        return b

    def share(q: float) -> float | None:
        return None if gain <= 0 else (best_at(q) - start) / gain

    gain_last_quarter = final - best_at(LAST_QUARTER)
    gain_last_half = final - best_at(0.5)
    # how long the run actually lasted: its recorded end, else its last experiment of any status
    ended = db.query("SELECT MAX(finished_at) AS t FROM experiments WHERE finished_at IS NOT NULL")
    end_ts_actual = run.get("finished_at") or (ended[0]["t"] if ended and ended[0]["t"] else None) or end_ts
    duration_min = (end_ts_actual - start_ts) / 60.0

    cfg = json.loads((run_dir / "config.json").read_text()) if (run_dir / "config.json").exists() else {}
    summary = json.loads((run_dir / "summary.json").read_text()) if (run_dir / "summary.json").exists() else {}
    code = (summary.get("base_commit") or "")[:7]
    arm = run_arm(cfg, summary) if cfg else "unknown arm"
    continuation = bool((cfg.get("run") or {}).get("continue_from"))  # warm start: its "gain" is the imported model
    return {
        "run_id": run_dir.name, "dir": str(run_dir), "code": code,
        "arm": f"{arm} @ {code}" if code else arm,  # runs on different code are different arms, as in the tables
        "workers": (cfg.get("run") or {}).get("workers", run.get("workers")),
        "budget_min": budget_min, "start": start, "final_best": final, "gain": gain,
        "n_improvements": len(improvements), "last_improvement_min": last_min,
        "share_at": {str(q): share(q) for q in CHECKPOINTS},
        "gain_last_quarter": gain_last_quarter, "gain_last_half": gain_last_half,
        "duration_min": duration_min, "continuation": continuation,
        "used_budget": duration_min >= LAST_QUARTER * budget_min,  # lasted into its final quarter
        "still_rising": gain_last_quarter >= RISING_MIN_ABS,
        "experiments_after": sum(1 for e in others if e["finished_at"] > last_ts),
        "planner_rounds_after": sum(1 for t in rounds if t > last_ts),
        "experiments": len(others),
    }


def _f(x, nd=3):
    return "–" if x is None else f"{x:.{nd}f}"


def _pct(x):
    return "–" if x is None else f"{100 * x:.0f}%"


def render(reports: list[dict]) -> str:
    L = ["# When did each run stop improving?", "",
         "Running best of the visible selection score, by minute of the run (experiments in order of completion, "
         "single models; the sealed set is never read). The start is the run's starting model, the best of its baseline "
         "fits. \"Share of final gain\" is how much of the run's final visible gain over the start had been reached at a "
         "quarter, half and three quarters of the time budget; the next two columns are the gain that arrived after the "
         f"midpoint and after three quarters. A run is \"still rising\" when the last quarter added at least {RISING_MIN_ABS} "
         "(the threshold is a judgement; the column before it shows the amount); a run that ended before its final "
         "quarter (the scripted control runs out of hypotheses in minutes) is not counted either way, nor is a warm-started "
         "run, whose gain is the model it imported.", "",
         "| run | arm | workers | budget (min) | start → best (visible) | share at 25% / 50% / 75% | gain after 50% | "
         "gain after 75% | last improvement (min) | experiments after it | planner rounds after it | still rising |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in reports:
        sh = r["share_at"]
        rising = ("continuation (its gain is the warm start)" if r["continuation"] else
                  ("yes" if r["still_rising"] else "no") if r["used_budget"] else "ended early")
        L.append(f"| {r['run_id']} | {r['arm']} | {r['workers']} | {r['budget_min']:.1f} | {_f(r['start'])} → {_f(r['final_best'])} "
                 f"| {_pct(sh['0.25'])} / {_pct(sh['0.5'])} / {_pct(sh['0.75'])} | {r['gain_last_half']:+.4f} | "
                 f"{r['gain_last_quarter']:+.4f} | {r['last_improvement_min']:.1f} | {r['experiments_after']} of {r['experiments']} "
                 f"| {r['planner_rounds_after']} | {rising} |")
    L += ["", "## By arm", ""]
    arms: dict[tuple, list[dict]] = {}
    for r in reports:
        arms.setdefault((r["arm"], r["workers"]), []).append(r)
    for (arm, workers), rs in sorted(arms.items(), key=lambda kv: (str(kv[0][0]), kv[0][1] or 0)):
        n = len(rs)
        used = [r for r in rs if r["used_budget"] and not r["continuation"]]
        head = f"- {arm}, {workers} workers ({n} run{'' if n == 1 else 's'}): "
        if all(r["continuation"] for r in rs):
            L.append(head + "warm-started from another campaign, so its gain is the imported model and it is not counted.")
            continue
        if not used:
            L.append(head + f"ended after {median(r['last_improvement_min'] for r in rs):.1f} min (median last improvement) "
                     f"of a {median(r['budget_min'] for r in rs):.0f}-min budget, so the budget was not the limit.")
            continue
        L.append(head + f"share of the final gain reached by the midpoint {median(r['share_at']['0.5'] or 0 for r in used):.0%} "
                 f"(median); gain after three quarters {median(r['gain_last_quarter'] for r in used):+.4f} (median); "
                 f"{sum(1 for r in used if r['still_rising'])} of {len(used)} still rising in the final quarter.")
    used = [r for r in reports if r["used_budget"] and not r["continuation"]]
    n_rising = sum(1 for r in used if r["still_rising"])
    L += ["", "## Reading", ""]
    if used:
        L.append(f"{n_rising} of {len(used)} runs that used their budget were still rising in the final quarter (median gain "
                 f"after three quarters {median(r['gain_last_quarter'] for r in used):+.4f}; median share of the gain reached "
                 f"by the midpoint {median(r['share_at']['0.5'] or 0 for r in used):.0%}). If that is a minority and the late "
                 "gains are small, the runs had plateaued before their deadline and a longer budget alone is unlikely to raise "
                 "the score; the lever is then a new feature family. If it is a majority, a longer budget is the cheaper next "
                 "test. Visible scores only: whether a late visible improvement survives on the sealed set is a separate "
                 "question the runs' summaries answer.")
    else:
        L.append("No run used its final quarter, so the budget was not what limited these runs.")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--runs", nargs="+", required=True, help="run directories (lab.db, config.json, summary.json)")
    ap.add_argument("--out", required=True, help="markdown report; a .json twin is written next to it")
    args = ap.parse_args(argv)
    reports = [r for r in (analyse_run(Path(d)) for d in args.runs) if r]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(reports))
    out.with_suffix(".json").write_text(json.dumps(reports, indent=1, default=str))
    print(render(reports))
    return 0


if __name__ == "__main__":
    sys.exit(main())
