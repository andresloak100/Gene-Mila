import numpy as np
from genemila.features.api import Feature, register


@register
class NuclearGenePathwayOverlapInteraction(Feature):
    name = "nuclear_gene_x_pathway_overlap_interacti_e519"
    version = 1
    description = ("For each (p,g): binary nuclear-localization indicator of gene g "
                   "multiplied by the number of gene sets shared between target(p) and g.")
    rationale = ("Nuclear genes may participate in more regulatory pathways, so combining "
                 "nuclear localization with pathway overlap could capture specific effects.")
    inputs = ["protein_annotation", "gene_sets", "control_cells"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        genes = ctx.genes

        # --- nuclear indicator for each gene ---
        nuclear = np.zeros(n_genes, dtype=np.float64)
        proto = ctx.knowledge("protein_annotation")
        if proto is not None:
            cols = list(proto.get("columns", []))
            try:
                nuc_idx = cols.index("nucleus")
            except ValueError:
                nuc_idx = None
            table = proto.get("genes", {}) or {}
            if nuc_idx is not None:
                for gi, g in enumerate(genes):
                    vals = table.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[nuc_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is not None and float(v) > 0:
                        nuclear[gi] = 1.0

        # --- gene set membership matrix (genes x sets) ---
        gs = ctx.knowledge("gene_sets")
        membership = None
        if gs:
            gene_to_row = {}
            set_list = list(gs.items())
            # build sparse-ish: for each gene, list of set indices
            gene_sets_map = {}
            for si, (_, members) in enumerate(set_list):
                if not members:
                    continue
                for m in members:
                    gi = ctx.gene_index.get(m)
                    if gi is not None:
                        gene_sets_map.setdefault(gi, []).append(si)
            n_sets = len(set_list)
            # overlap count matrix computed lazily per target; but n_genes small (2055)
            # Build dense membership only if affordable
            membership = np.zeros((n_genes, n_sets), dtype=np.float32)
            for gi, sis in gene_sets_map.items():
                membership[gi, sis] = 1.0

        # precompute overlap matrix: membership @ membership.T -> (n_genes, n_genes)
        if membership is not None and membership.shape[1] > 0:
            overlap = membership @ membership.T
        else:
            overlap = np.zeros((n_genes, n_genes), dtype=np.float32)

        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # aggregate overlap across all target indices (usually one)
            ov = overlap[tgt_idx, :]  # (n_tgt, n_genes)
            ov_sum = ov.sum(axis=0)   # (n_genes,)
            out[i, :, 0] = nuclear * ov_sum

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
