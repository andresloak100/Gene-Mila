import numpy as np
from genemila.features.api import Feature, register

@register
class TargetProteinLengthXGeneFoldingSet(Feature):
    name = "target_protein_length_x_gene_folding_set_e353"
    version = 1
    description = "Product of target protein length and an indicator that gene g belongs to a protein folding or proteasome gene set."
    rationale = "Long proteins are more prone to misfolding; their knockdown may induce proteotoxic stress, altering expression of folding/degradation genes."
    inputs = ["knowledge", "target_indices"]
    params = {"gene_set_names": ["GO:0006457", "REACTOME:Chaperonin-mediated protein folding"]}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        gene_set_names = params.get("gene_set_names", [])

        # Build folding indicator over genes
        indicator = np.zeros(n_genes, dtype=float)
        gs = ctx.knowledge("gene_sets")
        if gs is not None:
            names = list(gs.keys())
            for name in gene_set_names:
                members = None
                if name in gs:
                    members = gs[name]
                else:
                    # prefix / substring match fallback
                    for k in names:
                        if k == name or k.startswith(name) or name in k:
                            members = gs[k]
                            break
                if members:
                    for g in members:
                        idx = ctx.gene_index.get(g)
                        if idx is not None:
                            indicator[idx] = 1.0

        # Protein length lookup
        plen_map = {}
        prot = ctx.knowledge("protein_annotation")
        if prot is not None:
            cols = prot.get("columns", [])
            genes = prot.get("genes", {})
            try:
                li = cols.index("protein_length")
            except ValueError:
                li = 0
            for sym, vals in genes.items():
                if vals is None:
                    continue
                v = vals[li]
                if v is not None:
                    plen_map[sym] = float(v)

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tlen = 0.0
            tgenes = ctx.target_genes(p)
            if tgenes:
                lengths = [plen_map[g] for g in tgenes if g in plen_map]
                if lengths:
                    tlen = float(np.mean(lengths))
            out[i, :, 0] = tlen * indicator
        return out
