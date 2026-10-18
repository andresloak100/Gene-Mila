#!/usr/bin/env python3
"""Mac checks of 17 Oct 2026 (claim #68), step 4: compare the adapter runs A, B and C (adapter_check.sh) with
(1) the export's saved predictions (<export>/reproduced/predictions.npz: delta, member_delta, perts, genes, members;
    sha256 5dc71266..., the export's predictions_sha256) and
(2) the original runs' saved per-member predictions (artifacts/<EXP>/predictions.npz at the frozen alpha, each checked
    against the saved_predictions_sha256 recorded in the export's summary.json), with the verification driver's rule:
    members bit for bit, ensemble within rtol = atol = 1e-6 of the float64 mean of the saved members cast to float32.
Rows are matched by condition id, columns by the gene order (required identical). Reads predictions only: no label,
no score, no fitting. Writes comparison.json and comparison.md into the results directory.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

RTOL = ATOL = 1e-6
EXPORT_QUERY_SHA = "f0feecfb48fdd94e1cca134713770796de4ba5c4319b07ef859d719c009c3c78"
EXPORT_PRED_SHA = "5dc712660fa7cd60fc9c201bad8c12410055db47f28d016d9ec8af4d511b485f"
MANIFEST_SHA = "225adc3079251f3cd17f16999b3bc92ab18ae20e9fcde9ee0617b8f350869b45"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def cmp(a: np.ndarray, b: np.ndarray) -> dict:
    assert a.shape == b.shape, (a.shape, b.shape)
    d = np.abs(a.astype(np.float64) - b.astype(np.float64))
    allowed = ATOL + RTOL * np.abs(b.astype(np.float64))
    return {"shape": list(a.shape), "array_equal": bool(np.array_equal(a, b)),
            "max_abs_difference": float(d.max()), "mean_abs_difference": float(d.mean()),
            "values_exceeding_tolerance": int((d > allowed).sum()),
            "within_rtol_atol_1e-6": bool(np.allclose(a, b, rtol=RTOL, atol=ATOL))}


def load(p: Path) -> dict:
    with np.load(p, allow_pickle=False) as z:
        return {k: z[k].copy() for k in z.files}


export, results = Path(sys.argv[1]), Path(sys.argv[2])
manifest = json.loads((export / "package" / "manifest.json").read_text())
summary = json.loads((export / "summary.json").read_text())
assert sha(export / "package" / "manifest.json") == MANIFEST_SHA
genes, anchors = manifest["genes"], manifest["anchor_perts"]
member_ids = [m["experiment_id"] for m in manifest["members"]]

saved_export_path = export / "reproduced" / "predictions.npz"
saved_export = load(saved_export_path)
assert [str(x) for x in saved_export["genes"]] == genes and [str(x) for x in saved_export["perts"]] == anchors
assert [str(x) for x in saved_export["members"]] == member_ids
export_row = {p: i for i, p in enumerate(anchors)}

# the original runs' saved member predictions at the frozen alpha (the verification driver's reading)
originals, original_files = [], []
for mc, m in zip(summary["member_comparisons"], manifest["members"]):
    assert mc["experiment_id"] == m["experiment_id"]
    path = Path(mc["run_directory"]) / "artifacts" / m["experiment_id"] / "predictions.npz"
    got = sha(path)
    z = load(path)
    hit = np.flatnonzero(np.asarray(z["alphas"], dtype=float) == m["alpha"])
    assert len(hit) == 1 and [str(x) for x in z["perts"]] == anchors
    originals.append(z["delta"][int(hit[0])])
    original_files.append({"experiment_id": m["experiment_id"], "path": str(path), "sha256": got,
                           "sha256_recorded_by_export": mc["saved_predictions_sha256"],
                           "sha256_matches": got == mc["saved_predictions_sha256"]})
originals = np.stack(originals)
original_ensemble = np.mean(originals.astype(np.float64), axis=0).astype(np.float32)

runs = {"A": ("predict_targets_out", "predict-targets", "single-gene anchors (condition id == symbol)"),
        "B": ("predict_pairs_out", "predict", "pair anchors, queries serialised as predict_targets() does"),
        "C": ("predict_all_anchors_out", "predict", "all anchors, query bytes = the export's original query")}
out = {"check": "frozen adapter check, docs/PLAN_R_FRESH_TEST.md section 6 (Mac checks of 17 Oct 2026, claim #68)",
       "export": str(export), "manifest_sha256": MANIFEST_SHA,
       "export_receipt": {"query_sha256": EXPORT_QUERY_SHA, "predictions_sha256": EXPORT_PRED_SHA,
                          "saved_predictions_file_sha256": sha(saved_export_path)},
       "export_summary_ensemble_max_abs_difference": summary["ensemble_comparison"]["max_abs_difference"],
       "rule": "members np.array_equal; ensemble within rtol = atol = 1e-6 (verification_driver.py)",
       "original_member_files": original_files, "runs": {}}
assembled_m = np.empty_like(saved_export["member_delta"]); assembled_e = np.empty_like(saved_export["delta"]); filled = set()
for key, (sub, mode, what) in runs.items():
    d = results / sub
    rec = json.loads((d / "receipt.json").read_text())
    z = load(d / "predictions.npz")
    perts = [str(x) for x in z["perts"]]
    assert [str(x) for x in z["genes"]] == genes, "gene order differs"
    assert [str(x) for x in z["members"]] == member_ids, "member order differs"
    assert perts == rec["condition_ids"] and rec["genes"] == genes
    rows = [export_row[p] for p in perts]
    r = {"mode": mode, "conditions": what, "n_conditions": len(perts), "n_genes": len(genes),
         "receipt": {k: rec[k] for k in ("manifest_sha256", "query_sha256", "predictions_sha256", "anchor_sha256")},
         "receipt_runtime_equals_export": rec["runtime"] == manifest["runtime"],
         "predictions_file_sha256": sha(d / "predictions.npz"),
         "predictions_sha256_matches_file": sha(d / "predictions.npz") == rec["predictions_sha256"],
         "vs_export_saved_predictions": {
             "members": {mid: cmp(z["member_delta"][i], saved_export["member_delta"][i][rows])
                         for i, mid in enumerate(member_ids)},
             "ensemble": cmp(z["delta"], saved_export["delta"][rows])},
         "vs_original_run_predictions": {
             "members": {mid: cmp(z["member_delta"][i], originals[i][rows]) for i, mid in enumerate(member_ids)},
             "ensemble_vs_float64_mean_of_saved_members": cmp(z["delta"], original_ensemble[rows])}}
    if (d / "queries.json").exists():
        r["queries_json_sha256"] = sha(d / "queries.json")
        r["queries_json_matches_receipt"] = r["queries_json_sha256"] == rec["query_sha256"]
    if key == "C":
        r["query_sha256_equals_export"] = rec["query_sha256"] == EXPORT_QUERY_SHA
        r["predictions_sha256_equals_export"] = rec["predictions_sha256"] == EXPORT_PRED_SHA
    if key in ("A", "B"):
        assembled_m[:, rows] = z["member_delta"]; assembled_e[rows] = z["delta"]; filled |= set(rows)
    ve, vo = r["vs_export_saved_predictions"], r["vs_original_run_predictions"]
    r["verdict"] = {
        "members_bit_exact_vs_export": all(c["array_equal"] for c in ve["members"].values()),
        "ensemble_bit_exact_vs_export": ve["ensemble"]["array_equal"],
        "members_bit_exact_vs_original_runs": all(c["array_equal"] for c in vo["members"].values()),
        "ensemble_within_1e-6_vs_original_runs": vo["ensemble_vs_float64_mean_of_saved_members"]["within_rtol_atol_1e-6"],
        "ensemble_max_abs_difference_vs_original_runs": vo["ensemble_vs_float64_mean_of_saved_members"]["max_abs_difference"]}
    r["passes"] = all(r["verdict"][k] for k in ("members_bit_exact_vs_export", "members_bit_exact_vs_original_runs",
                                                "ensemble_within_1e-6_vs_original_runs")) and r["receipt_runtime_equals_export"]
    out["runs"][key] = r
assert filled == set(range(len(anchors)))
out["A_plus_B_reassembled_in_anchor_order"] = {
    "members_vs_export": {mid: cmp(assembled_m[i], saved_export["member_delta"][i]) for i, mid in enumerate(member_ids)},
    "ensemble_vs_export": cmp(assembled_e, saved_export["delta"]),
    "ensemble_vs_original_runs": cmp(assembled_e, original_ensemble)}
out["gate_passes"] = all(r["passes"] for r in out["runs"].values()) and all(f["sha256_matches"] for f in original_files)
(results / "comparison.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")

L = ["# Frozen adapter check: B1 Norman export, 17 October 2026", "",
     f"Export `{export}` (package manifest sha256 `{MANIFEST_SHA}`). Rule: members `np.array_equal`; ensemble within "
     "rtol = atol = 1e-6 (the verification driver's rule). Rows matched by condition id; gene order identical (asserted).", "",
     f"**Gate: {'PASSES' if out['gate_passes'] else 'FAILS'}.**", "",
     "| run | mode | conditions | members bit-exact vs export saved | ensemble bit-exact vs export saved | members bit-exact vs original runs | ensemble max abs diff vs original runs (≤ 1e-6?) |",
     "|---|---|---:|---|---|---|---|"]
for key, r in out["runs"].items():
    v = r["verdict"]
    L.append(f"| {key} | `{r['mode']}` | {r['n_conditions']} ({r['conditions']}) | {v['members_bit_exact_vs_export']} | "
             f"{v['ensemble_bit_exact_vs_export']} | {v['members_bit_exact_vs_original_runs']} | "
             f"{v['ensemble_max_abs_difference_vs_original_runs']:.6g} ({v['ensemble_within_1e-6_vs_original_runs']}) |")
L += ["", "Per member, max abs difference (vs export saved / vs original run):", ""]
for key, r in out["runs"].items():
    parts = [f"{mid} {r['vs_export_saved_predictions']['members'][mid]['max_abs_difference']:.3g} / "
             f"{r['vs_original_run_predictions']['members'][mid]['max_abs_difference']:.3g}" for mid in member_ids]
    L.append(f"- {key}: " + "; ".join(parts) + f"; ensemble {r['vs_export_saved_predictions']['ensemble']['max_abs_difference']:.3g} / "
             f"{r['vs_original_run_predictions']['ensemble_vs_float64_mean_of_saved_members']['max_abs_difference']:.6g}")
L += ["", "| run | query_sha256 | predictions_sha256 |", "|---|---|---|",
      f"| export (13 Oct) | `{EXPORT_QUERY_SHA}` | `{EXPORT_PRED_SHA}` |"]
for key, r in out["runs"].items():
    L.append(f"| {key} | `{r['receipt']['query_sha256']}` | `{r['receipt']['predictions_sha256']}` |")
c = out["runs"]["C"]
L += ["", f"Run C's query bytes equal the export's (`query_sha256` equal: {c['query_sha256_equals_export']}); its "
      f"`predictions_sha256` equals the export's: {c['predictions_sha256_equals_export']}"
      + (" (the predictions file is byte-identical to the export's)." if c["predictions_sha256_equals_export"]
         else " (the arrays are compared above)."), "",
      "Runs A and B have their own query bytes (a subset of the anchors, A's condition ids named by symbol), so their "
      "query_sha256 and predictions_sha256 differ from the export's by construction; their arrays are compared above.", "",
      f"Original saved member files: " + "; ".join(f"{f['experiment_id']} sha256 matches the export's record: {f['sha256_matches']}" for f in original_files), "",
      f"A and B reassembled in anchor order vs the export's saved arrays: members bit-exact "
      f"{all(v['array_equal'] for v in out['A_plus_B_reassembled_in_anchor_order']['members_vs_export'].values())}; ensemble bit-exact "
      f"{out['A_plus_B_reassembled_in_anchor_order']['ensemble_vs_export']['array_equal']}."]
(results / "comparison.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
