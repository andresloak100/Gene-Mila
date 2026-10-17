import numpy as np
from genemila.features.api import Feature, register


@register
class RandomProjectionPriorKnowledgeE328(Feature):
    name = "random_projection_prior_knowledge_e328"
    version = 1
    description = ("Random projection of curated gene-level prior-knowledge features "
                   "(gene/protein annotation, network degree, gene-set membership) to "
                   "n_components dims per gene.")
    rationale = ("A dense low-dimensional random projection of many safe, gene-level "
                 "prior features captures latent structure not captured by individual "
                 "features, without leakage since it is computed per gene.")
    inputs = ["knowledge"]
    params = {"n_components": 20, "random_seed": 42}
    dim = 20

    def _build_feature_matrix(self, ctx):
        cache = ctx.cache
        key = "_e328_featmat"
        if key in cache:
            return cache[key]

        genes = list(ctx.genes)
        n_genes = len(genes)
        gi = ctx.gene_index
        cols = []

        def add_col(vec):
            v = np.asarray(vec, dtype=np.float64).reshape(-1)
            if v.shape[0] != n_genes:
                return
            v = np.where(np.isfinite(v), v, np.nan)
            cols.append(v)

        # ---- gene_annotation ----
        ga = ctx.knowledge("gene_annotation")
        if isinstance(ga, dict) and isinstance(ga.get("genes"), dict):
            gtab = ga["genes"]
            columns = ga.get("columns", [])
            # gather numeric columns
            ncol = None
            sample = None
            for g in genes:
                if g in gtab:
                    sample = gtab[g]
                    break
            if sample is not None:
                ncol = len(sample)
                mat = np.full((n_genes, ncol), np.nan, dtype=np.float64)
                for i, g in enumerate(genes):
                    row = gtab.get(g)
                    if row is None:
                        continue
                    for j in range(min(ncol, len(row))):
                        try:
                            val = row[j]
                            if val is None:
                                continue
                            fv = float(val)
                            mat[i, j] = fv
                        except (TypeError, ValueError):
                            mat[i, j] = np.nan
                for j in range(ncol):
                    col = mat[:, j]
                    # skip amino-acid fraction block if all nan (handled by nan->0 anyway)
                    add_col(col)

        # ---- protein_annotation ----
        pa = ctx.knowledge("protein_annotation")
        if isinstance(pa, dict) and isinstance(pa.get("genes"), dict):
            ptab = pa["genes"]
            sample = None
            for g in genes:
                if g in ptab:
                    sample = ptab[g]
                    break
            if sample is not None:
                ncol = len(sample)
                mat = np.full((n_genes, ncol), np.nan, dtype=np.float64)
                for i, g in enumerate(genes):
                    row = ptab.get(g)
                    if row is None:
                        continue
                    for j in range(min(ncol, len(row))):
                        try:
                            val = row[j]
                            if val is None:
                                continue
                            mat[i, j] = float(val)
                        except (TypeError, ValueError):
                            mat[i, j] = np.nan
                for j in range(ncol):
                    add_col(mat[:, j])

        # ---- gene_constraint ----
        gc = ctx.knowledge("gene_constraint")
        if isinstance(gc, dict) and isinstance(gc.get("genes"), dict):
            ctab = gc["genes"]
            sample = None
            for g in genes:
                if g in ctab:
                    sample = ctab[g]
                    break
            if sample is not None:
                ncol = len(sample)
                mat = np.full((n_genes, ncol), np.nan, dtype=np.float64)
                for i, g in enumerate(genes):
                    row = ctab.get(g)
                    if row is None:
                        continue
                    for j in range(min(ncol, len(row))):
                        try:
                            val = row[j]
                            if val is None:
                                continue
                            mat[i, j] = float(val)
                        except (TypeError, ValueError):
                            mat[i, j] = np.nan
                for j in range(ncol):
                    add_col(mat[:, j])

        # ---- PPI degree ----
        ppi = ctx.knowledge("ppi_network")
        if isinstance(ppi, list):
            deg = np.zeros(n_genes, dtype=np.float64)
            wdeg = np.zeros(n_genes, dtype=np.float64)
            for edge in ppi:
                try:
                    a, b, w = edge[0], edge[1], float(edge[2])
                except (TypeError, ValueError, IndexError):
                    continue
                ia = gi.get(a)
                ib = gi.get(b)
                if ia is not None:
                    deg[ia] += 1.0
                    wdeg[ia] += w
                if ib is not None:
                    deg[ib] += 1.0
                    wdeg[ib] += w
            add_col(deg)
            add_col(wdeg)

        # ---- prior_network degree ----
        pn = ctx.knowledge("prior_network")
        if isinstance(pn, list):
            pdeg = np.zeros(n_genes, dtype=np.float64)
            for edge in pn:
                try:
                    a, b = edge[0], edge[1]
                except (TypeError, IndexError):
                    continue
                ia = gi.get(a)
                ib = gi.get(b)
                if ia is not None:
                    pdeg[ia] += 1.0
                if ib is not None:
                    pdeg[ib] += 1.0
            add_col(pdeg)

        # ---- gene-set membership counts / sizes ----
        gs = ctx.knowledge("gene_sets")
        if isinstance(gs, dict):
            membership = np.zeros(n_genes, dtype=np.float64)
            size_sum = np.zeros(n_genes, dtype=np.float64)
            for set_name, members in gs.items():
                if not isinstance(members, (list, tuple)):
                    continue
                sz = float(len(members))
                for g in members:
                    ix = gi.get(g)
                    if ix is not None:
                        membership[ix] += 1.0
                        size_sum[ix] += sz
            add_col(membership)
            add_col(size_sum)

        # ---- transcription factor flag ----
        tf = ctx.knowledge("transcription_factors")
        if isinstance(tf, (list, tuple)):
            tfv = np.zeros(n_genes, dtype=np.float64)
            for g in tf:
                ix = gi.get(g)
                if ix is not None:
                    tfv[ix] = 1.0
            add_col(tfv)

        if not cols:
            featmat = np.zeros((n_genes, 1), dtype=np.float64)
        else:
            featmat = np.stack(cols, axis=1)

        # clean: nan -> 0, inf -> 0
        featmat = np.where(np.isfinite(featmat), featmat, 0.0)

        # drop constant columns
        std = featmat.std(axis=0)
        keep = std > 1e-12
        if np.any(keep):
            featmat = featmat[:, keep]
        else:
            featmat = np.zeros((n_genes, 1), dtype=np.float64)

        # standardize
        mu = featmat.mean(axis=0)
        sd = featmat.std(axis=0)
        sd = np.where(sd > 1e-12, sd, 1.0)
        featmat = (featmat - mu) / sd

        cache[key] = featmat
        return featmat

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_comp = int(params.get("n_components", self.params["n_components"]))
        seed = int(params.get("random_seed", self.params["random_seed"]))

        featmat = self._build_feature_matrix(ctx)
        n_feat = featmat.shape[1]

        rng = np.random.RandomState(seed)
        R = rng.normal(0.0, 1.0, size=(n_feat, n_comp))
        # scale so output has roughly unit variance per component
        R = R / np.sqrt(max(n_feat, 1))

        proj = featmat @ R  # (n_genes, n_comp)
        proj = np.where(np.isfinite(proj), proj, 0.0)

        out = np.empty((len(perts), n_genes, n_comp), dtype=np.float64)
        for i in range(len(perts)):
            out[i] = proj
        return out
