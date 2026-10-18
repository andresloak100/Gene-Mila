import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufXGeneGlobinCorr(Feature):
    name = "target_loeuf_x_gene_globin_corr_e244"
    version = 1
    description = ("Product of the target gene's LOEUF (LoF constraint) and gene g's "
                   "control-expression correlation with the mean of globin genes.")
    rationale = ("LoF-intolerant targets may have stronger downstream effects on genes "
                 "co-regulated with globin genes.")
    inputs = ["control_cells", "gene_corr"]
    params = {}
    dim = 1

    GLOBIN_GENES = ["HBZ", "HBA1", "HBG1", "HBG2"]

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_p = len(perts)

        # --- gene-side: correlation of each gene with mean globin expression ---
        cache = ctx.cache
        key = "e244_gene_globin_corr"
        if key not in cache:
            ctrl = np.asarray(ctx.control_cells, dtype=float)
            glob_idx = [ctx.gene_index[g] for g in self.GLOBIN_GENES
                        if g in ctx.gene_index]
            if len(glob_idx) == 0:
                gene_corr = np.zeros(n_genes, dtype=float)
            else:
                glob_mean = ctrl[:, glob_idx].mean(axis=1)  # (n_cells,)
                gm = glob_mean - glob_mean.mean()
                gs = gm.std()
                # per-gene correlation with globin mean
                X = ctrl - ctrl.mean(axis=0, keepdims=True)
                xs = X.std(axis=0)
                denom = xs * gs
                num = (X * gm[:, None]).mean(axis=0)
                with np.errstate(divide="ignore", invalid="ignore"):
                    gene_corr = np.where(denom > 1e-12, num / denom, 0.0)
            gene_corr = np.nan_to_num(gene_corr, nan=0.0, posinf=0.0, neginf=0.0)
            cache[key] = gene_corr
        gene_corr = cache[key]

        # --- target-side: LOEUF (fallback pLI) from gene_constraint ---
        key2 = "e244_target_loeuf"
        if key2 not in cache:
            loeuf_map = {}
            pLI_map = {}
            kc = ctx.knowledge("gene_constraint")
            if kc is not None:
                cols = kc.get("columns", [])
                genes_tbl = kc.get("genes", {}) or {}
                # locate columns
                def _idx(name):
                    try:
                        return cols.index(name)
                    except (ValueError, AttributeError):
                        return None
                i_loeuf = _idx("oe_lof_upper")
                i_pli = _idx("pLI")
                for g, vals in genes_tbl.items():
                    if not isinstance(vals, (list, tuple)):
                        continue
                    if i_loeuf is not None and i_loeuf < len(vals):
                        v = vals[i_loeuf]
                        if v is not None:
                            loeuf_map[g] = float(v)
                    if i_pli is not None and i_pli < len(vals):
                        v = vals[i_pli]
                        if v is not None:
                            pLI_map[g] = float(v)
            cache[key2] = (loeuf_map, pLI_map)
        loeuf_map, pLI_map = cache[key2]

        # default LOEUF value for targets with no constraint data (median-ish)
        default_loeuf = 1.0

        out = np.zeros((n_p, n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            val = None
            for t in tg:
                if t in loeuf_map:
                    val = loeuf_map[t]
                    break
            if val is None:
                for t in tg:
                    if t in pLI_map:
                        # high pLI -> LoF-intolerant -> map to low LOEUF-like scale
                        val = 1.0 - float(pLI_map[t])
                        break
            if val is None:
                val = default_loeuf
            out[i, :, 0] = val * gene_corr

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
