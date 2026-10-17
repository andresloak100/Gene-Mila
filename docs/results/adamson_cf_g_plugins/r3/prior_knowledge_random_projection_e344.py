import numpy as np
from genemila.features.api import Feature, register


@register
class PriorKnowledgeRandomProjectionE344(Feature):
    name = "prior_knowledge_random_projection_e344"
    version = 1
    description = ("Random projection of a concatenated vector of selected prior-knowledge "
                   "features (gene annotation, protein annotation, network degrees) to 10 dims.")
    rationale = ("High-dimensional prior knowledge may contain latent structure not captured by "
                 "individual features; random projections provide a regularized summary of broad "
                 "biological context.")
    inputs = ["knowledge"]
    params = {"n_components": 10, "random_state": 42}
    dim = 10

    def _build_gene_matrix(self, ctx):
        n = ctx.n_genes
        cols = []

        def add_col(name, values):
            vals = np.full(n, np.nan, dtype=np.float64)
            for g, v in values.items():
                idx = ctx.gene_index.get(g)
                if idx is not None and v is not None:
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vals[idx] = fv
            cols.append((name, vals))

        # Gene annotation
        ga = ctx.knowledge("gene_annotation")
        if ga is not None and "genes" in ga:
            gcols = ga.get("columns", [])
            ggenes = ga.get("genes", {})
            # pick numeric columns (skip amino-acid fractions to limit dims but keep a few)
            wanted = ["gene_span_kb", "n_transcripts", "n_exons", "transcript_length",
                      "cds_length", "utr5_length", "utr3_length", "intron_length_kb",
                      "gc_cds", "gc_utr3", "gc_promoter", "cpg_oe_promoter",
                      "n_upstream_atg", "nearest_tss_kb", "n_tss_within_100kb"]
            idx_map = {c: i for i, c in enumerate(gcols)}
            for w in wanted:
                if w in idx_map:
                    ci = idx_map[w]
                    vals = {}
                    for g, row in ggenes.items():
                        if row is not None and ci < len(row):
                            vals[g] = row[ci]
                    add_col("ga_" + w, vals)
            # bidirectional / neighbours counts
            bid = ga.get("bidirectional", {}) or {}
            vals = {}
            for g, lst in bid.items():
                try:
                    vals[g] = len(lst) if lst is not None else 0.0
                except TypeError:
                    vals[g] = np.nan
            add_col("ga_n_bidirectional", vals)
            nb = ga.get("neighbours", {}) or {}
            vals = {}
            for g, lst in nb.items():
                try:
                    vals[g] = len(lst) if lst is not None else 0.0
                except TypeError:
                    vals[g] = np.nan
            add_col("ga_n_neighbours", vals)

        # Gene constraint
        gc = ctx.knowledge("gene_constraint")
        if gc is not None and "genes" in gc:
            gcols = gc.get("columns", [])
            ggenes = gc.get("genes", {})
            idx_map = {c: i for i, c in enumerate(gcols)}
            for w in ["oe_lof_upper", "pLI", "oe_lof", "oe_mis", "syn_z", "mis_z", "lof_z"]:
                if w in idx_map:
                    ci = idx_map[w]
                    vals = {}
                    for g, row in ggenes.items():
                        if row is not None and ci < len(row):
                            vals[g] = row[ci]
                    add_col("gc_" + w, vals)

        # Protein annotation
        pa = ctx.knowledge("protein_annotation")
        if pa is not None and "genes" in pa:
            pcols = pa.get("columns", [])
            pgenes = pa.get("genes", {})
            idx_map = {c: i for i, c in enumerate(pcols)}
            for w in ["protein_length", "has_signal_peptide", "signal_peptide_length",
                      "n_transmembrane", "secreted", "membrane", "endoplasmic_reticulum",
                      "golgi", "mitochondrion", "nucleus", "cytoplasm", "lysosome",
                      "peroxisome"]:
                if w in idx_map:
                    ci = idx_map[w]
                    vals = {}
                    for g, row in pgenes.items():
                        if row is not None and ci < len(row):
                            vals[g] = row[ci]
                    add_col("pa_" + w, vals)

        # PPI degree
        ppi = ctx.knowledge("ppi_network")
        if ppi is not None:
            deg = np.zeros(n, dtype=np.float64)
            wsum = np.zeros(n, dtype=np.float64)
            for e in ppi:
                try:
                    a, b, w = e[0], e[1], float(e[2])
                except (TypeError, ValueError, IndexError):
                    continue
                ia = ctx.gene_index.get(a)
                ib = ctx.gene_index.get(b)
                if ia is not None:
                    deg[ia] += 1.0
                    wsum[ia] += w
                if ib is not None:
                    deg[ib] += 1.0
                    wsum[ib] += w
            cols.append(("ppi_degree", deg))
            cols.append(("ppi_wsum", wsum))

        # prior network degree
        pn = ctx.knowledge("prior_network")
        if pn is not None:
            deg = np.zeros(n, dtype=np.float64)
            for e in pn:
                try:
                    a, b = e[0], e[1]
                except (TypeError, IndexError):
                    continue
                ia = ctx.gene_index.get(a)
                ib = ctx.gene_index.get(b)
                if ia is not None:
                    deg[ia] += 1.0
                if ib is not None:
                    deg[ib] += 1.0
            cols.append(("pn_degree", deg))

        # gene sets membership count
        gs = ctx.knowledge("gene_sets")
        if gs is not None:
            cnt = np.zeros(n, dtype=np.float64)
            for _, members in gs.items():
                try:
                    for g in members:
                        idx = ctx.gene_index.get(g)
                        if idx is not None:
                            cnt[idx] += 1.0
                except TypeError:
                    continue
            cols.append(("gs_count", cnt))

        if not cols:
            return np.zeros((n, 1), dtype=np.float64)

        mat = np.column_stack([c[1] for c in cols])
        # median-impute per column
        for j in range(mat.shape[1]):
            col = mat[:, j]
            finite = np.isfinite(col)
            if finite.any():
                med = np.median(col[finite])
            else:
                med = 0.0
            col[~finite] = med
            mat[:, j] = col
        # standardize
        mu = mat.mean(axis=0)
        sd = mat.std(axis=0)
        sd[sd < 1e-8] = 1.0
        mat = (mat - mu) / sd
        return mat

    def compute(self, ctx, perts, params):
        n_comp = int(params.get("n_components", 10))
        seed = int(params.get("random_state", 42))

        cache_key = ("pk_rp_e344", n_comp, seed)
        if cache_key in ctx.cache:
            proj = ctx.cache[cache_key]
        else:
            mat = self._build_gene_matrix(ctx)
            n_genes, d = mat.shape
            rng = np.random.RandomState(seed)
            # Gaussian random projection scaled by 1/sqrt(n_comp)
            R = rng.randn(d, n_comp) / np.sqrt(n_comp)
            proj = mat @ R  # (n_genes, n_comp)
            proj = np.nan_to_num(proj, nan=0.0, posinf=0.0, neginf=0.0)
            ctx.cache[cache_key] = proj

        out = np.zeros((len(perts), ctx.n_genes, n_comp), dtype=np.float64)
        for i in range(len(perts)):
            out[i] = proj
        return out
