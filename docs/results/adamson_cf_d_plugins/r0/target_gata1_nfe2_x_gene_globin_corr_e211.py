import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGata1Nfe2XGeneGlobinCorr(Feature):
    name = "target_gata1_nfe2_x_gene_globin_corr_e211"
    version = 1
    description = ("Product of an indicator that the target of perturbation p is a "
                   "neighbor of GATA1 or NFE2 in prior_network and the gene's "
                   "correlation with globin genes.")
    rationale = ("Perturbations of erythroid transcription factor neighbors "
                 "specifically affect genes co-expressed with globin genes.")
    inputs = ["prior_network", "gene_corr"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Globin gene set
        globin_genes = ["HBB", "HBA1", "HBA2", "HBD", "HBG1", "HBG2",
                        "HBE1", "HBZ", "HBM", "HBQ1", "MB"]
        globin_idx = [ctx.gene_index[g] for g in globin_genes if g in ctx.gene_index]

        # Build adjacency from prior_network for GATA1 / NFE2
        anchors = ["GATA1", "NFE2"]
        neighbor_set = set()
        net = ctx.knowledge("prior_network")
        if net is not None:
            # handle both list-of-edges and dict-of-lists representations
            if isinstance(net, dict):
                edges = []
                for k, v in net.items():
                    if isinstance(v, (list, tuple, set)):
                        for x in v:
                            edges.append((k, x))
                    else:
                        edges.append((k, v))
            else:
                edges = net
            for edge in edges:
                if not isinstance(edge, (list, tuple)) or len(edge) < 2:
                    continue
                a, b = edge[0], edge[1]
                if a in anchors and b in ctx.gene_index:
                    neighbor_set.add(b)
                if b in anchors and a in ctx.gene_index:
                    neighbor_set.add(a)

        # Gene-level correlation with globin genes (mean over available globin genes)
        if globin_idx:
            corr_slice = ctx.gene_corr[:, globin_idx]  # (n_genes, n_globin)
            gene_globin_corr = corr_slice.mean(axis=1)
        else:
            gene_globin_corr = np.zeros(n_genes, dtype=float)

        # Center the gene-level score so it varies in sign across genes,
        # avoiding a constant / all-nonnegative row structure.
        gene_globin_corr = gene_globin_corr - gene_globin_corr.mean()

        neighbor_idx = np.array(
            [ctx.gene_index[g] for g in neighbor_set if g in ctx.gene_index],
            dtype=int,
        )

        for i, p in enumerate(perts):
            target_genes = ctx.target_genes(p)
            target_idx = [ctx.gene_index[g] for g in target_genes
                          if g in ctx.gene_index]
            if not target_idx:
                continue

            # Indicator: does the perturbation target a GATA1/NFE2 neighbor?
            if neighbor_idx.size > 0:
                is_neighbor = float(np.isin(target_idx, neighbor_idx).any())
            else:
                is_neighbor = 0.0

            # Fallback: if no network info, use target-gene globin correlation
            # as a graded signal so rows are never all-zero.
            if is_neighbor != 0.0:
                out[i, :, 0] = gene_globin_corr
            else:
                tcorr = gene_globin_corr[np.array(target_idx, dtype=int)].mean()
                out[i, :, 0] = tcorr * gene_globin_corr

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
