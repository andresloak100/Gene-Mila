import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPromoterCpgDensityE201(Feature):
    name = "target_promoter_cpg_density_e201"
    version = 1
    description = (
        "Average promoter CpG density (CpG dinucleotides per bp, approximated from "
        "cpg_oe_promoter and promoter GC content) of a perturbation's target genes, "
        "broadcast to all genes."
    )
    rationale = (
        "CpG islands mark open, active promoters; targets with denser promoter CpGs "
        "may be more accessible and thus more responsive to CRISPRa, producing larger "
        "downstream expression changes."
    )
    inputs = ["control_cells"]
    params = {}
    dim = 1

    def _gene_cpg_density(self, ctx):
        cache = ctx.cache
        key = "_e201_gene_cpg_density"
        if key in cache:
            return cache[key]

        dens = np.zeros(ctx.n_genes, dtype=np.float64)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_tab = ann.get("genes", {}) or {}
            cols = ann.get("columns", []) or []
            col_idx = {c: i for i, c in enumerate(cols)}
            i_oe = col_idx.get("cpg_oe_promoter")
            i_gc = col_idx.get("gc_promoter")
            for gi, g in enumerate(ctx.genes):
                vals = genes_tab.get(g)
                if vals is None:
                    continue
                oe = None
                gc = None
                if i_oe is not None and i_oe < len(vals):
                    v = vals[i_oe]
                    if v is not None:
                        try:
                            oe = float(v)
                        except (TypeError, ValueError):
                            oe = None
                if i_gc is not None and i_gc < len(vals):
                    v = vals[i_gc]
                    if v is not None:
                        try:
                            gc = float(v)
                        except (TypeError, ValueError):
                            gc = None
                if oe is None and gc is None:
                    continue
                # Expected CpG observed/expected ratio. If oe available, use it;
                # otherwise approximate from GC content: CpG O/E ~ (GC^2)/(0.5*GC) style.
                if oe is None:
                    # Approximate CpG density from GC content using standard CpG O/E
                    # formula: E[CpG] under independence ~ p(C)p(G) = (GC/2)^2*2 = GC^2/2.
                    # O/E ratio ~ 1 at GC=0.5; use simple proxy.
                    gcf = max(min(gc, 1.0), 0.0)
                    oe = 2.0 * gcf * gcf + 1e-6
                # Convert O/E ratio to approximate density (CpGs per bp).
                # Baseline CpG frequency in human genome ~ 1/100 bp; O/E ~1 => 0.01.
                # Scale reasonably: density = oe * 0.01 * (0.5 + gc or 0.5)
                gcf = 0.5 if gc is None else max(min(gc, 1.0), 0.0)
                dens[gi] = oe * 0.01 * (0.5 + gcf)

        cache[key] = dens
        return dens

    def compute(self, ctx, perts, params):
        dens = self._gene_cpg_density(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=np.float64)
        for i, p in enumerate(perts):
            idx = ctx.target_indices(p)
            if not idx:
                continue
            val = float(np.mean(dens[np.asarray(idx, dtype=int)]))
            out[i, :, 0] = val
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
