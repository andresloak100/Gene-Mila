import numpy as np
from genemila.features.api import Feature, register


@register
class TargetEssentialityComboE50(Feature):
    name = "target_essentiality_combo_e50"
    version = 1
    description = "Combined target-gene LoF constraint score (LOEUF, pLI, missense z), standardized."
    rationale = "Perturbations of LoF-intolerant (essential) genes may produce larger downstream changes; a combined constraint score may capture nonlinear effects."
    inputs = ["knowledge:gene_constraint", "target_genes"]
    params = {"weight_loeuf": -1.0, "weight_pli": 1.0, "weight_mis_z": 1.0}
    dim = 1

    def compute(self, ctx, perts, params):
        w_loeuf = float(params.get("weight_loeuf", -1.0))
        w_pli = float(params.get("weight_pli", 1.0))
        w_mis = float(params.get("weight_mis_z", 1.0))

        kc = ctx.knowledge("gene_constraint")
        if kc is None:
            return np.zeros((len(perts), ctx.n_genes, 1))

        cols = kc.get("columns", [])
        genes_tbl = kc.get("genes", {})

        def col_idx(name):
            try:
                return cols.index(name)
            except ValueError:
                return None

        i_loeuf = col_idx("oe_lof_upper")
        i_pli = col_idx("pLI")
        i_mis = col_idx("mis_z")
        if i_pli is None:
            i_pli = col_idx("pli")
        if i_mis is None:
            i_mis = col_idx("mis_z")

        # Build per-gene raw score vector over ALL genes in the constraint table.
        n = len(genes_tbl)
        raw = np.full(n, np.nan, dtype=float)
        loeuf_v = np.full(n, np.nan, dtype=float)
        pli_v = np.full(n, np.nan, dtype=float)
        mis_v = np.full(n, np.nan, dtype=float)

        for j, (sym, vals) in enumerate(genes_tbl.items()):
            if vals is None:
                continue
            try:
                if i_loeuf is not None and vals[i_loeuf] is not None:
                    loeuf_v[j] = float(vals[i_loeuf])
                if i_pli is not None and vals[i_pli] is not None:
                    pli_v[j] = float(vals[i_pli])
                if i_mis is not None and vals[i_mis] is not None:
                    mis_v[j] = float(vals[i_mis])
            except (TypeError, ValueError, IndexError):
                continue

        # Component transforms.
        with np.errstate(invalid="ignore", divide="ignore"):
            loeuf_comp = -np.log(np.clip(loeuf_v, 1e-6, None))
        pli_comp = pli_v
        mis_comp = np.abs(mis_v)

        # Impute missing with median of each component.
        def impute(arr):
            out = arr.copy()
            mask = np.isfinite(out)
            if mask.any():
                med = np.median(out[mask])
            else:
                med = 0.0
            out[~mask] = med
            return out

        loeuf_comp = impute(loeuf_comp)
        pli_comp = impute(pli_comp)
        mis_comp = impute(mis_comp)

        raw = w_loeuf * loeuf_comp + w_pli * pli_comp + w_mis * mis_comp

        # Standardize across all genes.
        mu = raw.mean()
        sd = raw.std()
        if not np.isfinite(sd) or sd < 1e-12:
            sd = 1.0
        z = (raw - mu) / sd

        # Map gene symbol -> standardized score.
        sym_to_z = {}
        for j, sym in enumerate(genes_tbl.keys()):
            sym_to_z[sym] = z[j]

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                continue
            scores = [sym_to_z[g] for g in tg if g in sym_to_z]
            if scores:
                out[i, :, 0] = float(np.mean(scores))
        return out
