import numpy as np
from genemila.features.api import Feature, register


@register
class ComplexMembershipInteractionE479(Feature):
    name = "complex_membership_interaction_e479"
    version = 1
    description = ("For each (p,g): sum over protein complexes containing both the "
                   "perturbation target and gene g, weighted by complex essentiality "
                   "(mean LoF constraint of members).")
    rationale = ("Perturbing one subunit of a complex can destabilise the whole complex, "
                 "affecting co-members; essential complexes propagate stronger responses.")
    inputs = ["gene_constraint", "gene_sets", "target_indices"]
    params = {"complex_db": "CORUM"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)

        # ---- Build gene -> complex mapping from gene_sets ----
        complexes = None
        gs = ctx.knowledge("gene_sets")
        if gs is not None:
            # gene_sets may be dict {complex_name: [genes]} or wrapped
            if isinstance(gs, dict) and "genes" not in gs:
                raw = gs
            elif isinstance(gs, dict) and "genes" in gs:
                raw = gs["genes"]
            else:
                raw = {}
            # filter to complex-like sets
            complexes = []
            for name, members in raw.items():
                if not isinstance(members, (list, tuple)):
                    continue
                idx = [ctx.gene_index[g] for g in members if g in ctx.gene_index]
                if len(idx) >= 2:
                    complexes.append(np.array(sorted(set(idx)), dtype=np.int64))

        if not complexes:
            return np.zeros((n_perts, n_genes, 1), dtype=np.float64)

        # ---- Essentiality weights: (1 - LOEUF), clipped to [0,1] ----
        ess = np.full(n_genes, 0.5, dtype=np.float64)
        gc = ctx.knowledge("gene_constraint")
        if gc is not None and isinstance(gc, dict):
            genes_tbl = gc.get("genes", {})
            cols = gc.get("columns", [])
            try:
                loeuf_col = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_col = None
            if loeuf_col is not None and isinstance(genes_tbl, dict):
                for sym, vals in genes_tbl.items():
                    gi = ctx.gene_index.get(sym)
                    if gi is None or not isinstance(vals, (list, tuple)):
                        continue
                    if loeuf_col < len(vals) and vals[loeuf_col] is not None:
                        try:
                            l = float(vals[loeuf_col])
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(l):
                            ess[gi] = np.clip(1.0 - l, 0.0, 1.0)

        # ---- Per-complex weight = mean member essentiality ----
        # Precompute for each gene a dict: complex_id -> weight, but that is heavy.
        # Instead, build sparse membership: for each gene, list of (complex_id, weight).
        gene_to_complex = [[] for _ in range(n_genes)]
        for cid, members in enumerate(complexes):
            w = float(ess[members].mean())
            for gi in members:
                gene_to_complex[gi].append((cid, w))

        # ---- For each perturbation, find target genes and shared complexes ----
        out = np.zeros((n_perts, n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            targets = ctx.target_indices(p)
            if not targets:
                continue
            # accumulate weight per complex across targets (a complex could contain
            # multiple targets; take max weight once)
            target_complex_weight = {}
            for t in targets:
                for cid, w in gene_to_complex[t]:
                    prev = target_complex_weight.get(cid)
                    if prev is None or w > prev:
                        target_complex_weight[cid] = w
            if not target_complex_weight:
                continue
            col = out[i, :, 0]
            for gi in range(n_genes):
                s = 0.0
                for cid, w in gene_to_complex[gi]:
                    tw = target_complex_weight.get(cid)
                    if tw is not None:
                        s += 0.5 * (w + tw)  # combined weight
                col[gi] = s

        # ensure finite
        out[~np.isfinite(out)] = 0.0
        return out
