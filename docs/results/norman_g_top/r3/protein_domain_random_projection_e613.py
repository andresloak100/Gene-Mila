import numpy as np
from genemila.features.api import Feature, register


@register
class ProteinDomainRandomProjection(Feature):
    name = "protein_domain_random_projection_e613"
    version = 1
    description = ("Random Gaussian projection of the concatenated binary protein-domain "
                   "vectors of gene g and the union of domains of perturbation p's targets.")
    rationale = ("Protein domains give a sparse functional signature; a fixed random projection "
                 "captures latent functional axes shared between a gene and its perturbed targets.")
    inputs = ["knowledge"]
    params = {"K": 20, "seed": 42}
    dim = 20

    def _build_domain_matrix(self, ctx, params):
        cache = ctx.cache
        key = ("pdrp_domains", params.get("seed", 42))
        if key in cache:
            return cache[key]

        seed = int(params.get("seed", 42))
        K = int(params.get("K", 20))

        # Collect protein domain annotations from gene_annotation / protein_annotation knowledge.
        # We derive a domain vocabulary from gene_sets entries that look like domain families
        # (INTERPRO / PFAM / PROSITE style) and from protein_annotation columns.
        domain_sets = {}  # gene -> set of domain ids

        # 1) gene_annotation: per-gene annotation columns (not domains), skip.
        # 2) gene_sets: use protein-domain-like collections.
        gs = ctx.knowledge("gene_sets")
        domain_prefixes = ("INTERPRO:", "PFAM:", "PROSITE:", "SMART:", "PIRSF:",
                           "PRINTS:", "SUPFAM:", "SSF:", "CDD:", "DOMAIN:")
        if isinstance(gs, dict):
            for set_name, members in gs.items():
                if not isinstance(set_name, str):
                    continue
                up = set_name.upper()
                if not any(up.startswith(pref) for pref in domain_prefixes):
                    continue
                if not isinstance(members, (list, tuple)):
                    continue
                for g in members:
                    if g in ctx.gene_index:
                        domain_sets.setdefault(g, set()).add(set_name)

        # 3) protein_annotation: use compartment / feature flags as pseudo-domains.
        pa = ctx.knowledge("protein_annotation")
        if isinstance(pa, dict):
            cols = pa.get("columns", [])
            genes = pa.get("genes", {})
            if isinstance(cols, list) and isinstance(genes, dict):
                # flag columns only (0/1), excluding numeric lengths
                flag_cols = [c for c in cols if c not in (
                    "protein_length", "signal_peptide_length", "n_transmembrane")]
                for sym, vals in genes.items():
                    if sym not in ctx.gene_index or not isinstance(vals, (list, tuple)):
                        continue
                    for c, v in zip(cols, vals):
                        if c not in flag_cols:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if fv > 0.5:
                            domain_sets.setdefault(sym, set()).add("PA:" + str(c))

        # 4) targets dict: target->list of genes, treat as pathway-like domain signatures
        tg = ctx.knowledge("targets")
        if isinstance(tg, dict):
            for key, members in tg.items():
                if isinstance(members, (list, tuple)):
                    tag = "TG:" + str(key)
                    for g in members:
                        if g in ctx.gene_index:
                            domain_sets.setdefault(g, set()).add(tag)

        # Build vocabulary
        vocab = set()
        for s in domain_sets.values():
            vocab.update(s)
        vocab = sorted(vocab)
        n_dom = len(vocab)
        dom_index = {d: i for i, d in enumerate(vocab)}

        n_genes = ctx.n_genes
        if n_dom == 0:
            # Degenerate: no domain info. Use a single constant column.
            mat = np.zeros((n_genes, 1), dtype=np.float64)
            proj = np.zeros((K, 2), dtype=np.float64)
            cache[key] = (mat, proj, K)
            return cache[key]

        mat = np.zeros((n_genes, n_dom), dtype=np.float64)
        for g, s in domain_sets.items():
            gi = ctx.gene_index.get(g)
            if gi is None:
                continue
            cols = [dom_index[d] for d in s if d in dom_index]
            if cols:
                mat[gi, cols] = 1.0

        # Fixed random Gaussian projection: (K x 2*n_dom)
        rng = np.random.RandomState(seed)
        proj = rng.randn(K, 2 * n_dom) / np.sqrt(2 * n_dom)

        cache[key] = (mat, proj, K)
        return cache[key]

    def compute(self, ctx, perts, params):
        K = int(params.get("K", 20))
        mat, proj, Kp = self._build_domain_matrix(ctx, params)
        K = Kp
        n_genes = ctx.n_genes
        n_dom = mat.shape[1]
        out = np.zeros((len(perts), n_genes, K), dtype=np.float64)

        for i, p in enumerate(perts):
            targets = ctx.target_indices(p)
            if targets:
                union = mat[targets].max(axis=0)
            else:
                union = np.zeros(n_dom, dtype=np.float64)
            # concatenate gene vector and union vector
            concat = np.concatenate([mat, np.broadcast_to(union, (n_genes, n_dom))], axis=1)
            out[i] = concat @ proj.T

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
