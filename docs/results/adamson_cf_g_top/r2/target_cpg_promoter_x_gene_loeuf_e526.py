import numpy as np
from genemila.features.api import Feature, register


@register
class TargetCpgPromoterXGeneLoeuf(Feature):
    name = "target_cpg_promoter_x_gene_loeuf_e526"
    version = 1
    description = "Product of target gene's cpg_oe_promoter and gene g's LOEUF."
    rationale = ("CpG promoters mark broadly expressed, essential genes; perturbing such "
                 "targets may disproportionately affect LoF-intolerant (low LOEUF) genes.")
    inputs = ["control_cells"]
    params = {}
    dim = 1

    def _build_vectors(self, ctx):
        # cpg_oe_promoter per gene from gene_annotation
        cpg = np.zeros(ctx.n_genes, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_ann = ann.get("genes", {})
            cols = ann.get("columns", [])
            try:
                cpg_idx = cols.index("cpg_oe_promoter")
            except ValueError:
                cpg_idx = None
            if cpg_idx is not None:
                for g, vals in genes_ann.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    v = vals[cpg_idx]
                    if v is not None:
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            cpg[gi] = fv

        # LOEUF per gene from gene_constraint
        loeuf = np.zeros(ctx.n_genes, dtype=float)
        con = ctx.knowledge("gene_constraint")
        if con is not None:
            genes_con = con.get("genes", {})
            cols = con.get("columns", [])
            try:
                l_idx = cols.index("oe_lof_upper")
            except ValueError:
                l_idx = None
            if l_idx is not None:
                for g, vals in genes_con.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    v = vals[l_idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        loeuf[gi] = fv

        return cpg, loeuf

    def compute(self, ctx, perts, params):
        cpg, loeuf = self._build_vectors(ctx)
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            t_cpg = cpg[tgt_idx[0]]
            out[i, :, 0] = t_cpg * loeuf
        return out
