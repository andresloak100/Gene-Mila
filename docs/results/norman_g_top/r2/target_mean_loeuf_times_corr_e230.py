import numpy as np
from genemila.features.api import Feature, register


@register
class TargetMeanLoeufTimesCorr(Feature):
    name = "target_mean_loeuf_times_corr_e230"
    version = 1
    description = ("Mean LOEUF of p's target genes multiplied by the mean control-cell "
                   "Pearson correlation between gene g and each target gene.")
    rationale = ("Essential (low LOEUF) targets may drive stronger, co-expression-linked "
                 "downstream responses; this interaction captures that effect.")
    inputs = ["control_cells", "gene_corr", "target_genes"]
    params = {}
    dim = 1

    DEFAULT_LOEUF = 1.0

    def _loeuf_map(self, ctx):
        cache = ctx.cache
        key = "_e230_loeuf"
        if key in cache:
            return cache[key]
        loeuf = {}
        try:
            kn = ctx.knowledge("gene_constraint")
        except Exception:
            kn = None
        if kn and isinstance(kn, dict):
            cols = kn.get("columns", [])
            genes = kn.get("genes", {})
            if "oe_lof_upper" in cols and isinstance(genes, dict):
                idx = cols.index("oe_lof_upper")
                for g, vals in genes.items():
                    try:
                        v = vals[idx]
                    except Exception:
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except Exception:
                        continue
                    if np.isfinite(fv):
                        loeuf[g] = fv
        cache[key] = loeuf
        return loeuf

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        loeuf_map = self._loeuf_map(ctx)
        gene_corr = ctx.gene_corr
        gene_index = ctx.gene_index

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            target_idx = []
            loeufs = []
            for t in targets:
                if t in gene_index:
                    target_idx.append(gene_index[t])
                loeufs.append(loeuf_map.get(t, self.DEFAULT_LOEUF))
            if not loeufs:
                continue
            mean_loeuf = float(np.mean(loeufs))
            if not target_idx:
                continue
            # mean correlation of each gene g with target genes
            sub = gene_corr[:, target_idx]  # (n_genes, n_targets)
            mean_corr = sub.mean(axis=1)    # (n_genes,)
            vals = mean_corr * mean_loeuf
            vals = np.nan_to_num(vals, nan=0.0, posinf=0.0, neginf=0.0)
            out[i, :, 0] = vals

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
