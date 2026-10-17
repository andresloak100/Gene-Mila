import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneSharedDomainCountE589(Feature):
    name = "target_gene_shared_domain_count_e589"
    version = 1
    description = "Number of shared protein domains between target and gene."
    rationale = ("Genes sharing protein domains with the perturbation target may be "
                 "functionally related and respond more strongly.")
    inputs = ["protein_annotation", "target_indices"]
    params = {"normalize": "none"}
    dim = 1

    def _build_domain_sets(self, ctx):
        cache = ctx.cache
        key = "__shared_domain_sets_e589__"
        if key in cache:
            return cache[key]

        pa = ctx.knowledge("protein_annotation")
        gene_domains = {}
        if isinstance(pa, dict):
            genes_map = pa.get("genes", {})
            columns = pa.get("columns", [])
            if not isinstance(columns, list):
                columns = []
            # Identify domain-like columns: names containing 'domain'
            dom_col_idx = [i for i, c in enumerate(columns)
                           if isinstance(c, str) and "domain" in c.lower()]
            if not dom_col_idx:
                # Fallback: treat all protein_annotation columns as potential features
                dom_col_idx = list(range(len(columns)))
            for g, vals in genes_map.items():
                if not isinstance(vals, (list, tuple)):
                    continue
                doms = set()
                for idx in dom_col_idx:
                    if idx < len(vals):
                        v = vals[idx]
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv) and fv != 0.0:
                            doms.add((columns[idx] if idx < len(columns) else idx, fv))
                gene_domains[g] = doms
        cache[key] = gene_domains
        return gene_domains

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)
        gene_domains = self._build_domain_sets(ctx)
        normalize = params.get("normalize", "none") if params else "none"

        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if not tidx:
                continue
            target_doms = set()
            for ti in tidx:
                if 0 <= ti < ctx.n_genes:
                    tg = ctx.genes[ti]
                    target_doms |= gene_domains.get(tg, set())
            tcount = len(target_doms)
            if tcount == 0:
                continue
            for gi in range(ctx.n_genes):
                g = ctx.genes[gi]
                gd = gene_domains.get(g)
                if not gd:
                    continue
                shared = len(target_doms & gd)
                if shared == 0:
                    continue
                val = float(shared)
                if normalize == "target":
                    val = val / tcount
                elif normalize == "union":
                    union = len(target_doms | gd)
                    val = val / union if union > 0 else 0.0
                out[i, gi, 0] = val
        return out
