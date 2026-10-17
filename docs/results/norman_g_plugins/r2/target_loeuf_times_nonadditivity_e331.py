import numpy as np
from genemila.features.api import Feature, register

@register
class TargetLoeufTimesNonadditivity(Feature):
    name = "target_loeuf_times_nonadditivity_e331"
    version = 1
    description = ("Mean target-gene LOEUF multiplied by the mean absolute non-additive "
                   "residual of training perturbations sharing at least one target.")
    rationale = ("Genes under strong LoF constraint may have tighter regulation, so pair "
                 "perturbations involving them may deviate more from additivity; combining "
                 "constraint with observed non-additivity captures this.")
    inputs = ["control_cells", "train_delta"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # --- LOEUF per gene ---
        loeuf = np.full(n_genes, np.nan)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            cols = kc.get("columns", [])
            genes_tab = kc.get("genes", {})
            try:
                lo_idx = cols.index("oe_lof_upper")
            except ValueError:
                lo_idx = None
            if lo_idx is not None:
                for gi, g in enumerate(ctx.genes):
                    vals = genes_tab.get(g)
                    if vals is not None and lo_idx < len(vals):
                        v = vals[lo_idx]
                        if v is not None:
                            try:
                                fv = float(v)
                                if np.isfinite(fv):
                                    loeuf[gi] = fv
                            except (TypeError, ValueError):
                                pass
        # fallback: use median of available LOEUF values
        finite = np.isfinite(loeuf)
        if finite.any():
            fill = float(np.median(loeuf[finite]))
        else:
            fill = 1.0
        loeuf = np.where(finite, loeuf, fill)

        # --- cache: per-perturbation non-additivity and target sets ---
        cache = ctx.cache
        if "e331_nonadd" not in cache:
            train_perts = list(ctx.train_perts)
            nonadd = {}
            tgt_sets = {}
            for tp in train_perts:
                tgs = ctx.target_genes(tp)
                tgt_sets[tp] = set(tgs)
                _, d = ctx.train_delta(exclude=tp)
                if d.shape[0] == 0:
                    nonadd[tp] = 0.0
                    continue
                # additive prediction: mean delta over training perts (leave-one-out)
                # approximate per-target additive via mean of training deltas
                # Use per-perturbation additive: sum over targets of mean single response.
                # Simpler: additive baseline = mean of training deltas (generic response)
                # For non-additivity we need observed minus additive.
                # additive prediction for tp: sum over its targets of that gene's mean
                # delta computed from training perts that target that gene singly.
                # Fall back to generic mean if unavailable.
                mean_delta = d.mean(axis=0)  # (n_genes,)
                # Build single-gene response map from training singles
                obs = None
                # observed delta for tp is not available (we excluded it); use mean_delta as proxy?
                # We need observed delta of tp. We cannot get it without leakage for p itself,
                # but for OTHER training perts tp we can use full train_delta (excluding p).
                # Since we're computing per p, we must exclude p. That's what d is.
                # For tp != p, tp's observed delta is available in d only if tp != p.
                # Find tp in the returned pert ids.
                # train_delta returns (pert_ids, array). We need tp's row.
                # Re-fetch to get ids.
                # To avoid repeated calls, we cache full train deltas per p.
                nonadd[tp] = None  # placeholder
            # We'll compute properly per p below; cache target sets only
            cache["e331_tgt_sets"] = tgt_sets
            cache["e331_loeuf"] = loeuf
        else:
            tgt_sets = cache["e331_tgt_sets"]
            loeuf = cache["e331_loeuf"]

        for i, p in enumerate(perts):
            p_targets = set(ctx.target_genes(p))
            # mean LOEUF of p's targets
            if p_targets:
                idxs = [ctx.gene_index[g] for g in p_targets if g in ctx.gene_index]
                if idxs:
                    mean_loeuf = float(np.mean(loeuf[idxs]))
                else:
                    mean_loeuf = fill
            else:
                mean_loeuf = fill

            # get training deltas excluding p
            ids, d = ctx.train_delta(exclude=p)
            if d.shape[0] == 0:
                out[i, :, 0] = 0.0
                continue
            id_to_row = {pid: r for r, pid in enumerate(ids)}
            # generic mean delta (fallback additive)
            generic_mean = d.mean(axis=0)

            # build single-gene mean response from training singles in d
            single_resp = {}
            for pid in ids:
                tgs = tgt_sets.get(pid, set(ctx.target_genes(pid)))
                if len(tgs) == 1:
                    g = next(iter(tgs))
                    if g not in single_resp:
                        single_resp[g] = []
                    single_resp[g].append(d[id_to_row[pid]])
            single_mean = {}
            for g, rows in single_resp.items():
                single_mean[g] = np.mean(rows, axis=0)

            # compute non-additivity for training perts sharing a target with p
            residuals = []
            for pid in ids:
                tgs = tgt_sets.get(pid, set(ctx.target_genes(pid)))
                if not tgs:
                    continue
                if not (tgs & p_targets):
                    continue
                # additive prediction for pid
                add_pred = np.zeros(n_genes)
                ok = True
                for g in tgs:
                    if g in single_mean:
                        add_pred += single_mean[g]
                    else:
                        # fallback: use generic mean for that gene
                        gi = ctx.gene_index.get(g)
                        if gi is not None:
                            add_pred[gi] += generic_mean[gi]
                        else:
                            ok = False
                            break
                if not ok:
                    continue
                obs = d[id_to_row[pid]]
                resid = obs - add_pred
                residuals.append(float(np.mean(np.abs(resid))))

            if residuals:
                mean_resid = float(np.mean(residuals))
            else:
                mean_resid = 0.0

            out[i, :, 0] = mean_loeuf * mean_resid

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
