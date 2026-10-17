import numpy as np
from genemila.features.api import Feature, register


@register
class TargetStabilityXGeneProteasomeSensiE725(Feature):
    name = "target_stability_x_gene_proteasome_sensi_e725"
    version = 1
    description = ("Product of the target's protein-stability proxy and a per-gene "
                   "proteasome sensitivity score (correlation of gene expression with "
                   "mean proteasome subunit expression across control cells).")
    rationale = ("Perturbing a short-lived (unstable) target may stress proteostasis; "
                 "genes whose expression co-varies with proteasome subunits are more "
                 "sensitive to proteasome-related perturbations, so the effect scales "
                 "with target instability.")
    inputs = ["control_cells", "control_mean", "control_std", "protein_annotation"]
    params = {"proteasome_genes": "PSMA1,PSMA2,PSMA3,PSMA4,PSMA5,PSMA6,PSMA7,"
                                  "PSMB1,PSMB2,PSMB3,PSMB4,PSMB5,PSMB6,PSMB7,"
                                  "PSMB8,PSMB9,PSMB10"}
    dim = 1

    def _stability_proxy(self, ctx):
        """Per-gene protein stability proxy from protein_annotation (length, signal peptide)."""
        cache = ctx.cache
        key = "_e725_stability_proxy"
        if key in cache:
            return cache[key]
        n = ctx.n_genes
        proxy = np.zeros(n, dtype=float)
        pa = ctx.knowledge("protein_annotation")
        if pa is not None:
            cols = list(pa.get("columns", []))
            genes_tbl = pa.get("genes", {}) or {}
            try:
                i_len = cols.index("protein_length")
            except ValueError:
                i_len = 0
            try:
                i_sp = cols.index("has_signal_peptide")
            except ValueError:
                i_sp = 1
            for g, col in ctx.gene_index.items():
                vals = genes_tbl.get(g)
                if not vals:
                    continue
                length = vals[i_len] if i_len < len(vals) else None
                sp = vals[i_sp] if i_sp < len(vals) else None
                if length is None or length == "":
                    length = 0.0
                if sp is None or sp == "":
                    sp = 0.0
                try:
                    length = float(length)
                    sp = float(sp)
                except (TypeError, ValueError):
                    continue
                # Longer proteins with signal peptides are considered less stable.
                proxy[col] = length * (1.0 + sp)
        # Standardise for numerical stability.
        std = proxy.std()
        if std > 0:
            proxy = (proxy - proxy.mean()) / std
        else:
            proxy = np.zeros(n, dtype=float)
        cache[key] = proxy
        return proxy

    def _proteasome_sensitivity(self, ctx, params):
        cache = ctx.cache
        genes_str = params.get("proteasome_genes", self.params["proteasome_genes"])
        key = "_e725_proteasome_sensi_" + str(genes_str)
        if key in cache:
            return cache[key]

        n = ctx.n_genes
        sens = np.zeros(n, dtype=float)

        plist = [s.strip() for s in str(genes_str).split(",") if s.strip()]
        idxs = [ctx.gene_index[g] for g in plist if g in ctx.gene_index]

        if len(idxs) > 0:
            X = np.asarray(ctx.control_cells, dtype=float)
            # Mean expression of proteasome subunits per cell.
            prot = X[:, idxs].mean(axis=1)
            ps = prot.std()
            if ps > 0:
                pz = (prot - prot.mean()) / ps
            else:
                pz = np.zeros_like(prot)

            mean = np.asarray(ctx.control_mean, dtype=float)
            std = np.asarray(ctx.control_std, dtype=float)
            safe_std = np.where(std > 0, std, 1.0)
            Z = (X - mean[None, :]) / safe_std[None, :]

            # Pearson correlation of each gene with proteasome mean.
            corr = (Z * pz[:, None]).mean(axis=0)
            # Zero out genes with no variance.
            corr = np.where(std > 0, corr, 0.0)
            sens = corr

        cache[key] = sens
        return sens

    def compute(self, ctx, perts, params):
        stability = self._stability_proxy(ctx)
        sens = self._proteasome_sensitivity(ctx, params)
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)

        for i, p in enumerate(perts):
            tids = ctx.target_indices(p)
            if not tids:
                continue
            # Average stability proxy over targeted genes (usually one).
            s = float(np.mean(stability[tids]))
            out[i, :, 0] = s * sens

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
