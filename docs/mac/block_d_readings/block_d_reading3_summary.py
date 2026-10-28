#!/usr/bin/env python3
"""Block D, reading 3 (docs/PLAN_D_DISCOVERY_ADAMSON.md, "Readings"), descriptive: arm against arm on the development
tier. Reads the one feature_compare.py call that rebuilt the nine selected models (d1_r{0,2,3}, g1_r{0,2,3},
g0_r{0,2,3}) under the same parent (the built-in start) and fold seeds, and reports each run's (set) row (OOF M1 to
M7 and M12 as emitted, delta M1 +- SE_adj over the start, wins) and per arm the mean and sample SD (ddof 1) over its
runs, in the form of block G's adamson_cf_g_arm_summary. No test; no difference is claimed inside either arm's spread;
OOF is not held out for any arm. Written by the lab-code owner's Mac arm, 18 October 2026.
Usage: python -I block_d_reading3_summary.py <feature_compare.json> <out prefix>
"""
import json
import statistics
import sys
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
r = json.loads(src.read_text())
parent = r["parent"]["tiers"]["oof"]["metrics"]
rows = {x["source"]: x for x in r["rows"] if x["kind"] == "set"}
runs = []
for name in ["d1_r0", "d1_r2", "d1_r3", "g1_r0", "g1_r2", "g1_r3", "g0_r0", "g0_r2", "g0_r3"]:
    x = rows.get(name)
    if x is None or x.get("status") != "ok":
        runs.append({"source": name, "status": None if x is None else x.get("status"),
                     "reason": None if x is None else x.get("reason")})
        continue
    t = x["tiers"]["oof"]
    d = t["delta"]["pearson_delta"]
    runs.append({"source": name, "arm": name.split("_")[0], "status": "ok", "n_columns": x.get("n_columns"),
                 "features": x.get("features"), "metrics": t["metrics"], "M1": t["metrics"]["pearson_delta"],
                 "delta_M1": d["mean_diff"], "se_adj": d["se_adj"], "wins": d["wins_a"], "n": d["n"],
                 "verdict_adj": d["verdict_adj"], "report_deltas": t.get("report_deltas")})
arms = {}
for arm in ("d1", "g1", "g0"):
    ok = [x for x in runs if x.get("arm") == arm]
    m = {}
    for key in sorted({k for x in ok for k in x["metrics"]}):
        v = [x["metrics"][key] for x in ok if key in x["metrics"]]
        m[key] = {"mean": statistics.mean(v), "sd": statistics.stdev(v) if len(v) > 1 else None, "n": len(v)}
    dv = [x["delta_M1"] for x in ok]
    arms[arm] = {"n_runs": len(ok), "metrics": m,
                 "delta_M1": {"mean": statistics.mean(dv) if dv else None, "sd": statistics.stdev(dv) if len(dv) > 1 else None}}
res = {"reading": "block D reading 3: arm against arm, development tier (descriptive)", "source": str(src),
       "parent": {"source": r["parent"].get("source"), "features": r["parent"].get("features"), "oof_metrics": parent},
       "settings": r.get("settings"), "split_id": r.get("split_id"), "lab_commit": r.get("lab_commit"),
       "caveats": r.get("caveats"), "runs": runs, "arms": arms}
out.with_suffix(".json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")


def f(x, n=9):
    return "n/a" if x is None else f"{x:.{n}f}"


L = ["# Block D, reading 3: D1 against G1 and G0 on the development tier (descriptive)", "",
     f"One `tools/feature_compare.py --null-reps 0` call rebuilt the nine selected models under the same parent (the "
     f"built-in start: M1 {parent['pearson_delta']:.9f}) and fold seeds, on `data/adamson_cf_clean_tables` (split "
     f"`{r.get('split_id')}`). OOF is not held out for any arm: every system selected on these labels. No test; no "
     "difference is claimed inside either arm's spread. D1 differs from G1 by discovery mode and PR #71's code; G0 is "
     "the same bundle without the three tables (context).", "",
     "|arm|n runs|M1 mean ± sample SD|delta M1 versus parent mean ± sample SD|", "|---|---:|---|---|"]
for arm in ("d1", "g1", "g0"):
    a = arms[arm]
    L.append(f"|{arm}|{a['n_runs']}|{f(a['metrics'].get('pearson_delta', {}).get('mean'))} ± "
             f"{f(a['metrics'].get('pearson_delta', {}).get('sd'))}|{f(a['delta_M1']['mean'])} ± {f(a['delta_M1']['sd'])}|")
L += ["", "|source|columns|M1|delta M1|SE_adj|wins / n|", "|---|---:|---:|---:|---:|---|"]
for x in runs:
    if x.get("status") != "ok":
        L.append(f"|{x['source']}|status {x.get('status')}: {x.get('reason')}| | | | |")
        continue
    L.append(f"|{x['source']}|{x['n_columns']}|{f(x['M1'])}|{x['delta_M1']:+.9f}|{f(x['se_adj'])}|{x['wins']} / {x['n']}|")
L += ["", "Every emitted OOF metric per run, and per arm its mean and sample SD, is in the JSON twin.", ""]
L += [f"- {c}" for c in (r.get("caveats") or [])]
out.with_suffix(".md").write_text("\n".join(L) + "\n")
print("\n".join(L))
