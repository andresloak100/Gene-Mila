import numpy as np
from genemila.features.api import Feature, register


@register
class CarbonDioxideTransportMembershipE85(Feature):
    name = "carbon_dioxide_transport_membership_e85"
    version = 1
    description = "Binary feature: 1 if gene g is in the GOBP:carbon dioxide transport gene set, else 0."
    rationale = ("Genes involved in carbon dioxide transport form a coordinated erythroid/gas "
                 "transport module that may respond strongly to perturbations, capturing residual "
                 "functional structure not explained by generic response or target identity.")
    inputs = ["gene_sets"]
    params = {"gene_set_name": "GOBP:carbon dioxide transport"}
    dim = 1

    def compute(self, ctx, perts, params):
        gene_set_name = params.get("gene_set_name", "GOBP:carbon dioxide transport")
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        knowledge = ctx.knowledge("gene_sets")
        members = set()
        if isinstance(knowledge, dict):
            raw = knowledge.get(gene_set_name)
            if raw is None and "genes" in knowledge and isinstance(knowledge["genes"], dict):
                raw = knowledge["genes"].get(gene_set_name)
            if raw is not None:
                members = set(raw)
        elif isinstance(knowledge, list):
            for entry in knowledge:
                if isinstance(entry, dict) and entry.get("name") == gene_set_name:
                    members = set(entry.get("genes", []))
                    break
                if isinstance(entry, (list, tuple)) and len(entry) == 2 and entry[0] == gene_set_name:
                    members = set(entry[1])
                    break

        if not members:
            return out

        mask = np.zeros(ctx.n_genes, dtype=float)
        for i, g in enumerate(ctx.genes):
            if g in members:
                mask[i] = 1.0

        out[:, :, 0] = mask[None, :]
        return out
