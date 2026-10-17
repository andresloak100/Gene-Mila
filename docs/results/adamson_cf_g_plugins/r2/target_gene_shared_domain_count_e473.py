import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneSharedDomainCountE473(Feature):
    name = "target_gene_shared_domain_count_e473"
    version = 1
    description = "Number of shared protein domains/families between the perturbation target and gene g."
    rationale = ("Proteins sharing specific domains are often functionally linked and co-regulated; "
                 "domain overlap between a CRISPR target and a gene may predict that gene's response.")
    inputs = ["protein_annotation", "target_indices"]
    params = {}
    dim = 1

    # Columns in protein_annotation that are NOT domains (numeric / compartment / length features).
    _NON_DOMAIN_COLUMNS = {
        "protein_length", "has_signal_peptide", "signal_peptide_length", "n_transmembrane",
        "secreted", "membrane", "endoplasmic_reticulum", "golgi", "mitochondrion",
        "nucleus", "cytoplasm", "lysosome", "peroxisome",
    }

    def _build_domain_sets(self, ctx, annot):
        """Return dict gene -> frozenset of domain tokens, plus the ordered list of domain columns."""
        genes = annot.get("genes", {}) or {}
        columns = annot.get("columns", []) or []

        # Identify domain-like columns: any column not in the known non-domain set.
        domain_cols = [c for c in columns if c not in self._NON_DOMAIN_COLUMNS]

        # Fallback: if no explicit domain columns, treat compartment flags as coarse "families".
        if not domain_cols:
            domain_cols = [c for c in columns if c in ("secreted", "membrane",
                                                       "endoplasmic_reticulum", "golgi",
                                                       "mitochondrion", "nucleus",
                                                       "cytoplasm", "lysosome", "peroxisome")]

        col_idx = {c: i for i, c in enumerate(columns)}
        dom_col_idx = [col_idx[c] for c in domain_cols if c in col_idx]

        domain_sets = {}
        for g, vals in genes.items():
            if vals is None:
                domain_sets[g] = frozenset()
                continue
            toks = set()
            for j in dom_col_idx:
                if j < len(vals):
                    v = vals[j]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        # Non-numeric domain token: use its string value directly.
                        toks.add((domain_cols[dom_col_idx.index(j)], str(v)))
                        continue
                    if fv != 0.0:
                        toks.add((domain_cols[dom_col_idx.index(j)],))
            domain_sets[g] = frozenset(toks)
        return domain_sets

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        annot = ctx.knowledge("protein_annotation")
        if annot is None:
            return out

        cache_key = "_e473_domain_sets"
        if cache_key in ctx.cache:
            domain_sets = ctx.cache[cache_key]
        else:
            domain_sets = self._build_domain_sets(ctx, annot)
            ctx.cache[cache_key] = domain_sets

        gene_index = ctx.gene_index
        n_genes = ctx.n_genes

        # Precompute per-gene domain sets aligned to column order (empty for missing genes).
        gene_domains = [domain_sets.get(g, frozenset()) for g in ctx.genes]

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # Union of domain sets over all target genes for this perturbation.
            tgt_domains = set()
            for ti in tgt_idx:
                if 0 <= ti < n_genes:
                    tgt_domains.update(gene_domains[ti])
            if not tgt_domains:
                continue
            tgt_domains = frozenset(tgt_domains)

            row = out[i, :, 0]
            for gi in range(n_genes):
                gd = gene_domains[gi]
                if gd:
                    row[gi] = float(len(tgt_domains & gd))

        return out
