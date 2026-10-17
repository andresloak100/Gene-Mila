import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufXGeneSetSimilarityE575(Feature):
    name = "target_loeuf_x_gene_set_similarity_e575"
    version = 1
    description = "Product of target LOEUF and gene-set Jaccard similarity between target and gene."
    rationale = "Essential targets (low LOEUF) may have broader downstream effects, so "
    rationale += "interactions between target essentiality and gene-set similarity are informative."
    inputs = ["gene_constraint", "gene_sets", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)

        # Gene-set similarity feature (already registered), shape (n_perts, n_genes, 1)
        sim = ctx.feature("gene_set_similarity_e12", perts)
        sim = np.asarray(sim, dtype=float)
        if sim.ndim == 3:
            sim = sim[:, :, 0]
        elif sim.ndim == 2:
            pass
        else:
            sim = sim.reshape(n_perts, n_genes)

        # LOEUF per gene from gene_constraint knowledge
        constraint = ctx.knowledge("gene_constraint")
        loeuf_col = None
        loeuf_by_gene = {}
        if constraint is not None:
            cols = constraint.get("columns", [])
            try:
                loeuf_col = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_col = None
            if loeuf_col is not None:
                genes_tbl = constraint.get("genes", {})
                for g, vals in genes_tbl.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[loeuf_col]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    loeuf_by_gene[g] = float(v)

        # Default LOEUF for genes without annotation: use median of known, else 1.0
        if loeuf_by_gene:
            default_loeuf = float(np.median(list(loeuf_by_gene.values())))
        else:
            default_loeuf = 1.0

        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if targets:
                vals = [loeuf_by_gene.get(t, default_loeuf) for t in targets]
                t_loeuf = float(np.mean(vals))
            else:
                t_loeuf = default_loeuf
            out[i, :, 0] = t_loeuf * sim[i]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
