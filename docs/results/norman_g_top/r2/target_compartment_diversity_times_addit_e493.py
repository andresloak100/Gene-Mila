import numpy as np
from genemila.features.api import Feature, register

_COMPARTMENTS = [
    "secreted", "membrane", "endoplasmic_reticulum", "golgi",
    "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
]


@register
class TargetCompartmentDiversityTimesAdditiveE493(Feature):
    name = "target_compartment_diversity_times_addit_e493"
    version = 1
    description = (
        "Entropy of subcellular compartment flags across perturbation targets, "
        "multiplied by additive_response."
    )
    rationale = (
        "Targets in diverse compartments may couple differently; entropy captures "
        "functional compartment spread orthogonal to existing features."
    )
    inputs = ["protein_annotation", "additive_response"]
    params = {}
    dim = 1

    def _compartment_matrix(self, ctx):
        """Return (n_genes, n_compartments) 0/1 matrix from protein_annotation."""
        cache = ctx.cache
        key = "_e493_compartment_matrix"
        if key in cache:
            return cache[key]

        n_genes = ctx.n_genes
        n_comp = len(_COMPARTMENTS)
        mat = np.zeros((n_genes, n_comp), dtype=np.float64)

        ann = ctx.knowledge("protein_annotation")
        if ann is not None:
            cols = ann.get("columns", [])
            genes_tbl = ann.get("genes", {})
            # map compartment flag columns to indices
            col_idx = {}
            for c in _COMPARTMENTS:
                if c in cols:
                    col_idx[c] = cols.index(c)
            for gi, g in enumerate(ctx.genes):
                vals = genes_tbl.get(g)
                if vals is None:
                    continue
                for ci, c in enumerate(_COMPARTMENTS):
                    j = col_idx.get(c)
                    if j is None:
                        continue
                    v = vals[j]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv) and fv > 0:
                        mat[gi, ci] = 1.0

        cache[key] = mat
        return mat

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=np.float64)

        comp_mat = self._compartment_matrix(ctx)
        n_comp = comp_mat.shape[1]

        # additive_response feature, shape (n, n_genes, dim)
        try:
            add = ctx.feature("additive_response", perts, params=None)
            add = np.asarray(add, dtype=np.float64)
            if add.ndim == 3:
                add = add[:, :, 0]
            elif add.ndim == 2:
                pass
            else:
                add = np.zeros((n, ctx.n_genes))
        except Exception:
            add = np.zeros((n, ctx.n_genes))

        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if not tgt:
                ent = 0.0
            else:
                flags = comp_mat[tgt, :]  # (n_targets, n_comp)
                counts = flags.sum(axis=0)
                total = counts.sum()
                if total <= 0:
                    ent = 0.0
                else:
                    probs = counts / total
                    nz = probs[probs > 0]
                    ent = float(-(nz * np.log(nz)).sum())
            out[i, :, 0] = ent * add[i, :]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
