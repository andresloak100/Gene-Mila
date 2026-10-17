import numpy as np
from genemila.features.api import Feature, register


@register
class TargetConstraintResponse(Feature):
    name = "target_constraint_response_e77"
    version = 1
    description = ("Mean over target genes of (1 - LOEUF) times the mean absolute "
                   "single-perturbation delta of that target (excluding self).")
    rationale = ("LoF-intolerant (low LOEUF) genes may be dosage-sensitive; scaling "
                 "their single-gene response magnitude by (1 - LOEUF) captures how "
                 "strongly activating such a target perturbs the cell.")
    inputs = ["control_cells", "train_delta", "knowledge:gene_constraint"]
    params = {"loeuf_missing": 0.5}
    dim = 1

    def compute(self, ctx, perts, params):
        missing = float(params.get("loeuf_missing", 0.5))
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # ---- Load LOEUF per gene symbol from gene_constraint ----
        loeuf = {}
        gc = ctx.knowledge("gene_constraint")
        if gc is not None:
            cols = gc.get("columns", [])
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            genes_tbl = gc.get("genes", {})
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

        if loeuf:
            default_loeuf = float(np.median(list(loeuf.values())))
        else:
            default_loeuf = missing

        # Precompute LOEUF factor per gene (1 - LOEUF), clamped
        loeuf_factor = {}
        for g in ctx.genes:
            lf = loeuf.get(g, default_loeuf)
            if not np.isfinite(lf):
                lf = default_loeuf
            lf = min(max(lf, 0.0), 1.0)
            loeuf_factor[g] = 1.0 - lf

        # ---- Compute feature per perturbation, using train_delta(exclude=p) ----
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                continue

            # LEAKAGE RULE: exclude p when computing its own row
            tr_ids, d = ctx.train_delta(exclude=p)

            # Build mean |delta| per single perturbation gene from this fold
            single_abs = {}
            for j, pid in enumerate(tr_ids):
                ptg = ctx.target_genes(pid)
                if len(ptg) == 1 and pid == ptg[0]:
                    g = ptg[0]
                    if g in ctx.gene_index:
                        single_abs[g] = float(np.mean(np.abs(d[j, :])))

            if single_abs:
                default_abs = float(np.mean(list(single_abs.values())))
            else:
                default_abs = 0.0

            vals = []
            for g in tg:
                ab = single_abs.get(g, default_abs)
                vals.append(loeuf_factor.get(g, 1.0 - default_loeuf) * ab)
            out[i, :, 0] = float(np.mean(vals))

        out[~np.isfinite(out)] = 0.0
        return out
