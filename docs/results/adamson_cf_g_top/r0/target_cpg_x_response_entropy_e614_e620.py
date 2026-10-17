import numpy as np
from genemila.features.api import Feature, register


@register
class TargetCpgXResponseEntropy(Feature):
    name = "target_cpg_x_response_entropy_e614_e620"
    version = 1
    description = ("For each (p,g), product of the CpG observed/expected ratio in the "
                   "target gene's promoter and the response_entropy_e89 of gene g.")
    rationale = ("CpG islands mark regulatory promoters; pairing target promoter CpG density "
                 "with per-gene response entropy captures regulatory complexity interactions.")
    inputs = ["gene_annotation", "train_delta"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        gene_index = ctx.gene_index

        # --- response entropy per gene (leave-one-out across training perturbations) ---
        cache = ctx.cache
        if "resp_entropy_e89" not in cache:
            cache["resp_entropy_e89"] = {}
        ent_cache = cache["resp_entropy_e89"]

        # --- CpG O/E promoter ratio from gene_annotation ---
        ann = ctx.knowledge("gene_annotation")
        cpg_map = {}
        if ann is not None:
            cols = ann.get("columns", [])
            genes_ann = ann.get("genes", {})
            try:
                cpg_col = cols.index("cpg_oe_promoter")
            except ValueError:
                cpg_col = None
            if cpg_col is not None:
                for sym, vals in genes_ann.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[cpg_col]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        cpg_map[sym] = fv

        out = np.zeros((len(perts), n_genes, 1))

        for i, p in enumerate(perts):
            # target CpG O/E (mean over target genes if multiple)
            tgenes = ctx.target_genes(p)
            cpg_vals = [cpg_map[g] for g in tgenes if g in cpg_map]
            if len(cpg_vals) > 0:
                target_cpg = float(np.mean(cpg_vals))
            else:
                target_cpg = 0.0

            # response entropy (leave-one-out) for this perturbation
            if p in ent_cache:
                ent = ent_cache[p]
            else:
                _, d = ctx.train_delta(exclude=p)
                # Shannon entropy of delta values per gene across training perturbations
                if d.shape[0] == 0:
                    ent = np.zeros(n_genes)
                else:
                    # shift to non-negative via absolute magnitudes then normalise per gene
                    a = np.abs(d)
                    col_sum = a.sum(axis=0)
                    safe = col_sum > 0
                    ent = np.zeros(n_genes)
                    if np.any(safe):
                        probs = np.zeros_like(a)
                        probs[:, safe] = a[:, safe] / col_sum[safe]
                        # entropy in nats (or bits); use bits
                        with np.errstate(divide="ignore", invalid="ignore"):
                            logp = np.where(probs > 0, np.log2(probs), 0.0)
                        ent = -np.sum(probs * logp, axis=0)
                ent_cache[p] = ent

            out[i, :, 0] = target_cpg * ent

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
