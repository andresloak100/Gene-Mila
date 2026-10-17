import numpy as np
from genemila.features.api import Feature, register


@register
class TargetCompartmentXGeneAnnotation(Feature):
    name = "target_compartment_x_gene_annotation_e333"
    version = 1
    description = ("Indicator that the perturbation target's protein localizes to a chosen "
                   "UniProt compartment, multiplied by gene g's membership in that compartment "
                   "(and a membrane/secreted annotation term).")
    rationale = ("Perturbing targets in specific functional/localization categories produces "
                 "distinct signatures; the effect on a downstream gene g may depend jointly on "
                 "the target's compartment and g's own compartment annotation.")
    inputs = ["protein_annotation"]
    params = {"compartment": "membrane"}
    dim = 1

    _COMPARTMENTS = [
        "secreted", "membrane", "endoplasmic_reticulum", "golgi",
        "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
    ]

    def _build_matrix(self, ctx, comp):
        """Return (n_genes,) float array of compartment flags, and membrane/secreted term."""
        ann = ctx.knowledge("protein_annotation")
        n = ctx.n_genes
        flags = np.zeros(n, dtype=float)
        memsec = np.zeros(n, dtype=float)
        if ann is None:
            return flags, memsec
        columns = ann.get("columns", [])
        genes = ann.get("genes", {})
        try:
            ci = columns.index(comp)
        except ValueError:
            ci = -1
        try:
            mi = columns.index("membrane")
        except ValueError:
            mi = -1
        try:
            si = columns.index("secreted")
        except ValueError:
            si = -1
        for g in ctx.genes:
            row = genes.get(g)
            if row is None:
                continue
            gi = ctx.gene_index[g]
            if ci >= 0 and ci < len(row) and row[ci] is not None:
                try:
                    flags[gi] = float(row[ci])
                except (TypeError, ValueError):
                    pass
            m = 0.0
            s = 0.0
            if mi >= 0 and mi < len(row) and row[mi] is not None:
                try:
                    m = float(row[mi])
                except (TypeError, ValueError):
                    m = 0.0
            if si >= 0 and si < len(row) and row[si] is not None:
                try:
                    s = float(row[si])
                except (TypeError, ValueError):
                    s = 0.0
            memsec[gi] = max(m, s)
        return flags, memsec

    def compute(self, ctx, perts, params):
        comp = params.get("compartment", "membrane")
        if comp not in self._COMPARTMENTS:
            comp = "membrane"

        cache = ctx.cache
        key = ("e333", comp)
        if key not in cache:
            cache[key] = self._build_matrix(ctx, comp)
        gene_flags, gene_memsec = cache[key]

        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            tgt_flag = 0.0
            for ti in tgt_idx:
                if 0 <= ti < n:
                    tgt_flag = max(tgt_flag, gene_flags[ti])
            if tgt_flag <= 0.0:
                continue
            # interaction: target in compartment x gene g in same compartment
            # plus a membrane/secreted annotation term for gene g
            out[i, :, 0] = gene_flags + 0.5 * gene_memsec

        return out
