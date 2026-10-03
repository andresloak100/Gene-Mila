#!/usr/bin/env python3
"""Prepare a dataset bundle under data/<name>/.

    python prepare_data.py synthetic                      # small synthetic fixture (seconds)
    python prepare_data.py h5ad --name adamson --h5ad path/to/perturb_processed.h5ad
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
    h.add_argument("--h5ad", required=True)
    h.add_argument("--hvg", type=int, default=2000)
    h.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    out = REPO_ROOT / "data" / args.name
    if args.cmd == "synthetic":
        from genemila.data.synthetic import generate
        generate(out, n_genes=args.genes, n_perts=args.perts, seed=args.seed)
    else:
        from genemila.data.real import ingest_h5ad
        ingest_h5ad(Path(args.h5ad), out, args.name, n_hvg=args.hvg, seed=args.seed)
    print(f"dataset written to {out}")
    print((out / "manifest.json").read_text())


if __name__ == "__main__":
    main()
