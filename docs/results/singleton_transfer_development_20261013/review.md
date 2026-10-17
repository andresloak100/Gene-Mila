# Review before fitting

Claim #24 / draft PR #25. Prospective protocol published as `c8c1358` before real outcomes.

Chat 2 independently reviewed the scientific comparison. Accepted requirements:

- Hide the full gene-group `hide` union at each outer and inner level. Regenerate every label-dependent component and training scaler in the restricted view.
- Exclude a training singleton's own response and same-target singleton duplicates before transfer. Pair outcomes never enter singleton transfer while permitted singles exist.
- Include analytic additive, direct signed-external additive and uncalibrated transfer diagnostic controls alongside the matched five-column ridge comparison.
- Use fixed lambda 1; ridge alpha selection is nested. Record the ratio-of-across-seed-means MSE guards and sample SD of paired Pearson gains exactly.
- Three seeds reuse the cohort: report partition sensitivity, not biological replication or statistical significance. Stage B reuses the folds and historically selected B1 recipes: it is development evidence only.
- Refit fixed B1 recipes within each view; never score their full-training stored predictions as held-fold estimates. Preserve member source/parameter/alpha identities and batch behavior.
- Report singleton/pair strata and target/fallback coverage without selecting conditions by outcomes. Top-20 is by absolute true development delta, not cell-derived DE.

The existing `external_loo` helpers were inspected for reusable mathematics, but are not used as nested-validation machinery. Their condition-leave-one-out behavior is not the required full gene-hiding rule. This does not establish historical outer-label leakage; the old outer query was excluded first.

Root preflight loaded the verified frozen package without fitting or scoring: pinned manifest/runtime/file hashes passed; 112 public training conditions, 2,083 genes, no duplicate singleton target groups. The three member identities/alphas/seeds match the fixed plan.

The feature implementation has independent synthetic checks for self/hidden-label invariance, duplicate handling, exact known means, target order, masks/gene alignment, raw signed external behavior, fixed-KRR mathematics and fallbacks. Source review found a malformed-record handling gap before outcomes; it was fixed with a type check and dedicated synthetic cases. Final test counts and runner review belong in the final experiment report.

Final source review found no remaining actionable defects. The runner re-creates views at every level; the B1 ablation shares base matrices and reports both ensemble and matching-member differences. An unequal-baseline synthetic case verifies ratio-of-means gate arithmetic. The parent deadline kills and waits for a stuck child at 7,200 seconds; atomic child checkpoints and preservation of malformed partial checkpoints protect the record. Numeric arrays may be incomplete after hard termination, so no incomplete run can support promotion.

Final focused suite: **62 passed in 2.19 seconds** (49 feature cases, 13 runner/deadline cases). An early full-suite attempt was deliberately stopped to include the last checkpoint-preservation correction; it is not counted as a validation pass. The fresh full suite on final source passed: **529 passed, no skips, 8 dependency deprecation warnings, 653.50 seconds**. Command: `PYTHONHASHSEED=0 nice -n 19 <main .venv>/bin/python -m pytest -q`. No real fitting or new score preceded these checks.

A separate read-only Stage B audit followed the selected plugins and literal `ctx.feature` dependencies in the pinned snapshots (13/23/21 files for the three members). It found no direct full-training data reopen, new/shared FeatureContext, protected training-array access, dynamic feature dispatch or external mutable cache that bypasses restricted views. Training-dependent features use the supplied context; local/context caches are reset per fold. Three implicit composition dependencies were followed despite empty declarations: member 0 `external_direct_replogle2022_k562_e16`, member 1 `pair_target_shared_pathway_count_e126`, member 2 `target_level_e11`. This source check does not establish new model performance.

## Independent review after outcomes

Chat 2 read only the saved config, summary and progress log. It independently recomputed all 90 aggregate/paired mean-and-sample-SD pairs from saved seed metrics (maximum rounding difference 1.11e-16), confirmed the three negative Pearson gains, the 0.002 threshold, both passing error ratios, and the failed continuation gate. All 15 outer/45 inner folds, 112 conditions per seed (71 singles/41 pairs), 480/0 fit counts, exact inner alpha choices/tie rule, coverage arithmetic and monotonic progress events agree. No Stage B folds ran; config hash matches summary. This check did not read response labels or fit anything; root separately verified raw predictions as recorded in verification.json. No discrepancy found.
