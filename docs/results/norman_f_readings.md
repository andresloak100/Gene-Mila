# Block F readings: candidate features, no established arm gain

The approved two-stage feature test produced 10 passing rows, including four tier-1-labelled rows from two computational families. The complete F model sets do not establish an improvement over B2 on the prescribed development comparison. No model is promoted.

OOF Pearson delta over three search runs: **F 0.580526 ± 0.002321; B2 0.582457 ± 0.008062**. The F-minus-B2 mean difference is -0.001931, within both arms’ run-to-run spread. This is descriptive: no between-arm significance test is made.

## Provenance and rule

Paid-run code ce1b530; evaluation tools b6638c3 (PR #44). Andres directly approved the two-stage reading before evaluation; the decision is recorded on issue #41, comment 6223988752. The amendment headed 04:20 UTC was committed at 19:45:48 UTC, after paid search began and before the primary/sealed readings. The exact stage-1, select, stage-2 and pool sequence was used; the original single-stage test was not run.

The bundle is norman_ga: the existing Norman copy plus gene_annotation, retaining Replogle. This is a Replogle-plus-annotation arm. Parent: the tool’s built-in additive start; gene-grouped five-fold partitions, fold seeds 101/102/103, OOF-only comparison, honest alpha selection on the tool’s ridge grid. No --with-val1. These labels were already used during system search; they are not fresh held-out labels.

### Source run directories

- f_r0: `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ga_ds_addstart_w4_r0` (selected EXP_0715).
- f_r2: `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ga_ds_addstart_w4_r2` (selected EXP_0260).
- f_r3: `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ga_ds_addstart_w4_r3` (selected EXP_0603).
- b2_r0: `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w4_r0` (selected EXP_0724).
- b2_r2: `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w4_r2` (selected EXP_0715).
- b2_r3: `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/runs/norman_ds_addstart_w4_r3` (selected EXP_0625).

## Primary feature reading

94 plugins were copied unchanged: F r0=60, r2=1, r3=33. Stage 1 produced 66 status-ok add-one rows; the helper selected the top 20 by the fixed gain/SE rule, ten from r0 and ten from r3. Stage 2 used 1,319 null replicates per tested feature at nice19. It exited0 at 21:05:40 UTC, about38 minutes after log creation. All 66 rows enter pooled Holm; the 46 usable untested rows enter at p=1.

All ten passing rows have raw p=1/1320 and pooled Holm p=0.05 exactly, at the available permutation-resolution boundary, and pass the other fixed gates. Fourteen tested rows reach that minimum raw p; four of them fail the M1 effect/SE gate. A source/arithmetic audit reproduced every pooled flag.

| Computational family | Passing tier-1-labelled rows | OOF delta M1 ± adjusted SE | Wins / n | Pooled p |
|---|---|---:|---:|---:|
| Target-mean-promoter-CpG × additive | f_r0 e428/e666; f_r3 e412 | 0.000563135 ± 0.000153159 | 69/112 | 0.05 |
| Numeric TSS-distance score × additive | f_r0 e541 | 0.001422020 ± 0.000456330 | 69/112 | 0.05 |

The three CpG rows have identical complete saved reports, including null summaries; their missing-value fallbacks differ. They are repeated formula variants, not three independent mechanisms or independent outcome replications. The TSS feature ignores chromosome and strand, includes self-target distance0 and never reads the bidirectional partner mapping: its name does not establish a bidirectional-promoter mechanism. The other six passing rows also read Replogle and are separately labelled in the complete pooled table.

28 copied plugins were unassessable in this prescribed add-one setup: 25 missing-key errors and three constant-feature smoke failures. They were not repaired or substituted. A negative result for the assessed family would not prove that these excluded features add nothing. See [stage-1 audit](norman_f_stage1_audit.md), [primary audit](norman_f_primary_audit.md), [complete pooled table](norman_f_pooled_holm/pooled_holm.md) and unchanged copied plugins.

The positive reading is a development candidate screen under the agreed criterion, not a fresh-test replication, causal finding or novel biological discovery.

## Reading 2: selected models on the inspected sealed split

Each model was selected by its run’s visible rule. The pinned ce1b530 sealed tool was run only after pooling. It made four oracle scorings per run outside run query caps, including first scoring of the starting EXP_0007 model in each run; all other compared models had been scored at run end. No sealed outcome was used to select or alter any feature or model.

| Source | Selected Pearson delta | Selected − additive ± paired SE | Wins / n; verdict | Selected − start ± paired SE | Wins / n; verdict |
|---|---:|---:|---|---:|---|
| f_r0 | 0.720422 | +0.007830 ± 0.002321 | 39/56; selected better | +0.004298 ± 0.001608 | 38/56; selected better |
| f_r2 | 0.718198 | +0.005606 ± 0.001981 | 33/56; selected better | +0.002074 ± 0.001787 | 30/56; no difference established |
| f_r3 | 0.720116 | +0.007524 ± 0.002134 | 37/56; selected better | +0.003992 ± 0.002494 | 36/56; no difference established |

Cross-run spread is sample SD over the three search seeds on the same inspected cohort, not uncertainty on a fresh cohort. It is distinct from the paired SE in each reading.

| Sealed metric | Selected, mean ± sample SD | Additive, mean ± sample SD | Start, mean ± sample SD |
|---|---:|---:|---:|
| pearson_delta | 0.719579 ± 0.001206 | 0.712592 ± 0.000000 | 0.716124 ± 0.000000 |
| pearson_delta_nontarget | 0.713047 ± 0.001942 | 0.710729 ± 0.000000 | 0.709669 ± 0.000000 |
| mse | 0.005529 ± 0.000104 | 0.005898 ± 0.000000 | 0.005418 ± 0.000000 |
| mse_top | 0.117515 ± 0.004883 | 0.109988 ± 0.000000 | 0.117397 ± 0.000000 |
| r2_top | 0.851298 ± 0.004941 | 0.850030 ± 0.000000 | 0.851635 ± 0.000000 |
| pearson_delta_top | 0.794304 ± 0.005233 | 0.767523 ± 0.000000 | 0.787646 ± 0.000000 |
| direction_acc_top | 0.910714 ± 0.004464 | 0.900000 ± 0.000000 | 0.916071 ± 0.000000 |

Selected-minus-start Pearson across runs: 0.003455 ± 0.001206; selected-minus-additive: 0.006987 ± 0.001206. These spreads do not create a new arm-level significance test.

Only r0 establishes selected-over-start under its paired reading rule; r2/r3 do not. All three establish selected-over-additive Pearson under that rule. Error metrics are mixed: mean top-20 MSE is worse than the additive rule, while mean all-gene MSE is lower; selected all-gene MSE is slightly worse than the starting model. No uniform all-metric win is claimed. Categories below ten sealed perturbations are reported without a verdict. The full readings retain every category and exposure caveat: [r0](norman_f_r0_sealed_reading.md), [r2](norman_f_r2_sealed_reading.md), [r3](norman_f_r3_sealed_reading.md).

## Reading 3: F versus B2, descriptive OOF refits

The rows rebuild recorded selected feature sets/params under the tool’s ridge/alpha procedure; they are not the runs’ original fitted model type and alpha. Parent features dropped by a selected set remain documented in the tool report. There is no sealed F-versus-B2 reading.

| Source | Features | Columns | M1 | M2 | M3 | M4 | M5 | M6 | M7 | M12 | Delta M1 ± adjusted SE | Wins / n |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| f_r0 | 28 | 28 | 0.581095 | 0.568471 | 0.008225 | 0.185655 | 0.707466 | 0.648628 | 0.822842 | 0.739783 | +0.012907 ± 0.004671 | 71/112 |
| f_r2 | 11 | 11 | 0.577974 | 0.567531 | 0.008288 | 0.197469 | 0.698619 | 0.632955 | 0.804985 | 0.687016 | +0.009786 ± 0.003135 | 72/112 |
| f_r3 | 24 | 33 | 0.582510 | 0.571170 | 0.008079 | 0.189547 | 0.704808 | 0.644326 | 0.814658 | 0.765723 | +0.014322 ± 0.004962 | 60/112 |
| b2_r0 | 24 | 26 | 0.573973 | 0.563503 | 0.012737 | 0.227424 | 0.672770 | 0.627463 | 0.800967 | 0.739879 | +0.005785 ± 0.005612 | 61/112 |
| b2_r2 | 16 | 16 | 0.583382 | 0.571248 | 0.008283 | 0.190323 | 0.703731 | 0.640015 | 0.810119 | 0.706521 | +0.015194 ± 0.004759 | 78/112 |
| b2_r3 | 11 | 11 | 0.590017 | 0.578986 | 0.008138 | 0.197924 | 0.700693 | 0.651509 | 0.813690 | 0.602714 | +0.021829 ± 0.008675 | 61/112 |

M1=Pearson delta; M2=non-target Pearson delta; M3=all-gene MSE; M4=top-20 MSE; M5=top-20 R²; M6=top-20 delta Pearson; M7=top-20 direction accuracy; M12=delta scale ratio. M4–M7 use the lab’s top20 by absolute true delta, not CellForge’s Wilcoxon-DE gene list. M8–M11 are not emitted by this tool and are not invented here.

| Arm, n=3 | M1 mean ± sample SD | Delta M1 versus parent, mean ± sample SD |
|---|---:|---:|
| f | 0.580526 ± 0.002321 | 0.012338 ± 0.002321 |
| b2 | 0.582457 ± 0.008062 | 0.014269 ± 0.008062 |

No between-arm test is made with three runs per side. F has no established advantage over B2. OOF labels were used in both systems’ development; these rows are not a headline held-out benchmark or a CellForge win. [Complete comparison](norman_f_arm_vs_b2/feature_compare.md).

## Reading 4: annotation use and recorded resource use

| F run | Annotation plugins | Annotation-only / also Replogle | Selected annotation features | Completed experiments using annotation | Completed annotation-creation experiments |
|---|---:|---:|---:|---:|---:|
| f_r0 | 60 | 52 / 8 | 8 | 335 | 60 |
| f_r2 | 1 | 1 / 0 | 0 | 1 | 1 |
| f_r3 | 33 | 26 / 7 | 4 | 267 | 33 |

Annotation counts use direct source mentions and recorded feature sets. Completed experiments exclude baselines/ensembles; annotation-creation counts distinguish a new plugin from configurations reusing it. They do not count every attempted biological hypothesis or transitive dependency. All plugins are listed in two source groups with key/column evidence in [source inventory](norman_f_source_inventory.md); numeric/dynamic access is explicitly marked as source context rather than inferred runtime use.

| Source | Proposed / completed | Worker calls | Planner calls | Failed calls | Successful planner rounds | Ledger USD |
|---|---:|---:|---:|---:|---:|---:|
| f_r0 | 729 / 584 | 504 | 58 | 0 | 58 | 1.288493084 |
| f_r2 | 272 / 247 | 117 | 16 | 9 | 15 | 0.288033672 |
| f_r3 | 608 / 498 | 496 | 58 | 0 | 58 | 1.247661468 |
| b2_r0 | 730 / 581 | 498 | 59 | 0 | 59 | 1.292618180 |
| b2_r2 | 729 / 559 | 525 | 62 | 0 | 62 | 1.369456972 |
| b2_r3 | 648 / 490 | 406 | 51 | 0 | 51 | 1.194029504 |

| Arm, n=3 | Ledger cost/run, mean ± sample SD | Total ledger USD | Worker calls/run, mean ± sample SD | Planner calls/run, mean ± sample SD | Successful rounds/run, mean ± sample SD |
|---|---:|---:|---:|---:|---:|
| f | 0.941396 ± 0.566197 | 2.824188224 | 372.33 ± 221.16 | 44.00 ± 24.25 | 43.67 ± 24.83 |
| b2 | 1.285368 ± 0.087938 | 3.856104656 | 476.33 ± 62.39 | 57.33 ± 5.69 | 57.33 ± 5.69 |

F r2 recorded nine failed API calls (eight worker, one planner), fewer successful planner rounds and fewer completed experiments. Its lower use contributes to the arm’s lower total cost; this does not establish efficiency of the annotation source. Planner calls include failed/retried calls; successful parsed planner rounds are a different count. Costs are recorded token-cost ledger estimates, not provider invoices. The rounded progress receipts sum to2.824189 USD; the unrounded run usage sums to2.824188224 USD. The original cap remained52.44 and no extra paid call was made during readings.

## Reproduction and continuation

Raw JSON/Markdown twins, unchanged plugins and MD5/SHA256 manifest are preserved. Reproduce reading4 in a fresh own clone/output tree: `norman_f_collect_metadata.py` writes the fixed path `docs/results/norman_f_metadata.json`, refuses replacement and queries metadata through the existing read-only database snapshot helper. Means use `statistics.mean`; SD uses `statistics.stdev` over seeds0/2/3. Raw sources, schemas and full precision are in norman_f_summary.json, norman_f_sealed_summary.json and norman_f_metadata.json.

No active experiment, source, split, guard, existing bundle, ledger or run directory was modified. No lab/model source, configuration or controller change or model promotion is part of this results PR. Future replication requires a separately authorized plan and fresh cohort/test boundary; no follow-on arm is started here.

## Validation and publication evidence

The required full suite passed: **540 passed, 8 warnings in 685.48 s**, exit 0. It ran at nice 19 from the operator clone with API_KEY and DEEPSEEK_API_KEY unset. The eight warnings are existing cell_eval/Polars string-cache deprecations. [Test log](norman_f_pytest.log) and [exit record](norman_f_pytest.exit) are retained. Independent source, primary-rule, arithmetic and final-report audits passed. Credential-shaped-string scans cover result files and the staged diff; copied plugins remain byte-for-byte unchanged.

`norman_f_artifact_manifest.json` records file size, MD5 and SHA256 for every Block F result artifact except itself. `norman_f_plugin_manifest.json` separately records the original-to-copy source hashes. Review this report and the complete pooled/sealed tables before considering any separately authorized replication; the present result does not promote a model or authorize another run.
