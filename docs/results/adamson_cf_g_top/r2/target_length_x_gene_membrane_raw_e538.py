import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLengthXGeneMembraneRaw(Feature):
    name = "target_length_x_gene_membrane_raw_e538"
    version = 1
    description = "Product of target protein length (optionally log) and gene membrane indicator (0/1)."
    rationale = (
        "Longer target proteins have more interaction interfaces, so their perturbation may "
        "affect membrane-associated genes more strongly."
    )
    inputs = ["control_cells"]
    params = {"log_target_length": True}
    dim = 1

    def compute(self, ctx, perts, params):
        log_tl = bool(params.get("log_target_length", True))
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # memoise per-gene membrane indicator and protein lengths
        cache = ctx.cache
        if "e538_membrane" not in cache:
            prot = ctx.knowledge("protein_annotation")
            membrane = np.zeros(n_genes, dtype=float)
            plen = np.full(n_genes, np.nan, dtype=float)
            if prot is not None:
                genes = prot.get("genes", {})
                cols = prot.get("columns", [])
                try:
                    mi = cols.index("membrane")
                except ValueError:
                    mi = None
                try:
                    li = cols.index("protein_length")
                except ValueError:
                    li = None
                for j, g in enumerate(ctx.genes):
                    vals = genes.get(g)
                    if vals is None:
                        continue
                    if mi is not None and mi < len(vals) and vals[mi] is not None:
                        try:
                            membrane[j] = 1.0 if float(vals[mi]) > 0 else 0.0
                        except (TypeError, ValueError):
                            pass
                    if li is not None and li < len(vals) and vals[li] is not None:
                        try:
                            plen[j] = float(vals[li])
                        except (TypeError, ValueError):
                            pass
            cache["e538_membrane"] = membrane
            cache["e538_plen"] = plen
        membrane = cache["e538_membrane"]
        plen = cache["e538_plen"]

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            lengths = plen[tgt_idx]
            valid = lengths[np.isfinite(lengths)]
            if valid.size == 0:
                continue
            tl = float(np.mean(valid))
            if tl <= 0:
                continue
            if log_tl:
                tl = float(np.log1p(tl))
            out[i, :, 0] = tl * membrane

        out[~np.isfinite(out)] = 0.0
        return out
