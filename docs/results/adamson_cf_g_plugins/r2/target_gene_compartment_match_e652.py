import numpy as np
from genemila.features.api import Feature, register

@register
class TargetGeneCompartmentMatch(Feature):
    name = "target_gene_compartment_match_e652"
    version = 1
    description = "Indicator that target and gene share at least one UniProt compartment annotation."
    rationale = "Proteins in the same compartment are functionally linked; perturbation of one may affect others."
    inputs = ["protein_annotation", "targets"]
    params = {}
    dim = 1

    COMPARTMENTS = [
        "secreted", "membrane", "endoplasmic_reticulum", "golgi",
        "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
    ]

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        pa = ctx.knowledge("protein_annotation")
        if pa is None:
            return out
        genes_tbl = pa.get("genes", {})
        cols = pa.get("columns", [])

        # locate compartment flag columns
        comp_idx = []
        for c in self.COMPARTMENTS:
            if c in cols:
                comp_idx.append(cols.index(c))
        if not comp_idx:
            return out

        n_genes = ctx.n_genes
        # Build gene compartment flag matrix (n_genes x n_comp)
        gene_flags = np.zeros((n_genes, len(comp_idx)), dtype=np.float32)
        for g_i, g_name in enumerate(ctx.genes):
            vals = genes_tbl.get(g_name)
            if vals is None:
                continue
            for k, ci in enumerate(comp_idx):
                v = vals[ci] if ci < len(vals) else None
                if v is not None:
                    try:
                        gene_flags[g_i, k] = 1.0 if float(v) > 0 else 0.0
                    except (TypeError, ValueError):
                        pass

        # cache target compartment vectors
        cache = ctx.cache
        key = "comp_match_target_comp"
        if key not in cache:
            cache[key] = {}
        tcache = cache[key]

        for i, p in enumerate(perts):
            if p not in tcache:
                tvec = np.zeros(len(comp_idx), dtype=np.float32)
                for tg in ctx.target_genes(p):
                    vals = genes_tbl.get(tg)
                    if vals is None:
                        continue
                    for k, ci in enumerate(comp_idx):
                        v = vals[ci] if ci < len(vals) else None
                        if v is not None:
                            try:
                                if float(v) > 0:
                                    tvec[k] = 1.0
                            except (TypeError, ValueError):
                                pass
                tcache[p] = tvec
            tvec = tcache[p]
            if tvec.sum() == 0:
                continue
            # shared: gene has any compartment that target has
            shared = (gene_flags * tvec[None, :]).sum(axis=1) > 0
            out[i, :, 0] = shared.astype(np.float32)

        return out
