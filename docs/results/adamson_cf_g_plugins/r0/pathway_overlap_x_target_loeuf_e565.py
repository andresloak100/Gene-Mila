import numpy as np
from genemila.features.api import Feature, register


@register
class PathwayOverlapXTargetLoeufE565(Feature):
    name = "pathway_overlap_x_target_loeuf_e565"
    version = 1
    description = (
        "For each (p,g): pathway overlap fraction between target of p and gene g, "
        "multiplied by (1 - LOEUF_target)."
    )
    rationale = (
        "Genes sharing pathways with the target respond more strongly when the target "
        "is essential (low LOEUF), because essential targets have broader downstream effects."
    )
    inputs = ["knowledge", "target_genes", "feature"]
    params = {}
    dim = 1

    def _loeuf_map(self, ctx):
        key = "_loeuf_map_e565"
        if key in ctx.cache:
            return ctx.cache[key]
        loeuf = {}
        gc = ctx.knowledge("gene_constraint")
        if gc is not None:
            cols = gc.get("columns", [])
            genes_tbl = gc.get("genes", {})
            if "oe_lof_upper" in cols:
                idx = cols.index("oe_lof_upper")
                for sym, vals in genes_tbl.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        loeuf[sym] = fv
        ctx.cache[key] = loeuf
        return loeuf

    def _gene_sets_index(self, ctx):
        key = "_genesets_index_e565"
        if key in ctx.cache:
            return ctx.cache[key]
        gs = ctx.knowledge("gene_sets")
        gene_to_sets = {}
        if gs is not None:
            for set_name, members in gs.items():
                if not members:
                    continue
                for m in members:
                    gene_to_sets.setdefault(m, set()).add(set_name)
        ctx.cache[key] = gene_to_sets
        return gene_to_sets

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        loeuf = self._loeuf_map(ctx)
        gene_to_sets = self._gene_sets_index(ctx)

        # Precompute per-gene set membership (as sets of names) for measured genes
        gene_sets = [gene_to_sets.get(g, set()) for g in ctx.genes]
        gene_has_sets = np.array([len(s) > 0 for s in gene_sets], dtype=bool)

        # Default essentiality weight when LOEUF unavailable
        default_weight = 0.5

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            # Build union of pathway sets containing any target
            target_sets = set()
            for t in targets:
                target_sets |= gene_to_sets.get(t, set())
            if not target_sets:
                continue
            n_ts = len(target_sets)

            # Overlap fraction for each gene
            overlap = np.zeros(n_genes, dtype=float)
            for j in range(n_genes):
                if not gene_has_sets[j]:
                    continue
                inter = len(gene_sets[j] & target_sets)
                if inter:
                    overlap[j] = inter / n_ts

            # Essentiality weight: (1 - LOEUF_target), averaged over targets
            weights = []
            for t in targets:
                if t in loeuf:
                    weights.append(max(0.0, min(1.0, 1.0 - loeuf[t])))
            if weights:
                w = float(np.mean(weights))
            else:
                w = default_weight

            out[i, :, 0] = overlap * w

        # Ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
