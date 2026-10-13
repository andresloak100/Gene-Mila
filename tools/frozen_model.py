#!/usr/bin/env python3
"""Export a pinned frozen ensemble, or predict target-only queries without fitting."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from genemila.frozen import export_ensemble, predict_ensemble, sha256  # noqa: E402


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
        else:
            receipt = predict_ensemble(args.package, args.manifest_sha256, args.queries, args.out)
            print(f"predicted {len(receipt['condition_ids'])} conditions; receipt {args.out / 'receipt.json'}")
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(2, f"frozen model refused input: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
