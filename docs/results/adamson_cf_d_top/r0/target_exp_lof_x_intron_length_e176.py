import numpy as np
from genemila.features.api import Feature, register


@register
class TargetExpLofXIntronLength(Feature):
    name = "target_exp_lof_x_intron_length_e176"
    version = 1
    description = "Product of target gene's exp_lof and gene g's intron_length_kb."
    rationale = ("High expected LoF count targets may disrupt splicing or transcription "
                 "of long-intron genes; encodes target vulnerability x transcriptional burden.")
    inputs = ["gene_constraint", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # --- gene g intron length (kb) ---
        intron = np.zeros(n_genes, dtype=float)
        ga = ctx.knowledge("gene_annotation")
        if ga is not None:
            cols = ga.get("columns", [])
            try:
                idx = cols.index("intron_length_kb")
            except ValueError:
                idx = None
            genes_tab = ga.get("genes", {})
            if idx is not None:
                for j, g in enumerate(ctx.genes):
                    vals = genes_tab.get(g)
                    if vals is not None and idx < len(vals) and vals[idx] is not None:
                        try:
                            intron[j] = float(vals[idx])
                        except (TypeError, ValueError):
                            intron[j] = 0.0
        intron = np.nan_to_num(intron, nan=0.0, posinf=0.0, neginf=0.0)

        # --- target gene exp_lof ---
        gc = ctx.knowledge("gene_constraint")
        exp_lof_map = {}
        if gc is not None:
            cols = gc.get("columns", [])
            try:
                eidx = cols.index("exp_lof")
            except ValueError:
                eidx = None
            genes_tab = gc.get("genes", {})
            if eidx is not None:
                for g, vals in genes_tab.items():
                    if vals is not None and eidx < len(vals) and vals[eidx] is not None:
                        try:
                            exp_lof_map[g] = float(vals[eidx])
                        except (TypeError, ValueError):
                            pass

        for i, p in enumerate(perts):
            tv = 0.0
            for tg in ctx.target_genes(p):
                if tg in exp_lof_map:
                    tv += exp_lof_map[tg]
            if tv == 0.0:
                continue
            out[i, :, 0] = tv * intron

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
