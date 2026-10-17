import numpy as np
from genemila.features.api import Feature, register

# Hydrophobic amino acids per the hypothesis: A, I, L, M, F, W, Y, V
_HYDROPHOBIC = ("aa_A", "aa_I", "aa_L", "aa_M", "aa_F", "aa_W", "aa_Y", "aa_V")


@register
class TargetHydrophobicFractionE675(Feature):
    name = "target_hydrophobic_fraction_e675"
    version = 1
    description = (
        "Mean over the perturbation's target genes of the fraction of amino acids "
        "that are hydrophobic (sum of aa_A, aa_I, aa_L, aa_M, aa_F, aa_W, aa_Y, aa_V)."
    )
    rationale = (
        "Evolutionary conservation of the target modulates response magnitude; "
        "hydrophobic residue fraction is a proxy for conserved, buried protein core "
        "content and thus for the target's evolutionary constraint."
    )
    inputs = ["knowledge:gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=np.float64)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        genes = ann.get("genes") if isinstance(ann, dict) else None
        columns = ann.get("columns") if isinstance(ann, dict) else None
        if not genes or not columns:
            return out

        # Map hydrophobic amino-acid column names to their positions once.
        col_index = {}
        for j, c in enumerate(columns):
            col_index[c] = j

        # Precompute each gene's hydrophobic fraction once (memoised in ctx.cache).
        cache = ctx.cache
        key = "_e675_hydro_frac"
        frac = cache.get(key)
        if frac is None:
            frac = {}
            for sym, vals in genes.items():
                if vals is None:
                    continue
                s = 0.0
                ok = False
                for name in _HYDROPHOBIC:
                    j = col_index.get(name)
                    if j is None:
                        continue
                    v = vals[j]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        s += fv
                        ok = True
                if ok:
                    frac[sym] = s
            cache[key] = frac

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            vals = [frac[g] for g in targets if g in frac]
            if vals:
                out[i, :, 0] = float(np.mean(vals))

        out[~np.isfinite(out)] = 0.0
        return out
