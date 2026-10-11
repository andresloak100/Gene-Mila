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


def additive_delta(perts: list[str], targets: dict, train: list[str], train_delta: np.ndarray) -> np.ndarray:
    """baseline_additive's predicted change, the one rule the lab, the built-in additive_response below and
    tools/refit_visible.py share (here, so the feature cache key, the hash of this file, covers it): the sum over a
    perturbation's target genes (targets: perturbation -> its genes; sorted and without repeats, so the order a
    pair lists them changes nothing) of each gene's single change in `train` (the mean change in train_delta of
    the training perturbations whose one target it is) or, for a gene without a training single, the mean change of
    all training singles. A pair is Δ_A + Δ_B, a held-out single the mean single change; a perturbation without a
    listed target counts as one gene without a single. With no single in training at all, the mean training change
    stands in for the mean single change."""
    rows: dict[str, list[int]] = {}
    for i, p in enumerate(train):
        tg = targets.get(p) or []
        if len(tg) == 1:
            rows.setdefault(tg[0], []).append(i)
    single = {g: train_delta[r].mean(axis=0) for g, r in rows.items()}
    every = [i for r in rows.values() for i in r]
    fill = train_delta[every].mean(axis=0) if every else train_delta.mean(axis=0)
    out = np.zeros((len(perts), train_delta.shape[1]))
    for j, p in enumerate(perts):
        for g in sorted(set(targets.get(p) or [])) or [None]:
            out[j] += single.get(g, fill)
    return out


@register
class AdditiveResponse(Feature):
    # Built in only on a bundle whose targets include a pair of genes (registry.PAIR_BUILTIN_FEATURES; the lab registers
    # it nowhere else), where the starting model baseline_ridge_additive carries it: the additive baseline's predicted
    # change, leaving p out, so no agent model starts below the additive rule. The planner's feature registry shows the
    # first 70 characters of the description, so it opens with what the feature is. The Norman agents of 11 Oct 2026 (N3)
    # started from the three features above and never rebuilt the plain rule (docs/NORMAN_PLAN.md, section 8).
    name = "additive_response"
    description = ("The additive baseline's prediction: the sum over p's target genes of each gene's single-gene "
                   "training change (the mean change of the training perturbations whose one target is that gene), "
                   "with the mean single-gene training change for a gene without one, leaving p out.")
    rationale = ("A pair of genes often changes expression by about the sum of its genes' single-gene changes, so the "
                 "training singles predict pairs whose genes were each perturbed alone.")
    inputs = ["train_delta", "targets"]

    def compute(self, ctx: FeatureContext, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            names, d = ctx.train_delta(exclude=p)
            if not names:
                continue
            out[i, :, 0] = additive_delta([p], {q: ctx.target_genes(q) for q in [*names, p]}, names, d)[0]
        return out
