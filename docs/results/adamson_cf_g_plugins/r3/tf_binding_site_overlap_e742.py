import numpy as np
from genemila.features.api import Feature, FeatureContext, register

@register
class TFBindingSiteOverlapE742(Feature):
    name = "tf_binding_site_overlap_e742"
    version = 1
    description = "Count of TF binding motifs shared between the target's promoter and gene g's promoter."
    rationale = ("Promoters sharing many TF binding motifs are co-regulated; perturbing a target may "
                 "disrupt common upstream regulators and affect downstream genes sharing those motifs.")
    inputs = ["control_cells", "knowledge"]
    params = {"promoter_window": 1000}
    dim = 1

    def _tf_motif_sets(self, ctx, params):
        # Build a per-gene set of TF motifs using available prior knowledge.
        # We approximate motif membership from gene_sets entries that look like TF-motif/gene sets,
        # the transcription_factors list, and the gene_annotation promoter descriptors.
        cache_key = ("tf_motif_sets", params.get("promoter_window", 1000))
        if cache_key in ctx.cache:
            return ctx.cache[cache_key]

        n = ctx.n_genes
        gene_index = ctx.gene_index
        motif_sets = [set() for _ in range(n)]

        # 1) Use gene_sets: any set whose name mentions TF/motif/transcription factor binding.
        gs = ctx.knowledge("gene_sets")
        if isinstance(gs, dict):
            motif_like_keys = []
            for k in gs.keys():
                kl = k.lower()
                if ("motif" in kl) or ("transcription factor" in kl) or ("tf_" in kl) or kl.startswith("tf:") \
                   or ("tf " in kl) or ("transcription_factor" in kl):
                    motif_like_keys.append(k)
            # If none matched by name, fall back to using all gene_sets as motif proxies
            if not motif_like_keys:
                motif_like_keys = list(gs.keys())
            for k in motif_like_keys:
                members = gs.get(k, [])
                if not isinstance(members, (list, tuple)):
                    continue
                present = [gene_index[m] for m in members if m in gene_index]
                if not present:
                    continue
                motif_id = k
                for gi in present:
                    motif_sets[gi].add(motif_id)

        # 2) Add transcription factor annotations: genes that are TFs get their own symbol as a motif,
        #    and TFs are linked to genes via gene_sets membership already above. Also add a generic
        #    "TF" motif to every gene listed in any gene_set that contains a TF? That would be too broad.
        tfs = ctx.knowledge("transcription_factors")
        if isinstance(tfs, (list, tuple)):
            for tf in tfs:
                gi = gene_index.get(tf)
                if gi is not None:
                    motif_sets[gi].add("TF:" + tf)

        # 3) Use gene_annotation promoter descriptors as coarse motif proxies:
        #    discretise cpg_oe_promoter and gc_promoter into bins and add as pseudo-motifs.
        ga = ctx.knowledge("gene_annotation")
        if isinstance(ga, dict) and "columns" in ga and "genes" in ga:
            cols = ga["columns"]
            genes_ann = ga["genes"]
            try:
                i_cpg = cols.index("cpg_oe_promoter")
                i_gc = cols.index("gc_promoter")
            except ValueError:
                i_cpg = i_gc = None
            for sym, vals in genes_ann.items():
                gi = gene_index.get(sym)
                if gi is None or not isinstance(vals, (list, tuple)):
                    continue
                if i_cpg is not None and i_cpg < len(vals) and vals[i_cpg] is not None:
                    try:
                        v = float(vals[i_cpg])
                        b = int(np.clip(np.floor(v * 5.0), -5, 20))
                        motif_sets[gi].add("CPG_BIN:%d" % b)
                    except (TypeError, ValueError):
                        pass
                if i_gc is not None and i_gc < len(vals) and vals[i_gc] is not None:
                    try:
                        v = float(vals[i_gc])
                        b = int(np.clip(np.floor(v * 20.0), 0, 20))
                        motif_sets[gi].add("GC_BIN:%d" % b)
                    except (TypeError, ValueError):
                        pass

        # 4) Use protein_annotation compartment flags as additional coarse "motif" proxies,
        #    since co-localised proteins often share regulatory programs.
        pa = ctx.knowledge("protein_annotation")
        if isinstance(pa, dict) and "columns" in pa and "genes" in pa:
            cols = pa["columns"]
            flag_cols = ["secreted", "membrane", "endoplasmic_reticulum", "golgi",
                         "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome"]
            idxs = []
            for fc in flag_cols:
                if fc in cols:
                    idxs.append((fc, cols.index(fc)))
            for sym, vals in pa["genes"].items():
                gi = gene_index.get(sym)
                if gi is None or not isinstance(vals, (list, tuple)):
                    continue
                for fc, ci in idxs:
                    if ci < len(vals) and vals[ci] is not None:
                        try:
                            if float(vals[ci]) > 0:
                                motif_sets[gi].add("COMP:" + fc)
                        except (TypeError, ValueError):
                            pass

        ctx.cache[cache_key] = motif_sets
        return motif_sets

    def compute(self, ctx: FeatureContext, perts: list[str], params: dict) -> np.ndarray:
        motif_sets = self._tf_motif_sets(ctx, params)
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Precompute set sizes
        sizes = np.array([len(s) for s in motif_sets], dtype=float)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # Use the first target gene (single-gene targets in this dataset).
            ti = tgt_idx[0]
            tset = motif_sets[ti]
            if not tset:
                continue
            tsize = sizes[ti]
            # For each gene g, count intersection size with target's motif set.
            # Vectorised over genes using a loop over motifs (motifs are few relative to genes).
            inter = np.zeros(n_genes, dtype=float)
            for motif in tset:
                # Find genes containing this motif. We stored as sets; build a small index lazily.
                # To stay fast, we precompute motif->gene list in cache.
                pass
            # Build/update motif->genes map in cache for efficiency.
            map_key = "tf_motif_to_genes"
            if map_key not in ctx.cache:
                m2g = {}
                for gi, s in enumerate(motif_sets):
                    for m in s:
                        m2g.setdefault(m, []).append(gi)
                ctx.cache[map_key] = m2g
            m2g = ctx.cache[map_key]
            for motif in tset:
                gl = m2g.get(motif)
                if gl:
                    inter[gl] += 1.0
            out[i, :, 0] = inter

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
