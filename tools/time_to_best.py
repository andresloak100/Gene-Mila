"""When did each finished run stop improving?

For every run directory, follow the running best *visible* score (the selection score each experiment was
scored by, `primary_score`) through the run in order of completion and report the minute of the last
improvement, the share of the run's final gain already reached at 25%, 50% and 75% of its time budget, and how
many experiments and planner rounds came after the last improvement. This is the free check behind "longer
runs": if most runs went flat long before their deadline, a longer budget alone is unlikely to help; if they
were still improving in the last quarter, it is the cheaper next test.

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
LAST_QUARTER = 0.75  # an improvement after this share of the budget counts as "still rising"


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
    start = run.get("started_at") or min(e["finished_at"] for e in exps)
    end = run.get("deadline") or max(e["finished_at"] for e in exps)
    budget_min = max((end - start) / 60.0, 1e-9)
    rounds = [r["ts"] for r in db.query("SELECT ts FROM planner_rounds ORDER BY ts")]

    base = next((e["primary_score"] for e in exps if e.get("kind") == "baseline"), None)
    best = base if base is not None else -float("inf")
    improvements: list[tuple[float, float]] = []  # (minute, new best)
    for e in exps:
        if e.get("kind") == "baseline":
            continue
        if e["primary_score"] > best:
            best = e["primary_score"]
            improvements.append(((e["finished_at"] - start) / 60.0, best))
    if base is None and improvements:
        base = improvements[0][1]
    final = best if best > -float("inf") else base
    last_min = improvements[-1][0] if improvements else 0.0
    last_ts = start + last_min * 60.0
    gain = (final - base) if (final is not None and base is not None) else None

    def share(q: float) -> float | None:
        if not gain:
            return None
        best_q = base
        for minute, score in improvements:
            if minute <= q * budget_min:
                best_q = score
        return (best_q - base) / gain

    cfg = json.loads((run_dir / "config.json").read_text()) if (run_dir / "config.json").exists() else {}
    summary = json.loads((run_dir / "summary.json").read_text()) if (run_dir / "summary.json").exists() else {}
    code = (summary.get("base_commit") or "")[:7]
    arm = run_arm(cfg, summary) if cfg else "unknown arm"
    return {
        "run_id": run_dir.name, "dir": str(run_dir), "code": code,
        "arm": f"{arm} @ {code}" if code else arm,  # runs on different code are different arms, as in the tables
        "workers": (cfg.get("run") or {}).get("workers", run.get("workers")),
        "budget_min": budget_min, "start": base, "final_best": final, "gain": gain,
        "n_improvements": len(improvements), "last_improvement_min": last_min,
        "still_rising": bool(improvements) and last_min > LAST_QUARTER * budget_min,
        "share_at": {str(q): share(q) for q in CHECKPOINTS},
        "experiments_after": sum(1 for e in exps if e.get("kind") != "baseline" and e["finished_at"] > last_ts),
        "planner_rounds_after": sum(1 for t in rounds if t > last_ts),
        "experiments": sum(1 for e in exps if e.get("kind") != "baseline"),
    }


def _f(x, nd=3):
    return "–" if x is None else f"{x:.{nd}f}"


def _pct(x):
    return "–" if x is None else f"{100 * x:.0f}%"


def render(reports: list[dict]) -> str:
    L = ["# When did each run stop improving?", "",
         "Running best of the visible selection score, by minute of the run (experiments in order of completion; "
         "the sealed set is never read). \"Share of final gain\" is how much of the run's final visible gain over "
         "its starting model had been reached at a quarter, half and three quarters of the time budget. A run is "
         "\"still rising\" when its last improvement came in the final quarter.", "",
         "| run | arm | workers | budget (min) | start → best (visible) | share at 25% / 50% / 75% | last improvement (min) "
         "| experiments after it | planner rounds after it | still rising |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r in reports:
        sh = r["share_at"]
        L.append(f"| {r['run_id']} | {r['arm']} | {r['workers']} | {r['budget_min']:.1f} | {_f(r['start'])} → {_f(r['final_best'])} "
                 f"| {_pct(sh['0.25'])} / {_pct(sh['0.5'])} / {_pct(sh['0.75'])} | {r['last_improvement_min']:.1f} "
                 f"| {r['experiments_after']} of {r['experiments']} | {r['planner_rounds_after']} | {'yes' if r['still_rising'] else 'no'} |")
    L += ["", "## By arm", ""]
    arms: dict[tuple, list[dict]] = {}
    for r in reports:
        arms.setdefault((r["arm"], r["workers"]), []).append(r)
    for (arm, workers), rs in sorted(arms.items(), key=lambda kv: (str(kv[0][0]), kv[0][1] or 0)):
        rising = sum(1 for r in rs if r["still_rising"])
        L.append(f"- {arm}, {workers} workers ({len(rs)} run{'' if len(rs) == 1 else 's'}): last improvement at "
                 f"{median(r['last_improvement_min'] for r in rs):.1f} min (median) of a {median(r['budget_min'] for r in rs):.0f}-min budget; "
                 f"{rising} of {len(rs)} still rising in the final quarter.")
    n_rising = sum(1 for r in reports if r["still_rising"])
    L += ["", "## Reading", "",
          f"{n_rising} of {len(reports)} runs were still improving in their final quarter. If that is a minority, the runs "
          "went flat before their deadline and a longer budget alone is unlikely to raise the score; the lever is then a "
          "new feature family. If it is a majority, a longer budget is the cheaper next test. Visible scores only: whether "
          "a late visible improvement survives on the sealed set is a separate question the runs' summaries answer."]
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
