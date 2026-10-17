import numpy as np
from genemila.features.api import Feature, register

@register
class GeneResponseVarianceOverEssentialityE651(Feature):
    name = "gene_response_variance_over_essentiality_e651"
    version = 1
    description = ("Variance of gene g's delta values across training perturbations (leaving p out), "
                   "divided by the target's essentiality score (LOEUF-derived).")
    rationale = ("Essential targets may have buffered responses; non-essential targets may cause more "
                 "variable downstream effects. Scaling gene response variance by essentiality could "
                 "reveal such interactions.")
    inputs = ["train_delta", "gene_constraint", "target_indices"]
    params = {"epsilon": 1e-06}
    dim = 1

    def compute(self, ctx, perts, params):
        eps = float(params.get("epsilon", 1e-6))
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # --- Build essentiality score per gene from gnomAD LoF constraint (LOEUF) ---
        ess = np.full(n_genes, np.nan, dtype=float)
        gc = ctx.knowledge("gene_constraint")
        if gc is not None:
            cols = gc.get("columns", [])
            genes_map = gc.get("genes", {})
            try:
                loeuf_idx = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            if loeuf_idx is not None:
                for g, vals in genes_map.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    try:
                        v = vals[loeuf_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        # Essentiality score: low LOEUF = LoF-intolerant = more essential.
                        ess[gi] = 1.0 / (fv + eps)

        # Impute missing essentiality with median of finite values
        finite = np.isfinite(ess)
        if finite.any():
            med = float(np.median(ess[finite]))
        else:
            med = 1.0
        ess[~finite] = med
        # Guard against non-positive / non-finite
        ess = np.where(np.isfinite(ess) & (ess > 0), ess, med)

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            if d.shape[0] == 0:
                var_g = np.zeros(n_genes, dtype=float)
            else:
                var_g = d.var(axis=0)
            # Target essentiality: mean over target genes (usually one)
            tgt_idx = ctx.target_indices(p)
            if len(tgt_idx) > 0:
                t_ess = float(np.mean(ess[tgt_idx]))
            else:
                t_ess = med
            if not np.isfinite(t_ess) or t_ess <= 0:
                t_ess = med
            out[i, :, 0] = var_g / (t_ess + eps)

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
