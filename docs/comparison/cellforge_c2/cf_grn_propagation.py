"""CellForge idea: totalGAT, "graph attention over a gene interaction network, so the perturbation effect propagates
along known biology rather than through a dense layer" (gersteinlab/CellForge @6585ff9, docs/MODELS.md:108-109;
"Gene regulatory networks" as a model constraint, Method_Design/experts.py:583 and :696; refinement.py:941).

Our translation to a feature of a linear model (the implementation is ours, not CellForge's code): the perturbation
is a unit signal on its target genes, propagated k steps along the bundle's signed regulator -> target edges
(prior_network, CollecTRI; out-degree normalised, damped per step). Without that file the unsigned PPI graph stands
in; without both the feature is zero. No label is read. The sign of a knockdown's effect is left to the coefficient.
"""
from __future__ import annotations

import numpy as np

from genemila.features.api import Feature, FeatureContext, register


def _graph(ctx: FeatureContext) -> np.ndarray:
    """Row-normalised signed adjacency over the bundle's genes, built once per context."""
    if "cf_grn_w" in ctx.cache:
        return ctx.cache["cf_grn_w"]
    w = np.zeros((ctx.n_genes, ctx.n_genes))
    gi = ctx.gene_index
    net = ctx.knowledge("prior_network")
    if net:
        for a, b, sign in net:
            if a in gi and b in gi and a != b:
                w[gi[a], gi[b]] += float(sign)
    else:
        for a, b, score in ctx.knowledge("ppi_network") or []:
            if a in gi and b in gi and a != b:
                w[gi[a], gi[b]] += float(score)
                w[gi[b], gi[a]] += float(score)
    deg = np.abs(w).sum(axis=1, keepdims=True)
    w = np.divide(w, deg, out=np.zeros_like(w), where=deg > 0)
    ctx.cache["cf_grn_w"] = w
    return w


@register
class CfGrnPropagation(Feature):
    name = "cf_grn_propagation"
    description = ("Signed influence of p's targets on g after up to `steps` hops along regulator->target edges "
                   "(CollecTRI), damped per hop. Translated by us from CellForge's totalGAT network propagation.")
    rationale = ("A perturbed regulator changes its direct targets first, then theirs; propagating along the known "
                 "network reaches genes no training perturbation has touched.")
    inputs = ["targets", "prior_network", "ppi_network"]
    params = {"steps": 3, "damping": 0.5}

    def compute(self, ctx: FeatureContext, perts, params):
        w = _graph(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            idx = sorted(set(ctx.target_indices(p)))
            if not idx:
                continue
            x = np.zeros(ctx.n_genes)
            x[idx] = 1.0
            for k in range(int(params["steps"])):
                x = x @ w
                out[i, :, 0] += params["damping"] ** k * x
        return out
