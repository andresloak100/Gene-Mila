import numpy as np
from genemila.features.api import Feature, register

@register
class AdditiveResponseXMeanTargetSpanE296(Feature):
    name = "additive_response_x_mean_target_span_e296"
    version = 1
    description = "Product of additive_response and the mean gene_span_kb of the perturbation's target genes."
    rationale = ("Larger genes may have more regulatory elements or be more easily activated by CRISPRa, "
                 "influencing the magnitude of downstream changes. Multiplying the additive baseline "
                 "prediction by mean target gene span captures genomic context effects on perturbation efficiency.")
    inputs = ["train_delta", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)

        # Cache additive response (leave-one-out mean delta) per perturbation
        cache = ctx.cache
        if "ar_e296" not in cache:
            cache["ar_e296"] = {}
        ar_cache = cache["ar_e296"]

        # Load gene_span_kb from gene_annotation knowledge
        span = None
        if "span_e296" not in cache:
            try:
                ka = ctx.knowledge("gene_annotation")
            except Exception:
                ka = None
            span_arr = np.full(n_genes, np.nan, dtype=np.float64)
            if ka is not None:
                genes_dict = ka.get("genes") if isinstance(ka, dict) else None
                columns = ka.get("columns") if isinstance(ka, dict) else None
                if isinstance(genes_dict, dict) and isinstance(columns, list):
                    try:
                        span_idx = columns.index("gene_span_kb")
                    except ValueError:
                        span_idx = None
                    if span_idx is not None:
                        for g, vals in genes_dict.items():
                            gi = ctx.gene_index.get(g)
                            if gi is None:
                                continue
                            try:
                                v = vals[span_idx]
                            except Exception:
                                continue
                            if v is None:
                                continue
                            try:
                                fv = float(v)
                            except Exception:
                                continue
                            if np.isfinite(fv):
                                span_arr[gi] = fv
            cache["span_e296"] = span_arr
        span = cache["span_e296"]

        out = np.zeros((n_perts, n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            # Additive response = mean delta over training perturbations (leave p out)
            if p in ar_cache:
                ar = ar_cache[p]
            else:
                _, d = ctx.train_delta(exclude=p)
                ar = d.mean(axis=0)
                ar_cache[p] = ar

            # Mean gene_span_kb over p's targets
            t_idx = ctx.target_indices(p)
            if t_idx is None or len(t_idx) == 0:
                mean_span = 0.0
            else:
                vals = span[np.asarray(t_idx, dtype=int)]
                vals = vals[np.isfinite(vals)]
                if vals.size == 0:
                    mean_span = 0.0
                else:
                    mean_span = float(vals.mean())

            out[i, :, 0] = ar * mean_span

        # Ensure finite values
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
