import numpy as np
from genemila.features.api import Feature, register


@register
class AminoAcidCompositionE68(Feature):
    name = "amino_acid_composition_e68"
    version = 1
    description = (
        "Per-gene summary statistics of protein amino-acid composition: "
        "hydrophobic, charged, aromatic and small residue fractions."
    )
    rationale = (
        "Protein stability and degradation rates depend on amino-acid composition, "
        "which can affect how much a protein's level changes upon perturbation."
    )
    inputs = ["gene_annotation"]
    params = {"groups": "hydrophobic,charged,aromatic,small"}
    dim = 4

    _GROUP_DEFS = {
        "hydrophobic": ["A", "V", "I", "L", "M", "F", "W"],
        "charged": ["R", "K", "D", "E"],
        "aromatic": ["F", "W", "Y"],
        "small": ["G", "A", "S"],
    }

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        out = np.zeros((n_perts, ctx.n_genes, self.dim), dtype=float)

        groups_str = params.get("groups", self.params["groups"])
        if isinstance(groups_str, str):
            groups = [g.strip() for g in groups_str.split(",") if g.strip()]
        else:
            groups = list(groups_str)
        if not groups:
            groups = list(self._GROUP_DEFS.keys())

        ann = ctx.knowledge("gene_annotation")
        if not ann or "genes" not in ann or "columns" not in ann:
            return out

        cols = ann["columns"]
        col_index = {c: i for i, c in enumerate(cols)}
        gene_table = ann["genes"]

        # Precompute per-group column index lists
        group_cols = []
        for g in groups:
            aas = self._GROUP_DEFS.get(g.lower(), [])
            idxs = [col_index["aa_" + a] for a in aas if ("aa_" + a) in col_index]
            group_cols.append(idxs)

        # Build per-gene composition matrix (n_genes x n_groups) once
        n_groups = len(groups)
        comp = np.zeros((ctx.n_genes, n_groups), dtype=float)
        for gi, gene in enumerate(ctx.genes):
            row = gene_table.get(gene)
            if row is None:
                continue
            for k, idxs in enumerate(group_cols):
                if not idxs:
                    continue
                s = 0.0
                for ci in idxs:
                    v = row[ci]
                    if v is not None:
                        try:
                            s += float(v)
                        except (TypeError, ValueError):
                            pass
                comp[gi, k] = s

        # Same composition for every perturbation row (gene-level feature)
        for i in range(n_perts):
            out[i, :, :] = comp

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
