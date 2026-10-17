import numpy as np
from genemila.features.api import Feature, register


@register
class EssentialityTargetXMeanResponseG(Feature):
    name = "essentiality_target_x_mean_response_g_e361"
    version = 1
    description = ("For each (p,g): (1 - LOEUF_target) * mean_response_g, where mean_response_g "
                   "is the average delta of gene g across training perturbations (leaving p out).")
    rationale = ("Essential targets may amplify the response of genes that are already responsive; "
                 "this interaction captures target essentiality times per-gene mean response.")
    inputs = ["train_delta", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        # Load LOEUF values from gene_constraint knowledge
        loeuf = np.full(n_genes, np.nan, dtype=np.float64)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            genes_map = kc.get("genes", {})
            columns = kc.get("columns", [])
            try:
                loeuf_idx = columns.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            if loeuf_idx is not None:
                for g, vals in genes_map.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    if vals is None:
                        continue
                    try:
                        v = vals[loeuf_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        loeuf[gi] = fv

        # Genes without a valid LOEUF: treat as non-essential -> (1 - LOEUF) = 0
        # (so the interaction term is 0 for unknown essentiality)
        valid_loeuf = np.isfinite(loeuf)
        essentiality = np.zeros(n_genes, dtype=np.float64)
        essentiality[valid_loeuf] = 1.0 - loeuf[valid_loeuf]
        # Clip to reasonable range in case LOEUF > 1
        essentiality = np.clip(essentiality, 0.0, None)

        for i, p in enumerate(perts):
            # Mean response across training perturbations, leaving p out
            _, d = ctx.train_delta(exclude=p)
            if d.shape[0] == 0:
                mean_resp = np.zeros(n_genes, dtype=np.float64)
            else:
                mean_resp = d.mean(axis=0)

            # Target essentiality: use mean of essentiality over target genes of p
            target_idx = ctx.target_indices(p)
            if len(target_idx) > 0:
                tgt_ess = essentiality[target_idx]
                # Only consider targets with valid LOEUF
                valid_t = np.isfinite(loeuf[target_idx])
                if np.any(valid_t):
                    target_ess = float(np.mean(tgt_ess[valid_t]))
                else:
                    target_ess = 0.0
            else:
                target_ess = 0.0

            out[i, :, 0] = target_ess * mean_resp

        # Ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
