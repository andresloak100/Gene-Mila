import numpy as np
from genemila.features.api import Feature, register


@register
class TargetHasSignalPeptideXIsTarget(Feature):
    name = "target_has_signal_peptide_x_is_target_e247"
    version = 1
    description = "Product of target gene's has_signal_peptide (0/1) and is_target indicator."
    rationale = ("Secreted or membrane proteins (signal peptide present) may have different "
                 "downstream effects; interacting target signal-peptide status with the "
                 "is_target indicator isolates the perturbation's direct effect.")
    inputs = ["control_cells"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if ann is None:
            return out

        columns = ann.get("columns", [])
        genes_ann = ann.get("genes", {})
        try:
            sp_idx = columns.index("has_signal_peptide")
        except ValueError:
            return out

        # Build per-gene signal peptide lookup by gene symbol.
        sp_map = {}
        for sym, vals in genes_ann.items():
            if vals is None:
                continue
            try:
                v = vals[sp_idx]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                sp_map[sym] = float(v)
            except (TypeError, ValueError):
                continue

        gene_index = ctx.gene_index
        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if not tgenes:
                continue
            # Determine signal peptide status of target(s).
            sp_val = 0.0
            for tg in tgenes:
                if tg in sp_map:
                    sp_val = max(sp_val, sp_map[tg])
            if sp_val == 0.0:
                continue
            for tg in tgenes:
                gi = gene_index.get(tg)
                if gi is not None:
                    out[i, gi, 0] = sp_val
        return out
