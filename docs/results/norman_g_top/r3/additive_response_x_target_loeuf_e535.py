import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetLoeuf(Feature):
    name = "additive_response_x_target_loeuf_e535"
    version = 1
    description = "Product of additive_response and (1 - mean LOEUF) across target genes of p."
    rationale = ("LoF-intolerant (low LOEUF) targets are dosage-sensitive; their activation "
                 "may produce larger transcriptional consequences, scaling the additive response.")
    inputs = ["control_cells", "gene_constraint", "train_delta"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Load LOEUF mapping from gene_constraint prior.
        loeuf = {}
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            cols = kc.get("columns", [])
            genes_tbl = kc.get("genes", {})
            if "oe_lof_upper" in cols:
                idx = cols.index("oe_lof_upper")
                for g, vals in genes_tbl.items():
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
                        loeuf[g] = fv

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue

            # Additive response: mean over training perturbations of the summed target deltas.
            _, d = ctx.train_delta(exclude=p)
            # d shape (n_train, n_genes); additive = sum of columns for target genes
            add = d[:, tgt_idx].sum(axis=0)  # (n_train,)
            if add.size == 0:
                continue
            add_mean = float(np.mean(add))

            # Mean LOEUF over targets (only those with data).
            tgt_genes = ctx.target_genes(p)
            vals = [loeuf[g] for g in tgt_genes if g in loeuf]
            if vals:
                mean_loeuf = float(np.mean(vals))
            else:
                mean_loeuf = 0.0
            mult = 1.0 - mean_loeuf

            out[i, :, 0] = add_mean * mult

        return out
