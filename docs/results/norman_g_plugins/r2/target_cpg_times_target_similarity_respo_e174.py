import numpy as np
from genemila.features.api import Feature, register


@register
class TargetCpgTimesTargetSimilarityResponseE174(Feature):
    name = "target_cpg_times_target_similarity_respo_e174"
    version = 1
    description = ("Product of mean cpg_oe_promoter over p's target genes and "
                   "target_similarity_response.")
    rationale = ("Weighting response transfer by promoter CpG characteristics "
                 "combined with target similarity may capture a distinct axis.")
    inputs = ["gene_annotation", "target_similarity_response_e15"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes

        # Load gene_annotation cpg_oe_promoter per gene.
        cpg = np.full(n_genes, np.nan, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            cols = ann.get("columns", [])
            genes_tbl = ann.get("genes", {})
            if "cpg_oe_promoter" in cols:
                idx = cols.index("cpg_oe_promoter")
                for g, col in ctx.gene_index.items():
                    vals = genes_tbl.get(g)
                    if vals is not None and idx < len(vals):
                        v = vals[idx]
                        if v is not None:
                            try:
                                fv = float(v)
                                if np.isfinite(fv):
                                    cpg[col] = fv
                            except (TypeError, ValueError):
                                pass

        # Global fallback mean over annotated genes.
        finite_mask = np.isfinite(cpg)
        global_mean = float(cpg[finite_mask].mean()) if finite_mask.any() else 0.0

        # target_similarity_response feature.
        sim = ctx.feature("target_similarity_response_e15", perts, None)
        sim = np.asarray(sim, dtype=float)
        if sim.ndim == 3:
            sim = sim[:, :, 0]
        elif sim.ndim == 1:
            sim = sim[:, None]

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if tgt:
                vals = cpg[tgt]
                vals = vals[np.isfinite(vals)]
                mean_cpg = float(vals.mean()) if vals.size > 0 else global_mean
            else:
                mean_cpg = global_mean
            out[i, :, 0] = mean_cpg * sim[i]

        out[~np.isfinite(out)] = 0.0
        return out
