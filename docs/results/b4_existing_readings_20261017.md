# B4: existing one-worker readings, 17 October 2026

Reading-only receipt for ROADMAP section 6 step 4. The planned three-repeat B4 arm is incomplete: r3 lost its planner and is a separate arm. No new scoring, fit, oracle query, paid call, or change to the original runs was made.

All paths in this table are under `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/`. Each full path is repeated below. The selected experiment comes from `summary.json["best"]`, chosen on visible score.

| Run directory | Selected experiment | Stored sealed Pearson delta | Stored sealed additive | Point difference | Ledger USD | Status |
|---|---|---:|---:|---:|---:|---|
| `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w1_r0` | EXP_0189 | 0.722960087 | 0.712592076 | +0.010368011 | 0.389612324 | clean DeepSeek planner + one worker |
| `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w1_r2` | EXP_0182 | 0.719890613 | 0.712592076 | +0.007298537 | 0.451021668 | clean DeepSeek planner + one worker |
| `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w1_r3` | EXP_0013 | 0.716123956 | 0.712592076 | +0.003531880 | 0.000000000 | DeepSeek planner unusable/lost; separate arm |

Clean r0/r2 only: selected sealed Pearson delta **0.721425350 ± 0.002170446**, sample SD across these two independent search runs. This is an incomplete arm, not the planned three-repeat estimate. r3 is reported separately, not pooled. All scores use `split_a391fa9e7b4eccb7` and code `ce1b53043125cad78d060d1155e5ffe6efab5c0a` on the already inspected Norman cohort.

## Other stored sealed metrics

These names come from the runs' own metric implementation and do not establish comparability with CellForge's published table. `cellforge_mse` uses all genes; `_de` metrics use that implementation's DE genes. The JSON preserves every stored comparable metric and separately named cell-eval results.

| Run directory | MSE all | PCC expression all | R² expression all | MSE DE |
|---|---:|---:|---:|---:|
| `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w1_r0` | 0.005131116 | 0.989132730 | 0.975721266 | 0.105059377 |
| `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w1_r2` | 0.005410361 | 0.988674608 | 0.974448618 | 0.106995614 |
| `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w1_r3` | 0.005418020 | 0.988537306 | 0.974407254 | 0.109074351 |

## Usage and integrity

| Run directory | Worker calls | Planner calls | Failed calls | Worker USD | Planner USD | Reported research duration s |
|---|---:|---:|---:|---:|---:|---:|
| `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w1_r0` | 133 | 22 | 0 | 0.142875372 | 0.246736952 | 1200.7 |
| `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w1_r2` | 163 | 24 | 0 | 0.185338404 | 0.265683264 | 1238.8 |
| `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w1_r3` | 0 | 2 | 2 | 0.000000000 | 0.000000000 | 28.3 |

Total recorded cost across these directories: **0.840633992 ledger USD**. Ledger per-run sums, summary usage and read-only run-database call sums agree within 1e-12. r3 has no spend rows and records two failed planner calls at zero cost. Its planner fields are `mixed=true`, `used=[]`, `exhausted_at_min=0.2`; zero worker calls and only 10 completed experiments. The two clean runs have `mixed=false`, no switches/exhaustion and the configured DeepSeek planner.

## Planned arm reading: unavailable

The B4 plan specifies a paired comparison of the average of the three B4 selected models against the average of B2 r0/r2/r3, then per-run/secondary arm readings. No saved B4 `sealed_reading` or `arm_reading` result was found in project clones/results, the main/pinned result-file inventory, or log-directory JSON/Markdown. All three summaries have `ensemble=null`. The summaries contain point scores; they do not contain the paired perturbation differences, paired SE, wins, or cross-run averaged-prediction score required for the rule. A point-score difference is not a verdict.

The primary arm verdict is therefore **not available**, and B4 also lacks three clean planned repeats. No missing reading is silently reconstructed, no two-run replacement arm is proposed, and r3 is not combined with the clean runs. No additional score or retry is authorized by this reading-only step.

## Provenance

The JSON twin records full run paths, summary SHA256 values, selected experiment IDs, source commit, exact ledger rows grouped by role/model, read-only call aggregates, planner state, stored point metrics and the artifact-search scope. It uses the existing `tools/feature_audit.open_db_readonly` helper for run metadata and an immutable/read-only ledger connection (temporary DB/WAL copy if needed). It constructs no lab, query oracle, run database writer or spend-ledger object. It reads no private bundle or split file, `summary.md`, or original run-log end.

The sealed set has already been used repeatedly. These are descriptive existing outcomes, with no fresh-test, CellForge-win, multi-agent superiority or model-promotion claim.
