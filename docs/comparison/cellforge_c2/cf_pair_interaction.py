"""CellForge idea: scGen-X for Norman, "latent arithmetic over gene pairs with a non-additive interaction term":
"scGen-X keeps the latent-arithmetic backbone and adds an explicit interaction term for gene pairs, so the model can
represent synergy and antagonism rather than being forced into additivity" (gersteinlab/CellForge @6585ff9,
docs/MODELS.md:18, :54-56; the template's element_wise_multiplication at graph_discussion.py:872-879 is a cell-type
proposal, not this term, so it is not cited).

Our translation to a feature of a linear model (the implementation is ours, not CellForge's code): the additive
part is already the lab's additive_response, so this file carries only the interaction. For a perturbation of
several genes whose single-gene changes are all in training (leaving p out), two columns per gene g: the product of
the singles' changes (synergy or antagonism scales with both) and the sign-aware minimum (the weaker single bounds
the pair: buffering; zero where the singles disagree in sign). A single-gene perturbation, or a pair with a gene
never perturbed alone in training, has no interaction and both columns are zero, so on a bundle without pairs the
feature is constant and the comparison tool rejects it as such. Under gene-grouped folds (pipeline.cv_folds_of, what
feature_compare uses on a bundle with pairs) a predicted pair always has a single hidden from the view, so the term is
zero on every out-of-fold predicted row by construction: that tier cannot measure it. Only a tier whose pairs have
both singles in the full training set can (val1's seen-2 pairs with --with-val1; the sealed split).
"""
from __future__ import annotations

import numpy as np

from genemila.features.api import Feature, FeatureContext, register


def _singles(ctx: FeatureContext, names, d) -> dict:
    """gene -> mean training change of the perturbations whose one target is that gene."""
    rows: dict = {}
    for i, q in enumerate(names):
        tg = ctx.target_genes(q)
        if len(tg) == 1:
            rows.setdefault(tg[0], []).append(i)
    return {g: d[r].mean(axis=0) for g, r in rows.items()}


@register
class CfPairInteraction(Feature):
    name = "cf_pair_interaction"
    description = ("For a perturbation of several genes with every single in training: the product of the singles' "
                   "changes and their sign-aware minimum, per gene, leaving p out; zero otherwise. Translated by us "
                   "from CellForge's scGen-X pair interaction term.")
    rationale = ("Two activated genes rarely add exactly: a shared pathway saturates (the weaker single bounds the "
                 "pair) or cooperates (the product grows), and the fitted coefficients tell which.")
    inputs = ["targets", "train_delta"]
    dim = 2

    def compute(self, ctx: FeatureContext, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 2))
        for i, p in enumerate(perts):
            tg = sorted(set(ctx.target_genes(p)))
            if len(tg) < 2:
                continue
            names, d = ctx.train_delta(exclude=p)
            single = _singles(ctx, names, d)
            if any(g not in single for g in tg):
                continue
            s = np.array([single[g] for g in tg])
            prod = np.prod(s, axis=0)
            agree = np.all(np.sign(s) == np.sign(s[0]), axis=0)
            out[i, :, 0] = prod
            out[i, :, 1] = np.where(agree, np.sign(s[0]) * np.abs(s).min(axis=0), 0.0)
        return out
