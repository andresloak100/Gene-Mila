#!/usr/bin/env python3
"""Ensembl Compara paralogues as knowledge files: the paralog pairs among a bundle's genes ("paralogs") and a
per-gene table of paralog counts ("paralog_annotation").

Why: the ceiling analysis (docs/results/ceiling_analysis.md) says the missing information is which knockdowns behave
alike, and every winning model carries the response of training perturbations whose targets resemble the new target
(gene sets, interaction partners, co-expression). Paralogy is the one tier-1 similarity source named in
docs/NOVEL_FEATURE_NEEDS.md section 7 ("paralogs (Ensembl Compara)") and never built: gene duplication inferred from
protein sequence trees, measured without perturbing anything and holding no expression response. A paralog pair is a
perturbation-side relation (a target's paralog in training is a candidate relative when no annotated set or partner
connects them) and a gene-side one (the target's own paralogs among the measured genes, which a knockdown may spare,
or which may compensate). The file describes the data; it proposes no feature (docs/GOAL_CRITERIA.md A.1).

Input: a BioMart TSV export of human paralogues (dataset hsapiens_gene_ensembl). Ensembl is not reachable from the
cloud sessions, so this runs on the Mac. The export to make, with the bundle's gene list as the "Input external
references ID list" filter under Gene Name (so every bundle gene appears, with empty paralogue columns when it has
none) and these attributes, in this order, under "Homologues (Max select 6 orthologues)", Paralogues:
    Gene stable ID, Gene name, Human paralogue gene stable ID, Human paralogue associated gene name,
    Paralogue %id. target Human gene identical to query gene, Paralogue %id. query gene identical to target Human gene,
    Paralogue last common ancestor with Human, Paralogue homology type
The column headers (the display names above, or BioMart's internal names external_gene_name,
hsapiens_paralog_ensembl_gene, hsapiens_paralog_associated_gene_name, hsapiens_paralog_perc_id,
hsapiens_paralog_perc_id_r1, hsapiens_paralog_subtype, hsapiens_paralog_orthology_type when the export was made with
biomaRt) are TO BE VERIFIED against the BioMart page when the export is made; the builder refuses a file whose header
lacks any required column (exit 2) and names the missing ones. --release names the Ensembl release the export came
from, for the provenance (BioMart writes none into the file).

How the rows are read: a row is one (gene, paralogue) pair in one direction; the reverse pair is another row with the
two percentages swapped. Rows whose homology type is gene_split (one gene annotated as two) are skipped and counted.
"%id. target ... identical to query" is the percentage of the paralogue's protein identical to the gene's, and
"%id. query ... identical to target" the percentage of the gene's own protein identical to the paralogue's; both become
fractions. A gene without a paralogue (empty paralogue columns) is kept with zero counts; a bundle gene absent from the
export altogether is listed under "unmatched" (a retired symbol, usually). Several Ensembl genes with one name are
merged under it.

Output (JSON, both self-describing with a description the planner reads, and a source record):
  paralogs             {"description", "columns": [gene_a, gene_b, identity_a, identity_b, lca, homology_type],
                        "edges": [[...]], "source", "unmatched"}: every paralog pair with both genes measured, each
                        once (gene_a < gene_b); identity_a is the fraction of gene_a's protein identical to gene_b's
  paralog_annotation   {"description", "columns", "column_units", "genes": {symbol: [values]}, "source",
                        "unmatched"}: n_paralogs (human paralogues, measured or not), n_within_species_paralogs,
                        max_identity (highest fraction of the gene's protein identical to any paralogue; 0 without
                        one), n_paralogs_measured, max_identity_measured

    python tools/build_paralogs.py --tsv paralogues_adamson.tsv --release 115 --genes-from data/adamson_cf_clean \\
        --out paralogs.json --table-out paralog_annotation.json
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np

URL = ("https://www.ensembl.org/biomart/martview, dataset hsapiens_gene_ensembl, attributes Gene stable ID, Gene name, "
       "Human paralogue gene stable ID, Human paralogue associated gene name, Paralogue %id. target Human gene "
       "identical to query gene, Paralogue %id. query gene identical to target Human gene, Paralogue last common "
       "ancestor with Human, Paralogue homology type (TSV)")
# key -> patterns matched against the lower-cased header (the display name, then biomaRt's internal name)
HEADERS = {
    "gene": (r"^gene name$", r"^external_gene_name$"),
    "paralog": (r"paralog(?:ue)? associated gene name", r"^hsapiens_paralog_associated_gene_name$"),
    "pid_target": (r"%id.* target .*identical to query", r"^hsapiens_paralog_perc_id$"),
    "pid_query": (r"%id.* query .*identical to target", r"^hsapiens_paralog_perc_id_r1$"),
    "lca": (r"last common ancestor", r"^hsapiens_paralog_subtype$"),
    "type": (r"homology type", r"^hsapiens_paralog_orthology_type$"),
}
OPTIONAL = {"paralog_id": (r"paralog(?:ue)? gene stable id", r"^hsapiens_paralog_ensembl_gene$")}
SKIPPED_TYPES = {"gene_split"}
EDGE_COLUMNS = ["gene_a", "gene_b", "identity_a", "identity_b", "lca", "homology_type"]
TABLE_COLUMNS = ["n_paralogs", "n_within_species_paralogs", "max_identity", "n_paralogs_measured",
                 "max_identity_measured"]
TABLE_UNITS = ("n_paralogs: human paralogues of the gene in Ensembl Compara, measured or not (gene_split rows "
               "excluded); n_within_species_paralogs: those Ensembl labels within_species_paralog; max_identity: "
               "the highest fraction (0 to 1) of the gene's own protein identical to a paralogue's, 0 without one; "
               "n_paralogs_measured and max_identity_measured: the same over paralogues among the bundle's genes")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def find_columns(fieldnames: list[str]) -> dict[str, str]:
    """{key: header} for HEADERS (all required) and OPTIONAL (when present); ValueError names the missing ones."""
    cols = {}
    for key, patterns in {**HEADERS, **OPTIONAL}.items():
        for header in fieldnames:
            text = header.strip().lower()
            if any(re.search(p, text) for p in patterns):
                cols[key] = header
                break
    missing = [k for k in HEADERS if k not in cols]
    if missing:
        raise ValueError(f"the export lacks the columns {missing} (header: {fieldnames}); see the module docstring "
                         "for the BioMart attributes to export")
    return cols


def _fraction(text: str) -> float | None:
    text = (text or "").strip()
    if not text or text.upper() in ("NA", "NAN"):
        return None
    return round(float(text) / 100.0, 4)


def build(tsv: Path, keep: set[str], release: str) -> tuple[dict, dict]:
    """(paralogs file, paralog_annotation file) for the bundle genes `keep`."""
    with open(tsv, newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        cols = find_columns(reader.fieldnames or [])
        rows = list(reader)
    seen: set[str] = set()                      # genes that appear in the export at all
    paralogs: dict[str, dict[str, dict]] = {}   # gene -> paralogue key -> {"within": bool, "identity": float|None}
    edges: dict[tuple[str, str], dict] = {}
    skipped = 0
    for r in rows:
        gene = (r[cols["gene"]] or "").strip()
        if not gene:
            continue
        seen.add(gene)
        para = (r[cols["paralog"]] or "").strip()
        para_id = (r[cols["paralog_id"]] or "").strip() if "paralog_id" in cols else ""
        if not para and not para_id:
            continue  # a gene without paralogues: BioMart writes the gene with empty paralogue columns
        htype = (r[cols["type"]] or "").strip()
        if htype in SKIPPED_TYPES:
            skipped += 1
            continue
        pid_query, pid_target = _fraction(r[cols["pid_query"]]), _fraction(r[cols["pid_target"]])
        key = para or para_id  # an unnamed paralogue counts under its stable id
        entry = paralogs.setdefault(gene, {}).setdefault(key, {"within": False, "identity": None, "measured": False})
        entry["within"] = entry["within"] or htype == "within_species_paralog"
        if pid_query is not None and (entry["identity"] is None or pid_query > entry["identity"]):
            entry["identity"] = pid_query
        entry["measured"] = bool(para) and para in keep
        if gene in keep and para and para in keep and para != gene:
            a, b = (gene, para) if gene < para else (para, gene)
            ia, ib = (pid_query, pid_target) if gene < para else (pid_target, pid_query)
            e = edges.setdefault((a, b), {"identity_a": None, "identity_b": None, "lca": "", "homology_type": ""})
            for k, v in (("identity_a", ia), ("identity_b", ib)):
                if v is not None and (e[k] is None or v > e[k]):
                    e[k] = v
            e["lca"] = e["lca"] or (r[cols["lca"]] or "").strip()
            e["homology_type"] = e["homology_type"] or htype
    genes = {}
    for gene in sorted(keep & seen):
        ps = paralogs.get(gene, {})
        measured = [p for p in ps.values() if p["measured"]]
        ident = [p["identity"] for p in ps.values() if p["identity"] is not None]
        ident_m = [p["identity"] for p in measured if p["identity"] is not None]
        genes[gene] = [len(ps), sum(1 for p in ps.values() if p["within"]), max(ident, default=0.0), len(measured),
                       max(ident_m, default=0.0)]
    unmatched = sorted(keep - seen)
    source = {"file": tsv.name, "sha256": _sha256(tsv), "url": URL, "ensembl_release": release, "n_rows": len(rows),
              "n_genes_in_export": len(seen), "n_gene_split_rows_skipped": skipped,
              "policy": "tier 1 (docs/NOVEL_FEATURE_NEEDS.md section 7: paralogs, Ensembl Compara)"}
    # Kept short: the planner's state shows every knowledge file's description in one section
    # (genemila/research_state.py KNOWLEDGE_SECTION_CHARS), so a long one hides the files after it.
    edge_file = {
        "description": (f"Paralog pairs among the measured genes from Ensembl Compara release {release} (gene "
                        "duplication inferred from protein sequence trees; no perturbation or expression data). "
                        "edges: [gene_a, gene_b, identity_a, identity_b, lca, homology_type], each pair once with "
                        "gene_a < gene_b; identity_a is the fraction (0 to 1) of gene_a's protein identical to "
                        "gene_b's and identity_b the reverse; lca the taxon where the duplication happened (Homo "
                        "sapiens the most recent, Opisthokonta or older the oldest); homology_type as Ensembl labels "
                        "it (within_species_paralog for most pairs). unmatched lists bundle genes absent from the "
                        "export."),
        "columns": EDGE_COLUMNS,
        "edges": [[a, b, e["identity_a"], e["identity_b"], e["lca"], e["homology_type"]]
                  for (a, b), e in sorted(edges.items())],
        "source": source, "unmatched": unmatched,
    }
    table = {
        "description": (f"Per-gene paralog counts from Ensembl Compara release {release} (gene duplication inferred "
                        "from protein sequence trees; no perturbation or expression data). genes[symbol] = values in "
                        "the order of columns: n_paralogs (human paralogues of the gene, measured or not), "
                        "n_within_species_paralogs, max_identity (highest fraction of the gene's protein identical "
                        "to a paralogue's; 0 without one), n_paralogs_measured (paralogues among the bundle's genes), "
                        "max_identity_measured; units in column_units. A listed gene with no paralogue has zeros; "
                        "unmatched lists bundle genes absent from the export."),
        "columns": TABLE_COLUMNS, "column_units": TABLE_UNITS, "genes": genes, "source": source,
        "unmatched": unmatched,
    }
    return edge_file, table


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--tsv", required=True, help="BioMart paralogue export (see the module docstring)")
    ap.add_argument("--release", required=True, help="the Ensembl release the export came from, e.g. 115")
    ap.add_argument("--genes-from", required=True, help="bundle or public directory whose public.npz genes are kept")
    ap.add_argument("--out", required=True, help="the paralogs edge file to write")
    ap.add_argument("--table-out", help="the paralog_annotation per-gene table to write (optional)")
    args = ap.parse_args(argv)
    keep = {str(g) for g in np.load(Path(args.genes_from) / "public.npz", allow_pickle=False)["genes"]}
    try:
        edge_file, table = build(Path(args.tsv), keep, args.release)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    Path(args.out).write_text(json.dumps(edge_file, separators=(",", ":"), allow_nan=False))
    print(f"{len(edge_file['edges'])} paralog pairs among {len(table['genes'])} matched genes written to {args.out}; "
          f"{len(edge_file['unmatched'])} bundle genes unmatched; {edge_file['source']['n_gene_split_rows_skipped']} "
          "gene_split rows skipped")
    if args.table_out:
        Path(args.table_out).write_text(json.dumps(table, separators=(",", ":"), allow_nan=False))
        with_p = sum(1 for v in table["genes"].values() if v[0] > 0)
        print(f"{len(table['genes'])} genes written to {args.table_out} ({with_p} with a paralogue)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
