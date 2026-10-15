#!/usr/bin/env python3
"""A per-gene annotation table from the genome sequence and a GENCODE annotation, as a knowledge file for a bundle.

The bundle's prior knowledge (genemila/data/knowledge.py) says which genes share pathways, interactions and regulators,
but nothing about the genes themselves as molecules: where they sit, how long they are, what their messages encode.
This table adds those properties, all derived from the reference genome and its annotation, with no expression or
perturbation measurement behind them, so it cannot encode a held-out response (docs/NOVEL_FEATURE_NEEDS.md, section
2.1, ranks 2 and C3). Features read it with ctx.knowledge("gene_annotation"). Three uses motivated it:

  - cis effects of CRISPRi and CRISPRa: dCas9-KRAB at a promoter can silence a gene sharing that promoter, and an
    activator can switch on its neighbour; "bidirectional" and "neighbours" let a feature mark those genes;
  - amino-acid demand: a tRNA synthetase knockdown starves translation of one amino acid, so the amino-acid
    composition of each message ("aa_<X>" columns) is the per-gene side of a knockdown x demand feature;
  - message architecture (lengths, upstream ATGs, GC and CpG content), which sets how fast and how strongly a
    message's level can follow a change in its transcription or decay.

Each gene is represented by one transcript: for protein-coding genes the CCDS (else "basic") transcript with the
longest coding sequence, ties by longest message, then by transcript id; for other genes the longest "basic"
transcript. Its transcription start site (TSS) is the gene's TSS. A symbol annotated more than once keeps the gene on
the lowest-numbered primary chromosome. Coordinates are 1-based as in GTF.

The output (JSON):
    description  what the table is, its source files and every column with its unit (shown to the planner)
    columns      names of the numeric columns
    genes        {symbol: [value per column]}; null where a value does not exist (no coding sequence)
    loci         {symbol: [chromosome, TSS, strand]}
    bidirectional {symbol: [symbols whose TSS is on the other strand within --bidir-bp of this TSS]}
    neighbours   {symbol: [[symbol, TSS distance in bp], ...]} genes of the output within --neighbour-kb, nearest first
With --genes-from (a bundle or public directory) the output keeps the bundle's genes only (neighbour lists then name
bundle genes only; "n_tss_within_100kb" still counts every annotated gene). A bundle symbol the annotation does not
know is listed under "unmatched"; tools/knowledge_coverage.py helps map retired symbols.

    python tools/build_gene_annotation.py --gtf gencode.v27.primary_assembly.annotation.gtf \\
        --fasta Homo_sapiens_assembly38.fasta --genes-from data/norman --out gene_annotation.json
Inputs used for the first build (public, Broad's hg38 reference bucket, reachable from the cloud sessions):
    https://broad-references.s3.amazonaws.com/hg38/v0/gencode.v27.primary_assembly.annotation.gtf
    https://broad-references.s3.amazonaws.com/hg38/v0/Homo_sapiens_assembly38.fasta (and its .fai index)
"""
from __future__ import annotations

import argparse
import bisect
import collections
import json
import re
import sys
from pathlib import Path

import numpy as np

AMINO = "ACDEFGHIKLMNPQRSTVWY"
CODON = {a + b + c: aa for (a, b, c), aa in zip(
    ((x, y, z) for x in "TCAG" for y in "TCAG" for z in "TCAG"),
    "FFLLSSSSYY**CC*WLLLLPPPPHHQQRRRRIIIMTTTTNNKKSSRRVVVVAAAADDEEGGGG")}
COLUMNS = (["gene_span_kb", "n_transcripts", "n_exons", "transcript_length", "cds_length", "utr5_length",
            "utr3_length", "intron_length_kb", "gc_cds", "gc_utr3", "gc_promoter", "cpg_oe_promoter",
            "n_upstream_atg", "nearest_tss_kb", "n_tss_within_100kb"] + [f"aa_{a}" for a in AMINO])
UNITS = ("gene_span_kb: genomic span of the gene, kb; n_transcripts: annotated transcripts; n_exons, "
         "transcript_length (nt), cds_length (nt, stop codon excluded), utr5_length, utr3_length (nt), "
         "intron_length_kb: of the representative transcript; gc_cds, gc_utr3: GC fraction; gc_promoter, "
         "cpg_oe_promoter: GC fraction and CpG observed/expected in TSS +/- 500 bp; n_upstream_atg: ATG triplets in the "
         "5' UTR; nearest_tss_kb: distance to the nearest other annotated TSS, kb; n_tss_within_100kb: annotated TSSs of "
         "other genes within 100 kb; aa_<X>: fraction of amino acid X in the encoded protein")
_ATTR = re.compile(r'(\S+) "([^"]*)"')


def _chrom_rank(c: str) -> tuple:
    c = c.removeprefix("chr")
    return (0, int(c)) if c.isdigit() else (1, {"X": 0, "Y": 1, "M": 2}.get(c, 3), c)


def read_gtf(path: Path) -> dict:
    """{gene_id: {name, type, chrom, strand, start, end, transcripts: {tid: {type, tags, exons, cds, utr}}}}."""
    genes: dict = {}
    with open(path) as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            f = line.rstrip("\n").split("\t")
            if len(f) < 9 or f[2] not in ("gene", "transcript", "exon", "CDS", "UTR"):
                continue
            attrs = collections.defaultdict(list)
            for k, v in _ATTR.findall(f[8]):
                attrs[k].append(v)
            gid = attrs["gene_id"][0]
            start, end = int(f[3]), int(f[4])
            if f[2] == "gene":
                genes[gid] = {"name": attrs["gene_name"][0], "type": attrs["gene_type"][0], "chrom": f[0],
                              "strand": f[6], "start": start, "end": end, "transcripts": {}}
                continue
            tr = genes[gid]["transcripts"].setdefault(attrs["transcript_id"][0], {
                "type": (attrs.get("transcript_type") or [""])[0], "tags": set(), "exons": [], "cds": [], "utr": []})
            tr["tags"].update(attrs.get("tag", []))
            if f[2] in ("exon", "CDS", "UTR"):
                tr[{"exon": "exons", "CDS": "cds", "UTR": "utr"}[f[2]]].append((start, end))
    return genes


def representative(gene: dict) -> tuple[str, dict] | None:
    """The transcript that stands for the gene (see the module docstring)."""
    def length(iv):
        return sum(e - s + 1 for s, e in iv)
    trs = list(gene["transcripts"].items())
    if gene["type"] == "protein_coding":
        coding = [(t, tr) for t, tr in trs if tr["cds"]]
        pool = ([x for x in coding if "CCDS" in x[1]["tags"]] or [x for x in coding if "basic" in x[1]["tags"]]
                or coding)
        key = lambda x: (-length(x[1]["cds"]), -length(x[1]["exons"]), x[0])  # noqa: E731
    else:
        pool = [x for x in trs if "basic" in x[1]["tags"]] or trs
        key = lambda x: (-length(x[1]["exons"]), x[0])  # noqa: E731
    return min(pool, key=key) if pool else None


class Fasta:
    """Random access into an indexed FASTA (.fai next to it), one region at a time."""

    def __init__(self, path: Path):
        self.fh = open(path, "rb")
        self.index = {}
        for line in open(str(path) + ".fai"):
            name, length, offset, bases, width = line.split("\t")[:5]
            self.index[name] = (int(length), int(offset), int(bases), int(width))

    def get(self, chrom: str, start: int, end: int) -> str:
        """Bases start..end (1-based, inclusive), upper case; clipped to the chromosome."""
        length, offset, bases, width = self.index[chrom]
        start, end = max(1, start), min(length, end)
        if end < start:
            return ""
        a = offset + (start - 1) // bases * width + (start - 1) % bases
        b = offset + (end - 1) // bases * width + (end - 1) % bases
        self.fh.seek(a)
        return self.fh.read(b - a + 1).replace(b"\n", b"").replace(b"\r", b"").decode().upper()


def _revcomp(s: str) -> str:
    return s.translate(str.maketrans("ACGTN", "TGCAN"))[::-1]


def _spliced(fa: Fasta, chrom: str, strand: str, iv: list) -> str:
    seq = "".join(fa.get(chrom, s, e) for s, e in sorted(iv))
    return _revcomp(seq) if strand == "-" else seq


def _gc(s: str):
    return (s.count("G") + s.count("C")) / len(s) if s else None


def _cpg_oe(s: str):
    c, g = s.count("C"), s.count("G")
    return s.count("CG") * len(s) / (c * g) if c and g else None


def build(gtf: Path, fasta: Path | None, keep: set[str] | None, bidir_bp: int = 1000, neighbour_kb: float = 100.0,
          max_neighbours: int = 20) -> dict:
    genes = read_gtf(gtf)
    chosen: dict[str, dict] = {}
    for gid in sorted(genes):
        g = genes[gid]
        rep = representative(g)
        if rep is None:
            continue
        name = g["name"]
        prev = chosen.get(name)
        if prev is None or (_chrom_rank(g["chrom"]), gid) < (_chrom_rank(prev["gene"]["chrom"]), prev["gid"]):
            chosen[name] = {"gid": gid, "gene": g, "tid": rep[0], "tr": rep[1]}
    for c in chosen.values():
        ex = c["tr"]["exons"]
        c["tss"] = min(s for s, _ in ex) if c["gene"]["strand"] == "+" else max(e for _, e in ex)
    by_chrom = collections.defaultdict(list)
    for name, c in chosen.items():
        by_chrom[c["gene"]["chrom"]].append((c["tss"], name))
    for v in by_chrom.values():
        v.sort()
    fa = Fasta(fasta) if fasta else None
    out_names = sorted(n for n in chosen if keep is None or n in keep)
    keep_set = set(out_names)
    rows, loci, bidir, neigh = {}, {}, {}, {}
    for name in out_names:
        c = chosen[name]
        g, tr, chrom, strand, tss = c["gene"], c["tr"], c["gene"]["chrom"], c["gene"]["strand"], c["tss"]
        exons = sorted(tr["exons"])
        tlen = sum(e - s + 1 for s, e in exons)
        span = max(e for _, e in exons) - min(s for s, _ in exons) + 1
        cds = sorted(tr["cds"])
        utr5 = utr3 = []
        if cds:
            lo, hi = min(s for s, _ in cds), max(e for _, e in cds)
            before = [iv for iv in tr["utr"] if iv[1] < lo]
            after = [iv for iv in tr["utr"] if iv[0] > hi]
            utr5, utr3 = (before, after) if strand == "+" else (after, before)
        tsss = by_chrom[chrom]
        i = bisect.bisect_left(tsss, (tss, name))
        others = [(abs(t - tss), n, t) for t, n in tsss[max(0, i - 400):i + 400] if n != name]
        others.sort()
        row = {"gene_span_kb": (g["end"] - g["start"] + 1) / 1e3, "n_transcripts": len(g["transcripts"]),
               "n_exons": len(exons), "transcript_length": tlen,
               "cds_length": sum(e - s + 1 for s, e in cds) if cds else None,
               "utr5_length": sum(e - s + 1 for s, e in utr5) if cds else None,
               "utr3_length": sum(e - s + 1 for s, e in utr3) if cds else None,
               "intron_length_kb": (span - tlen) / 1e3,
               "nearest_tss_kb": others[0][0] / 1e3 if others else None,
               "n_tss_within_100kb": sum(1 for d, _, _ in others if d <= 100_000)}
        if fa is not None and chrom in fa.index:
            prom = fa.get(chrom, tss - 500, tss + 500)
            row.update(gc_promoter=_gc(prom), cpg_oe_promoter=_cpg_oe(prom))
            if cds:
                cseq = _spliced(fa, chrom, strand, cds)
                u5 = _spliced(fa, chrom, strand, utr5)
                row.update(gc_cds=_gc(cseq), gc_utr3=_gc(_spliced(fa, chrom, strand, utr3)),
                           n_upstream_atg=u5.count("ATG"))
                prot = "".join(CODON.get(cseq[j:j + 3], "X") for j in range(0, len(cseq) - len(cseq) % 3, 3))
                prot = prot.rstrip("*")
                counts = collections.Counter(prot)
                n = sum(counts[a] for a in AMINO)
                if n:
                    row.update({f"aa_{a}": counts[a] / n for a in AMINO})
        rows[name] = [None if row.get(col) is None else round(float(row[col]), 6) for col in COLUMNS]
        loci[name] = [chrom, tss, strand]
        bidir[name] = sorted(n for d, n, _ in others if d <= bidir_bp and chosen[n]["gene"]["strand"] != strand
                             and n in keep_set)
        neigh[name] = [[n, d] for d, n, _ in others if d <= neighbour_kb * 1e3 and n in keep_set][:max_neighbours]
    description = (f"Per-gene molecular annotation from the reference genome and its annotation ({Path(gtf).name}"
                   f"{', ' + Path(fasta).name if fasta else ''}); no expression or perturbation data. One transcript "
                   f"per gene (CCDS with the longest coding sequence). Columns: {UNITS}. Also loci (chromosome, TSS, "
                   f"strand), bidirectional (genes whose TSS is on the other strand within {bidir_bp} bp: shared "
                   f"promoters, which CRISPRi/CRISPRa at one TSS can also hit) and neighbours (genes within "
                   f"{neighbour_kb:g} kb, nearest first, with TSS distance in bp).")
    return {"description": description, "columns": COLUMNS, "genes": rows, "loci": loci, "bidirectional": bidir,
            "neighbours": neigh, "source": {"gtf": Path(gtf).name, "fasta": Path(fasta).name if fasta else None,
                                            "n_genes_annotated": len(chosen)}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--gtf", required=True)
    ap.add_argument("--fasta", help="indexed genome FASTA (a .fai next to it); without it no sequence columns")
    ap.add_argument("--genes-from", help="bundle or public directory whose public.npz genes the output keeps")
    ap.add_argument("--out", required=True)
    ap.add_argument("--bidir-bp", type=int, default=1000)
    ap.add_argument("--neighbour-kb", type=float, default=100.0)
    args = ap.parse_args(argv)
    keep = None
    if args.genes_from:
        keep = {str(g) for g in np.load(Path(args.genes_from) / "public.npz", allow_pickle=False)["genes"]}
    table = build(Path(args.gtf), Path(args.fasta) if args.fasta else None, keep, args.bidir_bp, args.neighbour_kb)
    if keep is not None:
        table["unmatched"] = sorted(keep - set(table["genes"]))
    Path(args.out).write_text(json.dumps(table, separators=(",", ":")))
    n_unmatched = len(table.get("unmatched", []))
    print(f"{len(table['genes'])} genes written to {args.out}" + (f"; {n_unmatched} bundle genes unmatched"
                                                                   if keep is not None else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
