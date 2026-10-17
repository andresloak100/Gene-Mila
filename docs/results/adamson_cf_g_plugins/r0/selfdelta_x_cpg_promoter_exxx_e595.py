import numpy as np
from genemila.features.api import Feature, register


@register
class SelfDeltaXCpgPromoterE595(Feature):
    name = "selfdelta_x_cpg_promoter_exxx_e595"
    version = 1
    description = "target_self_delta_e54 multiplied by promoter CpG o/e ratio of gene g."
    rationale = ("CpG-rich promoters are active/inducible; combining them with the "
                 "target's self-delta captures condition-specific responsiveness.")
    inputs = ["control_cells", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        ng = ctx.n_genes
        out = np.zeros((n, ng, 1), dtype=float)

        # Fetch target self-delta from the existing self-delta feature.
        try:
            selfdelta = ctx.feature("target_self_delta_e54", perts)
        except Exception:
            selfdelta = None

        if selfdelta is not None:
            selfdelta = np.asarray(selfdelta, dtype=float)
            if selfdelta.ndim == 2:
                selfdelta = selfdelta[:, :, None]
        else:
            # Fallback: compute per-perturbation self-delta from training deltas.
            selfdelta = np.zeros((n, ng, 1), dtype=float)
            for i, p in enumerate(perts):
                tgt = ctx.target_indices(p)
                if not tgt:
                    continue
                try:
                    _, d = ctx.train_delta(exclude=p)
                    vec = d.mean(axis=0)
                except Exception:
                    vec = np.zeros(ng, dtype=float)
                for g in tgt:
                    selfdelta[i, g, 0] = vec[g]

        # CpG o/e promoter per gene.
        cpg = np.full(ng, np.nan, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_map = ann.get("genes", {}) if isinstance(ann, dict) else {}
            cols = ann.get("columns", []) if isinstance(ann, dict) else []
            try:
                ci = cols.index("cpg_oe_promoter")
            except ValueError:
                ci = None
            if ci is not None:
                for j, sym in enumerate(ctx.genes):
                    vals = genes_map.get(sym)
                    if vals is None:
                        continue
                    try:
                        v = vals[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        cpg[j] = fv

        # Replace missing CpG values with the mean of observed ones (or 1.0).
        finite_mask = np.isfinite(cpg)
        if finite_mask.any():
            fill = float(cpg[finite_mask].mean())
        else:
            fill = 1.0
        cpg = np.where(finite_mask, cpg, fill)

        out[:, :, 0] = selfdelta[:, :, 0] * cpg[None, :]

        # Sanitize non-finite values.
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
