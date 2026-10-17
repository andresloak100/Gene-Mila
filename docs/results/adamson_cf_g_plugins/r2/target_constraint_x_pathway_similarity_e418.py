import numpy as np
from genemila.features.api import Feature, register

@register
class TargetConstraintXPathwaySimilarityE418(Feature):
    name = "target_constraint_x_pathway_similarity_e418"
    version = 1
    description = ("Product of inverted target LOEUF (LoF constraint) and gene-set "
                   "similarity between the target gene and each gene.")
    rationale = ("LoF-intolerant (low LOEUF) targets are likely essential; their "
                 "perturbation should dysregulate pathway members more strongly. "
                 "Combining inverted target LOEUF with gene-set similarity captures "
                 "constraint-weighted pathway coupling.")
    inputs = ["knowledge", "target_indices", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        # Fetch gene-set similarity feature (target t vs gene g).
        try:
            sim = ctx.feature("gene_set_similarity_e12", perts)
            sim = np.asarray(sim, dtype=float)
            if sim.ndim == 2:
                sim = sim[:, :, None]
        except Exception:
            sim = None

        # Load gene constraint knowledge (LOEUF).
        loeuf = {}
        try:
            gc = ctx.knowledge("gene_constraint")
            if gc is not None:
                cols = gc.get("columns", [])
                genes_tbl = gc.get("genes", {})
                if "oe_lof_upper" in cols:
                    idx = cols.index("oe_lof_upper")
                    for sym, vals in genes_tbl.items():
                        if vals is None:
                            continue
                        v = vals[idx]
                        if v is not None:
                            try:
                                loeuf[sym] = float(v)
                            except (TypeError, ValueError):
                                pass
        except Exception:
            pass

        def invert_loeuf(sym):
            v = loeuf.get(sym)
            if v is None:
                return 0.5  # neutral fallback
            # LOEUF typically ~0.1-1.5; lower = more constrained.
            # Invert via 1/(1+LOEUF) so lower LOEUF -> higher weight.
            return 1.0 / (1.0 + max(v, 0.0))

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if not tgenes:
                # No target: leave zeros.
                continue
            # Average inverted LOEUF over target genes.
            w = np.mean([invert_loeuf(t) for t in tgenes])
            if sim is not None:
                out[i, :, 0] = w * sim[i, :, 0]
            else:
                # Fallback: no similarity available -> zero.
                pass

        # Ensure finite.
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
