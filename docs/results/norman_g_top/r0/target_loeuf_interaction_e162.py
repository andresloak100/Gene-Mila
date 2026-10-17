import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoEUFInteraction(Feature):
    name = "target_loeuf_interaction_e162"
    version = 1
    description = ("Average LOEUF (oe_lof_upper) across p's target genes, "
                   "multiplied by the additive_response feature.")
    rationale = ("LOEUF reflects selective pressure on gene dosage; CRISPRa of "
                 "LoF-intolerant genes may produce larger transcriptomic changes, "
                 "so the additive response is scaled by target constraint.")
    inputs = ["control_cells", "gene_constraint"]
    params = {"constraint_metric": "oe_lof_upper"}
    dim = 1

    def compute(self, ctx, perts, params):
        metric = params.get("constraint_metric", "oe_lof_upper")
        n_genes = ctx.n_genes
        n_perts = len(perts)

        # Load LOEUF values per gene symbol once.
        cache = ctx.cache
        if "loeuf_by_gene" not in cache:
            loeuf = {}
            gc = ctx.knowledge("gene_constraint")
            if gc is not None and isinstance(gc, dict):
                genes_tbl = gc.get("genes", {}) or {}
                cols = gc.get("columns", []) or []
                try:
                    idx = cols.index(metric)
                except ValueError:
                    idx = None
                if idx is not None:
                    for sym, vals in genes_tbl.items():
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
                            loeuf[sym] = fv
            cache["loeuf_by_gene"] = loeuf
        loeuf = cache["loeuf_by_gene"]

        # Get additive_response feature (same perts order).
        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim == 1:
            add = add.reshape(n_perts, n_genes)

        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            vals = [loeuf[g] for g in tg if g in loeuf]
            if len(vals) == 0:
                scale = 0.0
            else:
                scale = float(np.mean(vals))
            row = add[i]
            row = np.where(np.isfinite(row), row, 0.0)
            out[i, :, 0] = scale * row

        out[~np.isfinite(out)] = 0.0
        return out
