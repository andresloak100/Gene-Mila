import numpy as np
from genemila.features.api import Feature, register


@register
class SynZScore(Feature):
    name = "syn_z_e115"
    version = 1
    description = "Synonymous Z-score (syn_z) for gene g from gene_constraint."
    rationale = (
        "Synonymous constraint may reflect translational efficiency or mRNA stability, "
        "influencing expression response; high syn_z may attenuate expression changes."
    )
    inputs = ["gene_constraint"]
    params = {"missing_value": 0.0}
    dim = 1

    def compute(self, ctx, perts, params):
        missing = float(params.get("missing_value", 0.0))
        n_genes = ctx.n_genes
        vals = np.full(n_genes, missing, dtype=float)

        table = ctx.knowledge("gene_constraint")
        if table is not None:
            columns = table.get("columns", [])
            col = None
            for c in ("syn_z", "syn_z_score", "synonymous_z", "syn_zscore"):
                if c in columns:
                    col = columns.index(c)
                    break
            if col is not None:
                genes = table.get("genes", {})
                for g, idx in ctx.gene_index.items():
                    row = genes.get(g)
                    if row is None:
                        continue
                    try:
                        v = row[col]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vals[idx] = fv

        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = vals[None, :]
        return out
