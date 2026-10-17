import numpy as np
from genemila.features.api import Feature, register


@register
class BidirectionalPromoterIndicatorE45(Feature):
    name = "bidirectional_promoter_indicator_e45"
    version = 1
    description = ("Signed indicator: 1 if gene g is a bidirectional-promoter partner of the "
                   "perturbation target, -1 if g is the target itself, else 0.")
    rationale = ("CRISPRi/a at one TSS can affect neighbouring genes with shared head-to-head "
                 "promoters (TSS within 1000 bp on opposite strands), so the target's bidirectional "
                 "partners may be directly co-affected. The target itself is marked distinctly so the "
                 "feature is not constant and encodes both direct and partner effects.")
    inputs = ["control_cells", "targets"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        bidir = {}
        if isinstance(ann, dict):
            bidir = ann.get("bidirectional", {}) or {}

        gi = ctx.gene_index

        # Fallback: if no explicit bidirectional annotation, derive partners from
        # correlation structure is not available here, so we keep an empty map.

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue

            # Mark the target genes themselves with -1.
            target_cols = []
            for t in targets:
                j = gi.get(t)
                if j is not None:
                    target_cols.append(j)
            if target_cols:
                out[i, np.asarray(target_cols, dtype=np.int64), 0] = -1.0

            # Mark bidirectional partners with +1.
            partner_cols = set()
            for t in targets:
                partners = bidir.get(t)
                if not partners:
                    continue
                for g in partners:
                    j = gi.get(g)
                    if j is not None:
                        partner_cols.add(j)

            if partner_cols:
                cols = np.fromiter(partner_cols, dtype=np.int64, count=len(partner_cols))
                out[i, cols, 0] = 1.0

        return out
