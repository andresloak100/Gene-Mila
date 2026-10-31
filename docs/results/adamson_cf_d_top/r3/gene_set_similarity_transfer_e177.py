import numpy as np
from genemila.features.api import Feature, register


@register
class GeneSetSimilarityTransferE177(Feature):
    name = "gene_set_similarity_transfer_e177"
    version = 1
    description = (
        "Similarity-weighted average of training delta responses, where weights are "
        "Jaccard similarities between gene sets containing the perturbation's target gene."
    )
    rationale = (
        "Perturbations of genes with similar functions (shared gene sets) may produce "
        "similar expression changes; transfer responses from functionally similar targets."
    )
    inputs = ["train_delta", "gene_sets"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # Load gene sets and build gene -> set-id mapping
        gs = ctx.knowledge("gene_sets")
        gene_to_sets = {}
        if isinstance(gs, dict):
            for set_name, members in gs.items():
                if not isinstance(members, (list, tuple)):
                    continue
                for g in members:
                    gene_to_sets.setdefault(g, set()).add(set_name)

        # Cache training deltas per exclusion perturbation
        # We need, for each p: training pert ids + deltas excluding p.
        # Reuse across calls where possible via ctx.cache.
        cache = ctx.cache

        def get_train(exclude):
            key = ("train_delta", exclude)
            if key not in cache:
                ids, d = ctx.train_delta(exclude=exclude)
                cache[key] = (list(ids), np.asarray(d, dtype=float))
            return cache[key]

        # Precompute set-membership frozensets for target genes of training perts
        # For each training pert, its target gene(s). We'll compute similarity per p.

        def target_sets_for_pert(p):
            tgenes = ctx.target_genes(p)
            sets = set()
            for tg in tgenes:
                s = gene_to_sets.get(tg)
                if s:
                    sets |= s
            return sets

        for i, p in enumerate(perts):
            train_ids, deltas = get_train(p)
            if deltas.shape[0] == 0:
                continue

            p_sets = target_sets_for_pert(p)

            if len(p_sets) == 0:
                # Fall back to mean response
                out[i, :, 0] = deltas.mean(axis=0)
                continue

            # Compute similarity to each training perturbation
            sims = np.zeros(len(train_ids), dtype=float)
            for j, q in enumerate(train_ids):
                q_sets = target_sets_for_pert(q)
                if len(q_sets) == 0:
                    sims[j] = 0.0
                    continue
                inter = len(p_sets & q_sets)
                if inter == 0:
                    sims[j] = 0.0
                else:
                    union = len(p_sets | q_sets)
                    sims[j] = inter / union if union > 0 else 0.0

            ssum = sims.sum()
            if ssum <= 0:
                out[i, :, 0] = deltas.mean(axis=0)
            else:
                out[i, :, 0] = (sims[:, None] * deltas).sum(axis=0) / ssum

        return out
