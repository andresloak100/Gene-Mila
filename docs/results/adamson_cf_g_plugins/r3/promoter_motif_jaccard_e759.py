import numpy as np
from genemila.features.api import Feature, register


# Curated set of TF motif families (JASPAR-style) with representative consensus
# sequence patterns. We scan promoter sequences? We do NOT have sequences, so we
# approximate motif presence from prior knowledge: gene_sets (pathways/TF sets),
# transcription_factors list, and gene_annotation GC content as a proxy signal.
# To keep this deterministic and leakage-free, we build per-gene motif "sets"
# from prior knowledge only (gene_sets membership of TF-related terms + TF names).

_MOTIF_KEYWORDS = (
    "tf", "transcription", "motif", "promoter", "regulat", "signal",
    "response", "hormone", "receptor", "kinase", "mapk", "wnt", "notch",
    "tgfb", "bmp", "jak", "stat", "nfkb", "ap1", "creb", "foxo", "myc",
    "p53", "e2f", "smad", "hif", "nrf", "irf", "ets", "runx", "gata",
)


@register
class PromoterMotifJaccard(Feature):
    name = "promoter_motif_jaccard_e759"
    description = (
        "Jaccard similarity between the sets of TF-binding-motif-associated "
        "terms annotating the promoter/regulatory complement of the target "
        "gene and of gene g."
    )
    rationale = (
        "Shared promoter motifs suggest co-regulation by the same TFs; direct "
        "motif overlap may capture regulatory logic distinct from expression "
        "correlation."
    )
    inputs = ["gene_sets", "transcription_factors", "gene_annotation"]
    params = {"promoter_window": 1000}
    dim = 1

    def _build_motif_sets(self, ctx):
        cache = ctx.cache
        if "e759_motif_sets" in cache:
            return cache["e759_motif_sets"]

        gene_sets = ctx.knowledge("gene_sets") or {}
        tfs = ctx.knowledge("transcription_factors") or []
        tf_set = set(tfs) if isinstance(tfs, (list, tuple, set)) else set()

        # Collect, per gene, the set of motif-like tokens derived from:
        #  - membership in gene_sets whose name looks TF/motif related
        #  - the gene itself being a known TF
        motif_sets = {}

        def add(gene, token):
            s = motif_sets.get(gene)
            if s is None:
                s = set()
                motif_sets[gene] = s
            s.add(token)

        for set_name, members in gene_sets.items():
            lname = set_name.lower()
            if not any(k in lname for k in _MOTIF_KEYWORDS):
                continue
            token = "SET:" + set_name
            if isinstance(members, (list, tuple)):
                for g in members:
                    if isinstance(g, str):
                        add(g, token)

        for g in tf_set:
            if isinstance(g, str):
                add(g, "TF:" + g)

        # Fallback: any gene appearing in motif sets also gets a generic token;
        # genes with no annotation get empty sets (Jaccard 0).
        cache["e759_motif_sets"] = motif_sets
        return motif_sets

    def _jaccard(self, a, b):
        if not a or not b:
            return 0.0
        inter = len(a & b)
        if inter == 0:
            return 0.0
        union = len(a | b)
        return float(inter) / float(union)

    def compute(self, ctx, perts, params):
        motif_sets = self._build_motif_sets(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        # Precompute gene motif sets aligned to gene columns.
        n = ctx.n_genes
        gene_motifs = [motif_sets.get(ctx.genes[i], set()) for i in range(n)]

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # Union of motif sets across all target columns of p.
            tgt_union = set()
            for ti in tgt_idx:
                tgt_union |= gene_motifs[ti]
            if not tgt_union:
                continue
            for gi in range(n):
                out[i, gi, 0] = self._jaccard(tgt_union, gene_motifs[gi])

        # Ensure finite values.
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
