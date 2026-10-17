# Feature comparison: adamson_cf_clean_tables

- data: `adamson_cf_clean_tables`, split `split_450515be1a0d8d2e`, knowledge added after the build: none (public.npz sha256 e8908ef34d85); lab commit `2f2e683`
- parent: `builtin`, 3 features, 3 columns: control_mean, mean_response, is_target
- fold seeds [101, 102, 103], k = 5, groups None; ridge, alpha grid [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0, 30000.0, 100000.0], alpha chosen on one seed's OOF and reported on another
- tiers: oof; deciding tier: oof; labels read: training labels (public.npz)
- null: gene permutation within control-mean bins, 999 replicates (seed 0, 10 bins; p floor 0.001); a candidate proportional to a parent column also gets the perturbation null (per-perturbation scalar of a candidate proportional to a parent column permuted within bins of the targets' mean control expression, parent columns in place) and must pass both; family-wise correction: max-gain step-down permutation (p_fwer) within each source's add-one rows, duplicates by prediction hash collapsed first; Holm on the raw p kept as p_holm; minimum effect 0.002; family sizes after deduplication: LEAD_H8 1
- metrics: M1 pearson_delta, M2 pearson_delta_nontarget, M3 mse, M4 mse_top, M5 r2_top, M6 pearson_delta_top, M7 direction_acc_top, M12 delta scale ratio; gains are candidate minus parent (M4: parent minus candidate), ± the overlap-adjusted paired SE

**Caveat:** OOF only: every system has selected on these labels; not held out.
**Caveat:** M4-M7 use each perturbation's top 20 genes by |true delta| (genemila.benchmark.evaluator), not CellForge's Wilcoxon DE top 20.
**Caveat:** ridge on the tool's alpha grid with an honest OOF alpha; a parent run's own model type and alpha are not reused.
**Caveat:** the literal caps make pasting labels into a file expensive, not impossible.

## Table 1. Systems: feature set + linear model

| row | tier | n features | n columns | M1 | M2 | M3 | M4 | M5 | M6 | M7 | M12 | ΔM1 ± SE_adj | wins/n | null p (FWER) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| parent | oof | 3 | 3 | 0.4842 | 0.4812 | 0.0067 | 0.1353 | 0.7698 | 0.6305 | 0.8503 | 0.6208 |  |  |  |  |
| LEAD_H8 (set) | oof | 4 | 4 | 0.4829 | 0.4811 | 0.0068 | 0.1368 | 0.7687 | 0.6300 | 0.8503 | 0.6197 | -0.0013 ± 0.0011 | 25/50 | 1.000 | not: M1 gain not above 2 SE_adj with wins > n/2; M1 gain not above the minimum effect 0.002; an OOF report does not gain; null p (FWER) > 0.05; no M2 gain |

## Table 2. Single features added to the parent

| source | feature | tier | status | ΔM1 ± SE_adj | wins/n | ΔM2 | ΔM4 | ΔM5 | ΔM7 | null p raw / Holm / FWER | excess | pert null p raw / FWER (parent column) | coef sign | max abs r | label-dependent | literal (numbers, string bytes, names) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LEAD_H8 | h8_constraint_residual | oof | ok | -0.0013 ± 0.0011 | 25/50 | -0.0001 | -0.0015 | -0.0011 | 0.0000 | 1.000 / 1.000 / 1.000 | -0.0009 | 0.769 / 0.769 (mean_response) | + (6/6 reports) | 0.270 | yes | 5, 2026, 0 | not: M1 gain not above 2 SE_adj with wins > n/2; M1 gain not above the minimum effect 0.002; an OOF report does not gain; null p (FWER) > 0.05; perturbation null p (FWER) > 0.05; no M2 gain |
