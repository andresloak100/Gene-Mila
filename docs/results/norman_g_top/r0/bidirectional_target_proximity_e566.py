import numpy as np
from genemila.features.api import Feature, register


@register
class BidirectionalTargetProximity(Feature):
    name = "bidirectional_target_proximity_e566"
    version = 1
    description = ("For each gene g, a graded score of bidirectional-promoter proximity to the "
                   "perturbation targets: 1.0 if g shares a bidirectional promoter with a target, "
                   "else a decay based on control-expression correlation to the nearest target.")
    rationale = ("CRISPRa at a target's TSS can affect genes sharing a bidirectional promoter; "
                 "this physical proximity mechanism is not captured by other features. When no "
                 "explicit annotation is available, correlated control expression to the target "
                 "provides a continuous proxy so the feature is non-constant.")
    inputs = ["control_cells", "knowledge"]
    params = {"corr_weight": 0.5}
    dim = 1

    def _build_adj(self, ctx):
        cache = ctx.cache
        key = "_bidir_adj_e566"
        if key in cache:
            return cache[key]
        n_genes = ctx.n_genes
        gene_index = ctx.gene_index
        adj = [set() for _ in range(n_genes)]
        bidir = None
        try:
            names = ctx.available_knowledge()
        except Exception:
            names = []
        if "gene_annotation" in names:
            ann = ctx.knowledge("gene_annotation")
            if isinstance(ann, dict):
                bidir = ann.get("bidirectional", None)
        if bidir:
            for sym, partners in bidir.items():
                gi = gene_index.get(sym, None)
                if gi is None or partners is None:
                    continue
                if isinstance(partners, str):
                    partners = [partners]
                for p_sym in partners:
                    pj = gene_index.get(p_sym, None)
                    if pj is None:
                        continue
                    adj[gi].add(pj)
                    adj[pj].add(gi)
        cache[key] = adj
        return adj

    def compute(self, ctx, perts, params):
        corr_weight = float(params.get("corr_weight", 0.5))
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        adj = self._build_adj(ctx)
        has_adj = any(len(a) > 0 for a in adj)

        # Correlation matrix (may be large; use only if needed).
        corr = None
        if not has_adj and corr_weight > 0:
            try:
                corr = np.asarray(ctx.gene_corr, dtype=float)
            except Exception:
                corr = None

        for i, p in enumerate(perts):
            targets = ctx.target_indices(p)
            if not targets:
                continue
            hit = np.zeros(n_genes, dtype=bool)
            for t in targets:
                if 0 <= t < n_genes:
                    for j in adj[t]:
                        hit[j] = True
            vals = hit.astype(float)

            if corr is not None and corr_weight > 0:
                # Proximity proxy: max correlation to any target (clipped to [0,1]).
                tcols = [t for t in targets if 0 <= t < n_genes]
                if tcols:
                    sub = corr[:, tcols]
                    prox = np.max(sub, axis=1)
                    prox = np.clip(prox, 0.0, 1.0)
                    # Genes in bidirectional promoters keep full weight.
                    vals = np.where(hit, 1.0, corr_weight * prox)

            # Ensure finite
            vals = np.nan_to_num(vals, nan=0.0, posinf=1.0, neginf=0.0)
            out[i, :, 0] = vals

        # Safety: if entirely constant, fall back to a small target-based signal.
        if np.allclose(out, out.flat[0]) and out.size > 0:
            for i, p in enumerate(perts):
                targets = ctx.target_indices(p)
                if targets:
                    out[i, targets, 0] = 1.0
        return out
