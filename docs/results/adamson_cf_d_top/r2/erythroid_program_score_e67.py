import numpy as np
from genemila.features.api import Feature, register


@register
class ErythroidProgramScore(Feature):
    name = "erythroid_program_score_e67"
    version = 1
    description = (
        "Per-gene continuous score: fraction of curated erythroid/hemoglobin-related "
        "gene sets that contain the gene."
    )
    rationale = (
        "Erythroid/hemoglobin genes are coordinately regulated; a continuous score "
        "captures the strength of this program and predicts larger expression changes."
    )
    inputs = ["gene_sets"]
    params = {"min_sets": 5}
    dim = 1

    _KEYWORDS = (
        "erythroid", "hemoglobin", "haemoglobin", "heme", "haem",
        "oxygen transport", "carbon dioxide transport", "gata1", "nfe2",
    )

    def _matches(self, name):
        low = str(name).lower()
        for kw in self._KEYWORDS:
            if kw in low:
                return True
        return False

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        score = np.zeros(n_genes, dtype=float)

        cache_key = ("erythroid_program_score_e67", int(params.get("min_sets", 5)))
        cached = ctx.cache.get(cache_key)
        if cached is not None:
            score = cached
        else:
            gs = ctx.knowledge("gene_sets")
            if gs:
                sets = gs
                if isinstance(gs, dict) and "gene_sets" in gs and isinstance(gs["gene_sets"], dict):
                    sets = gs["gene_sets"]

                selected = []
                if isinstance(sets, dict):
                    for name, members in sets.items():
                        if self._matches(name):
                            selected.append(members)
                elif isinstance(sets, (list, tuple)):
                    for entry in sets:
                        if isinstance(entry, dict):
                            name = entry.get("name", entry.get("set", ""))
                            members = entry.get("genes", entry.get("members", []))
                        elif isinstance(entry, (list, tuple)) and len(entry) == 2:
                            name, members = entry
                        else:
                            continue
                        if self._matches(name):
                            selected.append(members)

                min_sets = int(params.get("min_sets", 5))
                if len(selected) >= min_sets and len(selected) > 0:
                    counts = np.zeros(n_genes, dtype=float)
                    for members in selected:
                        if not members:
                            continue
                        for g in members:
                            idx = ctx.gene_index.get(g)
                            if idx is not None:
                                counts[idx] += 1.0
                    score = counts / float(len(selected))

            ctx.cache[cache_key] = score

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = score[None, :]
        return out
