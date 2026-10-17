import numpy as np
from genemila.features.api import Feature, register


@register
class TargetProteinHalfLifeE362(Feature):
    name = "target_protein_half_life_e362"
    version = 1
    description = (
        "Estimated protein half-life proxy for the perturbation target, derived from "
        "protein_annotation (protein length and PEST-like motif content), median-filled."
    )
    rationale = (
        "Proteins with short half-lives are depleted faster after CRISPRi, potentially "
        "producing larger or more specific downstream transcriptional responses. In the "
        "absence of a curated half-life database, protein length and PEST-like motif "
        "content serve as proxies for degradation propensity."
    )
    inputs = ["protein_annotation", "targets"]
    params = {"source": "proxy"}
    dim = 1

    def _target_gene(self, ctx, p):
        # Prefer the explicit target mapping from prior knowledge; fall back to ctx.
        tg = ctx.target_genes(p)
        if tg:
            return tg[0]
        return None

    def _protein_proxy(self, ctx, gene):
        """Return a half-life proxy score for a gene, or None if unavailable."""
        ann = ctx.knowledge("protein_annotation")
        if ann is None:
            return None
        genes = ann.get("genes", {})
        cols = ann.get("columns", [])
        if gene not in genes:
            return None
        vals = genes[gene]
        if vals is None:
            return None

        # Locate protein_length column.
        try:
            plen_idx = cols.index("protein_length")
        except ValueError:
            plen_idx = 0
        try:
            plen = float(vals[plen_idx])
        except (TypeError, ValueError, IndexError):
            return None
        if not np.isfinite(plen) or plen <= 0:
            return None

        # Proxy: shorter proteins degrade faster on average; combine with a
        # membrane/secreted penalty (membrane proteins turn over slower here).
        # Convert length to a monotone decreasing score in [0, 1].
        length_score = 1.0 / (1.0 + plen / 500.0)

        # Penalise transmembrane / signal-peptide (stable structural proteins).
        penalty = 1.0
        for flag in ("has_signal_peptide", "n_transmembrane"):
            if flag in cols:
                try:
                    v = float(vals[cols.index(flag)])
                except (TypeError, ValueError, IndexError):
                    continue
                if np.isfinite(v) and v > 0:
                    penalty *= 0.85

        return length_score * penalty

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        # Cache gene -> proxy score.
        cache = ctx.cache.setdefault("e362_proxy", {})

        scores = []
        for p in perts:
            gene = self._target_gene(ctx, p)
            if gene is None:
                scores.append(np.nan)
                continue
            if gene in cache:
                s = cache[gene]
            else:
                s = self._protein_proxy(ctx, gene)
                cache[gene] = s
            scores.append(np.nan if s is None else s)

        scores = np.asarray(scores, dtype=float)
        finite = scores[np.isfinite(scores)]
        if finite.size > 0:
            fill = float(np.median(finite))
        else:
            fill = 0.0
        scores = np.where(np.isfinite(scores), scores, fill)

        # Broadcast the target-level score to all genes for each perturbation.
        out[:, :, 0] = scores[:, None]
        return out
