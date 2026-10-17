import numpy as np
from genemila.features.api import Feature, register


@register
class TargetCompartmentFlagE252(Feature):
    name = "target_compartment_flag_e252"
    version = 1
    description = (
        "Multi-hot protein-compartment flags of the perturbation target gene, "
        "broadcast to every gene column."
    )
    rationale = (
        "Protein localization of the target determines how a perturbation "
        "propagates (nuclear targets -> transcriptional programs, membrane/ER "
        "targets -> signaling/secretion), so the target's compartment "
        "annotation is a perturbation-level modulator of the response."
    )
    inputs = ["protein_annotation", "targets"]
    params = {
        "compartments": (
            "nucleus, membrane, endoplasmic_reticulum, golgi, "
            "mitochondrion, secreted, cytoplasm, lysosome, peroxisome"
        )
    }
    dim = 9

    def _compartment_columns(self, ctx, params):
        """Resolve compartment names to column indices in protein_annotation."""
        ann = ctx.knowledge("protein_annotation")
        cols = []
        names = [c.strip() for c in params.get("compartments", "").split(",") if c.strip()]
        if ann is not None:
            colnames = ann.get("columns", [])
            idx = {c: i for i, c in enumerate(colnames)}
            for n in names:
                cols.append((n, idx.get(n, None)))
        else:
            cols = [(n, None) for n in names]
        return ann, cols

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        ann, cols = self._compartment_columns(ctx, params)

        # Pre-fetch annotation table (genes dict) and column positions.
        ann_genes = {}
        if ann is not None:
            ann_genes = ann.get("genes", {}) or {}

        out = np.zeros((n_perts, n_genes, self.dim), dtype=float)

        # Cache per-target compartment vector.
        target_vec_cache = {}

        def target_vec(target_gene):
            if target_gene in target_vec_cache:
                return target_vec_cache[target_gene]
            vec = np.zeros(self.dim, dtype=float)
            row = ann_genes.get(target_gene, None)
            if row is not None:
                for j, (name, ci) in enumerate(cols[: self.dim]):
                    if ci is None or ci >= len(row):
                        continue
                    val = row[ci]
                    if val is None:
                        continue
                    try:
                        v = float(val)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(v) and v > 0:
                        vec[j] = 1.0
            target_vec_cache[target_gene] = vec
            return vec

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                continue
            # Use the first annotated target gene (single-gene targets expected).
            vec = target_vec(tg[0])
            if np.any(vec):
                out[i, :, :] = vec[None, :]

        # Ensure finite values.
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
