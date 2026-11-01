import numpy as np
from genemila.features.api import Feature, register


@register
class TargetCpgPromoterXGeneIntronLength(Feature):
    name = "target_cpg_promoter_x_gene_intron_length_e232"
    version = 1
    description = "Product of target gene's cpg_oe_promoter (fallback 0.5) and gene g's intron_length_kb."
    rationale = ("CpG island promoters and long introns both harbor regulatory elements; their "
                 "interaction may amplify perturbation effects on gene expression.")
    inputs = ["gene_annotation"]
    params = {"fallback_cpg": 0.5}
    dim = 1

    def compute(self, ctx, perts, params):
        fallback = float(params.get("fallback_cpg", 0.5))
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        ann = ctx.knowledge("gene_annotation")
        cpg_col = None
        intron_col = None
        genes_ann = None
        if isinstance(ann, dict):
            cols = ann.get("columns", [])
            if isinstance(cols, (list, tuple)):
                for j, c in enumerate(cols):
                    if c == "cpg_oe_promoter":
                        cpg_col = j
                    elif c == "intron_length_kb":
                        intron_col = j
            genes_ann = ann.get("genes")

        # Per-gene intron length vector
        intron_vec = np.zeros(n_genes, dtype=float)
        cpg_map = {}
        if genes_ann is not None and intron_col is not None:
            for g, vals in genes_ann.items():
                idx = ctx.gene_index.get(g)
                if idx is None:
                    continue
                try:
                    v = vals[intron_col]
                except (IndexError, TypeError):
                    v = None
                if v is not None:
                    try:
                        fv = float(v)
                        if np.isfinite(fv):
                            intron_vec[idx] = fv
                    except (TypeError, ValueError):
                        pass
                if cpg_col is not None:
                    try:
                        cv = vals[cpg_col]
                    except (IndexError, TypeError):
                        cv = None
                    if cv is not None:
                        try:
                            cpg_map[g] = float(cv)
                        except (TypeError, ValueError):
                            pass

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            cpg_val = fallback
            for tg in tgenes:
                if tg in cpg_map:
                    v = cpg_map[tg]
                    if np.isfinite(v):
                        cpg_val = v
                    break
            out[i, :, 0] = cpg_val * intron_vec

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
