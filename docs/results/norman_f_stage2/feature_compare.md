# Feature comparison: norman_ga

- data: `norman_ga`, split `split_a391fa9e7b4eccb7`, knowledge added after the build: gene_annotation, replogle2022_k562 (public.npz sha256 b2c7eb3d3480); lab commit `b6638c3`
- parent: `builtin`, 4 features, 4 columns: control_mean, mean_response, is_target, additive_response
- fold seeds [101, 102, 103], k = 5, groups gene; ridge, alpha grid [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0, 30000.0, 100000.0], alpha chosen on one seed's OOF and reported on another
- tiers: oof; deciding tier: oof; labels read: training labels (public.npz)
- null: gene permutation within control-mean bins, 1319 replicates (seed 0, 10 bins); Holm within each source's add-one rows, family sizes: f_r0 10, f_r3 10
- metrics: M1 pearson_delta, M2 pearson_delta_nontarget, M3 mse, M4 mse_top, M5 r2_top, M6 pearson_delta_top, M7 direction_acc_top, M12 delta scale ratio; gains are candidate minus parent (M4: parent minus candidate), ± the overlap-adjusted paired SE

**Caveat:** OOF only: every system has selected on these labels; not held out.
**Caveat:** M4-M7 use each perturbation's top 20 genes by |true delta| (genemila.benchmark.evaluator), not CellForge's Wilcoxon DE top 20.
**Caveat:** ridge on the tool's alpha grid with an honest OOF alpha; a parent run's own model type and alpha are not reused.
**Caveat:** the literal caps make pasting labels into a file expensive, not impossible.

## Table 1. Systems: feature set + linear model

| row | tier | n features | n columns | M1 | M2 | M3 | M4 | M5 | M6 | M7 | M12 | ΔM1 ± SE_adj | wins/n | null p (Holm) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| parent | oof | 4 | 4 | 0.5682 | 0.5604 | 0.0083 | 0.1921 | 0.7015 | 0.6174 | 0.8074 | 0.7311 |  |  |  |  |
| f_r0 (set) | oof | 14 | 14 | 0.5746 | 0.5645 | 0.0083 | 0.1887 | 0.7053 | 0.6343 | 0.8122 | 0.7489 | +0.0064 ± 0.0020 | 73/112 | 0.001 | meaningful (development, OOF only, not held out) |
| f_r3 (set) | oof | 14 | 23 | 0.5759 | 0.5674 | 0.0083 | 0.1874 | 0.7065 | 0.6344 | 0.8172 | 0.7400 | +0.0077 ± 0.0025 | 66/112 | 0.001 | meaningful (development, OOF only, not held out) |

## Table 2. Single features added to the parent

| source | feature | tier | status | ΔM1 ± SE_adj | wins/n | ΔM2 | ΔM4 | ΔM5 | ΔM7 | null p raw / Holm | excess | max abs r | label-dependent | literal (numbers, string bytes, names) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| f_r0 | additive_times_bidirectional_count_e485 | oof | ok | +0.0000 ± 0.0000 | 71/112 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.645 / 1.000 | -0.0000 | 1.000 | yes | 15, 583, 0 | not: null p (Holm) > 0.05 |
| f_r0 | additive_times_bidirectional_proximity_e541 | oof | ok | +0.0014 ± 0.0005 | 69/112 | 0.0001 | 0.0018 | 0.0029 | 0.0000 | 0.001 / 0.008 | 0.0014 | 0.586 | yes | 14, 415, 0 | meaningful (development, OOF only, not held out) |
| f_r0 | additive_times_bidirectional_proximity_e542 | oof | ok | +0.0001 ± 0.0001 | 73/112 | 0.0001 | 0.0002 | 0.0005 | 0.0000 | 0.001 / 0.008 | 0.0005 | 0.003 | yes | 18, 533, 0 | not: M1 gain not above 2 SE_adj with wins > n/2 |
| f_r0 | additive_times_target_exon_count_e548 | oof | ok | +0.0002 ± 0.0002 | 55/112 | 0.0002 | -0.0002 | -0.0005 | -0.0001 | 0.001 / 0.008 | 0.0003 | 0.731 | yes | 7, 336, 0 | not: M1 gain not above 2 SE_adj with wins > n/2 |
| f_r0 | additive_times_target_hydrophobic_fracti_e679 | oof | ok | +0.0001 ± 0.0000 | 68/112 | 0.0001 | 0.0001 | -0.0001 | 0.0007 | 1.000 / 1.000 | 0.0000 | 0.090 | yes | 17, 520, 0 | not: null p (Holm) > 0.05 |
| f_r0 | additive_times_target_promoter_cpg_e428 | oof | ok | +0.0006 ± 0.0002 | 69/112 | 0.0005 | 0.0003 | -0.0001 | -0.0001 | 0.001 / 0.008 | 0.0006 | 0.937 | yes | 7, 380, 0 | meaningful (development, OOF only, not held out) |
| f_r0 | additive_times_target_promoter_cpg_e666 | oof | ok | +0.0006 ± 0.0002 | 69/112 | 0.0005 | 0.0003 | -0.0001 | -0.0001 | 0.001 / 0.008 | 0.0006 | 0.937 | yes | 8, 409, 0 | meaningful (development, OOF only, not held out) |
| f_r0 | screen_delta_over_transcript_length_e546 | oof | ok | +0.0000 ± 0.0000 | 59/112 | 0.0000 | 0.0001 | 0.0002 | 0.0010 | 1.000 / 1.000 | -0.0000 | 0.010 | no | 9, 360, 0 | not: M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; null p (Holm) > 0.05 |
| f_r0 | screen_delta_over_transcript_length_e547 | oof | ok | +0.0037 ± 0.0017 | 64/112 | 0.0031 | 0.0023 | 0.0026 | 0.0060 | 0.001 / 0.008 | 0.0038 | 0.055 | no | 10, 355, 0 | meaningful (development, OOF only, not held out) |
| f_r0 | target_promoter_cpg_e406 | oof | ok | +0.0000 ± 0.0000 | 66/112 | 0.0000 | -0.0000 | -0.0000 | -0.0009 | 1.000 / 1.000 | 0.0000 | 0.034 | no | 4, 269, 0 | not: M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; null p (Holm) > 0.05 |
| f_r3 | additive_response_x_target_promoter_cpg_e412 | oof | ok | +0.0006 ± 0.0002 | 69/112 | 0.0005 | 0.0003 | -0.0001 | -0.0001 | 0.001 / 0.008 | 0.0006 | 0.937 | yes | 14, 495, 0 | meaningful (development, OOF only, not held out) |
| f_r3 | bidirectional_partner_coexpression_with__e531 | oof | ok | +0.0007 ± 0.0005 | 51/112 | 0.0004 | 0.0005 | 0.0007 | 0.0024 | 0.001 / 0.008 | 0.0008 | 0.501 | no | 13, 385, 0 | not: M1 gain not above 2 SE_adj with wins > n/2 |
| f_r3 | gene_annotation_random_projection_e567 | oof | ok | +0.0001 ± 0.0001 | 63/112 | 0.0001 | 0.0001 | 0.0001 | 0.0009 | 0.001 / 0.008 | 0.0001 | 0.193 | no | 24, 437, 0 | not: M1 gain not above 2 SE_adj with wins > n/2 |
| f_r3 | replogle_additive_x_promoter_cpg_oe_e441 | oof | ok | +0.0026 ± 0.0010 | 63/112 | 0.0022 | 0.0011 | 0.0015 | 0.0039 | 0.001 / 0.008 | 0.0026 | 0.068 | no | 9, 376, 0 | meaningful (development, OOF only, not held out) |
| f_r3 | replogle_additive_x_target_promoter_cpg__e558 | oof | ok | +0.0029 ± 0.0014 | 62/112 | 0.0025 | 0.0017 | 0.0022 | 0.0045 | 0.001 / 0.008 | 0.0029 | 0.071 | no | 11, 447, 0 | meaningful (development, OOF only, not held out) |
| f_r3 | replogle_additive_x_target_promoter_cpg__e590 | oof | ok | +0.0032 ± 0.0014 | 62/112 | 0.0028 | 0.0018 | 0.0024 | 0.0048 | 0.001 / 0.008 | 0.0032 | 0.071 | no | 13, 376, 0 | meaningful (development, OOF only, not held out) |
| f_r3 | replogle_additive_x_target_promoter_cpg_e460 | oof | ok | +0.0029 ± 0.0014 | 60/112 | 0.0025 | 0.0016 | 0.0022 | 0.0040 | 0.001 / 0.008 | 0.0029 | 0.065 | no | 10, 571, 0 | meaningful (development, OOF only, not held out) |
| f_r3 | replogle_additive_x_target_promoter_gc_e328 | oof | ok | +0.0047 ± 0.0017 | 62/112 | 0.0042 | 0.0026 | 0.0034 | 0.0068 | 0.001 / 0.008 | 0.0047 | 0.072 | no | 13, 314, 0 | meaningful (development, OOF only, not held out) |
| f_r3 | target_mean_cpg_oe_promoter_e402_e350 | oof | ok | +0.0000 ± 0.0000 | 66/112 | 0.0000 | -0.0000 | -0.0000 | -0.0009 | 1.000 / 1.000 | 0.0000 | 0.034 | no | 4, 278, 0 | not: M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; null p (Holm) > 0.05 |
| f_r3 | target_promoter_cpg_mean_e521 | oof | ok | +0.0000 ± 0.0000 | 66/112 | 0.0000 | -0.0000 | -0.0000 | -0.0009 | 1.000 / 1.000 | 0.0000 | 0.034 | no | 8, 277, 0 | not: M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; null p (Holm) > 0.05 |
