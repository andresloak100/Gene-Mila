import numpy as np
from genemila.features.api import Feature, register


@register
class PPIPartnerResponseTransferE47(Feature):
    name = "ppi_partner_response_transfer_e47"
    version = 1
    description = (
        "Weighted average of the mean training response (leave-one-out) of gene g's "
        "PPI partners, using PPI confidence as weight."
    )
    rationale = (
        "Proteins in physical complexes often show coordinated expression changes; "
        "partner responses transfer information about g's likely response."
    )
    inputs = ["ppi_network", "train_delta"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        gene_index = ctx.gene_index

        cache = ctx.cache
        key = "ppi_adj_e47"
        adj = cache.get(key)
        if adj is None:
            adj = [[] for _ in range(n_genes)]
            ppi = ctx.knowledge("ppi_network")
            if ppi:
                for entry in ppi:
                    if not entry or len(entry) < 3:
                        continue
                    a, b, w = entry[0], entry[1], entry[2]
                    ia = gene_index.get(a)
                    ib = gene_index.get(b)
                    if ia is None or ib is None:
                        continue
                    try:
                        w = float(w)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(w) or w <= 0:
                        continue
                    if ia == ib:
                        continue
                    adj[ia].append((ib, w))
                    adj[ib].append((ia, w))

            partner_idx = []
            partner_w = []
            for g in range(n_genes):
                lst = adj[g]
                if lst:
                    pidx = np.array([p for p, _ in lst], dtype=np.int64)
                    pw = np.array([w for _, w in lst], dtype=np.float64)
                    s = pw.sum()
                    if s > 0:
                        pw = pw / s
                    else:
                        pw = np.full(len(pidx), 1.0 / len(pidx))
                else:
                    pidx = np.empty(0, dtype=np.int64)
                    pw = np.empty(0, dtype=np.float64)
                partner_idx.append(pidx)
                partner_w.append(pw)
            cache[key] = (partner_idx, partner_w)
        else:
            partner_idx, partner_w = adj

        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            if d.shape[0] == 0:
                continue
            mean_resp = d.mean(axis=0)
            global_mean = float(mean_resp.mean())

            for g in range(n_genes):
                pidx = partner_idx[g]
                if pidx.size == 0:
                    out[i, g, 0] = global_mean
                else:
                    pw = partner_w[g]
                    out[i, g, 0] = float(np.dot(pw, mean_resp[pidx]))

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
