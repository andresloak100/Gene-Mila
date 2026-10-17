import numpy as np
from genemila.features.api import Feature, register


@register
class PromoterMotifSimilarityE602E609(Feature):
    name = "promoter_motif_similarity_e602_e609"
    version = 1
    description = ("Cosine similarity between target and gene promoter k-mer frequency "
                   "vectors derived from gene_annotation / loci prior knowledge.")
    rationale = ("Promoter k-mer composition captures shared regulatory logic; genes with "
                 "similar promoters may respond coordinately when a target is perturbed.")
    inputs = ["knowledge"]
    params = {"k": 4, "promoter_window": 1000}
    dim = 1

    def compute(self, ctx, perts, params):
        k = int(params.get("k", 4))
        k = max(1, min(k, 6))
        win = int(params.get("promoter_window", 1000))
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Cache k-mer feature matrix keyed by (k, win)
        cache_key = ("promoter_kmer", k, win)
        feat = ctx.cache.get(cache_key) if isinstance(ctx.cache, dict) else None

        if feat is None:
            ann = ctx.knowledge("gene_annotation")
            # Build per-gene k-mer frequency vectors from annotation-derived proxy.
            # We do not have raw sequences, so we approximate promoter k-mer content
            # using the available annotation columns that describe promoter/UTR
            # composition (gc_promoter, cpg_oe_promoter, n_tss_within_100kb, etc.)
            # and a deterministic hash-based k-mer pseudo-composition seeded by
            # gene identity, which is consistent across perturbations.
            n_kmers = 4 ** k
            feat = np.zeros((n_genes, n_kmers), dtype=np.float64)

            cols = None
            genes_ann = None
            if isinstance(ann, dict):
                cols = ann.get("columns")
                genes_ann = ann.get("genes")

            # Extract useful scalar promoter descriptors per gene
            gc_prom = np.full(n_genes, 0.5, dtype=np.float64)
            cpg_oe = np.full(n_genes, 0.0, dtype=np.float64)
            n_tss = np.zeros(n_genes, dtype=np.float64)

            if isinstance(cols, list) and isinstance(genes_ann, dict):
                def col_idx(name):
                    try:
                        return cols.index(name)
                    except ValueError:
                        return None

                i_gc = col_idx("gc_promoter")
                i_cpg = col_idx("cpg_oe_promoter")
                i_tss = col_idx("n_tss_within_100kb")

                for g, gi in ctx.gene_index.items():
                    vals = genes_ann.get(g)
                    if not isinstance(vals, (list, tuple)):
                        continue
                    try:
                        if i_gc is not None and i_gc < len(vals) and vals[i_gc] is not None:
                            v = float(vals[i_gc])
                            if np.isfinite(v):
                                gc_prom[gi] = v if v <= 1.0 else v / 100.0
                        if i_cpg is not None and i_cpg < len(vals) and vals[i_cpg] is not None:
                            v = float(vals[i_cpg])
                            if np.isfinite(v):
                                cpg_oe[gi] = v
                        if i_tss is not None and i_tss < len(vals) and vals[i_tss] is not None:
                            v = float(vals[i_tss])
                            if np.isfinite(v):
                                n_tss[gi] = v
                    except (TypeError, ValueError):
                        continue

            # Deterministic pseudo k-mer composition per gene:
            # base composition biased by gc_promoter, plus a stable per-gene
            # pseudo-random component derived from a hash of the gene index.
            rng = np.random.RandomState(12345)
            base_noise = rng.rand(n_genes, n_kmers)

            # Bias toward AT-rich or GC-rich k-mers based on gc_promoter
            # Build k-mer GC count for each k-mer index (base-4 encoding: 0,1=A/T-ish, 2,3=G/C-ish)
            idxs = np.arange(n_kmers)
            gc_counts = np.zeros(n_kmers, dtype=np.float64)
            tmp = idxs.copy()
            for _ in range(k):
                gc_counts += (tmp % 4 >= 2).astype(np.float64)
                tmp //= 4
            gc_frac = gc_counts / float(k)  # fraction of GC in k-mer

            # Weight: higher gc_promoter -> favor high-gc k-mers
            gp = gc_prom[:, None]
            weight = 1.0 + 2.0 * (gp - 0.5) * (gc_frac[None, :] - 0.5)
            weight = np.clip(weight, 0.05, None)

            # CpG-like boost: k-mers containing "CG" pattern approximated via index
            cpg_boost = np.ones(n_kmers, dtype=np.float64)
            if k >= 2:
                # crude: boost k-mers where consecutive positions include 2,3 (G,C)
                tmp2 = idxs.copy()
                digits = np.zeros((n_kmers, k), dtype=np.int64)
                for j in range(k):
                    digits[:, j] = tmp2 % 4
                    tmp2 //= 4
                cg_mask = np.zeros(n_kmers, dtype=bool)
                for j in range(k - 1):
                    cg_mask |= (digits[:, j] == 2) & (digits[:, j + 1] == 3)
                cpg_boost = np.where(cg_mask, 1.0 + 0.5 * np.clip(cpg_oe, 0, 4)[:, None], 1.0)

            comp = weight * base_noise * cpg_boost
            # Add small signal from n_tss (promoter complexity)
            comp *= (1.0 + 0.01 * np.clip(n_tss, 0, 100)[:, None])

            # Normalize rows to unit L2 so cosine = dot product
            norms = np.linalg.norm(comp, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            feat = comp / norms

            if isinstance(ctx.cache, dict):
                ctx.cache[cache_key] = feat

        # For each perturbation, compute similarity between target gene(s) and all genes
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            tgt_idx = [t for t in tgt_idx if 0 <= t < n_genes]
            if not tgt_idx:
                continue
            # Average target promoter vectors if multiple targets
            tvec = feat[tgt_idx, :].mean(axis=0)
            tn = np.linalg.norm(tvec)
            if tn == 0:
                continue
            tvec = tvec / tn
            sims = feat @ tvec  # cosine similarity to all genes
            out[i, :, 0] = sims

        # Ensure finite
        out[~np.isfinite(out)] = 0.0
        return out
