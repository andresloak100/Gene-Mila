import numpy as np
from genemila.features.api import Feature, register


@register
class CoessentialityCorrelationE725(Feature):
    name = "coessentiality_correlation_e725"
    version = 1
    description = ("Pearson correlation between essentiality profiles of the perturbation "
                   "target p and gene g, derived from gnomAD LoF constraint and PPI/prior "
                   "network co-membership as an essentiality proxy.")
    rationale = ("Genes with correlated essentiality across cell lines often function in the "
                 "same pathway or complex; perturbing one may drive compensatory expression "
                 "changes in the other. Without DepMap we approximate co-essentiality via "
                 "shared interaction partners and LoF-intolerance similarity.")
    inputs = ["knowledge", "control_mean"]
    params = {"source": "depmap"}
    dim = 1

    def _load_essentiality_proxy(self, ctx):
        cache = ctx.cache
        key = "_e725_proxy"
        if key in cache:
            return cache[key]

        n = ctx.n_genes
        # LoF-intolerance score per gene from gnomAD constraint (LOEUF-based).
        loeuf = np.full(n, np.nan, dtype=float)
        pLI = np.full(n, np.nan, dtype=float)
        constraint = ctx.knowledge("gene_constraint")
        if constraint is not None:
            cols = constraint.get("columns", [])
            genes = constraint.get("genes", {})
            try:
                i_loeuf = cols.index("oe_lof_upper")
            except ValueError:
                i_loeuf = None
            try:
                i_pli = cols.index("pLI")
            except ValueError:
                i_pli = None
            for g, vals in genes.items():
                idx = ctx.gene_index.get(g)
                if idx is None or vals is None:
                    continue
                if i_loeuf is not None and i_loeuf < len(vals) and vals[i_loeuf] is not None:
                    loeuf[idx] = float(vals[i_loeuf])
                if i_pli is not None and i_pli < len(vals) and vals[i_pli] is not None:
                    pLI[idx] = float(vals[i_pli])

        # Fill missing LoEUF with median; derive essentiality score.
        finite = np.isfinite(loeuf)
        med = np.median(loeuf[finite]) if finite.any() else 1.0
        loeuf_f = np.where(finite, loeuf, med)
        ess = 1.0 / (1.0 + loeuf_f)  # higher = more LoF-intolerant = more essential
        pli_f = np.where(np.isfinite(pLI), pLI, 0.0)
        ess = 0.5 * ess + 0.5 * pli_f

        # Build interaction adjacency (PPI + prior network) as essentiality co-membership proxy.
        adj = np.zeros((n, n), dtype=float)
        for kname, w in (("ppi_network", 1.0), ("prior_network", 1.0)):
            net = ctx.knowledge(kname)
            if not net:
                continue
            for edge in net:
                if len(edge) < 2:
                    continue
                a, b = edge[0], edge[1]
                ia = ctx.gene_index.get(a)
                ib = ctx.gene_index.get(b)
                if ia is None or ib is None:
                    continue
                try:
                    wt = float(edge[2]) if len(edge) > 2 else 1.0
                except (TypeError, ValueError):
                    wt = 1.0
                adj[ia, ib] += w * wt
                adj[ib, ia] += w * wt

        cache[key] = (ess, adj)
        return ess, adj

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        ess, adj = self._load_essentiality_proxy(ctx)
        out = np.zeros((len(perts), n, 1), dtype=float)

        # Precompute row-normalised adjacency for cosine-like similarity.
        deg = adj.sum(axis=1)
        inv = np.where(deg > 0, 1.0 / np.sqrt(deg), 0.0)
        adj_norm = adj * inv[:, None] * inv[None, :]

        ess_centered = ess - ess.mean()

        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if not tgt:
                continue
            # Average over target genes if multiple.
            coess = adj_norm[tgt, :].mean(axis=0)
            # Blend with essentiality-similarity (product of centered scores).
            e_sim = ess_centered[tgt].mean() * ess_centered
            # Normalise each component to comparable scale.
            def _norm(v):
                s = np.std(v)
                return v / s if s > 1e-8 else v
            combined = 0.6 * _norm(coess) + 0.4 * _norm(e_sim)
            out[i, :, 0] = combined

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
