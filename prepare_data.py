#!/usr/bin/env python3
"""Prepare a dataset bundle under data/<name>/.

    python prepare_data.py synthetic                      # small synthetic fixture (seconds)
    python prepare_data.py describe FILE.h5ad [FILE2.h5ad ...]   # inspect before ingesting
    python prepare_data.py h5ad --name adamson --h5ad AdamsonWeissman2016_GSM2406681_10X010.h5ad
    python prepare_data.py h5ad --name adamson --h5ad A.h5ad --splits cellforge_splits.json
"""

import argparse
from pathlib import Path

from genemila import REPO_ROOT


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("synthetic")
    s.add_argument("--name", default="synthetic")
    s.add_argument("--genes", type=int, default=300)
    s.add_argument("--perts", type=int, default=80)
    s.add_argument("--seed", type=int, default=0)
    h = sub.add_parser("h5ad")
    h.add_argument("--name", required=True)
    h.add_argument("--h5ad", required=True, nargs="+")
    h.add_argument("--condition", help="obs column with perturbation labels (auto-detected)")
    h.add_argument("--control", help="control label (auto-detected)")
    h.add_argument("--hvg", type=int, default=2000)
    h.add_argument("--min-cells", type=int, default=20)
    h.add_argument("--no-collapse", action="store_true", help="keep each label separate (e.g. per guide)")
    h.add_argument("--splits", help="JSON with train/val1/val2 perturbation lists to use instead of ours")
    h.add_argument("--seed", type=int, default=0)
    d = sub.add_parser("describe")
    d.add_argument("files", nargs="+")
    args = ap.parse_args()
    if args.cmd == "describe":
        import json
        from genemila.data.real import describe_h5ad
        for f in args.files:
            print(json.dumps(describe_h5ad(Path(f)), indent=1, default=str))
        return
    out = REPO_ROOT / "data" / args.name
    if args.cmd == "synthetic":
        from genemila.data.synthetic import generate
        generate(out, n_genes=args.genes, n_perts=args.perts, seed=args.seed)
    else:
        from genemila.data.real import ingest_h5ad
        ingest_h5ad([Path(p) for p in args.h5ad], out, args.name, condition_key=args.condition,
                    control_value=args.control, n_hvg=args.hvg, min_cells=args.min_cells,
                    collapse_by_target=not args.no_collapse, seed=args.seed,
                    splits_file=Path(args.splits) if args.splits else None)
    print(f"dataset written to {out}")
    print((out / "manifest.json").read_text())


if __name__ == "__main__":
    main()
