import numpy as np
from genemila.features.api import Feature, register


@register
class TargetAACompositionInteractionE159(Feature):
    name = "target_aa_composition_interaction_e159"
    version = 1
    description = (
        "Interaction between the amino-acid fraction (e.g. arginine) of the "
        "perturbation target protein and whether gene g belongs to translation "
        "gene sets."
    )
    rationale = (
        "Arginine-rich proteins are often RNA-binding/translation-related; "
        "perturbing them may preferentially affect translation machinery genes."
    )
    inputs = ["gene_annotation", "gene_sets"]
    params = {
        "aa_column": "aa_R",
        "translation_sets": ["GO:0006412", "REACTOME:Translation"],
    }
    dim = 1

    def _translation_mask(self, ctx, params):
        key = ("e159_translation_mask", tuple(params.get("translation_sets", [])))
        cache = ctx.cache
        if key in cache:
            return cache[key]

        mask = np.zeros(ctx.n_genes, dtype=np.float64)
        gs = ctx.knowledge("gene_sets")
        if isinstance(gs, dict):
            set_names = params.get("translation_sets", [])
            for sname in set_names:
                members = gs.get(sname)
                if not members:
                    continue
                for g in members:
                    idx = ctx.gene_index.get(g)
                    if idx is not None:
                        mask[idx] = 1.0
        cache[key] = mask
        return mask

    def _aa_fraction_table(self, ctx, params):
        aa_col = params.get("aa_column", "aa_R")
        key = ("e159_aa_frac", aa_col)
        cache = ctx.cache
        if key in cache:
            return cache[key]

        frac = np.zeros(ctx.n_genes, dtype=np.float64)
        ann = ctx.knowledge("gene_annotation")
        if isinstance(ann, dict):
            cols = ann.get("columns", [])
            genes = ann.get("genes", {})
            try:
                cidx = cols.index(aa_col)
            except ValueError:
                cidx = None
            if cidx is not None and isinstance(genes, dict):
                for g, vals in genes.items():
                    idx = ctx.gene_index.get(g)
                    if idx is None:
                        continue
                    if vals is None or cidx >= len(vals):
                        continue
                    v = vals[cidx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        frac[idx] = fv
        cache[key] = frac
        return frac

    def compute(self, ctx, perts, params):
        aa_frac = self._aa_fraction_table(ctx, params)
        trans_mask = self._translation_mask(ctx, params)

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=np.float64)
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # average aa fraction over target genes of p (usually one)
            tgt_aa = float(np.mean(aa_frac[tgt_idx]))
            if not np.isfinite(tgt_aa):
                continue
            out[i, :, 0] = tgt_aa * trans_mask

        out[~np.isfinite(out)] = 0.0
        return out
