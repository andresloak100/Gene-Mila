import numpy as np
from genemila.features.api import Feature, register


@register
class ReplogleAdditiveXMeanTargetPromoterE301(Feature):
    name = "replogle_additive_x_mean_target_promoter_e301"
    version = 1
    description = ("Product of the sign-corrected Replogle additive response and the mean "
                   "promoter GC content of the perturbation's target genes.")
    rationale = ("Promoter GC content influences transcriptional activity and CRISPRa efficiency; "
                 "aggregating target promoter GC captures target-specific regulatory strength, "
                 "modulating the Replogle-based additive prediction.")
    inputs = ["train_delta", "knowledge"]
    params = {"aggregation": "mean"}
    dim = 1

    def compute(self, ctx, perts, params):
        agg = params.get("aggregation", "mean")

        # --- Replogle additive response (signed) ---
        base = ctx.feature("replogle_additive_response_signed_e104", perts)
        base = np.asarray(base, dtype=float)
        if base.ndim == 3:
            base = base[:, :, 0]
        elif base.ndim == 1:
            base = base[:, None]

        # --- gene_annotation promoter GC ---
        ann = ctx.knowledge("gene_annotation")
        gc_map = {}
        col_idx = None
        if ann is not None and isinstance(ann, dict):
            genes_ann = ann.get("genes")
            columns = ann.get("columns", [])
            if isinstance(genes_ann, dict):
                # locate gc_promoter column
                for j, c in enumerate(columns):
                    if str(c).strip().lower() == "gc_promoter":
                        col_idx = j
                        break
                if col_idx is None:
                    # fallback: assume order given in description
                    # gene_span_kb, n_transcripts, n_exons, transcript_length, cds_length,
                    # utr5_length, utr3_length, intron_length_kb, gc_cds, gc_utr3, gc_promoter
                    col_idx = 10
                for g, vals in genes_ann.items():
                    try:
                        v = vals[col_idx]
                    except Exception:
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except Exception:
                        continue
                    if np.isfinite(fv):
                        gc_map[g] = fv

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p) or []
            vals = [gc_map[g] for g in targets if g in gc_map]
            if len(vals) == 0:
                agg_gc = 0.0
            else:
                arr = np.asarray(vals, dtype=float)
                if agg == "mean":
                    agg_gc = float(arr.mean())
                elif agg == "sum":
                    agg_gc = float(arr.sum())
                elif agg == "max":
                    agg_gc = float(arr.max())
                elif agg == "min":
                    agg_gc = float(arr.min())
                else:
                    agg_gc = float(arr.mean())

            out[i, :, 0] = base[i] * agg_gc

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
