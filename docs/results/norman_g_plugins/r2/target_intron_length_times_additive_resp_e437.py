import numpy as np
from genemila.features.api import Feature, register


@register
class TargetIntronLengthTimesAdditiveResp(Feature):
    name = "target_intron_length_times_additive_resp_e437"
    version = 1
    description = "Product of the mean intron length of p's target genes and additive_response."
    rationale = ("Intron length correlates with gene expression regulation and may affect "
                 "CRISPRa response magnitude, scaling the additive baseline.")
    inputs = ["control_cells", "gene_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # additive_response feature (leakage-safe, handled by that feature)
        try:
            add = ctx.feature("additive_response", perts)
        except Exception:
            add = None
        if add is not None:
            add = np.asarray(add, dtype=float).reshape(len(perts), n_genes, -1)
            add = add[:, :, 0]
        else:
            add = np.zeros((len(perts), n_genes))

        ann = ctx.knowledge("gene_annotation")
        intron_idx = None
        intron_vals = None
        if isinstance(ann, dict):
            cols = ann.get("columns") or []
            if "intron_length_kb" in cols:
                intron_idx = cols.index("intron_length_kb")
            genes_ann = ann.get("genes") or {}
        else:
            genes_ann = {}

        def mean_intron(target_genes):
            if not target_genes:
                return 0.0
            vals = []
            for g in target_genes:
                row = genes_ann.get(g)
                if row is None or intron_idx is None:
                    continue
                try:
                    v = row[intron_idx]
                except Exception:
                    continue
                if v is None:
                    continue
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(v):
                    vals.append(v)
            if not vals:
                return 0.0
            return float(np.mean(vals))

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            mi = mean_intron(tg)
            out[i, :, 0] = mi * add[i]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
