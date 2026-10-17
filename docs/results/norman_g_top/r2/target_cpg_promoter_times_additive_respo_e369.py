import numpy as np
from genemila.features.api import Feature, register


@register
class TargetCpgPromoterTimesAdditiveResponseE369(Feature):
    name = "target_cpg_promoter_times_additive_respo_e369"
    version = 1
    description = "Mean cpg_oe_promoter of p's target genes multiplied by additive_response."
    rationale = ("CpG-rich promoters are associated with open chromatin and higher "
                 "transcriptional responsiveness, potentially amplifying perturbation effects.")
    inputs = ["control_cells", "gene_annotation", "train_delta"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        col_idx = None
        cpg_vals = None
        if ann is not None:
            cols = ann.get("columns", [])
            if "cpg_oe_promoter" in cols:
                col_idx = cols.index("cpg_oe_promoter")
            genes_ann = ann.get("genes", {})
            cpg_vals = {}
            for g in ctx.genes:
                v = None
                entry = genes_ann.get(g)
                if entry is not None and col_idx is not None and col_idx < len(entry):
                    v = entry[col_idx]
                cpg_vals[g] = v

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            add = d.mean(axis=0)

            tgenes = ctx.target_genes(p)
            vals = []
            if cpg_vals is not None:
                for g in tgenes:
                    v = cpg_vals.get(g)
                    if v is not None:
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            vals.append(fv)
            if vals:
                mean_cpg = float(np.mean(vals))
            else:
                mean_cpg = 0.0

            out[i, :, 0] = mean_cpg * add

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
