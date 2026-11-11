import numpy as np
from genemila.features.api import Feature, FeatureContext, register


@register
class TargetGlobinCorrGeneCorrE273(Feature):
    name = "target_globin_corr_gene_corr_e273"
    version = 1
    description = (
        "For each (p,g): average control-cell correlation between the target gene "
        "and globin genes (HBZ, HBG1, HBG2, HBA1), applied only if g is a globin gene."
    )
    rationale = (
        "Targets co-expressed with globin genes may regulate or share regulatory "
        "programs with globin expression, leading to coordinated responses."
    )
    inputs = ["gene_corr", "control_cells", "targets"]
    params = {"globin_genes": ["HBZ", "HBG1", "HBG2", "HBA1"]}
    dim = 1

    def compute(self, ctx: FeatureContext, perts: list[str], params: dict) -> np.ndarray:
        globin_genes = params.get("globin_genes", ["HBZ", "HBG1", "HBG2", "HBA1"])
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)

        corr = ctx.gene_corr
        if corr is None:
            return out

        # Indices of globin genes present in the measured gene set.
        globin_idx = [ctx.gene_index[g] for g in globin_genes if g in ctx.gene_index]
        if not globin_idx:
            return out
        globin_idx = np.asarray(globin_idx, dtype=int)

        # Boolean mask of columns that are globin genes (for the g indicator).
        is_globin = np.zeros(ctx.n_genes, dtype=bool)
        is_globin[globin_idx] = True

        for i, p in enumerate(perts):
            # Target gene columns for this perturbation.
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue

            # Correlation of target gene(s) with each globin gene, averaged.
            sub = corr[np.ix_(np.asarray(t_idx, dtype=int), globin_idx)]
            avg_corr = float(np.mean(sub))

            # Only nonzero for globin response genes.
            out[i, is_globin, 0] = avg_corr

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
