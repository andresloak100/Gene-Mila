import numpy as np
from genemila.features.api import Feature, register


@register
class BidirectionalPartnerCoexpression(Feature):
    name = "bidirectional_partner_coexpression_e387"
    version = 2
    description = (
        "For each perturbation target with a bidirectional promoter partner "
        "(head-to-head TSS within 1000 bp), score each gene g by the Pearson "
        "correlation across control cells between g and the partner gene, "
        "scaled by a per-perturbation effect. Falls back to a target-based "
        "coexpression signature when no bidirectional partner is known."
    )
    rationale = (
        "CRISPRi/a at a bidirectional promoter can affect both genes; "
        "downstream effects may propagate to genes coexpressed with the partner "
        "(or, absent annotation, with the target itself)."
    )
    inputs = ["control_cells", "gene_corr"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)
        out = np.zeros((n_perts, n_genes, 1))

        gene_index = ctx.gene_index
        gene_corr = np.nan_to_num(ctx.gene_corr, nan=0.0, posinf=0.0, neginf=0.0)

        # Load prior knowledge (bidirectional partners) once.
        bidir = None
        try:
            bidir = ctx.knowledge("gene_annotation_bidirectional")
        except Exception:
            bidir = None
        if bidir is None:
            try:
                for name in ctx.available_knowledge():
                    if "bidirectional" in name.lower():
                        bidir = ctx.knowledge(name)
                        break
            except Exception:
                bidir = None
        if not isinstance(bidir, dict):
            bidir = {}

        cache = ctx.cache
        partner_cache = cache.setdefault("bidir_partner_idx_e387_v2", {})

        for i, p in enumerate(perts):
            if p not in partner_cache:
                partner_idx = -1
                target_idx = -1
                try:
                    targets = ctx.target_genes(p)
                except Exception:
                    targets = []
                for t in targets:
                    if t in gene_index and target_idx < 0:
                        target_idx = gene_index[t]
                    partners = bidir.get(t) if bidir else None
                    if partners:
                        if isinstance(partners, str):
                            partners = [partners]
                        for partner in partners:
                            if partner in gene_index and partner != t:
                                partner_idx = gene_index[partner]
                                break
                    if partner_idx >= 0:
                        break
                partner_cache[p] = (partner_idx, target_idx)

            partner_idx, target_idx = partner_cache[p]

            if partner_idx >= 0:
                # Coexpression with the bidirectional partner.
                vec = gene_corr[:, partner_idx].copy()
                # Emphasise partner itself and exclude self-correlation noise.
                vec[partner_idx] = 1.0
            elif target_idx >= 0:
                # Fallback: coexpression with the target gene itself.
                vec = gene_corr[:, target_idx].copy()
                vec[target_idx] = 1.0
            else:
                # No usable target: neutral row.
                vec = np.zeros(n_genes)

            out[i, :, 0] = vec

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
