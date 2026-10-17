import numpy as np
from genemila.features.api import Feature, register


@register
class TargetUtr5LengthTimesAdditiveE429(Feature):
    name = "target_utr5_length_times_additive_e429"
    version = 1
    description = ("Mean 5' UTR length of p's target genes multiplied by the "
                   "additive_response prediction.")
    rationale = ("UTR length influences mRNA stability and translation efficiency, "
                 "which may modulate CRISPRa effects; multiplying by the additive "
                 "baseline captures gene-specific amplification.")
    inputs = ["gene_annotation", "additive_response"]
    params = {}
    dim = 1

    def _utr5_for_gene(self, ann, gene):
        genes = ann.get("genes") or {}
        vals = genes.get(gene)
        if vals is None:
            return None
        cols = ann.get("columns") or []
        try:
            idx = cols.index("utr5_length")
        except ValueError:
            return None
        try:
            v = vals[idx]
        except (IndexError, TypeError):
            return None
        if v is None:
            return None
        try:
            v = float(v)
        except (TypeError, ValueError):
            return None
        if not np.isfinite(v):
            return None
        return v

    def compute(self, ctx, perts, params):
        ann = ctx.knowledge("gene_annotation")
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # additive_response feature: (len(perts), n_genes, dim)
        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add_2d = add[:, :, 0]
        elif add.ndim == 2:
            add_2d = add
        else:
            add_2d = np.zeros((len(perts), n_genes), dtype=float)

        if ann is None:
            return out

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            vals = []
            for g in targets:
                v = self._utr5_for_gene(ann, g)
                if v is not None:
                    vals.append(v)
            if not vals:
                continue
            mean_utr5 = float(np.mean(vals))
            out[i, :, 0] = mean_utr5 * add_2d[i, :]

        out[~np.isfinite(out)] = 0.0
        return out
