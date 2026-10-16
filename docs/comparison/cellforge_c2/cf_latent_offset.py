"""CellForge idea: CPA-X, a "disentangled perturbation embedding" in a latent space "explicitly factorised:
perturbation effect on one axis" where a perturbation is an additive offset (gersteinlab/CellForge @6585ff9,
docs/MODELS.md:17, :31-40) and a gene embedding built from "gene ontology, pathway information"
(Method_Design/refinement.py:1022). (The template's embedding_dimension 128 at graph_discussion.py:872-879 belongs to
a cell-type proposal, so it is not cited.)

Our translation to a feature of a linear model (the implementation is ours, not CellForge's code): the latent space
is the top `rank` right-singular vectors of the training change profiles (leaving p out); each training
perturbation's latent code is its projection. An unseen perturbation gets no code of its own, so its code is the
kernel-weighted mean of the codes of training perturbations whose targets are near its targets in the physical
interaction graph (ppi_network, else prior_network taken undirected; cosine of neighbourhood profiles, raised to
`power`). The feature is that code decoded back to gene space. Without any related training perturbation it is zero.
"""
from __future__ import annotations

import numpy as np

from genemila.features.api import Feature, FeatureContext, register


def _neighbourhood(ctx: FeatureContext) -> np.ndarray:
    """(n_genes, n_genes) symmetric: self plus weighted interaction partners, built once per context."""
    if "cf_nbr" not in ctx.cache:
        a = np.eye(ctx.n_genes)
        gi = ctx.gene_index
        edges = ctx.knowledge("ppi_network") or [[x, y, 1.0] for x, y, _ in ctx.knowledge("prior_network") or []]
        for x, y, score in edges:
            if x in gi and y in gi and x != y:
                a[gi[x], gi[y]] += float(score)
                a[gi[y], gi[x]] += float(score)
        ctx.cache["cf_nbr"] = a
    return ctx.cache["cf_nbr"]


def _embed(ctx: FeatureContext, perts) -> np.ndarray:
    """Unit-norm neighbourhood profile of every perturbation's targets."""
    a = _neighbourhood(ctx)
    e = np.zeros((len(perts), ctx.n_genes))
    for i, p in enumerate(perts):
        for t in sorted(set(ctx.target_indices(p))):
            e[i] += a[t]
    norm = np.linalg.norm(e, axis=1, keepdims=True)
    return np.divide(e, norm, out=np.zeros_like(e), where=norm > 0)


@register
class CfLatentOffset(Feature):
    name = "cf_latent_offset"
    description = ("Low-rank (`rank` singular vectors) training change decoded from a latent code that p borrows "
                   "from training perturbations whose targets neighbour its own in the PPI graph (cosine kernel), "
                   "leaving p out. Translated by us from CellForge's CPA-X perturbation embedding.")
    rationale = ("Perturbation effects share a few latent programs; a physical partner of the target is likely to "
                 "sit at the same place in that space.")
    inputs = ["targets", "ppi_network", "prior_network", "train_delta"]
    params = {"rank": 10, "power": 2.0}

    def compute(self, ctx: FeatureContext, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        e = _embed(ctx, perts)
        train_e = dict(zip(ctx.train_perts, _embed(ctx, ctx.train_perts)))
        for i, p in enumerate(perts):
            names, d = ctx.train_delta(exclude=p)
            if not names:
                continue
            w = np.maximum(np.array([train_e[q] for q in names]) @ e[i], 0.0) ** params["power"]
            if w.sum() == 0:
                continue
            r = min(int(params["rank"]), len(names))
            _, _, vt = np.linalg.svd(d, full_matrices=False)
            v = vt[:r]
            out[i, :, 0] = ((w / w.sum()) @ (d @ v.T)) @ v
        return out
