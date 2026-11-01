#!/usr/bin/env python3
"""Block D, reading 5 (docs/PLAN_D_DISCOVERY_ADAMSON.md, "Readings"), descriptive: per run the number of experiments,
the largest planner state (block_d/<run>.check.txt; 24,000-character cut in discovery mode), the planner's and the
workers' cost and calls (summary.json["llm_usage"]), and whether planner.dry fired (summary.json["discovery"]
["dry_at_round"], and a "discovery_dry" line in controller.log). Mean and sample SD (ddof 1) over the runs. Reads those
files only: no label, no score, no fit. Written by the lab-code owner's Mac arm, 18 October 2026.
Usage: python -I block_d_reading5.py --out <prefix> <run dir>=<check.txt> ...   (writes <prefix>.json and <prefix>.md)
"""
import json
import re
import statistics
import sys
from pathlib import Path

args = sys.argv[1:]
out = Path(args[args.index("--out") + 1])
pairs = [a.split("=", 1) for i, a in enumerate(args) if a != "--out" and (i == 0 or args[i - 1] != "--out")]
EXP = ["experiments_proposed", "experiments_completed", "experiments_completed_planner", "experiments_failed",
       "experiments_rejected", "experiments_killed", "experiments_cancelled", "duplicate_experiments"]
runs = []
for run_dir, check in pairs:
    d = Path(run_dir)
    s = json.loads((d / "summary.json").read_text())
    u = s.get("llm_usage") or {}
    m = re.search(r"largest planner state (\d+) characters", Path(check).read_text())
    log = (d / "controller.log").read_text(errors="replace") if (d / "controller.log").exists() else ""
    r = {"run": d.name, "run_dir": str(d), "duration_s": s.get("duration_s"), "cpu_hours": s.get("cpu_hours")}
    for k in EXP:
        v = s.get(k)
        r[k] = len(v) if isinstance(v, (list, dict)) else v
    r.update({"largest_planner_state_chars": int(m.group(1)) if m else None,
              "planner_calls": (u.get("planner") or {}).get("calls"), "planner_cost_usd": (u.get("planner") or {}).get("cost_usd"),
              "worker_calls": (u.get("worker") or {}).get("calls"), "worker_cost_usd": (u.get("worker") or {}).get("cost_usd"),
              "all_cost_usd": (u.get("all") or {}).get("cost_usd"),
              "failed_calls": (u.get("all") or {}).get("failed_calls"),
              "planner_rounds": sum(v.get("rounds", 0) for v in ((s.get("planner") or {}).get("rounds") or {}).values()),
              "planner_mixed": (s.get("planner") or {}).get("mixed"),
              "dry_at_round": (s.get("discovery") or {}).get("dry_at_round"),
              "dry_fired": (s.get("discovery") or {}).get("dry_at_round") is not None,
              "controller_log_discovery_dry_lines": len(re.findall(r"discovery_dry", log))})
    runs.append(r)
NUM = EXP + ["duration_s", "cpu_hours", "largest_planner_state_chars", "planner_calls", "planner_cost_usd", "worker_calls",
             "worker_cost_usd", "all_cost_usd", "failed_calls", "planner_rounds"]
agg = {}
for k in NUM:
    v = [r[k] for r in runs if isinstance(r[k], (int, float)) and not isinstance(r[k], bool)]
    agg[k] = {"values": v, "mean": statistics.mean(v) if v else None, "sd": statistics.stdev(v) if len(v) > 1 else None}
out.with_suffix(".json").write_text(json.dumps({"reading": "block D reading 5 (descriptive)", "runs": runs,
                                                "aggregate_mean_sd_ddof1": agg}, indent=1, sort_keys=True) + "\n")


def f(x):
    return "n/a" if x is None else (f"{x:.4g}" if isinstance(x, float) else str(x))


L = ["# Block D, reading 5: experiments, planner state, cost and the dry rule (descriptive)", "",
     "From `summary.json` (`experiments_*`, `llm_usage`, `planner`, `discovery.dry_at_round`), `controller.log` and "
     "`block_d/<run>.check.txt`. Costs are the run's own accounting; the block's spend is the ledger's (reading of the "
     "chain).", "", "| | " + " | ".join(r["run"] for r in runs) + " | mean ± sd |", "|---|" + "---:|" * (len(runs) + 1)]
for k in NUM:
    L.append(f"| {k} | " + " | ".join(f(r[k]) for r in runs) + f" | {f(agg[k]['mean'])} ± {f(agg[k]['sd'])} |")
for k in ("planner_mixed", "dry_at_round", "dry_fired", "controller_log_discovery_dry_lines"):
    L.append(f"| {k} | " + " | ".join(f(r[k]) for r in runs) + " | |")
out.with_suffix(".md").write_text("\n".join(L) + "\n")
print("\n".join(L))
