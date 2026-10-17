import numpy as np
from genemila.features.api import Feature, register


@register
class CoessentialityInteractionE289(Feature):
    name = "coessentiality_interaction_e289"
    version = 1
    description = (
        "For each (p,g): a co-essentiality proxy between the perturbation target and gene g, "
        "scaled by the target's average self-delta across training perturbations (leave-p-out). "
        "Co-essentiality proxy = (1-LOEUF_target)*(1-LOEUF_g) modulated by PPI/prior-network "
        "connectivity between target and g, falling back to the plain essentiality product."
    )
    rationale = (
        "Genes that are co-essential (functionally dependent) tend to reside in shared pathways; "
        "perturbing one may shift the other's expression. We approximate co-essentiality with "
        "LoF-constraint (LOEUF) and network connectivity from PPI/prior knowledge, and weight it by "
        "the observed self-delta of the target so the effect magnitude matches measured responses."
    )
    inputs = ["train_delta", "knowledge"]
    params = {"network_weight": 0.5}
    dim = 1

    def _loeuf(self, ctx):
        cache = ctx.cache
        key = "_e289_loeuf"
        if key in cache:
            return cache[key]
        vals = np.full(ctx.n_genes, np.nan, dtype=float)
        kn = ctx.knowledge("gene_constraint")
        if kn is not None and isinstance(kn, dict):
            genes = kn.get("genes", {}) or {}
            cols = kn.get("columns", []) or []
            try:
                idx = list(cols).index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                for g, v in genes.items():
                    j = ctx.gene_index.get(g)
                    if j is None:
                        continue
                    try:
                        val = v[idx]
                    except Exception:
                        continue
                    if val is None:
                        continue
                    try:
                        fv = float(val)
                    except Exception:
                        continue
                    if np.isfinite(fv):
                        vals[j] = fv
        # Fill missing with median of observed (or 1.0 if none)
        obs = vals[np.isfinite(vals)]
        fill = float(np.median(obs)) if obs.size else 1.0
        vals = np.where(np.isfinite(vals), vals, fill)
        # essentiality score in [0,1]: (1 - LOEUF), clipped at 0
        ess = np.clip(1.0 - vals, 0.0, None)
        cache[key] = ess
        return ess

    def _network_adj(self, ctx):
        cache = ctx.cache
        key = "_e289_net"
        if key in cache:
            return cache[key]
        n = ctx.n_genes
        adj = np.zeros(n, dtype=float)  # placeholder, we build sparse dict of pairs
        pairs = {}
        for kname in ("ppi_network", "prior_network"):
            kn = ctx.knowledge(kname)
            if kn is None:
                continue
            try:
                entries = kn if isinstance(kn, list) else kn.get("edges", [])
            except Exception:
                entries = []
            if not isinstance(entries, list):
                continue
            for e in entries:
                if not isinstance(e, (list, tuple)) or len(e) < 2:
                    continue
                a, b = e[0], e[1]
                try:
                    w = float(e[2]) if len(e) > 2 else 1.0
                except Exception:
                    w = 1.0
                if not np.isfinite(w):
                    w = 1.0
                ia = ctx.gene_index.get(a)
                ib = ctx.gene_index.get(b)
                if ia is None or ib is None or ia == ib:
                    continue
                key_ab = (ia, ib) if ia < ib else (ib, ia)
                prev = pairs.get(key_ab)
                if prev is None or w > prev:
                    pairs[key_ab] = w
        cache[key] = pairs
        return pairs

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)
        net_w = float(params.get("network_weight", 0.5))
        ess = self._loeuf(ctx)
        pairs = self._network_adj(ctx)

        # Normalize network weights to [0,1] for a bounded modulation factor
        if pairs:
            wvals = np.array(list(pairs.values()), dtype=float)
            wmax = float(wvals.max()) if wvals.size else 1.0
            if not np.isfinite(wmax) or wmax <= 0:
                wmax = 1.0
        else:
            wmax = 1.0

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            self_delta = float(d.mean()) if d.size else 0.0
            if not np.isfinite(self_delta):
                self_delta = 0.0

            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                # No measured target: fall back to generic essentiality-weighted self-delta
                out[i, :, 0] = self_delta * ess
                continue

            # Aggregate over targets (typically one)
            ess_t = float(np.mean([ess[t] for t in tgt_idx]))
            row = np.empty(n, dtype=float)
            for g in range(n):
                # base co-essentiality product
                base = ess_t * ess[g]
                # network modulation: average connectivity from any target to g
                net = 0.0
                for t in tgt_idx:
                    if t == g:
                        net = max(net, 1.0)
                        continue
                    k = (t, g) if t < g else (g, t)
                    w = pairs.get(k)
                    if w is not None:
                        net = max(net, w / wmax)
                mod = 1.0 + net_w * net
                row[g] = self_delta * base * mod

            out[i, :, 0] = row

        # Ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
