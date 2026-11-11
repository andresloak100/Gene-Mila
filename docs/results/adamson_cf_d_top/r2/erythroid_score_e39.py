import numpy as np
from genemila.features.api import Feature, register


@register
class ErythroidScoreE39(Feature):
    name = "erythroid_score_e39"
    version = 1
    description = (
        "Graded erythroid-program score per gene: weighted count of erythroid-related "
        "gene-set memberships (weighted by inverse set size), standardized across genes."
    )
    rationale = (
        "Erythroid genes share a regulatory program and respond similarly to perturbations; "
        "a graded membership score captures this better than binary membership."
    )
    inputs = ["gene_sets"]
    params = {"set_keywords": ["erythro", "hemoglobin", "heme", "carbon dioxide"]}
    dim = 1

    def _matches(self, name, keywords):
        lname = name.lower()
        for kw in keywords:
            if kw.lower() in lname:
                return True
        return False

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        keywords = params.get(
            "set_keywords", ["erythro", "hemoglobin", "heme", "carbon dioxide"]
        )
        if isinstance(keywords, str):
            keywords = [keywords]
        keywords = [str(k) for k in keywords]

        cache = ctx.cache
        key = ("erythroid_score_e39", tuple(keywords))
        if key in cache:
            score = cache[key]
        else:
            score = np.zeros(n_genes, dtype=np.float64)
            gs = ctx.knowledge("gene_sets")
            items = []
            if isinstance(gs, dict):
                items = list(gs.items())
            elif isinstance(gs, (list, tuple)):
                for entry in gs:
                    if isinstance(entry, dict):
                        for k, v in entry.items():
                            items.append((k, v))
                    elif isinstance(entry, (list, tuple)) and len(entry) == 2:
                        items.append((entry[0], entry[1]))

            for name, members in items:
                if not isinstance(name, str) or not self._matches(name, keywords):
                    continue
                if not members:
                    continue
                try:
                    n_members = len(members)
                except TypeError:
                    continue
                if n_members <= 0:
                    continue
                w = 1.0 / np.sqrt(float(n_members))
                idx = []
                for g in members:
                    j = ctx.gene_index.get(g)
                    if j is not None:
                        idx.append(j)
                if idx:
                    score[np.asarray(idx, dtype=np.int64)] += w

            mu = float(score.mean())
            sd = float(score.std())
            if sd > 1e-12:
                score = (score - mu) / sd
            else:
                score = score - mu
            cache[key] = score

        out = np.empty((len(perts), n_genes, 1), dtype=np.float64)
        out[:, :, 0] = score[np.newaxis, :]
        out[~np.isfinite(out)] = 0.0
        return out
