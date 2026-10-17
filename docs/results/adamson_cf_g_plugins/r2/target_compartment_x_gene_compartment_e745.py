import numpy as np
from genemila.features.api import Feature, register

@register
class TargetCompartmentXGeneCompartmentE745(Feature):
    name = "target_compartment_x_gene_compartment_e745"
    version = 1
    description = "Indicator that target and gene share the same protein localization compartment."
    rationale = ("Perturbing a target localized to a specific compartment has a stronger effect on "
                 "genes whose products function in that same compartment, reflecting functional "
                 "interaction within shared cellular machinery.")
    inputs = ["knowledge", "target_genes"]
    params = {}
    dim = 1

    COMPARTMENTS = ["secreted", "membrane", "endoplasmic_reticulum", "golgi",
                    "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome"]

    def _build_gene_flags(self, ctx):
        cache_key = "_e745_gene_flags"
        if cache_key in ctx.cache:
            return ctx.cache[cache_key]

        pa = ctx.knowledge("protein_annotation")
        n = ctx.n_genes
        ncomp = len(self.COMPARTMENTS)
        flags = np.zeros((n, ncomp), dtype=np.float32)

        if pa is not None:
            genes = pa.get("genes", {})
            cols = pa.get("columns", [])
            col_idx = {c: i for i, c in enumerate(cols)}
            comp_cols = []
            for c in self.COMPARTMENTS:
                comp_cols.append(col_idx.get(c, None))
            for gi, g in enumerate(ctx.genes):
                vals = genes.get(g)
                if vals is None:
                    continue
                for ci, cc in enumerate(comp_cols):
                    if cc is None:
                        continue
                    v = vals[cc]
                    if v is not None and v == 1:
                        flags[gi, ci] = 1.0

        ctx.cache[cache_key] = flags
        return flags

    def compute(self, ctx, perts, params):
        gene_flags = self._build_gene_flags(ctx)  # (n_genes, ncomp)
        n = ctx.n_genes
        ncomp = len(self.COMPARTMENTS)
        out = np.zeros((len(perts), n, 1), dtype=np.float32)

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                continue
            tflags = np.zeros(ncomp, dtype=np.float32)
            found = False
            for t in tg:
                gi = ctx.gene_index.get(t)
                if gi is not None:
                    tflags = np.maximum(tflags, gene_flags[gi])
                    found = True
            if not found:
                continue
            # shared compartment indicator: any overlap
            shared = (gene_flags * tflags[None, :]).sum(axis=1)
            out[i, :, 0] = (shared > 0).astype(np.float32)

        return out
