import numpy as np
from genemila.features.api import Feature, register


@register
class ErythroidTfTargetMembershipE48(Feature):
    name = "erythroid_tf_target_membership_e48"
    version = 1
    description = (
        "Binary feature: 1 if gene g is in GATA1 or NFE2 target gene sets "
        "(or prior_network neighbors), else 0."
    )
    rationale = (
        "GATA1 and NFE2 are erythroid transcription factors that regulate a "
        "coordinated program; genes in their target sets may respond similarly "
        "to perturbations affecting this program."
    )
    inputs = ["gene_sets", "prior_network"]
    params = {
        "sources": [
            "gene_sets:GATA1",
            "gene_sets:NFE2",
            "prior_network:GATA1",
            "prior_network:NFE2",
        ]
    }
    dim = 1

    def _build_membership(self, ctx, sources):
        members = set()

        gene_sets = ctx.knowledge("gene_sets")
        prior_network = ctx.knowledge("prior_network")

        for src in sources:
            if not isinstance(src, str) or ":" not in src:
                continue
            kind, key = src.split(":", 1)
            kind = kind.strip().lower()
            key = key.strip()

            if kind == "gene_sets":
                if not isinstance(gene_sets, dict):
                    continue
                # Direct exact key match.
                entry = gene_sets.get(key)
                if entry is None:
                    # Try case-insensitive / suffix matching against keys.
                    key_up = key.upper()
                    for k, v in gene_sets.items():
                        if not isinstance(k, str):
                            continue
                        k_up = k.upper()
                        if k_up == key_up or k_up.endswith(":" + key_up) or k_up.endswith("_" + key_up):
                            entry = v
                            break
                if isinstance(entry, (list, tuple, set)):
                    for g in entry:
                        if isinstance(g, str):
                            members.add(g)

            elif kind == "prior_network":
                if not isinstance(prior_network, (list, tuple)):
                    continue
                key_up = key.upper()
                for edge in prior_network:
                    if not isinstance(edge, (list, tuple)) or len(edge) < 2:
                        continue
                    a, b = edge[0], edge[1]
                    if not isinstance(a, str) or not isinstance(b, str):
                        continue
                    if a.upper() == key_up:
                        members.add(b)
                    if b.upper() == key_up:
                        members.add(a)

        return members

    def compute(self, ctx, perts, params, **kwargs):
        sources = params.get("sources", self.params["sources"])
        if isinstance(sources, str):
            sources = [sources]

        cache_key = ("erythroid_tf_target_membership_e48", tuple(sources))
        if cache_key in ctx.cache:
            members = ctx.cache[cache_key]
        else:
            members = self._build_membership(ctx, sources)
            ctx.cache[cache_key] = members

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        members_up = {m.upper() for m in members if isinstance(m, str)}
        if members_up:
            for j, g in enumerate(ctx.genes):
                if isinstance(g, str) and g.upper() in members_up:
                    out[:, j, 0] = 1.0
        return out
