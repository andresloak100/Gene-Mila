import numpy as np
from genemila.features.api import Feature, register


@register
class ProteinDomainOverlapTargetGene(Feature):
    name = "protein_domain_overlap_target_gene_e270"
    version = 1
    description = ("Jaccard similarity between protein domain sets of the perturbation "
                   "target and gene g, using prior protein/gene-set annotations.")
    rationale = ("Proteins sharing domains often act in the same complexes or pathways; "
                 "perturbing a target may perturb partners sharing domains.")
    inputs = ["knowledge"]
    params = {"domain_source": "interpro"}
    dim = 1

    def _build_domain_sets(self, ctx, params):
        cache = ctx.cache
        key = ("protein_domains", params.get("domain_source", "interpro"))
        if key in cache:
            return cache[key]

        source = params.get("domain_source", "interpro")
        domain_sets = {}  # gene symbol -> set of domain strings

        # Try gene_sets (e.g. INTERPRO / PFAM / REACTOME style keys) first.
        gs = ctx.knowledge("gene_sets")
        if isinstance(gs, dict):
            prefixes = []
            if source == "interpro":
                prefixes = ["INTERPRO", "IPR", "PFAM", "Pfam", "DOMAIN"]
            elif source == "pfam":
                prefixes = ["PFAM", "Pfam", "INTERPRO"]
            else:
                prefixes = [source.upper(), source]
            for set_name, genes in gs.items():
                if not isinstance(set_name, str) or not isinstance(genes, (list, tuple)):
                    continue
                up = set_name.upper()
                matched = False
                for pref in prefixes:
                    if up.startswith(pref.upper() + ":") or up.startswith(pref.upper() + "_"):
                        matched = True
                        break
                if not matched:
                    continue
                dom = set_name
                for g in genes:
                    if isinstance(g, str):
                        domain_sets.setdefault(g, set()).add(dom)

        # Fallback: protein_annotation may carry domain-like flags; if no domains found,
        # use compartment flags as a coarse "domain" proxy so feature is still non-trivial.
        if not domain_sets:
            pa = ctx.knowledge("protein_annotation")
            if isinstance(pa, dict) and isinstance(pa.get("genes"), dict):
                cols = pa.get("columns", [])
                flag_cols = [i for i, c in enumerate(cols)
                             if isinstance(c, str) and c in (
                                 "secreted", "membrane", "endoplasmic_reticulum", "golgi",
                                 "mitochondrion", "nucleus", "cytoplasm", "lysosome",
                                 "peroxisome")]
                for g, vals in pa["genes"].items():
                    s = set()
                    if isinstance(vals, (list, tuple)):
                        for i in flag_cols:
                            if i < len(vals) and vals[i] is not None:
                                try:
                                    if float(vals[i]) > 0:
                                        s.add("PA:" + str(cols[i]))
                                except (TypeError, ValueError):
                                    pass
                    if s:
                        domain_sets[g] = s

        cache[key] = domain_sets
        return domain_sets

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=float)
        domain_sets = self._build_domain_sets(ctx, params)
        if not domain_sets:
            return out

        genes = ctx.genes
        gene_domains = [domain_sets.get(g, None) for g in genes]

        for i, p in enumerate(perts):
            tgt_genes = ctx.target_genes(p)
            tgt_dom = set()
            for tg in tgt_genes:
                ds = domain_sets.get(tg)
                if ds:
                    tgt_dom |= ds
            if not tgt_dom:
                continue
            for j in range(n_genes):
                gd = gene_domains[j]
                if not gd:
                    continue
                inter = len(tgt_dom & gd)
                if inter == 0:
                    continue
                union = len(tgt_dom | gd)
                if union > 0:
                    out[i, j, 0] = inter / union
        return out
