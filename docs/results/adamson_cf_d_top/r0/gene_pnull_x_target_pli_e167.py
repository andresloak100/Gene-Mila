import numpy as np
from genemila.features.api import Feature, register


@register
class GenePnullXTargetPliE167(Feature):
    name = "gene_pnull_x_target_pli_e167"
    version = 1
    description = "Product of gene g's pNull and the target's pLI (fallback 1-LOEUF, then 0)."
    rationale = ("High pNull indicates LoF tolerance; interacting with target constraint "
                 "should predict smaller deltas for tolerant genes.")
    inputs = ["gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        # Load constraint table
        gc = ctx.knowledge("gene_constraint") or {}
        genes_tbl = gc.get("genes", {}) or {}
        columns = gc.get("columns", []) or []

        # Locate pNull and pLI / LOEUF column indices
        def col_idx(name):
            for i, c in enumerate(columns):
                if c == name:
                    return i
            return None

        idx_pnull = col_idx("pNull")
        idx_pli = col_idx("pLI")
        idx_loeuf = col_idx("oe_lof_upper")

        # Build per-gene pNull vector in ctx gene order
        pnull = np.zeros(n_genes, dtype=float)
        for gi, g in enumerate(ctx.genes):
            vals = genes_tbl.get(g)
            if vals is None:
                continue
            if idx_pnull is not None and idx_pnull < len(vals):
                v = vals[idx_pnull]
                if v is not None:
                    try:
                        pnull[gi] = float(v)
                    except (TypeError, ValueError):
                        pass

        # Precompute target constraint scalar per perturbation
        target_pli = np.zeros(n_perts, dtype=float)
        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if not tgenes:
                continue
            t = tgenes[0]
            vals = genes_tbl.get(t)
            if vals is None:
                continue
            val = 0.0
            found = False
            if idx_pli is not None and idx_pli < len(vals) and vals[idx_pli] is not None:
                try:
                    val = float(vals[idx_pli])
                    found = True
                except (TypeError, ValueError):
                    found = False
            if not found and idx_loeuf is not None and idx_loeuf < len(vals) and vals[idx_loeuf] is not None:
                try:
                    val = 1.0 - float(vals[idx_loeuf])
                    found = True
                except (TypeError, ValueError):
                    found = False
            if not found:
                val = 0.0
            target_pli[i] = val

        # Outer product: (n_perts, n_genes)
        out[:, :, 0] = target_pli[:, None] * pnull[None, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
