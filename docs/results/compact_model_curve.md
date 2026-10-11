# How few features does the model need? (Adamson, best Opus run)

Free, offline, training perturbations only: written and run on the Mac on 2026-10-11 by
`tools/compact_model_curve.py` on `runs/newcode_opus_w4_r0`. The output is
`docs/results/compact_model_curve_newcode_opus_w4_r0.json` (md5 37d593a18d71c81faef99f3d2d03c015, rebuilt byte for byte
from the Mac's paste). Scores are out-of-fold pearson_delta over the 50 training perturbations with the lab's 5 folds
(label-dependent features recomputed without each fold). The feature pool is the run's 12-feature best model, every
other feature that improved on its parent, and the three built-ins: 16 features, 25 columns.

## Forward selection (add the feature that raises the score most)

| features | columns | feature added | out-of-fold pearson_delta |
|---|---|---|---|
| 1 | 1 | knn_response_reconstruction_weights_e162 | 0.5409 |
| 2 | 3 | knn_response_symbol_family_e58 | 0.5614 |
| 3 | 4 | is_target_x_control_mean_e35 | 0.5768 |
| 4 | 7 | knn_response_geneset_e12 | 0.5791 |
| 6 | 10 | (is_target, shared_geneset_score_e15) | 0.5799 |
| 12 | 19 | | 0.5810 |
| 13 | 20 | (best point on the path) | 0.5812 |
| 16 | 25 | everything | 0.5773 |
| the run's own 12-feature best model | 17 | | 0.5832 |

Three features reach 0.577; after the third the curve is flat within about 0.004, and the whole pool scores lower than
its best subsets.

## Redundancy among the 25 columns

- Matrix rank 22 of 25. knn_response_geneset_e11 is an exact copy of knn_response_geneset_e12 (all three columns,
  |r| = 1.0); the two columns of normalized_mean_response_e56 correlate 0.9998.
- 10 column pairs correlate above 0.9 and 34 above 0.7. The kNN-transfer features correlate 0.91 to 0.92 with each
  other: they are versions of one idea, predicting a knockdown from the responses of related knockdowns.
- A Lasso on the whole pool keeps 22 columns at lambda 0.0001, 19 at 0.0003, 11 at 0.001, 9 at 0.003 and 4 at 0.01;
  the last four are kNN-transfer columns.

## Reading

The model is saturated by near-duplicates: agents re-implement the same transfer feature with another similarity
measure, each version scores a hair higher on the visible folds by chance, and it is kept. A compact model of three
features keeps the accuracy of the twelve-feature model within the fold noise; pruning does not raise accuracy, because
it adds no information. Astra's 176-column continuation reached 0.606 on its own folds and 0.602 against 0.599 on the
held-out set.

## Limits (for the full audit in tools/feature_audit.py)

- The penalty is chosen on the same folds that score each subset, so every number is slightly optimistic, more so for
  larger subsets.
- The Lasso path is fitted on one fold's training rows: it shows which columns survive, not a stability estimate.
- Forward selection is greedy and by whole feature; merging duplicates is not tried.
- One fold seed. The same model scored 0.602 and 0.582 under two fold seeds in Astra's check, so differences below about
  0.02 here are not established.
