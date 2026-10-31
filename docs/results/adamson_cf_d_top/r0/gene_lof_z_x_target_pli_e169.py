import numpy as np
from genemila.features.api import Feature, register

@register
class GeneLofZXTargetPLI(Feature):
    name = "gene_lof_z_x_target_pli_e169"
    version = 1
    description = "Product of gene g's negated lof_z (intolerance) and target p's pLI."
    rationale = ("Negative lof_z indicates LoF intolerance; interacting with target constraint "
                 "captures essential gene co-regulation.")
    inputs = ["knowledge:gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        kc = ctx.knowledge("gene_constraint")
        if not kc:
            return out
        genes_tbl = kc.get("genes", {})
        columns = kc.get("columns", [])
        try:
            lof_z_idx = columns.index("lof_z")
            pli_idx = columns.index("pLI")
        except ValueError:
            return out

        # Per-gene negated lof_z (positive = intolerant), 0 when missing.
        gene_intol = np.zeros(n_genes, dtype=float)
        gene_pli = np.zeros(n_genes, dtype=float)
        for g, gi in ctx.gene_index.items():
            vals = genes_tbl.get(g)
            if vals is None:
                continue
            try:
                lz = vals[lof_z_idx]
                if lz is not None:
                    lz = float(lz)
                    if np.isfinite(lz):
                        gene_intol[gi] = max(0.0, -lz)
                pl = vals[pli_idx]
                if pl is not None:
                    pl = float(pl)
                    if np.isfinite(pl):
                        gene_pli[gi] = pl
            except (IndexError, TypeError, ValueError):
                continue

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            t_pli = gene_pli[tgt_idx].max()
            if t_pli <= 0:
                continue
            out[i, :, 0] = gene_intol * t_pli

        return out
