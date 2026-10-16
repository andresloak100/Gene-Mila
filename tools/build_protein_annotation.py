#!/usr/bin/env python3
"""UniProt protein features (signal peptide, membrane spans, localisation) as a knowledge file ("protein_annotation").

The genome annotation table (tools/build_gene_annotation.py) says how a gene's message is built; this one says where
its protein goes. The motivating use is rank 1 of docs/NOVEL_FEATURE_NEEDS.md, section 2.1: a knockdown of the SRP
receptor, the translocon or the OST complex should hit the messages of ER-targeted proteins (signal peptide or
transmembrane spans) through SRP-dependent decay, so the gene side of that interaction is "is this protein
ER-targeted", which no bundle file carries. The nine localisation flags give the same kind of gene-side term for
other compartments (mitochondrial import, nuclear, secretory). UniProt's reviewed (Swiss-Prot) annotation is curated
protein knowledge from sequence, structure and literature, with no perturbation screen or expression response behind
it: tier 1 of the data-source policy (section 7). Features read it with ctx.knowledge("protein_annotation").

Input: a UniProt REST TSV export of the reviewed human proteome. UniProt is not reachable from the cloud sessions, so
this runs on the Mac. The export used for the first build (about 20,400 entries, a few MB):
    https://rest.uniprot.org/uniprotkb/stream?format=tsv&query=organism_id:9606+AND+reviewed:true&fields=accession,gene_primary,length,ft_signal,ft_transmem,cc_subcellular_location,keyword
The field names (accession, gene_primary, length, ft_signal, ft_transmem, cc_subcellular_location, keyword) and the
column headers they produce (Entry, Gene Names (primary), Length, Signal peptide, Transmembrane, Subcellular location
[CC], Keywords) are TO BE VERIFIED against https://www.uniprot.org/help/return_fields when the export is made; the
builder refuses a file whose header lacks any of them (exit 2) and names the missing ones.

How the rows are read: an entry is assigned to every name in "Gene Names (primary)" (a few entries carry several,
"; "-separated); a gene with several entries keeps the longest protein (one row per gene, as the other tables).
UniProt writes features as "SIGNAL 1..22; /evidence=..." and "TRANSMEM 12..34; /note=...; TRANSMEM 56..78; ...":
the signal peptide length is the end of the SIGNAL range (null when UniProt writes "?" or "<"/">" for an unknown end,
the flag still 1), and n_transmembrane counts the TRANSMEM occurrences. The localisation flags are 0/1 by substring in
the lower-cased subcellular-location text and keywords together: secreted ("secreted"), membrane ("membrane", any
membrane), endoplasmic_reticulum, golgi, mitochondrion ("mitochondri"), nucleus ("nucleus", "nucleolus",
"nucleoplasm"; not "nucle", which would catch nucleotide-binding), cytoplasm ("cytoplasm", "cytosol"), lysosome,
peroxisome. UniProt's text also names compartments in "Note=" sentences and isoform-specific locations, so a flag
means "UniProt mentions this compartment for the protein", not "its main location".

The output (JSON): description (shown to the planner), columns, column_units, genes {symbol: [value per column]},
source {file, sha256, url, n_entries}, and with --genes-from (a bundle or public directory) only the bundle's genes,
plus "unmatched" (symbols UniProt does not use as a primary gene name).

    python tools/build_protein_annotation.py --tsv uniprot_human_reviewed.tsv --genes-from data/adamson \\
        --out protein_annotation.json
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

URL = ("https://rest.uniprot.org/uniprotkb/stream?format=tsv&query=organism_id:9606+AND+reviewed:true"
       "&fields=accession,gene_primary,length,ft_signal,ft_transmem,cc_subcellular_location,keyword")
HEADERS = {"entry": "Entry", "gene": "Gene Names (primary)", "length": "Length", "signal": "Signal peptide",
           "transmem": "Transmembrane", "location": "Subcellular location [CC]", "keywords": "Keywords"}
LOCALISATION = {"secreted": ("secreted",), "membrane": ("membrane",),
                "endoplasmic_reticulum": ("endoplasmic reticulum",), "golgi": ("golgi",),
                "mitochondrion": ("mitochondri",), "nucleus": ("nucleus", "nucleolus", "nucleoplasm"),
                "cytoplasm": ("cytoplasm", "cytosol"), "lysosome": ("lysosom",), "peroxisome": ("peroxisom",)}
COLUMNS = ["protein_length", "has_signal_peptide", "signal_peptide_length", "n_transmembrane"] + list(LOCALISATION)
UNITS = ("protein_length: amino acids; has_signal_peptide: 0/1; signal_peptide_length: amino acids (0 without one, "
         "null when UniProt leaves the end open); n_transmembrane: UniProt TRANSMEM segments; "
         + ", ".join(LOCALISATION) + ": 0/1, UniProt names the compartment in the subcellular location or keywords")
_SIGNAL = re.compile(r"\bSIGNAL\s+[<>]?(\d+|\?)\.\.([<>]?)(\d+|\?)")
_TRANSMEM = re.compile(r"\bTRANSMEM\b")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def parse_signal(text: str) -> tuple[int, int | None]:
    """(has_signal_peptide, signal_peptide_length) from UniProt's "Signal peptide" feature text."""
    m = _SIGNAL.search(text or "")
    if not m:
        return 0, 0
    open_end = m.group(2) != "" or m.group(3) == "?"   # "1..>22" or "1..?": UniProt does not know where it ends
    return 1, (None if open_end else int(m.group(3)))


def row_values(r: dict) -> list:
    """The COLUMNS values of one UniProt entry (a dict keyed by HEADERS' column names)."""
    has_sp, sp_len = parse_signal(r[HEADERS["signal"]])
    text = f"{r[HEADERS['location']]} {r[HEADERS['keywords']]}".lower()
    return ([int(r[HEADERS["length"]]), has_sp, sp_len, len(_TRANSMEM.findall(r[HEADERS["transmem"]] or ""))]
            + [int(any(w in text for w in words)) for words in LOCALISATION.values()])


def build(tsv: Path, keep: set[str] | None) -> dict:
    with open(tsv, newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        missing = [h for h in HEADERS.values() if h not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{tsv.name} lacks columns {missing}; check the UniProt field names in the module "
                             "docstring against https://www.uniprot.org/help/return_fields")
        rows = list(reader)
    best: dict[str, dict] = {}
    for r in rows:
        for name in filter(None, (g.strip() for g in (r[HEADERS["gene"]] or "").split(";"))):
            prev = best.get(name)
            # the longest protein stands for the gene; ties by accession so the choice is reproducible
            if prev is None or (-int(r[HEADERS["length"]]), r[HEADERS["entry"]]) < (-int(prev[HEADERS["length"]]),
                                                                                    prev[HEADERS["entry"]]):
                best[name] = r
    genes = {n: row_values(best[n]) for n in sorted(best) if keep is None or n in keep}
    # Kept short: the planner's state shows all knowledge files in one section cut at 2,500 characters
    # (genemila/research_state.py SECTION_CHARS), so a long description would hide the files listed after it.
    description = ("Protein features from UniProt reviewed human entries (curated sequence annotation; no perturbation "
                   "or expression response); one entry per gene, the longest protein. genes[symbol] = values in the "
                   "order of columns: protein_length, has_signal_peptide (0/1: ER-targeted, secretory or membrane "
                   "protein), signal_peptide_length, n_transmembrane (membrane-spanning segments; >0 is also "
                   "ER-targeted), then 0/1 flags for where UniProt places the protein: secreted, membrane, "
                   "endoplasmic_reticulum, golgi, mitochondrion, nucleus, cytoplasm, lysosome, peroxisome (a protein "
                   "may carry several; a flag means the compartment is named, not that it is the main one); units in "
                   "column_units. unmatched lists bundle genes UniProt does not use as a primary gene name.")
    return {"description": description, "columns": COLUMNS, "column_units": UNITS, "genes": genes,
            "source": {"file": tsv.name, "sha256": _sha256(tsv), "url": URL, "n_entries": len(rows),
                       "n_genes_in_table": len(best)}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--tsv", required=True, help="UniProt REST TSV export (see the module docstring for the URL)")
    ap.add_argument("--genes-from", help="bundle or public directory whose public.npz genes the output keeps")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    keep = None
    if args.genes_from:
        keep = {str(g) for g in np.load(Path(args.genes_from) / "public.npz", allow_pickle=False)["genes"]}
    try:
        table = build(Path(args.tsv), keep)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if keep is not None:
        table["unmatched"] = sorted(keep - set(table["genes"]))
    Path(args.out).write_text(json.dumps(table, separators=(",", ":")))
    print(f"{len(table['genes'])} genes written to {args.out}"
          + (f"; {len(table['unmatched'])} bundle genes unmatched" if keep is not None else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
