"""Reading 4 metadata only; run after readings 1–3. No models or metrics are selected.

Usage: python docs/results/norman_f_collect_metadata.py /absolute/main/checkout
The output refuses replacement. Existing run databases are opened through the lab's
read-only snapshot helper; only recorded metadata is queried.
"""
from __future__ import annotations

import ast
from collections import Counter
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT)]
from feature_audit import open_db_readonly  # noqa: E402

COLUMNS = ["gene_span_kb", "n_transcripts", "n_exons", "transcript_length",
           "cds_length", "utr5_length", "utr3_length", "intron_length_kb",
           "gc_cds", "gc_utr3", "gc_promoter", "cpg_oe_promoter",
           "n_upstream_atg", "nearest_tss_kb", "n_tss_within_100kb"]
COLUMNS += [f"aa_{a}" for a in "ACDEFGHIKLMNPQRSTVWY"]
FIELDS = {"genes", "columns", "column_units", "loci", "bidirectional",
          "neighbours", "source", "unmatched"}


def source_inventory(path: Path) -> dict:
    source = path.read_text()
    tree = ast.parse(source)
    strings = {n.value for n in ast.walk(tree)
               if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    numeric = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Subscript) and any(
            isinstance(x, ast.Constant) and type(x.value) is int
            for x in ast.walk(n.slice)
        ):
            numeric.append({"line": n.lineno, "expression": ast.unparse(n)})
    mentioned = FIELDS.intersection(strings) | set(COLUMNS).intersection(strings)
    return {"feature": path.stem, "path": str(path.relative_to(ROOT)),
            "reads_replogle_literal": "replogle2022_k562" in source,
            "annotation_field_literals": sorted(FIELDS.intersection(strings)),
            "annotation_column_literals": [c for c in COLUMNS if c in strings],
            "numeric_subscript_contexts": numeric,
            "source_evidence": [{"line": i, "text": line.strip()}
                                for i, line in enumerate(source.splitlines(), 1)
                                if "gene_annotation" in line or any(k in line for k in mentioned)]}


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main_checkout = Path(sys.argv[1]).resolve()
    out = ROOT / "docs/results/norman_f_metadata.json"
    if out.exists():
        raise SystemExit(f"refusing to replace {out}")
    for required in ("norman_f_pooled_holm/pooled_holm.json",
                     "norman_f_arm_vs_b2/feature_compare.json",
                     *(f"norman_f_r{s}_sealed_reading.json" for s in (0, 2, 3))):
        if not (ROOT / "docs/results" / required).is_file():
            raise SystemExit(f"earlier reading missing: {required}")
    records = []
    for arm, prefix in (("f", "norman_ga_ds_addstart_w4"),
                        ("b2", "norman_ds_addstart_w4")):
        for seed in (0, 2, 3):
            run = main_checkout / "runs" / f"{prefix}_r{seed}"
            summary = json.loads((run / "summary.json").read_text())
            config = json.loads((run / "config.json").read_text())
            plugins = sorted((ROOT / "docs/results/norman_f_plugins" / f"r{seed}").glob("*.py")) if arm == "f" else []
            names = {p.stem for p in plugins}
            selected = set((summary.get("best") or {}).get("features") or [])
            with tempfile.TemporaryDirectory() as scratch:
                conn = open_db_readonly(run, Path(scratch))
                try:
                    rows = [dict(r) for r in conn.execute(
                        "SELECT experiment_id,status,kind,new_feature,feature_set_json "
                        "FROM experiments WHERE status!='reserved'")]
                    calls = [dict(r) for r in conn.execute(
                        "SELECT role,provider,model,COUNT(*) calls,"
                        "COALESCE(SUM(1-ok),0) failed_calls,COALESCE(SUM(cost_usd),0) cost_usd "
                        "FROM llm_calls GROUP BY role,provider,model")]
                    rounds = [dict(r) for r in conn.execute(
                        "SELECT provider,model,COUNT(*) successful_rounds,"
                        "COALESCE(SUM(n_proposed),0) proposed,COALESCE(SUM(n_queued),0) queued,"
                        "MAX(state_chars) max_state_chars FROM planner_rounds GROUP BY provider,model")]
                finally:
                    conn.close()
            proposed = [r for r in rows if r["kind"] not in ("baseline", "ensemble")]
            completed = [r for r in proposed if r["status"] == "completed"]
            def uses_annotation(r: dict) -> bool:
                return bool(names.intersection(json.loads(r["feature_set_json"] or "[]")))
            inventories = [source_inventory(p) for p in plugins]
            records.append({
                "arm": arm, "seed": seed, "run_dir": str(run),
                "code": summary["base_commit"], "duration_s": summary["duration_s"],
                "workers": config["run"]["workers"],
                "proposed": len(proposed), "completed": len(completed),
                "annotation_plugins": len(names),
                "selected_annotation_features": sorted(names & selected),
                "completed_with_annotation": sum(uses_annotation(r) for r in completed),
                "completed_annotation_creations": sum(r["new_feature"] in names for r in completed),
                "registered_with_annotation_by_status": dict(Counter(r["status"] for r in proposed if uses_annotation(r))),
                "annotation_only_plugins": [r["feature"] for r in inventories if not r["reads_replogle_literal"]],
                "annotation_and_replogle_plugins": [r["feature"] for r in inventories if r["reads_replogle_literal"]],
                "source_inventory": inventories, "llm_usage": summary["llm_usage"],
                "llm_calls_by_provider_role": calls, "successful_planner_rounds": rounds,
                "planner": summary.get("planner"),
            })
    result = {"method": "Recorded metadata only; no fit, scorer, model selection or protected labels.",
              "count_limits": "Direct source-reference/recorded-feature counts, not all attempted biological hypotheses or transitive usage.",
              "source_limits": "Literal key/column references and numeric subscript contexts are source evidence; dynamic access and runtime use are not inferred. Inspect the unchanged copied plugins.",
              "annotation_columns": COLUMNS, "runs": records}
    with out.open("x") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print(f"recorded metadata for {len(records)} runs -> {out}")


if __name__ == "__main__":
    main()
