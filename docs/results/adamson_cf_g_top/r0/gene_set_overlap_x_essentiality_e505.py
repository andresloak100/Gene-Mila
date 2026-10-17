import numpy as np
from genemila.features.api import Feature, register

@register
class GeneSetOverlapXEssentiality(Feature):
    name = "gene_set_overlap_x_essentiality_e505"
    version = 1
    description = "Product of gene_set_overlap_e20 and (1 - LOEUF_target)."
    rationale = ("Essential genes tend to be in more critical pathways; perturbing them may "
                 "affect co-pathway genes more strongly, so the interaction of gene-set overlap "
                 "with target essentiality should be more predictive.")
    inputs = ["knowledge", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        # --- Build gene set membership matrix (genes x sets) from knowledge ---
        gs = ctx.knowledge("gene_sets")
        if gs is None:
            gs = {}
        # gene -> list of set indices
        gene_sets_map = {}
        set_list = list(gs.items())
        for sidx, (sname, members) in enumerate(set_list):
            if not isinstance(members, (list, tuple)):
                continue
            for g in members:
                gi = ctx.gene_index.get(g)
                if gi is not None:
                    gene_sets_map.setdefault(gi, []).append(sidx)

        n_sets = len(set_list)
        # membership matrix (n_genes, n_sets) as float, built sparsely
        M = np.zeros((ctx.n_genes, n_sets), dtype=np.float32)
        for gi, slist in gene_sets_map.items():
            for s in slist:
                M[gi, s] = 1.0

        # --- LOEUF per gene from gene_constraint ---
        loeuf = np.full(ctx.n_genes, np.nan, dtype=np.float64)
        gc = ctx.knowledge("gene_constraint")
        if gc is not None:
            cols = gc.get("columns", [])
            try:
                loeuf_col = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_col = None
            genes_tbl = gc.get("genes", {})
            if loeuf_col is not None:
                for g, vals in genes_tbl.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    try:
                        v = vals[loeuf_col]
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

        # essentiality per gene = 1 - LOEUF (clipped to [0,1] where defined)
        ess = np.where(np.isfinite(loeuf), 1.0 - loeuf, np.nan)
        ess = np.clip(ess, 0.0, 1.0)
        # fill missing with median of defined (or 0.5 fallback)
        defined = np.isfinite(ess)
        if defined.any():
            fill = float(np.median(ess[defined]))
        else:
            fill = 0.5
        ess_filled = np.where(defined, ess, fill)

        # Cache M in ctx.cache for reuse
        ctx.cache["_gso_M"] = M

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            # target essentiality
            tg = ctx.target_genes(p)
            t_ess = fill
            seen = False
            acc = []
            for g in tg:
                gi = ctx.gene_index.get(g)
                if gi is not None:
                    acc.append(ess_filled[gi])
                    seen = True
            if seen and acc:
                t_ess = float(np.mean(acc))

            # gene set overlap: for target sets, count overlap with gene g's sets
            target_sets = set()
            for g in tg:
                gi = ctx.gene_index.get(g)
                if gi is not None:
                    target_sets.update(gene_sets_map.get(gi, []))
            if target_sets:
                ts = np.array(sorted(target_sets), dtype=np.int64)
                # overlap counts: M[:, ts] @ ones
                overlap = M[:, ts].sum(axis=1)
            else:
                overlap = np.zeros(ctx.n_genes, dtype=np.float32)

            out[i, :, 0] = overlap.astype(np.float64) * t_ess

        # ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
