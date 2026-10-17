import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneLoeufSimilarityE551(Feature):
    name = "target_gene_loeuf_similarity_e551"
    version = 1
    description = "Similarity in LOEUF between perturbation target and gene g: 1/(1+|LOEUF_t - LOEUF_g|)."
    rationale = "LoF-intolerant genes may share essential pathways; similar constraint may capture functional coupling."
    inputs = ["knowledge:gene_constraint", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        kc = ctx.knowledge("gene_constraint")
        if kc is None:
            return out

        genes_tbl = kc.get("genes", {}) or {}
        columns = kc.get("columns", []) or []
        try:
            loeuf_idx = columns.index("oe_lof_upper")
        except ValueError:
            return out

        # Per-gene LOEUF mapped onto ctx gene columns; NaN where unavailable.
        gene_loeuf = np.full(ctx.n_genes, np.nan, dtype=float)
        for g, col in ctx.gene_index.items():
            vals = genes_tbl.get(g)
            if vals is None:
                continue
            if loeuf_idx >= len(vals):
                continue
            v = vals[loeuf_idx]
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                gene_loeuf[col] = fv

        valid_gene = np.isfinite(gene_loeuf)

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            tvals = []
            for tg in tgenes:
                vals = genes_tbl.get(tg)
                if vals is None or loeuf_idx >= len(vals) or vals[loeuf_idx] is None:
                    continue
                try:
                    fv = float(vals[loeuf_idx])
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    tvals.append(fv)
            if not tvals:
                continue
            t = float(np.mean(tvals))
            sim = 1.0 / (1.0 + np.abs(t - gene_loeuf))
            sim = np.where(valid_gene, sim, 0.0)
            out[i, :, 0] = sim

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
