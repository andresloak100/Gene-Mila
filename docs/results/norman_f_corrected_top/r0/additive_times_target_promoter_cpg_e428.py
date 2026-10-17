import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveTimesTargetPromoterCpG(Feature):
    name = "additive_times_target_promoter_cpg_e428"
    version = 1
    description = ("Elementwise product of additive_response and the mean promoter CpG "
                   "observed/expected ratio of the perturbation's target gene(s).")
    rationale = ("Target promoter CpG content may modulate CRISPRa efficiency, scaling the "
                 "additive transcriptional response.")
    inputs = ["additive_response", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        # additive_response feature (n, n_genes, dim)
        add = ctx.feature("additive_response", perts)
        if add.ndim == 3:
            add = add[:, :, 0]
        add = np.asarray(add, dtype=np.float64)

        # gene annotation
        ann = ctx.knowledge("gene_annotation") or {}
        genes_ann = ann.get("genes", {})
        # column index for gc_promoter / cpg_oe_promoter
        columns = ann.get("columns", [])
        cpg_idx = None
        for j, c in enumerate(columns):
            if c == "cpg_oe_promoter":
                cpg_idx = j
                break

        # cache mean target cpg per perturbation
        cache = ctx.cache
        key = "e428_target_cpg"
        if key not in cache:
            cache[key] = {}
        cpg_cache = cache[key]

        for i, p in enumerate(perts):
            if p in cpg_cache:
                val = cpg_cache[p]
            else:
                targets = ctx.target_genes(p) or []
                vals = []
                for tg in targets:
                    row = genes_ann.get(tg)
                    if row is None or cpg_idx is None:
                        continue
                    v = row[cpg_idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vals.append(fv)
                val = float(np.mean(vals)) if vals else 0.0
                cpg_cache[p] = val
            out[i, :, 0] = add[i] * val

        return out
