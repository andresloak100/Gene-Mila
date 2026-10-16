import numpy as np
from genemila.features.api import Feature, register


@register
class ReplogleAdditiveXTargetPromoterCpgE558(Feature):
    name = "replogle_additive_x_target_promoter_cpg__e558"
    version = 1
    description = "Product of sign-corrected Replogle additive response and the mean CpG observed/expected ratio of the promoters of the perturbation's target genes."
    rationale = "Promoter CpG content of the target genes modulates the additive Replogle response, capturing regulatory context of the perturbed loci."
    inputs = ["gene_annotation", "replogle2022_k562", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes

        # --- Replogle additive response (sign-corrected) ---
        rep = ctx.knowledge("replogle2022_k562")
        rep_genes = None
        rep_perts = None
        rep_sign = -1.0
        if rep is not None:
            rep_genes = rep.get("genes")
            rep_perts = rep.get("perts") or {}
            s = rep.get("sign")
            if s is not None:
                rep_sign = float(s)

        # Map gene symbol -> column index for bundle genes
        gene_index = ctx.gene_index

        # Precompute per-target-gene Replogle delta vector aligned to bundle genes.
        # rep_perts[gene] = {"delta": [...]} possibly null.
        rep_delta = {}
        if rep_perts is not None and rep_genes is not None:
            for g, entry in rep_perts.items():
                if entry is None:
                    continue
                d = entry.get("delta") if isinstance(entry, dict) else None
                if d is None:
                    continue
                rep_delta[g] = np.asarray(d, dtype=float)

        # --- gene_annotation cpg_oe_promoter ---
        ann = ctx.knowledge("gene_annotation")
        cpg_map = {}
        if ann is not None:
            cols = ann.get("columns") or []
            genes_ann = ann.get("genes") or {}
            try:
                cpg_idx = cols.index("cpg_oe_promoter")
            except ValueError:
                cpg_idx = None
            if cpg_idx is not None:
                for g, vals in genes_ann.items():
                    if vals is None:
                        continue
                    v = vals[cpg_idx]
                    if v is not None:
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            cpg_map[g] = fv

        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue

            # mean cpg_oe_promoter over targets
            cpg_vals = [cpg_map[g] for g in targets if g in cpg_map]
            if cpg_vals:
                mean_cpg = float(np.mean(cpg_vals))
            else:
                mean_cpg = 0.0

            if mean_cpg == 0.0:
                continue

            # replogle additive response: sum over targets of sign-corrected delta
            add = np.zeros(n_genes, dtype=float)
            any_rep = False
            for g in targets:
                dvec = rep_delta.get(g)
                if dvec is None:
                    continue
                # align length to n_genes
                m = min(n_genes, dvec.shape[0])
                add[:m] += dvec[:m]
                any_rep = True
            if not any_rep:
                continue

            add *= rep_sign
            out[i, :, 0] = add * mean_cpg

        # ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
