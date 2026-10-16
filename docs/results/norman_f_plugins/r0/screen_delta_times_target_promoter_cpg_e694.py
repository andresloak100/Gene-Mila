import numpy as np
from genemila.features.api import Feature, register

@register
class ScreenDeltaTimesTargetPromoterCpg(Feature):
    name = "screen_delta_times_target_promoter_cpg_e694"
    version = 1
    description = "Elementwise product of signed screen delta of target and mean promoter CpG o/e of target genes."
    rationale = "Combines screen delta with promoter CpG content of targets to capture epigenetic modulation."
    inputs = ["control_cells", "replogle2022_k562", "gene_annotation"]
    params = {}
    dim = 1

    def _as_float(self, v):
        """Robustly convert a value that may be a scalar, list, or array into a float."""
        if v is None:
            return None
        arr = np.asarray(v, dtype=np.float64).ravel()
        if arr.size == 0:
            return None
        return float(arr[0])

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        ga = ctx.knowledge("gene_annotation")
        repl = ctx.knowledge("replogle2022_k562")

        cpg_map = {}
        if ga is not None and "genes" in ga and "columns" in ga:
            cols = ga["columns"]
            if "cpg_oe_promoter" in cols:
                idx = cols.index("cpg_oe_promoter")
                for g, vals in ga["genes"].items():
                    if vals is None:
                        continue
                    try:
                        if len(vals) <= idx:
                            continue
                    except TypeError:
                        continue
                    fv = self._as_float(vals[idx])
                    if fv is not None:
                        cpg_map[g] = fv

        screen_map = {}
        if repl is not None and "perts" in repl:
            sign = repl.get("sign", -1)
            for g, d in repl["perts"].items():
                if d is None or "delta" not in d:
                    continue
                fv = self._as_float(d["delta"])
                if fv is not None:
                    screen_map[g] = sign * fv

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue

            vals = [cpg_map[g] for g in targets if g in cpg_map]
            if not vals:
                continue
            mean_cpg = float(np.mean(vals))

            screen_vals = [screen_map[g] for g in targets if g in screen_map]
            if not screen_vals:
                continue
            mean_screen = float(np.mean(screen_vals))

            out[i, :, 0] = mean_screen * mean_cpg

        return out
