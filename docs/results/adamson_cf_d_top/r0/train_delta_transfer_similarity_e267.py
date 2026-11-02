import numpy as np
from genemila.features.api import Feature, register

@register
class TrainDeltaTransferSimilarityE267(Feature):
    name = "train_delta_transfer_similarity_e267"
    version = 1
    description = ("Cosine-similarity weighted average of training deltas for gene g, "
                   "where weights are cosine similarities between the target gene of p "
                   "and the target genes of training perturbations in gene-set space.")
    rationale = ("Perturbations with similar target gene functions (gene-set membership) "
                 "produce similar downstream expression changes; transferring deltas from "
                 "functionally similar training perturbations can predict unseen effects.")
    inputs = ["train_delta"]
    params = {"similarity_metric": "cosine"}
    dim = 1

    def _gene_set_vectors(self, ctx):
        cached = ctx.cache.get("_e267_gs_vectors")
        if cached is not None:
            return cached
        gs = ctx.knowledge("gene_sets")
        n_genes = ctx.n_genes
        vecs = {}
        if gs is None:
            ctx.cache["_e267_gs_vectors"] = vecs
            return vecs
        # Build a mapping gene -> list of set ids
        gene_to_sets = {}
        for set_name, members in gs.items():
            for g in members:
                gene_to_sets.setdefault(g, []).append(set_name)
        # Assign an index to each set
        set_index = {}
        for set_name in gs.keys():
            set_index[set_name] = len(set_index)
        n_sets = len(set_index)
        # Build sparse-ish vectors only for genes we care about
        for g in ctx.genes:
            sets = gene_to_sets.get(g)
            if not sets:
                continue
            v = np.zeros(n_sets, dtype=np.float64)
            for s in sets:
                idx = set_index.get(s)
                if idx is not None:
                    v[idx] = 1.0
            vecs[g] = v
        ctx.cache["_e267_gs_vectors"] = vecs
        return vecs

    def _target_gene(self, ctx, p):
        tg = ctx.target_genes(p)
        if tg:
            return tg[0]
        return None

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=np.float64)
        vecs = self._gene_set_vectors(ctx)

        for i, p in enumerate(perts):
            try:
                train_ids, deltas = ctx.train_delta(exclude=p)
            except Exception:
                continue
            n_train = deltas.shape[0]
            if n_train == 0:
                continue

            p_gene = self._target_gene(ctx, p)
            p_vec = vecs.get(p_gene) if p_gene is not None else None

            if p_vec is None:
                # fall back to unweighted mean
                out[i, :, 0] = deltas.mean(axis=0)
                continue

            p_norm = np.linalg.norm(p_vec)
            if p_norm == 0.0:
                out[i, :, 0] = deltas.mean(axis=0)
                continue

            weights = np.zeros(n_train, dtype=np.float64)
            for j, tp in enumerate(train_ids):
                t_gene = self._target_gene(ctx, tp)
                t_vec = vecs.get(t_gene) if t_gene is not None else None
                if t_vec is None:
                    continue
                tn = np.linalg.norm(t_vec)
                if tn == 0.0:
                    continue
                weights[j] = float(np.dot(p_vec, t_vec) / (p_norm * tn))

            wsum = weights.sum()
            if wsum <= 0.0 or not np.isfinite(wsum):
                out[i, :, 0] = deltas.mean(axis=0)
            else:
                out[i, :, 0] = (weights[:, None] * deltas).sum(axis=0) / wsum

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
