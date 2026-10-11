"""Baseline features. Agents add new ones in genemila/features/plugins/."""

from __future__ import annotations

import numpy as np

from .api import Feature, FeatureContext, register


@register
class ControlMean(Feature):
    name = "control_mean"
    description = "Mean expression of gene g in control cells."
    rationale = "Highly expressed genes have more room to change; captures scale effects."
    inputs = ["control_cells"]

    def compute(self, ctx: FeatureContext, perts, params):
        return np.broadcast_to(ctx.control_mean[None, :, None], (len(perts), ctx.n_genes, 1)).copy()


@register
class MeanResponse(Feature):
    name = "mean_response"
    description = "Average delta of gene g across training perturbations, leaving p out."
    rationale = "Many perturbations share a generic stress/response program."
    inputs = ["train_delta"]

    def compute(self, ctx: FeatureContext, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            out[i, :, 0] = d.mean(axis=0)
        return out


@register
class IsTarget(Feature):
    # 1 on every target of p, so a pair marks both of its genes. The description is shown to the planner (feature
    # registry of the research state) and stays as every Adamson run read it; the rationale, stored with the feature
    # and never sent in a prompt, is worded for any modality (docs/NORMAN_PLAN.md section 4, item 11).
    name = "is_target"
    description = "1 if gene g is the gene targeted by perturbation p, else 0."
    rationale = ("A perturbation acts first on its own targets' expression: a knockdown lowers it, an activation "
                 "raises it.")
    inputs = ["targets"]

    def compute(self, ctx: FeatureContext, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            out[i, ctx.target_indices(p), 0] = 1.0
        return out
