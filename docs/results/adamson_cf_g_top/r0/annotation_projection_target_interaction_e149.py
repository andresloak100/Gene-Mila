import numpy as np
from genemila.features.api import Feature, register


@register
class AnnotationProjectionTargetInteractionE149(Feature):
    name = "annotation_projection_target_interaction_e149"
    version = 1
    description = ("For each (p,g), product of target expression and a random projection "
                   "of standardized gene annotation features onto a low-dimensional space.")
    rationale = ("A low-dimensional random projection of gene annotation captures latent "
                 "structure; interacting it with target expression models context-dependent effects.")
    inputs = ["control_mean", "control_std", "knowledge", "target_indices"]
    params = {"n_components": 20, "seed": 149}
    dim = 1

    def _build_annotation_matrix(self, ctx):
        cached = ctx.cache.get("_e149_annot")
        if cached is not None:
            return cached

        ann = ctx.knowledge("gene_annotation")
        prot = ctx.knowledge("protein_annotation")
        cons = ctx.knowledge("gene_constraint")

        genes = ctx.genes
        n = ctx.n_genes

        # Collect annotation sub-tables keyed by gene symbol.
        tables = []
        if ann and isinstance(ann, dict) and "genes" in ann:
            tables.append((ann["genes"], ann.get("columns")))
        if prot and isinstance(prot, dict) and "genes" in prot:
            tables.append((prot["genes"], prot.get("columns")))
        if cons and isinstance(cons, dict) and "genes" in cons:
            tables.append((cons["genes"], cons.get("columns")))

        # Determine total width from first table with columns; otherwise infer.
        feat_cols = []
        for tbl, cols in tables:
            if cols is not None:
                feat_cols.append(len(cols))
            else:
                # infer from first non-empty entry
                for v in tbl.values():
                    if isinstance(v, (list, tuple)):
                        feat_cols.append(len(v))
                    break
                else:
                    feat_cols.append(0)

        total = sum(feat_cols) if feat_cols else 0
        if total == 0:
            mat = np.zeros((n, 1), dtype=float)
            ctx.cache["_e149_annot"] = mat
            return mat

        mat = np.zeros((n, total), dtype=float)
        offset = 0
        for (tbl, cols), width in zip(tables, feat_cols):
            for i, g in enumerate(genes):
                v = tbl.get(g)
                if v is None:
                    continue
                for j in range(min(width, len(v))):
                    val = v[j]
                    if val is None:
                        continue
                    try:
                        fv = float(val)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        mat[i, offset + j] = fv
            offset += width

        ctx.cache["_e149_annot"] = mat
        return mat

    def compute(self, ctx, perts, params):
        n_components = int(params.get("n_components", 20))
        seed = int(params.get("seed", 149))
        n_genes = ctx.n_genes
        n_perts = len(perts)

        ann = self._build_annotation_matrix(ctx)
        # Standardize columns (guard against zero variance).
        mu = ann.mean(axis=0)
        sd = ann.std(axis=0)
        sd_safe = np.where(sd > 1e-8, sd, 1.0)
        Z = (ann - mu) / sd_safe
        # Replace any non-finite with 0.
        Z = np.nan_to_num(Z, nan=0.0, posinf=0.0, neginf=0.0)

        rng = np.random.default_rng(seed)
        R = rng.standard_normal((Z.shape[1], n_components)) / np.sqrt(max(Z.shape[1], 1))
        proj = Z @ R  # (n_genes, n_components)

        # Target expression: use control_mean as expression proxy.
        expr = np.asarray(ctx.control_mean, dtype=float)
        expr = np.nan_to_num(expr, nan=0.0, posinf=0.0, neginf=0.0)

        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        # Cache target index sets per perturbation (targets may be multi-gene).
        for i, p in enumerate(perts):
            idxs = ctx.target_indices(p)
            if not idxs:
                continue
            # Aggregate target expression across targeted genes.
            t_expr = float(np.mean(expr[idxs])) if idxs else 0.0
            if not np.isfinite(t_expr):
                t_expr = 0.0
            # Sum projected components weighted by target expression.
            out[i, :, 0] = t_expr * proj.sum(axis=1)

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
