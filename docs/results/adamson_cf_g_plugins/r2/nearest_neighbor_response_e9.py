import numpy as np
from genemila.features.api import Feature, register


@register
class NearestNeighborResponseE9(Feature):
    name = "nearest_neighbor_response_e9"
    version = 1
    description = ("Delta of the training perturbation whose target gene is most similar to the "
                   "target of p (by control-expression correlation or annotation cosine), LOO.")
    rationale = "Perturbations of functionally related genes often yield overlapping expression changes."
    inputs = ["control_cells", "train_delta", "gene_corr", "target_indices"]
    params = {"similarity_metric": "expression_correlation"}
    dim = 1

    def _annotation_vectors(self, ctx, genes):
        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return None
        table = ann.get("genes", {})
        cols = ann.get("columns", [])
        if not cols:
            return None
        vecs = np.zeros((len(genes), len(cols)), dtype=float)
        mask = np.zeros((len(genes), len(cols)), dtype=bool)
        for i, g in enumerate(genes):
            vals = table.get(g)
            if vals is None:
                continue
            for j in range(min(len(cols), len(vals))):
                v = vals[j]
                if v is None:
                    continue
                try:
                    vecs[i, j] = float(v)
                    mask[i, j] = True
                except (TypeError, ValueError):
                    continue
        return vecs, mask

    def _target_gene(self, ctx, p):
        tg = ctx.target_genes(p)
        if not tg:
            return None
        return tg[0]

    def _similarity(self, ctx, genes, metric):
        n = len(genes)
        idx = np.array([ctx.gene_index.get(g, -1) for g in genes])
        valid = idx >= 0

        if metric == "annotation_cosine":
            res = self._annotation_vectors(ctx, genes)
            if res is not None:
                vecs, mask = res
                # standardize per column over valid entries
                means = np.zeros(vecs.shape[1])
                stds = np.ones(vecs.shape[1])
                for j in range(vecs.shape[1]):
                    m = mask[:, j]
                    if m.sum() > 1:
                        v = vecs[m, j]
                        means[j] = v.mean()
                        s = v.std()
                        stds[j] = s if s > 1e-8 else 1.0
                z = (vecs - means) / stds
                z = z * mask
                norms = np.linalg.norm(z, axis=1)
                norms[norms < 1e-8] = 1.0
                zn = z / norms[:, None]
                sim = zn @ zn.T
                return sim

        # default: expression correlation via gene_corr
        sim = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if valid[i] and valid[j]:
                    sim[i, j] = ctx.gene_corr[idx[i], idx[j]]
        return sim

    def compute(self, ctx, perts, params):
        metric = params.get("similarity_metric", "expression_correlation")
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        # cache similarity structure across perturbations
        cache_key = ("nn_e9", metric)
        if cache_key not in ctx.cache:
            train_perts = list(ctx.train_perts)
            train_genes = [self._target_gene(ctx, p) for p in train_perts]
            # only keep those with a resolvable target
            keep = [i for i, g in enumerate(train_genes) if g is not None]
            kept_perts = [train_perts[i] for i in keep]
            kept_genes = [train_genes[i] for i in keep]
            sim = self._similarity(ctx, kept_genes, metric) if kept_genes else np.zeros((0, 0))
            ctx.cache[cache_key] = (kept_perts, kept_genes, sim)

        kept_perts, kept_genes, sim = ctx.cache[cache_key]
        kept_set = set(kept_perts)
        pert_to_kidx = {p: i for i, p in enumerate(kept_perts)}

        for i, p in enumerate(perts):
            tg = self._target_gene(ctx, p)
            _, deltas = ctx.train_delta(exclude=p)
            # map deltas rows to training perts: train_delta returns pert_ids
            ids, _ = ctx.train_delta(exclude=p)
            id_to_row = {pid: r for r, pid in enumerate(ids)}

            best_row = -1
            if tg is not None and kept_genes:
                # similarity of tg to kept genes
                sims = self._similarity(ctx, [tg] + kept_genes, metric)[0, 1:]
                # exclude the perturbation itself (LOO)
                for k, kp in enumerate(kept_perts):
                    if kp == p:
                        sims[k] = -np.inf
                order = np.argsort(-sims)
                for k in order:
                    kp = kept_perts[k]
                    if kp in id_to_row:
                        best_row = id_to_row[kp]
                        break

            if best_row >= 0:
                out[i, :, 0] = deltas[best_row]
            else:
                out[i, :, 0] = deltas.mean(axis=0) if len(deltas) else 0.0

        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
