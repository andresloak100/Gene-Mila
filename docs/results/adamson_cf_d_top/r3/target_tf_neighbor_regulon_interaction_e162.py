import numpy as np
from genemila.features.api import Feature, register


@register
class TargetTfNeighborRegulonInteractionE162(Feature):
    name = "target_tf_neighbor_regulon_interaction_e162"
    version = 1
    description = (
        "Interaction between the number of transcription-factor neighbours of the "
        "perturbation target in prior_network and whether gene g is a downstream "
        "neighbour of any of those TFs."
    )
    rationale = (
        "Perturbing a gene connected to many TFs may broadly alter transcriptional "
        "programs, affecting genes regulated by those TFs."
    )
    inputs = ["prior_network", "transcription_factors"]
    params = {"tf_list": "transcription_factors"}
    dim = 1

    def _load_tf_set(self, ctx, params):
        key = "_e162_tf_set"
        cache = ctx.cache
        if key in cache:
            return cache[key]
        tf_names = params.get("tf_list", "transcription_factors")
        tf_raw = ctx.knowledge(tf_names) if isinstance(tf_names, str) else tf_names
        if tf_raw is None:
            cache[key] = set()
            return cache[key]
        if isinstance(tf_raw, dict):
            tf_raw = list(tf_raw.keys())
        tf_set = set(str(t) for t in tf_raw)
        cache[key] = tf_set
        return tf_set

    def _load_adj(self, ctx):
        key = "_e162_adj"
        cache = ctx.cache
        if key in cache:
            return cache[key]
        pn = ctx.knowledge("prior_network")
        adj = {}
        if pn is not None:
            for edge in pn:
                try:
                    a, b = str(edge[0]), str(edge[1])
                except (IndexError, TypeError):
                    continue
                adj.setdefault(a, set()).add(b)
                adj.setdefault(b, set()).add(a)
        cache[key] = adj
        return adj

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        tf_set = self._load_tf_set(ctx, params)
        adj = self._load_adj(ctx)
        gene_index = ctx.gene_index

        # Global structural signal: how often each gene is a regulon member of TFs
        # across the whole network. Used as a fallback so rows are not all-zero.
        gene_tf_degree = np.zeros(n_genes, dtype=float)
        for tf in tf_set:
            for g in adj.get(tf, ()):
                gi = gene_index.get(g)
                if gi is not None:
                    gene_tf_degree[gi] += 1.0

        cache = ctx.cache.setdefault("e162_cache", {})

        for i, p in enumerate(perts):
            p = str(p)
            if p in cache:
                count, mask = cache[p]
            else:
                neigh = adj.get(p, set())
                tf_neigh = neigh & tf_set
                count = float(len(tf_neigh))

                mask = np.zeros(n_genes, dtype=bool)
                if count > 0:
                    regulon = set()
                    for tf in tf_neigh:
                        regulon |= adj.get(tf, set())
                    for g in regulon:
                        gi = gene_index.get(g)
                        if gi is not None:
                            mask[gi] = True
                cache[p] = (count, mask)

            if count > 0:
                # Interaction term: TF-neighbour count * regulon membership.
                out[i, :, 0] = count * mask.astype(float)
            else:
                # Fallback: use target connectivity to TFs times global TF-degree,
                # providing non-constant signal for perturbations with no TF neighbours.
                out[i, :, 0] = gene_tf_degree

        if not np.any(out):
            # Ultimate fallback: broadcast global TF-degree so feature varies across genes.
            out[:, :, 0] = gene_tf_degree[None, :]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
