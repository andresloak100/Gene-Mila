import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufXCoexpressionRankE560(Feature):
    name = "target_loeuf_x_coexpression_rank_e560"
    version = 1
    description = "Product of target LOEUF (oe_lof_upper) and the rank of Pearson correlation between target and gene g across control cells."
    rationale = "Essential targets (low LOEUF) with coordinated coexpression should amplify perturbation effects on coexpressed genes."
    inputs = ["control_cells", "knowledge"]
    params = {}
    dim = 1

    def _loeuf_map(self, ctx):
        if "loeuf_map" in ctx.cache:
            return ctx.cache["loeuf_map"]
        m = {}
        k = ctx.knowledge("gene_constraint")
        if k is not None:
            cols = k.get("columns", [])
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                genes = k.get("genes", {})
                for g, vals in genes.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except Exception:
                        continue
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except Exception:
                        continue
                    if np.isfinite(v):
                        m[g] = v
        ctx.cache["loeuf_map"] = m
        return m

    def _median_loeuf(self, ctx):
        if "median_loeuf" in ctx.cache:
            return ctx.cache["median_loeuf"]
        m = self._loeuf_map(ctx)
        if m:
            med = float(np.median(np.array(list(m.values()), dtype=float)))
        else:
            med = 1.0
        ctx.cache["median_loeuf"] = med
        return med

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        loeuf_map = self._loeuf_map(ctx)
        default_loeuf = self._median_loeuf(ctx)

        # Coexpression correlation matrix across control cells (cached).
        if "coexpr_corr" in ctx.cache:
            corr = ctx.cache["coexpr_corr"]
        else:
            X = np.asarray(ctx.control_cells, dtype=float)
            # standardize columns
            mu = X.mean(axis=0)
            sd = X.std(axis=0)
            sd = np.where(sd < 1e-12, 1.0, sd)
            Z = (X - mu) / sd
            n = Z.shape[0]
            denom = max(n - 1, 1)
            corr = (Z.T @ Z) / denom
            corr = np.clip(corr, -1.0, 1.0)
            np.fill_diagonal(corr, 1.0)
            corr = np.nan_to_num(corr, nan=0.0)
            ctx.cache["coexpr_corr"] = corr

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # Use first target gene
            t = tgt_idx[0]
            row = corr[t, :]
            # Rank of correlation (average ties via argsort trick)
            order = np.argsort(row, kind="mergesort")
            ranks = np.empty(n_genes, dtype=float)
            ranks[order] = np.arange(n_genes, dtype=float)
            # normalize rank to [0,1]
            if n_genes > 1:
                ranks = ranks / (n_genes - 1)
            else:
                ranks = np.zeros(n_genes, dtype=float)

            # target LOEUF
            tgenes = ctx.target_genes(p)
            loeuf_val = default_loeuf
            if tgenes:
                loeuf_val = loeuf_map.get(tgenes[0], default_loeuf)
            out[i, :, 0] = loeuf_val * ranks

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
