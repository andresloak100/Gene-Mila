import numpy as np
from genemila.features.api import Feature, register


@register
class TargetAaPFractionE235(Feature):
    name = "target_aa_p_fraction_e235"
    version = 1
    description = "Fraction of proline residues in the protein of the targeted gene p, broadcast to all genes g."
    rationale = (
        "Proline-rich proteins often act as scaffolds; their perturbation may be "
        "buffered by network redundancy, so targets with higher proline fraction "
        "may yield dampened expression changes."
    )
    inputs = ["gene_annotation", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        aa_p_map = {}
        if ann is not None:
            genes_tbl = ann.get("genes", {}) if isinstance(ann, dict) else {}
            cols = ann.get("columns", []) if isinstance(ann, dict) else []
            try:
                p_idx = list(cols).index("aa_P")
            except ValueError:
                p_idx = None
            if p_idx is not None:
                for sym, vals in genes_tbl.items():
                    try:
                        v = vals[p_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        aa_p_map[sym] = fv

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            vals = [aa_p_map[t] for t in targets if t in aa_p_map]
            if vals:
                out[i, :, 0] = float(np.mean(vals))
            else:
                out[i, :, 0] = 0.0

        out[~np.isfinite(out)] = 0.0
        return out
