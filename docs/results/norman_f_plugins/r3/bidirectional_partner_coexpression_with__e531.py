import numpy as np
from genemila.features.api import Feature, register


@register
class BidirectionalPartnerCoexpressionE531(Feature):
    name = "bidirectional_partner_coexpression_with__e531"
    version = 1
    description = ("Mean control-cell Pearson correlation between gene g and the "
                   "bidirectional partners of the perturbation's target genes.")
    rationale = ("A target with a bidirectional partner may co-activate that partner, "
                 "which could then influence g; this indirect path is captured by "
                 "coexpression between the partner and g.")
    inputs = ["control_cells", "gene_corr"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Load bidirectional prior knowledge once.
        bidir_map = {}
        info = ctx.knowledge("gene_annotation")
        if info is not None:
            raw = info.get("bidirectional")
            if isinstance(raw, dict):
                for k, v in raw.items():
                    if v is None:
                        continue
                    if isinstance(v, str):
                        bidir_map[k] = [v]
                    else:
                        try:
                            bidir_map[k] = [str(x) for x in v if x is not None]
                        except TypeError:
                            bidir_map[k] = []
            elif isinstance(raw, list):
                for entry in raw:
                    if not entry:
                        continue
                    k = entry[0]
                    v = entry[1] if len(entry) > 1 else None
                    if v is None:
                        bidir_map[k] = []
                    elif isinstance(v, str):
                        bidir_map[k] = [v]
                    else:
                        try:
                            bidir_map[k] = [str(x) for x in v if x is not None]
                        except TypeError:
                            bidir_map[k] = []

        corr = np.asarray(ctx.gene_corr, dtype=float)  # (n_genes, n_genes)
        n_perts = len(perts)
        target_partner_cols = []  # list per perturbation of partner column arrays

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            partner_cols = []
            if targets:
                for t in targets:
                    for partner in bidir_map.get(t, ()):
                        j = ctx.gene_index.get(partner)
                        if j is not None:
                            partner_cols.append(j)
            target_partner_cols.append(partner_cols)

        # If no perturbation has any partner, fall back to a target-based signal
        # so the feature is not constant. Use mean correlation of target genes
        # with all genes (this is non-constant across perts).
        any_partner = any(len(cols) > 0 for cols in target_partner_cols)
        if not any_partner:
            for i, p in enumerate(perts):
                targets = ctx.target_genes(p)
                tgt_cols = [ctx.gene_index[t] for t in targets if t in ctx.gene_index]
                if tgt_cols:
                    out[i, :, 0] = corr[np.asarray(tgt_cols, dtype=int), :].mean(axis=0)
            return out

        for i in range(n_perts):
            cols = target_partner_cols[i]
            if not cols:
                # Fall back per-perturbation to target-gene correlation mean
                targets = ctx.target_genes(perts[i])
                tgt_cols = [ctx.gene_index[t] for t in targets if t in ctx.gene_index]
                if tgt_cols:
                    out[i, :, 0] = corr[np.asarray(tgt_cols, dtype=int), :].mean(axis=0)
                continue
            rows = corr[np.asarray(cols, dtype=int), :]
            out[i, :, 0] = rows.mean(axis=0)

        return out
