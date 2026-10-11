#!/usr/bin/env python3
"""Count the cells behind each perturbation's recorded target mean, for tools/noise_ceiling.py --ncells.

A bundle stores at most a few hundred held-out cells per visible-validation perturbation, while its recorded
target mean averages every cell of that perturbation in the source file. The noise ceiling needs the full count
to carry its Spearman-Brown step to the target. This tool re-reads only the obs and var tables of the source h5ad
recorded in the bundle's manifest (backed mode, X is never loaded) and groups the labels exactly as the ingestion
did (genemila.data.real: the manifest's condition_key, control labels and collapse_by_target, targets parsed by
parse_label against the source's gene names from the manifest's gene_name_key, keyed by perturbation_key so either
order of a combination pools, and a label with an unknown token skipped when the manifest records strict_labels).
Nothing else is read; the output is {perturbation: cells}.

    python tools/count_target_cells.py --bundle data/adamson_cf --out data/adamson_cf/ncells.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from genemila.data.real import parse_label, perturbation_key  # noqa: E402


def count_cells(manifest: dict, h5ad: Path | None = None, gene_name_key: str | None = None) -> dict[str, int]:
    """gene_name_key: the var column with gene symbols; None takes the one the manifest records, else gene_name
    (var_names when the file has no such column, as the ingest does)."""
    import anndata as ad
    sources = [Path(p) for p in manifest["source"]] if h5ad is None else [Path(h5ad)]
    controls = manifest["control_value"]
    controls = [controls] if isinstance(controls, str) else list(controls)
    collapse = bool(manifest.get("collapse_by_target", True))
    strict = bool(manifest.get("strict_labels", False))
    gene_name_key = gene_name_key or manifest.get("gene_name_key") or "gene_name"
    counts: dict[str, int] = {}
    for path in sources:
        a = ad.read_h5ad(path, backed="r")
        try:
            cond = a.obs[manifest["condition_key"]].astype(object).fillna("unassigned").to_numpy(dtype=str)
            genes = set((a.var[gene_name_key] if gene_name_key in a.var else a.var_names).astype(str))
        finally:
            if getattr(a, "file", None) is not None:
                a.file.close()
        labels, n = np.unique(cond, return_counts=True)
        for c, k in zip(labels, n):
            if c in controls:
                continue
            tg, unknown = parse_label(str(c), genes)
            if not tg or (strict and unknown):
                continue
            key = perturbation_key(tg) if collapse else str(c)
            counts[key] = counts.get(key, 0) + int(k)
    return dict(sorted(counts.items()))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--bundle", required=True, help="bundle directory (its manifest.json names the source h5ad)")
    ap.add_argument("--out", required=True, help="output JSON {perturbation: cells}")
    ap.add_argument("--h5ad", default=None, help="the source h5ad, when it moved since the bundle was built")
    ap.add_argument("--gene-name-key", default=None,
                    help="var column with gene symbols (default: the manifest's gene_name_key, else gene_name)")
    args = ap.parse_args(argv)
    manifest = json.loads((Path(args.bundle) / "manifest.json").read_text())
    if len(manifest.get("source", [])) != 1 and args.h5ad:
        ap.error("--h5ad replaces a single source file; this bundle was built from several")
    counts = count_cells(manifest, Path(args.h5ad) if args.h5ad else None, args.gene_name_key)
    Path(args.out).write_text(json.dumps(counts, indent=1))
    print(f"{len(counts)} perturbations, {sum(counts.values()):,} cells -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
