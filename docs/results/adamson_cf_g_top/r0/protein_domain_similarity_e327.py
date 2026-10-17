import numpy as np
from genemila.features.api import Feature, register


@register
class ProteinDomainSimilarityE327(Feature):
    name = "protein_domain_similarity_e327"
    version = 1
    description = "Jaccard similarity of protein domain sets between perturbation target and gene."
    rationale = ("Protein domains reflect conserved functional units; shared domains may indicate "
                 "similar interaction partners or regulatory roles, so genes sharing domains with "
                 "the perturbed target may show larger expression changes.")
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        ann = ctx.knowledge("protein_annotation")
        if ann is None:
            return out

        genes_tbl = ann.get("genes", {}) or {}
        columns = ann.get("columns", []) or []

        # Identify domain-like columns. The documented columns are protein_length,
        # has_signal_peptide, signal_peptide_length, n_transmembrane, and then
        # compartment 0/1 flags. We treat the compartment flags as a domain-like
        # feature set (functional localization signature) since no explicit
        # Pfam/InterPro domain columns are provided.
        flag_cols = []
        for j, c in enumerate(columns):
            cl = str(c).lower()
            if cl in ("protein_length", "signal_peptide_length", "n_transmembrane"):
                continue
            if cl.startswith("has_") or cl in (
                "secreted", "membrane", "endoplasmic_reticulum", "golgi",
                "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
            ):
                flag_cols.append(j)
        if not flag_cols:
            # Fallback: any trailing 0/1-looking columns beyond the first 4
            flag_cols = list(range(4, len(columns)))

        # Resolve gene -> row index in annotation table
        gene_row = {}
        for sym, vals in genes_tbl.items():
            gene_row[sym] = vals

        def get_set(sym):
            vals = gene_row.get(sym)
            if vals is None:
                return frozenset()
            s = set()
            for j in flag_cols:
                if j >= len(vals):
                    continue
                v = vals[j]
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv) and fv > 0.5:
                    s.add(columns[j])
            return frozenset(s)

        # Precompute gene sets for all genes
        gene_sets = [get_set(g) for g in ctx.genes]

        cache = ctx.cache
        key = "_e327_sets"
        if key not in cache:
            cache[key] = gene_sets
        gene_sets = cache[key]

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                continue
            tset = frozenset()
            for t in tg:
                tset = tset | get_set(t)
            if not tset:
                continue
            tset_size = len(tset)
            for g_idx in range(n_genes):
                gset = gene_sets[g_idx]
                if not gset:
                    continue
                inter = len(tset & gset)
                if inter == 0:
                    continue
                union = tset_size + len(gset) - inter
                if union > 0:
                    out[i, g_idx, 0] = inter / union

        out[~np.isfinite(out)] = 0.0
        return out
