import numpy as np
from genemila.features.api import Feature, register


@register
class ChromatinAccessibilityCorrE478(Feature):
    name = "chromatin_accessibility_corr_e478"
    version = 1
    description = (
        "For each (p,g): Pearson correlation between the chromatin-accessibility "
        "profile of the perturbation target and that of gene g, where the profile "
        "is a proxy built from promoter/genomic annotations (GC content, CpG "
        "island content, gene span, TSS neighbourhood density, transcript "
        "complexity) treated as pseudo cell-type accessibility dimensions."
    )
    rationale = (
        "Genes with correlated chromatin accessibility profiles across cell "
        "types tend to be co-regulated; perturbations of a target may therefore "
        "shift genes whose promoter accessibility profile resembles the target's."
    )
    inputs = ["gene_annotation"]
    params = {"promoter_region": "TSS +/- 2kb"}
    dim = 1

    def _build_profiles(self, ctx, genes):
        n = len(genes)
        n_dims = 8
        prof = np.zeros((n, n_dims), dtype=float)
        valid = np.zeros(n, dtype=bool)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            ann_genes = ann.get("genes", {}) or {}
            columns = ann.get("columns", []) or []
            col_idx = {c: i for i, c in enumerate(columns)}

            wanted = [
                "gene_span_kb",
                "n_transcripts",
                "n_exons",
                "transcript_length",
                "intron_length_kb",
                "gc_cds",
                "gc_utr3",
                "gc_promoter",
                "cpg_oe_promoter",
                "n_tss_within_100kb",
                "n_upstream_atg",
                "nearest_tss_kb",
            ]
            wanted = [w for w in wanted if w in col_idx]

            if len(wanted) > 0:
                for i, g in enumerate(genes):
                    vals = ann_genes.get(g)
                    if vals is None:
                        continue
                    row = np.full(len(wanted), np.nan, dtype=float)
                    for j, w in enumerate(wanted):
                        v = vals[col_idx[w]]
                        if v is not None:
                            try:
                                row[j] = float(v)
                            except (TypeError, ValueError):
                                row[j] = np.nan
                    if np.all(np.isnan(row)):
                        continue
                    # Reduce to n_dims via averaging blocks / padding.
                    if len(row) >= n_dims:
                        # split into n_dims roughly equal groups
                        groups = np.array_split(row, n_dims)
                        reduced = np.array(
                            [np.nanmean(gr) if not np.all(np.isnan(gr)) else np.nan
                             for gr in groups], dtype=float
                        )
                    else:
                        reduced = np.full(n_dims, np.nan, dtype=float)
                        reduced[:len(row)] = row
                    prof[i, :] = reduced
                    valid[i] = True

        if not valid.any():
            # Fallback: derive profiles from control expression statistics.
            cm = ctx.control_mean
            cs = ctx.control_std
            prof[:, 0] = cm
            prof[:, 1] = cs
            prof[:, 2] = cs / (np.abs(cm) + 1e-6)
            prof[:, 3] = cm * cm
            prof[:, 4] = np.log1p(np.abs(cm))
            prof[:, 5] = np.log1p(np.abs(cs))
            prof[:, 6] = np.abs(cs - cm)
            prof[:, 7] = cm + cs
            valid[:] = True

        # Standardize each dimension (z-score) over valid genes, impute NaNs.
        if valid.any():
            vp = prof[valid]
            mu = np.nanmean(vp, axis=0)
            sd = np.nanstd(vp, axis=0)
            sd[~np.isfinite(sd)] = 1.0
            sd[sd < 1e-9] = 1.0
            mu = np.where(np.isfinite(mu), mu, 0.0)
            nan_mask = ~np.isfinite(prof)
            if nan_mask.any():
                rows, cols = np.where(nan_mask)
                prof[rows, cols] = mu[cols]
            prof = (prof - mu) / sd
        else:
            prof = np.zeros_like(prof)

        prof[~np.isfinite(prof)] = 0.0
        return prof

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        prof = self._build_profiles(ctx, ctx.genes)
        centered = prof - prof.mean(axis=1, keepdims=True)
        norms = np.linalg.norm(centered, axis=1)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            t = tgt_idx[0]
            if norms[t] < 1e-9:
                continue
            tv = centered[t]
            num = centered @ tv
            denom = norms * norms[t]
            corr = np.zeros(n_genes, dtype=float)
            good = denom > 1e-9
            corr[good] = num[good] / denom[good]
            corr = np.clip(corr, -1.0, 1.0)
            out[i, :, 0] = corr

        out[~np.isfinite(out)] = 0.0
        return out
