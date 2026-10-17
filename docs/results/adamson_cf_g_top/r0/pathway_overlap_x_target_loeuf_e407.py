import numpy as np
from genemila.features.api import Feature, register


@register
class PathwayOverlapXTargetLoeuf(Feature):
    name = "pathway_overlap_x_target_loeuf_e407"
    version = 1
    description = (
        "Product of pathway overlap score (fraction of gene sets containing the "
        "target that also contain gene g) and (1 - LOEUF_target) from gnomAD LoF "
        "constraint."
    )
    rationale = (
        "Pathway co-membership indicates functional relatedness; weighting by "
        "target essentiality (low LOEUF) captures genes strongly affected by "
        "perturbation of essential pathway members."
    )
    inputs = ["knowledge", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # --- Load gene sets (knowledge) ---
        gs = ctx.knowledge("gene_sets")
        if gs is None:
            gs = {}
        # Normalise to a list of (name, set_of_genes)
        if isinstance(gs, dict):
            sets_items = list(gs.items())
        else:
            sets_items = list(enumerate(gs))

        # Build per-gene membership as list of set indices, restricted to measured genes
        gene_sets_of_gene = [[] for _ in range(n_genes)]
        set_members = []  # list of sets of gene indices
        for si, (_, members) in enumerate(sets_items):
            idxs = []
            if isinstance(members, (list, tuple, set)):
                for g in members:
                    gi = ctx.gene_index.get(g)
                    if gi is not None:
                        idxs.append(gi)
            if not idxs:
                set_members.append(None)
                continue
            idx_set = set(idxs)
            set_members.append(idx_set)
            for gi in idx_set:
                gene_sets_of_gene[gi].append(si)

        # --- Load LOEUF constraint ---
        lc = ctx.knowledge("gene_constraint")
        loeuf = np.full(n_genes, np.nan, dtype=float)
        if lc is not None:
            genes_tbl = lc.get("genes", {})
            columns = lc.get("columns", [])
            try:
                loeuf_col = columns.index("oe_lof_upper")
            except ValueError:
                loeuf_col = None
            if loeuf_col is not None:
                for g, vals in genes_tbl.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    try:
                        v = vals[loeuf_col]
                    except (IndexError, TypeError):
                        continue
                    if v is not None:
                        try:
                            loeuf[gi] = float(v)
                        except (TypeError, ValueError):
                            pass

        # Fill missing LOEUF with median of observed (neutral-ish imputation)
        observed = np.isfinite(loeuf)
        if observed.any():
            med = float(np.nanmedian(loeuf[observed]))
        else:
            med = 1.0
        loeuf_filled = np.where(np.isfinite(loeuf), loeuf, med)
        # Clip to [0, 1] for (1 - LOEUF) scaling; LOEUF can exceed 1
        loeuf_clipped = np.clip(loeuf_filled, 0.0, 1.0)
        essentiality = 1.0 - loeuf_clipped  # (1 - LOEUF_target)

        for i, p in enumerate(perts):
            # Target gene indices for this perturbation
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue

            # Collect sets containing any target gene
            tgt_sets = set()
            for tg in tgt_idx:
                tgt_sets.update(gene_sets_of_gene[tg])

            if not tgt_sets:
                continue
            n_tgt_sets = len(tgt_sets)

            # Compute overlap fraction for each gene: |tgt_sets ∩ gene_sets(g)| / n_tgt_sets
            overlap = np.zeros(n_genes, dtype=float)
            for g in range(n_genes):
                gs_list = gene_sets_of_gene[g]
                if not gs_list:
                    continue
                cnt = 0
                for si in gs_list:
                    if si in tgt_sets:
                        cnt += 1
                if cnt:
                    overlap[g] = cnt / n_tgt_sets

            # Target essentiality: max over target genes
            ess = float(np.max(essentiality[tgt_idx]))
            out[i, :, 0] = overlap * ess

        # Ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
