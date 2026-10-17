import numpy as np
from genemila.features.api import Feature, FeatureContext, register


@register
class TargetPromoterCpgContentE317(Feature):
    name = "target_promoter_cpg_content_e317"
    version = 1
    description = "CpG observed/expected ratio in the promoter region of the perturbation target gene."
    rationale = (
        "Promoter CpG content proxies chromatin accessibility and CRISPRi/a efficiency "
        "at the target site, which can scale the magnitude of the response."
    )
    inputs = ["knowledge:gene_annotation", "target_genes"]
    params = {"impute": "median"}
    dim = 1

    def compute(self, ctx: FeatureContext, perts: list[str], params: dict) -> np.ndarray:
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        cache = ctx.cache
        if "e317_col" not in cache:
            col = None
            if ann is not None:
                columns = ann.get("columns", [])
                try:
                    col = columns.index("cpg_oe_promoter")
                except (ValueError, AttributeError):
                    col = None
            cache["e317_col"] = col
        col = cache["e317_col"]

        genes_ann = {}
        if ann is not None and col is not None:
            genes_ann = ann.get("genes", {}) or {}

        # Build per-gene value vector over ctx.genes
        if "e317_vec" not in cache:
            vals = np.full(ctx.n_genes, np.nan, dtype=float)
            for gi, g in enumerate(ctx.genes):
                rec = genes_ann.get(g)
                if rec is None:
                    continue
                try:
                    v = rec[col]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    vals[gi] = fv
            finite = vals[np.isfinite(vals)]
            if finite.size > 0:
                med = float(np.median(finite))
            else:
                med = 0.0
            vals = np.where(np.isfinite(vals), vals, med)
            cache["e317_vec"] = vals
        vec = cache["e317_vec"]

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if not tgenes:
                continue
            idxs = [ctx.gene_index[g] for g in tgenes if g in ctx.gene_index]
            if not idxs:
                continue
            # use the mean promoter CpG content across target genes
            val = float(np.mean(vec[idxs]))
            out[i, :, 0] = val

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
