import numpy as np
from genemila.features.api import Feature, register

@register
class TargetCompartmentXGeneCompartmentSpE566(Feature):
    name = "target_compartment_x_gene_compartment_sp_e566"
    version = 1
    description = ("Product of indicator that the perturbation target's protein localizes to "
                   "compartment C and indicator that gene g's protein localizes to the same "
                   "compartment C, for each of 9 compartments (one-hot expansion).")
    rationale = ("Perturbing a target localized to a compartment may specifically affect genes "
                 "whose products localize to the same compartment, reflecting organelle-specific "
                 "stress responses. A per-compartment product is more specific than a coarse "
                 "compartment indicator.")
    inputs = ["protein_annotation", "targets"]
    params = {"expand_compartments": True}
    dim = 9

    COMPARTMENTS = [
        "secreted",
        "membrane",
        "endoplasmic_reticulum",
        "golgi",
        "mitochondrion",
        "nucleus",
        "cytoplasm",
        "lysosome",
        "peroxisome",
    ]

    def _build_gene_flags(self, ctx):
        cached = ctx.cache.get("_e566_gene_flags")
        if cached is not None:
            return cached

        n_genes = ctx.n_genes
        n_comp = len(self.COMPARTMENTS)
        gene_flags = np.zeros((n_genes, n_comp), dtype=np.float64)

        ann = ctx.knowledge("protein_annotation")
        if ann is not None:
            genes_dict = ann.get("genes", {}) or {}
            columns = ann.get("columns", []) or []
            col_index = {c: i for i, c in enumerate(columns)}
            comp_cols = []
            for c in self.COMPARTMENTS:
                comp_cols.append(col_index.get(c, None))

            for g_idx, g in enumerate(ctx.genes):
                vals = genes_dict.get(g)
                if vals is None:
                    continue
                for j, ci in enumerate(comp_cols):
                    if ci is None:
                        continue
                    try:
                        v = vals[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        gene_flags[g_idx, j] = 1.0 if float(v) != 0.0 else 0.0
                    except (TypeError, ValueError):
                        continue

        ctx.cache["_e566_gene_flags"] = gene_flags
        return gene_flags

    def _target_flags(self, ctx, p, ann):
        """Return (n_comp,) indicator of target protein compartments."""
        n_comp = len(self.COMPARTMENTS)
        flags = np.zeros(n_comp, dtype=np.float64)

        tgenes = ctx.target_genes(p)
        if not tgenes:
            return flags

        ann_genes = (ann or {}).get("genes", {}) or {}
        columns = (ann or {}).get("columns", []) or []
        col_index = {c: i for i, c in enumerate(columns)}
        comp_cols = [col_index.get(c, None) for c in self.COMPARTMENTS]

        for tg in tgenes:
            vals = ann_genes.get(tg)
            if vals is None:
                continue
            for j, ci in enumerate(comp_cols):
                if ci is None:
                    continue
                try:
                    v = vals[ci]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                try:
                    if float(v) != 0.0:
                        flags[j] = 1.0
                except (TypeError, ValueError):
                    continue
        return flags

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_comp = len(self.COMPARTMENTS)
        out = np.zeros((len(perts), n_genes, n_comp), dtype=np.float64)

        gene_flags = self._build_gene_flags(ctx)
        ann = ctx.knowledge("protein_annotation")

        for i, p in enumerate(perts):
            tflag = self._target_flags(ctx, p, ann)
            if not tflag.any():
                continue
            # product: target_flag[c] * gene_flag[g, c]
            out[i, :, :] = gene_flags * tflag[np.newaxis, :]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
