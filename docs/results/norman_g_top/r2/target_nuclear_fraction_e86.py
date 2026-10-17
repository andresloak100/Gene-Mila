import numpy as np
from genemila.features.api import Feature, register


@register
class TargetNuclearFractionE86(Feature):
    name = "target_nuclear_fraction_e86"
    version = 1
    description = "Fraction of a perturbation's target genes whose protein is annotated as nuclear."
    rationale = ("CRISPRa raises target expression; nuclear-localized products (e.g. transcription "
                 "factors) can propagate broader transcriptional effects than cytoplasmic ones.")
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        nucleus_idx = None
        genes_map = {}
        if isinstance(ann, dict):
            cols = ann.get("columns", [])
            if "nucleus" in cols:
                nucleus_idx = cols.index("nucleus")
            genes_map = ann.get("genes", {}) or {}

        # Precompute nuclear flag per gene symbol.
        nuclear_flag = {}
        if nucleus_idx is not None:
            for sym, vals in genes_map.items():
                if vals is None:
                    continue
                try:
                    v = vals[nucleus_idx]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                nuclear_flag[sym] = 1.0 if float(v) > 0 else 0.0

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                frac = 0.0
            else:
                flags = [nuclear_flag.get(g, 0.0) for g in targets]
                frac = float(np.mean(flags))
            out[i, :, 0] = frac

        return out
