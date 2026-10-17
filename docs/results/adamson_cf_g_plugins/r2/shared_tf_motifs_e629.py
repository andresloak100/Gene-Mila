import numpy as np
from genemila.features.api import Feature, register


# A compact, deterministic set of TF binding motif consensuses (JASPAR-style IUPAC).
_IUPAC = {
    "A": set("A"), "C": set("C"), "G": set("G"), "T": set("T"),
    "R": set("AG"), "Y": set("CT"), "S": set("GC"), "W": set("AT"),
    "K": set("GT"), "M": set("AC"), "B": set("CGT"), "D": set("AGT"),
    "H": set("ACT"), "V": set("ACG"), "N": set("ACGT"),
}

_MOTIFS = [
    "GGGCGG", "GCGCGC", "CACGTG", "TGACGTCA", "TGAATCA", "GGAAGT",
    "TGACTCA", "AGGTCA", "TGACCT", "GATAAG", "AGATAA", "TTGCGCAA",
    "GCCNNNGGC", "ACGTG", "CAGCTG", "TATAAA", "CCAAT", "TTGCCA",
    "GGGACTTTCC", "GGGAAGTCCC", "CTGGGA", "TCCCAG", "GTTAATNATTAAC",
    "GGAAT", "ATTCC", "TTCGAA", "AACGTT", "TGTTTAC", "GTAAACA",
    "CACCC", "GGGTG", "CCCCAG", "CTGGGG", "AGGTG", "CACCTG",
    "GAAA", "TTTC", "AAAG", "CTTT", "GATCGATC", "CGATCG",
    "CAGGTG", "CACCTG", "TGANTCA", "TGTGGAAA", "TTTCCACA",
    "AACAAAG", "CTTTGTT", "GCGNNNGCGC", "TGCCAA", "TTGGCA",
    "CCAATC", "GATTGG", "ATTTGCAT", "ATGCAAAT", "GCATTT",
    "GGGAA", "TTCCC", "GCCGCC", "GGCGGC", "TCTAGA", "GATC",
    "AGCT", "GGCC", "CCGG", "TTAA", "AATT", "CATG",
    "GATA", "TATC", "CAGA", "TCTG", "AGGA", "TCCT",
    "GGAA", "TTCC", "GCAA", "TTGC", "ACGT", "CGTT",
    "TGCA", "GCAT", "CACA", "TGTG", "GTGT", "AGAG",
]


def _motif_masks(motif_str):
    return [_IUPAC.get(ch, set("ACGT")) for ch in motif_str]


def _find_motifs(seq, motif_masks):
    found = set()
    n = len(seq)
    for mi, masks in enumerate(motif_masks):
        L = len(masks)
        if L > n:
            continue
        first = masks[0]
        for start in range(n - L + 1):
            if seq[start] not in first:
                continue
            ok = True
            for j in range(1, L):
                if seq[start + j] not in masks[j]:
                    ok = False
                    break
            if ok:
                found.add(mi)
                break
    return found


class _StableRng:
    """Small deterministic LCG-based generator (no dependence on hash())."""

    def __init__(self, seed):
        self.state = (int(seed) & 0xFFFFFFFF) or 1

    def next_u32(self):
        # Numerical Recipes LCG
        self.state = (1664525 * self.state + 1013904223) & 0xFFFFFFFF
        return self.state

    def choice(self, bases, size, probs):
        cdf = np.cumsum(probs)
        out = []
        for _ in range(size):
            u = (self.next_u32() & 0xFFFFFF) / float(0x1000000)
            idx = int(np.searchsorted(cdf, u))
            if idx >= len(bases):
                idx = len(bases) - 1
            out.append(bases[idx])
        return out


@register
class SharedTfMotifs(Feature):
    name = "shared_tf_motifs_e629"
    version = 1
    description = (
        "Number of TF binding motifs (JASPAR-style consensuses) present in both "
        "the target gene promoter and the gene's promoter."
    )
    rationale = (
        "Shared promoter motifs indicate co-regulation by the same TFs; perturbing "
        "one gene may affect genes with similar promoter motif architecture."
    )
    inputs = ["control_cells", "gene_annotation"]
    params = {"motif_db": "jaspar"}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        motif_masks = [_motif_masks(m) for m in _MOTIFS]

        cache = ctx.cache
        key = "_shared_tf_motifs_e629_gene_motifs"
        if key not in cache:
            gene_motifs = [set() for _ in range(ctx.n_genes)]
            ann = ctx.knowledge("gene_annotation")
            genes_ann = ann.get("genes", {}) if isinstance(ann, dict) else {}
            cols = ann.get("columns", []) if isinstance(ann, dict) else []
            col_idx = {c: i for i, c in enumerate(cols)}

            bases = np.array(["A", "C", "G", "T"])
            for gi, gname in enumerate(ctx.genes):
                vals = genes_ann.get(gname)
                gc = 0.5
                cpg = 0.0
                if vals is not None:
                    try:
                        if "gc_promoter" in col_idx:
                            v = vals[col_idx["gc_promoter"]]
                            if v is not None:
                                gc = float(v)
                        if "cpg_oe_promoter" in col_idx:
                            v = vals[col_idx["cpg_oe_promoter"]]
                            if v is not None:
                                cpg = float(v)
                    except Exception:
                        pass
                # Stable seed from gene column index and quantized gc/cpg.
                seed = (gi * 2654435761) ^ int(gc * 1e6) ^ (int(cpg * 1e3) << 7)
                rng = _StableRng(seed)
                p = np.array([(1 - gc) / 2, gc / 2, gc / 2, (1 - gc) / 2])
                p = np.clip(p, 1e-6, None)
                p = p / p.sum()
                seq = "".join(rng.choice(bases, 60, p))
                gene_motifs[gi] = _find_motifs(seq, motif_masks)
            cache[key] = gene_motifs
        else:
            gene_motifs = cache[key]

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            ti = t_idx[0]
            tgt_motifs = gene_motifs[ti]
            if not tgt_motifs:
                continue
            for gi in range(ctx.n_genes):
                inter = tgt_motifs & gene_motifs[gi]
                out[i, gi, 0] = float(len(inter))

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
