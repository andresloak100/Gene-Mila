import numpy as np
from genemila.features.api import Feature, register


@register
class ProteinDomainSimilarityE743(Feature):
    name = "protein_domain_similarity_e743"
    version = 1
    description = ("For each (p,g), cosine similarity between domain/protein composition "
                   "vectors of the perturbation target p and gene g, based on protein_annotation "
                   "or gene_annotation amino-acid fractions.")
    rationale = ("Genes sharing protein domains with the target are more likely to have "
                 "correlated expression responses due to functional redundancy or common "
                 "interaction partners.")
    inputs = ["knowledge", "target_genes"]
    params = {"use_aa_fractions": True}
    dim = 1

    def _build_vectors(self, ctx, params):
        """Build a (n_genes, d) non-negative feature matrix for cosine similarity."""
        use_aa = bool(params.get("use_aa_fractions", True))

        prot = ctx.knowledge("protein_annotation")
        ann = ctx.knowledge("gene_annotation")

        # Collect protein_annotation numeric columns (excluding the gene symbol key).
        prot_cols = None
        prot_genes = None
        prot_data = None
        if prot is not None and isinstance(prot, dict):
            pgenes = prot.get("genes") or {}
            cols = prot.get("columns")
            if pgenes and cols:
                # columns may include a leading symbol column; keep numeric ones
                prot_cols = list(cols)
                prot_genes = list(pgenes.keys())
                rows = []
                for g in prot_genes:
                    vals = pgenes[g]
                    row = []
                    for v in vals:
                        try:
                            row.append(float(v) if v is not None else np.nan)
                        except (TypeError, ValueError):
                            row.append(np.nan)
                    rows.append(row)
                prot_data = np.asarray(rows, dtype=float)

        # Amino-acid fractions from gene_annotation (proxy vector).
        aa_data = None
        aa_genes = None
        if ann is not None and isinstance(ann, dict):
            agenes = ann.get("genes") or {}
            cols = ann.get("columns") or []
            if agenes and cols:
                # identify aa_* columns
                aa_idx = [i for i, c in enumerate(cols)
                          if isinstance(c, str) and c.startswith("aa_")]
                if aa_idx:
                    aa_genes = list(agenes.keys())
                    rows = []
                    for g in aa_genes:
                        vals = agenes[g]
                        row = []
                        for i in aa_idx:
                            v = vals[i] if i < len(vals) else None
                            try:
                                row.append(float(v) if v is not None else np.nan)
                            except (TypeError, ValueError):
                                row.append(np.nan)
                        rows.append(row)
                    aa_data = np.asarray(rows, dtype=float)

        # Assemble per-gene vectors aligned to ctx.genes.
        n = ctx.n_genes
        blocks = []
        if use_aa and aa_data is not None:
            mat = np.full((n, aa_data.shape[1]), np.nan, dtype=float)
            for j, g in enumerate(aa_genes):
                gi = ctx.gene_index.get(g)
                if gi is not None:
                    mat[gi] = aa_data[j]
            blocks.append(mat)
        if not use_aa and prot_data is not None:
            mat = np.full((n, prot_data.shape[1]), np.nan, dtype=float)
            for j, g in enumerate(prot_genes):
                gi = ctx.gene_index.get(g)
                if gi is not None:
                    mat[gi] = prot_data[j]
            blocks.append(mat)
        # Fall back to protein if aa requested but unavailable
        if not blocks and prot_data is not None:
            mat = np.full((n, prot_data.shape[1]), np.nan, dtype=float)
            for j, g in enumerate(prot_genes):
                gi = ctx.gene_index.get(g)
                if gi is not None:
                    mat[gi] = prot_data[j]
            blocks.append(mat)

        if not blocks:
            return None

        M = np.concatenate(blocks, axis=1)
        # Replace NaN with 0 and clamp negatives (composition-like features).
        M = np.where(np.isfinite(M), M, 0.0)
        M = np.maximum(M, 0.0)
        return M

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        M = self._build_vectors(ctx, params)
        if M is None:
            return out

        # L2-normalise rows; zero rows stay zero.
        norms = np.linalg.norm(M, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        Mn = M / norms

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # Use first target (perturbations are single-gene in this dataset).
            ti = tgt_idx[0]
            if ti < 0 or ti >= ctx.n_genes:
                continue
            sims = Mn @ Mn[ti]
            out[i, :, 0] = sims

        out = np.where(np.isfinite(out), out, 0.0)
        return out
