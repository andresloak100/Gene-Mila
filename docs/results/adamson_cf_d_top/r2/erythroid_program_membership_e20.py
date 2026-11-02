import numpy as np
from genemila.features.api import Feature, register


@register
class ErythroidProgramMembershipE20(Feature):
    name = "erythroid_program_membership_e20"
    version = 1
    description = (
        "Binary indicator: 1 if gene g is in carbon dioxide transport / oxygen "
        "transport / erythrocyte differentiation gene sets, is a prior_network "
        "neighbor of GATA1 or NFE2, or is a globin gene; else 0."
    )
    rationale = (
        "Residual component 1 is enriched for GATA1/NFE2 neighbors and carbon "
        "dioxide transport genes (HBZ, HBA1, HBG2, ...), suggesting a shared "
        "erythroid-lineage response program across perturbations."
    )
    inputs = ["gene_sets"]
    params = {}
    dim = 1

    _GLOBINS = ("HBZ", "HBA1", "HBA2", "HBG1", "HBG2", "HBB", "HBD")
    _GENE_SET_KEYS = (
        "GOBP:carbon dioxide transport",
        "GOBP:oxygen transport",
        "GOBP:erythrocyte differentiation",
    )
    _HUB_GENES = ("GATA1", "NFE2")

    def _build_membership(self, ctx):
        members = set()

        # Gene sets
        gs = ctx.knowledge("gene_sets")
        if isinstance(gs, dict):
            for key in self._GENE_SET_KEYS:
                genes = gs.get(key)
                if genes:
                    members.update(str(g) for g in genes)

        # prior_network neighbors of GATA1 / NFE2
        pn = ctx.knowledge("prior_network")
        if pn:
            hubs = set(self._HUB_GENES)
            for edge in pn:
                try:
                    a, b = edge[0], edge[1]
                except (IndexError, TypeError):
                    continue
                a = str(a)
                b = str(b)
                if a in hubs:
                    members.add(b)
                elif b in hubs:
                    members.add(a)

        # Globin genes
        members.update(self._GLOBINS)

        # Map to gene columns
        membership = np.zeros(ctx.n_genes, dtype=np.float64)
        gi = ctx.gene_index
        for g in members:
            idx = gi.get(g)
            if idx is not None:
                membership[idx] = 1.0
        return membership

    def compute(self, ctx, perts, params):
        key = "erythroid_program_membership_e20__membership"
        membership = ctx.cache.get(key)
        if membership is None:
            membership = self._build_membership(ctx)
            ctx.cache[key] = membership

        n = len(perts)
        out = np.empty((n, ctx.n_genes, 1), dtype=np.float64)
        out[:, :, 0] = membership[None, :]
        return out
