import numpy as np
from genemila.features.api import Feature, register


@register
class TargetChromatinAccessibilityE590(Feature):
    name = "target_chromatin_accessibility_e590"
    version = 1
    description = ("Mean chromatin-accessibility proxy (promoter GC content and CpG "
                   "density) around the TSS of each target gene of a perturbation, "
                   "broadcast to all genes.")
    rationale = ("CRISPRa requires accessible chromatin at the target promoter; targets "
                 "in GC-rich, CpG-dense (open) promoters may be activated more strongly. "
                 "Promoter GC content and CpG density serve as a proxy for accessibility.")
    inputs = ["knowledge"]
    params = {}
    dim = 1

    def _accessibility(self, ctx):
        """Per-gene accessibility proxy from gene_annotation promoter GC and CpG density."""
        cached = ctx.cache.get("_e590_access")
        if cached is not None:
            return cached

        n = ctx.n_genes
        acc = np.zeros(n, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None and "genes" in ann:
            cols = list(ann.get("columns", []))
            idx_gc = cols.index("gc_promoter") if "gc_promoter" in cols else None
            idx_cpg = cols.index("cpg_oe_promoter") if "cpg_oe_promoter" in cols else None
            genes = ann["genes"]
            gc_vals = []
            cpg_vals = []
            for g in ctx.genes:
                row = genes.get(g)
                gc = np.nan
                cpg = np.nan
                if row is not None:
                    if idx_gc is not None and idx_gc < len(row) and row[idx_gc] is not None:
                        try:
                            gc = float(row[idx_gc])
                        except (TypeError, ValueError):
                            gc = np.nan
                    if idx_cpg is not None and idx_cpg < len(row) and row[idx_cpg] is not None:
                        try:
                            cpg = float(row[idx_cpg])
                        except (TypeError, ValueError):
                            cpg = np.nan
                gc_vals.append(gc)
                cpg_vals.append(cpg)
            gc_arr = np.array(gc_vals, dtype=float)
            cpg_arr = np.array(cpg_vals, dtype=float)

            def _z(a):
                m = np.isfinite(a)
                if m.sum() < 2:
                    return np.zeros_like(a)
                mu = a[m].mean()
                sd = a[m].std()
                if sd <= 0:
                    return np.zeros_like(a)
                z = (a - mu) / sd
                z[~m] = 0.0
                return z

            acc = _z(gc_arr) + _z(cpg_arr)
            acc = np.nan_to_num(acc, nan=0.0, posinf=0.0, neginf=0.0)
        else:
            # Fallback: use control expression level as a weak accessibility proxy.
            cm = ctx.control_mean
            m = np.isfinite(cm)
            if m.sum() >= 2 and cm[m].std() > 0:
                acc = (cm - cm[m].mean()) / cm[m].std()
                acc = np.nan_to_num(acc, nan=0.0, posinf=0.0, neginf=0.0)

        ctx.cache["_e590_access"] = acc
        return acc

    def compute(self, ctx, perts, params):
        acc = self._accessibility(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            idxs = ctx.target_indices(p)
            if idxs:
                val = float(np.mean(acc[idxs]))
            else:
                val = 0.0
            if not np.isfinite(val):
                val = 0.0
            out[i, :, 0] = val
        return out
