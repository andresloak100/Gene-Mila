import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPromoterCpgStrengthXGeneSetE168(Feature):
    name = "target_promoter_cpg_strength_x_gene_set__e168"
    version = 1
    description = "Product of target promoter CpG strength and gene-set similarity to the target."
    rationale = ("CpG-rich target promoters mark broad regulatory programs; genes functionally "
                 "similar to such targets may be more co-regulated and respond more strongly.")
    inputs = ["control_cells", "knowledge"]
    params = {}
    dim = 1

    def _cpg_strength(self, ctx):
        """Per-gene promoter CpG strength from gene_annotation (cpg_oe_promoter)."""
        if "_cpg_strength_vec" in ctx.cache:
            return ctx.cache["_cpg_strength_vec"]
        vec = np.zeros(ctx.n_genes, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None and isinstance(ann, dict):
            cols = ann.get("columns", [])
            genes = ann.get("genes", {}) or {}
            try:
                ci = cols.index("cpg_oe_promoter")
            except ValueError:
                ci = None
            if ci is not None:
                for g, vals in genes.items():
                    idx = ctx.gene_index.get(g)
                    if idx is None or vals is None:
                        continue
                    try:
                        v = vals[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vec[idx] = fv
        ctx.cache["_cpg_strength_vec"] = vec
        return vec

    def _gene_sets(self, ctx):
        if "_gene_set_map" in ctx.cache:
            return ctx.cache["_gene_set_map"]
        gs = ctx.knowledge("gene_sets")
        mapping = {}
        if isinstance(gs, dict):
            for setname, members in gs.items():
                if not isinstance(members, (list, tuple)):
                    continue
                idxs = [ctx.gene_index[g] for g in members if g in ctx.gene_index]
                if idxs:
                    mapping[setname] = np.asarray(idxs, dtype=int)
        ctx.cache["_gene_set_map"] = mapping
        return mapping

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)

        cpg = self._cpg_strength(ctx)
        gene_sets = self._gene_sets(ctx)

        # Build membership sets per gene for Jaccard similarity
        if "_gene_set_membership" in ctx.cache:
            membership = ctx.cache["_gene_set_membership"]
        else:
            membership = [set() for _ in range(ctx.n_genes)]
            for setname, idxs in gene_sets.items():
                for i in idxs:
                    membership[i].add(setname)
            ctx.cache["_gene_set_membership"] = membership

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            # Target promoter CpG strength: average over target genes
            t_cpg = float(np.mean([cpg[t] for t in t_idx]))
            if not np.isfinite(t_cpg):
                t_cpg = 0.0

            # Gene-set similarity: max Jaccard between target gene(s) and each gene g
            target_sets = set()
            for t in t_idx:
                target_sets |= membership[t]

            if target_sets:
                sim = np.zeros(ctx.n_genes, dtype=float)
                tset = target_sets
                tlen = len(tset)
                for g in range(ctx.n_genes):
                    gset = membership[g]
                    if not gset:
                        continue
                    inter = len(tset & gset)
                    if inter == 0:
                        continue
                    union = tlen + len(gset) - inter
                    if union > 0:
                        sim[g] = inter / union
            else:
                sim = np.zeros(ctx.n_genes, dtype=float)

            out[i, :, 0] = t_cpg * sim

        out[~np.isfinite(out)] = 0.0
        return out
