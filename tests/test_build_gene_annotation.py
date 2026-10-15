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
    """chr1 (100 bp per line): PLUS on + with a 5' UTR holding one ATG, a 9-nt CDS ATG GCC AAA (M A K) and a 3' UTR;
    MINUS on - whose TSS is 300 bp from PLUS's (a shared promoter); FAR on + 50 kb away; chr2: a second copy of the
    symbol PLUS, which the chr1 copy outranks."""
    seq = ["N"] * 60_000
    def put(pos, s):  # 1-based
        seq[pos - 1:pos - 1 + len(s)] = list(s)
    put(1000, "CCATGCC")                     # 5' UTR 1000-1006 (one ATG)
    put(1007, "ATGGCCAAA")                   # CDS 1007-1015
    put(1016, "TAGGGGCCCC")                  # stop + 3' UTR 1019-1025 (UTR after stop codon)
    chrom1 = "".join("A" if c == "N" else c for c in seq)
    fa = tmp / "g.fa"
    lines = [">chr1"] + [chrom1[i:i + 100] for i in range(0, len(chrom1), 100)] + [">chr2"] + ["A" * 100] * 50
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
        ("chr1", "UTR", 1019, 1025, "+", _attrs("G1", "PLUS", "protein_coding", "T1", "protein_coding")),
        ("chr1", "gene", 500, 700, "-", _attrs("G2", "MINUS", "lncRNA")),
        ("chr1", "transcript", 500, 700, "-", _attrs("G2", "MINUS", "lncRNA", "T2", "lncRNA", ["basic"])),
        ("chr1", "exon", 500, 700, "-", _attrs("G2", "MINUS", "lncRNA", "T2", "lncRNA", ["basic"])),
        ("chr1", "gene", 51000, 51100, "+", _attrs("G3", "FAR", "lncRNA")),
        ("chr1", "transcript", 51000, 51100, "+", _attrs("G3", "FAR", "lncRNA", "T3", "lncRNA", ["basic"])),
        ("chr1", "exon", 51000, 51100, "+", _attrs("G3", "FAR", "lncRNA", "T3", "lncRNA", ["basic"])),
        ("chr2", "gene", 100, 200, "+", _attrs("G4", "PLUS", "lncRNA")),
        ("chr2", "transcript", 100, 200, "+", _attrs("G4", "PLUS", "lncRNA", "T4", "lncRNA", ["basic"])),
        ("chr2", "exon", 100, 200, "+", _attrs("G4", "PLUS", "lncRNA", "T4", "lncRNA", ["basic"])),
    ]
    gtf.write_text("##toy\n" + "".join(f"{c}\tT\t{t}\t{s}\t{e}\t.\t{st}\t.\t{a}\n" for c, t, s, e, st, a in rows))
    return gtf, fa


def test_known_values(tmp_path):
    gtf, fa = _toy(tmp_path)
    t = bga.build(gtf, fa, None)
    col = {c: i for i, c in enumerate(t["columns"])}
    plus = t["genes"]["PLUS"]
    assert t["loci"]["PLUS"] == ["chr1", 1000, "+"] and t["loci"]["MINUS"] == ["chr1", 700, "-"]
    assert plus[col["cds_length"]] == 9 and plus[col["utr5_length"]] == 7 and plus[col["utr3_length"]] == 7
    assert plus[col["n_upstream_atg"]] == 1
    assert plus[col["aa_M"]] == plus[col["aa_A"]] == plus[col["aa_K"]] == round(1 / 3, 6)
    assert plus[col["gc_cds"]] == round(4 / 9, 6)  # ATGGCCAAA: G, G, C, C
    assert t["bidirectional"]["PLUS"] == ["MINUS"] and t["bidirectional"]["MINUS"] == ["PLUS"]
    assert t["genes"]["MINUS"][col["cds_length"]] is None and t["bidirectional"]["FAR"] == []
    assert t["neighbours"]["PLUS"] == [["MINUS", 300], ["FAR", 50000]]
    assert plus[col["n_tss_within_100kb"]] == 2 and plus[col["nearest_tss_kb"]] == 0.3


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
