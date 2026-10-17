#!/usr/bin/env python3
"""Export a pinned frozen ensemble, or predict target-only queries without fitting."""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from genemila.frozen import export_ensemble, predict_ensemble, sha256  # noqa: E402


def predict_targets(package: Path, manifest_sha256: str, conditions: dict[str, list[str]], out: Path) -> dict:
    """The new-cohort path (docs/PLAN_R_FRESH_TEST.md): predictions for new conditions named by their target
    symbols, through predict_ensemble's strict query path, which refuses a target outside the frozen gene universe.
    conditions maps a condition id to its target genes. Returns {"delta": (conditions × genes) float32 mean delta
    on the original public control scale, "perts", "genes", "receipt"}. No control profile is accepted: a cohort's
    own control enters only on the holder's side, when the delta is scored against the cohort's own means. This
    lives outside genemila/frozen.py so the pinned runtime sources of an existing export stay byte identical."""
    if not isinstance(conditions, dict) or not conditions:
        raise ValueError("conditions must be a nonempty mapping of condition id to target genes")
    out = Path(out)
    # Fixed serialisation, so the receipt's query_sha256 is reproducible from the condition list alone.
    query_bytes = (json.dumps({"schema_version": 1, "queries": [
        {"condition_id": c, "target_genes": list(t)} for c, t in conditions.items()]}, indent=2, sort_keys=True)
        + "\n").encode()
    with tempfile.TemporaryDirectory(prefix=".frozen-targets-") as tmp:
        query = Path(tmp) / "queries.json"
        query.write_bytes(query_bytes)
        receipt = predict_ensemble(package, manifest_sha256, query, out)
    # The deposit keeps the exact query bytes the receipt pins (query_sha256), beside predictions.npz and receipt.json.
    (out / "queries.json").write_bytes(query_bytes)
    with np.load(out / "predictions.npz", allow_pickle=False) as z:
        return {"delta": z["delta"].copy(), "perts": z["perts"].tolist(), "genes": z["genes"].tolist(),
                "receipt": receipt}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    export = modes.add_parser("export")
    export.add_argument("--receipt", type=Path, required=True)
    export.add_argument("--receipt-sha256", required=True)
    export.add_argument("--member", action="append", required=True, metavar="EXPERIMENT=ALPHA",
                        help="explicit frozen identity and alpha; supply every receipt member")
    export.add_argument("--trust-archived-pickle", action="store_true",
                        help="acknowledge archived pickle and plugin execution after hash verification")
    export.add_argument("--out", type=Path, required=True)
    predict = modes.add_parser("predict")
    predict.add_argument("--package", type=Path, required=True)
    predict.add_argument("--manifest-sha256", required=True)
    predict.add_argument("--queries", type=Path, required=True)
    predict.add_argument("--out", type=Path, required=True)
    targets = modes.add_parser("predict-targets", help="one single-target condition per symbol, named by it")
    targets.add_argument("--package", type=Path, required=True)
    targets.add_argument("--manifest-sha256", required=True)
    targets.add_argument("--target", action="append", required=True, metavar="SYMBOL")
    targets.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.mode == "export":
            selections = []
            for item in args.member:
                experiment, alpha = item.split("=", 1)
                selections.append((experiment, float(alpha)))
            export_ensemble(args.receipt, args.receipt_sha256, selections, args.out,
                            trust_pickle=args.trust_archived_pickle)
            print(f"exported {args.out}; manifest SHA256 {sha256(args.out / 'manifest.json')}")
        elif args.mode == "predict-targets":
            got = predict_targets(args.package, args.manifest_sha256, {t: [t] for t in args.target}, args.out)
            print(f"predicted {len(got['perts'])} conditions; receipt {args.out / 'receipt.json'}")
        else:
            receipt = predict_ensemble(args.package, args.manifest_sha256, args.queries, args.out)
            print(f"predicted {len(receipt['condition_ids'])} conditions; receipt {args.out / 'receipt.json'}")
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(2, f"frozen model refused input: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
