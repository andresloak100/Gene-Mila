import numpy as np
from genemila.features.api import Feature, register


@register
class TargetHalfLifeInteractionE91(Feature):
    name = "target_half_life_interaction_e91"
    version = 1
    description = ("Interaction between target protein half-life proxy (from protein_annotation) "
                   "and whether gene g shares a complex/pathway with the target.")
    rationale = ("Short-lived proteins are rapidly depleted upon knockdown, producing stronger "
                 "downstream effects; the effect should be amplified for members of the same complex.")
    inputs = ["protein_annotation", "gene_sets", "target_indices"]
    params = {"half_life_source": "external"}
    dim = 1

    def _half_life_proxy(self, ctx):
        """Return per-gene stability proxy (higher = shorter half-life / less stable)."""
        cache = ctx.cache
        if "e91_hl" in cache:
            return cache["e91_hl"]
        n = ctx.n_genes
        hl = np.zeros(n, dtype=float)
        ann = ctx.knowledge("protein_annotation")
        if ann is not None and isinstance(ann, dict):
            genes = ann.get("genes", {}) or {}
            cols = ann.get("columns", []) or []
            idx = {c: i for i, c in enumerate(cols)}
            i_len = idx.get("protein_length", None)
            i_sig = idx.get("has_signal_peptide", None)
            i_tm = idx.get("n_transmembrane", None)
            i_secreted = idx.get("secreted", None)
            i_mem = idx.get("membrane", None)
            i_cyto = idx.get("cytoplasm", None)
            i_nuc = idx.get("nucleus", None)
            for g, gi in ctx.gene_index.items():
                vals = genes.get(g, None)
                if vals is None:
                    continue
                try:
                    score = 0.0
                    plen = None
                    if i_len is not None and vals[i_len] is not None:
                        plen = float(vals[i_len])
                    # Shorter proteins tend to be less stable; PEST-like: no membrane/signal,
                    # cytoplasmic, moderate length -> less stable.
                    if plen is not None and plen > 0:
                        score += 1.0 / (1.0 + np.log1p(plen))
                    else:
                        score += 0.3
                    if i_sig is not None and vals[i_sig] is not None:
                        score -= 0.4 * float(vals[i_sig])
                    if i_tm is not None and vals[i_tm] is not None:
                        score -= 0.3 * min(float(vals[i_tm]), 3.0) / 3.0
                    if i_secreted is not None and vals[i_secreted] is not None:
                        score -= 0.3 * float(vals[i_secreted])
                    if i_mem is not None and vals[i_mem] is not None:
                        score -= 0.2 * float(vals[i_mem])
                    if i_cyto is not None and vals[i_cyto] is not None:
                        score += 0.3 * float(vals[i_cyto])
                    if i_nuc is not None and vals[i_nuc] is not None:
                        score += 0.1 * float(vals[i_nuc])
                    hl[gi] = score
                except (TypeError, ValueError, IndexError):
                    continue
        # standardise
        mu = hl.mean()
        sd = hl.std()
        if sd > 1e-8:
            hl = (hl - mu) / sd
        else:
            hl = np.zeros(n, dtype=float)
        cache["e91_hl"] = hl
        return hl

    def _gene_set_membership(self, ctx):
        """Return sparse-ish dict gene_index -> set of set names (or None)."""
        cache = ctx.cache
        if "e91_sets" in cache:
            return cache["e91_sets"]
        gs = ctx.knowledge("gene_sets")
        membership = {}
        if gs is not None and isinstance(gs, dict):
            for setname, members in gs.items():
                if not isinstance(members, (list, tuple)):
                    continue
                for m in members:
                    gi = ctx.gene_index.get(m, None)
                    if gi is None:
                        continue
                    s = membership.get(gi)
                    if s is None:
                        s = set()
                        membership[gi] = s
                    s.add(setname)
        cache["e91_sets"] = membership
        return membership

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)
        hl = self._half_life_proxy(ctx)
        membership = self._gene_set_membership(ctx)

        # Precompute gene set sizes for fraction weighting
        set_sizes = {}
        for gi, sets in membership.items():
            for s in sets:
                set_sizes[s] = set_sizes.get(s, 0) + 1

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if len(tgt_idx) == 0:
                continue
            # target half-life proxy: average over targeted genes
            t_hl = float(np.mean(hl[tgt_idx]))
            t_sets = set()
            for ti in tgt_idx:
                s = membership.get(ti)
                if s:
                    t_sets |= s
            if not t_sets:
                continue
            for gi in range(n):
                g_sets = membership.get(gi)
                if not g_sets:
                    continue
                shared = t_sets & g_sets
                if not shared:
                    continue
                # fraction of gene's sets that are shared with target
                frac = len(shared) / float(len(g_sets)) if g_sets else 0.0
                out[i, gi, 0] = t_hl * frac
        return out
