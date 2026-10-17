import numpy as np
from genemila.features.api import Feature, register


@register
class TargetKnockdownProxyE13(Feature):
    name = "target_knockdown_proxy_e13"
    version = 1
    description = (
        "Target-level scalar (control mean expression or transcript length of the "
        "target gene) broadcast to all genes, as a proxy for CRISPRi knockdown efficiency."
    )
    rationale = (
        "Perturbations with stronger expected knockdown (based on target gene properties) "
        "produce larger expression changes; target expression or transcript length proxies "
        "knockdown strength and modulates response magnitude."
    )
    inputs = ["control_mean", "knowledge", "target_indices"]
    params = {"use": "control_mean"}
    dim = 1

    def compute(self, ctx, perts, params):
        use = params.get("use", "control_mean")
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Precompute target-level scalar per gene (for genes that are targets).
        gene_scalar = None
        if use == "control_mean":
            gene_scalar = np.asarray(ctx.control_mean, dtype=float)
        elif use == "transcript_length":
            ann = ctx.knowledge("gene_annotation")
            gene_scalar = np.full(n_genes, np.nan, dtype=float)
            if ann is not None:
                genes = ann.get("genes", {}) or {}
                cols = ann.get("columns", []) or []
                try:
                    idx = cols.index("transcript_length")
                except ValueError:
                    idx = None
                if idx is not None:
                    for gi, g in enumerate(ctx.genes):
                        vals = genes.get(g)
                        if vals is not None and len(vals) > idx and vals[idx] is not None:
                            try:
                                gene_scalar[gi] = float(vals[idx])
                            except (TypeError, ValueError):
                                pass
            # Fallback to control mean for missing entries.
            cm = np.asarray(ctx.control_mean, dtype=float)
            gene_scalar = np.where(np.isfinite(gene_scalar), gene_scalar, cm)
        else:
            gene_scalar = np.asarray(ctx.control_mean, dtype=float)

        # Fill non-finite with 0 to keep values finite.
        gene_scalar = np.where(np.isfinite(gene_scalar), gene_scalar, 0.0)

        # Cache target indices per perturbation.
        tcache = ctx.cache.setdefault("e13_target_indices", {})
        for i, p in enumerate(perts):
            if p in tcache:
                tidx = tcache[p]
            else:
                tidx = ctx.target_indices(p)
                tcache[p] = tidx
            if tidx:
                scalar = float(np.mean(gene_scalar[tidx]))
            else:
                scalar = 0.0
            out[i, :, 0] = scalar

        return out
