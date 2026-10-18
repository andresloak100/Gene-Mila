import numpy as np
from genemila.features.api import Feature, register


@register
class ObsLofGeneE130E142(Feature):
    name = "obs_lof_gene_e130_e142"
    version = 1
    description = "log10(1 + observed LoF variant count) per gene from gnomAD constraint."
    rationale = "Genes tolerant to loss-of-function (high obs_lof) may be less essential and more buffered, leading to smaller expression changes."
    inputs = ["knowledge:gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        kc = ctx.knowledge("gene_constraint")
        if not kc:
            return out

        genes_tbl = kc.get("genes", {}) or {}
        columns = kc.get("columns", []) or []
        try:
            col_idx = list(columns).index("obs_lof")
        except ValueError:
            col_idx = None

        vals = np.zeros(ctx.n_genes, dtype=float)
        if col_idx is not None:
            for g, gidx in ctx.gene_index.items():
                entry = genes_tbl.get(g)
                if entry is None:
                    continue
                try:
                    v = entry[col_idx]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    continue
                if not np.isfinite(v) or v < 0:
                    continue
                vals[gidx] = np.log10(1.0 + v)

        out[:, :, 0] = vals[None, :]
        return out
