import numpy as np
from genemila.features.api import Feature, register

AA_COLS = [f"aa_{c}" for c in "ACDEFGHIKLMNPQRSTVWY"]


@register
class TargetAaFractionSimilarity(Feature):
    name = "target_aa_fraction_similarity_e341"
    version = 1
    description = "Mean cosine similarity between gene g's amino-acid fraction vector and each target of p."
    rationale = "Proteins with similar amino acid composition may share functional domains, making g more likely co-regulated with p's targets."
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        ann = ctx.knowledge("gene_annotation")
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1))

        if ann is None:
            return out
        genes_tbl = ann.get("genes", {})
        columns = ann.get("columns", [])
        # map aa column names to indices within the per-gene value list
        col_idx = {}
        for i, c in enumerate(columns):
            if c in AA_COLS:
                col_idx[c] = i
        if not col_idx:
            return out
        aa_order = [c for c in AA_COLS if c in col_idx]
        if not aa_order:
            return out
        idx_list = [col_idx[c] for c in aa_order]

        # build per-gene aa matrix (n_genes x n_aa), NaN for missing
        aa_mat = np.full((n, len(aa_order)), np.nan, dtype=float)
        for gi, g in enumerate(ctx.genes):
            vals = genes_tbl.get(g)
            if vals is None:
                continue
            row = []
            ok = True
            for j in idx_list:
                if j >= len(vals) or vals[j] is None:
                    ok = False
                    break
                row.append(float(vals[j]))
            if ok:
                aa_mat[gi] = row

        # normalise rows for cosine similarity
        norms = np.linalg.norm(aa_mat, axis=1)
        safe = np.where(norms > 0, norms, 1.0)
        unit = aa_mat / safe[:, None]
        valid = np.isfinite(aa_mat).all(axis=1) & (norms > 0)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            tgt_idx = [t for t in tgt_idx if 0 <= t < n]
            if not tgt_idx:
                continue
            tgt_unit = unit[tgt_idx]  # (T, n_aa)
            tgt_valid = valid[tgt_idx]
            # similarity of every gene to each target
            sims = unit @ tgt_unit.T  # (n, T)
            # mask invalid
            mask_g = valid[:, None] & tgt_valid[None, :]
            sims = np.where(mask_g, sims, 0.0)
            counts = mask_g.sum(axis=1)
            sums = sims.sum(axis=1)
            res = np.where(counts > 0, sums / np.maximum(counts, 1), 0.0)
            out[i, :, 0] = res

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
