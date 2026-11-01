import numpy as np
from genemila.features.api import Feature, register


@register
class ProteinLocalizationE24(Feature):
    name = "protein_localization_e24"
    version = 1
    description = ("Per-gene numeric protein subcellular localization profile from "
                   "UniProt protein_annotation: compartment flags plus a few "
                   "structural localization indicators (signal peptide, "
                   "transmembrane count, secreted/membrane).")
    rationale = ("Subcellular localization shapes how a gene product interacts with "
                 "perturbation machinery and downstream regulatory responses; "
                 "compartment membership is a fundamental property not captured by "
                 "expression alone.")
    inputs = ["protein_annotation"]
    params = {
        "compartments": [
            "nucleus",
            "mitochondrion",
            "endoplasmic_reticulum",
            "cytoplasm",
            "membrane",
            "secreted",
            "golgi",
            "lysosome",
            "peroxisome",
        ],
        "use_structural": True,
    }
    dim = 12  # up to 9 compartment flags + 3 structural indicators

    def compute(self, ctx, perts, params):
        comps = list(params.get("compartments", self.params["compartments"]))
        use_struct = bool(params.get("use_structural", True))

        n_genes = ctx.n_genes
        dim = len(comps) + (3 if use_struct else 0)
        out = np.zeros((len(perts), n_genes, dim), dtype=float)

        # Build gene -> vector once (shared across perturbations), memoised.
        cache = ctx.cache
        key = ("protein_localization_e24", tuple(comps), use_struct)
        vec = cache.get(key) if cache is not None else None
        if vec is None:
            vec = self._build_vectors(ctx, comps, use_struct)
            if cache is not None:
                cache[key] = vec

        # Same gene-level profile applies to every perturbation row.
        for i in range(len(perts)):
            out[i] = vec
        return out

    def _build_vectors(self, ctx, comps, use_struct):
        n_genes = ctx.n_genes
        dim = len(comps) + (3 if use_struct else 0)
        vec = np.zeros((n_genes, dim), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if not ann:
            return vec

        genes_tbl = ann.get("genes") or {}
        columns = ann.get("columns") or []

        # Map column name -> index
        col_idx = {c: i for i, c in enumerate(columns)}

        # Compartment column indices (may be absent; treat as zero)
        comp_cols = []
        for c in comps:
            comp_cols.append(col_idx.get(c, None))

        sp_col = col_idx.get("has_signal_peptide", None)
        tm_col = col_idx.get("n_transmembrane", None)

        for g in ctx.genes:
            row = genes_tbl.get(g)
            gi = ctx.gene_index.get(g)
            if gi is None:
                continue
            if row is None:
                continue
            k = 0
            for ci in comp_cols:
                if ci is not None and ci < len(row):
                    val = row[ci]
                    if val is not None:
                        try:
                            vec[gi, k] = 1.0 if float(val) > 0 else 0.0
                        except (TypeError, ValueError):
                            vec[gi, k] = 0.0
                k += 1
            if use_struct:
                # has_signal_peptide flag
                if sp_col is not None and sp_col < len(row) and row[sp_col] is not None:
                    try:
                        vec[gi, k] = 1.0 if float(row[sp_col]) > 0 else 0.0
                    except (TypeError, ValueError):
                        vec[gi, k] = 0.0
                # number of transmembrane segments (clipped)
                if tm_col is not None and tm_col < len(row) and row[tm_col] is not None:
                    try:
                        vec[gi, k + 1] = float(row[tm_col])
                    except (TypeError, ValueError):
                        vec[gi, k + 1] = 0.0
                # ER-targeted proxy: signal peptide or transmembrane
                vec[gi, k + 2] = 1.0 if (vec[gi, k] > 0 or vec[gi, k + 1] > 0) else 0.0

        # Replace any non-finite values defensively
        vec = np.nan_to_num(vec, nan=0.0, posinf=0.0, neginf=0.0)
        return vec
