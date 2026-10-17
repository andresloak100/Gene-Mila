import numpy as np
from genemila.features.api import Feature, register


@register
class TargetEssentialityPpiNeighborDeltaInteraction(Feature):
    name = "target_essentiality_ppi_neighbor_delta_i_e515"
    version = 1
    description = (
        "For each (p,g), multiply (1 - LOEUF_target) by ppi_neighbor_mean_delta_e286."
    )
    rationale = (
        "Perturbing essential targets may propagate effects more strongly through "
        "PPI neighbors, so combining target essentiality (1 - LOEUF) with the "
        "neighbor mean delta captures a synergistic interaction."
    )
    inputs = ["gene_constraint", "control_cells", "train_delta"]
    params = {}
    dim = 1

    def _loeuf_table(self, ctx):
        cache = ctx.cache
        key = "_e515_loeuf"
        if key in cache:
            return cache[key]
        loeuf = {}
        data = ctx.knowledge("gene_constraint")
        if data is not None:
            genes = data.get("genes", {}) or {}
            cols = data.get("columns", []) or []
            try:
                idx = list(cols).index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                for g, vals in genes.items():
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
                        loeuf[g] = fv
        cache[key] = loeuf
        return loeuf

    def _ppi_neighbor_index(self, ctx):
        cache = ctx.cache
        key = "_e515_ppi_index"
        if key in cache:
            return cache[key]
        # Build symmetric PPI neighbor sets restricted to measured genes.
        gene_index = ctx.gene_index
        neigh = {gi: set() for gi in range(ctx.n_genes)}
        data = ctx.knowledge("ppi_network")
        if data is not None:
            for entry in data:
                try:
                    a, b = entry[0], entry[1]
                except (IndexError, TypeError):
                    continue
                ia = gene_index.get(a)
                ib = gene_index.get(b)
                if ia is None or ib is None:
                    continue
                if ia == ib:
                    continue
                neigh[ia].add(ib)
                neigh[ib].add(ia)
        # Convert to arrays for fast mean computation.
        idx_list = []
        for gi in range(ctx.n_genes):
            s = neigh[gi]
            if s:
                idx_list.append(np.fromiter(s, dtype=np.int64, count=len(s)))
            else:
                idx_list.append(np.empty(0, dtype=np.int64))
        cache[key] = idx_list
        return idx_list

    def _neighbor_mean_delta(self, ctx, delta):
        # delta: (n_train, n_genes) -> (n_genes,) mean over PPI neighbors
        idx_list = self._ppi_neighbor_index(ctx)
        n_genes = ctx.n_genes
        out = np.zeros(n_genes, dtype=np.float64)
        # Vectorize where possible: group by neighbor count.
        counts = np.array([len(ix) for ix in idx_list], dtype=np.int64)
        has = counts > 0
        if not np.any(has):
            return out
        # Compute column means of delta once.
        col_mean = delta.mean(axis=0) if delta.shape[0] > 0 else np.zeros(n_genes)
        # For each gene with neighbors, average col_mean over its neighbors.
        for gi in np.nonzero(has)[0]:
            ix = idx_list[gi]
            out[gi] = col_mean[ix].mean()
        return out

    def compute(self, ctx, perts, params):
        loeuf_table = self._loeuf_table(ctx)
        n_genes = ctx.n_genes
        n_perts = len(perts)
        out = np.zeros((n_perts, n_genes, 1), dtype=np.float64)

        # Cache neighbor mean per training-delta set; but exclude=p means each
        # perturbation has its own delta set, so compute per perturbation.
        for i, p in enumerate(perts):
            # Target essentiality scalar.
            ess = 0.0
            tgenes = ctx.target_genes(p)
            if tgenes:
                # Use first mapped target with LOEUF available.
                found = False
                for tg in tgenes:
                    if tg in loeuf_table:
                        ess = 1.0 - loeuf_table[tg]
                        found = True
                        break
                if not found:
                    ess = 0.0
            else:
                ess = 0.0
            if not np.isfinite(ess):
                ess = 0.0

            _, delta = ctx.train_delta(exclude=p)
            delta = np.asarray(delta, dtype=np.float64)
            if delta.ndim != 2:
                delta = delta.reshape(-1, n_genes)
            if delta.shape[0] == 0:
                nb_mean = np.zeros(n_genes, dtype=np.float64)
            else:
                nb_mean = self._neighbor_mean_delta(ctx, delta)

            vals = ess * nb_mean
            vals = np.where(np.isfinite(vals), vals, 0.0)
            out[i, :, 0] = vals

        out = np.where(np.isfinite(out), out, 0.0)
        return out
