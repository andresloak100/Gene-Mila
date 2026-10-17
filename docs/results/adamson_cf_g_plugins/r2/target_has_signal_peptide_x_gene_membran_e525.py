import numpy as np
from genemila.features.api import Feature, register


@register
class TargetHasSignalPeptideXGeneMembrane(Feature):
    name = "target_has_signal_peptide_x_gene_membran_e525"
    version = 1
    description = ("Product of target gene's has_signal_peptide (0/1) and an indicator "
                   "that gene g is a membrane protein (n_transmembrane > 0).")
    rationale = ("Signal-peptide targets are routed to the secretory pathway; perturbing them "
                 "may disproportionately affect membrane-protein-encoding genes.")
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if not ann or "genes" not in ann or "columns" not in ann:
            return out

        cols = ann["columns"]
        try:
            i_sp = cols.index("has_signal_peptide")
            i_tm = cols.index("n_transmembrane")
        except ValueError:
            return out

        genes_tbl = ann["genes"]

        # Per-gene membrane indicator: n_transmembrane > 0
        gene_membrane = np.zeros(n_genes, dtype=float)
        for g, col in ctx.gene_index.items():
            vals = genes_tbl.get(g)
            if vals is None:
                continue
            v = vals[i_tm]
            if v is not None:
                try:
                    if float(v) > 0:
                        gene_membrane[col] = 1.0
                except (TypeError, ValueError):
                    pass

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            has_sp = 0.0
            for t in targets:
                vals = genes_tbl.get(t)
                if vals is None:
                    continue
                v = vals[i_sp]
                if v is not None:
                    try:
                        if float(v) > 0:
                            has_sp = 1.0
                            break
                    except (TypeError, ValueError):
                        pass
            if has_sp != 0.0:
                out[i, :, 0] = gene_membrane

        return out
