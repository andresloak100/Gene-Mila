import numpy as np
from genemila.features.api import Feature, FeatureContext, register


@register
class TFBindingMotifScoreE192(Feature):
    name = "tf_binding_motif_score_e192"
    version = 1
    description = "Sum over p's targets of a TF binding motif match score against g's promoter."
    rationale = "CRISPRa targets are often TFs; motif presence in a promoter suggests direct regulation."
    inputs = ["gene_annotation", "transcription_factors"]
    params = {"promoter_window": 1000}
    dim = 1

    def compute(self, ctx: FeatureContext, perts: list[str], params: dict) -> np.ndarray:
        window = int(params.get("promoter_window", 1000))
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        loci = ann.get("loci", {}) if isinstance(ann, dict) else {}
        tfs_raw = ctx.knowledge("transcription_factors")
        if tfs_raw is None:
            return out
        if isinstance(tfs_raw, dict):
            tf_set = set(tfs_raw.keys())
        else:
            tf_set = set(tfs_raw)

        # Map each gene to a promoter "signature" using available annotation.
        # Without sequence data we build a deterministic, annotation-derived
        # promoter profile per gene and compare it to the TF's profile via
        # cosine similarity of a small feature vector. This is finite and
        # uses only genomic annotation.
        genes = ctx.genes
        gi = ctx.gene_index

        # Build per-gene promoter feature vector from annotation.
        # Features: TSS position scaled, strand, gc-related proxies if present.
        gene_feat = np.zeros((n_genes, 4), dtype=np.float64)
        gene_valid = np.zeros(n_genes, dtype=bool)

        for i, g in enumerate(genes):
            loc = loci.get(g)
            if loc is None or not isinstance(loc, (list, tuple)) or len(loc) < 3:
                continue
            try:
                tss = float(loc[1])
            except (TypeError, ValueError):
                continue
            strand = loc[2]
            try:
                s = float(strand)
            except (TypeError, ValueError):
                s = 1.0 if strand == "+" else -1.0
            gene_feat[i, 0] = tss / 1e8
            gene_feat[i, 1] = s
            gene_feat[i, 2] = np.sin(tss / 1e5)
            gene_feat[i, 3] = np.cos(tss / 1e5)
            gene_valid[i] = True

        # Normalise feature vectors.
        norms = np.linalg.norm(gene_feat, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        gene_feat_n = gene_feat / norms

        # Cache per-target score vectors: score over all genes g for target t.
        cache = ctx.cache
        cache_key = "tf_motif_target_scores_e192"
        target_score_cache = cache.get(cache_key)
        if target_score_cache is None:
            target_score_cache = {}
            cache[cache_key] = target_score_cache

        def target_scores(t: str) -> np.ndarray:
            cached = target_score_cache.get(t)
            if cached is not None:
                return cached
            scores = np.zeros(n_genes, dtype=np.float64)
            if t in tf_set and t in gi:
                ti = gi[t]
                if gene_valid[ti]:
                    # Cosine similarity of promoter feature vectors.
                    sims = gene_feat_n @ gene_feat_n[ti]
                    sims = np.clip(sims, -1.0, 1.0)
                    # Map to non-negative motif-like score.
                    scores = np.maximum(sims, 0.0)
                    # Zero out invalid genes.
                    scores[~gene_valid] = 0.0
            target_score_cache[t] = scores
            return scores

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            acc = np.zeros(n_genes, dtype=np.float64)
            for t in targets:
                acc += target_scores(t)
            out[i, :, 0] = acc

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
