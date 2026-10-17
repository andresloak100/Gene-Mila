import numpy as np
from genemila.features.api import Feature, register


@register
class NuclearGeneXTargetNuclear(Feature):
    name = "nuclear_gene_x_target_nuclear_e506"
    version = 1
    description = (
        "Product of a binary indicator that gene g encodes a nuclear protein "
        "and a binary indicator that the perturbation target encodes a nuclear protein."
    )
    rationale = (
        "Nuclear proteins often interact in transcriptional regulation or chromatin "
        "modification; perturbing a nuclear target may more strongly affect other "
        "nuclear genes due to shared localization and functional coupling."
    )
    inputs = ["protein_annotation", "targets"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if not ann:
            return out
        columns = ann.get("columns", [])
        genes_map = ann.get("genes", {})
        if "nucleus" not in columns:
            return out
        nuc_idx = columns.index("nucleus")

        # Binary nuclear flag per gene column.
        gene_nuclear = np.zeros(n_genes, dtype=float)
        for g in ctx.genes:
            vals = genes_map.get(g)
            if vals is None:
                continue
            try:
                v = vals[nuc_idx]
            except (IndexError, TypeError):
                continue
            if v is not None:
                try:
                    gene_nuclear[ctx.gene_index[g]] = 1.0 if float(v) > 0 else 0.0
                except (TypeError, ValueError):
                    pass

        # Cache target nuclear flags.
        cache = ctx.cache
        key = "_nuc_target_flags_e506"
        target_flags = cache.get(key)
        if target_flags is None:
            target_flags = {}
            cache[key] = target_flags

        for i, p in enumerate(perts):
            flag = target_flags.get(p)
            if flag is None:
                flag = 0.0
                for tg in ctx.target_genes(p):
                    vals = genes_map.get(tg)
                    if vals is None:
                        continue
                    try:
                        v = vals[nuc_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is not None:
                        try:
                            if float(v) > 0:
                                flag = 1.0
                                break
                        except (TypeError, ValueError):
                            continue
                target_flags[p] = flag
            if flag != 0.0:
                out[i, :, 0] = gene_nuclear

        return out
