import numpy as np
from genemila.features.api import Feature, register


@register
class NearestTssDistanceGeneE100(Feature):
    name = "nearest_tss_distance_gene_e100"
    version = 1
    description = (
        "Log-transformed distance (kb) from gene g's TSS to the nearest other TSS, "
        "from gene_annotation.nearest_tss_kb; missing imputed with median."
    )
    rationale = (
        "Genes in dense regulatory neighborhoods may be more sensitive to perturbations "
        "due to shared enhancers or chromatin domains; smaller nearest-TSS distance "
        "marks genes more susceptible to local regulatory interference."
    )
    inputs = ["knowledge:gene_annotation"]
    params = {"log_transform": True}
    dim = 1

    def compute(self, ctx, perts, params):
        log_transform = bool(params.get("log_transform", True))
        n_genes = ctx.n_genes

        ann = ctx.knowledge("gene_annotation")
        values = np.full(n_genes, np.nan, dtype=float)

        if ann is not None:
            genes_tbl = ann.get("genes", {}) or {}
            columns = ann.get("columns", []) or []
            try:
                col_idx = columns.index("nearest_tss_kb")
            except ValueError:
                col_idx = None

            if col_idx is not None:
                for g, row in genes_tbl.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    if row is None or col_idx >= len(row):
                        continue
                    v = row[col_idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        values[gi] = fv

        finite = np.isfinite(values)
        if finite.any():
            median = float(np.median(values[finite]))
        else:
            median = 0.0
        values[~finite] = median

        if log_transform:
            values = np.log1p(np.abs(values)) * np.sign(values)
            # log1p of non-negative distances; negatives unlikely but handled safely
            values = np.log1p(np.clip(values, 0.0, None)) if np.all(values >= 0) else values

        gene_feat = values.reshape(1, n_genes, 1)
        out = np.broadcast_to(gene_feat, (len(perts), n_genes, 1)).copy()
        out[~np.isfinite(out)] = 0.0
        return out
