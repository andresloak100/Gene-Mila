import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneSharedDomainCountE694(Feature):
    name = "target_gene_shared_domain_count_e694"
    version = 1
    description = ("Number of shared InterPro/Pfam protein domains between the perturbation "
                   "target gene and gene g, using protein_annotation domain/compartment features.")
    rationale = ("Protein domains reflect functional modules; shared domains often indicate "
                 "participation in similar complexes or pathways, which could mediate "
                 "coordinated responses.")
    inputs = ["protein_annotation", "target_genes"]
    params = {"min_domain_frequency": 2}
    dim = 1

    def _build_domain_matrix(self, ctx, params):
        # Build a binary (n_genes x n_features) matrix from protein_annotation flags,
        # using the annotation columns that describe protein localization/domain-like
        # properties. Restrict to features present in >= min_domain_frequency genes.
        key = ("domain_matrix", float(params.get("min_domain_frequency", 2)))
        cache = ctx.cache
        if key in cache:
            return cache[key]

        n_genes = ctx.n_genes
        ann = ctx.knowledge("protein_annotation")
        if not ann:
            mat = np.zeros((n_genes, 0), dtype=np.float32)
            cache[key] = mat
            return mat

        genes_tbl = ann.get("genes", {}) or {}
        columns = ann.get("columns", []) or []

        # Identify annotation columns that are 0/1 flags (domain/compartment-like).
        # We use all numeric columns that are predominantly binary, excluding
        # continuous length-type columns.
        exclude_substr = ("length", "signal_peptide_length")
        candidate_cols = []
        for j, col in enumerate(columns):
            lc = str(col).lower()
            if any(s in lc for s in exclude_substr):
                continue
            candidate_cols.append(j)

        rows = []
        for g in ctx.genes:
            vals = genes_tbl.get(g)
            if vals is None:
                rows.append(None)
                continue
            rows.append(vals)

        # Determine which candidate columns are binary across available genes.
        arr_parts = []
        for j in candidate_cols:
            col_vals = []
            ok = True
            for v in rows:
                if v is None:
                    continue
                try:
                    x = v[j]
                except Exception:
                    ok = False
                    break
                if x is None:
                    continue
                try:
                    fx = float(x)
                except Exception:
                    ok = False
                    break
                if not np.isfinite(fx):
                    continue
                col_vals.append(fx)
            if not ok or len(col_vals) == 0:
                continue
            uniq = np.unique(np.array(col_vals, dtype=np.float64))
            if uniq.size <= 2 and np.all((uniq == 0.0) | (uniq == 1.0)):
                arr_parts.append(j)

        if not arr_parts:
            mat = np.zeros((n_genes, 0), dtype=np.float32)
            cache[key] = mat
            return mat

        mat = np.zeros((n_genes, len(arr_parts)), dtype=np.float32)
        for i, v in enumerate(rows):
            if v is None:
                continue
            for k, j in enumerate(arr_parts):
                try:
                    x = v[j]
                except Exception:
                    continue
                if x is None:
                    continue
                try:
                    fx = float(x)
                except Exception:
                    continue
                if np.isfinite(fx) and fx > 0.5:
                    mat[i, k] = 1.0

        # Filter by minimum domain frequency (number of genes carrying the feature).
        min_freq = float(params.get("min_domain_frequency", 2))
        freq = mat.sum(axis=0)
        keep = freq >= max(1.0, min_freq)
        mat = mat[:, keep]

        cache[key] = mat
        return mat

    def compute(self, ctx, perts, params):
        n = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n, n_genes, 1), dtype=np.float32)

        mat = self._build_domain_matrix(ctx, params)
        if mat.shape[1] == 0:
            return out

        gene_index = ctx.gene_index

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            tgt_idx = [gene_index[t] for t in targets if t in gene_index]
            if not tgt_idx:
                continue
            # Shared-domain count: for each gene g, number of domain features that
            # are active in both g and any target gene. Use max over target genes.
            tgt_dom = mat[tgt_idx, :]  # (n_t, n_dom)
            # Intersection counts with each target: (n_genes, n_dom) & (n_t, n_dom)
            # shared[g, t] = dot(mat[g], tgt_dom[t])
            shared = mat @ tgt_dom.T  # (n_genes, n_t)
            out[i, :, 0] = shared.max(axis=1)

        out[~np.isfinite(out)] = 0.0
        return out
