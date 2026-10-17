# The lead's hypothesis: residualised constraint (family 8)

One feature plugin written by the lead, `h8_constraint_residual.py` (feature `h8_constraint_residual`). It is the
hand-written hypothesis test of [`docs/ROADMAP.md`](../../ROADMAP.md) D4, pre-registered as family 8 of
[`docs/PREREG_G_KNOWN_BIOLOGY.md`](../../PREREG_G_KNOWN_BIOLOGY.md): constraint residualised on control expression
and tier-1 essentiality proxies. **It is a human hypothesis.** `tools/feature_compare.py` scores it like any other
`--source`, and whoever reports it says "the lead's hypothesis", never GOAL_CRITERIA A.1: no agent found it, and the
agents of block G never see this file (their checkout is pinned at `baa7dfd`, which predates it). Fixed now, before
any block G score exists. **Nothing here has run on real data.**

## The pre-registration (family 8)

- Sign: Adamson CRISPRi **positive** (residual constraint scales the response up beyond basal expression and
  essentiality). Norman CRISPRa: not predicted.
- Verdict before reading: **OPEN** (the one open family with power, ROADMAP D3).
- Null: **both** (the gene null and the perturbation null), because the candidate is a parent column times a
  per-perturbation scalar.
- Minimum effect of practical interest: mean out-of-fold M1 gain above `max(2 SE_adj, 0.002)`.
- A family of one: the step-down correction has one member, so `p_fwer` equals the raw null p.

## The feature, exactly

Per output gene j of the bundle: constraint `s_j = -oe_lof_upper_j` (minus LOEUF, so larger means more constrained),
taken from `ctx.knowledge("gene_constraint")` (`tools/build_gene_constraint.py`: `genes[symbol]` is one value per
entry of `columns`, `null` where gnomAD has none). Genes without a value are left out of the fit and get `c = 0`
below.

Confounds, per gene: `x1_j = log1p(ctx.control_mean[j])` (basal expression); `e_j = 1` if gene j belongs to any
CORUM complex set in `ctx.knowledge("gene_sets")` (the clean bundle names them `CORUM:<complex>`,
`genemila/data/knowledge_clean.py`), else 0; `r_j = 1` if it belongs to any Reactome set (`REACTOME:<pathway>`)
whose name contains `ribosom`, `proteasom` or `spliceosom` (case-insensitive), else 0. If the bundle has no
`gene_sets`, or none of those sets, the indicators are all zero and the residual then removes basal expression only.

Fit, once per context (cached on `ctx.cache`), ordinary least squares over the genes that have a constraint value:
`s_j ~ 1 + x1_j + e_j + r_j`; residual `rho_j = s_j - fitted_j`; genes without a value get `rho_j = 0`.

Per perturbation p: `c_p` = mean of `rho` over p's target genes that have a constraint value (`ctx.target_genes(p)`;
targets outside the bundle or without a value skipped; no such target gives `c_p = 0`).

Output `(len(perts), n_genes, 1)`: `additive_response[i, :] * c_p`, with `additive_response` from
`ctx.feature("additive_response", perts)` (`dependencies = ["additive_response"]`). The candidate is therefore
proportional to a parent column, and `tools/feature_compare.py` applies both nulls to it, as the pre-registration
requires. The file is deterministic (no `hash()` or `id()`, sets iterated in sorted order), reads training labels only
through `additive_response`, passes `genemila.guard.check_plugin_source` and the literal caps of
`tools/task_package/literal.py`, and passes `python -m genemila.pipeline smoke`.

## Why each confound is removed

Family 6 of the pre-registration (raw constraint) is KNOWN: constraint is a proxy for essentiality and basal
expression, and essential, highly expressed genes already produce the largest transcriptional responses, so a raw
constraint feature restates that known dependence through its confounds. Family 8 removes both: `log1p` control mean
takes out basal expression, and the CORUM and Reactome ribosome, proteasome and spliceosome indicators are the tier-1
essentiality proxies (DepMap is tier 3 and excluded, `docs/NOVEL_FEATURE_NEEDS.md` section 7). What is left, if it
predicts the response, is the new rule the hypothesis claims.

## Scoring (Astra, on the Mac, after block G; free)

Never beside a paid run, at `nice -n 19`, with `<MAIN>` the main checkout and `<ds>` each of `adamson_cf` and
`norman`:

```
nice -n 19 python tools/feature_compare.py --data <MAIN>/data/<ds>_clean_tables --out docs/results/<ds>_lead_h8 \
  --source LEAD_H8=docs/comparison/lead_h8_constraint --null-reps 999
```

The report is `feature_compare.md` and `feature_compare.json` in `--out`; cite them with the directory, as every
number in this repository is. Fewer than 999 replicates reads "null too coarse" and decides nothing.

## How to read the result

In the row `h8_constraint_residual` of each report (a family of one):

1. `proportional` is `true` and `parent_column` is `additive_response`; otherwise the file did not run as written.
2. Both nulls pass: `null.p_fwer` and `null_pert.p_fwer` are each at most 0.05.
3. The gain is above the minimum effect: the mean out-of-fold M1 gain exceeds `max(2 SE_adj, 0.002)`.
4. The sign: `coef_candidate_std` is positive in every fold seed on Adamson (the prediction); on Norman the sign is
   recorded, not predicted. A sign that flips in any fold seed on Adamson drops the mechanism claim and the feature
   is reported as predictive but unexplained.

A pass on 1 to 4 is reported as "the lead's pre-registered hypothesis, OPEN, supported on Adamson", provisional until
the citation pass of `docs/CANDIDATE_LITERATURE_CHECK.md` confirms its keys; a failure is reported as such. Neither
is A.1. **Nothing has run.**

## Tests

`python -m pytest -q tests/test_lead_h8_constraint.py`: the guard and the literal caps; on a pair bundle with a
synthetic `gene_constraint` table and `CORUM:` and `REACTOME:` sets, the shape, a zero row for a perturbation whose
targets have no value, and equality with `additive_response` times the hand-computed residual mean; the pipeline
smoke; and `tools/feature_compare.py` reporting the row as proportional to `additive_response` with a `null_pert`.
