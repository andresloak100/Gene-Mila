import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPPIDegreeMean(Feature):
    name = "target_ppi_degree_mean_e300"
    version = 1
    description = ("Mean PPI degree of the perturbation's target genes in ppi_network, "
                   "optionally normalized by mean protein length.")
    rationale = ("Highly connected proteins may amplify or dampen perturbation effects; "
                 "normalizing by protein length controls for gene size.")
    inputs = ["control_cells"]
    params = {"normalize_by_protein_length": True}
    dim = 1

    def compute(self, ctx, perts, params):
        normalize = bool(params.get("normalize_by_protein_length", True))

        # Build degree map from ppi_network (cached).
        cache = ctx.cache
        if "ppi_degree" not in cache:
            degree = {}
            ppi = ctx.knowledge("ppi_network")
            if ppi:
                for entry in ppi:
                    if len(entry) < 2:
                        continue
                    a, b = entry[0], entry[1]
                    if a == b:
                        continue
                    degree[a] = degree.get(a, 0) + 1
                    degree[b] = degree.get(b, 0) + 1
            cache["ppi_degree"] = degree

            # Protein length map.
            plen = {}
            prot = ctx.knowledge("protein_annotation")
            if prot and "genes" in prot and "columns" in prot:
                cols = prot["columns"]
                try:
                    idx = cols.index("protein_length")
                except ValueError:
                    idx = 0
                for g, vals in prot["genes"].items():
                    if vals is not None and len(vals) > idx and vals[idx] is not None:
                        try:
                            plen[g] = float(vals[idx])
                        except (TypeError, ValueError):
                            pass
            cache["protein_length"] = plen

        degree = cache["ppi_degree"]
        plen = cache["protein_length"]

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            degs = []
            lens = []
            for g in targets:
                degs.append(float(degree.get(g, 0)))
                if g in plen and plen[g] > 0:
                    lens.append(plen[g])
            mean_deg = float(np.mean(degs)) if degs else 0.0

            if normalize:
                if lens:
                    mean_len = float(np.mean(lens))
                    if mean_len > 0:
                        mean_deg = mean_deg / mean_len
                else:
                    mean_deg = 0.0

            out[i, :, 0] = mean_deg

        return out
