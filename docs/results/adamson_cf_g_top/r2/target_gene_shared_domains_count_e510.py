import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneSharedDomainsCountE510(Feature):
    name = "target_gene_shared_domains_count_e510"
    version = 1
    description = "Number of shared protein domains between the perturbation target and gene g."
    rationale = (
        "Genes sharing protein domains with the perturbation target may belong to "
        "shared regulatory pathways or functional modules, leading to coordinated "
        "expression changes after perturbation."
    )
    inputs = ["protein_annotation", "target_indices"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        pa = ctx.knowledge("protein_annotation")
        if not pa or "genes" not in pa or "columns" not in pa:
            return out

        columns = list(pa["columns"])
        genes_map = pa["genes"]

        # Identify domain-related columns. protein_annotation columns are numeric
        # features/flags; domain membership is not guaranteed to be present.
        # We treat any per-gene numeric annotation column as a "domain-like" feature
        # and count co-occurrence of nonzero entries between target and gene.
        # Prefer explicit domain columns if they exist.
        domain_cols = []
        for j, c in enumerate(columns):
            lc = str(c).lower()
            if "domain" in lc or "pfam" in lc or "interpro" in lc:
                domain_cols.append(j)

        # Build a per-gene annotation matrix over the domain columns (or all if none).
        use_cols = domain_cols if domain_cols else list(range(len(columns)))
        n_cols = len(use_cols)

        # Map gene -> row vector of annotation values
        ann = {}
        for g, vals in genes_map.items():
            if vals is None:
                continue
            v = np.zeros(n_cols, dtype=float)
            for k, j in enumerate(use_cols):
                try:
                    x = vals[j]
                except (IndexError, TypeError):
                    x = None
                if x is None:
                    continue
                try:
                    v[k] = float(x)
                except (TypeError, ValueError):
                    v[k] = 0.0
            ann[g] = v

        # Binary presence signature for domain co-occurrence
        sig = {g: (v > 0).astype(float) for g, v in ann.items()}

        # Precompute target signatures
        target_sigs = {}
        for p in perts:
            tg = ctx.target_genes(p)
            if not tg:
                target_sigs[p] = None
                continue
            # Use first target gene available in annotation
            tsig = None
            for t in tg:
                if t in sig:
                    tsig = sig[t]
                    break
            target_sigs[p] = tsig

        # Map gene index -> gene symbol
        genes = ctx.genes

        for i, p in enumerate(perts):
            tsig = target_sigs.get(p)
            if tsig is None:
                continue
            row = out[i, :, 0]
            for gi, g in enumerate(genes):
                gs = sig.get(g)
                if gs is None:
                    continue
                row[gi] = float(np.dot(tsig, gs))

        return out
