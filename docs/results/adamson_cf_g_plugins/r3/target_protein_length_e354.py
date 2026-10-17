import numpy as np
from genemila.features.api import Feature, register


@register
class TargetProteinLengthE354(Feature):
    name = "target_protein_length_e354"
    version = 1
    description = "Protein length (UniProt) of the perturbation target, broadcast to all genes."
    rationale = ("Longer proteins may be harder to fully knock down with CRISPRi, so "
                 "target protein length may modulate the magnitude of observed effects.")
    inputs = ["knowledge:protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        genes_tbl = {}
        col_idx = None
        if isinstance(ann, dict):
            genes_tbl = ann.get("genes", {}) or {}
            cols = ann.get("columns", []) or []
            try:
                col_idx = list(cols).index("protein_length")
            except ValueError:
                col_idx = None

        def _get_len(sym):
            if sym is None or sym not in genes_tbl:
                return None
            vals = genes_tbl[sym]
            if vals is None:
                return None
            try:
                if col_idx is not None and col_idx < len(vals):
                    v = vals[col_idx]
                elif len(vals) == 1:
                    v = vals[0]
                else:
                    v = None
            except Exception:
                v = None
            if v is None:
                return None
            try:
                fv = float(v)
            except (TypeError, ValueError):
                return None
            if not np.isfinite(fv):
                return None
            return fv

        # Collect target protein lengths and build fallback median.
        target_lens = []
        for p in perts:
            tg = ctx.target_genes(p)
            val = None
            if tg:
                val = _get_len(tg[0])
            target_lens.append(val)

        valid = [v for v in target_lens if v is not None]
        if valid:
            fill = float(np.median(np.asarray(valid, dtype=float)))
        else:
            fill = 0.0

        for i, val in enumerate(target_lens):
            v = val if val is not None else fill
            out[i, :, 0] = v

        return out
