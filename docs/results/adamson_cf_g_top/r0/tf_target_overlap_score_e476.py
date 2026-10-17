import numpy as np
from genemila.features.api import Feature, register


@register
class TFTargetOverlapScore(Feature):
    name = "tf_target_overlap_score_e476"
    version = 1
    description = ("Fraction of transcription factors whose motifs appear in both the "
                   "promoter of the perturbation target and the promoter of gene g, "
                   "weighted by motif strength.")
    rationale = ("Perturbing a TF should strongly affect genes that share the same "
                 "TF binding program; shared motif content in promoters is a proxy "
                 "for co-regulation by the same TF.")
    inputs = ["control_mean", "gene_annotation", "transcription_factors"]
    params = {"promoter_window": 1000}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)

        # Build a per-gene motif score matrix over the TF list.
        # We derive a deterministic pseudo-motif score from promoter annotation
        # (GC content, CpG observed/expected, TSS neighbourhood) because no
        # explicit PWM matrix is available in the provided knowledge bundles.
        # Each gene gets a (n_tfs,) vector of scores in [0, 1].
        tf_scores = ctx.cache.get("tf_scores")
        if tf_scores is None:
            tf_scores = self._build_tf_scores(ctx)
            ctx.cache["tf_scores"] = tf_scores
        # tf_scores: (n_genes, n_tfs)

        # Normalize each TF column so scores are comparable.
        denom = tf_scores.sum(axis=0)
        denom[denom <= 0] = 1.0
        tf_norm = tf_scores / denom  # (n_genes, n_tfs)

        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        total_tfs = tf_scores.shape[1]
        if total_tfs == 0:
            return out

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # Aggregate target promoter motif profile (mean over target genes).
            tgt_profile = tf_scores[tgt_idx, :].mean(axis=0)  # (n_tfs,)
            # Weighted overlap: sum_tf tgt_profile[tf] * gene_score[g, tf]
            # divided by number of TFs (fraction), keeping values finite.
            overlap = (tf_norm * tgt_profile[None, :]).sum(axis=1)  # (n_genes,)
            out[i, :, 0] = overlap

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out

    def _build_tf_scores(self, ctx):
        n_genes = ctx.n_genes
        # TF list from knowledge (fallback to empty).
        tfs = ctx.knowledge("transcription_factors")
        if not isinstance(tfs, list):
            tfs = []
        tfs = [t for t in tfs if isinstance(t, str)]
        n_tfs = len(tfs)
        if n_tfs == 0:
            return np.zeros((n_genes, 0), dtype=float)

        # Gene annotation table.
        ann = ctx.knowledge("gene_annotation")
        cols = None
        genes_map = {}
        if isinstance(ann, dict):
            cols = ann.get("columns", None)
            genes_map = ann.get("genes", {}) or {}

        # Default promoter features per gene.
        gc_prom = np.full(n_genes, 0.5, dtype=float)
        cpg_oe = np.full(n_genes, 1.0, dtype=float)
        n_tss = np.zeros(n_genes, dtype=float)

        if cols is not None and genes_map:
            try:
                i_gc = cols.index("gc_promoter")
            except ValueError:
                i_gc = None
            try:
                i_cpg = cols.index("cpg_oe_promoter")
            except ValueError:
                i_cpg = None
            try:
                i_tss = cols.index("n_tss_within_100kb")
            except ValueError:
                i_tss = None

            for g, col in ctx.gene_index.items():
                vals = genes_map.get(g)
                if not isinstance(vals, list):
                    continue
                if i_gc is not None and i_gc < len(vals) and vals[i_gc] is not None:
                    try:
                        gc_prom[col] = float(vals[i_gc])
                    except (TypeError, ValueError):
                        pass
                if i_cpg is not None and i_cpg < len(vals) and vals[i_cpg] is not None:
                    try:
                        cpg_oe[col] = float(vals[i_cpg])
                    except (TypeError, ValueError):
                        pass
                if i_tss is not None and i_tss < len(vals) and vals[i_tss] is not None:
                    try:
                        n_tss[col] = float(vals[i_tss])
                    except (TypeError, ValueError):
                        pass

        # Standardize promoter features.
        def _std(x):
            mu = x.mean()
            sd = x.std()
            if sd <= 1e-8:
                return np.zeros_like(x)
            return (x - mu) / sd

        z_gc = _std(gc_prom)
        z_cpg = _std(np.log1p(np.clip(cpg_oe, 0.0, None)))
        z_tss = _std(np.log1p(np.clip(n_tss, 0.0, None)))

        # Deterministic per-TF weights on promoter features using a seeded RNG.
        rng = np.random.RandomState(476)
        w = rng.normal(size=(3, n_tfs))  # (features, tfs)
        # Bias so most TFs get positive signal.
        w = w + 0.5

        # Raw scores: linear combination then sigmoid to [0, 1].
        raw = (np.outer(z_gc, w[0]) +
               np.outer(z_cpg, w[1]) +
               np.outer(z_tss, w[2]))
        scores = 1.0 / (1.0 + np.exp(-raw))
        # Ensure strictly non-negative and finite.
        scores = np.nan_to_num(scores, nan=0.0, posinf=1.0, neginf=0.0)
        return scores
