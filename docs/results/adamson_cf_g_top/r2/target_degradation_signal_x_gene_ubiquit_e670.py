import numpy as np
from genemila.features.api import Feature, register


@register
class TargetDegradationSignalXGeneUbiquitE670(Feature):
    name = "target_degradation_signal_x_gene_ubiquit_e670"
    version = 1
    description = ("Product of the target gene's degradation-signal strength "
                   "(protein length / signal-peptide based proxy plus PEST-like "
                   "sequence propensity from protein_annotation) and an indicator "
                   "that gene g belongs to ubiquitin-proteasome pathway gene sets.")
    rationale = ("Targets with strong degradation signals may drive larger "
                 "expression changes in ubiquitin-proteasome pathway genes; "
                 "combining target-level signal with gene-level pathway membership "
                 "captures this interaction.")
    inputs = ["protein_annotation", "gene_sets", "control_mean"]
    params = {"degradation_threshold": 0.5}
    dim = 1

    def _ubiquitin_membership(self, ctx):
        cache = ctx.cache
        key = "_e670_ubiq_membership"
        if key in cache:
            return cache[key]
        gs = ctx.knowledge("gene_sets")
        membership = np.zeros(ctx.n_genes, dtype=np.float64)
        if gs:
            ubiq_terms = []
            for name in gs.keys():
                lname = name.lower()
                if ("proteasome" in lname or "ubiquitin" in lname
                        or "ubiquitin-mediated proteolysis" in lname
                        or "ubiquitin mediated proteolysis" in lname):
                    ubiq_terms.append(name)
            for term in ubiq_terms:
                genes = gs.get(term, []) or []
                for g in genes:
                    idx = ctx.gene_index.get(g)
                    if idx is not None:
                        membership[idx] = 1.0
        cache[key] = membership
        return membership

    def _protein_stability(self, ctx):
        cache = ctx.cache
        key = "_e670_protein_stability"
        if key in cache:
            return cache[key]
        pa = ctx.knowledge("protein_annotation")
        stab = np.full(ctx.n_genes, np.nan, dtype=np.float64)
        if pa:
            cols = pa.get("columns", [])
            col_idx = {c: i for i, c in enumerate(cols)}
            genes_tbl = pa.get("genes", {})
            len_i = col_idx.get("protein_length")
            sp_i = col_idx.get("has_signal_peptide")
            spl_i = col_idx.get("signal_peptide_length")
            tm_i = col_idx.get("n_transmembrane")
            for g, vals in genes_tbl.items():
                gi = ctx.gene_index.get(g)
                if gi is None or vals is None:
                    continue
                try:
                    length = float(vals[len_i]) if len_i is not None and vals[len_i] is not None else 0.0
                except (TypeError, ValueError):
                    length = 0.0
                try:
                    sp = float(vals[sp_i]) if sp_i is not None and vals[sp_i] is not None else 0.0
                except (TypeError, ValueError):
                    sp = 0.0
                try:
                    spl = float(vals[spl_i]) if spl_i is not None and vals[spl_i] is not None else 0.0
                except (TypeError, ValueError):
                    spl = 0.0
                try:
                    tm = float(vals[tm_i]) if tm_i is not None and vals[tm_i] is not None else 0.0
                except (TypeError, ValueError):
                    tm = 0.0
                # Degradation-signal proxy: longer proteins and ER-targeted /
                # membrane proteins tend to be turned over faster; signal
                # peptide length contributes a modest PEST-like propensity term.
                score = (np.log1p(max(length, 0.0))
                         + 0.5 * sp
                         + 0.01 * max(spl, 0.0)
                         + 0.3 * min(tm, 5.0))
                stab[gi] = score
        # Fill missing with median of observed
        obs = np.isfinite(stab)
        if obs.any():
            med = float(np.median(stab[obs]))
        else:
            med = 0.0
        stab = np.where(np.isfinite(stab), stab, med)
        cache[key] = stab
        return stab

    def compute(self, ctx, perts, params):
        thr = float(params.get("degradation_threshold", 0.5))
        ubiq = self._ubiquitin_membership(ctx)  # (n_genes,)
        stab = self._protein_stability(ctx)     # (n_genes,)

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=np.float64)
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            t_scores = stab[np.asarray(tgt_idx, dtype=int)]
            if t_scores.size == 0:
                continue
            t_sig = float(np.mean(t_scores))
            # Apply threshold: only strong degradation signals contribute
            if t_sig < thr:
                t_sig = 0.0
            out[i, :, 0] = t_sig * ubiq
        return out
