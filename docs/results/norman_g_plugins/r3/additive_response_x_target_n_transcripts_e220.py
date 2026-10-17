import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetNTranscripts(Feature):
    name = "additive_response_x_target_n_transcripts_e220"
    version = 1
    description = "Product of additive_response and the mean n_transcripts of the perturbation's target genes."
    rationale = ("Isoform diversity (number of transcripts) of the targeted gene(s) may modulate how "
                 "strongly the additive activation response manifests, so scale the additive baseline "
                 "by the average transcript count of the targets.")
    inputs = ["gene_annotation", "target_genes", "train_delta"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # --- Load n_transcripts per gene from gene_annotation ---
        ann = ctx.knowledge("gene_annotation")
        n_transcripts_map = {}
        if ann is not None:
            cols = ann.get("columns", [])
            genes = ann.get("genes", {})
            try:
                idx = cols.index("n_transcripts")
            except ValueError:
                idx = None
            if idx is not None:
                for g, vals in genes.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        n_transcripts_map[g] = float(v)
                    except (TypeError, ValueError):
                        continue

        # Fallback default for genes with no annotation
        default_nt = 1.0

        # --- Precompute additive baseline (mean delta over training perts) per exclusion ---
        cache = ctx.cache

        for i, p in enumerate(perts):
            # Leakage-safe additive baseline: mean training delta excluding p
            key = ("additive_mean", p)
            if key in cache:
                base = cache[key]
            else:
                _, d = ctx.train_delta(exclude=p)
                base = d.mean(axis=0) if d.shape[0] > 0 else np.zeros(n_genes)
                cache[key] = base

            # Mean n_transcripts over the perturbation's target genes
            targets = ctx.target_genes(p)
            if targets:
                vals = [n_transcripts_map.get(g, default_nt) for g in targets]
                mean_nt = float(np.mean(vals))
            else:
                mean_nt = default_nt

            out[i, :, 0] = base * mean_nt

        # Guard against non-finite values
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
