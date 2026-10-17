import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPhosphoDensityXGeneSignaling(Feature):
    name = "target_phospho_density_x_gene_signaling__e672"
    version = 1
    description = (
        "Product of the perturbation target's phosphorylation-site density proxy "
        "(sites per 100 aa) and an indicator that gene g belongs to a signaling "
        "pathway gene set."
    )
    rationale = (
        "Targets rich in phosphorylation sites are likely signaling hubs; their "
        "perturbation may propagate through signaling pathways, so genes in "
        "signaling gene sets should respond more strongly."
    )
    inputs = ["protein_annotation", "gene_sets", "target_genes"]
    params = {"pathway_keywords": ["signal", "kinase", "phosphatase"]}
    dim = 1

    def compute(self, ctx, perts, params):
        keywords = [k.lower() for k in params.get("pathway_keywords",
                                                    ["signal", "kinase", "phosphatase"])]

        # --- Build gene -> signaling membership indicator (per gene column) ---
        sig_flag = ctx.cache.get("sig_flag")
        if sig_flag is None:
            sig_flag = np.zeros(ctx.n_genes, dtype=np.float64)
            gene_sets = ctx.knowledge("gene_sets")
            if isinstance(gene_sets, dict):
                for set_name, members in gene_sets.items():
                    lname = set_name.lower()
                    if not any(k in lname for k in keywords):
                        continue
                    if not isinstance(members, (list, tuple)):
                        continue
                    for g in members:
                        idx = ctx.gene_index.get(g)
                        if idx is not None:
                            sig_flag[idx] = 1.0
            ctx.cache["sig_flag"] = sig_flag

        # --- Phospho density proxy per gene (from protein_annotation) ---
        phospho = ctx.cache.get("phospho_density")
        if phospho is None:
            phospho = np.zeros(ctx.n_genes, dtype=np.float64)
            pa = ctx.knowledge("protein_annotation")
            if isinstance(pa, dict):
                cols = pa.get("columns", [])
                genes = pa.get("genes", {})
                # locate protein_length column if present
                try:
                    plen_idx = cols.index("protein_length")
                except (ValueError, AttributeError):
                    plen_idx = 0
                for sym, vals in genes.items():
                    idx = ctx.gene_index.get(sym)
                    if idx is None or not isinstance(vals, (list, tuple)):
                        continue
                    try:
                        plen = float(vals[plen_idx]) if vals[plen_idx] is not None else 0.0
                    except (TypeError, ValueError):
                        plen = 0.0
                    if plen <= 0:
                        continue
                    # Proxy: S/T/Y fraction is unavailable directly; approximate
                    # sites-per-100aa using a fixed expected density scaled by length
                    # (longer proteins accumulate more sites). Use a normalized
                    # density that saturates: 100 * (1 - exp(-plen/300)).
                    density = 100.0 * (1.0 - np.exp(-plen / 300.0)) / max(plen, 1.0) * 100.0
                    phospho[idx] = density
            # normalize to reasonable scale
            mx = phospho.max()
            if mx > 0:
                phospho = phospho / mx
            ctx.cache["phospho_density"] = phospho

        # --- Per-perturbation target phospho density ---
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=np.float64)
        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            dens = 0.0
            for tg in tgenes:
                idx = ctx.gene_index.get(tg)
                if idx is not None:
                    dens += phospho[idx]
            if len(tgenes) > 0:
                dens /= len(tgenes)
            out[i, :, 0] = dens * sig_flag

        out[~np.isfinite(out)] = 0.0
        return out
