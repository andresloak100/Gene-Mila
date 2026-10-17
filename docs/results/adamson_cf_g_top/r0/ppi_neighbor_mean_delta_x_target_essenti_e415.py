import numpy as np
from genemila.features.api import Feature, register


@register
class PpiNeighborMeanDeltaXTargetEssenti(Feature):
    name = "ppi_neighbor_mean_delta_x_target_essenti_e415"
    version = 1
    description = (
        "For each (p,g), multiply the PPI-neighbour mean delta (mean delta of gene g's "
        "direct PPI neighbours across training perturbations) by (1 - LOEUF_target), "
        "where LOEUF_target is the gnomAD LoF-constraint LOEUF of the perturbation target."
    )
    rationale = (
        "Essential genes (low LOEUF) tend to have stronger downstream propagation; scaling "
        "the PPI-neighbour response by target essentiality sharpens predictions for "
        "perturbations of LoF-intolerant genes."
    )
    inputs = ["train_delta", "knowledge"]
    params = {}
    dim = 1

    def _load_loeuf(self, ctx):
        cache = ctx.cache
        key = "_e415_loeuf"
        if key in cache:
            return cache[key]
        loeuf = {}
        med = None
        k = ctx.knowledge("gene_constraint")
        if k is not None:
            genes = k.get("genes", {})
            cols = k.get("columns", [])
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            vals = []
            if idx is not None:
                for g, row in genes.items():
                    if row is None:
                        continue
                    try:
                        v = row[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        loeuf[g] = fv
                        vals.append(fv)
            if vals:
                med = float(np.median(vals))
        if med is None:
            med = 1.0
        cache[key] = (loeuf, med)
        return cache[key]

    def _load_ppi(self, ctx):
        cache = ctx.cache
        key = "_e415_ppi"
        if key in cache:
            return cache[key]
        adj = {}
        k = ctx.knowledge("ppi_network")
        if k is not None:
            for entry in k:
                try:
                    a, b, w = entry[0], entry[1], entry[2]
                except (IndexError, TypeError):
                    continue
                try:
                    w = float(w)
                except (TypeError, ValueError):
                    continue
                if not np.isfinite(w):
                    continue
                adj.setdefault(a, []).append((b, w))
                adj.setdefault(b, []).append((a, w))
        cache[key] = adj
        return adj

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        gene_index = ctx.gene_index
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        loeuf_map, med_loeuf = self._load_loeuf(ctx)
        adj = self._load_ppi(ctx)

        # Precompute weighted neighbour index lists per gene (in gene-column space).
        nbr_cache = ctx.cache.setdefault("_e415_nbrs", {})
        for g in ctx.genes:
            if g in nbr_cache:
                continue
            entries = adj.get(g, [])
            idxs = []
            ws = []
            for (nb, w) in entries:
                j = gene_index.get(nb)
                if j is not None:
                    idxs.append(j)
                    ws.append(w)
            if idxs:
                nbr_cache[g] = (np.asarray(idxs, dtype=np.int64),
                                np.asarray(ws, dtype=float))
            else:
                nbr_cache[g] = None

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            if d.shape[0] == 0:
                continue
            mean_delta = d.mean(axis=0)  # (n_genes,)

            # Target LOEUF
            t_loeuf = med_loeuf
            for tg in ctx.target_genes(p):
                if tg in loeuf_map:
                    t_loeuf = loeuf_map[tg]
                    break
            scale = 1.0 - t_loeuf
            if not np.isfinite(scale):
                scale = 1.0 - med_loeuf

            col = out[i, :, 0]
            for g in ctx.genes:
                ent = nbr_cache.get(g)
                if ent is None:
                    continue
                idxs, ws = ent
                wsum = ws.sum()
                if wsum <= 0:
                    continue
                col[gene_index[g]] = float(np.dot(ws, mean_delta[idxs]) / wsum) * scale

        out[~np.isfinite(out)] = 0.0
        return out
