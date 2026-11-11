import numpy as np
from genemila.features.api import Feature, register


@register
class GlobinCorrTargetArsInteraction(Feature):
    name = "globin_corr_target_ars_interaction_e165"
    version = 1
    description = (
        "Mean absolute Pearson correlation of gene g's control expression with residual "
        "component genes, multiplied by whether perturbation p targets an aminoacyl-tRNA "
        "synthetase."
    )
    rationale = (
        "Genes co-expressed with globin/residual genes in control may be co-regulated and "
        "respond to perturbations affecting translation or stress pathways; synthetase "
        "targets may amplify this coordinated response."
    )
    inputs = ["control_cells"]
    params = {
        "residual_genes": ["HBZ", "HBG2", "HIST1H1C", "HBA1", "HBG1", "MS4A4A", "HIST1H2BK", "GAL"],
        "ars_targets": ["CARS", "HARS", "IARS2", "AARS"],
    }
    dim = 1

    def compute(self, ctx, perts, params):
        residual_genes = params.get("residual_genes", self.params["residual_genes"])
        ars_targets = params.get("ars_targets", self.params["ars_targets"])
        ars_set = set(ars_targets)

        # Compute mean absolute correlation of every gene with the residual genes.
        key = ("globin_corr_e165", tuple(residual_genes))
        if key in ctx.cache:
            mean_abs_corr = ctx.cache[key]
        else:
            X = np.asarray(ctx.control_cells, dtype=float)
            # Center columns
            Xc = X - X.mean(axis=0, keepdims=True)
            std = Xc.std(axis=0)
            std_safe = np.where(std > 0, std, 1.0)
            Xn = Xc / std_safe
            n_cells = X.shape[0]

            resid_idx = [ctx.gene_index[g] for g in residual_genes if g in ctx.gene_index]
            if len(resid_idx) == 0:
                mean_abs_corr = np.zeros(ctx.n_genes, dtype=float)
            else:
                R = Xn[:, resid_idx]  # (n_cells, n_resid)
                # correlation matrix between all genes and residual genes
                corr = (Xn.T @ R) / max(n_cells, 1)  # (n_genes, n_resid)
                # zero-out residual genes with zero std
                valid = std[resid_idx] > 0
                if not np.all(valid):
                    corr[:, ~valid] = 0.0
                mean_abs_corr = np.abs(corr).mean(axis=1)
            mean_abs_corr = np.nan_to_num(mean_abs_corr, nan=0.0, posinf=0.0, neginf=0.0)
            ctx.cache[key] = mean_abs_corr

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            is_ars = 1.0 if (len(tg) > 0 and any(t in ars_set for t in tg)) else 0.0
            if is_ars == 0.0 and p in ars_set:
                is_ars = 1.0
            out[i, :, 0] = mean_abs_corr * is_ars

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
