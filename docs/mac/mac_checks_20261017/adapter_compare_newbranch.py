#!/usr/bin/env python3
"""Mac checks of 17 Oct 2026 (claim #68), step 4, EXTRA diagnostic (not part of the PLAN_R section 6 gate): compare
run D (adapter_newbranch.sh: the 31 single-gene anchors under renamed ids "<SYMBOL>__new", so predict_ensemble takes
its new-condition branch) with the export's saved predictions of the same 31 anchors (<export>/reproduced/predictions.npz)
and with run A (predict_targets_out, the anchor branch). Rows matched by symbol ("<SYMBOL>__new" -> "<SYMBOL>"); gene
and member orders asserted identical. Same rule as adapter_compare.py: members bit for bit (np.array_equal), and
rtol = atol = 1e-6 reported beside it. Reads predictions only: no label, no score, no fitting. Writes
comparison_newbranch.json and comparison_newbranch.md into the results directory. Written by the 02:48 UTC session.
Usage: python -I adapter_compare_newbranch.py <export dir> <results dir>
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

RTOL = ATOL = 1e-6
MANIFEST_SHA = "225adc3079251f3cd17f16999b3bc92ab18ae20e9fcde9ee0617b8f350869b45"
SUFFIX = "__new"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(p: Path) -> dict:
    with np.load(p, allow_pickle=False) as z:
        return {k: z[k].copy() for k in z.files}


def cmp(a: np.ndarray, b: np.ndarray) -> dict:
    assert a.shape == b.shape, (a.shape, b.shape)
    d = np.abs(a.astype(np.float64) - b.astype(np.float64))
    allowed = ATOL + RTOL * np.abs(b.astype(np.float64))
    return {"shape": list(a.shape), "array_equal": bool(np.array_equal(a, b)),
            "max_abs_difference": float(d.max()), "mean_abs_difference": float(d.mean()),
            "values_differing": int((d > 0).sum()), "values_exceeding_tolerance": int((d > allowed).sum()),
            "within_rtol_atol_1e-6": bool(np.allclose(a, b, rtol=RTOL, atol=ATOL))}


export, results = Path(sys.argv[1]), Path(sys.argv[2])
manifest = json.loads((export / "package" / "manifest.json").read_text())
assert sha(export / "package" / "manifest.json") == MANIFEST_SHA
genes, anchors = manifest["genes"], manifest["anchor_perts"]
member_ids = [m["experiment_id"] for m in manifest["members"]]
saved = load(export / "reproduced" / "predictions.npz")
assert [str(x) for x in saved["genes"]] == genes and [str(x) for x in saved["perts"]] == anchors
assert [str(x) for x in saved["members"]] == member_ids
row = {p: i for i, p in enumerate(anchors)}

d_dir, a_dir = results / "predict_newbranch_out", results / "predict_targets_out"
d, a = load(d_dir / "predictions.npz"), load(a_dir / "predictions.npz")
d_receipt = json.loads((d_dir / "receipt.json").read_text())
d_ids = [str(x) for x in d["perts"]]
assert all(i.endswith(SUFFIX) for i in d_ids) and d_receipt["condition_ids"] == d_ids
symbols = [i[: -len(SUFFIX)] for i in d_ids]
assert [str(x) for x in d["genes"]] == genes and [str(x) for x in d["members"]] == member_ids
assert [str(x) for x in a["perts"]] == symbols, "run D's symbols are run A's conditions, in the same order"
idx = [row[s] for s in symbols]

query_file = results / "inputs" / "newbranch_queries.json"
out = {
    "what": "EXTRA diagnostic, not part of the PLAN_R section 6 gate: the new-condition branch of predict_ensemble "
            "(anchors frozen, each new condition computed in its own feature batch) on 31 known answers",
    "export": str(export), "manifest_sha256": MANIFEST_SHA, "conditions": len(d_ids), "genes": len(genes),
    "members": member_ids,
    "receipt": {"query_sha256": d_receipt["query_sha256"], "predictions_sha256": d_receipt["predictions_sha256"],
                "query_file_sha256": sha(query_file), "predictions_file_sha256": sha(d_dir / "predictions.npz")},
    "rule": "members np.array_equal; ensemble and members also reported against rtol = atol = 1e-6",
    "vs_export_saved": {}, "vs_run_a": {}, "per_condition_max_abs_difference_vs_export": {},
}
out["receipt"]["query_sha256_matches_file"] = out["receipt"]["query_sha256"] == out["receipt"]["query_file_sha256"]
out["receipt"]["predictions_sha256_matches_file"] = (
    out["receipt"]["predictions_sha256"] == out["receipt"]["predictions_file_sha256"])
for k, mid in enumerate(member_ids):
    out["vs_export_saved"][mid] = cmp(d["member_delta"][k], saved["member_delta"][k][idx])
    out["vs_run_a"][mid] = cmp(d["member_delta"][k], a["member_delta"][k])
out["vs_export_saved"]["ensemble"] = cmp(d["delta"], saved["delta"][idx])
out["vs_run_a"]["ensemble"] = cmp(d["delta"], a["delta"])
for j, s in enumerate(symbols):
    out["per_condition_max_abs_difference_vs_export"][s] = max(
        float(np.abs(d["member_delta"][k][j].astype(np.float64) - saved["member_delta"][k][row[s]].astype(np.float64)).max())
        for k in range(len(member_ids)))
out["all_members_bit_exact_vs_export"] = all(out["vs_export_saved"][m]["array_equal"] for m in member_ids)
out["ensemble_bit_exact_vs_export"] = out["vs_export_saved"]["ensemble"]["array_equal"]
out["all_within_1e-6_vs_export"] = all(v["within_rtol_atol_1e-6"] for v in out["vs_export_saved"].values())
(results / "comparison_newbranch.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")

lines = ["# Frozen adapter check, EXTRA diagnostic: the new-condition branch (not part of the gate)", "",
         "Run D: the 31 single-gene anchors under renamed ids `<SYMBOL>__new` (same targets), so `predict_ensemble` "
         "freezes the 119 anchors and computes each condition in its own feature batch, the branch a new cohort target "
         "takes. Compared with the export's saved anchor predictions and with run A (the anchor branch). "
         f"Export manifest sha256 `{MANIFEST_SHA}`.", "",
         f"Members bit-exact vs the export's saved predictions: **{out['all_members_bit_exact_vs_export']}**; "
         f"ensemble bit-exact: **{out['ensemble_bit_exact_vs_export']}**; everything within rtol = atol = 1e-6: "
         f"**{out['all_within_1e-6_vs_export']}**.", "",
         "| array | vs export saved: bit-exact | max abs diff | values differing | over 1e-6 rule | vs run A: bit-exact | max abs diff |",
         "|---|---|---:|---:|---:|---|---:|"]
for m in member_ids + ["ensemble"]:
    e, r = out["vs_export_saved"][m], out["vs_run_a"][m]
    lines.append(f"| {m} | {e['array_equal']} | {e['max_abs_difference']:.6g} | {e['values_differing']} | "
                 f"{e['values_exceeding_tolerance']} | {r['array_equal']} | {r['max_abs_difference']:.6g} |")
worst = sorted(out["per_condition_max_abs_difference_vs_export"].items(), key=lambda kv: -kv[1])[:5]
lines += ["", "Largest per-condition member difference vs the export: "
          + ", ".join(f"{s} {v:.6g}" for s, v in worst), "",
          f"Receipt: query_sha256 `{out['receipt']['query_sha256']}` (equals the queries file: "
          f"{out['receipt']['query_sha256_matches_file']}); predictions_sha256 `{out['receipt']['predictions_sha256']}` "
          f"(equals the predictions.npz beside it: {out['receipt']['predictions_sha256_matches_file']}). "
          "The predictions.npz is not committed (`.gitignore`)."]
(results / "comparison_newbranch.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
