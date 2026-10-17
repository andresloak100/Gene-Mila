import numpy as np
from genemila.features.api import Feature, register


@register
class GeneLoeufXPathwayResponseE712(Feature):
    name = "gene_loeuf_x_pathway_response_e712"
    version = 1
    description = (
        "For each (p,g), multiply (1 - LOEUF of gene g) by the pathway-weighted "
        "mean response of genes sharing pathways with g."
    )
    rationale = (
        "Essential genes may be more sensitive to perturbations, and this "
        "sensitivity may be modulated by pathway context. The product of "
        "gene essentiality and pathway-weighted neighbour response captures "
        "condition-dependent essentiality effects."
    )
    inputs = ["control_cells", "train_delta", "knowledge"]
    params = {}
    dim = 1

    def _loeuf(self, ctx, params):
        key = "loeuf"
        if key in ctx.cache:
            return ctx.cache[key]
        vec = np.full(ctx.n_genes, np.nan, dtype=np.float64)
        cons = ctx.knowledge("gene_constraint")
        if cons is not None:
            cols = cons.get("columns", [])
            genes = cons.get("genes", {})
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                for sym, vals in genes.items():
                    gi = ctx.gene_index.get(sym)
                    if gi is None:
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
                        vec[gi] = fv
        ctx.cache[key] = vec
        return vec

    def _pathway_membership(self, ctx, params):
        key = "pathway_membership"
        if key in ctx.cache:
            return ctx.cache[key]
        gsets = ctx.knowledge("gene_sets")
        n = ctx.n_genes
        pathways = []
        if gsets:
            for pname in sorted(gsets.keys()):
                members = gsets[pname]
                if not isinstance(members, (list, tuple)):
                    continue
                idxs = []
                for sym in members:
                    gi = ctx.gene_index.get(sym)
                    if gi is not None:
                        idxs.append(gi)
                if len(idxs) >= 2:
                    pathways.append(np.array(sorted(set(idxs)), dtype=np.int64))
        gene_to_paths = [[] for _ in range(n)]
        for pi, arr in enumerate(pathways):
            for gi in arr:
                gene_to_paths[gi].append(pi)
        ctx.cache[key] = (pathways, gene_to_paths)
        return pathways, gene_to_paths

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        loeuf = self._loeuf(ctx, params)
        ess = np.where(np.isfinite(loeuf), 1.0 - loeuf, 0.0)
        ess = np.clip(ess, 0.0, 1.0)

        pathways, gene_to_paths = self._pathway_membership(ctx, params)

        # Precompute for each pathway a boolean membership mask for fast means.
        pathway_masks = []
        for arr in pathways:
            mask = np.zeros(n_genes, dtype=bool)
            mask[arr] = True
            pathway_masks.append(mask)

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            if d.shape[0] == 0:
                continue
            mean_delta = d.mean(axis=0)  # (n_genes,)

            # Pathway mean response per pathway
            pathway_means = np.zeros(len(pathways), dtype=np.float64)
            for pi, mask in enumerate(pathway_masks):
                pathway_means[pi] = mean_delta[mask].mean()

            # Pathway-weighted mean response per gene
            pathway_resp = np.zeros(n_genes, dtype=np.float64)
            for gi in range(n_genes):
                plist = gene_to_paths[gi]
                if not plist:
                    continue
                pathway_resp[gi] = float(np.mean(pathway_means[plist]))

            out[i, :, 0] = ess * pathway_resp

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
