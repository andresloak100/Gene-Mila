import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneSharedDomainCountE454(Feature):
    name = "target_gene_shared_domain_count_e454"
    version = 1
    description = "Number of shared protein domains between target and gene g, using UniProt annotations."
    rationale = (
        "Protein domains are conserved functional units. Sharing domains between target and gene "
        "may indicate similar biochemical roles or interaction partners."
    )
    inputs = ["protein_annotation", "targets"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        pa = ctx.knowledge("protein_annotation")
        if not pa:
            return out

        genes_map = pa.get("genes", {}) or {}
        columns = pa.get("columns", []) or []
        n_cols = len(columns)

        # Identify domain-like flag columns: 0/1 flags describing where the protein is placed
        # or structural features. We use the compartment/location flags and structural flags.
        # The columns list starts with protein_length, has_signal_peptide, signal_peptide_length,
        # n_transmembrane, then 0/1 flags (secreted, membrane, ...).
        # Shared "domains" here = shared binary annotation flags.
        flag_start = 0
        for i, c in enumerate(columns):
            if c == "n_transmembrane":
                flag_start = i + 1
                break
        else:
            flag_start = 4
        flag_cols = list(range(flag_start, n_cols))

        # Build per-gene boolean flag vector (only flag columns)
        n_flags = len(flag_cols)
        gene_flags = {}
        for g, vals in genes_map.items():
            if vals is None:
                continue
            vec = np.zeros(n_flags, dtype=bool)
            for j, ci in enumerate(flag_cols):
                if ci < len(vals):
                    v = vals[ci]
                    if v is not None:
                        try:
                            vec[j] = bool(float(v) > 0.5)
                        except (TypeError, ValueError):
                            vec[j] = False
            gene_flags[g] = vec

        # Cache target flag vectors by perturbation id
        cache = ctx.cache
        key = "_e454_target_flags"
        if key not in cache:
            cache[key] = {}

        tflags_cache = cache[key]

        for i, p in enumerate(perts):
            if p not in tflags_cache:
                tvec = None
                tgenes = ctx.target_genes(p)
                for tg in tgenes:
                    if tg in gene_flags:
                        tvec = gene_flags[tg]
                        break
                tflags_cache[p] = tvec
            tvec = tflags_cache[p]
            if tvec is None:
                continue

            for g, gvec in gene_flags.items():
                gi = ctx.gene_index.get(g)
                if gi is None:
                    continue
                out[i, gi, 0] = float(np.count_nonzero(tvec & gvec))

        return out
