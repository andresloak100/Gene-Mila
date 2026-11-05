#!/usr/bin/env python3
"""CellForge's Table 1 layout with our rows, on our split (lead's comment of 3 Nov on #51). Reads only committed
bridge reports, the run summaries' sealed scores and docs/results/cellforge_table1.json; scores nothing.

    python docs/results/cellforge_table1_ours/build.py --runs ~/Documents/Mila/Gene-Mila/gene-mila/runs
"""
import argparse, json, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RES = ROOT / "docs" / "results"
COLS = ["cellforge_mse", "cellforge_pcc", "cellforge_r2", "cellforge_mse_de", "cellforge_pcc_de", "cellforge_r2_de",
        "pearson_delta"]
HEAD = ["MSE ↓", "PCC ↑", "R² ↑", "MSE_DE ↓", "PCC_DE ↑", "R²_DE ↑", "pearson_delta ↑"]


def bridge(path):
    p = RES / path
    if not p.exists():
        return None
    m = json.loads(p.read_text())["cellforge"]["metrics"]
    return {k: m[k] for k in COLS}


def run_sel(runs, name, baseline=False):
    if name.startswith("T:"):  # block T runs live in this clone's runs/ (docs/PLAN_T_TABLE_AGENTS.md)
        runs, name = RUNS_T, name[2:]
    s = json.loads((runs / name / "summary.json").read_text())
    want = "EXP_0003" if baseline else s["best"]["experiment_id"]
    g = next((e for e in s["generalization_query_only"] if e["experiment_id"] == want), None)
    if g is None:  # the run did not score its selected model with CellForge's metrics: score_selected.py did, once
        rep = json.loads((Path(__file__).parent / f"selected_{name}.json").read_text())
        assert rep["experiment_id"] == want
        v = rep["cellforge"]["metrics"]
        return {k: v[k] for k in COLS}, f"{name}:{want} (score_selected.py)", s["split_id"]
    v = dict(g["comparable"]["val2"])
    v["pearson_delta"] = g["query_only_pearson_delta"]
    return {k: v[k] for k in COLS}, f"{name}:{want}", s["split_id"]


def agg(rows):
    rows = [r for r in rows if r is not None]
    if not rows:
        return None, 0
    if len(rows) == 1:
        return {k: (rows[0][k], None) for k in COLS}, 1
    return {k: (statistics.mean(r[k] for r in rows), statistics.stdev(r[k] for r in rows)) for k in COLS}, len(rows)


def fmt(v):
    if v is None:
        return "pending"
    m, sd = v
    return f"{m:.4f}" if sd is None else f"{m:.4f} ± {sd:.4f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--runs-t", default=str(ROOT / "runs"), help="where block T's runs are (default: this clone's runs/)")
    a_ = ap.parse_args()
    global RUNS_T
    runs, RUNS_T = Path(a_.runs).expanduser(), Path(a_.runs_t).expanduser()
    cf = json.loads((RES / "cellforge_table1.json").read_text())
    out = {"datasets": {}, "sources": {}}
    md = ["# CellForge's Table 1, our rows on our split", "",
          "Built by `build.py` beside this file from committed reports and the run summaries' sealed (val2) scores. "
          "Scored once for this table and nothing else: the Unperturbed rows (`unperturbed.py`) and three runs' "
          "selected models (`score_selected.py`); no setting was chosen on any of these scores. Our rows are on our split and bundle, CellForge's rows are copied from its paper "
          "(`docs/results/cellforge_table1.json`) and are **not comparable**: its split, preprocessing and metric scale "
          "cannot be reproduced (AGENTS.md). Both sealed sets are worn, so every row is descriptive. Agent rows are "
          "mean ± sample sd over three seeds; GEARS over seeds 0, 2, 3; the other rows are deterministic, one run. "
          "pearson_delta is the lab's primary metric (correlation of predicted and true change from control); "
          "CellForge's PCC is on absolute expression and is near 0.98 for every model.", ""]
    spec = {
        "adamson": {"bundle": "adamson_cf", "rows": [
            ("Unperturbed (control mean)", [bridge("cellforge_table1_ours/unperturbed_adamson.json")], "bridge"),
            ("Mean response (lab's start, OLS)", None, ("adamson_cf_g0_ds_w4_r0", True)),
            ("Linear, Ahlmann-Eltze 2025", [bridge("linear_ae_adamson.json")], "bridge"),
            ("GEARS, Roohani 2023", [bridge(f"gears_adamson_s{s}.json") for s in (0, 2, 3)], "bridge"),
            ("Gene-Mila agents, DeepSeek, clean tier 1 (block G0)", None,
             [f"adamson_cf_g0_ds_w4_r{r}" for r in (0, 2, 3)]),
            ("Gene-Mila agents, DeepSeek, clean tier 1 + tables (G1)", None,
             [f"adamson_cf_g1_ds_w4_r{r}" for r in (0, 2, 3)]),
            ("Gene-Mila agents, DeepSeek, clean tier 1 (block T0, code d53edff)", None,
             [f"T:adamson_cf_t0_ds_w4_r{r}" for r in (0, 2, 3)]),
            ("CellForge pipeline, run by us, DeepSeek v4-pro (block U, 1 run)", [bridge("cellforge_ours/cf_adamson_s42.json")], "bridge"),
        ]},
        "norman": {"bundle": "norman", "rows": [
            ("Unperturbed (control mean)", [bridge("cellforge_table1_ours/unperturbed_norman.json")], "bridge"),
            ("Additive singles (lab's start)", None, ("norman_g0_ds_w4_r0", True)),
            ("Linear, Ahlmann-Eltze 2025", [bridge("linear_ae_norman.json")], "bridge"),
            ("GEARS, Roohani 2023", [bridge(f"gears_norman_s{s}.json") for s in (0, 2, 3)], "bridge"),
            ("Gene-Mila agents, DeepSeek, clean tier 1 (block G0)", None,
             [f"norman_g0_ds_w4_r{r}" for r in (0, 2, 3)]),
            ("Gene-Mila agents, DeepSeek, clean tier 1 + tables (G1)", None,
             [f"norman_g1_ds_w4_r{r}" for r in (0, 2, 3)]),
            ("Gene-Mila agents, DeepSeek, clean tier 1 (block T0, code d53edff)", None,
             [f"T:norman_t0_ds_w4_r{r}" for r in (0, 2, 3)]),
            ("CellForge pipeline, run by us, DeepSeek v4-pro (block U, pending)",
             [bridge(f"cellforge_ours/cf_norman_s{s}.json") for s in (42, 0, 2)], "bridge"),
        ]},
    }
    for ds, sp in spec.items():
        rows_out, splits = {}, set()
        md += [f"## {cf['datasets'][ds]['title']}", "", "| Model | n | " + " | ".join(HEAD) + " |",
               "|---|---:|" + "---:|" * len(HEAD)]
        for label, vals, src in sp["rows"]:
            srcs = []
            if src != "bridge":
                names, base = (([src[0]], True) if isinstance(src, tuple) else (src, False))
                got = [run_sel(runs, n, base) for n in names]
                vals = [g[0] for g in got]
                srcs = [g[1] for g in got]
                assert len({g[2] for g in got}) == 1
                splits.add(got[0][2])
            a, n = agg(vals)
            rows_out[label] = {"n": n, "metrics": a and {k: {"mean": m, "sd": sd} for k, (m, sd) in a.items()},
                               "sources": srcs}
            md.append(f"| {label} | {n or '–'} | " + " | ".join(fmt(a and a[k]) for k in COLS) + " |")
        assert len(splits) == 1, f"{ds}: agent rows on different splits {splits}"
        md += ["", "CellForge's own rows (its paper, not comparable):", "", "| Model | " + " | ".join(HEAD[:6]) + " |",
               "|---|" + "---:|" * 6]
        for label, v in cf["datasets"][ds]["rows"].items():
            vv = v if isinstance(v[0], (int, float)) else [x[0] if isinstance(x, list) else x for x in v]
            md.append(f"| {label} | " + " | ".join(f"{x:.4f}" if isinstance(x, (int, float)) else str(x) for x in vv) + " |")
        md.append("")
        out["datasets"][ds] = rows_out
    md += ["## Srivatsan 2020 (sci-Plex 3, drugs)", "",
           "No row of ours. The lab models genetic perturbations only, and no Srivatsan bundle exists; building one "
           "is assigned to the Mila agent (`docs/BRIEF_MILA_AGENT.md` section 3).", "",
           "## Caveats", "",
           "- Adamson GEARS, linear and Unperturbed rows use the corrected three-source export "
           "(`~/cellforge_adamson_export_corrected_20261028`), which has 1,770 more controls and 10 more training cells "
           "than the bundle the agents saw. Norman's export follows the bundle's single source exactly.",
           "- The agent rows are each run's selected model; the block G0 and G1 bundles (`adamson_cf_clean`, "
           "`norman_clean`, with or without three tables) share the split of `adamson_cf` and `norman`.",
           "- Three agent runs (adamson_cf_g0 r3, adamson_cf_g1 r2, norman_g1 r2) had not stored CellForge's metrics "
           "for their selected model; `score_selected.py` scored that fixed model once, and its pearson_delta matches "
           "the published block G sealed reading.",
           "- Block T0 (`docs/PLAN_T_TABLE_AGENTS.md`) repeats block G0's design on code d53edff: six fresh DeepSeek "
           "runs, 20 minutes each, run on 3-4 Nov 2026 for this table; $4.34 by the shared ledger. Every planner stayed "
           "DeepSeek and no feature read a table (`genemila_t_logs/*.check.txt`).",
           "- The CellForge row is CellForge's own pipeline (gersteinlab/CellForge 6585ff9, unchanged) run by us on the same "
           "Adamson export, every agent DeepSeek v4-pro, its model's predictions scored once by the bridge like GEARS "
           "(`docs/PLAN_U_CELLFORGE.md`, receipts `cellforge_ours/cf_adamson_s42/`). Its model gave the same "
           "prediction, to five decimals, for every held-out perturbation: its output did not vary with its hashed perturbation token "
           "(own validation correlation 0.10 per cell), so the row equals the Unperturbed row to three decimals. One run; $1.86 by the block's proxy ledger.",
           "- The Norman CellForge row is pending. The block's first Norman run (`cellforge_ours/cf_norman_s42/`) finished its "
           "analysis, design and code generation ($0.78 by the proxy ledger); the agent's training script, a 4-layer transformer "
           "over 512 gene tokens trained on the CPU, then reached 47 GB of memory on the 24 GB Mac (macOS memory reports of "
           "5 Nov 2026, 03:10 and 03:13 UTC) and every block U process was killed with the session at 03:13 UTC before it "
           "finished. The row fills when the block is rerun under a memory cap.",
           "- GEARS falls back to the mean training change for held-out perturbations outside its gene graph; see "
           "each seed's receipt. On Norman no held-out perturbation needed the fallback (`../gears_norman/aggregate.md`).", ""]
    (Path(__file__).parent / "table.md").write_text("\n".join(md))
    (Path(__file__).parent / "table.json").write_text(json.dumps(out, indent=1))
    print("\n".join(md))


if __name__ == "__main__":
    main()
