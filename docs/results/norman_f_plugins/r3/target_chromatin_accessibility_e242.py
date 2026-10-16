import numpy as np
from genemila.features.api import Feature, register


@register
class TargetChromatinAccessibilityE242(Feature):
    name = "target_chromatin_accessibility_e242"
    version = 1
    description = "Mean chromatin-accessibility proxy (e.g. promoter GC content) over p's target genes."
    rationale = ("CRISPRa requires accessible chromatin for effective activation; target genes in open "
                 "regions may be more efficiently activated, leading to larger downstream deltas.")
    inputs = ["knowledge:gene_annotation"]
    params = {"proxy": "gc_promoter"}
    dim = 1

    def compute(self, ctx, perts, params):
        proxy = params.get("proxy", "gc_promoter")
        ann = ctx.knowledge("gene_annotation")

        # Build a lookup gene -> proxy value once, cached across perturbations.
        cache = ctx.cache
        key = ("tca_e242_lookup", proxy)
        lookup = cache.get(key)
        if lookup is None:
            lookup = {}
            if ann is not None:
                genes_map = ann.get("genes") if isinstance(ann, dict) else None
                columns = ann.get("columns") if isinstance(ann, dict) else None
                if isinstance(genes_map, dict) and isinstance(columns, (list, tuple)):
                    # locate the proxy column index
                    col_idx = None
                    for j, c in enumerate(columns):
                        if c == proxy:
                            col_idx = j
                            break
                    if col_idx is not None:
                        for g, vals in genes_map.items():
                            try:
                                v = vals[col_idx]
                            except (TypeError, IndexError, KeyError):
                                continue
                            if v is None:
                                continue
                            try:
                                fv = float(v)
                            except (TypeError, ValueError):
                                continue
                            if np.isfinite(fv):
                                lookup[g] = fv
            cache[key] = lookup

        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            vals = [lookup[g] for g in targets if g in lookup]
            if vals:
                val = float(np.mean(vals))
            else:
                val = 0.0
            if not np.isfinite(val):
                val = 0.0
            out[i, :, 0] = val
        return out
