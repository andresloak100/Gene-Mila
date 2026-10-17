import numpy as np
from genemila.features.api import Feature, register


@register
class TargetExpressionVarianceMeanE585(Feature):
    name = "target_expression_variance_mean_e585"
    version = 1
    description = ("Mean variance of expression across cell types for the perturbation's "
                   "target genes (constant across genes g for a given p).")
    rationale = ("Genes whose expression varies strongly across cell types/contexts may be "
                 "more responsive to perturbation; averaging this over p's targets gives a "
                 "target-level potential-for-change score.")
    inputs = ["control_cells", "gene_annotation"]
    params = {}
    dim = 1

    def _gene_variance(self, ctx):
        """Per-gene expression variance across cell types.

        No external atlas is available inside the plugin, so we proxy 'expression
        across cell types' with the spread of each gene's expression across the
        control cell population (a context/state proxy), combined with a
        sequence-derived expressivity proxy when annotation is present.
        """
        cache = ctx.cache
        key = "e585_gene_var"
        if key in cache:
            return cache[key]

        # Variance of each gene across control cells (n_genes,)
        X = np.asarray(ctx.control_cells, dtype=float)
        if X.ndim != 2 or X.shape[1] != ctx.n_genes:
            var = np.zeros(ctx.n_genes, dtype=float)
        else:
            var = X.var(axis=0)
        var = np.nan_to_num(var, nan=0.0, posinf=0.0, neginf=0.0)
        var = np.clip(var, 0.0, None)

        # Sequence-derived expressivity proxy: genes with many transcripts / exons
        # and longer transcripts tend to be broadly and variably expressed.
        ann = ctx.knowledge("gene_annotation")
        if isinstance(ann, dict):
            genes_tbl = ann.get("genes") or {}
            cols = ann.get("columns") or []
            idx = {c: i for i, c in enumerate(cols)}
            i_exon = idx.get("n_exons")
            i_tlen = idx.get("transcript_length")
            i_span = idx.get("gene_span_kb")
            if i_exon is not None or i_tlen is not None or i_span is not None:
                seq = np.zeros(ctx.n_genes, dtype=float)
                have = np.zeros(ctx.n_genes, dtype=bool)
                for j, g in enumerate(ctx.genes):
                    vals = genes_tbl.get(g)
                    if not vals:
                        continue
                    acc = 0.0
                    n = 0
                    if i_exon is not None and i_exon < len(vals) and vals[i_exon] is not None:
                        acc += float(vals[i_exon]); n += 1
                    if i_tlen is not None and i_tlen < len(vals) and vals[i_tlen] is not None:
                        acc += np.log1p(max(float(vals[i_tlen]), 0.0)); n += 1
                    if i_span is not None and i_span < len(vals) and vals[i_span] is not None:
                        acc += np.log1p(max(float(vals[i_span]), 0.0)); n += 1
                    if n > 0:
                        seq[j] = acc / n
                        have[j] = True
                if have.any():
                    s = seq[have]
                    mu, sd = s.mean(), s.std()
                    if sd > 1e-12:
                        seq = (seq - mu) / sd
                    else:
                        seq = np.zeros_like(seq)
                    seq = np.where(have, seq, 0.0)
                    # gentle multiplicative modulation of the variance proxy
                    var = var * np.exp(0.25 * seq)

        cache[key] = var
        return var

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        var = self._gene_variance(ctx)
        for i, p in enumerate(perts):
            idxs = ctx.target_indices(p)
            if idxs:
                v = float(np.mean(var[idxs]))
            else:
                v = 0.0
            if not np.isfinite(v):
                v = 0.0
            out[i, :, 0] = v
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
