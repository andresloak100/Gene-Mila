#!/usr/bin/env python3
"""Block D, reading 1 (docs/PLAN_D_DISCOVERY_ADAMSON.md, "Readings"): the discovery record per run, descriptive.

Per run, from runs/<run>/summary.json["discovery"], planner/discovery_rounds.json and planner/discovery_EXP_*.json:
rounds and counted rounds, hypotheses and how many named an unread input, the inputs proposed, the round the planner
went dry (or never), features scored for derivability, the new_input_features and derived_features lists with their
derived_r2; and from block_d/<run>.check.txt the counts of features reading each knowledge file and control statistic.
Then mean and sample SD (ddof 1) over the runs for every count. Reads those files only: no label, no score, no fit, no
private/ or splits.json. Written by the lab-code owner's Mac arm, 18 October 2026.
Usage: python -I block_d_reading1.py --out <prefix> <run dir>=<check.txt> ...   (writes <prefix>.json and <prefix>.md)
"""
import json
import re
import statistics
import sys
from pathlib import Path

args = sys.argv[1:]
out = Path(args[args.index("--out") + 1])
pairs = [a.split("=", 1) for i, a in enumerate(args) if a != "--out" and (i == 0 or args[i - 1] != "--out")]

COUNTS = ["rounds", "rounds_counted", "hypotheses", "hypotheses_naming_an_unread_input",
          "features_scored_for_derivability", "n_new_input_features", "n_below_threshold_naming_an_unread_input",
          "n_derived_features", "n_inputs_proposed",
          "n_evidence_files", "n_rounds_files"]
runs = []
for run_dir, check in pairs:
    d = Path(run_dir)
    s = json.loads((d / "summary.json").read_text())
    disc = s.get("discovery") or {}
    rounds_file = d / "planner" / "discovery_rounds.json"
    rounds = json.loads(rounds_file.read_text()) if rounds_file.exists() else None
    evidence = sorted(p.name for p in (d / "planner").glob("discovery_EXP_*.json"))
    reads = {}
    for line in Path(check).read_text().splitlines():
        m = re.match(r"features reading (\S+): (\d+) ", line)
        if m:
            reads[m.group(1)] = int(m.group(2))
    r = {"run": d.name, "run_dir": str(d), "check_file": str(check),
         "base_commit": s.get("base_commit"), "duration_s": s.get("duration_s"),
         "enabled": disc.get("enabled"), "rounds": disc.get("rounds"), "rounds_counted": disc.get("rounds_counted"),
         "hypotheses": disc.get("hypotheses"),
         "hypotheses_naming_an_unread_input": disc.get("hypotheses_naming_an_unread_input"),
         "inputs_proposed": disc.get("inputs_proposed") or [], "n_inputs_proposed": len(disc.get("inputs_proposed") or []),
         "dry_rule": disc.get("dry_rule"), "dry_at_round": disc.get("dry_at_round"),
         "features_scored_for_derivability": disc.get("features_scored_for_derivability"),
         "derived_r2_threshold": disc.get("derived_r2_threshold"),
         "new_input_features": disc.get("new_input_features") or [],
         "n_new_input_features": len(disc.get("new_input_features") or []),
         "n_below_threshold_naming_an_unread_input": sum(1 for x in disc.get("new_input_features") or [] if x.get("novel_inputs")),
         "derived_features": disc.get("derived_features") or [],
         "n_derived_features": len(disc.get("derived_features") or []),
         "evidence_files": evidence, "n_evidence_files": len(evidence),
         "summary_evidence_files_equal_dir": sorted(disc.get("evidence_files") or []) == evidence,
         "n_rounds_files": len(rounds) if isinstance(rounds, list) else None,
         "rounds_file_rounds": rounds if isinstance(rounds, list) else None,
         "features_reading": reads}
    runs.append(r)

agg = {}
for k in COUNTS:
    v = [r[k] for r in runs if isinstance(r[k], (int, float))]
    agg[k] = {"values": v, "mean": statistics.mean(v) if v else None,
              "sd": statistics.stdev(v) if len(v) > 1 else None}
read_keys = sorted({k for r in runs for k in r["features_reading"]})
agg_reads = {}
for k in read_keys:
    v = [r["features_reading"].get(k, 0) for r in runs]
    agg_reads[k] = {"values": v, "mean": statistics.mean(v), "sd": statistics.stdev(v) if len(v) > 1 else None}
res = {"reading": "block D reading 1: the discovery record per run (descriptive)", "runs": runs,
       "aggregate_mean_sd_ddof1": agg, "features_reading_mean_sd_ddof1": agg_reads}
out.with_suffix(".json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")


def f(x):
    return "n/a" if x is None else (f"{x:.3f}" if isinstance(x, float) else str(x))


L = ["# Block D, reading 1: the discovery record per run (descriptive)", "",
     "From `summary.json[\"discovery\"]`, `planner/discovery_rounds.json`, `planner/discovery_EXP_*.json` and the run's "
     "`block_d/<run>.check.txt`. No test, no score; counts only. `n_new_input_features` is the summary's "
     "`new_input_features` list: every feature scored for derivability with derived_r2 below the threshold, whether or not it "
     "named an unread input; `n_below_threshold_naming_an_unread_input` counts those that did.", "",
     "| | " + " | ".join(r["run"] for r in runs) + " | mean ± sd |", "|---|" + "---:|" * (len(runs) + 1)]
for k in COUNTS:
    L.append(f"| {k} | " + " | ".join(f(r[k]) for r in runs) + f" | {f(agg[k]['mean'])} ± {f(agg[k]['sd'])} |")
L.append("| dry_at_round | " + " | ".join(f(r["dry_at_round"]) for r in runs) + " | |")
L += ["", "Features reading each input (`.check.txt`):", "",
      "| input | " + " | ".join(r["run"] for r in runs) + " | mean ± sd |", "|---|" + "---:|" * (len(runs) + 1)]
for k in read_keys:
    L.append(f"| {k} | " + " | ".join(str(r["features_reading"].get(k, 0)) for r in runs)
             + f" | {f(agg_reads[k]['mean'])} ± {f(agg_reads[k]['sd'])} |")
for r in runs:
    L += ["", f"## {r['run']}", "", f"Code `{(r['base_commit'] or '')[:10]}`, {r['duration_s']} s. Inputs proposed: "
          + (", ".join(f"`{x}`" for x in r["inputs_proposed"]) or "none") + ".", "",
          f"`new_input_features` (the summary's name for every scored feature with derived_r2 below {r['derived_r2_threshold']}, "
          f"whether or not it named an unread input; {r['n_below_threshold_naming_an_unread_input']} of "
          f"{r['n_new_input_features']} did, shown with the input): "
          + (", ".join(f"`{x['feature']}` ({x['r2']}; {', '.join(x.get('novel_inputs') or []) or 'no novel input'})"
                       for x in r["new_input_features"]) or "none") + ".", "",
          "Derived features: " + (", ".join(f"`{x['feature']}` ({x['r2']})" for x in r["derived_features"]) or "none") + "."]
out.with_suffix(".md").write_text("\n".join(L) + "\n")
print("\n".join(L))
