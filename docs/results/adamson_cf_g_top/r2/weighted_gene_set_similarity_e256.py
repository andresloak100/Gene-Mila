import numpy as np
from genemila.features.api import Feature, register


@register
class WeightedGeneSetSimilarityE256(Feature):
    name = "weighted_gene_set_similarity_e256"
    version = 1
    description = ("Jaccard gene-set similarity between target gene and gene g, "
                   "weighted by a monotonic transform of the target's LOEUF constraint.")
    rationale = ("gene_set_similarity is a weak positive feature; weighting by target "
                 "constraint highlights perturbations that strongly affect essential pathways.")
    inputs = ["knowledge", "target_genes"]
    params = {"weight_transform": "1/(1+loeuf)"}
    dim = 1

    def _build_gene_sets(self, ctx):
        if "gs_membership" in ctx.cache:
            return ctx.cache["gs_membership"]
        gs = ctx.knowledge("gene_sets")
        n = ctx.n_genes
        membership = np.zeros((n,), dtype=object)
        for i in range(n):
            membership[i] = set()
        if gs:
            for _, members in gs.items():
                if not isinstance(members, (list, tuple)):
                    continue
                idxs = [ctx.gene_index[m] for m in members if m in ctx.gene_index]
                for gi in idxs:
                    membership[gi].add(_)
        ctx.cache["gs_membership"] = membership
        return membership

    def _target_loeuf(self, ctx, target_genes):
        key = ("loeuf", tuple(target_genes))
        if key in ctx.cache:
            return ctx.cache[key]
        cons = ctx.knowledge("gene_constraint")
        val = np.nan
        if cons and target_genes:
            genes = cons.get("genes", {})
            cols = cons.get("columns", [])
            try:
                loeuf_idx = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = 0
            for t in target_genes:
                rec = genes.get(t)
                if rec is not None:
                    try:
                        v = rec[loeuf_idx]
                    except (TypeError, IndexError):
                        v = None
                    if v is not None:
                        try:
                            v = float(v)
                        except (TypeError, ValueError):
                            v = None
                        if v is not None and np.isfinite(v):
                            val = v
                            break
        ctx.cache[key] = val
        return val

    def _weight(self, loeuf, transform):
        if loeuf is None or not np.isfinite(loeuf):
            return 1.0
        loeuf = float(loeuf)
        if loeuf < 0:
            loeuf = 0.0
        if transform == "1-loeuf":
            w = 1.0 - loeuf
        elif transform == "inv":
            w = 1.0 / (1.0 + loeuf)
        elif transform == "exp":
            w = float(np.exp(-loeuf))
        else:  # default "1/(1+loeuf)"
            w = 1.0 / (1.0 + loeuf)
        return float(w)

    def compute(self, ctx, perts, params):
        transform = params.get("weight_transform", "1/(1+loeuf)")
        membership = self._build_gene_sets(ctx)
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            loeuf = self._target_loeuf(ctx, tgenes)
            w = self._weight(loeuf, transform)

            if not tgenes:
                continue

            # union of gene sets for the target genes
            tset = set()
            for t in tgenes:
                gi = ctx.gene_index.get(t)
                if gi is not None:
                    tset |= membership[gi]
            if not tset:
                continue

            tsize = len(tset)
            row = out[i, :, 0]
            for g in range(n_genes):
                gset = membership[g]
                if not gset:
                    continue
                inter = len(tset & gset)
                if inter == 0:
                    continue
                union = tsize + len(gset) - inter
                if union > 0:
                    row[g] = w * (inter / union)

        return out
