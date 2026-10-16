import numpy as np
from genemila.features.api import Feature, register


@register
class PromoterSimilarityTargetG(Feature):
    name = "promoter_similarity_target_g_e564"
    version = 1
    description = "Mean cosine similarity between promoter feature vectors (gc_promoter, cpg_oe_promoter) of perturbation targets and gene g."
    rationale = "Genes with similar promoters may be co-regulated, so activating targets may affect g through shared transcriptional machinery."
    inputs = ["knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        ka = ctx.knowledge("gene_annotation")
        if not ka:
            return out
        genes = ka.get("genes", {})
        cols = ka.get("columns", [])
        try:
            i_gc = cols.index("gc_promoter")
            i_cpg = cols.index("cpg_oe_promoter")
        except ValueError:
            return out

        n_genes = ctx.n_genes
        vecs = np.zeros((n_genes, 2), dtype=float)
        valid = np.zeros(n_genes, dtype=bool)
        for gi, g in enumerate(ctx.genes):
            vals = genes.get(g)
            if vals is None:
                continue
            try:
                a = vals[i_gc]
                b = vals[i_cpg]
            except Exception:
                continue
            if a is None or b is None:
                continue
            try:
                a = float(a)
                b = float(b)
            except Exception:
                continue
            if not (np.isfinite(a) and np.isfinite(b)):
                continue
            vecs[gi, 0] = a
            vecs[gi, 1] = b
            valid[gi] = True

        norms = np.linalg.norm(vecs, axis=1)
        norms_safe = np.where(norms > 0, norms, 1.0)
        vecs_n = vecs / norms_safe[:, None]
        zero = norms <= 0

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            idxs = []
            for tg in tgenes:
                gi = ctx.gene_index.get(tg)
                if gi is not None and valid[gi] and not zero[gi]:
                    idxs.append(gi)
            if not idxs:
                continue
            v = vecs_n[idxs]  # (t, 2)
            sims = v @ vecs_n.T  # (t, n_genes)
            mean_sims = sims.mean(axis=0)
            mask = valid & (~zero)
            row = np.zeros(n_genes, dtype=float)
            row[mask] = mean_sims[mask]
            out[i, :, 0] = row
        return out
