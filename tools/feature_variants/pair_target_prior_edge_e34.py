import numpy as np
from genemila.features.api import Feature, register

@register
class PairTargetPriorEdge(Feature):
    name = "pair_target_prior_edge_e34"
    version = 3
    description = "Pair prior-edge weight, with per-pair control-correlation fallback for missing or zero edges."
    rationale = "If two targets interact in the prior regulatory network, their combined effect may deviate from the sum of singles."
    inputs = ["prior_network", "control_cells"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        lookup = ctx.cache.get("_pair_edge_lookup_e34")
        if lookup is None:
            lookup = {}
            net = ctx.knowledge("prior_network")
            if net is not None:
                # Accept several common prior-network schemas.
                if isinstance(net, dict):
                    for k, v in net.items():
                        try:
                            w = float(v)
                        except (TypeError, ValueError):
                            continue
                        if not np.isfinite(w):
                            continue
                        if isinstance(k, (list, tuple)) and len(k) >= 2:
                            a, b = k[0], k[1]
                        elif isinstance(k, str):
                            for sep in ("+", "-", "|", "_", ":"):
                                if sep in k:
                                    a, b = k.split(sep, 1)
                                    break
                            else:
                                continue
                        else:
                            continue
                        key = (a, b) if a <= b else (b, a)
                        lookup[key] = w
                elif isinstance(net, (list, tuple)):
                    for entry in net:
                        if isinstance(entry, dict):
                            a = entry.get("source", entry.get("from", entry.get("a", entry.get("gene_a"))))
                            b = entry.get("target", entry.get("to", entry.get("b", entry.get("gene_b"))))
                            w = entry.get("weight", entry.get("value", entry.get("score", entry.get("w", 0.0))))
                        elif isinstance(entry, (list, tuple)) and len(entry) >= 3:
                            a, b, w = entry[0], entry[1], entry[2]
                        else:
                            continue
                        try:
                            w = float(w)
                        except (TypeError, ValueError):
                            continue
                        if not np.isfinite(w) or a is None or b is None:
                            continue
                        key = (a, b) if a <= b else (b, a)
                        lookup[key] = w
            ctx.cache["_pair_edge_lookup_e34"] = lookup

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if targets is None or len(targets) != 2:
                continue
            a, b = targets[0], targets[1]
            key = (a, b) if a <= b else (b, a)
            w = lookup.get(key, 0.0)
            if w != 0.0:
                out[i, :, 0] = w
            else:
                # Preserve this row's standalone rule, independent of its batch.
                gene_index = ctx.gene_index
                if a not in gene_index or b not in gene_index:
                    continue
                w = float(ctx.gene_corr[gene_index[a], gene_index[b]])
                if np.isfinite(w) and w != 0.0:
                    out[i, :, 0] = w

        # Ensure rows are finite.
        if not np.all(np.isfinite(out)):
            out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)

        return out
