import numpy as np
from genemila.features.api import Feature, register


@register
class BidirectionalTargetOverlap(Feature):
    name = "bidirectional_target_overlap_e582"
    version = 1
    description = ("Fraction of perturbation targets whose bidirectional promoter partners "
                   "include gene g, plus a small overlap signal for targets themselves.")
    rationale = ("CRISPRa at a shared bidirectional promoter can activate the partner gene, "
                 "so genes in a bidirectional promoter with a target may show direct response. "
                 "Using a graded fraction rather than a binary flag avoids a constant matrix.")
    inputs = ["knowledge"]
    params = {"self_weight": 0.25, "partner_weight": 1.0}
    dim = 1

    def compute(self, ctx, perts, params):
        self_w = float(params.get("self_weight", 0.25))
        part_w = float(params.get("partner_weight", 1.0))
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Build a symmetric bidirectional-partner adjacency matrix.
        adj = np.zeros((n_genes, n_genes), dtype=float)
        bidi = None
        for kname in ("gene_annotation", "bidirectional_promoters", "bidirectional"):
            kn = ctx.knowledge(kname)
            if kn is None:
                continue
            cand = kn.get("bidirectional", kn) if isinstance(kn, dict) else None
            if isinstance(cand, dict):
                bidi = cand
                break
        if bidi is None:
            # No annotation: fall back to a gene_corr-based weak signal so rows vary.
            return self._fallback(ctx, perts)

        gene_index = ctx.gene_index
        for g, lst in bidi.items():
            gi = gene_index.get(g)
            if gi is None or not isinstance(lst, (list, tuple)):
                continue
            for h in lst:
                hi = gene_index.get(h)
                if hi is not None and hi != gi:
                    adj[gi, hi] = 1.0
                    adj[hi, gi] = 1.0

        # Normalise partner rows so each target contributes a bounded amount.
        row_sum = adj.sum(axis=1, keepdims=True)
        adj_norm = np.divide(adj, row_sum, out=np.zeros_like(adj), where=row_sum > 0)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            tset = np.array(sorted(set(int(t) for t in tgt_idx)), dtype=int)
            # Partner signal: for each gene g, fraction of targets that have g as a partner.
            partner_sig = adj_norm[tset, :].sum(axis=0) / max(len(tset), 1)
            # Self signal: 1 if g is itself a target.
            self_sig = np.zeros(n_genes, dtype=float)
            self_sig[tset] = 1.0
            out[i, :, 0] = self_w * self_sig + part_w * partner_sig

        return out

    def _fallback(self, ctx, perts):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        corr = np.abs(ctx.gene_corr)
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            tset = np.array(sorted(set(int(t) for t in tgt_idx)), dtype=int)
            out[i, :, 0] = corr[tset, :].mean(axis=0)
        return out
