import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveTimesBidirectionalProximityE541(Feature):
    name = "additive_times_bidirectional_proximity_e541"
    version = 1
    description = "Elementwise product of additive_response and a bidirectional-promoter proximity score."
    rationale = ("CRISPRa at a shared bidirectional promoter can activate both genes; "
                 "weighting by inverse TSS distance captures how strongly gene g's promoter "
                 "is shared with a target of p.")
    inputs = ["control_cells", "gene_annotation"]
    params = {"max_distance": 1000}
    dim = 1

    def compute(self, ctx, perts, params):
        max_distance = float(params.get("max_distance", 1000))
        n_genes = ctx.n_genes

        cache = ctx.cache
        if "bidir_tss" not in cache:
            ann = ctx.knowledge("gene_annotation")
            cache["bidir_tss"] = self._build_tss(ctx, ann)
        tss = cache["bidir_tss"]  # (n_genes,) float, nan if unknown

        # additive_response feature
        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add = add[:, :, 0]

        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            t_idx = [ctx.gene_index[t] for t in targets if t in ctx.gene_index]
            if not t_idx:
                continue
            t_tss = tss[t_idx]
            valid_t = np.isfinite(t_tss)
            if not np.any(valid_t):
                continue
            t_tss = t_tss[valid_t]

            g_tss = tss
            valid_g = np.isfinite(g_tss)
            if not np.any(valid_g):
                continue

            # pairwise distances: (n_genes, n_targets)
            diff = np.abs(g_tss[:, None] - t_tss[None, :])
            within = diff <= max_distance
            score = np.where(within, 1.0 / (1.0 + diff), 0.0)
            score = score.max(axis=1)
            score[~valid_g] = 0.0

            out[i, :, 0] = add[i] * score

        return out

    def _build_tss(self, ctx, ann):
        n = ctx.n_genes
        tss = np.full(n, np.nan, dtype=float)
        if not ann:
            return tss
        loci = ann.get("loci")
        if not loci:
            return tss
        for g, idx in ctx.gene_index.items():
            loc = loci.get(g)
            if not loc:
                continue
            try:
                val = float(loc[1])
            except (TypeError, ValueError, IndexError):
                continue
            if np.isfinite(val):
                tss[idx] = val
        return tss
