# Block D readings: the first discovery-mode runs on Adamson (18 October 2026)

The readings fixed in [`docs/PLAN_D_DISCOVERY_ADAMSON.md`](../PLAN_D_DISCOVERY_ADAMSON.md) (PR #75), made after the chain
ended, free, `nice -n 19`, credentials unset, by the lab-code owner's Mac arm (claim
[#68](https://github.com/andresloak100/Gene-Mila/issues/68)) from the clone `gene-mila-d-readings` at `23b3b12` (PR #71's
head, `D_COMMIT`; it contains block G's tool commit `2f2e683`). Each output has its `.command.txt` (the exact command),
`.log` and `.exit` beside it. The runs' own records (cap line, chain log, check files, `config.json`, `summary.json`)
are in [`docs/mac/block_d_records/`](../mac/block_d_records/README.md).


Completed by Astra on Andres's direct instruction: [final review](adamson_cf_d_completion.md) / [JSON](adamson_cf_d_completion.json). The primary development fair test has two response-transfer passes; the unread-input secondary subset has none. No new biological discovery is claimed. All remaining calls exited0 and the ledger is unchanged. The original narrative below records the18October preparation; the completion review supersedes its running status.

## The block

Three runs `gene-mila/runs/adamson_cf_d1_ds_w4_r{0,2,3}_discovery`, block G's g1 settings on
`data/adamson_cf_clean_tables` (split `split_450515be1a0d8d2e`) plus `schedule.discovery=true`, code `23b3b12`. Started by
Andres from his Terminal at 17:53 UTC, ended 18:57:45 UTC, all three passed every check of `block_d_run.sh`. Ledger
$60.232225 → $61.240534: **$1.008309** of the $10 cap (r0 $0.546548, r2 $0.137546, r3 $0.324215). Its own arm: never
pooled with G1 (different code and planner view).

## Status (completed 28 October 2026)

| Reading | What | Status | Files |
|---|---|---|---|
| 1 | the discovery record per run (descriptive) | **done** | [`adamson_cf_d1_discovery_record.md`](adamson_cf_d1_discovery_record.md) / `.json` |
| 2 | the fair test (A.1) over every plugin of the three runs | **done**: all234 tested,211unique,2pooled passes; see completion review | `adamson_cf_d_plugins/` (+ `.sha256`, posted on #41 before the tool ran), `adamson_cf_d_stage1/`, `adamson_cf_d_top/`, `adamson_cf_d_stage2/`, `adamson_cf_d_pooled_holm/` |
| 3 | arm against arm, development tier (descriptive) | **done**, nine sets ok | `adamson_cf_d1_vs_g/` |
| 5 | experiments, planner state, cost, the dry rule (descriptive) | **done** | `adamson_cf_d1_descriptive.md` |
| 4 | per run, sealed, last (worn, indicative only) | **done last**, three separate calls | `adamson_cf_d1_r{0,2,3}_sealed_reading.md` |

## Reading 1 (descriptive; no test)

| | r0 | r2 | r3 | mean ± sd |
|---|---:|---:|---:|---:|
| planner rounds (counted) | 25 (24) | 6 (6) | 14 (14) | 15 ± 9.5 |
| went dry at round | 25 | 6 | 14 | |
| hypotheses | 192 | 48 | 113 | 117.7 ± 72.1 |
| hypotheses naming an unread input | 54 | 10 | 37 | 33.7 ± 22.2 |
| features scored for derivability | 141 | 40 | 89 | 90.0 ± 50.5 |
| below the 0.8 derived threshold (the summary's `new_input_features`) | 135 | 39 | 85 | 86.3 ± 48.0 |
| of those, naming an unread input | 48 | 9 | 33 | 30.0 ± 19.7 |
| derived (derived_r2 ≥ 0.8) | 6 | 1 | 4 | 3.7 ± 2.5 |
| selected model (visible, not a held-out score) | ridge, 23 features, 0.5524 | ridge, 9, 0.5056 | ridge, 11, 0.5507 | |

## Reading 2: original preparation (completed result in final review)

Family: **every plugin of the three runs**, 270 files (r0 141, r2 40, r3 89), copied unchanged; their sha256
([`adamson_cf_d_plugins.sha256`](adamson_cf_d_plugins.sha256)) were posted on
[#41](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6253847779) before the tool ran. Stage 1
(`--null-reps 0`, exit 0, 314 rows): add-one rows f_r0 123 ok / 18 duplicate, f_r2 34 ok / 6 duplicate, f_r3 77 ok / 11
duplicate / 1 literal. Select: **m_total 234**, all 234 status-ok rows into stage 2 at 999 replicates (`selection.json`
sha256 `a13a33b1c6ae37644efbd781d15e839aa7e67d0b42442292b391a64b0cbf713d`). Stage 2 started 2026-10-18T19:04:53Z.
