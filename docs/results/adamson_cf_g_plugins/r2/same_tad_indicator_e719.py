import numpy as np
from genemila.features.api import Feature, register


@register
class SameTadIndicatorE719(Feature):
    name = "same_tad_indicator_e719"
    version = 1
    description = "Indicator that gene g lies within a genomic window (same chromosome) of the perturbation target."
    rationale = ("Local chromatin structure (TADs/enhancer-promoter contacts) can mediate off-target "
                 "regulatory effects; genes near the targeted TSS on the same chromosome are more likely "
                 "to be co-regulated, so we mark same-chromosome genes within a fixed distance window.")
    inputs = ["control_cells"]
    params = {"window_kb": 1000}
    dim = 1

    def compute(self, ctx, perts, params):
        window_kb = float(params.get("window_kb", 1000))
        window_bp = window_kb * 1000.0

        # Load loci once and cache chromosome / TSS arrays.
        cache = ctx.cache
        if "e719_loci" not in cache:
            anno = ctx.knowledge("gene_annotation")
            genes = ctx.genes
            n = ctx.n_genes
            chrom = np.full(n, -1, dtype=np.int64)
            tss = np.full(n, np.nan, dtype=np.float64)
            chrom_names = {}
            if anno is not None:
                loci = anno.get("loci", {}) or {}
                for i, g in enumerate(genes):
                    loc = loci.get(g)
                    if loc is None or len(loc) < 3:
                        continue
                    c, t, _strand = loc[0], loc[1], loc[2]
                    if c is None or t is None:
                        continue
                    try:
                        tval = float(t)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(tval):
                        continue
                    if c not in chrom_names:
                        chrom_names[c] = len(chrom_names)
                    chrom[i] = chrom_names[c]
                    tss[i] = tval
            cache["e719_loci"] = (chrom, tss)

        chrom, tss = cache["e719_loci"]
        n = ctx.n_genes

        out = np.zeros((len(perts), n, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if not tidx:
                continue
            # Use the first measured target gene's locus as anchor.
            valid_anchor = None
            for t in tidx:
                if 0 <= t < n and chrom[t] >= 0 and np.isfinite(tss[t]):
                    valid_anchor = t
                    break
            if valid_anchor is None:
                continue
            tc = chrom[valid_anchor]
            tt = tss[valid_anchor]

            same_chrom = chrom == tc
            close = np.abs(tss - tt) <= window_bp
            mask = same_chrom & close
            mask &= np.isfinite(tss)
            out[i, :, 0] = mask.astype(np.float64)

        return out
