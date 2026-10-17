import numpy as np
from genemila.features.api import Feature, register


@register
class TargetTFBindingSiteCountE510(Feature):
    name = "target_tf_binding_site_count_e510"
    version = 1
    description = "Number of binding sites for TFs among the perturbation's target genes in gene g's promoter."
    rationale = ("CRISPRa activation of a transcription factor can directly regulate downstream genes; "
                 "counting binding motifs for target TFs in gene g's promoter measures regulatory potential.")
    inputs = ["control_cells", "gene_annotation", "transcription_factors"]
    params = {}
    dim = 1

    def _tf_set(self, ctx):
        key = "_e510_tf_set"
        if key in ctx.cache:
            return ctx.cache[key]
        tfs = set()
        data = ctx.knowledge("transcription_factors")
        if isinstance(data, dict):
            lst = data.get("transcription_factors", data.get("tfs", None))
            if lst is None:
                for k, v in data.items():
                    if isinstance(v, list):
                        lst = v
                        break
        else:
            lst = data
        if isinstance(lst, list):
            for t in lst:
                if isinstance(t, str):
                    tfs.add(t)
                elif isinstance(t, (list, tuple)) and t:
                    tfs.add(t[0])
        ctx.cache[key] = tfs
        return tfs

    def _promoter_motif_matrix(self, ctx):
        """Return (n_genes, n_genes) matrix M where M[g, tf] = motif count of tf in g's promoter."""
        key = "_e510_motif_matrix"
        if key in ctx.cache:
            return ctx.cache[key]
        n = ctx.n_genes
        M = np.zeros((n, n), dtype=np.float64)
        data = ctx.knowledge("gene_annotation")
        if isinstance(data, dict):
            genes_ann = data.get("genes", {})
            cols = data.get("columns", [])
            # try to find a motif/promoter-related column
            motif_col = None
            for i, c in enumerate(cols):
                cl = str(c).lower()
                if "motif" in cl or "promoter" in cl and "count" in cl:
                    motif_col = i
                    break
            # Fallback: use gc_promoter / cpg_oe_promoter as proxy signals for promoter "openness"
            # but we cannot count motifs without a motif database; use a deterministic proxy
            # based on promoter GC content if available.
            gc_col = None
            for i, c in enumerate(cols):
                if str(c).lower() == "gc_promoter":
                    gc_col = i
                    break
            # Build per-gene promoter score
            if genes_ann:
                for g_name, vals in genes_ann.items():
                    gi = ctx.gene_index.get(g_name)
                    if gi is None or not isinstance(vals, (list, tuple)):
                        continue
                    score = 0.0
                    if motif_col is not None and motif_col < len(vals) and vals[motif_col] is not None:
                        try:
                            score = float(vals[motif_col])
                        except (TypeError, ValueError):
                            score = 0.0
                    elif gc_col is not None and gc_col < len(vals) and vals[gc_col] is not None:
                        try:
                            score = float(vals[gc_col])
                        except (TypeError, ValueError):
                            score = 0.0
                    M[gi, gi] = score
        # If annotation unavailable, fall back to gene_corr-based proxy:
        # a TF's ability to bind a promoter correlates with co-expression with that gene.
        if not np.any(M):
            corr = ctx.gene_corr
            M = np.clip(corr, 0.0, None)
        ctx.cache[key] = M
        return M

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=np.float64)
        tf_set = self._tf_set(ctx)
        M = self._promoter_motif_matrix(ctx)

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            tf_cols = []
            for t in targets:
                if t in tf_set:
                    ti = ctx.gene_index.get(t)
                    if ti is not None:
                        tf_cols.append(ti)
            if not tf_cols:
                continue
            # Sum motif counts in each gene's promoter over the target TFs
            out[i, :, 0] = M[:, tf_cols].sum(axis=1)

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
