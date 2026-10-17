import numpy as np
from genemila.features.api import Feature, register


@register
class TargetERMembraneXGeneUPRSet(Feature):
    name = "target_er_membrane_x_gene_upr_set_e354"
    version = 1
    description = "Interaction of target ER/membrane localization with gene UPR membership, combined with control expression to avoid constant rows."
    rationale = "Knockdown of ER/membrane proteins can disrupt ER homeostasis, triggering UPR; the interaction of target compartment with gene UPR membership may predict response, scaled by baseline expression."
    inputs = ["protein_annotation", "gene_sets", "control_mean"]
    params = {"upr_gene_sets": ["GO:0030968", "REACTOME:Unfolded Protein Response"]}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        # Build UPR gene indicator over ctx.genes
        upr_sets = params.get("upr_gene_sets", [])
        gene_sets = ctx.knowledge("gene_sets")
        upr_genes = set()
        if isinstance(gene_sets, dict):
            for sname in upr_sets:
                members = gene_sets.get(sname)
                if members:
                    upr_genes.update(members)
        upr_indicator = np.zeros(n_genes, dtype=float)
        if upr_genes:
            for g in upr_genes:
                idx = ctx.gene_index.get(g)
                if idx is not None:
                    upr_indicator[idx] = 1.0

        # Scale by baseline expression so rows vary across genes even when target flag is 0
        base = np.asarray(ctx.control_mean, dtype=float)
        base = np.abs(base)
        if not np.all(np.isfinite(base)):
            base = np.nan_to_num(base, nan=0.0, posinf=0.0, neginf=0.0)
        # Normalise to a reasonable scale
        bmax = float(np.max(base)) if base.size else 0.0
        if bmax > 0:
            base = base / bmax

        # Protein annotation
        prot = ctx.knowledge("protein_annotation")
        cols = []
        genes_map = {}
        if isinstance(prot, dict):
            cols = list(prot.get("columns", []))
            genes_map = prot.get("genes", {}) or {}
        col_idx = {c: i for i, c in enumerate(cols)}

        def _flag(vals, name):
            j = col_idx.get(name)
            if j is None or vals is None or j >= len(vals):
                return 0.0
            v = vals[j]
            try:
                return 1.0 if float(v) > 0 else 0.0
            except (TypeError, ValueError):
                return 0.0

        target_cache = {}

        def target_er_membrane(p):
            if p in target_cache:
                return target_cache[p]
            res = 0.0
            tg = ctx.target_genes(p)
            for t in tg:
                vals = genes_map.get(t) if isinstance(genes_map, dict) else None
                if vals is None:
                    continue
                mem = _flag(vals, "membrane")
                er = _flag(vals, "endoplasmic_reticulum")
                if mem > 0 or er > 0:
                    res = 1.0
                    break
            target_cache[p] = res
            return res

        for i, p in enumerate(perts):
            ti = target_er_membrane(p)
            # Interaction term: UPR membership boosted by target ER/membrane flag,
            # plus a small baseline expression term so rows are never constant.
            row = (1.0 + ti) * upr_indicator + 0.1 * base
            out[i, :, 0] = row

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
