import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXGeneConstraintE315(Feature):
    name = "additive_response_x_gene_constraint_e315"
    version = 1
    description = "Product of additive_response and a normalized LoF-intolerance score of gene g."
    rationale = ("Highly constrained genes may be more tightly regulated and thus more responsive "
                 "to perturbations of their regulators, so the additive baseline's effect may be "
                 "amplified for genes that are LoF-intolerant.")
    inputs = ["control_cells", "gene_constraint", "train_delta"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        genes = ctx.genes

        # ---- Build normalized LoF-intolerance score per gene in [0, 1] ----
        cache = ctx.cache
        key = "e315_lof_score"
        if key not in cache:
            score = np.full(n_genes, np.nan, dtype=float)
            gc = ctx.knowledge("gene_constraint")
            if gc is not None:
                table_genes = gc.get("genes", {})
                cols = gc.get("columns", [])
                # locate relevant columns
                try:
                    i_oe = cols.index("oe_lof_upper")
                except (ValueError, AttributeError):
                    i_oe = None
                try:
                    i_pli = cols.index("pLI")
                except (ValueError, AttributeError):
                    i_pli = None

                oe_vals = np.full(n_genes, np.nan, dtype=float)
                pli_vals = np.full(n_genes, np.nan, dtype=float)

                for gi, g in enumerate(genes):
                    row = table_genes.get(g)
                    if row is None:
                        continue
                    if i_oe is not None and i_oe < len(row):
                        v = row[i_oe]
                        if v is not None:
                            try:
                                oe_vals[gi] = float(v)
                            except (TypeError, ValueError):
                                pass
                    if i_pli is not None and i_pli < len(row):
                        v = row[i_pli]
                        if v is not None:
                            try:
                                pli_vals[gi] = float(v)
                            except (TypeError, ValueError):
                                pass

                # Prefer LOEUF (1 - oe_lof_upper), fall back to pLI
                has_oe = np.isfinite(oe_vals)
                has_pli = np.isfinite(pli_vals)
                score[has_oe] = 1.0 - oe_vals[has_oe]
                only_pli = (~has_oe) & has_pli
                score[only_pli] = pli_vals[only_pli]

            # Normalize to [0,1] using finite values
            finite = np.isfinite(score)
            if finite.any():
                lo = np.nanmin(score[finite])
                hi = np.nanmax(score[finite])
                if hi > lo:
                    norm = (score - lo) / (hi - lo)
                else:
                    norm = np.where(finite, 0.5, np.nan)
            else:
                norm = np.full(n_genes, np.nan, dtype=float)
            # Missing constraint -> neutral 0 contribution
            norm = np.where(np.isfinite(norm), norm, 0.0)
            norm = np.clip(norm, 0.0, 1.0)
            cache[key] = norm

        lof_score = cache[key]  # (n_genes,)

        # ---- Additive baseline: sum of training-mean delta over p's target genes ----
        # Memoize the leave-one-out mean delta per perturbation id.
        add_key = "e315_additive"
        if add_key not in cache:
            cache[add_key] = {}

        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            targets = ctx.target_indices(p)
            if len(targets) == 0:
                # no measured target -> zero additive response
                continue

            store = cache[add_key]
            if p in store:
                add_vec = store[p]
            else:
                _, d = ctx.train_delta(exclude=p)
                # mean delta per gene across training perturbations (n, n_genes)
                mean_delta = d.mean(axis=0)  # (n_genes,)
                # additive response = sum of mean delta over target genes, broadcast to all genes
                add_vec = np.full(n_genes, mean_delta[targets].sum(), dtype=float)
                store[p] = add_vec

            out[i, :, 0] = add_vec * lof_score

        # Guarantee finiteness
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
