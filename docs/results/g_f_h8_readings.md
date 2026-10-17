# G, corrected F and lead H8 readings — 17 October 2026

All prescribed scientific readings completed with explicit exit0 at frozen source2f2e6838316915198c52abeb34cf02f2b3aacc87. G's complete-family test found no qualifying feature on either dataset. Corrected F found six Replogle-assisted development candidates and no tier1 candidate. The lead's unchanged H8 hypothesis was not supported on either dataset. These findings do not establish agent discovery, a screen-free mechanism or a Nature Genetics candidate.

The [JSON twin](g_f_h8_readings.json) carries the exact source run directories, raw summary objects, coefficient arrays, rejected original CpG rows and SHA256 references. The [results index](README.md) lists each new evidence file separately. Repository tests and final publication checks have separate receipts; they are not scientific reruns.

## G reading1: complete-family tests

| Dataset | Tested | Unique after cross-source duplicates | Null replicates | Found | Tier1 |
|---|---:|---:|---:|---|---|
| adamson_cf | 221 | 210 | 999 | [] | [] |
| norman | 174 | 158 | 999 | [] | [] |

Adamson retained all276 copied primary plugins, 221 eligible rows,32 stage1 duplicates and23 exclusions. Norman retained223 copied primary plugins,174 eligible rows (44/62/68),40 within-source duplicates and9 exclusions:6 dependency KeyErrors,1 constant smoke and2 literal caps. No row was repaired, substituted or retried. All status-ok candidates were selected without --k or --partial, and the fixed complete family was scored with999replicates. Both applicable nulls, coefficient signs and every fixed gate were independently audited. The three full-view-only Norman proportional rows lacked valid perturbation nulls and correctly failed.

Raw pooled files retain legacy BlockF/gene_annotation headings and pooled_holm filenames; these G readings cover all three tables. The authoritative pooled columns are p_fwer_pooled and p_fwer_pert_pooled.

## G reading2: exact six-run descriptive OOF comparison

Each arm below is mean ± sample SD (ddof1) over its independent runs0/2/3. The exact six-run call was made once for each dataset, with null_reps0 and no --with-val1. It uses the selected models as recorded, ridge with honest OOF alpha selection and fold seeds101/102/103. This is descriptive development evidence.

| Dataset | Arm | M1 mean | sample SD | ΔM1 versus common parent mean | sample SD |
|---|---|---:|---:|---:|---:|
| adamson_cf | g0 | 0.525950138575 | 0.0352630739505 | 0.0417198688117 | 0.0352630739505 |
| adamson_cf | g1 | 0.490964427987 | 0.00443557778147 | 0.00673415822402 | 0.00443557778147 |
| norman | g0 | 0.577886422128 | 0.00108522001338 | 0.00969837581037 | 0.00108522001338 |
| norman | g1 | 0.57931058046 | 0.00762830793666 | 0.0111225341419 | 0.00762830793666 |

### adamson_cf — all emitted arm metrics

| Metric | G0 mean ± sample SD | G1 mean ± sample SD |
|---|---:|---:|
| M1 (pearson_delta) | 0.525950138575 ± 0.0352630739505 | 0.490964427987 ± 0.00443557778147 |
| M2 (pearson_delta_nontarget) | 0.520590432781 ± 0.0377076711995 | 0.482718890928 ± 0.00422716876626 |
| M3 (mse) | 0.00650928588124 ± 0.000424980806868 | 0.00680374806459 ± 7.78923623712e-05 |
| M4 (mse_top) | 0.125148913713 ± 0.0159510134747 | 0.13695056436 ± 0.0029002619458 |
| M5 (r2_top) | 0.785494390968 ± 0.027152969505 | 0.768171736348 ± 0.00441742317652 |
| M6 (pearson_delta_top) | 0.688553159574 ± 0.0492341709152 | 0.637183723973 ± 0.00450993629205 |
| M7 (direction_acc_top) | 0.861055555556 ± 0.0179616360716 | 0.844555555556 ± 0.00397678448182 |
| M12 (delta_scale_ratio) | 0.655332919126 ± 0.0719384952339 | 0.617155712681 ± 0.0367557556166 |

### norman — all emitted arm metrics

| Metric | G0 mean ± sample SD | G1 mean ± sample SD |
|---|---:|---:|
| M1 (pearson_delta) | 0.577886422128 ± 0.00108522001338 | 0.57931058046 ± 0.00762830793666 |
| M2 (pearson_delta_nontarget) | 0.566388201126 ± 0.00280333244865 | 0.568553864452 ± 0.00772349168473 |
| M3 (mse) | 0.00832757986336 ± 0.000194913794349 | 0.00849378002471 ± 5.29141025555e-05 |
| M4 (mse_top) | 0.191138682272 ± 0.00996222790423 | 0.192200831601 ± 0.00520363877398 |
| M5 (r2_top) | 0.703928366059 ± 0.0101760108776 | 0.701973684604 ± 0.00241547080316 |
| M6 (pearson_delta_top) | 0.631284613068 ± 0.00215348255062 | 0.628596034243 ± 0.00885138733053 |
| M7 (direction_acc_top) | 0.807118055556 ± 0.00831748510718 | 0.806845238095 ± 0.00613060924259 |
| M12 (delta_scale_ratio) | 0.72263581145 ± 0.0450132277495 | 0.708385412783 ± 0.0935091221409 |

Per-run values and source identifiers remain in adamson_cf_g_arm_summary and norman_g_arm_summary twins. No significance or within-noise arm verdict is inferred. The comparison tool emits M1–M7/M12; M8–M11 are absent.

## G reading3: prescribed separate per-run sealed readings

Each dataset used six separate calls in order g0r0/r2/r3 then g1r0/r2/r3; every call exited0 before the next. Only each selected model was read against its own start (Norman additionally reports its own additive baseline in that same prescribed reading). No cross-arm or cross-run sealed pair or selection was made.

These cohorts are worn and indicative: Norman is its fifth reading after B1/B2/B4/F. Norman categories of n8 and n5 are reported only, with no category verdict inferred. On Norman, six starts and g1r2 selected EXP_0671 were legitimate first scorings; all16 available stored-score matches were true and8 null matches were disclosed. Adamson separately has10true/2null checks; its first scorings were g0r3 EXP_0613 and g1r2 EXP_0730. Raw category, paired arithmetic and receipt audits passed. The stored aggregate arm summaries are descriptive only; they do not supply a cross-arm sealed test.

Full new per-run JSON/Markdown and aggregate/audit twins are in adamson_cf_g_sealed_* and norman_g_sealed_*. No old sealed scores were reread.

## G reading4: source, count and planner audit

| Dataset | G1 direct GA/GC/PA calls in selected model r0 | r2 | r3 | G0 direct calls |
|---|---|---|---|---|
| Adamson | 3/5/3 | 1/3/4 | 1/2/0 | 0/0/0 in every run |
| Norman | 0/1/0 | 5/1/1 | 1/3/2 | 0/0/0 in every run |

The Adamson g1r2 GA raw-mention count2/direct-call count1 distinction is preserved. All planner maxima were below20,000 characters; all used DeepSeek without a mixed planner or external knowledge. Norman maxima: G0 15102/14045/13907; G1 15366/17111/16620. Adamson maxima: G0 12541/14717/14826; G1 16967/16834/16605.

Total experiments are MISSING from every permitted .check receipt; no EXP identifier or file count is used to infer them. Static direct calls are not a complete transitive/runtime attribution. Exact schema-name literals, lookup keys, source hashes and fallback/proxy limitations are preserved in the source/direct-table/addendum audit twins. Norman r3e519's TSS windows lack chromosome equality; no missing schema field was silently repaired.

## Corrected F: stage2 and pool only

Original stage1 and all94 plugins were preserved; all66 original status-ok rows (40/1/25) were selected without --k/--partial. Stage2 produced59ok add-one rows,7within-source duplicate rows and3set rows. The corrected pool has59tested,6cross-source duplicates and53unique candidates,999replicates,partial=false,untested=[] and no null-resolution warning.

Six Replogle-assisted development candidates pass the fixed rules; none is tier1. All are non-proportional, so perturbation p-values are absent for these six; both nulls remain applied to proportional members. The independent audit reconstructed all raw/Holm/within-source/pooled p-values, checked59gene and12perturbation nulls with999finite gains each (10unique pooled perturbation rows), all gate/sign/source flags and all66Markdown rows.

| Source | Feature | Gain | SE_adj | Fixed minimum | pooled gene p | Signs |
|---|---|---:|---:|---:|---:|---|
| f_r0 | screen_delta_over_transcript_length_e547 | 0.00372043410993 | 0.00165650638311 | 0.00331301276622 | 0.001 | + in6/6 |
| f_r3 | replogle_additive_x_promoter_cpg_oe_e441 | 0.00261625989944 | 0.00104841107536 | 0.00209682215072 | 0.001 | + in6/6 |
| f_r3 | replogle_additive_x_target_promoter_cpg__e558 | 0.00293176206467 | 0.00136959419364 | 0.00273918838728 | 0.001 | + in6/6 |
| f_r3 | replogle_additive_x_target_promoter_cpg__e590 | 0.00317679126839 | 0.00142661044365 | 0.0028532208873 | 0.001 | + in6/6 |
| f_r3 | replogle_additive_x_target_promoter_cpg_e460 | 0.00293242982622 | 0.00143219796536 | 0.00286439593072 | 0.001 | + in6/6 |
| f_r3 | replogle_additive_x_target_promoter_gc_e328 | 0.00466328343956 | 0.00173066183905 | 0.00346132367811 | 0.001 | + in6/6 |

The six coefficient entries are ordered fold-seed pairs, not six independent runs. All coefficient arrays are retained. Original CpG e428 fails gain0.0005631345545483463<0.002 and pooled perturbation p0.363; e666/e412 are duplicate predictions. Old positive F claims are replaced by this corrected limited result. All142 original artifacts and94 plugins remained byte-identical in both clones after pooling and are checked again at consolidation. No old-null results or old sealed-score values were read.

## Lead H8: fixed human hypothesis, not agent discovery

The lead clarified the parent name BEFORE any H8 score in [comment6236891780](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6236891780): mean_response on Adamson, additive_response on Norman. Both rows were proportional in full/fold views and had the required perturbation null. The formula, words, plugin, sign prediction, both nulls, minimum effect and all other criteria were unchanged. Adamson's predicted positive sign passed; Norman's sign was recorded, not predicted.

| Dataset | Parent | Gain | SE_adj | Fixed minimum | gene p (FWER) | perturbation p (FWER) | Coefficients | Verdict |
|---|---|---:|---:|---:|---:|---:|---|---|
| adamson_cf | mean_response | -0.00134683181807 | 0.00107909103624 | 0.00215818207249 | 1.000 | 0.769 | positive6/6 | Not supported |
| norman | additive_response | 1.44689166563e-05 | 6.82636251194e-05 | 0.002 | 0.199 | 0.526 | negative6/6; not predicted | Not supported |

Both nulls used999replicates. Independent audits passed92checks on Adamson and135on Norman, including finite saved gains, raw/Holm/FWER p-values, all8metrics, signs and every fixed failed gate. Adamson also fails M2; Norman passes M2 but fails M1 effect/report consistency and both nulls.

| Pre-run evidence | Adamson | Norman |
|---|---:|---:|
| Constraint values | 2018/2024 | 2012/2018 |
| CORUM genes | 628 | 639 |
| Reactome sets | 19 | 19 |
| Reactome genes | 286 | 279 |
| Word counts ribosom/proteasom/mrna splicing | 7/9/3 | 7/9/3 |

All19 fixed pathway names and both exact pre-run commands/output/exits are retained in dataset prerun twins. No expression-only/CORUM-only fallback was needed. Unchanged plugin SHA256: d561229865326a42fd0e562f7cb294f40b77788aa0b6ce547c277935311a23ad. Current pre-score README SHA256: beb3e9ae4691c0fd693e44289523fd82e74bfff03fb0336fa4cd3bca490c8dc8. lead_h8_prescore_protocol preserves the exact code, authority and public input hashes.

### adamson_cf H8 — all emitted metrics

| Metric | Default parent | Parent + H8 |
|---|---:|---:|
| M1 (pearson_delta) | 0.484230269763 | 0.482883437945 |
| M2 (pearson_delta_nontarget) | 0.481203697242 | 0.48108081249 |
| M3 (mse) | 0.0066812035665 | 0.00676872887318 |
| M4 (mse_top) | 0.135254758334 | 0.136758958888 |
| M5 (r2_top) | 0.769801054531 | 0.768695045575 |
| M6 (pearson_delta_top) | 0.630481874087 | 0.629953208278 |
| M7 (direction_acc_top) | 0.850333333333 | 0.850333333333 |
| M12 (delta_scale_ratio) | 0.62075682911 | 0.61970858669 |

Fixed failures:

- M1 gain not above 2 SE_adj with wins > n/2
- M1 gain not above the minimum effect 0.002
- an OOF report does not gain
- null p (FWER) > 0.05
- perturbation null p (FWER) > 0.05
- no M2 gain

### norman H8 — all emitted metrics

| Metric | Default parent | Parent + H8 |
|---|---:|---:|
| M1 (pearson_delta) | 0.568188046318 | 0.568202515235 |
| M2 (pearson_delta_nontarget) | 0.560352201774 | 0.560448094093 |
| M3 (mse) | 0.00831844910126 | 0.00830817239667 |
| M4 (mse_top) | 0.192143183362 | 0.191897792134 |
| M5 (r2_top) | 0.701534815117 | 0.70191283192 |
| M6 (pearson_delta_top) | 0.617350910854 | 0.617158814957 |
| M7 (direction_acc_top) | 0.80744047619 | 0.807291666667 |
| M12 (delta_scale_ratio) | 0.731130850349 | 0.736243136343 |

Fixed failures:

- M1 gain not above 2 SE_adj with wins > n/2
- M1 gain not above the minimum effect 0.002
- an OOF report does not gain
- null p (FWER) > 0.05
- perturbation null p (FWER) > 0.05


## Interpretation and preservation

OOF and sealed results are worn development evidence. M4–M7 use top20 by absolute true delta, not CellForge Wilcoxon DE. No fresh-test, within-noise, CellForge victory or biological novelty claim follows. The lead decides the next block; this publication starts no H/R/probe or paid run.

Raw results, JSON/Markdown twins, unchanged plugin copies, pre-score input/source hashes, exact commands/logs/exits and independent audits are retained. The only executable-content additions are unchanged source snapshots under docs/results. No data/runs/private/harness/package contents or credentials belong in Git. The scientific readers, evaluator, guards, splits, source runs and old142Fartifacts are unchanged.

## Issue51 publication receipts

- [Result notice](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6233130270)
- [Result notice](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6236179594)
- [Result notice](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6237566655)
- [Result notice](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6237612172)
- [Result notice](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6237719856)

The consolidated draft PR and export-only receipt are added after the required full suite and final publication checks. The package itself remains outside Git.
