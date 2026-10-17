"""The lead's hand-written hypothesis (docs/ROADMAP.md D4; docs/PREREG_G_KNOWN_BIOLOGY.md family 8): constraint
residualised on control expression and tier-1 essentiality proxies, times additive_response. A human hypothesis,
scored by tools/feature_compare.py and reported as such, never as GOAL_CRITERIA A.1. Fixed before any block G score
exists. The README beside this file states the formula, the gene sets the words below match, and every place the
operationalisation departs from the wording of family 8.

Per gene j of the bundle: s_j = -oe_lof_upper_j (minus LOEUF) from ctx.knowledge("gene_constraint"); genes without a
value are left out of the fit and get rho_j = 0. e_j = 1 if j is in any "CORUM:" set of ctx.knowledge("gene_sets");
r_j = 1 if j is in any "REACTOME:" set whose name contains one of ESSENTIAL_WORDS (case-insensitive). Once per
context (ctx.cache), ordinary least squares over the genes with a value: s_j ~ 1 + ctx.control_mean[j] + e_j + r_j;
rho_j is the residual. Per perturbation p: c_p = mean of rho over p's targets with a value, else 0.
Output (len(perts), n_genes, 1): additive_response[i, :] * c_p, so feature_compare applies both nulls.
"""
from __future__ import annotations

import numpy as np

from genemila.features.api import Feature, FeatureContext, register

ESSENTIAL_WORDS = ("ribosom", "proteasom", "mrna splicing")


def _residual(ctx: FeatureContext) -> tuple[np.ndarray, np.ndarray]:
    """(rho, has): the OLS residual of -LOEUF on 1, control_mean, CORUM membership and Reactome
    ribosome/proteasome/mRNA-splicing membership over the genes with a value, and which genes have one."""
    if "h8_residual" not in ctx.cache:
        n = ctx.n_genes
        s = np.full(n, np.nan)
        table = ctx.knowledge("gene_constraint")
        if table and "oe_lof_upper" in table["columns"]:
            k = table["columns"].index("oe_lof_upper")
            rows = table["genes"]
            for j, g in enumerate(ctx.genes):
                vals = rows.get(g)
                if vals is not None and vals[k] is not None:
                    s[j] = -float(vals[k])
        has = np.isfinite(s)
        e = np.zeros(n)
        r = np.zeros(n)
        gi = ctx.gene_index
        sets = ctx.knowledge("gene_sets") or {}
        for name in sorted(sets):
            if name.startswith("CORUM:"):
                for g in sets[name]:
                    if g in gi:
                        e[gi[g]] = 1.0
            elif name.startswith("REACTOME:") and any(w in name.lower() for w in ESSENTIAL_WORDS):
                for g in sets[name]:
                    if g in gi:
                        r[gi[g]] = 1.0
        rho = np.zeros(n)
        if has.sum() > 4:
            x = np.column_stack([np.ones(n), ctx.control_mean, e, r])[has]
            beta = np.linalg.lstsq(x, s[has], rcond=None)[0]
            rho[has] = s[has] - x @ beta
        ctx.cache["h8_residual"] = (rho, has)
    return ctx.cache["h8_residual"]


@register
class H8ConstraintResidual(Feature):
    name = "h8_constraint_residual"
    description = ("additive_response times the mean, over p's targets with a gnomAD value, of -LOEUF residualised "
                   "(OLS) on control mean, CORUM membership and Reactome ribosome/proteasome/mRNA-splicing "
                   "membership. The lead's pre-registered family 8; a human hypothesis, never A.1.")
    rationale = ("Raw constraint restates basal expression and essentiality (family 6, KNOWN); whether the part "
                 "left after removing both scales the response is OPEN.")
    inputs = ["targets", "gene_constraint", "gene_sets", "control_cells", "train_delta"]
    dependencies = ["additive_response"]

    def compute(self, ctx: FeatureContext, perts, params):
        rho, has = _residual(ctx)
        c = np.zeros(len(perts))
        for i, p in enumerate(perts):
            idx = [t for t in ctx.target_indices(p) if has[t]]
            if idx:
                c[i] = rho[idx].mean()
        add = ctx.feature("additive_response", perts)[:, :, 0]
        return (add * c[:, None])[:, :, None]
