"""The lead's hand-written hypothesis (docs/ROADMAP.md D4; docs/PREREG_G_KNOWN_BIOLOGY.md family 8): constraint
residualised on control expression and tier-1 essentiality proxies, times additive_response. A human hypothesis,
scored by tools/feature_compare.py and reported as such, never as GOAL_CRITERIA A.1. Fixed before any block G score
exists.

Per output gene j of the bundle: constraint s_j = -oe_lof_upper_j (minus LOEUF, so larger means more constrained),
from ctx.knowledge("gene_constraint"); genes without a value are left out of the fit and get c = 0 below.
Confounds, per gene: x1_j = log1p(ctx.control_mean[j]) (basal expression); e_j = 1 if gene j belongs to any
CORUM complex set ("CORUM:" prefix) in ctx.knowledge("gene_sets"), else 0; r_j = 1 if it belongs to any Reactome
set ("REACTOME:" prefix) whose name contains ribosom, proteasom or spliceosom (case-insensitive), else 0. Without
gene_sets or without such sets the indicators are all zero and the residual removes basal expression only.
Fit, once per context (cached on ctx.cache), ordinary least squares over the genes that have a constraint value:
s_j ~ 1 + x1_j + e_j + r_j; residual rho_j = s_j - fitted_j; genes without a value get rho_j = 0.
Per perturbation p: c_p = mean of rho over p's target genes that have a constraint value (targets outside the bundle
or without a value skipped; no such target gives c_p = 0).
Output (len(perts), n_genes, 1): additive_response[i, :] * c_p, so the candidate is proportional to a parent column
and feature_compare applies both nulls (the gene null and the perturbation null).
"""
from __future__ import annotations

import numpy as np

from genemila.features.api import Feature, FeatureContext, register

ESSENTIAL_WORDS = ("ribosom", "proteasom", "spliceosom")


def _residual(ctx: FeatureContext) -> tuple[np.ndarray, np.ndarray]:
    """(rho, has): the OLS residual of -LOEUF on 1, log1p(control_mean), CORUM membership and Reactome
    ribosome/proteasome/spliceosome membership over the genes with a value, and which genes have one."""
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
            x = np.column_stack([np.ones(n), np.log1p(ctx.control_mean), e, r])[has]
            beta = np.linalg.lstsq(x, s[has], rcond=None)[0]
            rho[has] = s[has] - x @ beta
        ctx.cache["h8_residual"] = (rho, has)
    return ctx.cache["h8_residual"]


@register
class H8ConstraintResidual(Feature):
    name = "h8_constraint_residual"
    description = ("additive_response times the mean, over p's targets with a gnomAD value, of -LOEUF residualised "
                   "(OLS) on log1p control mean, CORUM membership and Reactome ribosome/proteasome/spliceosome "
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
