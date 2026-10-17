import numpy as np
from genemila.features.api import Feature, register


@register
class ComplexPartnerAvgResponseE154(Feature):
    name = "complex_partner_avg_response_e154"
    version = 1
    description = ("Average leave-one-out delta response of genes sharing a protein complex "
                   "with gene g, computed per perturbation.")
    rationale = ("Proteins in the same complex are functionally coupled; perturbing one member "
                 "may affect expression of co-members via feedback/compensatory mechanisms, so "
                 "the mean response of complex partners is predictive of g's response.")
    inputs = ["train_delta", "knowledge"]
    params = {"complex_source": "protein_annotation"}
    dim = 1

    def _build_complex_partners(self, ctx, params):
        """Return list-of-lists: partner gene indices for each gene index."""
        cache = ctx.cache
        key = ("complex_partners_e154", params.get("complex_source", "protein_annotation"))
        if key in cache:
            return cache[key]

        n = ctx.n_genes
        partners = [[] for _ in range(n)]

        # Build complex membership from protein_annotation compartments as a proxy:
        # genes sharing the same membrane/secretory complex compartment are grouped.
        # More precisely, use gene_sets whose names suggest complexes.
        complex_sets = []
        gs = ctx.knowledge("gene_sets")
        if isinstance(gs, dict):
            for name, members in gs.items():
                lname = name.lower()
                if ("complex" in lname) or ("corum" in lname) or ("complexes" in lname):
                    if isinstance(members, (list, tuple)):
                        complex_sets.append(members)

        # Fallback: use protein_annotation compartments (membrane + ER + secreted grouping)
        if not complex_sets:
            pa = ctx.knowledge("protein_annotation")
            if isinstance(pa, dict) and "genes" in pa and "columns" in pa:
                cols = pa["columns"]
                genes_tbl = pa["genes"]
                try:
                    i_mem = cols.index("membrane")
                except ValueError:
                    i_mem = None
                try:
                    i_er = cols.index("endoplasmic_reticulum")
                except ValueError:
                    i_er = None
                try:
                    i_sec = cols.index("secreted")
                except ValueError:
                    i_sec = None
                group_members = []
                for sym, vals in genes_tbl.items():
                    if sym not in ctx.gene_index or vals is None:
                        continue
                    try:
                        flags = []
                        if i_mem is not None and vals[i_mem] == 1:
                            flags.append("mem")
                        if i_er is not None and vals[i_er] == 1:
                            flags.append("er")
                        if i_sec is not None and vals[i_sec] == 1:
                            flags.append("sec")
                    except (IndexError, TypeError):
                        continue
                    if flags:
                        group_members.append((tuple(sorted(flags)), ctx.gene_index[sym]))
                # group by flag signature
                from collections import defaultdict
                groups = defaultdict(list)
                for sig, gi in group_members:
                    groups[sig].append(gi)
                for members in groups.values():
                    if len(members) > 1:
                        complex_sets.append([ctx.genes[gi] for gi in members])

        # Convert complex sets to partner lists
        for members in complex_sets:
            idxs = [ctx.gene_index[s] for s in members if s in ctx.gene_index]
            if len(idxs) < 2:
                continue
            for gi in idxs:
                for gj in idxs:
                    if gj != gi:
                        partners[gi].append(gj)

        # Deduplicate
        for gi in range(n):
            if partners[gi]:
                partners[gi] = sorted(set(partners[gi]))

        cache[key] = partners
        return partners

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)
        partners = self._build_complex_partners(ctx, params)

        # Precompute per-gene partner index arrays
        partner_arrays = [np.asarray(pl, dtype=int) if pl else None for pl in partners]

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)  # (n_train, n_genes)
            if d.shape[0] == 0:
                continue
            mean_d = d.mean(axis=0)  # (n_genes,)
            for gi in range(n):
                pa = partner_arrays[gi]
                if pa is None or pa.size == 0:
                    out[i, gi, 0] = 0.0
                else:
                    out[i, gi, 0] = float(mean_d[pa].mean())

        # Ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
