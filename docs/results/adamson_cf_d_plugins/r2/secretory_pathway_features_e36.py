import numpy as np
from genemila.features.api import Feature, register

@register
class SecretoryPathwayFeaturesE36(Feature):
    name = "secretory_pathway_features_e36"
    version = 1
    description = "Per-gene protein annotation features: has_signal_peptide, signal_peptide_length, n_transmembrane."
    rationale = ("Secretory and membrane proteins are subject to ER quality control and trafficking; "
                 "their abundance of signal peptide and transmembrane segments may modulate how "
                 "perturbations affecting the secretory pathway propagate to gene expression.")
    inputs = ["protein_annotation"]
    params = {}
    dim = 3

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)
        out = np.zeros((n_perts, n_genes, 3), dtype=np.float64)

        anno = ctx.knowledge("protein_annotation")
        if anno is None:
            return out

        genes_tbl = anno.get("genes", {}) or {}
        cols = anno.get("columns", []) or []

        # Locate column indices by name (robust to ordering).
        def _col_idx(name):
            try:
                return cols.index(name)
            except ValueError:
                return None

        i_sp = _col_idx("has_signal_peptide")
        i_spl = _col_idx("signal_peptide_length")
        i_tm = _col_idx("n_transmembrane")

        raw = np.zeros((n_genes, 3), dtype=np.float64)
        present = np.zeros(n_genes, dtype=bool)

        for gi, g in enumerate(ctx.genes):
            vals = genes_tbl.get(g)
            if vals is None:
                continue
            present[gi] = True
            row = np.zeros(3, dtype=np.float64)
            for k, ci in enumerate((i_sp, i_spl, i_tm)):
                if ci is None or ci >= len(vals):
                    continue
                v = vals[ci]
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    row[k] = fv
            raw[gi] = row

        # Standardize each column across genes (mean/std over present genes).
        if present.any():
            sub = raw[present]
            mu = sub.mean(axis=0)
            sd = sub.std(axis=0)
            sd = np.where(sd > 1e-12, sd, 1.0)
            std = (raw - mu) / sd
        else:
            std = raw

        # Missing genes -> 0 (mean after standardization).
        std[~present] = 0.0
        std = np.where(np.isfinite(std), std, 0.0)

        # Same per-gene vector for every perturbation row.
        out[:, :, :] = std[np.newaxis, :, :]
        return out
