import numpy as np
from genemila.features.api import Feature, register


@register
class ReplogleAdditiveXTargetPromoterGC(Feature):
    name = "replogle_additive_x_target_promoter_gc_e382"
    version = 1
    description = "Product of sign-corrected Replogle additive response and mean promoter GC of target genes."
    rationale = ("CRISPRa efficiency depends on promoter GC content of the target genes; "
                 "the Replogle additive response should be modulated by the target promoters' GC.")
    inputs = ["replogle_additive_response_signed_e104", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)

        base = ctx.feature("replogle_additive_response_signed_e104", perts)
        if base.ndim == 2:
            base = base[:, :, None]

        ann = ctx.knowledge("gene_annotation")
        gc_map = {}
        if ann is not None:
            cols = ann.get("columns", [])
            genes_ann = ann.get("genes", {})
            try:
                gi = cols.index("gc_promoter")
            except ValueError:
                gi = None
            if gi is not None:
                for g, vals in genes_ann.items():
                    if vals is None:
                        continue
                    v = vals[gi]
                    if v is not None:
                        gc_map[g] = float(v)

        cache = ctx.cache
        if "e382_target_gc" not in cache:
            cache["e382_target_gc"] = {}

        for i, p in enumerate(perts):
            if p in cache["e382_target_gc"]:
                mgc = cache["e382_target_gc"][p]
            else:
                tg = ctx.target_genes(p)
                vals = [gc_map[g] for g in tg if g in gc_map]
                mgc = float(np.mean(vals)) if vals else 0.0
                cache["e382_target_gc"][p] = mgc
            out[i, :, 0] = base[i, :, 0] * mgc

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
