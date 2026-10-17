import numpy as np
from genemila.features.api import Feature, register


@register
class NearestTargetTssDistanceE189(Feature):
    name = "nearest_target_tss_distance_e189"
    version = 1
    description = "Min absolute TSS distance (bp) from gene g to any target TSS of perturbation p."
    rationale = ("CRISPRa influence decays with genomic distance from the targeted TSS, so genes "
                 "closer to a target's TSS are more likely to be co-activated; distance to the "
                 "nearest target TSS should correlate with delta magnitude.")
    inputs = ["control_cells", "loci"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        # Load loci prior knowledge
        loci = ctx.knowledge("gene_annotation") or {}
        loci_map = loci.get("loci", {}) if isinstance(loci, dict) else {}

        genes = ctx.genes
        n_genes = ctx.n_genes

        # Precompute TSS per gene column (nan if unknown)
        tss = np.full(n_genes, np.nan, dtype=np.float64)
        for gi, g in enumerate(genes):
            entry = loci_map.get(g)
            if entry is not None and len(entry) >= 2:
                try:
                    t = entry[1]
                    if t is not None:
                        tss[gi] = float(t)
                except (TypeError, ValueError):
                    pass

        # Also need TSS for target genes that may not be measured in ctx.genes.
        # Build a lookup for any gene symbol in loci_map.
        def get_tss(sym):
            e = loci_map.get(sym)
            if e is not None and len(e) >= 2:
                try:
                    if e[1] is not None:
                        return float(e[1])
                except (TypeError, ValueError):
                    return np.nan
            return np.nan

        # Cache target TSS per perturbation id
        cache = ctx.cache
        tss_key = "_e189_target_tss"
        if tss_key not in cache:
            cache[tss_key] = {}
        tss_cache = cache[tss_key]

        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            if p in tss_cache:
                tvals = tss_cache[p]
            else:
                tg = ctx.target_genes(p) or []
                vals = [get_tss(s) for s in tg]
                vals = [v for v in vals if np.isfinite(v)]
                tvals = np.array(vals, dtype=np.float64) if vals else np.array([], dtype=np.float64)
                tss_cache[p] = tvals

            if tvals.size == 0:
                # No usable target TSS: leave zeros (finite)
                continue

            # For each gene g, min |TSS(g) - t|
            g_tss = tss  # (n_genes,)
            # Broadcast: (n_genes, n_targets)
            diff = np.abs(g_tss[:, None] - tvals[None, :])
            mind = np.nanmin(diff, axis=1)
            # Where gene TSS is nan -> nan -> replace with 0? Keep finite only.
            mind = np.where(np.isfinite(mind), mind, 0.0)
            out[i, :, 0] = mind

        return out
