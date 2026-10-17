import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPpiNeighborEssentialityWeighted(Feature):
    name = "target_ppi_neighbor_essentiality_weighte_e764"
    version = 2
    description = ("For each (p,g), mean of mean_response over direct PPI neighbors of the "
                   "perturbation target, weighted by (1 - LOEUF) of each neighbor.")
    rationale = ("Essential genes are more likely to have strong downstream effects when "
                 "perturbed; weighting neighbor responses by their essentiality may highlight "
                 "critical interactions.")
    inputs = ["control_cells", "train_delta", "knowledge"]
    params = {}
    dim = 1

    def _build_adj(self, ctx):
        if "ppi_adj" in ctx.cache:
            return ctx.cache["ppi_adj"]
        ppi = ctx.knowledge("ppi_network")
        adj = {}
        if ppi is not None:
            # ppi may be a list of [a,b] pairs or a dict with 'edges'
            edges = ppi
            if isinstance(ppi, dict):
                edges = ppi.get("edges", ppi.get("interactions", []))
            for entry in edges:
                try:
                    a, b = entry[0], entry[1]
                except (TypeError, IndexError, KeyError):
                    continue
                if a == b:
                    continue
                adj.setdefault(a, set()).add(b)
                adj.setdefault(b, set()).add(a)
        ctx.cache["ppi_adj"] = adj
        return adj

    def _build_weight(self, ctx):
        if "ess_weight" in ctx.cache:
            return ctx.cache["ess_weight"]
        n_genes = ctx.n_genes
        loeuf = np.ones(n_genes, dtype=float)
        constraint = ctx.knowledge("gene_constraint")
        if constraint is not None:
            cols = []
            genes_map = None
            if isinstance(constraint, dict):
                cols = constraint.get("columns", []) or []
                genes_map = constraint.get("genes", {})
            loeuf_idx = None
            for cand in ("oe_lof_upper", "loeuf", "LOEUF"):
                if cand in cols:
                    loeuf_idx = cols.index(cand)
                    break
            if loeuf_idx is not None and isinstance(genes_map, dict):
                for g, vals in genes_map.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    try:
                        v = vals[loeuf_idx]
                    except (TypeError, IndexError, KeyError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        loeuf[gi] = fv
        weight = 1.0 - loeuf
        # ensure non-negative and finite
        weight = np.where(np.isfinite(weight), weight, 0.0)
        weight = np.clip(weight, 0.0, None)
        ctx.cache["ess_weight"] = weight
        return weight

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        adj = self._build_adj(ctx)
        weight = self._build_weight(ctx)

        # Fallback weight if all essentiality weights are zero
        if not np.any(weight > 0):
            weight = np.ones(n_genes, dtype=float)

        # Global fallback mean response (over training perts) for perturbations with no neighbors
        try:
            _, d_all = ctx.train_delta(exclude=None)
        except TypeError:
            _, d_all = ctx.train_delta()
        global_mean = d_all.mean(axis=0) if d_all.shape[0] > 0 else np.zeros(n_genes)

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            mean_resp = d.mean(axis=0) if d.shape[0] > 0 else global_mean

            targets = ctx.target_genes(p)
            neighbor_idx = set()
            for t in targets:
                for nb in adj.get(t, ()):
                    gi = ctx.gene_index.get(nb)
                    if gi is not None:
                        neighbor_idx.add(gi)

            if not neighbor_idx:
                # fallback: use target genes themselves if measured, else global mean
                tgt_idx = [gi for gi in ctx.target_indices(p) if 0 <= gi < n_genes]
                if tgt_idx:
                    out[i, :, 0] = mean_resp[np.array(tgt_idx, dtype=int)].mean()
                else:
                    out[i, :, 0] = global_mean.mean()
                continue

            idx = np.fromiter(neighbor_idx, dtype=int, count=len(neighbor_idx))
            w = weight[idx]
            r = mean_resp[idx]
            wsum = w.sum()
            if wsum > 0:
                out[i, :, 0] = (w * r).sum() / wsum
            else:
                out[i, :, 0] = r.mean()

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
