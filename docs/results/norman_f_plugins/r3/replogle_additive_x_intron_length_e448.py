import numpy as np
from genemila.features.api import Feature, register


@register
class ReplogleAdditiveXIntronLengthE448(Feature):
    name = "replogle_additive_x_intron_length_e448"
    version = 1
    description = "Product of sign-corrected Replogle additive response and total intron length (kb) of gene g, normalized by SD across genes."
    rationale = "Intron length is a static gene annotation feature that may modulate how a perturbation's signal propagates; interacting it with the strong Replogle additive response could uncover modulation."
    inputs = ["control_cells", "gene_annotation"]
    params = {"normalize": "true"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        normalize = str(params.get("normalize", "true")).lower() in ("true", "1", "yes")

        # ---- intron length per gene (kb) from gene_annotation ----
        ann = ctx.knowledge("gene_annotation")
        intron_kb = np.zeros(n_genes, dtype=np.float64)
        if ann is not None:
            genes_map = ann.get("genes", {}) or {}
            columns = ann.get("columns", []) or []
            try:
                col_idx = columns.index("intron_length_kb")
            except ValueError:
                col_idx = None
            if col_idx is not None:
                for i, g in enumerate(ctx.genes):
                    vals = genes_map.get(g)
                    if vals is not None and col_idx < len(vals) and vals[col_idx] is not None:
                        try:
                            intron_kb[i] = float(vals[col_idx])
                        except (TypeError, ValueError):
                            intron_kb[i] = 0.0
        # replace non-finite with 0
        intron_kb = np.where(np.isfinite(intron_kb), intron_kb, 0.0)

        if normalize:
            sd = float(np.std(intron_kb))
            if sd > 0:
                intron_norm = intron_kb / sd
            else:
                intron_norm = intron_kb
        else:
            intron_norm = intron_kb

        # ---- sign-corrected Replogle additive response ----
        repl = ctx.feature("replogle_additive_response_signed_e104", perts)
        # shape (n_perts, n_genes, 1)
        repl = np.asarray(repl, dtype=np.float64)
        if repl.ndim == 2:
            repl = repl[:, :, None]

        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)
        for i in range(len(perts)):
            out[i, :, 0] = repl[i, :, 0] * intron_norm

        out = np.where(np.isfinite(out), out, 0.0)
        return out
