import numpy as np
from genemila.features.api import Feature, register


@register
class SharedTFBindingCountPromoterE419(Feature):
    name = "shared_tf_binding_count_promoter_e419"
    version = 1
    description = ("Count of transcription factors (from the provided TF list) whose binding "
                   "is likely at both the perturbation target's promoter and gene g's promoter, "
                   "approximated via promoter GC content and CpG observed/expected ratio.")
    rationale = ("Promoters with high GC and high CpG O/E are enriched for binding of many "
                 "TFs (especially GC-box factors). If both the target promoter and gene g's "
                 "promoter are GC-rich, they are likely co-occupied by the same GC-binding TFs, "
                 "suggesting co-regulation and a shared response to perturbing the target.")
    inputs = ["gene_annotation", "transcription_factors"]
    params = {"gc_threshold": 0.6, "cpg_threshold": 0.6}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)
        out = np.zeros((n_perts, n_genes, 1), dtype=np.float64)

        gc_thr = float(params.get("gc_threshold", 0.6))
        cpg_thr = float(params.get("cpg_threshold", 0.6))

        ann = ctx.knowledge("gene_annotation")
        tf_list = ctx.knowledge("transcription_factors")

        # Build per-gene boolean "likely TF-bound / GC-rich promoter" mask.
        gc_vec = np.zeros(n_genes, dtype=np.float64)
        cpg_vec = np.zeros(n_genes, dtype=np.float64)

        cols = None
        genes_map = None
        if isinstance(ann, dict):
            cols = ann.get("columns")
            genes_map = ann.get("genes")

        gi_gc = None
        gi_cpg = None
        if isinstance(cols, list):
            for idx, cname in enumerate(cols):
                cl = str(cname).lower()
                if "gc_promoter" in cl or cl == "gc_promoter":
                    gi_gc = idx
                if "cpg_oe_promoter" in cl or cl == "cpg_oe_promoter":
                    gi_cpg = idx

        if isinstance(genes_map, dict) and gi_gc is not None:
            for gname in ctx.genes:
                vals = genes_map.get(gname)
                if not vals:
                    continue
                col = ctx.gene_index.get(gname)
                if col is None:
                    continue
                try:
                    v = vals[gi_gc]
                    if v is not None:
                        gc_vec[col] = float(v)
                except (IndexError, TypeError, ValueError):
                    pass
                if gi_cpg is not None:
                    try:
                        v2 = vals[gi_cpg]
                        if v2 is not None:
                            cpg_vec[col] = float(v2)
                    except (IndexError, TypeError, ValueError):
                        pass

        # TF membership set (used to weight / restrict). Even without per-TF promoter
        # models, we use the TF list to define the "universe" of TFs and their
        # GC-box preference via a shared GC-rich promoter heuristic.
        tf_set = set()
        if isinstance(tf_list, list):
            for t in tf_list:
                if isinstance(t, str):
                    tf_set.add(t)
        elif isinstance(tf_list, dict):
            for t in tf_list.keys():
                tf_set.add(str(t))

        # Heuristic: number of TFs in the list that are GC-box-like factors.
        # We approximate that each GC-rich promoter is bound by a fraction of the
        # TF list; the shared count between two GC-rich promoters scales with the
        # number of GC-preferring TFs.
        n_tf = max(len(tf_set), 1)

        # Compute per-gene "GC-rich promoter" indicator (soft).
        gc_norm = np.clip((gc_vec - gc_thr) / max(1e-6, (1.0 - gc_thr)), 0.0, 1.0)
        cpg_norm = np.clip((cpg_vec - cpg_thr) / max(1e-6, (1.0 - cpg_thr)), 0.0, 1.0)
        # Combine GC and CpG signals; fall back to GC only if CpG missing.
        if np.any(cpg_vec > 0):
            promoter_score = 0.5 * gc_norm + 0.5 * cpg_norm
        else:
            promoter_score = gc_norm

        # Expected number of shared GC-box-binding TFs for two promoters is
        # proportional to the product of their promoter scores and the count of
        # GC-preferring TFs in the list.
        # Assume a modest fraction (e.g. 20%) of the TF list is GC-box preferring.
        frac_gc_tfs = 0.2
        n_gc_tfs = frac_gc_tfs * n_tf

        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if not tidx:
                continue
            # Use the mean promoter score across target gene columns.
            t_score = float(np.mean(promoter_score[tidx]))
            if t_score <= 0.0:
                continue
            # Shared TF count ~ t_score * g_score * n_gc_tfs
            out[i, :, 0] = t_score * promoter_score * n_gc_tfs

        # Ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
