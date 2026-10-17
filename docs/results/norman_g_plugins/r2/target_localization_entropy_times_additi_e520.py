import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLocalizationEntropyTimesAdditiveE520(Feature):
    name = "target_localization_entropy_times_additi_e520"
    version = 1
    description = ("Product of additive_response and the Shannon entropy of subcellular "
                   "localization flags (from protein_annotation) across p's target genes.")
    rationale = ("Targets localizing to diverse compartments may have distinct effects; "
                 "entropy quantifies this diversity and modulates the additive response.")
    inputs = ["control_cells", "protein_annotation", "train_delta"]
    params = {}
    dim = 1

    _LOC_FLAGS = ["secreted", "membrane", "endoplasmic_reticulum", "golgi",
                  "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome"]

    def _get_annotation(self, ctx):
        cache = ctx.cache
        key = "_loc_entropy_annot"
        if key in cache:
            return cache[key]

        ann = ctx.knowledge("protein_annotation")
        if ann is None or "genes" not in ann:
            cache[key] = None
            return None

        cols = ann.get("columns", [])
        flag_idx = []
        for f in self._LOC_FLAGS:
            if f in cols:
                flag_idx.append(cols.index(f))
        flag_idx = np.array(flag_idx, dtype=int)
        n_flags = len(flag_idx)

        genes_map = ann["genes"]
        n_genes = ctx.n_genes
        loc = np.zeros((n_genes, n_flags), dtype=float)
        has = np.zeros(n_genes, dtype=bool)

        if n_flags > 0:
            max_idx = int(flag_idx.max())
            for g, gi in ctx.gene_index.items():
                vals = genes_map.get(g)
                if vals is None:
                    continue
                try:
                    arr = np.asarray(vals, dtype=float)
                except (TypeError, ValueError):
                    continue
                if arr.ndim != 1 or arr.size <= max_idx:
                    continue
                sub = arr[flag_idx]
                sub = np.where(np.isfinite(sub), sub, 0.0)
                loc[gi, :] = sub
                has[gi] = True

        cache[key] = (loc, has)
        return cache[key]

    def _entropy_for_targets(self, loc, target_idx):
        if len(target_idx) == 0 or loc.shape[1] == 0:
            return 0.0
        counts = loc[target_idx, :].sum(axis=0)
        total = counts.sum()
        if total <= 0:
            return 0.0
        p = counts / total
        p = p[p > 0]
        return float(-(p * np.log(p)).sum())

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        annot = self._get_annotation(ctx)
        if annot is None:
            return out
        loc, _has = annot

        try:
            add = ctx.feature("additive_response", perts)
        except Exception:
            add = None

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            ent = self._entropy_for_targets(loc, t_idx)

            if add is not None:
                base = np.asarray(add[i, :, 0], dtype=float)
            else:
                _, d = ctx.train_delta(exclude=p)
                base = np.zeros(ctx.n_genes, dtype=float)
                if len(t_idx) > 0 and d.shape[0] > 0:
                    base = d[:, t_idx].sum(axis=1)

            row = ent * base
            row = np.where(np.isfinite(row), row, 0.0)
            out[i, :, 0] = row

        return out
