import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPromoterActivityScoreE537(Feature):
    name = "target_promoter_activity_score_e537"
    version = 1
    description = ("Mean over p's target genes of (cpg_oe_promoter + log1p(n_tss_within_100kb)) "
                   "from the gene_annotation prior.")
    rationale = ("Promoter CpG content and local TSS density reflect transcriptional "
                 "responsiveness; targets with high promoter CpG or many nearby TSS may be "
                 "more strongly activated by CRISPRa.")
    inputs = ["knowledge:gene_annotation", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        cols = ann.get("columns", [])
        try:
            i_cpg = cols.index("cpg_oe_promoter")
            i_tss = cols.index("n_tss_within_100kb")
        except ValueError:
            return out

        genes_tbl = ann.get("genes", {})

        # Precompute per-gene score: cpg_oe_promoter + log1p(n_tss_within_100kb)
        score_by_gene = {}
        for sym, vals in genes_tbl.items():
            try:
                cpg = vals[i_cpg]
                tss = vals[i_tss]
            except (IndexError, TypeError):
                continue
            if cpg is None or tss is None:
                continue
            try:
                cpg = float(cpg)
                tss = float(tss)
            except (TypeError, ValueError):
                continue
            if not (np.isfinite(cpg) and np.isfinite(tss)):
                continue
            score_by_gene[sym] = cpg + np.log1p(max(tss, 0.0))

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            vals = [score_by_gene[g] for g in targets if g in score_by_gene]
            if vals:
                out[i, :, 0] = float(np.mean(vals))

        # Ensure finite values
        out[~np.isfinite(out)] = 0.0
        return out
