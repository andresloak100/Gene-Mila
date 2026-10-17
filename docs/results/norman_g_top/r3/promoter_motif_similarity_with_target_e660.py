import numpy as np
from genemila.features.api import Feature, register


@register
class PromoterMotifSimilarityWithTarget(Feature):
    name = "promoter_motif_similarity_with_target_e660"
    version = 1
    description = (
        "Cosine similarity between gene g's promoter feature vector and the mean "
        "promoter feature vector of perturbation p's target genes."
    )
    rationale = (
        "Promoter sequence composition (GC content, CpG islands, upstream ATG "
        "density) is a proxy for shared promoter motifs and regulatory context; "
        "genes with similar promoters may be co-regulated and respond similarly "
        "to perturbation of their targets."
    )
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    # Columns of gene_annotation.genes used as the promoter feature vector.
    _COLS = ["gc_promoter", "cpg_oe_promoter", "n_upstream_atg"]

    def _build_vectors(self, ctx):
        cached = ctx.cache.get("_e660_prom_vecs")
        if cached is not None:
            return cached

        ann = ctx.knowledge("gene_annotation")
        n = ctx.n_genes
        vecs = np.zeros((n, len(self._COLS)), dtype=float)
        present = np.zeros(n, dtype=bool)

        if ann is not None and isinstance(ann, dict):
            genes = ann.get("genes", {}) or {}
            cols = ann.get("columns", []) or []
            # Map our desired column names to indices in the annotation table.
            col_idx = {}
            for c in self._COLS:
                if c in cols:
                    col_idx[c] = cols.index(c)
            if col_idx:
                for gi, gname in enumerate(ctx.genes):
                    vals = genes.get(gname)
                    if vals is None:
                        continue
                    ok = True
                    row = []
                    for c in self._COLS:
                        if c in col_idx:
                            v = vals[col_idx[c]]
                            if v is None:
                                ok = False
                                break
                            try:
                                fv = float(v)
                            except (TypeError, ValueError):
                                ok = False
                                break
                            if not np.isfinite(fv):
                                ok = False
                                break
                            row.append(fv)
                        else:
                            row.append(0.0)
                    if ok:
                        vecs[gi, :] = row
                        present[gi] = True

        # Standardise each column across genes that have data, then L2-normalise
        # each gene's vector so cosine similarity is a simple dot product.
        for j in range(vecs.shape[1]):
            col = vecs[:, j]
            mask = present
            if mask.any():
                mu = col[mask].mean()
                sd = col[mask].std()
                if sd > 1e-12:
                    vecs[mask, j] = (col[mask] - mu) / sd
                else:
                    vecs[mask, j] = 0.0
            vecs[~mask, j] = 0.0

        norms = np.linalg.norm(vecs, axis=1)
        norms[norms < 1e-12] = 1.0
        vecs = vecs / norms[:, None]

        result = (vecs, present)
        ctx.cache["_e660_prom_vecs"] = result
        return result

    def compute(self, ctx, perts, params):
        vecs, present = self._build_vectors(ctx)
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)

        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            # Keep only targets that have promoter data.
            valid = [t for t in tidx if 0 <= t < n and present[t]]
            if not valid:
                out[i, :, 0] = 0.0
                continue
            # Mean promoter vector of the targets (order-independent).
            mean_vec = vecs[valid, :].mean(axis=0)
            norm = np.linalg.norm(mean_vec)
            if norm < 1e-12:
                out[i, :, 0] = 0.0
                continue
            mean_vec = mean_vec / norm
            # Cosine similarity of every gene with the target-mean promoter.
            sims = vecs @ mean_vec
            # Genes without promoter data get zero.
            sims[~present] = 0.0
            out[i, :, 0] = sims

        out[~np.isfinite(out)] = 0.0
        return out
