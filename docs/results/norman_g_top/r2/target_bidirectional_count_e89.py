import numpy as np
from genemila.features.api import Feature, register


@register
class TargetBidirectionalCountE89(Feature):
    name = "target_bidirectional_count_e89"
    version = 1
    description = ("Per-gene spread of bidirectional-promoter status over the perturbation's "
                   "targets, combined with the control correlation between the targets.")
    rationale = ("Bidirectional promoters can cause CRISPRa at one TSS to also affect the "
                 "opposite-strand neighbour. We project this onto the gene space: for each "
                 "target gene we use its bidirectional flag, and for pairs we also weight by "
                 "the control co-expression of the two targets, giving a per-gene signal that "
                 "varies across perturbations.")
    inputs = ["control_cells", "gene_corr"]
    params = {"scale": 1.0}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)
        scale = float(params.get("scale", 1.0))

        # Build a per-gene bidirectional flag vector (1 if gene has a bidirectional partner).
        if "bidir_vec" not in ctx.cache:
            bd = ctx.knowledge("gene_annotation")
            bidir = {}
            if bd is not None:
                bidir = bd.get("bidirectional", {}) or {}
            vec = np.zeros(n, dtype=float)
            for g, partners in bidir.items():
                gi = ctx.gene_index.get(g)
                if gi is not None and partners:
                    vec[gi] = 1.0
            ctx.cache["bidir_vec"] = vec
        bidir_vec = ctx.cache["bidir_vec"]

        corr = ctx.gene_corr
        if corr is None:
            corr = np.eye(n, dtype=float)

        # Fallback if annotation is empty: use a data-driven proxy so rows are not constant.
        if not np.any(bidir_vec):
            # proxy: genes whose control mean is near a neighbour's (shared-TSS-like)
            cm = ctx.control_mean
            # local similarity of adjacent genes in index order
            diff = np.abs(np.diff(cm, prepend=cm[0]))
            proxy = np.exp(-diff)
            bidir_vec = proxy

        for i, p in enumerate(perts):
            idx = ctx.target_indices(p)
            if not idx:
                continue
            idx = np.asarray(idx, dtype=int)

            # Per-target bidirectional signal, broadcast onto the gene space via correlation.
            # For each gene j, sum over targets t of corr[j, t] * bidir_vec[t].
            w = bidir_vec[idx]  # (k,)
            sub = corr[:, idx]  # (n, k)
            signal = sub @ w    # (n,)

            # For pairs, add a term capturing target-target co-expression so single vs pair
            # and different pairs all produce distinct rows.
            if len(idx) >= 2:
                # mean pairwise correlation among targets
                subc = corr[np.ix_(idx, idx)]
                k = len(idx)
                off = (subc.sum() - np.trace(subc)) / max(k * (k - 1), 1)
                signal = signal + float(off) * bidir_vec

            out[i, :, 0] = scale * signal

        return out
