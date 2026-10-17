import numpy as np
from genemila.features.api import Feature, FeatureContext, register


@register
class TargetProteinLengthXGeneBindingFunE527(Feature):
    name = "target_protein_length_x_gene_binding_fun_e527"
    version = 1
    description = ("Product of target protein length and an indicator that gene g is annotated "
                   "with a binding-related function (gene set name contains 'binding').")
    rationale = ("Longer target proteins have more interaction interfaces; perturbing them may "
                 "affect genes involved in protein binding or complex formation more.")
    inputs = ["protein_annotation", "gene_sets"]
    params = {}
    dim = 1

    def compute(self, ctx: FeatureContext, perts: list[str], params: dict) -> np.ndarray:
        n_genes = ctx.n_genes

        # --- binding-related gene indicator (shared across perturbations) ---
        cache_key = "_e527_binding_indicator"
        if cache_key in ctx.cache:
            binding_ind = ctx.cache[cache_key]
        else:
            binding_ind = np.zeros(n_genes, dtype=float)
            gene_sets = ctx.knowledge("gene_sets")
            if gene_sets:
                # gene_sets is a dict: set_name -> list of genes
                for set_name, members in gene_sets.items():
                    if "binding" not in set_name.lower():
                        continue
                    for g in members:
                        idx = ctx.gene_index.get(g)
                        if idx is not None:
                            binding_ind[idx] = 1.0
            ctx.cache[cache_key] = binding_ind

        # --- target protein length lookup ---
        protein_ann = ctx.knowledge("protein_annotation")
        prot_len_map = {}
        if protein_ann:
            genes_tbl = protein_ann.get("genes", {})
            cols = protein_ann.get("columns", [])
            try:
                len_col = cols.index("protein_length")
            except ValueError:
                len_col = 0
            for sym, vals in genes_tbl.items():
                if vals is None:
                    continue
                v = vals[len_col]
                if v is not None:
                    try:
                        prot_len_map[sym] = float(v)
                    except (TypeError, ValueError):
                        pass

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tlen = 0.0
            for tg in ctx.target_genes(p):
                if tg in prot_len_map:
                    tlen = prot_len_map[tg]
                    break
            out[i, :, 0] = tlen * binding_ind

        return out
