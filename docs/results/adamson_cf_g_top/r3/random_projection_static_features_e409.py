import numpy as np
from genemila.features.api import Feature, register


@register
class RandomProjectionStaticFeatures(Feature):
    name = "random_projection_static_features_e409"
    version = 1
    description = ("A single random Gaussian projection of concatenated static gene and "
                   "target features (annotation, protein, constraint, network degree).")
    rationale = ("Many weak static features can be summarised into one regularized scalar via a "
                 "fixed random projection, capturing latent structure without manual engineering.")
    inputs = ["knowledge", "control_mean"]
    params = {"seed": 42, "n_components": 1}
    dim = 1

    def _build_gene_matrix(self, ctx, params):
        cache = ctx.cache
        key = ("rp_static_e409", params.get("seed", 42))
        if key in cache:
            return cache[key]

        genes = ctx.genes
        n = ctx.n_genes
        gidx = ctx.gene_index

        # Collect feature columns as dicts gene->value, then align.
        columns = []

        def add_column(mapping, default=0.0):
            col = np.full(n, default, dtype=np.float64)
            for g, v in mapping.items():
                j = gidx.get(g)
                if j is not None:
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        col[j] = fv
            columns.append(col)

        # Gene annotation
        ann = ctx.knowledge("gene_annotation")
        if ann and "genes" in ann and "columns" in ann:
            cols = ann["columns"]
            gd = ann["genes"]
            # pick numeric columns
            for ci, cname in enumerate(cols):
                mapping = {}
                for g, vals in gd.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    mapping[g] = v
                add_column(mapping)

        # Protein annotation
        prot = ctx.knowledge("protein_annotation")
        if prot and "genes" in prot and "columns" in prot:
            cols = prot["columns"]
            gd = prot["genes"]
            for ci, cname in enumerate(cols):
                mapping = {}
                for g, vals in gd.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    mapping[g] = v
                add_column(mapping)

        # Gene constraint
        cons = ctx.knowledge("gene_constraint")
        if cons and "genes" in cons and "columns" in cons:
            cols = cons["columns"]
            gd = cons["genes"]
            for ci, cname in enumerate(cols):
                mapping = {}
                for g, vals in gd.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    mapping[g] = v
                add_column(mapping)

        # Network degrees
        ppi = ctx.knowledge("ppi_network")
        if ppi:
            deg = {}
            for edge in ppi:
                if len(edge) < 2:
                    continue
                a, b = edge[0], edge[1]
                deg[a] = deg.get(a, 0.0) + 1.0
                deg[b] = deg.get(b, 0.0) + 1.0
            add_column(deg)

        prior = ctx.knowledge("prior_network")
        if prior:
            deg = {}
            for edge in prior:
                if len(edge) < 2:
                    continue
                a, b = edge[0], edge[1]
                deg[a] = deg.get(a, 0.0) + 1.0
                deg[b] = deg.get(b, 0.0) + 1.0
            add_column(deg)

        # Pathway membership count
        gsets = ctx.knowledge("gene_sets")
        if gsets:
            counts = {}
            for _name, members in gsets.items():
                if not isinstance(members, (list, tuple)):
                    continue
                for g in members:
                    counts[g] = counts.get(g, 0.0) + 1.0
            add_column(counts)

        # TF membership
        tfs = ctx.knowledge("transcription_factors")
        if tfs:
            tfs = set(tfs)
            add_column({g: 1.0 for g in genes if g in tfs})

        # control_mean and control_std as static features
        cm = np.asarray(ctx.control_mean, dtype=np.float64)
        cs = np.asarray(ctx.control_std, dtype=np.float64)
        cm = np.where(np.isfinite(cm), cm, 0.0)
        cs = np.where(np.isfinite(cs), cs, 0.0)
        columns.append(cm)
        columns.append(cs)

        if not columns:
            mat = np.zeros((n, 1), dtype=np.float64)
        else:
            mat = np.stack(columns, axis=1)

        # standardize columns
        mu = mat.mean(axis=0)
        sd = mat.std(axis=0)
        sd[sd < 1e-8] = 1.0
        mat = (mat - mu) / sd
        mat = np.where(np.isfinite(mat), mat, 0.0)

        # fixed random projection
        seed = int(params.get("seed", 42))
        rng = np.random.RandomState(seed)
        w = rng.randn(mat.shape[1]).astype(np.float64)
        proj = mat @ w  # (n_genes,)

        cache[key] = proj
        return proj

    def compute(self, ctx, perts, params):
        proj = self._build_gene_matrix(ctx, params)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=np.float64)
        # target projection: average over target genes' projections
        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if tgt:
                tval = float(np.mean(proj[tgt]))
            else:
                tval = 0.0
            out[i, :, 0] = proj + tval
        out = np.where(np.isfinite(out), out, 0.0)
        return out
