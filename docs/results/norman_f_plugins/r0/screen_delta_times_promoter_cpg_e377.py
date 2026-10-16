import numpy as np
from genemila.features.api import Feature, register


@register
class ScreenDeltaTimesPromoterCpG(Feature):
    name = "screen_delta_times_promoter_cpg_e377"
    version = 1
    description = ("Product of the sign-flipped Replogle2022 K562 CRISPRi screen delta of the "
                   "perturbation's target gene(s) and the promoter CpG observed/expected ratio "
                   "of that target gene (averaged over targets for pairs).")
    rationale = ("Promoter CpG content may modulate CRISPRa activation efficiency; scaling the "
                 "signed screen delta by the target's promoter CpG o/e ratio may capture "
                 "epigenetic modulation of the perturbation effect.")
    inputs = ["replogle2022_k562", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        ann = ctx.knowledge("gene_annotation")
        cpg_map = {}
        if ann is not None:
            genes_ann = ann.get("genes") if isinstance(ann, dict) else None
            cols = ann.get("columns") if isinstance(ann, dict) else None
            if genes_ann is not None and cols is not None:
                try:
                    cpg_idx = list(cols).index("cpg_oe_promoter")
                except (ValueError, TypeError):
                    cpg_idx = None
                if cpg_idx is not None:
                    for g, vals in genes_ann.items():
                        if vals is None:
                            continue
                        try:
                            v = vals[cpg_idx]
                        except (TypeError, IndexError, KeyError):
                            continue
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            cpg_map[g] = fv

        rep = ctx.knowledge("replogle2022_k562")
        sign = -1.0
        screen_genes = None
        screen_perts = None
        screen_measured = None
        if isinstance(rep, dict):
            try:
                sign = float(rep.get("sign", -1.0))
            except (TypeError, ValueError):
                sign = -1.0
            screen_genes = rep.get("genes")
            screen_perts = rep.get("perts")
            screen_measured = rep.get("measured")

        screen_index = {}
        if screen_perts is not None:
            screen_index = {g: i for i, g in enumerate(screen_perts)}

        # resolve bundle gene index for screen gene order
        screen_gene_cols = None
        if screen_genes is not None:
            screen_gene_cols = np.array(
                [ctx.gene_index.get(g, -1) for g in screen_genes], dtype=np.int64
            )

        def target_screen_delta(gene):
            if screen_perts is None or screen_measured is None:
                return None
            si = screen_index.get(gene)
            if si is None:
                return None
            try:
                val = screen_measured[si]
            except (TypeError, IndexError, KeyError):
                return None
            if val is None:
                return None
            try:
                fv = float(val)
            except (TypeError, ValueError):
                return None
            if not np.isfinite(fv):
                return None
            return fv

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            deltas = []
            cpgs = []
            for tg in targets:
                d = target_screen_delta(tg)
                if d is None:
                    continue
                c = cpg_map.get(tg)
                if c is None:
                    continue
                deltas.append(d)
                cpgs.append(c)
            if not deltas:
                continue
            mean_delta = float(np.mean(np.asarray(deltas, dtype=np.float64)))
            mean_cpg = float(np.mean(np.asarray(cpgs, dtype=np.float64)))
            val = sign * mean_delta * mean_cpg
            if not np.isfinite(val):
                continue
            out[i, :, 0] = val

        out[~np.isfinite(out)] = 0.0
        return out
