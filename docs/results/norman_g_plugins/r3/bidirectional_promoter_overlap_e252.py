import numpy as np
from genemila.features.api import Feature, register

@register
class BidirectionalPromoterOverlapE252(Feature):
    name = "bidirectional_promoter_overlap_e252"
    version = 2
    description = "Per gene g: 1 if g shares a bidirectional promoter with any target of p, else 0; falls back to correlation-weighted target signal when no bidirectional annotation is available."
    rationale = "CRISPRa at a TSS may also affect genes on the opposite strand within 1000 bp (shared bidirectional promoters). When the annotation is missing or gives a constant signal, use target-gene correlation as a proxy for shared regulatory context."
    inputs = ["knowledge", "gene_corr"]
    params = {"corr_weight": 0.5, "min_corr": 0.0}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)
        out = np.zeros((n_perts, n_genes, 1), dtype=float)
        gene_index = ctx.gene_index

        corr_weight = float(params.get("corr_weight", 0.5))
        min_corr = float(params.get("min_corr", 0.0))

        # Build bidirectional partner map: gene column -> set of partner columns.
        kb = ctx.knowledge("gene_annotation")
        bidir = (kb or {}).get("bidirectional", {}) if kb else {}
        partner_cache = {}
        if bidir:
            for sym, partners in bidir.items():
                if sym not in gene_index:
                    continue
                cols = set()
                if isinstance(partners, (list, tuple)):
                    for q in partners:
                        if isinstance(q, str):
                            qi = gene_index.get(q)
                            if qi is not None:
                                cols.add(qi)
                if cols:
                    partner_cache[gene_index[sym]] = cols

        gene_corr = ctx.gene_corr

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            tcols = [gene_index[t] for t in targets if t in gene_index]
            if not tcols:
                continue

            # Bidirectional overlap score.
            hit = np.zeros(n_genes, dtype=float)
            any_partner = False
            for tc in tcols:
                cols = partner_cache.get(tc)
                if cols:
                    any_partner = True
                    for c in cols:
                        hit[c] = 1.0

            # Correlation-based proxy from targets to all genes.
            corr_sig = np.zeros(n_genes, dtype=float)
            for tc in tcols:
                row = gene_corr[tc]
                vals = np.where(row >= min_corr, row, 0.0)
                corr_sig = np.maximum(corr_sig, vals)
            # also include target genes themselves
            for tc in tcols:
                corr_sig[tc] = max(corr_sig[tc], 1.0)

            if any_partner:
                combined = hit + corr_weight * corr_sig
            else:
                combined = corr_sig

            out[i, :, 0] = combined

        # Ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
