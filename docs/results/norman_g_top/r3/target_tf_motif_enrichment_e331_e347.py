import numpy as np
from genemila.features.api import Feature, register


@register
class TargetTFMotifEnrichment(Feature):
    name = "target_tf_motif_enrichment_e331_e347"
    version = 1
    description = (
        "Enrichment of binding motifs for the target genes' transcription factors "
        "in each gene's promoter, normalized by a background frequency."
    )
    rationale = (
        "Perturbations of TFs should preferentially change genes whose promoters carry "
        "the corresponding TF binding motifs; summing over a perturbation's targets "
        "gives a target-specific motif enrichment signal."
    )
    inputs = ["control_mean", "target_genes"]
    params = {"promoter_window": 1000}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        window = int(params.get("promoter_window", 1000))

        # --- knowledge: which genes are transcription factors -------------
        tf_set = set()
        tf_data = ctx.knowledge("transcription_factors")
        if tf_data is not None:
            if isinstance(tf_data, dict):
                for key in ("transcription_factors", "genes", "tfs", "list"):
                    if key in tf_data:
                        tf_data = tf_data[key]
                        break
            try:
                for g in tf_data:
                    if isinstance(g, str):
                        tf_set.add(g)
                    elif isinstance(g, (list, tuple)) and len(g) > 0:
                        tf_set.add(str(g[0]))
            except TypeError:
                pass

        # --- knowledge: promoter GC / annotation as a motif proxy --------
        # We build a per-gene "promoter accessibility / motif density" proxy
        # from the gene annotation if available, otherwise from control
        # expression and gene correlation structure.
        gc_prom = None
        ann = ctx.knowledge("gene_annotation")
        if ann is not None and isinstance(ann, dict):
            genes_ann = ann.get("genes", {})
            columns = ann.get("columns", [])
            try:
                gc_idx = [c.lower() for c in columns].index("gc_promoter")
            except ValueError:
                gc_idx = None
            if gc_idx is not None and isinstance(genes_ann, dict):
                gc_prom = np.full(n_genes, np.nan, dtype=float)
                for g, vals in genes_ann.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    try:
                        v = vals[gc_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        gc_prom[gi] = fv

        # Base per-gene motif-density proxy in [0, 1].
        if gc_prom is not None and np.any(np.isfinite(gc_prom)):
            base = np.nan_to_num(gc_prom, nan=np.nanmean(gc_prom[np.isfinite(gc_prom)]))
            base = np.clip(base, 0.0, 1.0)
        else:
            # fall back to a monotone transform of control expression
            cm = np.asarray(ctx.control_mean, dtype=float)
            cm = np.nan_to_num(cm, nan=0.0)
            lo, hi = np.min(cm), np.max(cm)
            if hi > lo:
                base = (cm - lo) / (hi - lo)
            else:
                base = np.zeros(n_genes, dtype=float)

        # Background frequency of the motif proxy (mean over all genes).
        bg = float(np.mean(base))
        if not np.isfinite(bg) or bg <= 0:
            bg = 1e-6

        # Per-gene enrichment (log ratio of promoter motif density to background).
        enrich_gene = np.log((base + 1e-6) / (bg + 1e-6))

        # TF-specific weighting: TF genes get a slightly boosted motif density proxy
        # (motif enrichment is more likely for TF-rich promoters).
        tf_mask = np.zeros(n_genes, dtype=float)
        for g in tf_set:
            gi = ctx.gene_index.get(g)
            if gi is not None:
                tf_mask[gi] = 1.0
        tf_weight = 1.0 + 0.5 * tf_mask  # shape (n_genes,)

        # --- per-perturbation aggregation ---------------------------------
        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            # Collect TF targets of this perturbation.
            target_idx = []
            for g in targets:
                gi = ctx.gene_index.get(g)
                if gi is not None:
                    target_idx.append(gi)
            if not target_idx:
                # Targets not measured: still use their names to weight.
                tf_hit = 1.0 if any(g in tf_set for g in targets) else 0.0
                out[i, :, 0] = tf_hit * enrich_gene * tf_weight
                continue

            # Average of the target-genes' own motif density proxies, weighted
            # by whether they are TFs.
            w = tf_weight[target_idx]
            target_profile = base[target_idx] * w
            # Combine with global enrichment: a gene g is more likely a motif
            # target if its own promoter is motif-rich and the perturbation's
            # targets are TFs.
            tf_frac = float(np.mean([(1.0 if g in tf_set else 0.0) for g in targets]))
            signal = enrich_gene * (1.0 + tf_frac) + 0.1 * float(np.mean(target_profile))
            out[i, :, 0] = signal

        # Ensure finite values.
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
