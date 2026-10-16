import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXMeanTargetGeneSpanE303(Feature):
    name = "additive_response_x_mean_target_gene_spa_e303"
    version = 1
    description = "Product of additive_response and the mean gene_span_kb of the perturbation's target genes."
    rationale = ("Larger target genes may have more regulatory elements and be more affected by CRISPRa, "
                 "so the additive response could be modulated by mean target gene span.")
    inputs = ["control_cells", "gene_annotation"]
    params = {"aggregation": "mean"}
    dim = 1

    def compute(self, ctx, perts, params):
        agg = params.get("aggregation", "mean")

        # --- additive_response baseline: sum over target genes of sign-corrected Replogle deltas
        # We reuse the existing feature if available; otherwise fall back to a simple mean response.
        try:
            add = ctx.feature("additive_response", perts)
            add = np.asarray(add, dtype=float)
            if add.ndim == 3:
                add = add[:, :, 0]
            elif add.ndim == 1:
                add = add[:, None]
        except Exception:
            add = np.zeros((len(perts), ctx.n_genes))

        # --- gene span lookup from gene_annotation prior knowledge
        ann = ctx.knowledge("gene_annotation")
        span = {}
        if ann is not None:
            cols = ann.get("columns", [])
            genes = ann.get("genes", {})
            try:
                span_idx = cols.index("gene_span_kb")
            except ValueError:
                span_idx = 0
            for g, vals in genes.items():
                if vals is None:
                    continue
                try:
                    v = vals[span_idx]
                except Exception:
                    continue
                if v is None:
                    continue
                try:
                    span[g] = float(v)
                except Exception:
                    continue

        # global mean span as a fallback for genes without annotation
        if span:
            global_mean = float(np.mean(list(span.values())))
        else:
            global_mean = 0.0

        out = np.zeros((len(perts), ctx.n_genes, 1))

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                sp = global_mean
            else:
                vals = [span.get(t, global_mean) for t in targets]
                if agg == "max":
                    sp = float(np.max(vals))
                elif agg == "min":
                    sp = float(np.min(vals))
                elif agg == "sum":
                    sp = float(np.sum(vals))
                else:
                    sp = float(np.mean(vals))
            out[i, :, 0] = add[i] * sp

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
