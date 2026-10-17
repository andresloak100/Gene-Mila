import numpy as np
from genemila.features.api import Feature, register


@register
class NuclearTargetXGeneLoeuf(Feature):
    name = "nuclear_target_x_gene_loeuf_e697"
    version = 1
    description = "Nuclear-target indicator times (1 - LOEUF) of gene g."
    rationale = ("Nuclear perturbation targets may affect essential genes differently; "
                 "interacting with gene LoF constraint (LOEUF) captures this.")
    inputs = ["knowledge", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # --- gene LOEUF -> (1 - LOEUF) per gene column ---
        gene_loeuf = np.full(n_genes, np.nan, dtype=float)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            cols = kc.get("columns", [])
            if "oe_lof_upper" in cols:
                idx = cols.index("oe_lof_upper")
                genes_tab = kc.get("genes", {})
                for g, col in ctx.gene_index.items():
                    vals = genes_tab.get(g)
                    if vals is not None and len(vals) > idx:
                        v = vals[idx]
                        if v is not None:
                            try:
                                fv = float(v)
                                if np.isfinite(fv):
                                    gene_loeuf[col] = fv
                            except (TypeError, ValueError):
                                pass
        # Missing LOEUF -> treat as neutral (1 - 0.5)? Use 0 contribution instead.
        has_loeuf = np.isfinite(gene_loeuf)
        gene_score = np.zeros(n_genes, dtype=float)
        gene_score[has_loeuf] = 1.0 - gene_loeuf[has_loeuf]
        gene_score = np.clip(gene_score, 0.0, None)

        # --- nuclear flag per gene (from protein_annotation) ---
        nuclear = np.zeros(n_genes, dtype=float)
        pa = ctx.knowledge("protein_annotation")
        if pa is not None:
            cols = pa.get("columns", [])
            if "nucleus" in cols:
                nidx = cols.index("nucleus")
                genes_tab = pa.get("genes", {})
                for g, col in ctx.gene_index.items():
                    vals = genes_tab.get(g)
                    if vals is not None and len(vals) > nidx:
                        v = vals[nidx]
                        if v is not None:
                            try:
                                if float(v) > 0:
                                    nuclear[col] = 1.0
                            except (TypeError, ValueError):
                                pass

        # --- per-perturbation nuclear target indicator ---
        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            is_nuclear = 0.0
            for tg in tgenes:
                gi = ctx.gene_index.get(tg)
                if gi is not None and nuclear[gi] > 0:
                    is_nuclear = 1.0
                    break
            if is_nuclear > 0:
                out[i, :, 0] = gene_score

        return out
