import numpy as np
from genemila.features.api import Feature, register


@register
class GeneLoeufXTargetSelfDelta(Feature):
    name = "gene_loeuf_x_target_selfdelta_e569"
    version = 1
    description = "For each (p,g): (1 - LOEUF of gene g) multiplied by target_self_delta_e54."
    rationale = (
        "Essential genes (low LOEUF) may buffer or alter the self-delta response; "
        "interacting gene essentiality with the target self-delta captures this modulation."
    )
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)

        # --- LOEUF per gene from gene_constraint ---
        # Default LOEUF = 1.0 -> (1 - LOEUF) = 0 for genes without constraint data.
        loeuf = np.ones(n_genes, dtype=float)
        try:
            gc = ctx.knowledge("gene_constraint")
        except Exception:
            gc = None

        if gc:
            cols = gc.get("columns", [])
            try:
                loeuf_idx = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            genes_map = gc.get("genes", {}) or {}
            if loeuf_idx is not None:
                for gname, vals in genes_map.items():
                    gi = ctx.gene_index.get(gname)
                    if gi is None:
                        continue
                    try:
                        v = vals[loeuf_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(v):
                        loeuf[gi] = v

        # Clamp LOEUF to a sane range so (1 - LOEUF) is finite.
        loeuf = np.clip(loeuf, 0.0, 2.0)
        essentiality = 1.0 - loeuf  # (n_genes,)

        # --- target_self_delta_e54: self delta of the perturbation target ---
        # Try composition via the feature API first; fall back to computing
        # directly from training deltas if the feature is unavailable.
        self_delta = None
        try:
            self_delta = ctx.feature("target_self_delta_e54", perts)
        except Exception:
            self_delta = None

        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        if self_delta is not None:
            sd = np.asarray(self_delta, dtype=float)
            # Normalise to (n_perts, n_genes)
            if sd.ndim == 3:
                sd = sd[:, :, 0]
            elif sd.ndim == 1:
                sd = sd.reshape(n_perts, -1)
            if sd.shape != (n_perts, n_genes):
                # Attempt to coerce; otherwise fall back.
                if sd.size == n_perts * n_genes:
                    sd = sd.reshape(n_perts, n_genes)
                else:
                    self_delta = None

        if self_delta is not None:
            sd = np.asarray(self_delta, dtype=float)
            if sd.ndim == 3:
                sd = sd[:, :, 0]
            if sd.shape == (n_perts, n_genes):
                out[:, :, 0] = sd * essentiality[None, :]
                out[~np.isfinite(out)] = 0.0
                return out

        # --- Fallback: compute target self-delta directly from train deltas ---
        # target_self_delta_e54: for perturbation p, the delta at its target gene(s),
        # broadcast to all genes g (so every gene g gets the target's self-delta).
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            try:
                _, d = ctx.train_delta(exclude=p)
            except Exception:
                continue
            if d is None or len(d) == 0:
                continue
            d = np.asarray(d, dtype=float)
            # Mean delta at the target gene(s) across training perturbations.
            self_val = float(np.mean(d[:, tgt_idx]))
            if not np.isfinite(self_val):
                continue
            # Broadcast target self-delta across genes, modulated by essentiality.
            out[i, :, 0] = self_val * essentiality

        out[~np.isfinite(out)] = 0.0
        return out
