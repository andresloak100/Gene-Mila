import numpy as np
from genemila.features.api import Feature, register


@register
class ResponseEntropyTargetEssentialityIntE389(Feature):
    name = "response_entropy_target_essentiality_int_e389"
    version = 1
    description = (
        "For each (p,g): response_entropy_e89 * (1 - LOEUF_target), where "
        "response_entropy_e89 is the per-gene Shannon entropy of delta values "
        "across training perturbations and LOEUF_target is the loss-of-function "
        "intolerance of the target gene."
    )
    rationale = (
        "Genes with high response entropy respond differently depending on target "
        "essentiality; the interaction term captures this. Essential targets may "
        "produce more consistent or stronger effects, and multiplying entropy by "
        "(1 - LOEUF_target) may enhance signal."
    )
    inputs = ["train_delta", "knowledge", "target_genes"]
    params = {}
    dim = 1

    def _get_loeuf_map(self, ctx):
        cache = ctx.cache
        if "e389_loeuf" in cache:
            return cache["e389_loeuf"]
        loeuf = {}
        median = None
        try:
            k = ctx.knowledge("gene_constraint")
        except Exception:
            k = None
        if k:
            genes = k.get("genes", {}) or {}
            cols = k.get("columns", []) or []
            try:
                idx = list(cols).index("oe_lof_upper")
            except ValueError:
                idx = None
            vals = []
            if idx is not None:
                for g, row in genes.items():
                    try:
                        v = row[idx]
                    except Exception:
                        v = None
                    if v is not None:
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            fv = None
                        if fv is not None and np.isfinite(fv):
                            loeuf[g] = fv
                            vals.append(fv)
            if vals:
                median = float(np.median(vals))
        if median is None:
            median = 1.0
        cache["e389_loeuf"] = (loeuf, median)
        return cache["e389_loeuf"]

    def compute(self, ctx, perts, params):
        n = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n, n_genes, 1), dtype=float)

        loeuf_map, loeuf_median = self._get_loeuf_map(ctx)

        # Compute response entropy per gene from training deltas (leave-one-out).
        # Entropy of delta values across perturbations: use a normalized
        # distribution over |delta| magnitudes.
        ent_cache = {}

        def entropy_for(exclude):
            if exclude in ent_cache:
                return ent_cache[exclude]
            _, d = ctx.train_delta(exclude=exclude)
            d = np.asarray(d, dtype=float)
            if d.ndim != 2 or d.shape[0] == 0:
                ent = np.zeros(n_genes, dtype=float)
            else:
                a = np.abs(d)
                # Normalize per gene into a probability distribution over perts.
                col_sum = a.sum(axis=0)
                safe = col_sum > 0
                ent = np.zeros(n_genes, dtype=float)
                if np.any(safe):
                    p = a[:, safe] / col_sum[safe][None, :]
                    # Shannon entropy in nats, normalized by log(n_perts) to [0,1]
                    with np.errstate(divide="ignore", invalid="ignore"):
                        plogp = np.where(p > 0, p * np.log(p), 0.0)
                    h = -plogp.sum(axis=0)
                    denom = np.log(d.shape[0]) if d.shape[0] > 1 else 1.0
                    if denom <= 0:
                        denom = 1.0
                    ent[safe] = h / denom
            ent_cache[exclude] = ent
            return ent

        for i, p in enumerate(perts):
            ent = entropy_for(p)
            # Determine target essentiality factor (1 - LOEUF_target).
            targets = []
            try:
                targets = ctx.target_genes(p)
            except Exception:
                targets = []
            if not targets:
                try:
                    targets = [ctx.genes[j] for j in ctx.target_indices(p)]
                except Exception:
                    targets = []
            if targets:
                loeuf_vals = [loeuf_map.get(t, loeuf_median) for t in targets]
                loeuf_t = float(np.mean(loeuf_vals))
            else:
                loeuf_t = loeuf_median
            factor = 1.0 - loeuf_t
            out[i, :, 0] = ent * factor

        # Ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
