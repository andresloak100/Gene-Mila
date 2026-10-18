import numpy as np
from genemila.features.api import Feature, register


@register
class ProteinCompartmentE22(Feature):
    name = "protein_compartment_e22"
    version = 1
    description = (
        "Binary indicators for whether gene g's protein is localized to "
        "mitochondrion, nucleus, or endoplasmic reticulum (from protein_annotation)."
    )
    rationale = (
        "Perturbations affecting protein synthesis or organelle function may have "
        "differential effects on genes whose products localize to those organelles."
    )
    inputs = ["protein_annotation"]
    params = {"compartments": "mitochondrion,nucleus,endoplasmic_reticulum"}
    dim = 3

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, self.dim), dtype=float)

        comp_param = params.get("compartments", self.params["compartments"])
        if isinstance(comp_param, str):
            comps = [c.strip() for c in comp_param.split(",") if c.strip()]
        else:
            comps = list(comp_param)
        if not comps:
            comps = ["mitochondrion", "nucleus", "endoplasmic_reticulum"]

        col_map = {
            "mitochondrion": "mitochondrion",
            "nucleus": "nucleus",
            "endoplasmic_reticulum": "endoplasmic_reticulum",
            "er": "endoplasmic_reticulum",
            "secreted": "secreted",
            "membrane": "membrane",
            "golgi": "golgi",
            "cytoplasm": "cytoplasm",
            "lysosome": "lysosome",
            "peroxisome": "peroxisome",
        }

        gene_feat = np.zeros((n, self.dim), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if ann is not None:
            columns = ann.get("columns", []) if isinstance(ann, dict) else []
            genes_tbl = ann.get("genes", {}) if isinstance(ann, dict) else {}
            col_index = {c: i for i, c in enumerate(columns)}
            for d, comp in enumerate(comps):
                if d >= self.dim:
                    break
                colname = col_map.get(comp, comp)
                ci = col_index.get(colname, None)
                if ci is None:
                    continue
                for g, vals in genes_tbl.items():
                    gi = ctx.gene_index.get(g, None)
                    if gi is None or vals is None:
                        continue
                    if ci < len(vals) and vals[ci] is not None:
                        try:
                            v = float(vals[ci])
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(v) and v > 0:
                            gene_feat[gi, d] = 1.0

        out[:] = gene_feat[np.newaxis, :, :]
        return out
