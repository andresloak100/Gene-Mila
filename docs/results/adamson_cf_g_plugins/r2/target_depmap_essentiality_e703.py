import numpy as np
from genemila.features.api import Feature, register


@register
class TargetDepmapEssentialityE703(Feature):
    name = "target_depmap_essentiality_e703"
    version = 1
    description = (
        "For each perturbation target, use its essentiality score (DepMap CERES-like, "
        "or a gene_constraint proxy) broadcast to all gene rows."
    )
    rationale = (
        "Perturbing essential genes tends to produce larger, broader expression changes; "
        "the target's essentiality is a per-perturbation scalar broadcast across genes."
    )
    inputs = ["knowledge", "target_genes"]
    params = {"source": "depmap_ceres"}
    dim = 1

    def _build_score_map(self, ctx, params):
        source = params.get("source", "depmap_ceres")

        # Try an explicit DepMap table if provided via knowledge (unlikely in this bundle).
        if source == "depmap_ceres":
            for kname in ("depmap_ceres", "depmap_gene_effect", "depmap"):
                kn = ctx.knowledge(kname)
                if kn is not None and isinstance(kn, dict):
                    genes = kn.get("genes", {})
                    cols = kn.get("columns", [])
                    if isinstance(genes, dict) and len(genes) > 0:
                        # pick a gene-effect column if present
                        idx = 0
                        for j, c in enumerate(cols):
                            lc = str(c).lower()
                            if "effect" in lc or "ceres" in lc or "chronos" in lc:
                                idx = j
                                break
                        score = {}
                        for g, vals in genes.items():
                            try:
                                v = vals[idx]
                            except Exception:
                                v = None
                            if v is None:
                                continue
                            try:
                                fv = float(v)
                            except Exception:
                                continue
                            if np.isfinite(fv):
                                score[g] = fv
                        if score:
                            return score

        # Fallback / proxy: gnomAD LoF constraint (LOEUF). Low LOEUF = LoF-intolerant
        # ~ essential-like. Convert to an "essentiality" score: -LOEUF so higher = more essential.
        kn = ctx.knowledge("gene_constraint")
        score = {}
        if kn is not None and isinstance(kn, dict):
            genes = kn.get("genes", {})
            cols = kn.get("columns", [])
            loeuf_idx = None
            pli_idx = None
            for j, c in enumerate(cols):
                lc = str(c).lower()
                if loeuf_idx is None and ("oe_lof_upper" in lc or "loeuf" in lc):
                    loeuf_idx = j
                if pli_idx is None and lc == "pli":
                    pli_idx = j
            if isinstance(genes, dict):
                for g, vals in genes.items():
                    v = None
                    if loeuf_idx is not None:
                        try:
                            v = vals[loeuf_idx]
                        except Exception:
                            v = None
                    if v is None and pli_idx is not None:
                        try:
                            v = vals[pli_idx]
                        except Exception:
                            v = None
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except Exception:
                        continue
                    if not np.isfinite(fv):
                        continue
                    if loeuf_idx is not None and v is vals[loeuf_idx] if False else True:
                        pass
                    # If we used LOEUF, negate so higher = more essential.
                    if loeuf_idx is not None and _is_from(vals, loeuf_idx, v):
                        score[g] = -fv
                    else:
                        # pLI: higher = more essential already
                        score[g] = fv
        return score

    def compute(self, ctx, perts, params):
        score_map = self._build_score_map(ctx, params)

        # Normalize scores to a stable scale (median ~0, robust spread ~1) for model friendliness.
        if score_map:
            vals = np.array([v for v in score_map.values() if np.isfinite(v)], dtype=float)
            if vals.size > 1:
                med = float(np.median(vals))
                mad = float(np.median(np.abs(vals - med)))
                scale = 1.4826 * mad if mad > 0 else (float(np.std(vals)) or 1.0)
            else:
                med = float(vals[0]) if vals.size else 0.0
                scale = 1.0
        else:
            med, scale = 0.0, 1.0

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            s = 0.0
            got = False
            for g in tg:
                if g in score_map:
                    s += score_map[g]
                    got = True
            if got and len(tg) > 0:
                s = s / float(len(tg))
            else:
                s = med  # neutral fill for unmapped targets
            z = (s - med) / scale if scale > 0 else 0.0
            if not np.isfinite(z):
                z = 0.0
            out[i, :, 0] = z
        return out


def _is_from(vals, idx, v):
    # helper: check that v came from the given column (identity by value comparison)
    try:
        return vals[idx] is v or vals[idx] == v
    except Exception:
        return False
