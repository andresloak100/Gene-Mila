import numpy as np
from genemila.features.api import Feature, register


@register
class SecretedMembraneXResponseEntropy(Feature):
    name = "secreted_membrane_x_response_entropy_e694"
    version = 1
    description = ("For each (p,g), multiply a binary indicator (1 if gene g has signal_peptide "
                   "or n_transmembrane>0 from protein_annotation) by response_entropy_e89.")
    rationale = ("Secreted/membrane proteins may have distinct response variability due to "
                 "extracellular signaling or membrane dynamics; interacting with response entropy "
                 "captures gene-specific context.")
    inputs = ["knowledge:protein_annotation", "feature:response_entropy_e89"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes

        # Binary indicator from protein_annotation
        indicator = np.zeros(n_genes, dtype=np.float64)
        prot = ctx.knowledge("protein_annotation")
        if prot is not None:
            genes = prot.get("genes", {})
            cols = prot.get("columns", [])
            # locate columns
            try:
                i_sp = cols.index("has_signal_peptide")
            except ValueError:
                i_sp = None
            try:
                i_tm = cols.index("n_transmembrane")
            except ValueError:
                i_tm = None
            for gi, g in enumerate(ctx.genes):
                vals = genes.get(g)
                if vals is None:
                    continue
                flag = False
                if i_sp is not None and vals[i_sp] is not None:
                    try:
                        if float(vals[i_sp]) > 0:
                            flag = True
                    except (TypeError, ValueError):
                        pass
                if not flag and i_tm is not None and vals[i_tm] is not None:
                    try:
                        if float(vals[i_tm]) > 0:
                            flag = True
                    except (TypeError, ValueError):
                        pass
                if flag:
                    indicator[gi] = 1.0

        # response_entropy_e89: shape (len(perts), n_genes, dim)
        ent = ctx.feature("response_entropy_e89", perts)
        ent = np.asarray(ent, dtype=np.float64)
        if ent.ndim == 2:
            ent = ent[:, :, None]
        if ent.shape[0] != len(perts):
            # fall back defensively
            ent = np.zeros((len(perts), n_genes, 1))

        out = ent * indicator[None, :, None]
        out = np.where(np.isfinite(out), out, 0.0)
        return out
