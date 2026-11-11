import numpy as np
from genemila.features.api import Feature, register


@register
class TfTargetMembershipE34(Feature):
    name = "tf_target_membership_e34"
    version = 1
    description = "Binary TF-target membership indicators per gene for selected TFs."
    rationale = ("Genes regulated by erythroid/myeloid TFs share response patterns; "
                 "membership encodes this regulatory program.")
    inputs = ["transcription_factors", "gene_sets", "prior_network"]
    params = {"tf_list": ["GATA1", "NFE2", "ATF4"]}
    dim = 3

    def compute(self, ctx, perts, params):
        tf_list = list(params.get("tf_list", ["GATA1", "NFE2", "ATF4"]))
        n_genes = ctx.n_genes
        gene_index = ctx.gene_index

        # Build per-TF target sets from gene_sets and prior_network (cached).
        cache = ctx.cache
        key = ("tf_target_membership_e34", tuple(tf_list))
        if key not in cache:
            gene_sets = ctx.knowledge("gene_sets") or {}
            prior_network = ctx.knowledge("prior_network") or []

            # Collect edges: TF -> gene.
            edges = {tf: set() for tf in tf_list}
            tf_set = set(tf_list)

            # From gene_sets: entries whose name references a TF.
            for set_name, members in gene_sets.items():
                if not isinstance(members, (list, tuple)):
                    continue
                name_upper = str(set_name).upper()
                for tf in tf_list:
                    if tf.upper() in name_upper:
                        edges[tf].update(members)

            # From prior_network: [source, target, weight] edges.
            for edge in prior_network:
                if not isinstance(edge, (list, tuple)) or len(edge) < 2:
                    continue
                src, dst = str(edge[0]), str(edge[1])
                if src in tf_set:
                    edges[src].add(dst)
                if dst in tf_set:
                    edges[dst].add(src)

            # Map to gene columns.
            mat = np.zeros((n_genes, len(tf_list)), dtype=np.float64)
            for j, tf in enumerate(tf_list):
                for g in edges.get(tf, ()):
                    idx = gene_index.get(g)
                    if idx is not None:
                        mat[idx, j] = 1.0
            cache[key] = mat

        mat = cache[key]
        n_perts = len(perts)
        out = np.empty((n_perts, n_genes, self.dim), dtype=np.float64)
        out[:] = mat[np.newaxis, :, :]
        return out
