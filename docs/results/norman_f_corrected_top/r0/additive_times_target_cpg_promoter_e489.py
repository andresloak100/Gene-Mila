import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveTimesTargetCpgPromoterE489(Feature):
    name = "additive_times_target_cpg_promoter_e489"
    version = 1
    description = "additive_response multiplied by the summed cpg_oe_promoter of the perturbation's target genes."
    rationale = ("CRISPRa efficiency depends on promoter context; CpG-rich promoters are often "
                 "associated with active transcription, so scaling the additive response by the "
                 "target promoter's CpG observed/expected ratio may capture activation strength.")
    inputs = ["gene_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        # Base additive response feature (composition).
        base = ctx.feature("additive_response", perts)
        base = np.asarray(base, dtype=float)
        if base.ndim == 2:
            base = base[:, :, None]
        base = np.nan_to_num(base, nan=0.0, posinf=0.0, neginf=0.0)

        ann = ctx.knowledge("gene_annotation")
        genes_map = None
        if isinstance(ann, dict):
            genes_map = ann.get("genes")
        if not isinstance(genes_map, dict):
            genes_map = {}

        # Column index of cpg_oe_promoter within the per-gene annotation vector.
        columns = None
        if isinstance(ann, dict):
            columns = ann.get("columns")
        cpg_col = None
        if isinstance(columns, (list, tuple)):
            for j, c in enumerate(columns):
                if c == "cpg_oe_promoter":
                    cpg_col = j
                    break

        cache = ctx.cache
        cache_key = "e489_cpg_promoter_per_gene"
        cpg_per_gene = cache.get(cache_key)
        if cpg_per_gene is None:
            cpg_per_gene = np.zeros(ctx.n_genes, dtype=float)
            if cpg_col is not None:
                for gi, g in enumerate(ctx.genes):
                    vals = genes_map.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[cpg_col]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        cpg_per_gene[gi] = fv
            cache[cache_key] = cpg_per_gene

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            s = 0.0
            for ti in tgt_idx:
                s += cpg_per_gene[ti]
            if s == 0.0:
                continue
            out[i, :, 0] = base[i, :, 0] * s

        if not np.all(np.isfinite(out)):
            out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
