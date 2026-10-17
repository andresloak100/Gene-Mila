import numpy as np
from genemila.features.api import Feature, register


@register
class TargetProteinLengthXGeneMembraneE2E300(Feature):
    name = "target_protein_length_x_gene_membrane_e2_e300"
    version = 1
    description = ("Product of target protein length and an indicator that gene g is "
                   "membrane-associated (has transmembrane segments or a membrane flag).")
    rationale = ("Long proteins may be more sensitive to perturbation; the effect may be "
                 "stronger for genes whose products share the same compartment.")
    inputs = ["protein_annotation", "target_indices"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        prior = ctx.knowledge("protein_annotation")
        if prior is None:
            return out

        cols = prior.get("columns", [])
        genes = prior.get("genes", {})
        try:
            i_len = cols.index("protein_length")
        except ValueError:
            i_len = 0
        try:
            i_tm = cols.index("n_transmembrane")
        except ValueError:
            i_tm = None
        try:
            i_mem = cols.index("membrane")
        except ValueError:
            i_mem = None

        # Gene-level membrane indicator and protein length arrays
        prot_len = np.zeros(ctx.n_genes, dtype=float)
        is_mem = np.zeros(ctx.n_genes, dtype=float)
        for j, g in enumerate(ctx.genes):
            vals = genes.get(g)
            if vals is None:
                continue
            try:
                L = vals[i_len]
                if L is not None:
                    prot_len[j] = float(L)
            except (IndexError, TypeError, ValueError):
                pass
            mem = 0.0
            if i_tm is not None:
                try:
                    tm = vals[i_tm]
                    if tm is not None and float(tm) > 0:
                        mem = 1.0
                except (IndexError, TypeError, ValueError):
                    pass
            if i_mem is not None and mem == 0.0:
                try:
                    m = vals[i_mem]
                    if m is not None and float(m) > 0:
                        mem = 1.0
                except (IndexError, TypeError, ValueError):
                    pass
            is_mem[j] = mem

        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if not tidx:
                continue
            tlen = 0.0
            for t in tidx:
                tlen += prot_len[t]
            if tlen == 0.0:
                continue
            out[i, :, 0] = tlen * is_mem

        return out
