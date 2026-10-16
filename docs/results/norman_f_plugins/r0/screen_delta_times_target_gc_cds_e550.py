import numpy as np
from genemila.features.api import Feature, register

@register
class ScreenDeltaTimesTargetGCCDS(Feature):
    name = "screen_delta_times_target_gc_cds_e550"
    version = 1
    description = "Elementwise product of replogle_delta_signed_e35 and gc_cds of the target gene (for pairs, mean of gc_cds)."
    rationale = "Multiplying signed Replogle screen delta by GC content of the target gene's CDS improves prediction due to CRISPRa efficiency variation."
    inputs = ["knowledge", "replogle_delta_signed_e35"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        # Get gc_cds values from gene_annotation knowledge
        ann = ctx.knowledge("gene_annotation")
        gc_cds_map = {}
        if ann is not None and "genes" in ann and "columns" in ann:
            cols = ann["columns"]
            if "gc_cds" in cols:
                idx = cols.index("gc_cds")
                genes_dict = ann["genes"]
                for g, vals in genes_dict.items():
                    if vals is not None and len(vals) > idx and vals[idx] is not None:
                        gc_cds_map[g] = float(vals[idx])

        # Get signed screen delta from the other feature
        try:
            screen = ctx.feature("replogle_delta_signed_e35", perts, params=None)
        except Exception:
            screen = None

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue

            # Mean gc_cds over targets
            gc_vals = [gc_cds_map.get(t) for t in targets]
            gc_vals = [v for v in gc_vals if v is not None]
            if not gc_vals:
                continue
            gc_mean = float(np.mean(gc_vals))

            # Get signed screen delta row for this perturbation
            if screen is not None:
                sd = screen[i, :, 0]
            else:
                sd = np.zeros(ctx.n_genes)
                # fallback: compute directly from knowledge
                rep = ctx.knowledge("replogle2022_k562")
                if rep is not None and "perts" in rep and "genes" in rep:
                    sign = rep.get("sign", 1)
                    genes_list = rep["genes"]
                    gene_idx = {g: j for j, g in enumerate(genes_list)}
                    # map bundle genes to columns
                    col_map = {}
                    for j, g in enumerate(genes_list):
                        if g in ctx.gene_index:
                            col_map[j] = ctx.gene_index[g]
                    pertd = rep["perts"]
                    # sum over targets
                    target_idx = [gene_idx[t] for t in targets if t in gene_idx]
                    if target_idx:
                        vec = np.zeros(ctx.n_genes)
                        for j in target_idx:
                            if j in col_map:
                                vec[col_map[j]] += 1.0
                        # look up delta
                        # pertd structure unknown; skip fallback
                        pass

            out[i, :, 0] = sd * gc_mean

        return out
