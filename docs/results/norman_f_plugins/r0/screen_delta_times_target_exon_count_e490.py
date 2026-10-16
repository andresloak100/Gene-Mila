import numpy as np
from genemila.features.api import Feature, register


@register
class ScreenDeltaTimesTargetExonCount(Feature):
    name = "screen_delta_times_target_exon_count_e490"
    version = 1
    description = "Elementwise product of replogle_delta_signed_e35 and the sum of n_exons over the perturbation's target genes."
    rationale = ("Exon count reflects gene complexity and may modulate CRISPRa efficiency; "
                 "scaling the signed screen delta by the total exon count of the targets "
                 "provides a complexity-weighted response signal.")
    inputs = ["replogle_delta_signed_e35", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # Fetch the screen delta feature (shape (n_perts, n_genes, 1))
        screen = ctx.feature("replogle_delta_signed_e35", perts)
        if screen.ndim == 2:
            screen = screen[:, :, None]

        # Load gene annotation once and cache the n_exons lookup
        cache = ctx.cache
        if "e490_exon_map" not in cache:
            ann = ctx.knowledge("gene_annotation")
            exon_map = {}
            if ann is not None:
                genes_dict = ann.get("genes") if isinstance(ann, dict) else None
                columns = ann.get("columns") if isinstance(ann, dict) else None
                if genes_dict and columns:
                    try:
                        idx = columns.index("n_exons")
                    except ValueError:
                        idx = None
                    if idx is not None:
                        for sym, vals in genes_dict.items():
                            try:
                                v = vals[idx]
                            except (TypeError, IndexError):
                                continue
                            if v is None:
                                continue
                            try:
                                fv = float(v)
                            except (TypeError, ValueError):
                                continue
                            if np.isfinite(fv):
                                exon_map[sym] = fv
            cache["e490_exon_map"] = exon_map
        exon_map = cache["e490_exon_map"]

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            s = 0.0
            for t in targets:
                s += exon_map.get(t, 0.0)
            out[i, :, 0] = screen[i, :, 0] * s

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
