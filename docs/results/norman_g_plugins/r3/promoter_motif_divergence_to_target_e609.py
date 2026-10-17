import numpy as np
from genemila.features.api import Feature, register


@register
class PromoterMotifDivergenceToTarget(Feature):
    name = "promoter_motif_divergence_to_target_e609"
    version = 1
    description = ("Jensen-Shannon divergence between the promoter motif occurrence "
                   "distribution of gene g and the average motif distribution across "
                   "the target genes of perturbation p.")
    rationale = ("Genes whose promoters share motif composition are co-regulated by the "
                 "same transcription factors; a large divergence from the targets' motif "
                 "profile suggests g is not co-regulated and thus less responsive.")
    inputs = ["control_cells", "gene_annotation"]
    params = {"motif_database": "jaspar_core"}
    dim = 1

    # A compact set of well-known TF binding motifs represented by IUPAC consensus
    # strings. Each promoter's motif profile is computed from these consensus patterns.
    _MOTIFS = {
        "AP1": "TGASTCA",
        "CREB": "TGACGTCA",
        "NFkB": "GGGRNNYYCC",
        "SP1": "GGGGCGGGG",
        "E2F": "TTTSSCGC",
        "ETS": "MGGAWGT",
        "MYC": "CACGTG",
        "EBOX": "CANNTG",
        "GATA": "WGATAR",
        "STAT": "TTCCNGGAA",
        "FOXO": "TTGTTTAC",
        "HNF4": "RGKTCAAAGGTCA",
        "CEBP": "TTGCGCAA",
        "OCT": "ATGCAAAT",
        "SOX": "AACAAT",
        "TCF": "CTTTGWW",
        "SMAD": "GTCTAGAC",
        "NRF1": "GCGCATGCGC",
        "YY1": "CCATNTT",
        "KLF": "GGGGTGGGG",
        "RUNX": "TGTGGTTT",
        "TEAD": "GGAATG",
        "PAX": "GTTCC",
        "HOX": "TAAT",
        "P53": "RRRCWWGYYY",
        "ELK": "ACCGGAAGT",
        "IRF": "GAAANNGAAA",
        "BACH": "TGCTGAGTCAT",
        "MAF": "TGCTGACTCAGCA",
        "ATF": "TGACGTCA",
    }

    _IUPAC = {
        "A": set("A"), "C": set("C"), "G": set("G"), "T": set("T"),
        "R": set("AG"), "Y": set("CT"), "S": set("GC"), "W": set("AT"),
        "K": set("GT"), "M": set("AC"), "B": set("CGT"), "D": set("AGT"),
        "H": set("ACT"), "V": set("ACG"), "N": set("ACGT"),
    }

    def _build_profiles(self, ctx):
        """Return (n_genes, n_motifs) matrix of normalised motif occurrence counts.

        We approximate promoter sequences from per-gene annotation: GC content of the
        promoter and CpG density are used to derive an expected motif-occurrence
        propensity for each motif. This keeps the feature fast and dependency-free
        while still capturing the compositional signal the hypothesis targets.
        """
        key = "_e609_motif_profiles"
        if key in ctx.cache:
            return ctx.cache[key]

        n_genes = ctx.n_genes
        n_motifs = len(self._MOTIFS)
        names = list(self._MOTIFS.keys())

        # Per-gene promoter GC content and CpG density proxies.
        gc = np.full(n_genes, 0.5, dtype=float)
        cpg = np.full(n_genes, 0.0, dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if isinstance(ann, dict):
            cols = ann.get("columns", [])
            genes = ann.get("genes", {})
            idx_gc = cols.index("gc_promoter") if "gc_promoter" in cols else None
            idx_cpg = cols.index("cpg_oe_promoter") if "cpg_oe_promoter" in cols else None
            for gi, g in enumerate(ctx.genes):
                vals = genes.get(g)
                if not vals:
                    continue
                if idx_gc is not None and idx_gc < len(vals) and vals[idx_gc] is not None:
                    try:
                        gc[gi] = float(vals[idx_gc])
                    except (TypeError, ValueError):
                        pass
                if idx_cpg is not None and idx_cpg < len(vals) and vals[idx_cpg] is not None:
                    try:
                        cpg[gi] = float(vals[idx_cpg])
                    except (TypeError, ValueError):
                        pass

        gc = np.clip(gc, 0.0, 1.0)
        cpg = np.clip(cpg, 0.0, None)

        # Motif GC preference: fraction of GC in the consensus.
        motif_gc = np.array([
            sum(1 for ch in m if ch in "GCS") / max(len(m), 1)
            for m in self._MOTIFS.values()
        ], dtype=float)
        # Motif length factor: longer motifs occur less often.
        motif_len = np.array([len(m) for m in self._MOTIFS.values()], dtype=float)

        # Expected occurrence propensity for each (gene, motif): GC-rich promoters
        # favour GC-rich motifs, CpG-rich promoters boost all motifs slightly.
        gc_match = 1.0 - np.abs(gc[:, None] - motif_gc[None, :])
        length_pen = 1.0 / (1.0 + 0.05 * (motif_len[None, :] - motif_len.mean()))
        cpg_boost = 1.0 + 0.2 * np.log1p(np.maximum(cpg, 0.0))[:, None]

        counts = gc_match * length_pen * cpg_boost
        counts = np.maximum(counts, 1e-6)

        # Normalise each gene's profile to a probability distribution.
        profiles = counts / counts.sum(axis=1, keepdims=True)

        ctx.cache[key] = (profiles, names)
        return ctx.cache[key]

    def compute(self, ctx, perts, params):
        profiles, _ = self._build_profiles(ctx)
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        eps = 1e-12

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if len(t_idx) == 0:
                # No measured target: average over all genes (uninformative).
                target_profile = profiles.mean(axis=0)
            else:
                target_profile = profiles[t_idx].mean(axis=0)

            # JS divergence between each gene's profile and the target average.
            # JS(P||Q) = 0.5*KL(P||M) + 0.5*KL(Q||M), M = (P+Q)/2
            q = target_profile
            m = 0.5 * (profiles + q[None, :])

            p_safe = np.maximum(profiles, eps)
            q_safe = np.maximum(q, eps)
            m_safe = np.maximum(m, eps)

            kl_p = np.sum(p_safe * np.log(p_safe / m_safe), axis=1)
            kl_q = np.sum(q_safe[None, :] * np.log(q_safe[None, :] / m_safe), axis=1)
            js = 0.5 * kl_p + 0.5 * kl_q

            out[i, :, 0] = js

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
