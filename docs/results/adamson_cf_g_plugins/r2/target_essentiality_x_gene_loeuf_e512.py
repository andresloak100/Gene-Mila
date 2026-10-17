import numpy as np
from genemila.features.api import Feature, register


@register
class TargetEssentialityXGeneLoeufE512(Feature):
    name = "target_essentiality_x_gene_loeuf_e512"
    version = 1
    description = "Product of target gene essentiality proxy (1 - LOEUF) and gene g LOEUF."
    rationale = ("Essential (LoF-intolerant) targets may produce broader downstream changes; "
                 "interacting target essentiality with per-gene constraint (LOEUF) captures this.")
    inputs = ["knowledge:gene_constraint"]
    params = {}
    dim = 1

    def _get_loeuf(self, ctx, symbols):
        """Return LOEUF array aligned to symbols, with median imputation for missing."""
        cache = ctx.cache
        key = "_e512_loeuf"
        if key not in cache:
            kc = ctx.knowledge("gene_constraint") or {}
            genes = kc.get("genes", {}) or {}
            cols = kc.get("columns", []) or []
            try:
                loeuf_idx = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            flags = kc.get("flags", {}) or {}
            vals = {}
            for g, row in genes.items():
                if row is None or loeuf_idx is None:
                    continue
                try:
                    v = row[loeuf_idx]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    continue
                if not np.isfinite(v):
                    continue
                # skip flagged unreliable genes
                fl = flags.get(g, "")
                if fl and ("lof_too_many" in fl or "no_exp_lof" in fl):
                    continue
                vals[g] = v
            cache[key] = vals
        vals = cache[key]

        present = [vals[g] for g in symbols if g in vals]
        if present:
            median = float(np.median(present))
        else:
            median = 1.0

        out = np.full(len(symbols), median, dtype=float)
        for i, g in enumerate(symbols):
            if g in vals:
                out[i] = vals[g]
        return out

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Per-gene LOEUF aligned to ctx.genes
        gene_loeuf = self._get_loeuf(ctx, ctx.genes)
        # Clamp to reasonable range
        gene_loeuf = np.clip(gene_loeuf, 0.0, 5.0)

        # Precompute target essentiality per perturbation
        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if tgenes:
                t_loeuf = self._get_loeuf(ctx, tgenes)
                # essentiality proxy: 1 - LOEUF (low LOEUF -> high essentiality)
                ess = np.clip(1.0 - t_loeuf, 0.0, 1.0)
                ess_val = float(np.mean(ess))
            else:
                ess_val = 0.0
            out[i, :, 0] = ess_val * gene_loeuf

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
