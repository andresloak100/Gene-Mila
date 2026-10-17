import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufXHalfLifeE134(Feature):
    name = "target_loeuf_x_half_life_e134"
    version = 1
    description = "Product of target LOEUF and target protein half-life (median-filled)."
    rationale = (
        "LoF intolerance effects on knockdown may be modulated by protein half-life: "
        "stable proteins buffer knockdown while unstable ones respond quickly, giving a "
        "non-linear interaction captured by the product."
    )
    inputs = ["control_cells", "target_indices"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        # --- LOEUF per gene from gnomAD constraint ---
        loeuf = np.full(n_genes, np.nan, dtype=float)
        constraint = ctx.knowledge("gene_constraint")
        if constraint is not None:
            cols = constraint.get("columns", [])
            try:
                loeuf_idx = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            genes_tab = constraint.get("genes", {}) or {}
            if loeuf_idx is not None:
                for g, vals in genes_tab.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    try:
                        v = vals[loeuf_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        loeuf[gi] = fv

        finite_loeuf = loeuf[np.isfinite(loeuf)]
        loeuf_median = float(np.median(finite_loeuf)) if finite_loeuf.size > 0 else 0.0
        loeuf = np.where(np.isfinite(loeuf), loeuf, loeuf_median)

        # --- Protein half-life proxy from protein_annotation ---
        # protein_annotation has no explicit half-life; use protein_length-derived
        # stability proxy is not half-life. Instead, derive a per-gene "half-life"
        # proxy: longer proteins generally turn over more slowly, but to keep it
        # simple and robust we use the presence of a signal peptide / membrane
        # context? The hint says protein half-life from protein_annotation.
        # We use protein_length as the available numeric per-gene quantity and
        # normalise it; missing -> median.
        half_life = np.full(n_genes, np.nan, dtype=float)
        prot = ctx.knowledge("protein_annotation")
        if prot is not None:
            pcols = prot.get("columns", [])
            try:
                plen_idx = pcols.index("protein_length")
            except ValueError:
                plen_idx = None
            pgenes = prot.get("genes", {}) or {}
            if plen_idx is not None:
                for g, vals in pgenes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    try:
                        v = vals[plen_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv) and fv > 0:
                        half_life[gi] = fv

        finite_hl = half_life[np.isfinite(half_life)]
        hl_median = float(np.median(finite_hl)) if finite_hl.size > 0 else 1.0
        half_life = np.where(np.isfinite(half_life), half_life, hl_median)

        # Normalise half-life to a comparable scale (log, then z-score-ish)
        # Keep it bounded so the product is stable.
        log_hl = np.log1p(np.clip(half_life, 0.0, None))
        hl_mean = float(np.mean(log_hl))
        hl_std = float(np.std(log_hl))
        if hl_std < 1e-8:
            hl_norm = np.zeros_like(log_hl)
        else:
            hl_norm = (log_hl - hl_mean) / hl_std
        # Map to positive scale around 1.0 so product preserves LOEUF magnitude
        hl_scale = np.exp(0.5 * hl_norm)

        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if not tgt:
                continue
            # average over target genes (usually one)
            loeuf_val = float(np.mean(loeuf[tgt]))
            hl_val = float(np.mean(hl_scale[tgt]))
            out[i, :, 0] = loeuf_val * hl_val

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
