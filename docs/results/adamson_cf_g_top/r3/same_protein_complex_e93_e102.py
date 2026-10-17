import numpy as np
from genemila.features.api import Feature, register


@register
class SameProteinComplexE93E102(Feature):
    name = "same_protein_complex_e93_e102"
    version = 1
    description = "Binary indicator: 1 if target and gene g are annotated to the same protein complex (protein_annotation / PPI), else 0."
    rationale = "Perturbing a complex member may destabilize the entire complex, causing coordinated expression changes of other members."
    inputs = ["protein_annotation", "ppi_network", "targets"]
    params = {"source": "protein_annotation"}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        G = ctx.n_genes
        out = np.zeros((n, G, 1), dtype=float)

        source = str(params.get("source", "protein_annotation"))

        # Build gene -> set of complex tags. Prefer protein_annotation compartment
        # flags (co-localization as a proxy for complex membership); optionally
        # augment with PPI connected-component membership.
        ann = ctx.knowledge("protein_annotation")
        ppi = ctx.knowledge("ppi_network")

        gene_tags = {}

        def add_tag(g, tag):
            s = gene_tags.get(g)
            if s is None:
                s = set()
                gene_tags[g] = s
            s.add(tag)

        use_ann = source in ("protein_annotation", "both", "all") or ann is not None
        use_ppi = source in ("ppi_network", "ppi", "both", "all")

        if ann is not None and use_ann:
            cols = ann.get("columns", [])
            genes_map = ann.get("genes", {}) or {}
            flag_cols = [c for c in cols if c in (
                "secreted", "membrane", "endoplasmic_reticulum", "golgi",
                "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome"
            )]
            struct_cols = [c for c in cols if c in (
                "has_signal_peptide", "n_transmembrane"
            )]
            idx = {c: i for i, c in enumerate(cols)}
            for g, vals in genes_map.items():
                if not vals:
                    continue
                for c in flag_cols:
                    i = idx.get(c)
                    if i is None:
                        continue
                    v = vals[i]
                    if v is not None and float(v) > 0:
                        add_tag(g, "ann:" + c)
                for c in struct_cols:
                    i = idx.get(c)
                    if i is None:
                        continue
                    v = vals[i]
                    if v is not None:
                        fv = float(v)
                        if c == "has_signal_peptide" and fv > 0:
                            add_tag(g, "ann:signal_peptide")
                        elif c == "n_transmembrane" and fv > 0:
                            add_tag(g, "ann:transmembrane")

        if ppi is not None and use_ppi:
            # Build connected components of the PPI graph (union-find).
            edges = []
            nodes = set()
            for e in ppi:
                if not e or len(e) < 2:
                    continue
                a, b = e[0], e[1]
                nodes.add(a)
                nodes.add(b)
                edges.append((a, b))
            parent = {x: x for x in nodes}

            def find(x):
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x

            def union(a, b):
                ra, rb = find(a), find(b)
                if ra != rb:
                    parent[ra] = rb

            for a, b in edges:
                union(a, b)
            comp_sizes = {}
            for x in nodes:
                r = find(x)
                comp_sizes[r] = comp_sizes.get(r, 0) + 1
            # Stable component id: use the sorted representative node name.
            for x in nodes:
                r = find(x)
                if comp_sizes.get(r, 0) >= 2:
                    add_tag(x, "ppi:" + str(r))

        gene_index = ctx.gene_index
        col_tags = [None] * G
        for g, s in gene_tags.items():
            ci = gene_index.get(g)
            if ci is not None:
                col_tags[ci] = frozenset(s)

        for i, p in enumerate(perts):
            try:
                tgt_idx = ctx.target_indices(p)
            except Exception:
                tgt_idx = []
            if not tgt_idx:
                continue
            tgt_tags = set()
            for ti in tgt_idx:
                if 0 <= ti < G and col_tags[ti] is not None:
                    tgt_tags.update(col_tags[ti])
            if not tgt_tags:
                continue
            tgt_tags = frozenset(tgt_tags)
            for gi in range(G):
                ct = col_tags[gi]
                if ct is not None and not ct.isdisjoint(tgt_tags):
                    out[i, gi, 0] = 1.0

        return out
