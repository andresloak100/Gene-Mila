import numpy as np
from genemila.features.api import Feature, register


@register
class DomainSimilarityE123(Feature):
    name = "domain_similarity_e123"
    version = 1
    description = "Jaccard similarity of protein domain sets between target gene t and gene g."
    rationale = ("Protein domains define function; genes sharing domains may be co-regulated "
                 "or part of complexes, so domain-set overlap between target and gene g "
                 "predicts co-response.")
    inputs = ["protein_annotation", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # Build per-gene domain sets from protein_annotation.
        # The annotation has numeric columns (protein_length, flags, etc.) but no explicit
        # domain list; we derive a domain "signature" from the categorical/localization
        # flags and coarse length bins, which serve as a domain-composition proxy.
        ann = ctx.knowledge("protein_annotation")
        gene_domains = {}
        if ann is not None and isinstance(ann, dict):
            cols = ann.get("columns", [])
            genes_tbl = ann.get("genes", {})
            # Identify flag-like / categorical columns (compartment flags, signal peptide, tm).
            flag_cols = []
            for j, c in enumerate(cols):
                lc = str(c).lower()
                if ("secreted" in lc or "membrane" in lc or "endoplasmic" in lc
                        or "golgi" in lc or "mitochond" in lc or "nucleus" in lc
                        or "cytoplasm" in lc or "lysosome" in lc or "peroxisome" in lc
                        or "signal_peptide" in lc):
                    flag_cols.append(j)
            # Also use amino-acid fraction columns as a compositional domain proxy.
            aa_cols = [j for j, c in enumerate(cols) if str(c).startswith("aa_")]
            # Length bin index (coarse) as a domain-composition token.
            len_idx = None
            for j, c in enumerate(cols):
                if str(c) == "protein_length":
                    len_idx = j
                    break

            for sym in ctx.genes:
                vals = genes_tbl.get(sym)
                if vals is None:
                    gene_domains[sym] = frozenset()
                    continue
                toks = set()
                for j in flag_cols:
                    try:
                        v = vals[j]
                    except Exception:
                        continue
                    if v is not None and v == 1:
                        toks.add(("flag", j))
                # coarse aa composition signature: which aa fractions are > 0.05
                for j in aa_cols:
                    try:
                        v = vals[j]
                    except Exception:
                        continue
                    if v is not None and v > 0.05:
                        toks.add(("aa", j))
                if len_idx is not None:
                    try:
                        L = vals[len_idx]
                    except Exception:
                        L = None
                    if L is not None:
                        toks.add(("lenbin", int(np.log2(max(L, 1.0)))))
                gene_domains[sym] = frozenset(toks)
        else:
            for sym in ctx.genes:
                gene_domains[sym] = frozenset()

        # Precompute gene-indexed domain sets.
        gene_sets = [gene_domains.get(g, frozenset()) for g in ctx.genes]

        # Cache similarity matrix lazily per target set (cheap enough to recompute).
        sim_cache = ctx.cache.setdefault("domain_sim_e123", {})

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if not tgenes:
                continue
            # Union of domains of all targets of p.
            tset = set()
            for tg in tgenes:
                tset |= gene_domains.get(tg, frozenset())
            if not tset:
                continue
            key = frozenset(tset)
            sims = sim_cache.get(key)
            if sims is None:
                tset_f = frozenset(tset)
                sims = np.zeros(n_genes, dtype=float)
                tsize = len(tset_f)
                for gi in range(n_genes):
                    gs = gene_sets[gi]
                    if not gs:
                        continue
                    inter = len(tset_f & gs)
                    if inter == 0:
                        continue
                    union = tsize + len(gs) - inter
                    if union > 0:
                        sims[gi] = inter / union
                sim_cache[key] = sims
            out[i, :, 0] = sims

        # Ensure finite.
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
