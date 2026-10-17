import numpy as np
from genemila.features.api import Feature, register


@register
class CoessentialityCorrelationE744(Feature):
    name = "coessentiality_correlation_e744"
    version = 1
    description = (
        "For each (p,g), a similarity between the essentiality proxy of the perturbation "
        "target p and gene g, computed from gnomAD LoF constraint (LOEUF) as a scalar "
        "essentiality proxy: similarity = exp(-|z_p - z_g|) with a sign so that low LOEUF "
        "(LoF-intolerant / essential) maps to high essentiality."
    )
    rationale = (
        "Co-essentiality reflects functional coupling; genes with similar essentiality "
        "profiles tend to be functionally coupled, so perturbing one may affect the other. "
        "Without DepMap cell-line profiles, gnomAD LoF constraint (LOEUF) provides a scalar "
        "per-gene essentiality proxy; genes with similar constraint are more likely coupled."
    )
    inputs = ["knowledge", "target_genes"]
    params = {"use_constraint_proxy": True, "scale": 1.0}
    dim = 1

    def _essentiality_vector(self, ctx):
        """Return (n_genes,) array of essentiality proxy, NaN where unavailable."""
        cache = ctx.cache
        key = "_coess_e744_vec"
        if key in cache:
            return cache[key]

        n = ctx.n_genes
        vec = np.full(n, np.nan, dtype=float)

        kn = None
        try:
            kn = ctx.knowledge("gene_constraint")
        except Exception:
            kn = None
        if kn is None:
            try:
                avail = ctx.available_knowledge()
            except Exception:
                avail = []
            for name in avail:
                if "constraint" in str(name).lower():
                    try:
                        kn = ctx.knowledge(name)
                    except Exception:
                        kn = None
                    if kn is not None:
                        break

        if kn is not None and isinstance(kn, dict):
            cols = kn.get("columns", [])
            genes_tbl = kn.get("genes", {}) or {}
            # find LOEUF column index
            idx = None
            for j, c in enumerate(cols):
                cl = str(c).lower()
                if "oe_lof_upper" in cl or cl == "loeuf":
                    idx = j
                    break
            if idx is None:
                # fallback: pLI column
                for j, c in enumerate(cols):
                    if "pli" in str(c).lower():
                        idx = j
                        break
            if idx is not None:
                for g, vals in genes_tbl.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    if not isinstance(vals, (list, tuple)) or len(vals) <= idx:
                        continue
                    v = vals[idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vec[gi] = fv

        # Convert LOEUF (low = essential) to essentiality score (high = essential).
        # Use -log(LOEUF) which is monotone decreasing in LOEUF.
        valid = np.isfinite(vec) & (vec > 0)
        ess = np.full(n, np.nan, dtype=float)
        ess[valid] = -np.log(vec[valid])

        # z-score over valid entries for scale-free distance
        if np.any(np.isfinite(ess)):
            mu = np.nanmean(ess)
            sd = np.nanstd(ess)
            if sd > 0 and np.isfinite(sd):
                ess = (ess - mu) / sd

        cache[key] = ess
        return ess

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        use_proxy = bool(params.get("use_constraint_proxy", True))
        scale = float(params.get("scale", 1.0))
        if not np.isfinite(scale) or scale <= 0:
            scale = 1.0

        ess = self._essentiality_vector(ctx)

        # Fill missing essentiality with 0 (mean after z-scoring)
        ess_filled = np.where(np.isfinite(ess), ess, 0.0)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # average essentiality proxy across target genes
            tvals = ess_filled[tgt_idx]
            tp = float(np.mean(tvals))
            if not np.isfinite(tp):
                continue
            diff = np.abs(ess_filled - tp)
            sim = np.exp(-diff / scale)
            out[i, :, 0] = sim

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
