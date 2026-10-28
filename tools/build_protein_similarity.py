#!/usr/bin/env python3
"""Protein-sequence similarity from UniProt's per-protein embeddings as knowledge files: the nearest sequence
neighbours among a bundle's genes ("protein_similarity") and, optionally, a per-gene table of the embedding's
principal components ("protein_embedding").

Why: a second similarity source that no gene set, interaction partner or co-expression supplies. UniProt distributes a
precomputed embedding of every protein of the human reference proteome, computed from the amino-acid sequence alone
by a protein language model (https://www.uniprot.org/help/embeddings; no perturbation, no expression response, no
GPU needed here). Two proteins with similar embeddings share folds, domains and often function, including pairs too
diverged for Ensembl to call paralogues and pairs no curated set connects. Under the data-source policy of
docs/NOVEL_FEATURE_NEEDS.md section 7 (allowed when measured or derived without perturbing genes and free of the
responses the lab predicts) this is tier 1 by the rule's wording, though the table there does not name it; the lead
confirms the tier before a run. The files describe the data; they propose no feature (docs/GOAL_CRITERIA.md A.1).

Inputs (UniProt is not reachable from the cloud sessions, so this runs on the Mac):
  --h5    UniProt's per-protein embeddings of the human reference proteome, an HDF5 file keyed by accession, one
          vector per entry:
              https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/embeddings/UP000005640_9606/per-protein.h5
          (path and layout TO BE VERIFIED on https://www.uniprot.org/help/embeddings when the file is fetched; the
          builder refuses a file whose entries are not one-dimensional vectors of one common length)
  --tsv   the UniProt REST TSV export of the reviewed human proteome that tools/build_protein_annotation.py reads
          (the same file serves both); only the columns Entry, Gene Names (primary) and Length are used, so an
          export with those three fields is enough
  --release  the UniProt release of both files, e.g. 2025_04, for the provenance

How the rows are read: an entry is assigned to every name in "Gene Names (primary)" ("; "-separated), and a gene
keeps the longest protein that has an embedding (ties by accession), as the protein table keeps the longest protein.
Each kept vector is scaled to unit length; the similarity of two genes is the cosine of their vectors. For every
bundle gene with an embedding its --k most similar other bundle genes are taken, and the union over both directions
is written, each pair once (gene_a < gene_b). Bundle genes without a reviewed entry or without an embedding are
listed under "unmatched".

Output (JSON, self-describing with a description the planner reads, and a source record):
  protein_similarity   {"description", "columns": [gene_a, gene_b, cosine], "edges": [[...]], "source", "unmatched"}
  protein_embedding    (--table-out, --components N) {"description", "columns": [pc1..pcN], "column_units",
                        "genes": {symbol: [values]}, "source", "unmatched"}: the first N principal components of
                        the bundle genes' unit vectors (centred over those genes), with the variance each explains
                        in the source record

    python tools/build_protein_similarity.py --h5 per-protein.h5 --tsv uniprot_human_reviewed.tsv --release 2025_04 \\
        --genes-from data/adamson_cf_clean --k 10 --out protein_similarity.json \\
        --table-out protein_embedding.json --components 8
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

URL_H5 = ("https://ftp.uniprot.org/pub/databases/uniprot/current_release/knowledgebase/embeddings/UP000005640_9606/"
          "per-protein.h5")
URL_TSV = ("https://rest.uniprot.org/uniprotkb/stream?format=tsv&query=organism_id:9606+AND+reviewed:true"
           "&fields=accession,gene_primary,length")
HEADERS = {"entry": "Entry", "gene": "Gene Names (primary)", "length": "Length"}
EDGE_COLUMNS = ["gene_a", "gene_b", "cosine"]
DEFAULT_K = 10


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_embeddings(h5: Path, wanted: set[str]) -> tuple[dict[str, np.ndarray], int, int]:
    """{accession: vector} for the wanted accessions present in the file, the file's entry count and the dimension.
    ValueError when the entries are not vectors of one common length."""
    import h5py
    out: dict[str, np.ndarray] = {}
    dim = None
    with h5py.File(h5, "r") as fh:
        keys = list(fh.keys())
        for key in keys:
            if key not in wanted:
                continue
            v = np.asarray(fh[key][()], dtype=np.float64).ravel()
            if dim is None:
                dim = int(v.size)
            if v.ndim != 1 or v.size != dim or dim == 0:
                raise ValueError(f"{h5.name}: entry {key} is not a vector of length {dim}; see the module docstring")
            out[key] = v
    return out, len(keys), (dim or 0)


def gene_entries(tsv: Path) -> dict[str, list[tuple[int, str]]]:
    """{gene name: [(length, accession)]} from the UniProt TSV; ValueError names missing columns."""
    with open(tsv, newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        missing = [h for h in HEADERS.values() if h not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{tsv.name} lacks columns {missing}; the export needs the fields accession, "
                             "gene_primary and length (see the module docstring)")
        out: dict[str, list[tuple[int, str]]] = {}
        for r in reader:
            for name in filter(None, (g.strip() for g in (r[HEADERS["gene"]] or "").split(";"))):
                out.setdefault(name, []).append((int(r[HEADERS["length"]]), r[HEADERS["entry"]]))
    return out


def choose_accessions(entries: dict[str, list[tuple[int, str]]], keep: set[str], have: set[str]) -> dict[str, str]:
    """{gene: accession}: for each bundle gene the longest protein that has an embedding, ties by accession."""
    chosen = {}
    for gene in sorted(keep & set(entries)):
        cands = sorted(((-ln, acc) for ln, acc in entries[gene] if acc in have))
        if cands:
            chosen[gene] = cands[0][1]
    return chosen


def neighbours(names: list[str], E: np.ndarray, k: int) -> list[list]:
    """[[a, b, cosine]] over the union of every gene's k nearest others, each pair once (a < b), sorted."""
    if len(names) < 2 or k < 1:
        return []
    U = E / np.maximum(np.linalg.norm(E, axis=1, keepdims=True), 1e-12)
    S = U @ U.T
    np.fill_diagonal(S, -np.inf)
    k = min(k, len(names) - 1)
    edges: dict[tuple[str, str], float] = {}
    for i, a in enumerate(names):
        for j in np.argsort(-S[i], kind="stable")[:k]:
            b = names[j]
            key = (a, b) if a < b else (b, a)
            edges[key] = round(float(S[i, j]), 4)
    return [[a, b, c] for (a, b), c in sorted(edges.items())]


def components(names: list[str], E: np.ndarray, n: int) -> tuple[dict[str, list[float]], list[float]]:
    """The first n principal components of the unit vectors, centred over these genes, and the variance fraction
    each explains."""
    U = E / np.maximum(np.linalg.norm(E, axis=1, keepdims=True), 1e-12)
    X = U - U.mean(axis=0, keepdims=True)
    n = max(0, min(n, min(X.shape) - 1 if min(X.shape) > 1 else 0))
    if n == 0:
        return {g: [] for g in names}, []
    _, s, vt = np.linalg.svd(X, full_matrices=False)
    scores = X @ vt[:n].T
    # a reproducible sign: the largest-magnitude loading of each component is positive
    sign = np.sign(vt[:n][np.arange(n), np.argmax(np.abs(vt[:n]), axis=1)])
    scores = scores * sign
    var = (s ** 2) / max(float((s ** 2).sum()), 1e-12)
    return ({g: [round(float(x), 4) for x in scores[i]] for i, g in enumerate(names)},
            [round(float(v), 4) for v in var[:n]])


def build(h5: Path, tsv: Path, keep: set[str], release: str, k: int = DEFAULT_K,
          n_components: int = 0) -> tuple[dict, dict | None]:
    """(protein_similarity file, protein_embedding table or None) for the bundle genes `keep`."""
    entries = gene_entries(tsv)
    wanted = {acc for gene in keep & set(entries) for _, acc in entries[gene]}
    vectors, n_entries, dim = read_embeddings(h5, wanted)
    chosen = choose_accessions(entries, keep, set(vectors))
    names = sorted(chosen)
    E = np.vstack([vectors[chosen[g]] for g in names]) if names else np.zeros((0, dim))
    unmatched = sorted(keep - set(chosen))
    source = {"h5_file": h5.name, "h5_sha256": _sha256(h5), "h5_url": URL_H5, "tsv_file": tsv.name,
              "tsv_sha256": _sha256(tsv), "tsv_url": URL_TSV, "uniprot_release": release, "n_embeddings_in_file": n_entries,
              "dimension": dim, "k": k, "n_genes_with_embedding": len(names), "accessions": chosen,
              "policy": ("sequence only, no perturbation or expression data: tier 1 by the rule of "
                         "docs/NOVEL_FEATURE_NEEDS.md section 7, not named in its table; the lead confirms")}
    edges = neighbours(names, E, k)
    # Kept short: the planner's state shows every knowledge file's description in one section
    # (genemila/research_state.py KNOWLEDGE_SECTION_CHARS), so a long one hides the files after it.
    edge_file = {
        "description": (f"Protein-sequence similarity among the measured genes from UniProt's per-protein embeddings "
                        f"(release {release}; a protein language model's vector of each protein, computed from its "
                        "amino-acid sequence alone; no perturbation, expression or interaction data). edges: "
                        f"[gene_a, gene_b, cosine], the union of each gene's {k} most similar other measured genes "
                        "(the longest protein of the gene), each pair once with gene_a < gene_b; cosine in -1 to 1, "
                        "higher is more similar in sequence, fold and often function, including pairs too diverged "
                        "to be called paralogs. unmatched lists bundle genes with no reviewed entry or embedding."),
        "columns": EDGE_COLUMNS, "edges": edges, "source": source, "unmatched": unmatched,
    }
    table = None
    if n_components > 0:
        scores, var = components(names, E, n_components)
        n = len(var)
        table = {
            "description": (f"The first {n} principal components of the measured genes' protein-sequence embeddings "
                            f"(UniProt per-protein embeddings, release {release}; sequence only, no perturbation or "
                            "expression data), centred over the measured genes. genes[symbol] = values in the order "
                            f"of columns pc1..pc{n}; genes with similar values share sequence features (fold, "
                            "domains); the variance each component explains is in source.explained_variance. "
                            "unmatched lists bundle genes with no reviewed entry or embedding."),
            "columns": [f"pc{i + 1}" for i in range(n)],
            "column_units": "unitless scores on unit-length embedding vectors",
            "genes": scores, "source": {**source, "explained_variance": var}, "unmatched": unmatched,
        }
    return edge_file, table


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--h5", required=True, help="UniProt per-protein embeddings (HDF5 keyed by accession)")
    ap.add_argument("--tsv", required=True, help="UniProt reviewed-human TSV with Entry, Gene Names (primary), Length")
    ap.add_argument("--release", required=True, help="the UniProt release of both files, e.g. 2025_04")
    ap.add_argument("--genes-from", required=True, help="bundle or public directory whose public.npz genes are kept")
    ap.add_argument("--k", type=int, default=DEFAULT_K, help=f"nearest neighbours per gene (default {DEFAULT_K})")
    ap.add_argument("--out", required=True, help="the protein_similarity edge file to write")
    ap.add_argument("--table-out", help="the protein_embedding per-gene table to write (optional)")
    ap.add_argument("--components", type=int, default=0, help="principal components in the table (0: no table)")
    args = ap.parse_args(argv)
    if args.table_out and args.components < 1:
        ap.error("--table-out needs --components N with N >= 1")
    keep = {str(g) for g in np.load(Path(args.genes_from) / "public.npz", allow_pickle=False)["genes"]}
    try:
        edge_file, table = build(Path(args.h5), Path(args.tsv), keep, args.release, args.k,
                                 args.components if args.table_out else 0)
    except (ValueError, OSError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    Path(args.out).write_text(json.dumps(edge_file, separators=(",", ":"), allow_nan=False))
    print(f"{len(edge_file['edges'])} similarity pairs among {edge_file['source']['n_genes_with_embedding']} genes "
          f"with an embedding written to {args.out}; {len(edge_file['unmatched'])} bundle genes unmatched")
    if table is not None:
        Path(args.table_out).write_text(json.dumps(table, separators=(",", ":"), allow_nan=False))
        print(f"{len(table['genes'])} genes x {len(table['columns'])} components written to {args.table_out} "
              f"(explained variance {table['source']['explained_variance']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
