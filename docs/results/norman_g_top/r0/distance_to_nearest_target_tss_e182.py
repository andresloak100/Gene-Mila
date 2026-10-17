import numpy as np
from genemila.features.api import Feature, register


@register
class DistanceToNearestTargetTSS(Feature):
    name = "distance_to_nearest_target_tss_e182"
    version = 1
    description = "Min |TSS distance| from gene g to any target gene's TSS (log-scaled)."
    rationale = ("CRISPRa can act on nearby genes; the genomic distance from g's TSS to "
                 "the nearest target TSS captures local cis-regulatory potential.")
    inputs = ["knowledge", "control_cells"]
    params = {"log_transform": True}
    dim = 1

    def _load_loci(self, ctx):
        cache = ctx.cache
        if "e182_loci" in cache:
            return cache["e182_loci"]
        loci = None
        for name in ctx.available_knowledge():
            if "gene_annotation" in name or "annotation" in name:
                k = ctx.knowledge(name)
                if k and isinstance(k, dict) and "loci" in k:
                    loci = k["loci"]
                    break
        if loci is None:
            k = ctx.knowledge("gene_annotation")
            if k and isinstance(k, dict):
                loci = k.get("loci")
        if loci is None:
            loci = {}
        cache["e182_loci"] = loci
        return loci

    def compute(self, ctx, perts, params):
        log_transform = bool(params.get("log_transform", True))
        loci = self._load_loci(ctx)
        n_genes = ctx.n_genes

        # Per-gene TSS position and chromosome, using gene symbol lookup.
        tss = np.full(n_genes, np.nan, dtype=np.float64)
        chrom = [None] * n_genes
        for i, g in enumerate(ctx.genes):
            rec = loci.get(g)
            if rec is None:
                continue
            try:
                c = rec[0]
                t = float(rec[1])
            except (IndexError, TypeError, ValueError):
                continue
            chrom[i] = c
            tss[i] = t

        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)
        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            # Collect target TSS positions grouped by chromosome.
            tgt_tss = {}
            for tg in targets:
                rec = loci.get(tg)
                if rec is None:
                    continue
                try:
                    c = rec[0]
                    t = float(rec[1])
                except (IndexError, TypeError, ValueError):
                    continue
                tgt_tss.setdefault(c, []).append(t)
            if not tgt_tss:
                continue
            for j in range(n_genes):
                c = chrom[j]
                if c is None or c not in tgt_tss:
                    continue
                tj = tss[j]
                if not np.isfinite(tj):
                    continue
                arr = tgt_tss[c]
                d = min(abs(tj - x) for x in arr)
                out[i, j, 0] = d

        if log_transform:
            out = np.log1p(np.maximum(out, 0.0))
        return out
