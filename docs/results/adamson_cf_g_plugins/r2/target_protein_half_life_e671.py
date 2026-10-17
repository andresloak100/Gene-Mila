import numpy as np
from genemila.features.api import Feature, register


@register
class TargetProteinHalfLifeE671(Feature):
    name = "target_protein_half_life_e671"
    version = 1
    description = "Half-life of the target protein in hours, broadcast to all genes for a perturbation."
    rationale = ("Targets with shorter half-lives are depleted more rapidly and may produce stronger "
                 "downstream effects. No measured half-life table is available in the provided knowledge, "
                 "so a proxy is inferred from protein_annotation features via a fixed monotone formula.")
    inputs = ["protein_annotation", "target_genes"]
    params = {"source": "schwanhausser"}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        # Build per-gene half-life proxy from protein_annotation (cached).
        if "half_life_proxy" not in ctx.cache:
            pa = ctx.knowledge("protein_annotation")
            hl = np.full(ctx.n_genes, np.nan, dtype=float)
            if pa is not None:
                cols = pa.get("columns", [])
                genes_tbl = pa.get("genes", {}) or {}
                # locate relevant columns
                def col_idx(name):
                    try:
                        return cols.index(name)
                    except ValueError:
                        return None
                i_len = col_idx("protein_length")
                i_sp = col_idx("has_signal_peptide")
                i_tm = col_idx("n_transmembrane")
                i_mem = col_idx("membrane")
                i_secreted = col_idx("secreted")
                for g, vals in genes_tbl.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    try:
                        plen = float(vals[i_len]) if i_len is not None and vals[i_len] is not None else np.nan
                        sp = float(vals[i_sp]) if i_sp is not None and vals[i_sp] is not None else 0.0
                        tm = float(vals[i_tm]) if i_tm is not None and vals[i_tm] is not None else 0.0
                        mem = float(vals[i_mem]) if i_mem is not None and vals[i_mem] is not None else 0.0
                        sec = float(vals[i_secreted]) if i_secreted is not None and vals[i_secreted] is not None else 0.0
                    except (TypeError, IndexError):
                        continue
                    if not np.isfinite(plen):
                        plen = 400.0
                    # Simple proxy: long, secreted/membrane proteins tend to be more stable.
                    # Base half-life ~ log-length scaled, plus stability bonuses.
                    base = 6.0 + 4.0 * np.log1p(max(plen, 1.0)) / np.log1p(1000.0)
                    bonus = 4.0 * (1.0 if (sp > 0 or tm > 0 or mem > 0 or sec > 0) else 0.0)
                    bonus += 1.0 * min(tm, 7.0)
                    hl[gi] = base + bonus
            # fill missing with median of known, else a default
            finite = np.isfinite(hl)
            if finite.any():
                med = float(np.median(hl[finite]))
            else:
                med = 10.0
            hl[~finite] = med
            # clip to a plausible range
            hl = np.clip(hl, 0.5, 60.0)
            ctx.cache["half_life_proxy"] = hl

        hl = ctx.cache["half_life_proxy"]

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if tgenes:
                idxs = [ctx.gene_index[g] for g in tgenes if g in ctx.gene_index]
                if idxs:
                    val = float(np.mean(hl[idxs]))
                else:
                    val = float(np.median(hl))
            else:
                val = float(np.median(hl))
            out[i, :, 0] = val

        out[~np.isfinite(out)] = 0.0
        return out
