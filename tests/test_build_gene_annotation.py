"""tools/build_gene_annotation.py on a two-chromosome toy genome with known answers."""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import build_gene_annotation as bga  # noqa: E402


def _attrs(gid, name, gtype, tid=None, ttype=None, tags=()):
    a = f'gene_id "{gid}"; gene_type "{gtype}"; gene_name "{name}";'
    if tid:
        a += f' transcript_id "{tid}"; transcript_type "{ttype}";' + "".join(f' tag "{t}";' for t in tags)
    return a


def _toy(tmp: Path):
    """chr1 (100 bp per line): PLUS on + with a 5' UTR holding one ATG, a 9-nt CDS ATG GCC AAA (M A K), the stop TAG
    and a 3' UTR; as in GENCODE, the 3' UTR feature starts at the stop codon. MINUS on - whose TSS is 300 bp from
    PLUS's (a shared promoter); FAR on + 50 kb away; chr2: a second copy of the symbol PLUS, which the chr1 copy
    outranks, and RCODE, a coding gene on - with two exons (see _RCODE)."""
    chroms = {"chr1": ["A"] * 60_000, "chr2": ["A"] * 5000}
    def put(chrom, pos, s):  # 1-based
        chroms[chrom][pos - 1:pos - 1 + len(s)] = list(s)
    put("chr1", 1000, "CCATGCC")                     # 5' UTR 1000-1006 (one ATG)
    put("chr1", 1007, "ATGGCCAAA")                   # CDS 1007-1015
    put("chr1", 1016, "TAGGGGCCCC")                  # stop 1016-1018 + 3' UTR 1019-1025
    # RCODE's message (5'->3'): 5' UTR CATGCA (one ATG), CDS ATG|CCC TGG (M P W, split by a 10-bp intron),
    # stop TAA, 3' UTR GCAT. On - the message reads from high to low coordinates: exon 1 is 2024-2032 (its first 9
    # nt), exon 2 is 2001-2013 (the other 13).
    mrna = "CATGCA" + "ATGCCCTGG" + "TAA" + "GCAT"
    put("chr2", 2024, bga._revcomp(mrna[:9]))
    put("chr2", 2001, bga._revcomp(mrna[9:]))
    chrom1, chrom2 = "".join(chroms["chr1"]), "".join(chroms["chr2"])
    fa = tmp / "g.fa"
    lines = ([">chr1"] + [chrom1[i:i + 100] for i in range(0, len(chrom1), 100)]
             + [">chr2"] + [chrom2[i:i + 100] for i in range(0, len(chrom2), 100)])
    fa.write_text("\n".join(lines) + "\n")
    off1 = len(">chr1\n")
    off2 = off1 + len(chrom1) + len(chrom1) // 100 + len(">chr2\n")
    Path(str(fa) + ".fai").write_text(f"chr1\t{len(chrom1)}\t{off1}\t100\t101\nchr2\t5000\t{off2}\t100\t101\n")
    gtf = tmp / "a.gtf"
    rows = [
        ("chr1", "gene", 1000, 1025, "+", _attrs("G1", "PLUS", "protein_coding")),
        ("chr1", "transcript", 1000, 1025, "+", _attrs("G1", "PLUS", "protein_coding", "T1", "protein_coding", ["CCDS", "basic"])),
        ("chr1", "exon", 1000, 1025, "+", _attrs("G1", "PLUS", "protein_coding", "T1", "protein_coding", ["CCDS"])),
        ("chr1", "UTR", 1000, 1006, "+", _attrs("G1", "PLUS", "protein_coding", "T1", "protein_coding")),
        ("chr1", "CDS", 1007, 1015, "+", _attrs("G1", "PLUS", "protein_coding", "T1", "protein_coding")),
        ("chr1", "UTR", 1016, 1025, "+", _attrs("G1", "PLUS", "protein_coding", "T1", "protein_coding")),
        ("chr1", "stop_codon", 1016, 1018, "+", _attrs("G1", "PLUS", "protein_coding", "T1", "protein_coding")),
        ("chr1", "gene", 500, 700, "-", _attrs("G2", "MINUS", "lncRNA")),
        ("chr1", "transcript", 500, 700, "-", _attrs("G2", "MINUS", "lncRNA", "T2", "lncRNA", ["basic"])),
        ("chr1", "exon", 500, 700, "-", _attrs("G2", "MINUS", "lncRNA", "T2", "lncRNA", ["basic"])),
        ("chr1", "gene", 51000, 51100, "+", _attrs("G3", "FAR", "lncRNA")),
        ("chr1", "transcript", 51000, 51100, "+", _attrs("G3", "FAR", "lncRNA", "T3", "lncRNA", ["basic"])),
        ("chr1", "exon", 51000, 51100, "+", _attrs("G3", "FAR", "lncRNA", "T3", "lncRNA", ["basic"])),
        ("chr2", "gene", 100, 200, "+", _attrs("G4", "PLUS", "lncRNA")),
        ("chr2", "transcript", 100, 200, "+", _attrs("G4", "PLUS", "lncRNA", "T4", "lncRNA", ["basic"])),
        ("chr2", "exon", 100, 200, "+", _attrs("G4", "PLUS", "lncRNA", "T4", "lncRNA", ["basic"])),
    ] + [("chr2", t, s, e, "-", _attrs("G5", "RCODE", "protein_coding", "T5", "protein_coding", ["CCDS", "basic"]))
         for t, s, e in [("gene", 2001, 2032), ("transcript", 2001, 2032), ("exon", 2024, 2032), ("exon", 2001, 2013),
                         ("UTR", 2027, 2032), ("CDS", 2024, 2026), ("CDS", 2008, 2013), ("UTR", 2001, 2007),
                         ("stop_codon", 2005, 2007)]]
    gtf.write_text("##toy\n" + "".join(f"{c}\tT\t{t}\t{s}\t{e}\t.\t{st}\t.\t{a}\n" for c, t, s, e, st, a in rows))
    return gtf, fa


def test_known_values(tmp_path):
    gtf, fa = _toy(tmp_path)
    t = bga.build(gtf, fa, None)
    col = {c: i for i, c in enumerate(t["columns"])}
    plus = t["genes"]["PLUS"]
    assert t["loci"]["PLUS"] == ["chr1", 1000, "+"] and t["loci"]["MINUS"] == ["chr1", 700, "-"]
    assert plus[col["cds_length"]] == 9 and plus[col["utr5_length"]] == 7 and plus[col["utr3_length"]] == 7
    assert plus[col["gc_utr3"]] == 1.0  # GGGCCCC, without the stop codon TAG
    assert plus[col["n_upstream_atg"]] == 1
    assert plus[col["aa_M"]] == plus[col["aa_A"]] == plus[col["aa_K"]] == round(1 / 3, 6)
    assert plus[col["gc_cds"]] == round(4 / 9, 6)  # ATGGCCAAA: G, G, C, C
    assert t["bidirectional"]["PLUS"] == ["MINUS"] and t["bidirectional"]["MINUS"] == ["PLUS"]
    assert t["genes"]["MINUS"][col["cds_length"]] is None and t["bidirectional"]["FAR"] == []
    assert t["neighbours"]["PLUS"] == [["MINUS", 300], ["FAR", 50000]]
    assert plus[col["n_tss_within_100kb"]] == 2 and plus[col["nearest_tss_kb"]] == 0.3
    r = t["genes"]["RCODE"]
    assert t["loci"]["RCODE"] == ["chr2", 2032, "-"]
    assert r[col["transcript_length"]] == 22 and r[col["n_exons"]] == 2 and r[col["intron_length_kb"]] == 0.01
    assert r[col["cds_length"]] == 9 and r[col["utr5_length"]] == 6 and r[col["utr3_length"]] == 4
    assert r[col["n_upstream_atg"]] == 1 and r[col["gc_utr3"]] == 0.5  # GCAT
    assert r[col["gc_cds"]] == round(6 / 9, 6)  # ATGCCCTGG
    assert r[col["aa_M"]] == r[col["aa_P"]] == r[col["aa_W"]] == round(1 / 3, 6) and r[col["aa_K"]] == 0
    assert len(t["source"]["gtf_sha256"]) == len(t["source"]["fasta_sha256"]) == 64


def test_mitochondrial_code():
    # TGA is W and ATA is M in the vertebrate mitochondrial code, and AGG is a stop; in the standard code TGA stops.
    assert bga.translate("ATGTGAATAAGG", "chrM") == bga.translate("ATGTGAATAAGG", "MT") == "MWM"
    assert bga.translate("ATGTGAATAAGG", "chr1") == "M*IR"


def test_bundle_restriction_and_cli(tmp_path):
    gtf, fa = _toy(tmp_path)
    pub = tmp_path / "pub"
    pub.mkdir()
    np.savez(pub / "public.npz", genes=np.array(["PLUS", "FAR", "NOPE"]))
    out = tmp_path / "ga.json"
    assert bga.main(["--gtf", str(gtf), "--fasta", str(fa), "--genes-from", str(pub), "--out", str(out)]) == 0
    t = json.loads(out.read_text())
    assert sorted(t["genes"]) == ["FAR", "PLUS"] and t["unmatched"] == ["NOPE"]
    assert t["neighbours"]["PLUS"] == [["FAR", 50000]] and t["bidirectional"]["PLUS"] == []
    assert t["description"].startswith("Per-gene annotation") and len(t["description"]) < 900
