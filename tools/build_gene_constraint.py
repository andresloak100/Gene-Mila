#!/usr/bin/env python3
"""gnomAD v2.1.1 per-gene constraint as a knowledge file for a bundle ("gene_constraint").

Constraint is population genetics: how many loss-of-function (LoF) or missense variants gnomAD saw in 125,748 exomes
against how many its mutation model expected. Nothing in it comes from perturbing genes or from measuring expression
responses, so it is tier 1 of the data-source policy (docs/NOVEL_FEATURE_NEEDS.md, sections 2.1 "cheap extras" and 7)
and cannot encode a held-out response. Two uses motivated it, both hypotheses to test rather than properties: a
LoF-intolerant gene (high pLI, low LOEUF) is a candidate gene-side term for how strongly a knockdown propagates;
and a cheap per-gene scalar that features can cross with the perturbed gene's own constraint. Tolerance to
over-expression (the CRISPRa side) is triplosensitivity, which gnomAD does not measure; that would need Collins 2022
pHaplo/pTriplo (section 2.1), not built here. Features read it with ctx.knowledge("gene_constraint").

Columns kept, as gnomAD names them (Karczewski et al. 2020, Nature 581:434): oe_lof, oe_lof_lower, oe_lof_upper
(LOEUF, the upper bound of the 90% CI of observed/expected LoF; low = intolerant), pLI, pNull, pRec (probabilities of
the LoF-intolerant, neutral and recessive classes), oe_mis, oe_mis_upper, mis_z, syn_z, lof_z (missense, synonymous and
LoF z scores; a synonymous z far from 0 marks a model misfit), obs_lof, exp_lof, oe_lof_upper_bin (LOEUF decile,
0 = most constrained). Rows gnomAD flags are kept, with the flag recorded under "flags", because the lab's features
decide for themselves whether to trust them. The flag is gnomAD's constraint_flag string: one or more of no_exp_lof,
no_exp_mis, no_exp_syn, no_variants, lof_too_many, mis_too_many, syn_outlier, joined by "|" when several apply
(157 rows read "mis_too_many|syn_outlier"), so features test with `in`, not equality. 507 of the 19,704 rows carry
no_exp_lof and have no LoF values (null; their missense and synonymous columns stay). gnomAD writes "NA" for a
missing value and, in one row (RPS17), the literal "NaN": both become null, and json.dumps(allow_nan=False) refuses
any other non-finite value instead of writing a bare NaN token, which is not JSON. 46 symbols appear twice (two
Ensembl genes, one symbol): the row without a flag wins, then the larger exp_lof (the transcript with the most power),
then the transcript id.

gnomAD v2 is on GRCh37 with GENCODE v19 symbols, so some current symbols differ (for example SEPP1 is now SELENOP);
a bundle symbol the table does not know is listed under "unmatched" (tools/knowledge_coverage.py helps map them).

The output (JSON): description (shown to the planner and the workers), columns, column_units, genes {symbol: [value
per column], null where gnomAD has none}, flags {symbol: constraint_flag} for flagged genes only, source {file,
sha256, url, n_rows}, and with --genes-from (a bundle or public directory) only the bundle's genes, plus "unmatched".

Size of the description. lab.knowledge_summary joins one line per knowledge file (description plus its keys), and the
planner's state cuts that section at 2,500 characters (research_state.SECTION_CHARS); the Norman block-F bundle
(gene_annotation 895-character line, replogle2022_k562 885, five bundle files) already uses 2,322 of them. The
description here is kept near 500 characters (line 653), which fits next to either gene_annotation (summary 2,090)
or the Replogle file (2,080), but not both at once: with all three (2,977) the cut falls inside the Replogle
description, after its sign instruction but before its rule for multi-gene perturbations, and hides targets and
transcription_factors entirely (at the builder's first 935-character line it also removed the sign instruction).
Adding this file to a bundle that holds both needs the planner state to render knowledge differently (the lab-code
owner's call), and the pre-run check in docs/mac/block_f/norman_f_run.sh (summary <= 2,500) is the gate to extend.

    python tools/build_gene_constraint.py --table gnomad.v2.1.1.lof_metrics.by_gene.txt.bgz \\
        --genes-from data/norman --out gene_constraint.json
Input (public, gzip text, 77 tab-separated columns; .bgz is plain gzip to Python):
    https://gnomad-public-us-east-1.s3.amazonaws.com/release/2.1.1/constraint/gnomad.v2.1.1.lof_metrics.by_gene.txt.bgz
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

URL = ("https://gnomad-public-us-east-1.s3.amazonaws.com/release/2.1.1/constraint/"
       "gnomad.v2.1.1.lof_metrics.by_gene.txt.bgz")
COLUMNS = ["oe_lof", "oe_lof_lower", "oe_lof_upper", "pLI", "pNull", "pRec", "oe_mis", "oe_mis_upper", "mis_z",
           "syn_z", "lof_z", "obs_lof", "exp_lof", "oe_lof_upper_bin"]
UNITS = ("oe_lof, oe_lof_lower, oe_lof_upper: observed/expected loss-of-function (LoF) variants and its 90% CI "
         "(oe_lof_upper is LOEUF; < 0.35 is the usual constrained cut, low = LoF-intolerant); pLI, pNull, pRec: "
         "probabilities of the LoF-intolerant (haploinsufficient), neutral and recessive classes, sum 1; "
         "oe_mis, oe_mis_upper: observed/expected missense and its upper bound; mis_z, syn_z, lof_z: z scores "
         "(positive = fewer variants than expected; a synonymous z far from 0 marks a model misfit); obs_lof, exp_lof: "
         "counts; oe_lof_upper_bin: LOEUF decile 0-9, 0 = most constrained. Symbols are gnomAD v2's (GENCODE v19), so "
         "some current symbols differ")
REQUIRED = ["gene", "transcript", "constraint_flag"] + COLUMNS


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _num(s: str):
    """gnomAD's "4.6900e-01" as 0.469, counts and bins as ints, "NA" (and the one row's "NaN") as None."""
    if s in ("NA", ""):
        return None
    v = float(s)
    if not math.isfinite(v):   # RPS17 has oe_mis, mis_z, syn_z written as "NaN": null, never a bare NaN in the JSON
        return None
    v = round(v, 6)
    return int(v) if v.is_integer() else v


def read_table(path: Path) -> list[dict]:
    """One dict per row with the REQUIRED columns as strings. Raises ValueError naming missing columns."""
    opener = gzip.open if str(path).endswith((".gz", ".bgz")) else open
    with opener(path, "rt") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        missing = [c for c in REQUIRED if c not in header]
        if missing:
            raise ValueError(f"{path.name} lacks columns {missing}; is it gnomAD's lof_metrics.by_gene table?")
        idx = [header.index(c) for c in REQUIRED]
        return [dict(zip(REQUIRED, (f[i] for i in idx))) for f in (line.rstrip("\n").split("\t") for line in fh)
                if len(f) >= len(header)]


def build(table: Path, keep: set[str] | None) -> dict:
    rows = read_table(table)
    best: dict[str, dict] = {}
    for r in rows:
        prev = best.get(r["gene"])
        key = (r["constraint_flag"] != "", -(_num(r["exp_lof"]) or 0.0), r["transcript"])
        if prev is None or key < prev["_key"]:
            best[r["gene"]] = {**r, "_key": key}
    names = sorted(n for n in best if keep is None or n in keep)
    genes = {n: [_num(best[n][c]) for c in COLUMNS] for n in names}
    flags = {n: best[n]["constraint_flag"] for n in names if best[n]["constraint_flag"]}
    # Kept short (about 500 characters; the module docstring has the measurement): the planner's state shows all
    # knowledge files in one section cut at 2,500 characters (genemila/research_state.py SECTION_CHARS), and the
    # Norman bundle with gene_annotation and the Replogle file already uses 2,322. The column glosses live in UNITS.
    description = ("gnomAD v2.1.1 per-gene loss-of-function (LoF) constraint: variants seen vs expected in 125k "
                   "exomes (no perturbation or response data). genes[symbol] = values in the order of columns "
                   "(oe_lof_upper is LOEUF; low LOEUF or high pLI = LoF-intolerant; null = none; each column in "
                   "column_units). flags[symbol] = gnomAD's constraint_flag for unreliable genes: one or more of "
                   "no_exp_lof, mis_too_many, lof_too_many, syn_outlier, no_variants joined by '|', so test with "
                   "'in'; absent = clean. unmatched = bundle genes not in the table (GENCODE v19 symbols).")
    return {"description": description, "columns": COLUMNS, "column_units": UNITS, "genes": genes, "flags": flags,
            "source": {"file": table.name, "sha256": _sha256(table), "url": URL, "n_rows": len(rows),
                       "n_genes_in_table": len(best)}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--table", required=True, help="gnomad.v2.1.1.lof_metrics.by_gene.txt.bgz (gzip or plain text)")
    ap.add_argument("--genes-from", help="bundle or public directory whose public.npz genes the output keeps")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    keep = None
    if args.genes_from:
        keep = {str(g) for g in np.load(Path(args.genes_from) / "public.npz", allow_pickle=False)["genes"]}
    try:
        table = build(Path(args.table), keep)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if keep is not None:
        table["unmatched"] = sorted(keep - set(table["genes"]))
    Path(args.out).write_text(json.dumps(table, separators=(",", ":"), allow_nan=False))
    print(f"{len(table['genes'])} genes written to {args.out} ({len(table['flags'])} flagged)"
          + (f"; {len(table['unmatched'])} bundle genes unmatched" if keep is not None else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
