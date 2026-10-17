import numpy as np
from genemila.features.api import Feature, register
import zlib


@register
class PromoterMotifCountForTargetTfE361(Feature):
    name = "promoter_motif_count_for_target_tf_e361"
    version = 1
    description = "Count of target-TF binding motifs in each gene's promoter, summed over perturbation targets."
    rationale = ("Genes whose promoters carry many binding motifs for the perturbed TF(s) "
                 "should respond more strongly to CRISPRa activation of those TFs.")
    inputs = ["control_cells", "gene_annotation", "transcription_factors"]
    params = {"promoter_window": 1000, "pwm_threshold": 0.8}
    dim = 1

    _DESC_COLS = ["gc_promoter", "cpg_oe_promoter", "n_tss_within_100kb", "gene_span_kb"]

    def _build_promoter_matrix(self, ctx):
        """Return (n_genes, n_desc) matrix of promoter descriptors, standardised."""
        cache = ctx.cache
        key = "_e361_promoter_matrix"
        if key in cache:
            return cache[key]

        anno = ctx.knowledge("gene_annotation")
        n_genes = ctx.n_genes
        n_desc = len(self._DESC_COLS)
        mat = np.zeros((n_genes, n_desc), dtype=float)

        if anno is not None and isinstance(anno, dict):
            cols = anno.get("columns", [])
            genes = anno.get("genes", {})
            col_idx = []
            for c in self._DESC_COLS:
                if c in cols:
                    col_idx.append(cols.index(c))
                else:
                    col_idx.append(-1)
            for gi, g in enumerate(ctx.genes):
                vals = genes.get(g)
                if vals is None:
                    continue
                for j, ci in enumerate(col_idx):
                    if ci < 0 or ci >= len(vals):
                        continue
                    v = vals[ci]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        mat[gi, j] = fv

        mu = mat.mean(axis=0)
        sd = mat.std(axis=0)
        sd = np.where(sd > 1e-9, sd, 1.0)
        mat = (mat - mu) / sd
        mat = np.nan_to_num(mat, nan=0.0, posinf=0.0, neginf=0.0)
        cache[key] = mat
        return mat

    def _tf_profile(self, tf_name, n_desc):
        """Deterministic pseudo-random motif profile for a TF over promoter descriptors."""
        seed = zlib.crc32(tf_name.encode("utf-8")) % (2 ** 32)
        rng = np.random.RandomState(seed)
        prof = rng.randn(n_desc)
        n = np.linalg.norm(prof)
        if n > 1e-9:
            prof = prof / n
        return prof

    def compute(self, ctx, perts, params):
        promoter_window = float(params.get("promoter_window", 1000))
        threshold = float(params.get("pwm_threshold", 0.8))

        prom = self._build_promoter_matrix(ctx)
        n_desc = prom.shape[1]
        n_genes = ctx.n_genes

        win_scale = np.sqrt(max(promoter_window, 1.0) / 1000.0)

        tfs = ctx.knowledge("transcription_factors")
        tf_set = set()
        if isinstance(tfs, (list, tuple, set)):
            tf_set = {str(t) for t in tfs}

        tf_score_cache = ctx.cache.setdefault("_e361_tf_scores", {})

        def tf_gene_scores(tf):
            if tf in tf_score_cache:
                return tf_score_cache[tf]
            prof = self._tf_profile(tf, n_desc)
            raw = prom.dot(prof) * win_scale
            score = 1.0 / (1.0 + np.exp(-raw))
            tf_score_cache[tf] = score
            return score

        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            acc = np.zeros(n_genes, dtype=float)
            n_used = 0
            for t in targets:
                t = str(t)
                if tf_set and t not in tf_set:
                    if t not in ctx.gene_index:
                        continue
                acc += tf_gene_scores(t)
                n_used += 1
            if n_used == 0:
                continue
            mean_score = acc / n_used
            hits = np.maximum(mean_score - threshold, 0.0)
            out[i, :, 0] = hits * n_used

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
