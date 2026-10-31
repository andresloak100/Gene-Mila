import numpy as np
from genemila.features.api import Feature, register

@register
class GenePrecTargetLoeufInteractionE161(Feature):
    name = "gene_prec_target_loeuf_interaction_e161"
    version = 1
    description = ("Product of gene g's pRec (from gnomAD constraint) and the inverse "
                   "LOEUF (oe_lof_upper) of the perturbation target gene p, each normalized.")
    rationale = ("Dosage-sensitive genes (high pRec) may respond more strongly to perturbation "
                 "of essential (low LOEUF) genes; the product captures this interaction.")
    inputs = ["gene_constraint", "control_cells"]
    params = {"normalize": True}
    dim = 1

    def _get_column(self, ctx, table_name, col_name):
        """Extract a per-gene numeric column from a knowledge table, aligned to ctx.genes."""
        kb = ctx.knowledge(table_name)
        n = ctx.n_genes
        out = np.full(n, np.nan, dtype=np.float64)
        if kb is None:
            return out
        cols = kb.get("columns", [])
        if col_name not in cols:
            return out
        idx = cols.index(col_name)
        genes = kb.get("genes", {})
        for g, gi in ctx.gene_index.items():
            vals = genes.get(g)
            if vals is None:
                continue
            try:
                v = vals[idx]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                out[gi] = fv
        return out

    def _normalize(self, x):
        """Robust z-like normalization on finite entries; NaN -> 0."""
        out = np.zeros_like(x)
        fin = np.isfinite(x)
        if fin.sum() == 0:
            return out
        vals = x[fin]
        mu = np.mean(vals)
        sd = np.std(vals)
        if sd <= 0 or not np.isfinite(sd):
            out[fin] = vals - mu
        else:
            out[fin] = (vals - mu) / sd
        return out

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        normalize = bool(params.get("normalize", True))

        key = ("gene_prec_target_loeuf_e161", normalize)
        cache = ctx.cache
        if key not in cache:
            prec = self._get_column(ctx, "gene_constraint", "pRec")
            loeuf = self._get_column(ctx, "gene_constraint", "oe_lof_upper")

            # Fill missing with neutral median (finite) values
            def fill(x):
                fin = np.isfinite(x)
                if fin.sum() == 0:
                    return np.zeros_like(x)
                med = np.median(x[fin])
                y = x.copy()
                y[~fin] = med
                return y

            prec = fill(prec)
            loeuf = fill(loeuf)

            if normalize:
                prec_n = self._normalize(prec)
                loeuf_n = self._normalize(loeuf)
            else:
                prec_n = prec
                loeuf_n = loeuf

            # inverse LOEUF: low LOEUF (essential) -> large positive value
            inv_loeuf = 1.0 / (np.abs(loeuf_n) + 1.0)

            cache[key] = (prec_n, inv_loeuf)

        prec_n, inv_loeuf = cache[key]

        out = np.zeros((len(perts), n, 1), dtype=np.float64)
        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if len(tidx) == 0:
                continue
            # average inverse-LOEUF over target genes
            t_val = float(np.mean(inv_loeuf[tidx]))
            out[i, :, 0] = prec_n * t_val

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
