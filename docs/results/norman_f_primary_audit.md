# Block F primary-result audit

Independent read-only recomputation matched all pooled Holm values, non-null numerical gates, literal Replogle classifications, flags, source hashes and the saved Markdown. No model was changed or refitted in this audit.

Family: 66 status-ok stage-1 annotation rows. Tested: 20. Passing rows: 10. Tier-1-labelled rows: 4.

Every passing raw p is 1/1320; every passing pooled Holm p is exactly 0.05. This is the minimum attainable permutation p and the decision boundary, not a more precise tail estimate. Four other tested rows attain the same raw minimum but fail the M1 effect/SE gate. Five tested rows have p=1; one has p=851/1320. The 46 untested usable rows enter Holm at p=1.

All passing rows meet the fixed M1 effect/SE, majority-win, every-fold-seed, M2 gain and M4 non-worsening gates. Stage-2 non-null reports reproduce stage 1 exactly; all 20 tested plugin copies match their source hashes.

## Tier-1-labelled passing rows

| Source | Feature | OOF delta Pearson | Adjusted SE | Wins / perturbations | Pooled Holm p |
|---|---|---:|---:|---:|---:|
| f_r0 | additive_times_bidirectional_proximity_e541 | 0.001422020 | 0.000456330 | 69/112 | 0.05 |
| f_r0 | additive_times_target_promoter_cpg_e428 | 0.000563135 | 0.000153159 | 69/112 | 0.05 |
| f_r0 | additive_times_target_promoter_cpg_e666 | 0.000563135 | 0.000153159 | 69/112 | 0.05 |
| f_r3 | additive_response_x_target_promoter_cpg_e412 | 0.000563135 | 0.000153159 | 69/112 | 0.05 |

Run directories:
- f_r0: `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ga_ds_addstart_w4_r0`
- f_r2: `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ga_ds_addstart_w4_r2`
- f_r3: `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ga_ds_addstart_w4_r3`

## Interpretation limits

The four tier-1-labelled rows represent two computational families. The target-mean-promoter-CpG times additive formula appears as r0 e428/e666 and r3 e412. Their entire saved reports, including null summaries, are identical. Their missing-value fallbacks differ in source. These are three passing rows, not three distinct mechanisms or independent outcome replications.

The other formula is additive times a numeric TSS-distance score (r0 e541). Despite its bidirectional-proximity name, its code ignores chromosome and strand, includes self-target distance zero, and never reads the bidirectional partner mapping. Keep the fixed passing flag, but do not infer a bidirectional-promoter mechanism.

The whole F arm includes Replogle. Tier-1 classification here follows the predeclared literal-source rule for individual plugins; six other passing rows also read Replogle and remain separately labelled.

These are development candidates under the approved criterion on labels already used during search. They are not a fresh-test, causal, or novel-biological discovery claim. The 28 unusable stage-1 rows remain unassessed as documented in norman_f_stage1_audit.md. No thresholds, k, replicate count, candidate flags, data or model were changed after seeing results.
