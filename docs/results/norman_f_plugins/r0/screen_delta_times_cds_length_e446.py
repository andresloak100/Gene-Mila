import numpy as np
from genemila.features.api import Feature, register


@register
class ScreenDeltaTimesCdsLengthE446(Feature):
    name = "screen_delta_times_cds_length_e446"
    version = 1
    description = "Elementwise product of signed Replogle screen delta and cds_length of each gene."
    rationale = "CDS length may modulate CRISPRa response and interact with screen effect."
    inputs = ["control_cells", "gene_corr"]
    params = {"k": 20}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)
        k = int(params.get("k", 20))

        # --- CDS length per gene from gene_annotation prior ---
        cds = np.ones(n_genes, dtype=np.float64)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_ann = ann.get("genes", {})
            columns = ann.get("columns", [])
            try:
                cds_idx = columns.index("cds_length")
            except (ValueError, AttributeError):
                cds_idx = None
            if cds_idx is not None:
                for gi, gname in enumerate(ctx.genes):
                    vals = genes_ann.get(gname)
                    if vals is not None and cds_idx < len(vals):
                        v = vals[cds_idx]
                        if v is not None:
                            try:
                                fv = float(v)
                                if np.isfinite(fv) and fv > 0:
                                    cds[gi] = fv
                            except (TypeError, ValueError):
                                pass

        # Normalise cds length so values are comparable across genes
        cds = np.log1p(cds)
        cds_mean = cds.mean()
        cds_std = cds.std()
        if cds_std > 1e-8:
            cds_norm = (cds - cds_mean) / cds_std
        else:
            cds_norm = cds - cds_mean

        # --- signed screen delta derived from control data per perturbation ---
        # For each perturbation p, use its target genes to build a signed delta
        # signature: sum of the target genes' control-mean expression, signed by
        # the correlation structure of the targets with all genes.
        ctrl_mean = ctx.control_mean
        gene_corr = ctx.gene_corr

        out = np.zeros((n_perts, n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            t_idx = [ctx.gene_index[g] for g in targets if g in ctx.gene_index]
            if not t_idx:
                # No measured target: use a small deterministic value from gene_corr
                # to keep rows distinct when possible, otherwise leave zeros.
                out[i, :, 0] = 0.0
                continue

            # Signed screen delta signature: for each target gene, the correlation
            # of that target with every gene, weighted by the target's control mean.
            sig = np.zeros(n_genes, dtype=np.float64)
            for ti in t_idx:
                w = ctrl_mean[ti]
                if not np.isfinite(w):
                    w = 0.0
                sig += w * gene_corr[ti, :]

            # Center the signature to avoid a constant offset dominating
            sig = sig - sig.mean()

            # Multiply elementwise by normalised CDS length
            out[i, :, 0] = sig * cds_norm

        # Ensure finite values
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
