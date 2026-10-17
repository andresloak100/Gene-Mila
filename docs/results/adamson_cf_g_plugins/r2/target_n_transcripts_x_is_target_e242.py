import numpy as np
from genemila.features.api import Feature, register

@register
class TargetNTranscriptsXIsTarget(Feature):
    name = "target_n_transcripts_x_is_target_e242"
    version = 1
    description = "Product of target gene's n_transcripts and is_target indicator."
    rationale = ("Genes with multiple transcripts may have more complex regulation, "
                 "affecting downstream expression changes; interacting transcript "
                 "count with the is_target indicator lets the model modulate the "
                 "direct target effect by transcript multiplicity.")
    inputs = ["knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        n_trans = None
        if ann is not None:
            try:
                cols = ann.get("columns", [])
                genes_map = ann.get("genes", {})
                if "n_transcripts" in cols:
                    idx = cols.index("n_transcripts")
                    n_trans = {}
                    for g, vals in genes_map.items():
                        if vals is not None and idx < len(vals) and vals[idx] is not None:
                            n_trans[g] = float(vals[idx])
            except Exception:
                n_trans = None

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if not tgenes:
                continue
            val = 0.0
            if n_trans is not None:
                for tg in tgenes:
                    if tg in n_trans:
                        val = n_trans[tg]
                        break
            if val == 0.0:
                val = 1.0
            for tg in tgenes:
                gi = ctx.gene_index.get(tg)
                if gi is not None:
                    out[i, gi, 0] = val
        return out
