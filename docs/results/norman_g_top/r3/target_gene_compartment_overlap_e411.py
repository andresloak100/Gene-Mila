import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneCompartmentOverlapE411(Feature):
    name = "target_gene_compartment_overlap_e411"
    version = 1
    description = ("For each perturbation and gene, fraction of shared UniProt localization "
                   "flags between the perturbation's target protein(s) and gene g's protein, "
                   "averaged over targets.")
    rationale = ("Proteins in the same cellular compartment are more likely to interact "
                 "functionally; perturbing a target may preferentially affect genes whose "
                 "products reside in the same compartment.")
    inputs = ["knowledge"]
    params = {"aggregation": "mean"}
    dim = 1

    def _build_flag_matrix(self, ctx):
        cached = ctx.cache.get("e411_flag_matrix")
        if cached is not None:
            return cached

        pa = ctx.knowledge("protein_annotation")
        n = ctx.n_genes
        flags = np.zeros((n, 0), dtype=np.float32)
        flag_names = []

        if pa is not None:
            cols = pa.get("columns", [])
            genes = pa.get("genes", {})
            # localization flags: columns after n_transmembrane
            try:
                start = cols.index("n_transmembrane") + 1
            except ValueError:
                start = 4
            flag_names = [c for c in cols[start:] if c not in ("protein_length",)]
            flags = np.zeros((n, len(flag_names)), dtype=np.float32)
            for j, fname in enumerate(flag_names):
                for g, gi in ctx.gene_index.items():
                    vals = genes.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[cols.index(fname)]
                    except (ValueError, IndexError):
                        continue
                    if v is None:
                        continue
                    try:
                        flags[gi, j] = 1.0 if float(v) > 0 else 0.0
                    except (TypeError, ValueError):
                        flags[gi, j] = 0.0

        # Precompute pairwise shared-flag counts: (n_genes, n_genes)
        shared = flags @ flags.T  # counts of shared flags
        ctx.cache["e411_flag_matrix"] = (flags, shared, flag_names)
        return flags, shared, flag_names

    def compute(self, ctx, perts, params):
        flags, shared, flag_names = self._build_flag_matrix(ctx)
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=np.float32)
        agg = params.get("aggregation", "mean")

        if flags.shape[1] == 0:
            return out

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # shared counts between each target and all genes
            sub = shared[tgt_idx, :]  # (n_targets, n_genes)
            # normalize by number of flags of gene g (or max possible)
            nflags_g = flags.sum(axis=1)  # (n_genes,)
            denom = np.maximum(nflags_g, 1.0)
            frac = sub / denom[None, :]  # (n_targets, n_genes)
            frac = np.clip(frac, 0.0, 1.0)
            if agg == "max":
                out[i, :, 0] = frac.max(axis=0)
            elif agg == "sum":
                out[i, :, 0] = frac.sum(axis=0)
            else:
                out[i, :, 0] = frac.mean(axis=0)

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
