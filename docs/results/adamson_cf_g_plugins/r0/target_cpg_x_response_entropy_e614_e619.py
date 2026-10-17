import numpy as np
from genemila.features.api import Feature, register


@register
class TargetCpgXResponseEntropy(Feature):
    name = "target_cpg_x_response_entropy_e614_e619"
    version = 1
    description = (
        "For each (p,g), product of the CpG observed/expected ratio in the target "
        "gene's promoter and the response_entropy_e89 of gene g."
    )
    rationale = (
        "Perturbations of targets with high promoter CpG density may produce more "
        "variable responses in genes with high response entropy; combining target "
        "promoter CpG density with gene response entropy captures regulatory complexity."
    )
    inputs = ["control_cells", "train_delta", "knowledge:gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)

        # --- target promoter CpG o/e ratio from gene_annotation ---
        ann = ctx.knowledge("gene_annotation")
        cpg_vals = {}
        if ann is not None and isinstance(ann, dict):
            cols = ann.get("columns", [])
            genes_tbl = ann.get("genes", {})
            if "cpg_oe_promoter" in cols:
                idx = cols.index("cpg_oe_promoter")
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
                        cpg_vals[g] = fv

        # --- response entropy (leave-one-out) across training perturbations ---
        # Cache the full per-gene entropy computation is not possible for LOO
        # without recomputing, but we can fetch the registered feature if present.
        # Requirement: leave-one-out entropy per perturbation. We compute it directly
        # from train_delta(exclude=p) to respect the leakage rule.
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            # target CpG o/e
            tg = ctx.target_genes(p)
            cpg_target = 0.0
            for t in tg:
                if t in cpg_vals:
                    cpg_target = cpg_vals[t]
                    break
            if not np.isfinite(cpg_target):
                cpg_target = 0.0
            if cpg_target < 0:
                cpg_target = 0.0

            # leave-one-out response entropy
            _, d = ctx.train_delta(exclude=p)
            if d.size == 0:
                ent = np.zeros(n_genes, dtype=float)
            else:
                ent = self._entropy(d)

            out[i, :, 0] = cpg_target * ent

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out

    @staticmethod
    def _entropy(d):
        # d: (n_perts, n_genes). Shannon entropy of delta values per gene.
        # Discretise deltas into bins per gene to compute a distribution.
        n, g = d.shape
        if n == 0:
            return np.zeros(g, dtype=float)
        ent = np.zeros(g, dtype=float)
        # Use a fixed number of bins based on the global range per gene.
        for j in range(g):
            col = d[:, j]
            col = col[np.isfinite(col)]
            if col.size == 0:
                continue
            lo = col.min()
            hi = col.max()
            if hi <= lo:
                continue
            nb = max(2, min(10, col.size))
            counts, _ = np.histogram(col, bins=nb, range=(lo, hi))
            probs = counts.astype(float) / counts.sum()
            probs = probs[probs > 0]
            ent[j] = -np.sum(probs * np.log(probs))
        return ent
