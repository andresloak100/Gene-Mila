# Fixed B1 development diagnosis

The fixed B1 recipes are fragile under these gene-hidden refits: the three-member ensemble trails additive in all three partition seeds. **This is not a re-evaluation of the original frozen B1 coefficients or its historical held-out 0.723.** No held-out labels or scores were queried.

Claim [#26](https://github.com/andresloak100/Gene-Mila/issues/26), draft [PR #27](https://github.com/andresloak100/Gene-Mila/pull/27). [Plan](B1_DIAGNOSTIC_PLAN.md) commits `1fdadb9`/`57d83d2`, reviewed source `07a3baa`, published before fitting. One run:45fixed ridge fits,302.190s,0APIspend. No tuning or retries.

## Fixed comparisons

| Recipe | Pearson delta ↑ | MSE ↓ | Top-20 MSE ↓ | Top-20 direction ↑ |
|---|---:|---:|---:|---:|
| Equal B1 ensemble | 0.476530 ± 0.035865 | 0.012467 ± 0.001711 | 0.199540 ± 0.013521 | 0.753869 ± 0.027543 |
| B1 r1 | 0.586247 ± 0.017491 | 0.008166 ± 0.000509 | 0.197858 ± 0.015830 | 0.808929 ± 0.022968 |
| B1 r2 | 0.584365 ± 0.020631 | 0.012914 ± 0.007600 | 0.188102 ± 0.016593 | 0.820536 ± 0.027063 |
| B1 r3 | 0.309025 ± 0.107512 | 0.041627 ± 0.005324 | 0.296194 ± 0.026369 | 0.667708 ± 0.061423 |
| Analytic additive | 0.561398 ± 0.016064 | 0.008236 ± 0.000350 | 0.193711 ± 0.013308 | 0.794494 ± 0.018042 |

All entries are mean ± sample SD over seeds0/1/2, five gene folds each,112public-training conditions/2083genes. Each recipe uses its original features/parameters/alpha/seed; all gene-sharing response rows are hidden. Equal ensemble minus additive Pearson delta **-0.084868 ± 0.022776**. This SD is same-cohort partition sensitivity, not biological replication or a significance test. Historical recipe selection used this cohort. Top-20 is by absolute development delta, not cell-derived DE or a matched CellForge evaluation.

The third recipe has much higher MSE and more variable Pearson delta than the first two. This is a supported target for a distinct prospective composition test. Removing it has **not** been evaluated on these seeds, and no model is promoted by this diagnostic.

## Error strata

| Group | Counts, seeds0/1/2 | Ensemble − additive Pearson delta | Ensemble − additive MSE | Ensemble − additive top-20 MSE |
|---|---:|---:|---:|---:|
| singleton | 71/71/71 | -0.123392 ± 0.023488 | 0.004260 ± 0.000836 | 0.004511 ± 0.004959 |
| pair | 41/41/41 | -0.018157 ± 0.021708 | 0.004182 ± 0.002953 | 0.008111 ± 0.009974 |
| pair_known_0 | 11/13/3 | 0.018334 ± 0.039415 | 0.000247 ± 0.003664 | -0.022373 ± 0.017229 |
| pair_known_1 | 30/28/38 | -0.026458 ± 0.018869 | 0.004809 ± 0.002759 | 0.016954 ± 0.016335 |
| external_all | 91/91/91 | -0.072507 ± 0.017088 | 0.004293 ± 0.002214 | 0.002402 ± 0.001754 |
| external_partial | 9/9/9 | -0.045851 ± 0.050176 | 0.002426 ± 0.004016 | 0.025775 ± 0.021079 |
| external_none | 12/12/12 | -0.207867 ± 0.082556 | 0.005117 ± 0.002259 | 0.016853 ± 0.006712 |

Groups overlap; known-singleton membership changes with folds. External coverage is raw profile availability, not feature completeness or perturbation exposure. Small pair-known0 groups (as few as3conditions) cannot support a model decision. All10metrics, every member/seed/stratum, sourcepins, fold memberships and coverage are in the [complete summary](results/b1_development_diagnostic_20261013/summary.json). These associations do not establish error causes.

## Source findings

A read-only audit of r3 found a concrete batch-dependent feature: `members/2/plugins/pair_shared_ppi_neighbor_replogle_mean_e492.py:94–96` substitutes the gene-varying control mean when the entire query batch is zero; otherwise line89 broadcasts a scalar neighbor statistic. Other queries can therefore change one condition’s feature. Smaller folds may take a different branch from the original119-condition inference batch. This is a plausible mechanism, not proof that it caused the measured errors.

`best_model_residual_e213_e247.py:29–33` is zero for unseen queries while training rows get a response-derived proxy at47–61. That mismatch can affect fitting/MSE, but its direct evaluation contribution after scaling is constant and cannot alone explain Pearson loss. Its line36 excludes the query response; no cached self-label leak was found in the inspected paths. Response-component SVD sign changes cancel between basis/loadings and are not identified as a defect. Original snapshots are preserved.

## Checks and handoff

Full suite474passed/no skips/8dependencywarnings654.14s; focused7passed1.27s. Independent raw-array arithmetic reproduced **2400metric values**, including all strata (maxabsolute difference7.772e-16). Exact ensemble average, ordering, fullhide/known-single metadata, source/input hashes and45fits pass; see [verification](results/b1_development_diagnostic_20261013/verification.json). Run arrays remain ignored locally; data-free config/summary/progress and source/input pins are archived forClaude.

Run directory: `/Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/gene-mila-b1-diagnosis/runs/b1_development_diagnostic_20261013`. Use the archived parent launcher with the pinned B1package, mainvenv/nice19/PYTHONHASHSEED0/singlethreadBLAS. Deadline7200s; exact command and checksums are recorded with the final evidence.

Next: predeclare one fixed members-r1+r2 equal-average candidate versus the original three-member mean on fold seeds3/4/5, with the same additive comparator, original recipes/alphas/model seeds and all metrics. Do not screen more subsets or score this candidate on the diagnosis seeds. Fresh partitions reuse the cohort and are not independent validation. Keep the delivered B1 package unchanged while testing; preserve negative results too. This fulfills the next targeted step authorized by Andres’s “go”.
