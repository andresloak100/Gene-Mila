import numpy as np
from genemila.features.api import Feature, register


@register
class RandomProjectionPriorFeatures(Feature):
    name = "random_projection_prior_features_e301"
    version = 1
    description = (
        "Random projection of standardized prior-knowledge features "
        "(gene annotation, protein annotation, constraint, network distances) "
        "into a low-dimensional latent space per (perturbation, gene) row."
    )
    rationale = (
        "Many weak prior-knowledge signals may jointly encode latent structure "
        "predictive of perturbation response; a fixed random projection aggregates "
        "them into a handful of components a linear model can exploit."
    )
    inputs = [
        "control_mean",
        "control_std",
        "gene_annotation",
        "protein_annotation",
        "gene_constraint",
        "ppi_network",
        "prior_network",
        "targets",
    ]
    params = {"n_components": 10, "seed": 42}
    dim = 10

    # ------------------------------------------------------------------ #
    def _build_base_matrix(self, ctx):
        """Return (n_genes, n_base) standardized prior-knowledge matrix + mask."""
        cache = ctx.cache
        if "rp_base" in cache:
            return cache["rp_base"]

        n_genes = ctx.n_genes
        genes = ctx.genes
        gi = ctx.gene_index

        cols = []

        # ---- gene annotation numeric columns ----
        ga = ctx.knowledge("gene_annotation")
        if ga is not None and isinstance(ga, dict) and "genes" in ga:
            columns = ga.get("columns", [])
            wanted = [
                "gene_span_kb",
                "n_transcripts",
                "n_exons",
                "transcript_length",
                "cds_length",
                "utr5_length",
                "utr3_length",
                "intron_length_kb",
                "gc_cds",
                "gc_utr3",
                "gc_promoter",
                "cpg_oe_promoter",
                "n_upstream_atg",
                "nearest_tss_kb",
                "n_tss_within_100kb",
            ]
            idxs = [columns.index(w) for w in wanted if w in columns]
            if idxs:
                arr = np.full((n_genes, len(idxs)), np.nan, dtype=float)
                gdict = ga["genes"]
                for g in genes:
                    j = gi[g]
                    vals = gdict.get(g)
                    if vals is None:
                        continue
                    for k, ci in enumerate(idxs):
                        v = vals[ci] if ci < len(vals) else None
                        if v is not None:
                            try:
                                arr[j, k] = float(v)
                            except (TypeError, ValueError):
                                pass
                cols.append(arr)

        # ---- protein annotation ----
        pa = ctx.knowledge("protein_annotation")
        if pa is not None and isinstance(pa, dict) and "genes" in pa:
            pcols = pa.get("columns", [])
            wanted_p = [
                "protein_length",
                "has_signal_peptide",
                "signal_peptide_length",
                "n_transmembrane",
                "secreted",
                "membrane",
                "endoplasmic_reticulum",
                "golgi",
                "mitochondrion",
                "nucleus",
                "cytoplasm",
                "lysosome",
                "peroxisome",
            ]
            idxs = [pcols.index(w) for w in wanted_p if w in pcols]
            if idxs:
                arr = np.full((n_genes, len(idxs)), np.nan, dtype=float)
                gdict = pa["genes"]
                for g in genes:
                    j = gi[g]
                    vals = gdict.get(g)
                    if vals is None:
                        continue
                    for k, ci in enumerate(idxs):
                        v = vals[ci] if ci < len(vals) else None
                        if v is not None:
                            try:
                                arr[j, k] = float(v)
                            except (TypeError, ValueError):
                                pass
                cols.append(arr)

        # ---- gene constraint ----
        gc = ctx.knowledge("gene_constraint")
        if gc is not None and isinstance(gc, dict) and "genes" in gc:
            ccols = gc.get("columns", [])
            wanted_c = ["oe_lof_upper", "pLI", "oe_lof", "oe_mis", "syn_z"]
            idxs = [ccols.index(w) for w in wanted_c if w in ccols]
            if idxs:
                arr = np.full((n_genes, len(idxs)), np.nan, dtype=float)
                gdict = gc["genes"]
                for g in genes:
                    j = gi[g]
                    vals = gdict.get(g)
                    if vals is None:
                        continue
                    for k, ci in enumerate(idxs):
                        v = vals[ci] if ci < len(vals) else None
                        if v is not None:
                            try:
                                arr[j, k] = float(v)
                            except (TypeError, ValueError):
                                pass
                cols.append(arr)

        # ---- control mean / std ----
        cm = np.asarray(ctx.control_mean, dtype=float).reshape(-1, 1)
        cs = np.asarray(ctx.control_std, dtype=float).reshape(-1, 1)
        cols.append(cm)
        cols.append(cs)

        # ---- network degree features (PPI + prior) ----
        deg_ppi = np.zeros(n_genes, dtype=float)
        ppi = ctx.knowledge("ppi_network")
        if ppi is not None and isinstance(ppi, (list, tuple)):
            for e in ppi:
                try:
                    a, b = e[0], e[1]
                except Exception:
                    continue
                if a in gi:
                    deg_ppi[gi[a]] += 1.0
                if b in gi:
                    deg_ppi[gi[b]] += 1.0
        cols.append(deg_ppi.reshape(-1, 1))

        deg_prior = np.zeros(n_genes, dtype=float)
        pn = ctx.knowledge("prior_network")
        if pn is not None and isinstance(pn, (list, tuple)):
            for e in pn:
                try:
                    a, b = e[0], e[1]
                except Exception:
                    continue
                if a in gi:
                    deg_prior[gi[a]] += 1.0
                if b in gi:
                    deg_prior[gi[b]] += 1.0
        cols.append(deg_prior.reshape(-1, 1))

        if not cols:
            base = np.zeros((n_genes, 1), dtype=float)
        else:
            base = np.concatenate(cols, axis=1)

        # standardize each column (nan-aware)
        mu = np.nanmean(base, axis=0)
        sd = np.nanstd(base, axis=0)
        sd[~np.isfinite(sd) | (sd < 1e-8)] = 1.0
        mu[~np.isfinite(mu)] = 0.0
        z = (base - mu) / sd
        z[~np.isfinite(z)] = 0.0

        cache["rp_base"] = z
        return z

    # ------------------------------------------------------------------ #
    def compute(self, ctx, perts, params):
        n_comp = int(params.get("n_components", self.params["n_components"]))
        seed = int(params.get("seed", self.params["seed"]))
        n_comp = max(1, n_comp)

        base = self._build_base_matrix(ctx)  # (n_genes, n_base)
        n_base = base.shape[1]

        rng = np.random.RandomState(seed)
        proj = rng.normal(0.0, 1.0 / np.sqrt(max(n_base, 1)),
                          size=(n_base, n_comp)).astype(float)

        gene_feat = base.dot(proj)  # (n_genes, n_comp)

        # target-level prior features: constraint of the target gene
        gc = ctx.knowledge("gene_constraint")
        gi = ctx.gene_index
        target_loeuf = np.zeros(ctx.n_genes, dtype=float)
        if gc is not None and isinstance(gc, dict) and "genes" in gc:
            ccols = gc.get("columns", [])
            if "oe_lof_upper" in ccols:
                ci = ccols.index("oe_lof_upper")
                for g in ctx.genes:
                    vals = gc["genes"].get(g)
                    if vals is not None and ci < len(vals) and vals[ci] is not None:
                        try:
                            target_loeuf[gi[g]] = float(vals[ci])
                        except (TypeError, ValueError):
                            pass

        out = np.zeros((len(perts), ctx.n_genes, n_comp), dtype=float)
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p) or []
            out[i] = gene_feat
            if tgt_idx:
                tgt_loeuf = np.mean([target_loeuf[t] for t in tgt_idx])
                tgt_loeuf = float(tgt_loeuf) if np.isfinite(tgt_loeuf) else 0.0
                mod = np.random.RandomState(seed).normal(0.0, 0.1, size=n_comp)
                out[i] += 0.05 * tgt_loeuf * mod.reshape(1, -1)

        out[~np.isfinite(out)] = 0.0
        return out
