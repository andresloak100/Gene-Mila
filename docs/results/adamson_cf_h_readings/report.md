# H: fixed readings 2–4, Adamson clean tables

The single B.2 call finished with exit0. All results below are OOF development results. GOAL_CRITERIA B.3 and B.4 remain unmet: no fresh test has been scored. A1 is the lab with clean tables; A1abl omits the three new tables; A2 uses one worker; A3 is the Codex client; A4 is Biomni; A5 is our deterministic translation of CellForge ideas; C0 is scripted/mock.

## Reading 2: metrics

Mean ± sample SD across independent search seeds0/2/3; A5 has n1 and no SD. C0 produced identical selected models across its three completed searches. M1–M7/M12 follow FEATURE_COMPARISON_PROTOCOL section5.

| Arm | n | M1 | M2 | M3 | M4 | M5 | M6 | M7 | M12 |
|---|---:|---|---|---|---|---|---|---|---|
| A1 | 3 | 0.490964 ± 0.004436 | 0.482719 ± 0.004227 | 0.006804 ± 0.000078 | 0.136951 ± 0.002900 | 0.768172 ± 0.004417 | 0.637184 ± 0.004510 | 0.844556 ± 0.003977 | 0.617156 ± 0.036756 |
| A1abl | 3 | 0.525950 ± 0.035263 | 0.520590 ± 0.037708 | 0.006509 ± 0.000425 | 0.125149 ± 0.015951 | 0.785494 ± 0.027153 | 0.688553 ± 0.049234 | 0.861056 ± 0.017962 | 0.655333 ± 0.071938 |
| A2 | 3 | 0.511801 ± 0.039550 | 0.506659 ± 0.043304 | 0.006354 ± 0.000601 | 0.124567 ± 0.016993 | 0.787949 ± 0.025890 | 0.660787 ± 0.043064 | 0.857333 ± 0.014434 | 0.651258 ± 0.048319 |
| A3 | 3 | 0.546526 ± 0.012170 | 0.540660 ± 0.008681 | 0.006072 ± 0.000318 | 0.112333 ± 0.007792 | 0.807378 ± 0.015032 | 0.709736 ± 0.017635 | 0.869278 ± 0.007192 | 0.664356 ± 0.022169 |
| A4 | 3 | 0.523532 ± 0.034141 | 0.519905 ± 0.033517 | 0.006411 ± 0.000235 | 0.123813 ± 0.010056 | 0.787480 ± 0.015754 | 0.680098 ± 0.042992 | 0.864111 ± 0.011932 | 0.651402 ± 0.026540 |
| A5 | 1 | 0.512154 (n1) | 0.512075 (n1) | 0.006909 (n1) | 0.147322 (n1) | 0.748358 (n1) | 0.661382 (n1) | 0.856333 (n1) | 0.471396 (n1) |
| C0 | 3 | 0.523681 ± 0.000000 | 0.515872 ± 0.000000 | 0.006226 ± 0.000000 | 0.124464 ± 0.000000 | 0.787762 ± 0.000000 | 0.678488 ± 0.000000 | 0.845500 ± 0.000000 | 0.569879 ± 0.000000 |

| Search | ΔM1 | SE_adj | wins /50 | features | system development verdict |
|---|---:|---:|---:|---:|---|
| A3_r0 | 0.04826509 | 0.01046299 | 34/50 | 1 | meaningful (development, OOF only, not held out) |
| A3_r2 | 0.06998926 | 0.01386193 | 39/50 | 1 | meaningful (development, OOF only, not held out) |
| A3_r3 | 0.06863315 | 0.01461797 | 40/50 | 2 | meaningful (development, OOF only, not held out) |
| A4_r0 | 0.05627735 | 0.01278378 | 38/50 | 1 | meaningful (development, OOF only, not held out) |
| A4_r2 | 0.06162700 | 0.01289557 | 39/50 | 2 | meaningful (development, OOF only, not held out) |
| A4_r3 | 0.00000000 | 0.00000000 | 0/50 | 0 | no candidate: the parent's model |
| A5_C2 | 0.02792333 | 0.00754358 | 36/50 | 1 | not: mse_top significantly worse |
| A1_r0 | 0.00218069 | 0.00481570 | 30/50 | 21 | not: M1 gain not above 2 SE_adj with wins > n/2; an OOF report does not gain; no M2 gain |
| A1_r2 | 0.00698018 | 0.00281665 | 28/50 | 20 | not: mse_top significantly worse |
| A1_r3 | 0.01104160 | 0.00461917 | 31/50 | 20 | meaningful (development, OOF only, not held out) |
| A1abl_r0 | 0.05629398 | 0.01285712 | 36/50 | 8 | meaningful (development, OOF only, not held out) |
| A1abl_r2 | 0.00150591 | 0.00759251 | 30/50 | 21 | not: M1 gain not above 2 SE_adj with wins > n/2; M1 gain not above the minimum effect 0.002; an OOF report does not gain; no M2 gain; mse_top significantly worse |
| A1abl_r3 | 0.06735971 | 0.01352852 | 38/50 | 17 | meaningful (development, OOF only, not held out) |
| A2_r0 | 0.00261113 | 0.00116532 | 27/50 | 8 | meaningful (development, OOF only, not held out) |
| A2_r2 | 0.07317181 | 0.01127903 | 40/50 | 9 | meaningful (development, OOF only, not held out) |
| A2_r3 | 0.00693032 | 0.00348933 | 30/50 | 14 | not: M1 gain not above 2 SE_adj with wins > n/2 |
| C0_r0 | 0.03945096 | 0.00808893 | 39/50 | 3 | meaningful (development, OOF only, not held out) |
| C0_r2 | 0.03945096 | 0.00808893 | 39/50 | 3 | meaningful (development, OOF only, not held out) |
| C0_r3 | 0.03945096 | 0.00808893 | 39/50 | 3 | meaningful (development, OOF only, not held out) |

Per-search pairs above retain the actual comparison. `readings.json` applies the unchanged pure `arm_rule` to these values descriptively, without treating fold reports as independent searches or claiming an arm wins on a fresh test.

| Arm | mean ΔM1 ± search SD | meaningful add-one rows | descriptive rule G / k·SE | median evaluate.py attempts |
|---|---|---:|---|---|
| A1 | 0.006734 ± 0.004436 | 0 | 0.006734 / 0.010060 (none; descriptive) | N/A: lab metadata or deterministic source |
| A1abl | 0.041720 ± 0.035263 | 4 | 0.041720 / 0.069286 (none; descriptive) | N/A: lab metadata or deterministic source |
| A2 | 0.027571 ± 0.039550 | 6 | 0.027571 / 0.091803 (none; descriptive) | N/A: lab metadata or deterministic source |
| A3 | 0.062296 ± 0.012170 | 3 | 0.062296 / 0.030318 (a; descriptive) | 2 |
| A4 | 0.039301 ± 0.034141 | 2 | 0.039301 / 0.070906 (none; descriptive) | 1 |
| A5 | 0.027923 (n1) | 0 | n1; no arm rule | N/A: lab metadata or deterministic source |
| C0 | 0.039451 ± 0.000000 | 3 | 0.039451 / 0.016255 (a; descriptive) | N/A: lab metadata or deterministic source |

## Reading 2: usage and throughput

| Search | wall min | calls | input / cached / output tokens | ledger-price USD | served model / provenance |
|---|---:|---:|---|---:|---|
| A1_r0 | 20.090 | 496 | 1084789 / 526336 / 492341 | 1.282675640 | deepseek:deepseek-v4-pro (planner); deepseek:deepseek-flash (worker); recorded request model, actual served identity not persisted here |
| A1_r2 | 20.075 | 486 | 1063157 / 522880 / 467606 | 1.222116620 | deepseek:deepseek-v4-pro (planner); deepseek:deepseek-flash (worker); recorded request model, actual served identity not persisted here |
| A1_r3 | 20.512 | 502 | 1081075 / 548736 / 442273 | 1.231253372 | deepseek:deepseek-v4-pro (planner); deepseek:deepseek-flash (worker); recorded request model, actual served identity not persisted here |
| A1abl_r0 | 20.517 | 164 | 260871 / 92160 / 167422 | 0.447471784 | deepseek:deepseek-v4-pro (planner); deepseek:deepseek-flash (worker); recorded request model, actual served identity not persisted here |
| A1abl_r2 | 20.512 | 516 | 865172 / 284160 / 462766 | 1.266211636 | deepseek:deepseek-v4-pro (planner); deepseek:deepseek-flash (worker); recorded request model, actual served identity not persisted here |
| A1abl_r3 | 20.522 | 388 | 626687 / 222848 / 313664 | 0.897626396 | deepseek:deepseek-v4-pro (planner); deepseek:deepseek-flash (worker); recorded request model, actual served identity not persisted here |
| A2_r0 | 20.025 | 152 | 316326 / 166656 / 147471 | 0.393610128 | deepseek:deepseek-v4-pro (planner); deepseek:deepseek-flash (worker); recorded request model, actual served identity not persisted here |
| A2_r2 | 20.510 | 78 | 178430 / 84352 / 97635 | 0.240953308 | deepseek:deepseek-v4-pro (planner); deepseek:deepseek-flash (worker); recorded request model, actual served identity not persisted here |
| A2_r3 | 20.008 | 134 | 289853 / 147840 / 104462 | 0.319063752 | deepseek:deepseek-v4-pro (planner); deepseek:deepseek-flash (worker); recorded request model, actual served identity not persisted here |
| A3_r0 | 20.012 | 93 | 8556420 / 8461824 / 68626 | 0.768945870 | deepseek-v4-pro |
| A3_r2 | 20.018 | 58 | 4927782 / 4856192 / 80277 | 0.626068140 | deepseek-v4-pro |
| A3_r3 | 20.015 | 77 | 7856999 / 7773440 / 71808 | 0.736688900 | deepseek-v4-pro |
| A4_r0 | 20.002 | 69 | 4043237 / 3918464 / 87199 | 0.682420810 | deepseek-v4-pro |
| A4_r2 | 20.000 | 85 | 5395225 / 5287808 / 102833 | 0.781672660 | deepseek-v4-pro |
| A4_r3 | 20.002 | 63 | 3556260 / 3469440 / 80941 | 0.587784100 | deepseek-v4-pro |
| C0_r0 | 3.518 | 9 | 7325 / 0 / 2725 | 0.000000000 | scripted planner / mock worker; 9 mock call records, zero paid API calls |
| C0_r2 | 3.613 | 9 | 7325 / 0 / 2725 | 0.000000000 | scripted planner / mock worker; 9 mock call records, zero paid API calls |
| C0_r3 | 3.508 | 9 | 7325 / 0 / 2725 | 0.000000000 | scripted planner / mock worker; 9 mock call records, zero paid API calls |

Costs are recorded ledger prices, not a verified provider bill. Cached tokens are included within input tokens. Package attempt counts exclude baseline TSV rows and count completed evaluate.py records; interrupted or scratch evaluations may be absent. Lab arms use experiments_proposed/completed/rejected/failed/killed/cancelled in the full JSON, not an invented evaluate.py count. C0 has nine mock-worker call records per run and zero paid API calls; its summary duration is the lab search duration, while the C0 outer wall-time receipts include operator/startup overhead. A5 has no H session usage: it is a pre-existing deterministic translation.

## Reading 3: frozen selection

`frozen_selection.json` pins all19 prescribed system identities, eligible top single features, parent and additive-rule identity, code/data/split/source hashes and settings. A5 remains n1; empty Biomni seed3 remains the parent. Identical single-feature prediction hashes are represented once per arm.

**Readiness limitation:** this is an immutable selection/specification batch, not a holder-ready fitted export. The B.2 call saved metrics and fold settings, not deployment weights. `frozen_model.py export` accepts already-fitted archived lab models; those are not asserted to be the exact B.2 fold fits. PLAN_R numeric exports, public-input prediction verification, eligibility/deposit and fresh scoring remain pending. No fitting or scientific rerun was used to conceal that gap. No holder contact or fresh-test call occurred. The additive rule is listed for the prescribed future batch; this Adamson B.2 call has no separately scored pair-additive row.

## Reading 4: sources, attempts and audit

| Session | completed evaluate.py attempts | TSV statuses | accepted kept / handback rejected | knowledge names in kept source | files naming visible harness |
|---|---:|---|---|---|---:|
| A3_r0 | 2 | {'baseline': 1, 'keep': 2} | 1 / 0 | gene_sets | 6 |
| A3_r2 | 1 | {'baseline': 1, 'keep': 1} | 1 / 0 | gene_sets, ppi_network | 20 |
| A3_r3 | 4 | {'baseline': 1, 'rejected': 1, 'keep': 3} | 2 / 0 | gene_sets, ppi_network | 7 |
| A4_r0 | 1 | {'baseline': 1, 'keep': 1} | 1 / 0 | gene_sets | 12 |
| A4_r2 | 2 | {'baseline': 1, 'keep': 2} | 2 / 0 | gene_sets | 10 |
| A4_r3 | 1 | {'baseline': 1, 'discard': 1} | 0 / 0 | none | 4 |

All seven foreign kept files were read by the operator along with their original handback guard/literal reports. They compute control-expression or leave-one-perturbation-out response-transfer features using gene sets/PPI; no pasted response arrays, file/network access or direct harness-label reads occur in those kept files. This is a source inspection, not a claim about everything the authoring agent did. Handback rejection count is distinct from evaluate.py rejection/one-change decisions. Lab selected model source identities and static knowledge calls are pinned in the frozen selection; lab experiment rejection categories remain as recorded in summary metadata.

The harness scan counts **files naming** `val1.npz` or `harness/val1`, excluding the package MANIFEST/program. Copies of one event can occur in multiple files; counts are not read-event counts, evidence of actual label reads, or proof no label was read. Visible harness access by the foreign authoring agent was allowed and disclosed; all frozen selection uses OOF only. Codex seed3’s literal `requests` transcript flag arose in a printed harness spec; the flag alone proves neither network access nor a failure. Original transcript hashes and flags are retained; raw transcripts/matrices are not published.

The three smoke rows and one duplicate row are left unchanged in B.2 JSON and listed in readings.json. No feature was repaired or dropped to improve this report.

## Reproduction and limits

Use the exact one-call command and candidate manifest in receipts; the B.2 JSON is the full precision authority. Reporting only reads existing outputs, archived selection metadata and static source, and uses the pure arm_rule function. No evaluator, guard, split, source feature or dataset was changed. Main checkout, driver STOP and prior failure evidence remain untouched.

B.2’s equal-scoring procedure is complete for these prescribed sources. Budget/timing/client versions and prior probe/image/STOP changes are disclosed in operational receipts. CellForge’s closed external attempt is distinct and not comparable to this translated A5 source. No claim of fresh-test superiority, biology discovery or publication-goal completion is supported by this development table.

## Additional source and decision details

The feature named `protein_domain_similarity_response_trans_e96` does not read a Pfam/InterPro domain table: its code uses gene-set, PPI and prior-network memberships as proxies. The feature name is not evidence of its mechanism. The operator read the selected single-feature sources before freezing; no source was edited.

Codex seed3’s rejected evaluation is recorded as a smoke rejection for a constant feature, followed by accepted later evaluations; the rejected implementation is not a candidate. Biomni seed3’s attempted coexpression feature was discarded, leaving the accepted handback empty. The recorded decisions show no one-change rejection; absence of such a record is not proof of every attempted scratch action. All handback guard/literal rejection counts are zero; package evaluation rejection is a different denominator.

| Lab search | selected source knowledge names (static calls or declared inputs) | proposed / completed / failed / rejected / killed / cancelled |
|---|---|---|
| A1_r0 | gene_annotation, gene_constraint, gene_sets, ppi_network, protein_annotation, transcription_factors | 790 / 665 / 52 / 8 / 2 / 9 |
| A1_r2 | gene_annotation, gene_constraint, gene_sets, ppi_network, prior_network, protein_annotation, transcription_factors | 755 / 652 / 46 / 9 / 0 / 2 |
| A1_r3 | gene_annotation, gene_constraint, gene_sets, ppi_network, prior_network, targets, transcription_factors | 822 / 686 / 43 / 7 / 1 / 14 |
| A1abl_r0 | gene_sets, ppi_network | 301 / 238 / 11 / 3 / 3 / 13 |
| A1abl_r2 | gene_sets, ppi_network, prior_network, targets | 826 / 641 / 52 / 11 / 1 / 18 |
| A1abl_r3 | gene_sets, ppi_network, prior_network, targets, transcription_factors | 631 / 570 / 22 / 1 / 3 / 8 |
| A2_r0 | gene_annotation, gene_constraint, gene_sets, protein_annotation | 177 / 145 / 11 / 1 / 1 / 3 |
| A2_r2 | gene_constraint, gene_sets, ppi_network, prior_network, protein_annotation | 123 / 101 / 5 / 1 / 1 / 9 |
| A2_r3 | gene_annotation, gene_constraint, gene_sets, ppi_network | 169 / 147 / 10 / 3 / 0 / 0 |
| C0_r0 | gene_sets, ppi_network, prior_network, targets | 177 / 175 / 1 / 0 / 0 / 0 |
| C0_r2 | gene_sets, ppi_network, prior_network, targets | 181 / 180 / 1 / 0 / 0 / 0 |
| C0_r3 | gene_sets, ppi_network, prior_network, targets | 179 / 178 / 1 / 0 / 0 / 0 |

Static source names and declared inputs identify dependencies, not an exhaustive runtime file-access trace. All B.2 literal and guard rejections are preserved without repair. No private/split/summary.md or old sealed artifact was manually read.

## Execution provenance and scope

H C0/A2 used frozen `baa7dfdbf17abd17a306d4dcfccb297baaf63b52`. Foreign sessions used immutable Docker image `sha256:b15af00eb763c5fb0fa8cb8001c3cd2d8b649492b11910ac0b90d5b799466a09`, Biomni0.0.8 and Codex0.166.0; exact host/baked source hashes and versions are in `receipts/resumed_20261101/image_preflight.json`. Operational source changes by the lead resolved the probe allowance, STOP-file coupling and image-name inspection before the authorized resumes; passed seeds were not repeated. The image-ID check ran once after PR106 and containers used the pinned ID. Prior stops and receipts are retained in this repository’s earlier H receipt directories and the copied operational metadata. The only B.2 call used lead-merged PR107/f58d44d for the empty-handback correction.

Shared ledger after H and before free readings:66.731336552 (24681 rows), below native H cap76.56 and user H/DK cumulative authorization95. Probe/failed-attempt spending stays charged; nine-session totals do not replace the shared ledger. Existing funds only, no top-up or balance/UI access. All raw datasets, run directories, model arrays and transcripts remain outside Git.

The full receipt source/destination hashes are in `receipt_sources.json`; B.2 raw JSON/Markdown are byte-for-byte unedited. This report adds no scientific job, model fit or score call.

## Arm usage totals and freeze receipt

| Arm | session wall minutes summed | recorded calls | input / cached / output | ledger-price USD |
|---|---:|---:|---|---:|
| A1 | 60.677 | 1484 | 3229021 / 1597952 / 1402220 | 3.736045632 |
| A1abl | 61.550 | 1068 | 1752730 / 599168 / 943852 | 2.611309816 |
| A2 | 60.543 | 364 | 784609 / 398848 / 349568 | 0.953627188 |
| A3 | 60.045 | 228 | 21341201 / 21091456 / 220711 | 2.131702910 |
| A4 | 60.003 | 217 | 12994722 / 12675712 / 270973 | 2.051877570 |
| A5 | 0.000 | 0 | 0 / 0 / 0 | 0.000000000 |
| C0 | 10.640 | 27 | 21975 / 0 / 8175 | 0.000000000 |

A5 zeros denote no new H search/session, not a measured zero-cost CellForge run. C0 calls are mocks. The 154 status-ok add-one rows are evaluated rows, not 154 improvements or discoveries; meaningful verdict counts are separate. Family-wise correction follows the tool’s prescribed within-source families (including prediction-hash duplicates), not a newly pooled across-arm null.

Frozen selection manifest SHA256 `8d34860a4e5e0af418034e84a5b6c0716f0aa98a815442079bf33f891673f913`, posted on [#41 before holder contact](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6566294043). This fulfills the H identity/selection listing; PLAN_R fitted exports and fresh-test deposit remain pending. No holder has been contacted.
