import numpy as np
from genemila.features.api import Feature, register


@register
class CpGTargetTFInteractionE168(Feature):
    name = "cpg_target_tf_interaction_e168"
    version = 2
    description = ("CpG-island promoter score of each gene, modulated by the perturbation "
                   "target's TF status and its expression/importance, so rows vary across "
                   "perturbations.")
    rationale = ("CpG islands mark active promoters; genes with CpG-island promoters may "
                 "respond more when the target is a TF. Scaling by target expression and "
                 "target correlation gives per-perturbation variation.")
    inputs = ["gene_annotation", "transcription_factors", "target_indices", "control_mean"]
    params = {"tf_list": "transcription_factors", "tf_weight": 1.0, "corr_weight": 0.5}
    dim = 1

    def _cpg_score(self, ctx):
        cache = ctx.cache
        key = "__cpg_promoter_score_e168__"
        if key in cache:
            return cache[key]

        n = ctx.n_genes
        score = np.zeros(n, dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            cols = ann.get("columns", []) or []
            genes_tbl = ann.get("genes", {}) or {}
            cidx = None
            for j, c in enumerate(cols):
                if c == "cpg_oe_promoter":
                    cidx = j
                    break
            if cidx is not None:
                for g, col in ctx.gene_index.items():
                    vals = genes_tbl.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[cidx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        score[col] = fv

        score = np.clip(score, 0.0, None)
        mx = score.max()
        if mx > 0:
            score = score / mx

        cache[key] = score
        return score

    def _tf_set(self, ctx, params):
        cache = ctx.cache
        key = "__tf_set_e168__"
        if key in cache:
            return cache[key]
        name = params.get("tf_list", "transcription_factors")
        tf = ctx.knowledge(name)
        tf_set = set()
        if tf is not None:
            if isinstance(tf, dict):
                for k, v in tf.items():
                    if isinstance(v, (list, tuple)):
                        tf_set.update(str(x) for x in v)
                    else:
                        tf_set.add(str(k))
            else:
                for x in tf:
                    tf_set.add(str(x))
        cache[key] = tf_set
        return tf_set

    def compute(self, ctx, perts, params):
        cpg = self._cpg_score(ctx)  # (n_genes,)
        tf_set = self._tf_set(ctx, params)
        tf_w = float(params.get("tf_weight", 1.0))
        corr_w = float(params.get("corr_weight", 0.5))

        cm = ctx.control_mean
        cm_abs = np.abs(cm)
        cm_max = cm_abs.max()
        if cm_max > 0:
            cm_norm = cm_abs / cm_max
        else:
            cm_norm = np.zeros_like(cm_abs)

        gene_corr = ctx.gene_corr

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            tidx = ctx.target_indices(p)

            is_tf = 0.0
            if tg and tf_set:
                is_tf = 1.0 if any(t in tf_set for t in tg) else 0.0

            # base: CpG score, boosted if target is a TF
            base = cpg * (1.0 + tf_w * is_tf)

            # per-perturbation modulation: how strongly each gene correlates with the
            # target gene(s), weighted by target expression magnitude.
            if tidx:
                corr_vec = np.zeros(ctx.n_genes, dtype=float)
                for ti in tidx:
                    if ti is not None and 0 <= ti < ctx.n_genes:
                        c = gene_corr[ti]
                        c = np.nan_to_num(c, nan=0.0, posinf=0.0, neginf=0.0)
                        corr_vec = np.maximum(corr_vec, np.abs(c))
                tgt_strength = float(np.mean([cm_norm[ti] for ti in tidx
                                              if 0 <= ti < ctx.n_genes]) or 0.0)
                mod = 1.0 + corr_w * tgt_strength * corr_vec
            else:
                mod = np.ones(ctx.n_genes, dtype=float)

            out[i, :, 0] = base * mod

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
