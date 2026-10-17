import numpy as np
from genemila.features.api import Feature, register


@register
class ComplexMemberTargetLoeufInteractionE116(Feature):
    name = "complex_member_target_loeuf_interaction_e116"
    version = 1
    description = (
        "For each (perturbation p, gene g), the product of a complex-sharing score "
        "between the target of p and g (1 if they share a protein complex, else a "
        "continuous score) and the target's LOEUF (oe_lof_upper, median-filled)."
    )
    rationale = (
        "If gene g and the target are in the same protein complex, loss of a complex "
        "member can destabilize the complex and drive compensatory upregulation of "
        "other members; this effect should be stronger for essential (low LOEUF) "
        "targets. Multiplying complex sharing by target LOEUF encodes this gating."
    )
    inputs = ["target_genes", "control_mean", "knowledge"]
    params = {}
    dim = 1

    def _loeuf_map(self, ctx):
        cache = ctx.cache
        key = "_e116_loeuf_map"
        if key in cache:
            return cache[key]
        loeuf = {}
        kn = ctx.knowledge("gene_constraint")
        if kn is not None:
            cols = list(kn.get("columns", []))
            units = kn.get("column_units", {})
            # locate the LOEUF column robustly
            idx = None
            for cand in ("oe_lof_upper", "LOEUF", "loeuf"):
                if cand in cols:
                    idx = cols.index(cand)
                    break
            if idx is None:
                # fall back: any column whose unit mentions LOEUF
                for i, c in enumerate(cols):
                    u = str(units.get(c, "")).lower()
                    if "loeuf" in u or "oe_lof_upper" in u:
                        idx = i
                        break
            genes = kn.get("genes", {})
            if idx is not None:
                for g, vals in genes.items():
                    try:
                        v = vals[idx]
                    except Exception:
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except Exception:
                        continue
                    if np.isfinite(fv):
                        loeuf[g] = fv
        cache[key] = loeuf
        return loeuf

    def _complex_sets(self, ctx):
        cache = ctx.cache
        key = "_e116_complex_sets"
        if key in cache:
            return cache[key]
        # Build gene -> set of complex ids from gene_sets entries whose key looks
        # like a complex (CORUM / complex-like), plus PPI-based fallback.
        gene_to_complexes = {}
        kn = ctx.knowledge("gene_sets")
        if isinstance(kn, dict):
            for set_name, members in kn.items():
                nm = str(set_name).lower()
                if ("complex" in nm) or ("corum" in nm):
                    if not isinstance(members, (list, tuple)):
                        continue
                    for g in members:
                        gene_to_complexes.setdefault(g, set()).add(set_name)
        cache[key] = gene_to_complexes
        return gene_to_complexes

    def _ppi_neighbors(self, ctx):
        cache = ctx.cache
        key = "_e116_ppi_neighbors"
        if key in cache:
            return cache[key]
        nb = {}
        kn = ctx.knowledge("ppi_network")
        if isinstance(kn, list):
            for edge in kn:
                if not isinstance(edge, (list, tuple)) or len(edge) < 3:
                    continue
                a, b, w = edge[0], edge[1], edge[2]
                try:
                    w = float(w)
                except Exception:
                    w = 1.0
                if not np.isfinite(w):
                    w = 1.0
                nb.setdefault(a, {})[b] = max(nb.get(a, {}).get(b, 0.0), w)
                nb.setdefault(b, {})[a] = max(nb.get(b, {}).get(a, 0.0), w)
        cache[key] = nb
        return nb

    def compute(self, ctx, perts, params):
        n = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n, n_genes, 1), dtype=float)

        loeuf_map = self._loeuf_map(ctx)
        gene_to_complexes = self._complex_sets(ctx)
        ppi_nb = self._ppi_neighbors(ctx)

        # median LOEUF for filling missing targets
        if loeuf_map:
            vals = np.array([v for v in loeuf_map.values() if np.isfinite(v)], dtype=float)
            med_loeuf = float(np.median(vals)) if vals.size else 1.0
        else:
            med_loeuf = 1.0

        gene_index = ctx.gene_index

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            # target LOEUF (median-filled), averaged over target genes
            tvals = []
            for t in targets:
                v = loeuf_map.get(t)
                if v is None or not np.isfinite(v):
                    v = med_loeuf
                tvals.append(v)
            target_loeuf = float(np.mean(tvals)) if tvals else med_loeuf

            # complex sharing per gene
            share = np.zeros(n_genes, dtype=float)

            # 1) explicit complex membership overlap
            target_complexes = set()
            for t in targets:
                target_complexes |= gene_to_complexes.get(t, set())
            if target_complexes:
                for g, idx in gene_index.items():
                    gc = gene_to_complexes.get(g)
                    if not gc:
                        continue
                    inter = len(gc & target_complexes)
                    if inter > 0:
                        share[idx] = inter / float(len(gc | target_complexes))

            # 2) PPI fallback for genes not covered by complexes
            uncovered = share == 0.0
            if np.any(uncovered):
                # build target neighbor weights
                tgt_w = {}
                for t in targets:
                    for nb_g, w in ppi_nb.get(t, {}).items():
                        tgt_w[nb_g] = max(tgt_w.get(nb_g, 0.0), w)
                # also direct target membership
                for t in targets:
                    if t in gene_index:
                        tgt_w[t] = max(tgt_w.get(t, 0.0), 1.0)
                if tgt_w:
                    maxw = max(tgt_w.values())
                    if maxw <= 0:
                        maxw = 1.0
                    for g, w in tgt_w.items():
                        idx = gene_index.get(g)
                        if idx is None:
                            continue
                        if uncovered[idx]:
                            share[idx] = w / maxw

            out[i, :, 0] = share * target_loeuf

        # ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
