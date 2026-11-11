import numpy as np
from genemila.features.api import Feature, register


@register
class SignalPeptideLengthE193E194(Feature):
    name = "signal_peptide_length_e193_e194"
    version = 1
    description = "Length of the signal peptide for gene g from protein_annotation (0 if missing)."
    rationale = (
        "Longer signal peptides indicate stronger co-translational ER targeting, "
        "reducing mRNA-level regulation and response magnitude."
    )
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vals = np.zeros(n_genes, dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if ann is not None:
            genes = ann.get("genes", {})
            cols = ann.get("columns", [])
            try:
                idx = list(cols).index("signal_peptide_length")
            except ValueError:
                idx = None
            if idx is not None:
                for gi, g in enumerate(ctx.genes):
                    row = genes.get(g)
                    if row is None:
                        continue
                    try:
                        v = row[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vals[gi] = fv

        out = np.broadcast_to(vals[None, :, None], (len(perts), n_genes, 1)).copy()
        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
