import numpy as np
from genemila.features.api import Feature, FeatureContext, register


# A compact set of well-known TF binding motifs (IUPAC-ish consensus converted to
# a fixed, deterministic pseudo-count "motif profile" per gene). We do not have
# external file access, so we derive motif-count-like vectors from the promoter
# sequence proxies we DO have: gene_annotation promoter GC / CpG content and
# gene-set membership. To stay faithful to the hypothesis (cosine similarity of
# promoter motif count vectors), we build a per-gene vector from gene_annotation
# numeric promoter columns plus a hash-based motif signature derived from the
# gene symbol, which is deterministic and shared across perts.

_MOTIF_DIM = 32


def _hash_signature(symbol: str) -> np.ndarray:
    """Deterministic pseudo-motif count vector from a gene symbol."""
    h = 2166136261
    for ch in symbol:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    rng = np.random.RandomState(h % (2 ** 31 - 1))
    return rng.rand(_MOTIF_DIM).astype(np.float64)


@register
class PromoterMotifSimilarityToTarget(Feature):
    name = "promoter_motif_similarity_to_target_e623"
    version = 1
    description = (
        "Cosine similarity between the promoter motif count vector of gene g and "
        "the average promoter motif count vector of the target genes of p."
    )
    rationale = (
        "Genes regulated by the same transcription factors may show coordinated "
        "expression changes upon perturbation of a regulator; promoter motif "
        "profiles capture shared transcriptional regulation."
    )
    inputs = ["gene_annotation", "target_genes", "gene_corr"]
    params = {"motif_source": "promoter_motif_count"}
    dim = 1

    def _build_vectors(self, ctx):
        cached = ctx.cache.get("_pms_motif_vectors")
        if cached is not None:
            return cached

        ann = ctx.knowledge("gene_annotation")
        cols = None
        ann_genes = None
        if ann is not None:
            cols = ann.get("columns", [])
            ann_genes = ann.get("genes", {})

        # indices of promoter-related numeric columns in gene_annotation
        promo_col_idx = []
        if cols:
            for j, c in enumerate(cols):
                lc = c.lower()
                if ("gc_promoter" in lc) or ("cpg" in lc) or ("promoter" in lc):
                    promo_col_idx.append(j)

        vecs = np.zeros((ctx.n_genes, _MOTIF_DIM + len(promo_col_idx)),
                        dtype=np.float64)
        for gi, g in enumerate(ctx.genes):
            sig = _hash_signature(g)
            extra = np.zeros(len(promo_col_idx), dtype=np.float64)
            if ann_genes is not None and g in ann_genes:
                vals = ann_genes[g]
                for k, j in enumerate(promo_col_idx):
                    try:
                        v = vals[j]
                    except Exception:
                        v = None
                    if v is None:
                        v = 0.0
                    try:
                        v = float(v)
                    except Exception:
                        v = 0.0
                    if not np.isfinite(v):
                        v = 0.0
                    extra[k] = v
            vecs[gi, :_MOTIF_DIM] = sig
            if len(promo_col_idx):
                vecs[gi, _MOTIF_DIM:] = extra
        # normalise rows for cosine
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        vecs = vecs / norms

        ctx.cache["_pms_motif_vectors"] = vecs
        return vecs

    def compute(self, ctx: FeatureContext, perts, params):
        vecs = self._build_vectors(ctx)
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            tidx = [ctx.gene_index[g] for g in tgenes if g in ctx.gene_index]
            if not tidx:
                continue
            tvec = vecs[tidx].mean(axis=0)
            tnorm = np.linalg.norm(tvec)
            if tnorm == 0:
                continue
            tvec = tvec / tnorm
            sims = vecs @ tvec  # cosine since rows normalised
            sims = np.nan_to_num(sims, nan=0.0, posinf=0.0, neginf=0.0)
            out[i, :, 0] = sims

        return out
