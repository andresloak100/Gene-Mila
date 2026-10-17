#!/usr/bin/env python3
"""The two-stage feature-level reading of block F (docs/PLAN_F_GENOME_ANNOTATION.md, amendment of 2026-10-16 04:20 UTC;
corrected test of docs/ROADMAP.md D2 and D3), with no judgement left to the operator.

Stage 1 scores every gene_annotation plugin of the three runs with tools/feature_compare.py and no null. `select`
copies every add-one row with status ok (the plugin files, unchanged, into one directory per run: a feature name can
recur across runs) and prints m_total and the stage-2 replicate count, 999 or more (--null-reps). The family-wise
correction needs every member, so --k (a smaller rerun) is refused unless --partial is given with it, and `pool` then
marks the reading partial and finds nothing. Stage 2 scores those files again
with that many null replicates: the gene null for every row, the perturbation null for every row proportional to a
parent column, and the B null gains of each stored in the report.

`pool` then reads the stage-2 report over the union of the three sources' add-one rows: rows with one prediction hash
collapse to the first (status duplicate in the report, or the same hash across sources), and the max-gain step-down
(feature_compare.max_gain_step_down) runs once over every unique tested row for the gene null (p_fwer_pooled) and
once over the unique proportional rows for the perturbation null (p_fwer_pert_pooled). The permutations are shared
within one feature_compare call but not across calls, so pooling rows from separate calls is conservative (the maximum
over independent nulls is larger than over the shared one). A feature is found when every stage-1 row is in stage 2
(a step-down over a subset of the family is not a family-wise reading: the reading is marked partial and nothing is
found), it is not a duplicate, it was tested with at least 999 replicates, p_fwer_pooled <= 0.05,
p_fwer_pert_pooled <= 0.05 too when it is proportional, its gain exceeds max(2 SE_adj, 0.002) (the minimum effect of
interest, ROADMAP D3), and the tool's other criteria hold (M2 gain, mse_top not worse, every OOF report gaining, more
than one fold seed); it supports a tier-1 claim only when its source does not read replogle2022_k562. The
standardised coefficient's sign per report (coef_candidate_std) is copied into the table so the sign can be read on
the common parent.

    python tools/block_f_readings.py select --stage1 docs/results/norman_f_stage1/feature_compare.json \
        --plugins docs/results/norman_f_plugins --out docs/results/norman_f_top
    python tools/block_f_readings.py pool --stage1 ... --stage2 docs/results/norman_f_stage2/feature_compare.json \
        --plugins docs/results/norman_f_plugins --out docs/results/norman_f_pooled
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

from feature_compare import MIN_GAIN, MIN_REPS_FAMILY, P_MAX, max_gain_step_down, null_too_coarse  # noqa: E402

SOURCES = ("f_r0", "f_r2", "f_r3")
NULL_LINES = ("null p (Holm)", "null p (FWER)", "perturbation null", "proportional to a parent column",
              "null too coarse", "no null", "M1 gain not above the minimum effect")


def _rows(report: dict, statuses=("ok",)) -> list[dict]:
    """The gene_annotation add-one rows of the three runs with one of the statuses, in the report's order."""
    return [x for x in report["rows"] if x["source"] in SOURCES and x["kind"] == "add_one" and x["status"] in statuses]


def _z(row: dict) -> float:
    d = row["tiers"]["oof"]["delta"]["pearson_delta"]
    se = d.get("se_adj") or 0.0
    return float(d["mean_diff"]) / se if se > 0 else float("-inf")


def _other_failures(row: dict) -> list[str]:
    return [f for f in row.get("failed_criteria", []) if not f.startswith(NULL_LINES)]


def _plugin(plugins: Path, row: dict) -> Path:
    return plugins / row["source"].split("_")[1] / f"{row['feature']}.py"


def select(stage1: Path, plugins: Path, out: Path, k: int | None = None, null_reps: int = MIN_REPS_FAMILY,
           partial: bool = False) -> dict:
    rows = _rows(json.loads(stage1.read_text()))
    ranked = sorted(rows, key=lambda x: (-_z(x), x["feature"]))
    top = ranked if k is None else ranked[:k]
    if k is not None and len(top) < len(rows):
        msg = (f"--k {k} copies {len(top)} of {len(rows)} rows; the family-wise correction needs every member, so a "
               "pooled reading of this subset is partial and finds nothing")
        if not partial:
            raise SystemExit(msg + " (drop --k, or add --partial for a rerun that is not read)")
        print("warning: " + msg, file=sys.stderr)
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} exists and is not empty")
    for x in top:
        src = _plugin(plugins, x)
        if not src.exists():
            raise SystemExit(f"plugin file missing: {src}")
        dst = out / src.parent.name / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    m_total, reps = len(rows), max(MIN_REPS_FAMILY, null_reps)
    record = {"m_total": m_total, "null_reps": reps, "k": k,
              "selected": [{"source": x["source"], "feature": x["feature"], "z": _z(x)} for x in top]}
    (out / "selection.json").write_text(json.dumps(record, indent=1))
    print(f"m_total {m_total}; stage-2 null replicates {reps}; selected {len(top)} of {len(rows)} into {out}")
    return record


def _pooled(rows: list[dict], key: str, field: str) -> None:
    """The step-down over the rows' stored null gains of tiers.oof[key], written to row[field]."""
    nulls = [x["tiers"]["oof"][key] for x in rows]
    if any("gains" not in n for n in nulls):
        raise SystemExit("the stage-2 report stores no null gains: rerun stage 2 with the corrected feature_compare")
    for x, p in zip(rows, max_gain_step_down([n["observed"] for n in nulls], [n["gains"] for n in nulls])):
        x[field] = p


def pool(stage1: Path, stage2: Path, plugins: Path, out: Path) -> dict:
    s1 = _rows(json.loads(stage1.read_text()))
    s2 = {(x["source"], x["feature"]): x for x in _rows(json.loads(stage2.read_text()), ("ok", "duplicate"))}
    tested = {key: x for key, x in s2.items() if x["status"] == "ok" and x["tiers"]["oof"].get("null")}
    # one column counts once across the union: the report's duplicates, and the same hash across sources
    dup_of, first = {}, {}
    for key, x in s2.items():
        if x["status"] == "duplicate":
            dup_of[key] = x["reason"].split(":")[0].replace("duplicate of ", "")
        elif key in tested:
            h = x.get("prediction_hash")
            kept = first.setdefault(h, key) if h else key
            if kept != key:
                dup_of[key] = f"{kept[1]} ({kept[0]})"
    unique = [tested[key] for key in tested if key not in dup_of]
    # a stage-1 row absent from stage 2 (or failed there) leaves the step-down over a subset: not family-wise
    untested = [x for x in s1 if (x["source"], x["feature"]) not in tested
                and (x["source"], x["feature"]) not in dup_of]
    _pooled(unique, "null", "p_fwer_pooled")
    prop = [x for x in unique if x["tiers"]["oof"].get("null_pert")]
    _pooled(prop, "null_pert", "p_fwer_pert_pooled")
    reps = min((x["tiers"]["oof"]["null"]["reps"] for x in unique), default=0)
    need = null_too_coarse(len(unique), reps)
    rows = []
    for x in s1:
        key = (x["source"], x["feature"])
        src = tested.get(key, x)
        d = src["tiers"]["oof"]["delta"]["pearson_delta"]
        gain, se = float(d.get("mean_diff", 0.0)), float(d.get("se_adj") or 0.0)
        other = _other_failures(src)
        reads = "replogle2022_k562" in _plugin(plugins, x).read_text()
        proportional = bool(src.get("proportional"))
        p_fwer, p_pert = src.get("p_fwer_pooled"), src.get("p_fwer_pert_pooled")
        found = (not untested and key in tested and key not in dup_of and not need and not other and p_fwer is not None
                 and p_fwer <= P_MAX and (not proportional or (p_pert is not None and p_pert <= P_MAX))
                 and gain > max(2 * se, MIN_GAIN))
        rows.append({"source": key[0], "feature": key[1], "tested": key in tested, "duplicate_of": dup_of.get(key),
                     "p": src["tiers"]["oof"]["null"]["p"] if key in tested else None,
                     "p_fwer_pooled": p_fwer if key in tested and key not in dup_of else None,
                     "proportional": proportional, "parent_column": src.get("parent_column"),
                     "p_pert": (src["tiers"]["oof"]["null_pert"] or {}).get("p") if key in tested else None,
                     "p_fwer_pert_pooled": p_pert, "gain": gain, "se_adj": se,
                     "min_effect": max(2 * se, MIN_GAIN), "coef_sign": src.get("coef_candidate_sign"),
                     "coef_candidate_std": src.get("coef_candidate_std"), "z_stage1": _z(x),
                     "other_failed": other, "reads_replogle": reads, "found": found,
                     "found_tier1": found and not reads})
    record = {"family": len(unique), "stage1_rows": len(s1), "tested": len(tested), "duplicates": len(dup_of),
              "null_reps": reps, "null_too_coarse_need": need, "partial": bool(untested),
              "untested": [f"{x['feature']} ({x['source']})" for x in untested], "rows": rows}
    out.mkdir(parents=True, exist_ok=True)
    (out / "pooled_holm.json").write_text(json.dumps(record, indent=1))
    lines = ["# Block F feature-level reading: pooled max-gain step-down over every gene_annotation feature", "",
             f"Stage 1: {len(s1)} add-one rows with status ok; stage 2 tested {len(tested)} of them with {reps} null "
             f"replicates (p floor {1 / (reps + 1) if reps else 1:.4g}); {len(dup_of)} duplicates (one column under "
             f"several names) count once, so the family is {len(unique)} unique rows. The step-down runs once over "
             "the family for the gene null (p_fwer pooled) and once over its proportional rows for the perturbation "
             f"null. A feature is found when it is not a duplicate, p_fwer pooled <= {P_MAX}, the perturbation null's "
             f"p_fwer pooled <= {P_MAX} too when it is proportional to a parent column, its gain exceeds "
             f"max(2 SE_adj, {MIN_GAIN}) and the tool's other criteria hold; tier 1 only when its source does not read "
             "replogle2022_k562. An untested row is not found."
             + (f" The null is too coarse for this family (need {need} replicates): nothing is found." if need else "")
             + (f" Stage 2 omitted {len(untested)} of {len(s1)} stage-1 rows ({', '.join(record['untested'])}): the "
                "pooled p is over a subset of the family and is not a family-wise reading; nothing is found."
                if untested else ""),
             "",
             "| source | feature | z (stage 1) | gain ± SE_adj | min effect | null p | FWER p (pooled) | proportional "
             "to | pert null p | pert FWER p (pooled) | coef sign | duplicate of | other failed criteria | reads "
             "Replogle | found | tier 1 |",
             "|---|---|---:|---|---:|---:|---:|---|---:|---:|---|---|---|---|---|---|"]

    def num(v, nd="4g"):
        return "" if v is None else f"{v:.{nd}}"

    for r in sorted(rows, key=lambda r: (-(r["z_stage1"] if r["z_stage1"] != float("-inf") else -1e9), r["feature"])):
        lines.append(f"| {r['source']} | {r['feature']} | {r['z_stage1']:.2f} | {r['gain']:+.4f} ± {r['se_adj']:.4f} | "
                     f"{r['min_effect']:.4f} | {num(r['p'])} | {num(r['p_fwer_pooled'], '3g')} | "
                     f"{r['parent_column'] or ('no' if r['tested'] else '')} | {num(r['p_pert'])} | "
                     f"{num(r['p_fwer_pert_pooled'], '3g')} | {r['coef_sign'] or ''} | {r['duplicate_of'] or ''} | "
                     f"{'; '.join(r['other_failed']) or '-'} | {'yes' if r['reads_replogle'] else 'no'} | "
                     f"{'**yes**' if r['found'] else 'no'} | {'**yes**' if r['found_tier1'] else 'no'} |")
    (out / "pooled_holm.md").write_text("\n".join(lines) + "\n")
    found = [r["feature"] for r in rows if r["found"]]
    print(f"family {len(unique)} unique of {len(tested)} tested ({len(dup_of)} duplicates), {reps} replicates; "
          + (f"partial ({len(untested)} stage-1 rows untested); " if untested else "")
          + f"found {found}; tier 1 {[r['feature'] for r in rows if r['found_tier1']]}")
    return record


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("select")
    s.add_argument("--stage1", required=True)
    s.add_argument("--plugins", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--k", type=int, default=None, help="copy only the top k rows by z (default: every row; the "
                                                       "family-wise correction needs every member)")
    s.add_argument("--null-reps", type=int, default=MIN_REPS_FAMILY, help="stage-2 replicates, at least 999")
    s.add_argument("--partial", action="store_true", help="allow --k: a subset rerun that pool will not read as "
                                                          "a family-wise test")
    q = sub.add_parser("pool")
    q.add_argument("--stage1", required=True)
    q.add_argument("--stage2", required=True)
    q.add_argument("--plugins", required=True)
    q.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "select":
        select(Path(a.stage1), Path(a.plugins), Path(a.out), a.k, a.null_reps, a.partial)
    else:
        pool(Path(a.stage1), Path(a.stage2), Path(a.plugins), Path(a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
