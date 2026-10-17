import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveTimesBidirectionalCountE485(Feature):
    name = "additive_times_bidirectional_count_e485"
    version = 1
    description = ("Elementwise product of additive_response and the number of target genes "
                   "of p that have at least one bidirectional promoter partner.")
    rationale = ("CRISPRa at a TSS can activate bidirectional promoters, so target genes with "
                 "more bidirectional partners may have broader downstream effects. This "
                 "modulates the additive baseline by that count.")
    inputs = ["additive_response", "knowledge"]
    params = {"use_sum": False, "default_count": 1.0}
    dim = 1

    def _get_bidi(self, ctx):
        # Try to find a bidirectional annotation in knowledge.
        names = []
        try:
            names = list(ctx.available_knowledge())
        except Exception:
            names = []
        # Prioritise likely names.
        ordered = ["gene_annotation", "gene_annotations", "bidirectional_promoters",
                   "bidirectional", "promoters"]
        seen = set()
        cand = []
        for n in ordered + names:
            if n not in seen:
                seen.add(n)
                cand.append(n)
        for kname in cand:
            try:
                ann = ctx.knowledge(kname)
            except Exception:
                continue
            if not isinstance(ann, dict):
                continue
            # Look for a bidirectional mapping.
            for key in ("bidirectional", "bidirectional_promoters", "bidi",
                        "bidirectional_partners"):
                if key in ann and isinstance(ann[key], dict):
                    return ann[key]
            # Sometimes the whole dict is gene -> list.
            if ann and all(isinstance(v, (list, tuple, set)) for v in ann.values()):
                return ann
        return None

    def compute(self, ctx, perts, params):
        use_sum = bool(params.get("use_sum", False))
        default_count = float(params.get("default_count", 1.0))

        # additive_response feature -> (n_perts, n_genes)
        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim == 1:
            add = add[:, None]

        bidi = self._get_bidi(ctx)

        # Build per-perturbation scalar multiplier.
        mult = np.ones(len(perts), dtype=float)
        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                mult[i] = default_count
                continue
            if bidi is None:
                mult[i] = default_count
                continue
            if use_sum:
                cnt = 0.0
                for g in targets:
                    lst = bidi.get(g)
                    if lst:
                        try:
                            cnt += float(len(lst))
                        except Exception:
                            cnt += 1.0
            else:
                cnt = 0.0
                for g in targets:
                    lst = bidi.get(g)
                    if lst:
                        cnt += 1.0
            # Use default count if no target had a partner, so rows are not all zero.
            mult[i] = cnt if cnt > 0.0 else default_count

        out = add * mult[:, None]
        out = out[:, :, None]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
