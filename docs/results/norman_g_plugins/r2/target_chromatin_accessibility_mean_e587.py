import numpy as np
from genemila.features.api import Feature, register


@register
class TargetChromatinAccessibilityMeanE587(Feature):
    name = "target_chromatin_accessibility_mean_e587"
    version = 1
    description = (
        "Mean chromatin accessibility score of the perturbation's target genes, "
        "derived from promoter CpG-island content and GC content as an accessibility proxy."
    )
    rationale = (
        "CRISPRa requires accessible chromatin at target promoters to activate transcription. "
        "Genes with CpG-rich, GC-rich promoters tend to reside in open, constitutively accessible "
        "chromatin; averaging this proxy over a perturbation's targets estimates how readily "
        "those targets can be activated."
    )
    inputs = ["knowledge"]
    params = {}
    dim = 1

    def _accessibility_table(self, ctx):
        cache = ctx.cache
        key = "_e587_access_table"
        if key in cache:
            return cache[key]

        n = ctx.n_genes
        acc = np.zeros(n, dtype=float)

        ka = ctx.knowledge("gene_annotation")
        if ka is not None and isinstance(ka, dict) and "genes" in ka:
            cols = ka.get("columns", [])
            try:
                i_cpg = cols.index("cpg_oe_promoter")
            except ValueError:
                i_cpg = None
            try:
                i_gcprom = cols.index("gc_promoter")
            except ValueError:
                i_gcprom = None
            genes_tbl = ka.get("genes", {})
            for g, gi in ctx.gene_index.items():
                vals = genes_tbl.get(g)
                if vals is None:
                    continue
                s = 0.0
                c = 0
                if i_cpg is not None and i_cpg < len(vals) and vals[i_cpg] is not None:
                    try:
                        s += float(vals[i_cpg])
                        c += 1
                    except (TypeError, ValueError):
                        pass
                if i_gcprom is not None and i_gcprom < len(vals) and vals[i_gcprom] is not None:
                    try:
                        s += float(vals[i_gcprom])
                        c += 1
                    except (TypeError, ValueError):
                        pass
                if c > 0:
                    acc[gi] = s / c

        # standardise across genes so the score is comparable and finite
        mu = float(np.nanmean(acc)) if n > 0 else 0.0
        sd = float(np.nanstd(acc)) if n > 0 else 0.0
        if not np.isfinite(mu):
            mu = 0.0
        if not np.isfinite(sd) or sd <= 1e-12:
            sd = 1.0
        acc = (acc - mu) / sd
        acc = np.nan_to_num(acc, nan=0.0, posinf=0.0, neginf=0.0)

        cache[key] = acc
        return acc

    def compute(self, ctx, perts, params):
        acc = self._accessibility_table(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            idx = ctx.target_indices(p)
            if idx:
                val = float(np.mean(acc[idx]))
            else:
                val = 0.0
            if not np.isfinite(val):
                val = 0.0
            out[i, :, 0] = val
        return out
