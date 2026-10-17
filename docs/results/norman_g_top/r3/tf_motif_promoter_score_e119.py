import numpy as np
from genemila.features.api import Feature, register


@register
class TFMotifPromoterScoreE119(Feature):
    name = "tf_motif_promoter_score_e119"
    version = 1
    description = ("For perturbations whose target is a transcription factor, score each gene by "
                   "the number of binding motifs for that TF in its promoter region; 0 for non-TF targets.")
    rationale = ("If the perturbation target is a transcription factor, the presence of its binding "
                 "motif in a gene's promoter predicts that gene as a direct target.")
    inputs = ["control_cells", "gene_annotation", "prior_network"]
    params = {"promoter_window": 1000}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # --- TF set ---
        tfs = ctx.knowledge("transcription_factors")
        if tfs is None:
            tfs = []
        if isinstance(tfs, dict):
            tfs = list(tfs.keys())
        tf_set = set(tfs)

        # --- Prior network edges as a motif/regulatory proxy: TF -> target ---
        # Cache a mapping: regulator gene -> set of target gene indices
        reg_map = ctx.cache.get("e119_reg_map")
        if reg_map is None:
            reg_map = {}
            pn = ctx.knowledge("prior_network")
            if pn is not None:
                for edge in pn:
                    try:
                        a, b = edge[0], edge[1]
                    except (IndexError, TypeError):
                        continue
                    if a in ctx.gene_index and b in ctx.gene_index:
                        reg_map.setdefault(a, set()).add(ctx.gene_index[b])
            ctx.cache["e119_reg_map"] = reg_map

        # --- Optional promoter-based motif count proxy via gene_annotation ---
        # Use GC promoter content as a weak motif-availability signal if no prior edges.
        ga = ctx.knowledge("gene_annotation")
        gc_prom = None
        gc_idx = None
        if isinstance(ga, dict) and "genes" in ga and "columns" in ga:
            cols = ga["columns"]
            if "gc_promoter" in cols:
                gc_idx = cols.index("gc_promoter")
                gc_prom = np.full(n_genes, np.nan, dtype=float)
                gdict = ga["genes"]
                for g, gi in ctx.gene_index.items():
                    vals = gdict.get(g)
                    if vals is not None and gc_idx < len(vals) and vals[gc_idx] is not None:
                        try:
                            gc_prom[gi] = float(vals[gc_idx])
                        except (TypeError, ValueError):
                            pass

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            # Only when at least one target is a TF
            tf_targets = [t for t in targets if t in tf_set]
            if not tf_targets:
                continue

            score = np.zeros(n_genes, dtype=float)
            for tf in tf_targets:
                tgts = reg_map.get(tf)
                if tgts:
                    idx = np.fromiter(tgts, dtype=int, count=len(tgts))
                    score[idx] += 1.0
                elif gc_prom is not None:
                    # Fallback: weak proxy using promoter GC content as motif density proxy
                    valid = np.isfinite(gc_prom)
                    if valid.any():
                        score[valid] += gc_prom[valid]

            # Normalize by number of TF targets in the perturbation
            score = score / float(len(tf_targets))
            out[i, :, 0] = score

        # Ensure finiteness
        out[~np.isfinite(out)] = 0.0
        return out
