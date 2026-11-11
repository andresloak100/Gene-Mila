import numpy as np
from genemila.features.api import Feature, register


@register
class GeneExpLofXTargetPliE165(Feature):
    name = "gene_exp_lof_x_target_pli_e165"
    version = 1
    description = "Product of gene g's exp_lof and target p's pLI (fallback LOEUF upper)."
    rationale = (
        "Genes with high expected LoF variant counts are dosage-sensitive; "
        "perturbing LoF-intolerant targets amplifies their expression changes."
    )
    inputs = ["gene_constraint", "targets"]
    params = {}
    dim = 1

    def _load_maps(self, ctx):
        cached = ctx.cache.get("e165_maps")
        if cached is not None:
            return cached

        exp_lof = {}
        pli = {}
        loeuf = {}

        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            cols = list(kc.get("columns", []))
            genes = kc.get("genes", {}) or {}

            def col_idx(name):
                try:
                    return cols.index(name)
                except ValueError:
                    return None

            i_exp = col_idx("exp_lof")
            i_pli = col_idx("pLI")
            if i_pli is None:
                i_pli = col_idx("pli")
            i_loeuf = col_idx("oe_lof_upper")
            if i_loeuf is None:
                i_loeuf = col_idx("loeuf")

            for g, vals in genes.items():
                if not isinstance(vals, (list, tuple)):
                    continue
                if i_exp is not None and i_exp < len(vals):
                    v = vals[i_exp]
                    if v is not None:
                        try:
                            exp_lof[g] = float(v)
                        except (TypeError, ValueError):
                            pass
                if i_pli is not None and i_pli < len(vals):
                    v = vals[i_pli]
                    if v is not None:
                        try:
                            pli[g] = float(v)
                        except (TypeError, ValueError):
                            pass
                if i_loeuf is not None and i_loeuf < len(vals):
                    v = vals[i_loeuf]
                    if v is not None:
                        try:
                            loeuf[g] = float(v)
                        except (TypeError, ValueError):
                            pass

        maps = (exp_lof, pli, loeuf)
        ctx.cache["e165_maps"] = maps
        return maps

    def compute(self, ctx, perts, params):
        exp_lof, pli, loeuf = self._load_maps(ctx)

        # gene-level exp_lof vector
        gene_exp = np.zeros(ctx.n_genes, dtype=float)
        for g, idx in ctx.gene_index.items():
            v = exp_lof.get(g)
            if v is not None and np.isfinite(v):
                gene_exp[idx] = v

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            target_pli = 0.0
            target_genes = ctx.target_genes(p)
            for tg in target_genes:
                v = pli.get(tg)
                if v is None or not np.isfinite(v):
                    v = loeuf.get(tg)
                if v is not None and np.isfinite(v):
                    target_pli = float(v)
                    break

            out[i, :, 0] = gene_exp * target_pli

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
