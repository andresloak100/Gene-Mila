import numpy as np
from genemila.features.api import Feature, register


@register
class EssentialityInteractionE561(Feature):
    name = "essentiality_interaction_e561"
    version = 1
    description = (
        "Product of the perturbation target's essentiality score and gene g's "
        "LOEUF-based essentiality score (from gnomAD gene_constraint)."
    )
    rationale = (
        "Co-essential genes tend to be functionally related; perturbing an essential "
        "target should produce stronger responses in genes that are themselves "
        "essentiality-sensitive. The interaction captures this coupling."
    )
    inputs = ["gene_constraint", "target_essentiality_score_e284"]
    params = {"impute_missing": "median"}
    dim = 1

    def _gene_loueuf(self, ctx, params):
        """Return (n_genes,) array of LOEUF values, median-imputed for missing."""
        cached = ctx.cache.get("e561_loueuf")
        if cached is not None:
            return cached

        n = ctx.n_genes
        vals = np.full(n, np.nan, dtype=float)

        gc = ctx.knowledge("gene_constraint")
        if gc is not None:
            genes = gc.get("genes", {})
            columns = gc.get("columns", [])
            # locate LOEUF column
            idx = None
            for j, c in enumerate(columns):
                if "oe_lof_upper" in c or "loeuf" in c.lower():
                    idx = j
                    break
            if idx is not None:
                for i, g in enumerate(ctx.genes):
                    row = genes.get(g)
                    if row is None:
                        continue
                    try:
                        v = row[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vals[i] = fv

        finite = np.isfinite(vals)
        if finite.any():
            fill = np.median(vals[finite])
        else:
            fill = 0.0
        vals[~finite] = fill

        ctx.cache["e561_loueuf"] = vals
        return vals

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)

        loueuf = self._gene_loueuf(ctx, params)

        # Per-perturbation target essentiality score from the existing feature.
        try:
            tgt = ctx.feature(
                "target_essentiality_score_e284", perts, params=None
            )
            tgt = np.asarray(tgt, dtype=float)
            if tgt.ndim == 3:
                # (n_perts, n_genes, dim) -> per-pert scalar (broadcast gene-wise)
                tgt_vec = tgt[:, :, 0].mean(axis=1)
            elif tgt.ndim == 2:
                tgt_vec = tgt.mean(axis=1)
            elif tgt.ndim == 1:
                tgt_vec = tgt
            else:
                tgt_vec = np.zeros(len(perts), dtype=float)
        except Exception:
            tgt_vec = np.zeros(len(perts), dtype=float)

        tgt_vec = np.asarray(tgt_vec, dtype=float).ravel()
        if tgt_vec.size != len(perts):
            fixed = np.zeros(len(perts), dtype=float)
            m = min(tgt_vec.size, len(perts))
            fixed[:m] = tgt_vec[:m]
            tgt_vec = fixed

        finite_t = np.isfinite(tgt_vec)
        if finite_t.any():
            tfill = np.median(tgt_vec[finite_t])
        else:
            tfill = 0.0
        tgt_vec = np.where(finite_t, tgt_vec, tfill)

        # (n_perts, n_genes) product
        out[:, :, 0] = tgt_vec[:, None] * loueuf[None, :]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
