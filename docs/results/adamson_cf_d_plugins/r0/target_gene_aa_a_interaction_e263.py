import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneAaAInteraction(Feature):
    name = "target_gene_aa_a_interaction_e263"
    version = 1
    description = ("Product of the target gene's alanine fraction (aa_A) and "
                   "gene g's alanine fraction from gene_annotation.")
    rationale = ("Alanine-rich proteins may share biophysical properties affecting "
                 "co-regulation or complex formation.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if not ann:
            return out

        genes = ann.get("genes", {})
        columns = ann.get("columns", [])
        if "aa_A" not in columns:
            return out
        aa_idx = columns.index("aa_A")

        # Build per-gene alanine fraction vector aligned to ctx.genes.
        aa_a = np.full(ctx.n_genes, np.nan, dtype=float)
        for i, g in enumerate(ctx.genes):
            vals = genes.get(g)
            if vals is None:
                continue
            v = vals[aa_idx] if aa_idx < len(vals) else None
            if v is None:
                continue
            try:
                aa_a[i] = float(v)
            except (TypeError, ValueError):
                continue

        # Replace NaNs with 0 so products are finite.
        aa_a = np.where(np.isfinite(aa_a), aa_a, 0.0)

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            # Average alanine fraction over target genes.
            t_val = float(np.mean(aa_a[t_idx]))
            out[i, :, 0] = t_val * aa_a

        return out
