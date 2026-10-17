import numpy as np
from genemila.features.api import Feature, register, FeatureContext


@register
class TargetLoeufE22(Feature):
    name = "target_loeuf_e22"
    version = 1
    description = "LOEUF (oe_lof_upper) of the perturbation target gene, broadcast to all genes."
    rationale = ("Genes that are loss-of-function intolerant (low LOEUF) may produce stronger "
                 "transcriptomic responses when perturbed; this exposes target essentiality "
                 "as a per-perturbation scalar for every gene row.")
    inputs = ["gene_constraint"]
    params = {"fillna": "median"}
    dim = 1

    def compute(self, ctx: FeatureContext, perts: list[str], params: dict) -> np.ndarray:
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        knowledge = ctx.knowledge("gene_constraint")
        gene_vals = {}
        loeuf_idx = None
        if knowledge is not None:
            cols = knowledge.get("columns", [])
            try:
                loeuf_idx = cols.index("oe_lof_upper")
            except (ValueError, AttributeError):
                loeuf_idx = None
            if loeuf_idx is not None:
                gene_vals = knowledge.get("genes", {}) or {}

        # Resolve target gene symbol per perturbation.
        target_syms = []
        for p in perts:
            syms = ctx.target_genes(p) if hasattr(ctx, "target_genes") else []
            target_syms.append(syms[0] if syms else None)

        # Collect LOEUF values (first non-null per target).
        raw = []
        for sym in target_syms:
            val = None
            if sym is not None and gene_vals:
                entry = gene_vals.get(sym)
                if entry is not None and loeuf_idx < len(entry):
                    v = entry[loeuf_idx]
                    if v is not None:
                        try:
                            fv = float(v)
                            if np.isfinite(fv):
                                val = fv
                        except (TypeError, ValueError):
                            val = None
            raw.append(val)

        fillna = params.get("fillna", "median")
        valid = [v for v in raw if v is not None]
        if valid:
            if fillna == "median":
                fill = float(np.median(valid))
            elif fillna == "mean":
                fill = float(np.mean(valid))
            elif fillna == "zero":
                fill = 0.0
            else:
                fill = float(np.median(valid))
        else:
            fill = 0.0

        for i, v in enumerate(raw):
            out[i, :, 0] = v if v is not None else fill

        return out
