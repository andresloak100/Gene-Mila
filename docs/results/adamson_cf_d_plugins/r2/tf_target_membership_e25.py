import numpy as np
from genemila.features.api import Feature, register

@register
class TFTargetMembershipE25(Feature):
    name = "tf_target_membership_e25"
    version = 1
    description = "Count of transcription factors (from the transcription_factors list) targeting each gene, via gene_sets and prior_network."
    rationale = "Genes regulated by transcription factors may share response patterns due to common upstream regulators."
    inputs = ["transcription_factors", "gene_sets", "prior_network"]
    params = {"include_tf_list": True}
    dim = 1

    def _build_tf_set(self, ctx, params):
        tfs = ctx.knowledge("transcription_factors")
        tf_set = set()
        if params.get("include_tf_list", True) and isinstance(tfs, (list, tuple)):
            for t in tfs:
                if isinstance(t, str):
                    tf_set.add(t)
        return tf_set

    def _counts(self, ctx, params):
        key = ("tf_target_membership_e25_counts", bool(params.get("include_tf_list", True)))
        if key in ctx.cache:
            return ctx.cache[key]

        tf_set = self._build_tf_set(ctx, params)
        counts = np.zeros(ctx.n_genes, dtype=float)

        if tf_set:
            # From gene_sets: each set name maps to member genes; if any TF is in the set,
            # attribute the set to its member genes.
            gene_sets = ctx.knowledge("gene_sets")
            if isinstance(gene_sets, dict):
                for set_name, members in gene_sets.items():
                    if not isinstance(members, (list, tuple)):
                        continue
                    # Does this set contain at least one TF?
                    has_tf = False
                    for m in members:
                        if isinstance(m, str) and m in tf_set:
                            has_tf = True
                            break
                    if not has_tf:
                        continue
                    # Attribute to all member genes present in ctx.gene_index
                    for m in members:
                        if isinstance(m, str):
                            gi = ctx.gene_index.get(m)
                            if gi is not None:
                                counts[gi] += 1.0

            # From prior_network: edges [source, target, weight]; if source is a TF,
            # count toward target.
            pn = ctx.knowledge("prior_network")
            if isinstance(pn, (list, tuple)):
                for edge in pn:
                    if not isinstance(edge, (list, tuple)) or len(edge) < 2:
                        continue
                    src, tgt = edge[0], edge[1]
                    if not isinstance(src, str) or not isinstance(tgt, str):
                        continue
                    if src in tf_set:
                        gi = ctx.gene_index.get(tgt)
                        if gi is not None:
                            counts[gi] += 1.0

        # Binary presence indicator: 1 if any TF targets gene, else 0.
        out = (counts > 0).astype(float)
        ctx.cache[key] = out
        return out

    def compute(self, ctx, perts, params):
        vec = self._counts(ctx, params)  # (n_genes,)
        out = np.empty((len(perts), ctx.n_genes, 1), dtype=float)
        out[:, :, 0] = vec[np.newaxis, :]
        # Ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
