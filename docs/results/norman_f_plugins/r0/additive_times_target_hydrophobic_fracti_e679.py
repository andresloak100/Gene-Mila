import numpy as np
from genemila.features.api import Feature, register

# Hydrophobic amino acids (Kyte-Doolittle positive hydropathy) - standard set
_HYDROPHOBIC = ("A", "V", "I", "L", "M", "F", "W", "Y", "P")


@register
class AdditiveTimesTargetHydrophobicFraction(Feature):
    name = "additive_times_target_hydrophobic_fracti_e679"
    version = 1
    description = "Elementwise product of additive_response and target_hydrophobic_fraction."
    rationale = ("Conserved/hydrophobic targets may exert stronger downstream effects due to "
                 "regulatory constraints; combining the additive baseline with a target-level "
                 "biophysical property captures this modulation.")
    inputs = ["control_cells", "train_delta", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n = len(perts)

        # --- additive_response (baseline prediction summed over targets) ---
        # Compute per-perturbation additive response using leave-one-out mean response,
        # matching the additive_response feature definition (sum over targets of the
        # mean training delta of each target gene, excluding p).
        out = np.zeros((n, n_genes, 1), dtype=np.float64)

        # Cache leave-one-out mean response per perturbation
        cache = ctx.cache
        if "hydrophobic_frac_gene" not in cache:
            cache["hydrophobic_frac_gene"] = self._gene_hydrophobic_fraction(ctx)
        gene_hydro = cache["hydrophobic_frac_gene"]  # (n_genes,) float, may be 0

        for i, p in enumerate(perts):
            # additive response row
            _, d = ctx.train_delta(exclude=p)
            if d.shape[0] > 0:
                mean_resp = d.mean(axis=0)
            else:
                mean_resp = np.zeros(n_genes, dtype=np.float64)

            targets = ctx.target_indices(p)
            if len(targets) == 0:
                additive = np.zeros(n_genes, dtype=np.float64)
            else:
                additive = mean_resp[targets].sum()

            # target hydrophobic fraction: mean over targets of gene hydrophobic fraction
            if len(targets) == 0:
                thf = 0.0
            else:
                thf = float(np.mean(gene_hydro[targets]))

            out[i, :, 0] = additive * thf

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out

    def _gene_hydrophobic_fraction(self, ctx):
        """Fraction of hydrophobic residues in each gene's protein product."""
        n_genes = ctx.n_genes
        frac = np.zeros(n_genes, dtype=np.float64)
        ann = ctx.knowledge("gene_annotation")
        if not ann:
            return frac

        genes_data = ann.get("genes", {})
        if not genes_data:
            return frac

        columns = ann.get("columns", [])
        # find indices of aa_* columns
        aa_cols = []
        aa_letters = []
        for j, c in enumerate(columns):
            if isinstance(c, str) and c.startswith("aa_"):
                aa_cols.append(j)
                aa_letters.append(c[3:])

        if not aa_cols:
            return frac

        hydro_set = set(_HYDROPHOBIC)

        for g_idx, gene in enumerate(ctx.genes):
            vals = genes_data.get(gene)
            if vals is None:
                continue
            total = 0.0
            hydro = 0.0
            for j, letter in zip(aa_cols, aa_letters):
                try:
                    v = vals[j]
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
                total += v
                if letter in hydro_set:
                    hydro += v
            if total > 0:
                frac[g_idx] = hydro / total

        return frac
