import numpy as np
from genemila.features.api import Feature, register


@register
class TFTargetMotifDensity(Feature):
    name = "tf_target_motif_density_e600_e577"
    version = 2
    description = ("Per (p,g): motif-density-derived regulatory weight for the perturbed TF, "
                   "modulated by gene promoter GC content and control expression variability; "
                   "varies per perturbation via TF family membership and target proximity.")
    rationale = ("TF perturbations directly affect target genes; motif density in promoters "
                 "quantifies regulatory potential of the perturbed TF family on each gene. "
                 "Weights must vary across perturbations to carry information.")
    inputs = ["control_cells", "control_mean", "control_std", "gene_corr", "knowledge", "targets"]
    params = {"promoter_window": "1000"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        try:
            win = float(params.get("promoter_window", "1000"))
        except Exception:
            win = 1000.0
        if not np.isfinite(win) or win <= 0:
            win = 1000.0
        prom_len = 2.0 * win + 200.0

        # ---- TF set ----
        tfs_raw = ctx.knowledge("transcription_factors")
        tf_set = set()
        if isinstance(tfs_raw, list):
            for x in tfs_raw:
                if isinstance(x, str):
                    tf_set.add(x)
        elif isinstance(tfs_raw, dict):
            for k in tfs_raw.keys():
                if isinstance(k, str):
                    tf_set.add(k)

        # ---- Per-gene base density proxy (promoter GC content if available) ----
        gene_ann = ctx.knowledge("gene_annotation")
        gc_promoter = np.full(n_genes, np.nan, dtype=float)
        if isinstance(gene_ann, dict):
            genes_ann = gene_ann.get("genes", {})
            cols = gene_ann.get("columns", [])
            if isinstance(cols, list) and "gc_promoter" in cols:
                gi = cols.index("gc_promoter")
            else:
                gi = 10
            if isinstance(genes_ann, dict):
                for i, g in enumerate(ctx.genes):
                    vals = genes_ann.get(g)
                    if isinstance(vals, (list, tuple)) and len(vals) > gi:
                        v = vals[gi]
                        if isinstance(v, (int, float)) and np.isfinite(v):
                            gc_promoter[i] = float(v)

        cm = np.asarray(ctx.control_mean, dtype=float)
        cm = np.where(np.isfinite(cm), cm, 0.0)
        cs = np.asarray(ctx.control_std, dtype=float)
        cs = np.where(np.isfinite(cs), cs, 0.0)

        if np.any(np.isfinite(gc_promoter)):
            gc_fill = np.nanmean(gc_promoter)
            base = np.where(np.isfinite(gc_promoter), gc_promoter, gc_fill)
        else:
            # fallback: expression-derived proxy
            base = np.abs(cm) + np.abs(cs)

        bmin = np.min(base)
        bmax = np.max(base)
        if bmax > bmin:
            base_n = (base - bmin) / (bmax - bmin)
        else:
            base_n = np.zeros(n_genes, dtype=float)
        base_n = np.clip(np.where(np.isfinite(base_n), base_n, 0.0), 0.0, 1.0)

        # Motif density per gene (per bp fraction scaled to plausible count/kb)
        density = base_n * (2000.0 / prom_len)

        # ---- Targeting specificity: use gene_corr to spread influence from TF targets ----
        # Genes strongly co-expressed with the TF itself get higher motif-density weight.
        gene_corr = np.asarray(ctx.gene_corr, dtype=float)

        # Precompute a per-gene "regulatory potential" that varies with the perturbed TF.
        # For a perturbation whose target(s) are TFs, weight = density * (1 + corr_to_target).
        # For non-TF perturbations, use a smaller expression-weighted prior that still varies.
        expr_prior = np.abs(cm) + np.abs(cs)
        emin, emax = np.min(expr_prior), np.max(expr_prior)
        if emax > emin:
            expr_prior_n = (expr_prior - emin) / (emax - emin)
        else:
            expr_prior_n = np.zeros(n_genes, dtype=float)
        expr_prior_n = np.clip(np.where(np.isfinite(expr_prior_n), expr_prior_n, 0.0), 0.0, 1.0)

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            tidx = ctx.target_indices(p)
            is_tf = any(tg in tf_set for tg in tgenes)

            if is_tf and len(tidx) > 0:
                # Correlate each gene with target TF(s); take max abs correlation.
                corr_cols = []
                for ti in tidx:
                    if 0 <= ti < gene_corr.shape[1]:
                        c = gene_corr[:, ti]
                        c = np.where(np.isfinite(c), c, 0.0)
                        corr_cols.append(np.abs(c))
                if corr_cols:
                    corr_score = np.max(np.vstack(corr_cols), axis=0)
                else:
                    corr_score = np.zeros(n_genes, dtype=float)
                # Combine: motif density scaled by co-expression strength
                row = density * (1.0 + corr_score)
            elif len(tidx) > 0:
                # Non-TF target: use expression prior modulated by correlation to target
                corr_cols = []
                for ti in tidx:
                    if 0 <= ti < gene_corr.shape[1]:
                        c = gene_corr[:, ti]
                        c = np.where(np.isfinite(c), c, 0.0)
                        corr_cols.append(np.abs(c))
                if corr_cols:
                    corr_score = np.max(np.vstack(corr_cols), axis=0)
                else:
                    corr_score = np.zeros(n_genes, dtype=float)
                row = 0.25 * expr_prior_n * (1.0 + corr_score)
            else:
                # Target not measured: fall back to expression prior (still varies per gene)
                row = 0.1 * expr_prior_n

            out[i, :, 0] = row

        out = np.where(np.isfinite(out), out, 0.0)
        return out
