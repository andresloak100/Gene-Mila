import numpy as np
from genemila.features.api import Feature, register


@register
class PairGenomicDistanceE676(Feature):
    name = "pair_genomic_distance_e676"
    version = 1
    description = "Genomic TSS distance between the two targets of a pair perturbation (log10(1+bp)); 0 for singles."
    rationale = "Pairs whose targets are close on the genome may share regulatory elements/chromatin domains, shaping the response."
    inputs = ["knowledge"]
    params = {"log_transform": True}
    dim = 1

    def compute(self, ctx, perts, params):
        log_transform = bool(params.get("log_transform", True))
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        loci = None
        try:
            ann = ctx.knowledge("gene_annotation")
            if ann is not None:
                loci = ann.get("loci", None)
        except Exception:
            loci = None

        def get_tss(symbol):
            if loci is None:
                return None
            entry = loci.get(symbol, None)
            if entry is None:
                return None
            try:
                return float(entry[1])
            except (TypeError, ValueError, IndexError):
                return None

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            dist = 0.0
            if targets is not None and len(targets) >= 2:
                tss_vals = [get_tss(g) for g in targets]
                tss_vals = [t for t in tss_vals if t is not None]
                if len(tss_vals) >= 2:
                    dist = float(abs(tss_vals[0] - tss_vals[1]))
            if log_transform:
                val = np.log10(1.0 + dist)
            else:
                val = dist
            out[i, :, 0] = val

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
