"""CellForge idea: pathway constraints and "pathway modularity" as the biological prior of the model: the plan template
carries `pathway_constraints` (gersteinlab/CellForge @6585ff9, Method_Design/graph_discussion.py:865-869), a pathway
proposal over KEGG, Reactome, GO and MSigDB (graph_discussion.py:882-895) and the assumption "Pathway modularity ...
Known biological pathway organization" (Method_Design/refinement.py:302-306).

Our translation to a feature of a linear model (the implementation is ours, not CellForge's code): a perturbation is
described by the gene sets its targets belong to (gene_sets: Reactome, GO BP, Hallmark); its predicted change of g
is the mean change of the training perturbations whose targets share those sets, weighted by the Jaccard overlap of
the two set profiles, leaving p itself out. Without gene_sets, or without a sharing training perturbation, it is zero.
"""
from __future__ import annotations

import numpy as np

from genemila.features.api import Feature, FeatureContext, register


def _membership(ctx: FeatureContext) -> np.ndarray:
    """(n_genes, n_sets) 0/1 matrix of the bundle's gene sets, built once per context."""
    if "cf_sets" not in ctx.cache:
        sets = ctx.knowledge("gene_sets") or {}
        m = np.zeros((ctx.n_genes, len(sets)))
        for j, n in enumerate(sorted(sets)):
            m[[ctx.gene_index[g] for g in sets[n] if g in ctx.gene_index], j] = 1.0
        ctx.cache["cf_sets"] = m
    return ctx.cache["cf_sets"]


def _profiles(ctx: FeatureContext, perts) -> np.ndarray:
    """(len(perts), n_sets): 1 where a target of the perturbation is in the set."""
    m = _membership(ctx)
    x = np.zeros((len(perts), ctx.n_genes))
    for i, p in enumerate(perts):
        x[i, ctx.target_indices(p)] = 1.0
    return (x @ m > 0).astype(float)


@register
class CfPathwayTransfer(Feature):
    name = "cf_pathway_transfer"
    description = ("Mean training change of g over perturbations whose targets share gene sets with p's, weighted by "
                   "the Jaccard overlap of the set profiles, leaving p out. Translated by us from CellForge's "
                   "pathway-constraint idea.")
    rationale = ("Genes of one pathway, when perturbed, move the same downstream programs, so a pathway-mate's "
                 "measured response is a prior for an unseen member's.")
    inputs = ["targets", "gene_sets", "train_delta"]
    params = {"power": 1.0}

    def compute(self, ctx: FeatureContext, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        prof = _profiles(ctx, perts)
        if prof.shape[1] == 0:
            return out
        train_prof = dict(zip(ctx.train_perts, _profiles(ctx, ctx.train_perts)))
        for i, p in enumerate(perts):
            names, d = ctx.train_delta(exclude=p)
            if not names:
                continue
            tp = np.array([train_prof[q] for q in names])
            both = tp @ prof[i]
            either = tp.sum(axis=1) + prof[i].sum() - both
            w = np.divide(both, either, out=np.zeros(len(names)), where=either > 0) ** params["power"]
            if w.sum() > 0:
                out[i, :, 0] = (w / w.sum()) @ d
        return out
