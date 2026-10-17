import numpy as np
from genemila.features.api import Feature, register


@register
class PathwayOverlapWeightedByEssentiality(Feature):
    name = "pathway_overlap_weighted_by_essentiality_e516"
    version = 1
    description = ("Product of (1 - LOEUF of the perturbation target) and the number of "
                   "prior gene sets containing both the target gene and gene g.")
    rationale = ("Essential targets may have stronger pathway-level effects, so weighting "
                 "pathway overlap by target essentiality could improve predictions.")
    inputs = ["target_genes", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Build gene -> set of gene-set indices membership map from gene_sets knowledge.
        gene_sets = ctx.knowledge("gene_sets")
        if not gene_sets:
            return out

        gene_index = ctx.gene_index
        # Map each gene to a set of set-ids (integers) it belongs to.
        memberships = {}
        for sid, (set_name, genes) in enumerate(gene_sets.items()):
            for g in genes:
                gi = gene_index.get(g)
                if gi is None:
                    continue
                memberships.setdefault(gi, set()).add(sid)

        # LOEUF per gene from gene_constraint knowledge.
        loeuf = np.full(n_genes, np.nan, dtype=float)
        constraint = ctx.knowledge("gene_constraint")
        cols = None
        if constraint:
            cols = constraint.get("columns", [])
            gene_data = constraint.get("genes", {})
            if "oe_lof_upper" in cols:
                idx = cols.index("oe_lof_upper")
                for g, vals in gene_data.items():
                    gi = gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    v = vals[idx]
                    if v is None:
                        continue
                    try:
                        loeuf[gi] = float(v)
                    except (TypeError, ValueError):
                        continue

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            # Use first target with a valid index and LOEUF.
            tgi = None
            t_loeuf = None
            for tg in targets:
                gi = gene_index.get(tg)
                if gi is None:
                    continue
                if tgi is None:
                    tgi = gi
                v = loeuf[gi]
                if np.isfinite(v):
                    tgi = gi
                    t_loeuf = v
                    break
            if tgi is None:
                continue
            if t_loeuf is None or not np.isfinite(t_loeuf):
                # fall back: no essentiality info -> weight 1.0
                weight = 1.0
            else:
                weight = 1.0 - t_loeuf

            t_sets = memberships.get(tgi)
            if not t_sets:
                continue
            t_sets = np.fromiter(t_sets, dtype=np.int64, count=len(t_sets))
            t_sorted = np.sort(t_sets)

            for gi, g_sets in memberships.items():
                g_arr = np.fromiter(g_sets, dtype=np.int64, count=len(g_sets))
                # count intersection
                count = np.intersect1d(t_sorted, np.sort(g_arr), assume_unique=True).size
                if count > 0:
                    out[i, gi, 0] = weight * count

        return out
