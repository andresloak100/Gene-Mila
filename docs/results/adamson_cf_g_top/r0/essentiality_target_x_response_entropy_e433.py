import numpy as np
from genemila.features.api import Feature, register


@register
class EssentialityTargetXResponseEntropy(Feature):
    name = "essentiality_target_x_response_entropy_e433"
    version = 1
    description = (
        "For each (p,g): (1 - LOEUF_target) * response_entropy_e89, "
        "interaction of target essentiality with per-gene response entropy."
    )
    rationale = (
        "Essential targets may cause stronger downstream effects; genes with high "
        "response entropy are more likely to be affected. Their interaction may "
        "capture condition-specific sensitivity."
    )
    inputs = ["control_cells", "train_delta"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Per-gene response entropy across training perturbations (leave-one-out safe
        # because it is a global statistic over training perturbations; we recompute
        # per-perturbation to respect the leakage rule where feasible).
        # Precompute LOEUF map from prior knowledge.
        loeuf = {}
        try:
            gc = ctx.knowledge("gene_constraint")
        except Exception:
            gc = None
        if gc is not None and isinstance(gc, dict):
            cols = gc.get("columns", [])
            genes_map = gc.get("genes", {})
            if "oe_lof_upper" in cols:
                idx = cols.index("oe_lof_upper")
                for sym, vals in genes_map.items():
                    if vals is not None and len(vals) > idx and vals[idx] is not None:
                        try:
                            loeuf[sym] = float(vals[idx])
                        except (TypeError, ValueError):
                            pass

        def one_minus_loeuf(sym):
            v = loeuf.get(sym, None)
            if v is None or not np.isfinite(v):
                return 0.0
            val = 1.0 - v
            if not np.isfinite(val):
                return 0.0
            return float(val)

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            if d.shape[0] == 0:
                continue
            # Response entropy per gene: Shannon entropy of delta magnitudes.
            # Use absolute normalized delta as a distribution proxy per gene.
            absd = np.abs(d)
            colsum = absd.sum(axis=0)
            safe = colsum > 0
            entropy = np.zeros(n_genes, dtype=float)
            if np.any(safe):
                probs = np.zeros_like(absd)
                probs[:, safe] = absd[:, safe] / colsum[safe]
                # entropy = -sum p log p
                with np.errstate(divide="ignore", invalid="ignore"):
                    plogp = np.where(probs > 0, probs * np.log(probs), 0.0)
                entropy = -plogp.sum(axis=0)
            entropy = np.nan_to_num(entropy, nan=0.0, posinf=0.0, neginf=0.0)

            # Target essentiality factor
            targets = ctx.target_genes(p)
            ess = 0.0
            if targets:
                vals = [one_minus_loeuf(t) for t in targets]
                ess = float(np.mean(vals)) if vals else 0.0
            if not np.isfinite(ess):
                ess = 0.0

            out[i, :, 0] = ess * entropy

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
