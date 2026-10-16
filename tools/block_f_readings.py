#!/usr/bin/env python3
"""The two-stage feature-level reading of block F (docs/PLAN_F_GENOME_ANNOTATION.md, amendment of 2026-10-16 04:20 UTC),
with no judgement left to the operator.

Stage 1 scores every gene_annotation plugin of the three runs with tools/feature_compare.py and no null. `select`
then ranks those add-one rows by their paired out-of-fold gain over the parent divided by the overlap-robust standard
error (ties by name), copies the top k plugin files, unchanged, into one directory per run (a feature name can
recur across runs, so one directory per run keeps the files apart), and prints m_total (every add-one row with status
ok) and the replicate count 20 * m_total - 1 for stage 2. Stage 2 scores those files again with that many null
replicates. `pool` then applies one Holm procedure of size m_total to the raw null p of the tested rows, with p = 1 for
every untested row, which can only make rejection harder than the pre-registered pooled rule; a feature is found when
its pooled Holm p is at most 0.05 and the tool's other criteria hold, and supports a tier-1 claim only when its source
does not read replogle2022_k562.

    python tools/block_f_readings.py select --stage1 docs/results/norman_f_stage1/feature_compare.json \
        --plugins docs/results/norman_f_plugins --out docs/results/norman_f_top --k 20
    python tools/block_f_readings.py pool --stage1 ... --stage2 docs/results/norman_f_stage2/feature_compare.json \
        --plugins docs/results/norman_f_plugins --out docs/results/norman_f_pooled_holm
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

from feature_compare import holm  # noqa: E402

SOURCES = ("f_r0", "f_r2", "f_r3")
NULL_LINES = ("null p (Holm)", "null too coarse", "no null")


def _rows(report: dict) -> list[dict]:
    """The gene_annotation add-one rows of the three runs with status ok, in the report's order."""
    return [x for x in report["rows"] if x["source"] in SOURCES and x["kind"] == "add_one" and x["status"] == "ok"]


def _z(row: dict) -> float:
    d = row["tiers"]["oof"]["delta"]["pearson_delta"]
    se = d.get("se_adj") or 0.0
    return float(d["mean_diff"]) / se if se > 0 else float("-inf")


def _other_failures(row: dict) -> list[str]:
    return [f for f in row.get("failed_criteria", []) if not f.startswith(NULL_LINES)]


def _plugin(plugins: Path, row: dict) -> Path:
    return plugins / row["source"].split("_")[1] / f"{row['feature']}.py"


def select(stage1: Path, plugins: Path, out: Path, k: int) -> dict:
    rows = _rows(json.loads(stage1.read_text()))
    ranked = sorted(rows, key=lambda x: (-_z(x), x["feature"]))
    top = ranked[:k]
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} exists and is not empty")
    for x in top:
        src = _plugin(plugins, x)
        if not src.exists():
            raise SystemExit(f"plugin file missing: {src}")
        dst = out / src.parent.name / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    m_total, reps = len(rows), max(199, 20 * len(rows) - 1)
    record = {"m_total": m_total, "null_reps": reps, "k": k,
              "selected": [{"source": x["source"], "feature": x["feature"], "z": _z(x)} for x in top]}
    (out / "selection.json").write_text(json.dumps(record, indent=1))
    print(f"m_total {m_total}; stage-2 null replicates {reps}; selected {len(top)} of {len(rows)} into {out}")
    return record


def pool(stage1: Path, stage2: Path, plugins: Path, out: Path) -> dict:
    s1 = _rows(json.loads(stage1.read_text()))
    s2 = {(x["source"], x["feature"]): x for x in _rows(json.loads(stage2.read_text()))}
    tested = {key: x for key, x in s2.items() if x["tiers"]["oof"].get("null")}
    keys = [(x["source"], x["feature"]) for x in s1]
    raw = [tested[key]["tiers"]["oof"]["null"]["p"] if key in tested else 1.0 for key in keys]
    adj = holm(raw)
    rows = []
    for key, x, p_raw, p_adj in zip(keys, s1, raw, adj):
        src = tested.get(key, x)
        other = _other_failures(src)
        reads = "replogle2022_k562" in _plugin(plugins, x).read_text()
        found = key in tested and not other and p_adj <= 0.05
        rows.append({"source": key[0], "feature": key[1], "tested": key in tested, "p": p_raw if key in tested else None,
                     "p_holm_pooled": p_adj, "z_stage1": _z(x), "other_failed": other, "reads_replogle": reads,
                     "found": found, "found_tier1": found and not reads})
    record = {"family": len(keys), "tested": len(tested), "rows": rows}
    out.mkdir(parents=True, exist_ok=True)
    (out / "pooled_holm.json").write_text(json.dumps(record, indent=1))
    lines = ["# Block F feature-level reading: pooled Holm over every gene_annotation feature", "",
             f"Family m_total = {len(keys)} add-one rows (status ok, stage 1); {len(tested)} tested against the null "
             f"(stage 2); untested rows enter Holm at p = 1. A feature is found when its pooled Holm p <= 0.05 and the "
             f"tool's other criteria hold; tier 1 only when its source does not read replogle2022_k562.", "",
             "| source | feature | z (stage 1) | null p | Holm p (pooled) | other failed criteria | reads Replogle | found | tier 1 |",
             "|---|---|---:|---:|---:|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (-(r["z_stage1"] if r["z_stage1"] != float("-inf") else -1e9), r["feature"])):
        lines.append(f"| {r['source']} | {r['feature']} | {r['z_stage1']:.2f} | "
                     f"{'' if r['p'] is None else f'{r['p']:.4g}'} | {r['p_holm_pooled']:.3g} | "
                     f"{'; '.join(r['other_failed']) or '-'} | {'yes' if r['reads_replogle'] else 'no'} | "
                     f"{'**yes**' if r['found'] else 'no'} | {'**yes**' if r['found_tier1'] else 'no'} |")
    (out / "pooled_holm.md").write_text("\n".join(lines) + "\n")
    found = [r["feature"] for r in rows if r["found"]]
    print(f"family {len(keys)}, tested {len(tested)}; found {found}; tier 1 {[r['feature'] for r in rows if r['found_tier1']]}")
    return record


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("select")
    s.add_argument("--stage1", required=True)
    s.add_argument("--plugins", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--k", type=int, default=20)
    q = sub.add_parser("pool")
    q.add_argument("--stage1", required=True)
    q.add_argument("--stage2", required=True)
    q.add_argument("--plugins", required=True)
    q.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "select":
        select(Path(a.stage1), Path(a.plugins), Path(a.out), a.k)
    else:
        pool(Path(a.stage1), Path(a.stage2), Path(a.plugins), Path(a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
