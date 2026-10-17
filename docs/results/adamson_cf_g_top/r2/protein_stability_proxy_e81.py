import numpy as np
from genemila.features.api import Feature, register


@register
class ProteinStabilityProxyE81(Feature):
    name = "protein_stability_proxy_e81"
    version = 1
    description = ("Per-gene protein-stability proxy from protein_annotation (length, "
                   "signal peptide, transmembrane) and gene_constraint (LOEUF), "
                   "interacted with the target gene's mean response magnitude.")
    rationale = ("Genes whose proteins turn over quickly can change abundance fast upon "
                 "transcriptional perturbation, so their downstream response is amplified. "
                 "Protein half-life is unavailable, so we build a stability proxy from "
                 "annotation (longer / membrane / signal-peptide proteins tend to be more "
                 "stable; high LOEUF = LoF-tolerant, loosely tied to turnover) and modulate "
                 "the generic response by the perturbed target's overall effect magnitude.")
    inputs = ["protein_annotation", "gene_constraint", "train_delta", "control_mean"]
    params = {"stability_weights": "default"}
    dim = 1

    def _stability(self, ctx):
        cache = ctx.cache
        key = "e81_stability"
        if key in cache:
            return cache[key]

        n = ctx.n_genes
        # protein_annotation columns of interest
        prot = ctx.knowledge("protein_annotation")
        length = np.zeros(n, dtype=float)
        has_sp = np.zeros(n, dtype=float)
        n_tm = np.zeros(n, dtype=float)
        prot_ok = np.zeros(n, dtype=bool)

        if prot is not None:
            cols = list(prot.get("columns", []))
            genes = prot.get("genes", {})
            try:
                i_len = cols.index("protein_length")
            except ValueError:
                i_len = None
            try:
                i_sp = cols.index("has_signal_peptide")
            except ValueError:
                i_sp = None
            try:
                i_tm = cols.index("n_transmembrane")
            except ValueError:
                i_tm = None
            for g, vals in genes.items():
                gi = ctx.gene_index.get(g)
                if gi is None or vals is None:
                    continue
                try:
                    if i_len is not None and vals[i_len] is not None:
                        length[gi] = float(vals[i_len])
                    if i_sp is not None and vals[i_sp] is not None:
                        has_sp[gi] = float(vals[i_sp])
                    if i_tm is not None and vals[i_tm] is not None:
                        n_tm[gi] = float(vals[i_tm])
                    prot_ok[gi] = True
                except (TypeError, ValueError, IndexError):
                    continue

        # gene_constraint: LOEUF
        cons = ctx.knowledge("gene_constraint")
        loeuf = np.full(n, np.nan, dtype=float)
        if cons is not None:
            cols = list(cons.get("columns", []))
            genes = cons.get("genes", {})
            try:
                i_lo = cols.index("oe_lof_upper")
            except ValueError:
                i_lo = None
            if i_lo is not None:
                for g, vals in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    try:
                        v = vals[i_lo]
                        if v is not None:
                            loeuf[gi] = float(v)
                    except (TypeError, ValueError, IndexError):
                        continue

        def zscore(x, mask):
            z = np.zeros_like(x)
            if mask.sum() < 2:
                return z
            mu = x[mask].mean()
            sd = x[mask].std()
            if sd < 1e-8:
                return z
            z[mask] = (x[mask] - mu) / sd
            return z

        # log-transform length for scale
        log_len = np.log1p(np.clip(length, 0, None))
        mask_prot = prot_ok
        z_len = zscore(log_len, mask_prot)
        z_sp = zscore(has_sp, mask_prot)
        z_tm = zscore(n_tm, mask_prot)

        mask_lo = np.isfinite(loeuf) & (loeuf > 0)
        log_lo = np.zeros(n, dtype=float)
        log_lo[mask_lo] = -np.log(np.clip(loeuf[mask_lo], 1e-3, None))
        z_lo = zscore(log_lo, mask_lo)

        # Default weights: longer & membrane & signal-peptide -> more stable (positive),
        # high LOEUF (LoF tolerant) -> slightly less stable proxy (negative).
        w = self.params.get("stability_weights", "default")
        if not isinstance(w, dict):
            w = {"len": 0.5, "sp": 0.5, "tm": 0.3, "lo": -0.3}
        wl = float(w.get("len", 0.5))
        wsp = float(w.get("sp", 0.5))
        wtm = float(w.get("tm", 0.3))
        wlo = float(w.get("lo", -0.3))

        stab = wl * z_len + wsp * z_sp + wtm * z_tm + wlo * z_lo
        # only trust where we have protein annotation; otherwise keep 0
        stab = np.where(mask_prot, stab, 0.0)
        stab = np.nan_to_num(stab, nan=0.0, posinf=0.0, neginf=0.0)
        cache[key] = stab
        return stab

    def compute(self, ctx, perts, params):
        stab = self._stability(ctx)  # (n_genes,)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            if d.shape[0] == 0:
                target_mag = 0.0
            else:
                # magnitude of the generic response program for this target
                target_mag = float(np.mean(np.abs(d.mean(axis=0))))
            # signed response interaction: stability proxy scaled by target effect magnitude
            out[i, :, 0] = stab * target_mag

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
