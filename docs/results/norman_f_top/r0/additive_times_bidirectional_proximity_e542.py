import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveTimesBidirectionalProximityE542(Feature):
    name = "additive_times_bidirectional_proximity_e542"
    version = 1
    description = ("Elementwise product of additive_response and a score indicating whether "
                   "gene g is bidirectional with any target of p, weighted by inverse TSS distance.")
    rationale = ("CRISPRa at a shared bidirectional promoter can activate both genes; this genomic "
                 "context may modulate the magnitude of additive response for nearby genes.")
    inputs = ["additive_response", "gene_annotation"]
    params = {"max_distance": 1000}
    dim = 1

    def _get_loci(self, ctx):
        cached = ctx.cache.get("_bidir_loci")
        if cached is not None:
            return cached
        ann = ctx.knowledge("gene_annotation")
        loci = {}
        if ann is not None:
            # Try several plausible layouts for annotation JSON.
            raw = None
            if isinstance(ann, dict):
                for key in ("loci", "genes", "annotations", "gene_annotation"):
                    v = ann.get(key)
                    if isinstance(v, dict):
                        raw = v
                        break
                if raw is None:
                    # maybe ann itself maps symbol -> info
                    raw = ann
            if isinstance(raw, dict):
                for sym, val in raw.items():
                    if val is None:
                        continue
                    chrom = tss = strand = None
                    if isinstance(val, dict):
                        chrom = val.get("chrom") or val.get("chr") or val.get("chromosome")
                        tss = val.get("tss") or val.get("start") or val.get("position")
                        strand = val.get("strand")
                    elif isinstance(val, (list, tuple)) and len(val) >= 3:
                        chrom, tss, strand = val[0], val[1], val[2]
                    if chrom is None or tss is None or strand is None:
                        continue
                    try:
                        tss = float(tss)
                    except (TypeError, ValueError):
                        continue
                    loci[sym] = (str(chrom), tss, strand)
        ctx.cache["_bidir_loci"] = loci
        return loci

    def compute(self, ctx, perts, params):
        max_distance = float(params.get("max_distance", 1000))

        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=np.float64)
        if add.ndim == 2:
            add = add[:, :, None]

        loci = self._get_loci(ctx)
        genes = ctx.genes
        n_genes = ctx.n_genes

        gene_locus = [loci.get(g) for g in genes]

        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            tinfo = []
            for t in targets:
                loc = loci.get(t)
                if loc is not None:
                    tinfo.append(loc)
            if not tinfo:
                continue

            score = np.zeros(n_genes, dtype=np.float64)
            for j in range(n_genes):
                gl = gene_locus[j]
                if gl is None:
                    continue
                gchrom, gtss, gstrand = gl
                best = 0.0
                for tchrom, ttss, tstrand in tinfo:
                    if tchrom != gchrom:
                        continue
                    if tstrand == gstrand:
                        continue
                    d = abs(gtss - ttss)
                    if d <= max_distance:
                        val = 1.0 / (1.0 + d)
                        if val > best:
                            best = val
                score[j] = best

            out[i, :, 0] = add[i, :, 0] * score

        # Fallback: if the genomic annotation is unavailable (score all-zero),
        # fall back to additive_response so the feature carries information.
        if not np.any(out):
            out = add.copy()

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
