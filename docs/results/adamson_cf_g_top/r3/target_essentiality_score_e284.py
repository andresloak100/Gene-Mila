import numpy as np
from genemila.features.api import Feature, register


@register
class TargetEssentialityScoreE284(Feature):
    name = "target_essentiality_score_e284"
    version = 1
    description = "Continuous essentiality score of the perturbation target from gnomAD LoF constraint (LOEUF/pLI)."
    rationale = (
        "Essential genes are critical for viability; their knockdown triggers broad stress/cell-cycle "
        "transcriptional programs. Essentiality is approximated by LoF constraint: low LOEUF or high pLI "
        "indicates LoF intolerance, hence higher essentiality."
    )
    inputs = ["control_cells", "gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        # --- load constraint table ---
        cons = ctx.knowledge("gene_constraint")
        genes_tbl = {}
        flags_tbl = {}
        columns = None
        if isinstance(cons, dict):
            genes_tbl = cons.get("genes", {}) or {}
            flags_tbl = cons.get("flags", {}) or {}
            columns = cons.get("columns", None)

        # locate column indices for oe_lof_upper (LOEUF) and pLI
        loeuf_idx = None
        pli_idx = None
        if columns is not None:
            cols_lower = [str(c).lower() for c in columns]
            for j, c in enumerate(cols_lower):
                if loeuf_idx is None and ("oe_lof_upper" in c or c == "loeuf"):
                    loeuf_idx = j
                if pli_idx is None and (c == "pli" or c.endswith("_pli") or "pli" == c):
                    pli_idx = j
        # fallback guesses if not found
        if loeuf_idx is None:
            loeuf_idx = 0
        if pli_idx is None:
            pli_idx = 1

        def _to_float(v):
            if v is None:
                return None
            try:
                f = float(v)
            except (TypeError, ValueError):
                return None
            if not np.isfinite(f):
                return None
            return f

        def _get_vals(sym):
            row = genes_tbl.get(sym)
            if row is None:
                return None, None
            loeuf = None
            pli = None
            try:
                if loeuf_idx < len(row):
                    loeuf = _to_float(row[loeuf_idx])
                if pli_idx < len(row):
                    pli = _to_float(row[pli_idx])
            except TypeError:
                return None, None
            return loeuf, pli

        def _is_unreliable(sym):
            fl = flags_tbl.get(sym)
            if not fl:
                return False
            # flags joined by '|'; unreliable if critical flags present
            for bad in ("no_exp_lof", "lof_too_many", "no_variants"):
                if bad in fl:
                    return True
            return False

        # --- compute raw essentiality score per target symbol ---
        # score: prefer -log(LOEUF) (clipped); else pLI; else None
        symbol_scores = {}

        def _score_for_symbol(sym):
            if sym in symbol_scores:
                return symbol_scores[sym]
            loeuf, pli = _get_vals(sym)
            unreliable = _is_unreliable(sym)
            score = None
            if loeuf is not None and loeuf > 0 and not unreliable:
                score = -np.log(loeuf)
            elif pli is not None and not unreliable:
                score = pli
            elif loeuf is not None and loeuf > 0:
                score = -np.log(loeuf)
            elif pli is not None:
                score = pli
            symbol_scores[sym] = score
            return score

        # gather scores for all targets to compute a median fallback
        target_syms = []
        for p in perts:
            tgs = ctx.target_genes(p)
            target_syms.append(tgs[0] if tgs else None)

        valid_scores = []
        for sym in target_syms:
            if sym is None:
                continue
            s = _score_for_symbol(sym)
            if s is not None:
                valid_scores.append(s)

        if len(valid_scores) > 0:
            fallback = float(np.median(valid_scores))
        else:
            fallback = 0.0

        # --- fill output ---
        # The essentiality score is a property of the target, so it is constant
        # across gene columns for each perturbation (broadcast to all genes).
        for i, sym in enumerate(target_syms):
            if sym is None:
                val = fallback
            else:
                s = _score_for_symbol(sym)
                val = fallback if s is None else s
            if not np.isfinite(val):
                val = fallback
            out[i, :, 0] = val

        return out
