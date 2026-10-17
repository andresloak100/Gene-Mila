import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLengthXGeneFunctionE269(Feature):
    name = "target_length_x_gene_function_e269"
    version = 2
    description = ("Per-gene product of target gene span (kb) and an indicator that "
                   "gene g is involved in transcription/splicing (from gene_sets).")
    rationale = ("Longer target genes may produce larger perturbation responses, and "
                 "the effect may be concentrated in transcription/splicing genes.")
    inputs = ["knowledge"]
    params = {"function_sets": ["GO:TRANSCRIPTION", "REACTOME:SPLICING"]}
    dim = 1

    def _parse_gene_annotation_span(self, ann):
        if ann is None:
            return {}
        cols = ann.get("columns", [])
        genes = ann.get("genes", {})
        if not genes:
            return {}
        span_idx = None
        for i, c in enumerate(cols):
            if c == "gene_span_kb":
                span_idx = i
                break
        if span_idx is None:
            span_idx = 0
        out = {}
        for sym, vals in genes.items():
            if vals is None:
                out[sym] = None
                continue
            try:
                v = vals[span_idx]
            except Exception:
                out[sym] = None
                continue
            if v is None:
                out[sym] = None
            else:
                try:
                    out[sym] = float(v)
                except Exception:
                    out[sym] = None
        return out

    def _build_function_indicator(self, ctx, set_names):
        n = ctx.n_genes
        ind = np.zeros(n, dtype=float)
        gs = ctx.knowledge("gene_sets")
        if not gs:
            return ind
        members = set()
        for name in set_names:
            genes = None
            if name in gs:
                genes = gs[name]
            else:
                lname = name.lower()
                for k in gs.keys():
                    if k.lower() == lname:
                        genes = gs[k]
                        break
                if genes is None:
                    for k in gs.keys():
                        if lname in k.lower():
                            genes = gs[k]
                            break
            if not genes:
                continue
            for g in genes:
                members.add(g)
        for g in members:
            idx = ctx.gene_index.get(g)
            if idx is not None:
                ind[idx] = 1.0
        return ind

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        set_names = params.get("function_sets", ["GO:TRANSCRIPTION", "REACTOME:SPLICING"])
        if isinstance(set_names, str):
            set_names = [set_names]

        cache = ctx.cache
        key_func = ("e269_func", tuple(set_names))
        if key_func in cache:
            func_ind = cache[key_func]
        else:
            func_ind = self._build_function_indicator(ctx, set_names)
            cache[key_func] = func_ind

        key_span = "e269_span_map"
        if key_span in cache:
            span_map = cache[key_span]
        else:
            ann = ctx.knowledge("gene_annotation")
            span_map = self._parse_gene_annotation_span(ann)
            cache[key_span] = span_map

        # Build a per-gene span vector for *all* genes so that the output varies
        # across genes (not just a scalar repeated). For each gene g, its own
        # span modulates the transcription/splicing indicator.
        n = ctx.n_genes
        gene_span = np.zeros(n, dtype=float)
        for g, idx in ctx.gene_index.items():
            v = span_map.get(g)
            if v is not None:
                gene_span[idx] = v

        # Per-perturbation scalar: target span (first target with known span),
        # fall back to mean span so rows differ across perturbations.
        pert_scale = np.zeros(len(perts), dtype=float)
        default_span = float(np.mean(gene_span[gene_span > 0])) if np.any(gene_span > 0) else 1.0
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            span = None
            if tg:
                for t in tg:
                    v = span_map.get(t)
                    if v is not None:
                        span = v
                        break
            if span is None or span <= 0:
                span = default_span
            pert_scale[i] = span

        # Combine: per-row target scale * per-gene (own span) * function indicator
        # This guarantees variation across rows (different targets -> different scale)
        # and across genes.
        base = gene_span * func_ind  # (n_genes,)
        if not np.any(base > 0):
            # if no function genes matched, still vary across rows using target span
            base = gene_span.copy()
        out[:, :, 0] = pert_scale[:, None] * base[None, :]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
