# Handoff: the state of the lab and the open work

Read [`AGENTS.md`](AGENTS.md) first; its rules apply to everything here.

## 1. Current state (whoever is working keeps this true)

**Completed model-quality block, 2026-10-14 02:57 UTC (13 October local) — Claim [#34](https://github.com/andresloak100/Gene-Mila/issues/34) closed:**
[PR #35](https://github.com/andresloak100/Gene-Mila/pull/35) stays an unmerged research record, final evidence
**dab64d0**. Documentation-only [PR #36](https://github.com/andresloak100/Gene-Mila/pull/36) merged2824088;
[PR #37](https://github.com/andresloak100/Gene-Mila/pull/37) merged **e5a2216**. Andres's explicit README/
documentation and bounded merge instructions authorize this useful evidence/Claude continuation update;
no rejected candidate code or model promotion was merged. **No model/controller process remains.**

Distinct source defect identified before Claim32 outcomes: e34 whole-batch fallback changes an
unmatched pair when an unrelated matched pair joins. e401 inherits it. Metadata-only activation showed
3matched/38unmatched pairs,14/15mixedtrain and7/15mixedquery batches in Claim32 partitions.
Copied e34version3 corrects fallback per row, matching original standalone semantics and preserving
nonzero positive/negative priors, missing/zero-edge fallback and singletons. Behavioral/e401 invariance
tests pass. Originalr2alpha **.00198**, specifications/features/params/columns/seeds/e401 and package
stay unchanged; only one copied plugin differs. This is a component correction, not an accuracy claim.

Prospective plan **9920fec**, reviewed source **d3909a1**, published before outcomes; exclusive
gene-mila-pair-batch/runs/b1_pair_batch_20261013 completed **45fits,268.524s,$0**, seeds12/13/14 x5fullhide.
Fixed gate **FAILED**: primary Pearson change **-0.0000027117 +/- 0.0000282624**, mixedsigns and below
.002; candidate/additive meanMSE **1.04495856>1.01**. Other errorguards pass. Candidate Pearson
**0.588816 +/- 0.021337**, control **0.588819 +/- 0.021309**, additive **0.562024 +/- 0.019969**.
Candidate MSE **0.008777 +/- 0.001214**, top20MSE **0.197545 +/- 0.023791**.
Paired MSE change againstcontrol **-0.009056 +/- 0.015643** lies insidepartitionSD; no stable-halving
claim. Posthoc existing-array decomposition shows seed14 change almost entirely gene-constant offsets,
consistent with error movement/almostunchangedPearson; descriptive only, no new candidate or causalproof.

Focused **8passed3.59s**; full **490passed**, no skips,8dependency warnings648.09s. Independent source/
method review and raw **2880metric/5138aggregate/21exactarray/15fold/45event/14source/820package/
292original+292copiedplugin** checks PASS. Chat2 data-free **2560statistic pairs/all6tables/counts/
fullhides/spec/gates** PASS. No discrepancy/fit replay. Exact config/summary/progress/command, all6arms/
10metrics/strata/plugin/source/runtime pins/reviews/checksums in docs/B1_PAIR_BATCH_RESULTS.md and
docs/results/b1_pair_batch_20261013/ onPR35. Key-shaped scan and SHA256/MD5 checks pass.
Integration README/map/datedMac snapshot are current; READMEchecker0errors/0warnings. Numeric arrays,
copiedplugins and originalpackage/context remain ignored locally. Root owns finalpublication/state;
collaborators finished. Main4562af5b/STOP/protected/private/split/data/account/ledger unchanged.

**Exact next for Claude:** preserve closed Claims30/32/34 and all original packages/runs; do not retune
their objectives/fallback/alpha/seeds/margins or merge unused research code. The previously supported
r1+r2 composition from Claim28 remains a development candidate; original frozenB1 remains delivered.
Read all three negative reports, the two-member report and docs/EXTERNAL_COHORT_METADATA.md. Specify
a separate frozenr1+r2 versus additive comparison on compatible unseen perturbations, with source/
batch recipe, cohort/controls/preprocessing, response-access boundary and multi-metric advancement
rule fixed before outcomes. Evaluatoraccount/host/cohort setup remains **deferred, not approved**;
a concrete proposal/owner decision is still needed before changing access or enrolling a new cohort.
No automatic new fits/exports/paidcalls/worn-heldout lookup or B3 restart. No fresh-test/CellForge win
or historicalB1score-drop claim. SharedDeepSeek provider-filtered ledger **43.599822392/cap48** unchanged.

**Completed and rejected, 2026-10-14 02:15 UTC — Claim [#32](https://github.com/andresloak100/Gene-Mila/issues/32) closed:**
[PR #33](https://github.com/andresloak100/Gene-Mila/pull/33) unmerged research record, evidence **618c4da**.
Independent raw2880metric/5139aggregate/21exactarray/15hide/45event/12source/820package checks PASS;
Chat2 data-free2560statistic pairs/all6report tables/alpha-only identity/counts/gates PASS.
No discrepancies or fit replay. Correct fixedgateFAILURE only top20/control **1.0106722979>1.01**.
All outcomes/report/reviews/SHA256/MD5 archived on PR33 in docs/B1_R2_REGULARIZATION_RESULTS.md and
docs/results/b1_r2_regularization_20261013/. Exact sampleSD figures and initial execution log below
are dated history; verification is complete. No process remains. No alpha/threshold/feature/seed retuning.
Claims30/32 failures remain closed and separate; the new e34 correction was already identified source
work, not a revised alpha candidate. Source defect efficacy remains unknown until prospective test.

**Model comparison completed; verification in progress, 2026-10-14 02:10 UTC (13 October local) — Claim [#32](https://github.com/andresloak100/Gene-Mila/issues/32),
draft [PR #33](https://github.com/andresloak100/Gene-Mila/pull/33):** Andres's explicit request to
improve the model authorizes this distinct free development block after rejected Claim30.
Own astra/b1-r2-regularization / gene-mila-r2-regularization, integration base a8f433e.
Prospective plan **fe64e9e**, docs/B1_R2_REGULARIZATION_PLAN.md, pushed before any outcome.
Change only deep-copied r2 ridge alpha0.00198 to20000, matching existing r1. Original features,
parameters/columns/model seeds/training-only scaling/train-then-whole-fold batches and equal weights
remain fixed. Same public cohort, fresh partition seeds9/10/11 x5;45 shared r1/originalr2/modifiedr2 fits.
Source audit flags existing batch fallback/kernel/external-input assumptions; this test preserves them,
does not establish their cause or repair them. No grid, scalar calibration, inner selection or old-seed
candidate scores. No paid/protected/account/main/data/STOP change. Delivered original B1 unchanged.

Fixed advancement: MSE improvement over equal original r1/r2 positive eachseed and mean>sampleSD;
candidate mean MSE/top20MSE<=1.01*additive mean, top20MSE<=1.01*fixedcontrol mean; Pearson change>=-.01
eachseed and mean>=-.002. Ratios of means; practical development screen, not independent validation,
significance, noninferiority or CellForge evidence. Failure closes this block without penalties/features/
seeds/margins retuned; passing only nominates independent validation, no automatic frozen export.

Root owns reviewed source/plan/parentlauncher/Git/docs/shared/live state. Focused8passed1.32s;
independent source/method review no material issue. Full **490 passed**, no skips,8warnings647.09s.
Reviewed code **8134cd9** scanned/published before fitting; helper/core unchanged. The exclusive run
completed cleanly in **266.442s,45fits,$0**, all3seeds9/10/11. No model/controller process remains.
Saved gate **FAILED**: only top20MSE/fixedE mean ratio **1.0106723** exceeds1.01. Other guards pass:
MSE gain **0.0001540287 +/- 0.0000925371**, Pearson change **-0.0004494645 +/- 0.0002914937**;
candidate Pearson **0.593702 +/- 0.005731**, control **0.594151 +/- 0.005555**, additive
**0.570125 +/- 0.005630**. Candidate MSE **0.00757968 +/- 0.00019867**, top20MSE
**0.17374269 +/- 0.00382295**. These are saved outcomes pending independent confirmation.
Do not relax the limit, reprice the failure, retune alpha/features/seeds or promote/merge unused code.
Exact next: independent raw-array/metric/stratum/gate/hash and Chat2 data-free verification; complete
all-outcome archive/checksums/report/current docs and close Claim32. DraftPR33 stays a research record
if checks confirm failure. Root owns publication/live/shared state; reviewer read-only, no fitting/API.
A source-only assessment of the already known prior-edge batch behavior is separate preparatory work,
not another candidate fit or permission to change this closed block. Keep delivered originalB1.
Main remains4562af5b; STOP stays. DeepSeek43.599822392/cap48 unchanged.

**Completed and rejected, 2026-10-14 01:47 UTC — Claim [#30](https://github.com/andresloak100/Gene-Mila/issues/30) closed:**
draft [PR #31](https://github.com/andresloak100/Gene-Mila/pull/31) stays unmerged research record;
final evidence **72e26bd**. Source1238dac/plan21f50d9 published before the exclusive
gene-mila-nested-blend/runs/b1_nested_blend_20261013 run;120fits,506.492s,zero API cost.
Full490passed/no skips/8warnings648.89s; focused8passed3.73s. No process remains.
Nested scalar C=A+lambda*(E-A), E=equal r1/r2; outer6/7/8 x5,inner3 gene-hidden folds; closed unchanged.
MSE improvement **0.0012205263 +/- 0.0012909020** is smaller than sampleSD; Pearson change
**-0.0179080735 +/- 0.0040632603** fails everyseed/mean margin. Error guards pass but do not override
the failed gate. C Pearson **0.557795 +/- 0.007611**, E **0.575703 +/- 0.009284**, additive
**0.549573 +/- 0.007776**; these are same-cohort development partitions, not delivered-model/test scores.
Independent raw2400metric/4179aggregate checks and15learnedweights/45inner/15outer memberships/
120event/package/source hashes PASS; Chat2 data-free2080statistic pairs and all counts/gates PASS.
Complete report/docs archive/checksums at docs/B1_NESTED_BLEND_RESULTS.md and
docs/results/b1_nested_blend_20261013/ on PR31. Numeric arrays/inner OOF stay ignored locally.
No tuning of lambda/objective/zero-weight epsilon/groupweights after outcomes. Keep originalB1.

**Completed and merged, 2026-10-14 00:37 UTC (13 October local) — Claim [#28](https://github.com/andresloak100/Gene-Mila/issues/28) closed:**
[PR #27](https://github.com/andresloak100/Gene-Mila/pull/27) merged as **0db04e42**;
[PR #29](https://github.com/andresloak100/Gene-Mila/pull/29) merged as **6e17ff8c**, evidence head **337ef8a**.
Andres's “go” accepted diagnosis then one targeted change; his explicit “merge it” instruction,
narrowed to useful model changes, covers these independently reviewed changes after the fixed gate passed.
No protected edit, new paid call, account change, main-checkout update or delivered-model promotion followed.

One fixed free run: `gene-mila-b1-two-member/runs/b1_two_member_test_20261013`,
**45 shared original-recipe fits, 307.875s**. Prospective plan **2fc1ab1**, reviewed source **5467687**
published before outcomes; fold seeds3/4/5, five folds, original features/parameters/alphas/model seeds.
Candidate r1+r2 mean Pearson delta **0.584325 ± 0.011274**, three-member refit control
**0.458983 ± 0.020521**, additive **0.561655 ± 0.008879** sample SD over same-cohort partitions.
Primary paired gain **+0.125342 ± 0.015775**, all3 positive; mean exceeds max(0.002, sampleSD).
Mean MSE/control ratio **0.696179**, top-20 MSE/control **0.944288**; both pass the1.01 guard.
Candidate MSE **0.009420 ± 0.001651**, top-20 MSE **0.200563 ± 0.008383**;
control **0.013530 ± 0.001790** / **0.212396 ± 0.006466**. Against additive, candidate correlation
**+0.022670 ± 0.002693**, but mean MSE/top-20 MSE remain **10.6%/4.1% higher**. No blanket additive win.
r1 alone is similarly correlated with lower mean error in descriptive context; no new subset was selected.

Full **482 passed**, no skips,8 dependency warnings,654.28s; focused **15 passed**1.39s.
Independent source/method review, raw **3,840 metric/4,492 aggregate** checks, Chat2 **2,240 mean/SD
statistic pairs**, separate report review and all source/input/array/gate checks pass. No discrepancies.
After merging, executable/test bytes match the full-suite source, both archive SHA256/MD5 lists and
source pins pass, secret scan passes and README checker has0errors/0warnings. Findings/all10metrics,
all seeds/strata, exact command, config/both summaries/progress/reviews/receipts are published in
`docs/B1_TWO_MEMBER_RESULTS.md` and `docs/results/b1_two_member_test_20261013/`. Numeric arrays/package
stay ignored locally. README, documentation map and dated `docs/mac/STATE.md` snapshot are current.
Root updated shared/live state; collaborator reviews finished. No model/controller process remains.

**Exact next for Claude:** read the two result reports and current package manifest, preserve this closed
composition block, and specify a frozen r1+r2 versus additive comparison on compatible unseen
perturbations. Fix the response-access boundary, cohort/controls/preprocessing and multi-metric
advancement rule before outcomes. This needs a distinct prospective claim/plan; account/host/cohort setup
is still **deferred, not approved**. Do not silently extend subsets/weights/seeds, refit or create a new
package, reopen diagnosis seeds0/1/2, query worn held-out scores, restart B3 or run paid agents.
Original frozen B1 remains delivered, manifest225adc3079251f3cd17f16999b3bc92ab18ae20e9fcde9ee0617b8f350869b45.
New partitions reuse the historically selected cohort; this is development robustness, not independent
validation or proof original B1's historical0.723 dropped. No CellForge superiority is established.
Main4562af5b/STOP/data/private/splits/protected code/permissions unchanged. DeepSeek ledger read-only
verified **43.599822392**, cap48; Claims26/28 spent$0. Filter ledger `provider='deepseek'` for this cap:
the same ledger also stores Claude CLI subscription estimates. Never sum all providers for the DeepSeek cap.

**Completed diagnosis, Claim [#26](https://github.com/andresloak100/Gene-Mila/issues/26),
[PR #27](https://github.com/andresloak100/Gene-Mila/pull/27), claim closed, evidence head 0e2ec6a:**
Published plan 1fdadb9/57d83d2 and reviewed source 07a3baa before fitting. One free run at
`gene-mila-b1-diagnosis/runs/b1_development_diagnostic_20261013`: 45 fixed refits, 302.190s, no retry/API.
Original three B1 recipes under full gene-hide unions, seeds0/1/2 x five folds, training-only scaling.
Ensemble Pearson delta **0.476530 ± 0.035865**, additive **0.561398 ± 0.016064**;
paired **−0.084868 ± 0.022776** sample SD. r1 **0.586247 ± 0.017491**, r2 **0.584365 ± 0.020631**,
r3 **0.309025 ± 0.107512**, with much higher error. These are refits, not frozen B1 rescoring.
A read-only r3 audit found a batch-dependent fallback and train/unseen proxy mismatch; their causal role
is unproven and snapshots remain unchanged. All ten metrics and descriptive metadata strata are in
`docs/B1_DIAGNOSTIC_RESULTS.md` and its complete archive. Full **474 passed**, no skips,
8 dependency warnings, 654.14s; focused7 passed. Root independently verified 2,400 raw metric values;
chat2 verified 1,440 statistic pairs, counts, folds and progress. No discrepancies. Secret scans,
SHA256/MD5 lists, exact command and dated Mac overview are published. Numeric arrays remain ignored locally.
This task is complete; Claim28 owns the one prospective follow-up. Do not rescreen the diagnosis seeds.

**Latest result, 2026-10-13 22:40 UTC — Claim [#24](https://github.com/andresloak100/Gene-Mila/issues/24),
draft [PR #25](https://github.com/andresloak100/Gene-Mila/pull/25), archive head **3f78618**, claim closed:** completed one free, fixed
missing-singleton transfer development comparison. **Negative primary result; do not promote or merge
the unused experimental feature/tool. B1 remains delivered and unchanged.** Plan `c8c1358`, reviewed
implementation `7606c04` were published before fitting; own `astra/singleton-transfer-development`,
`gene-mila-singleton-transfer/runs/singleton_transfer_development_20261013`. Three outer gene-fold seeds,
five folds, nested alpha selection, 112 public-training conditions/2083genes. Candidate minus matched
five-column control Pearson delta **−0.003245 ± 0.001620 sample SD**, all three negative. Control
0.573512±0.015021; candidate0.570267±0.013404. MSE control0.008086±0.000372/candidate0.008132±0.000304;
top20MSE0.194277±0.013439/0.193232±0.012043 (paired improvement smaller than its SD).
These are same-cohort development partition sensitivities, not independent replication, historical
B1 held-out comparisons or CellForge results. Fixed gate failed; StageB correctly **skipped**.
480A/0Bfits, summary57.771s; no retry/grid extension/API call. Full **529passed**, no skips,
8dependencywarnings653.50s; focused62passed2.19s. Independent raw-array arithmetic verified150metric
values (maxdifference8.882e-16), source/input hashes and seed aggregates. Complete ten-metric results,
allfolds/alphas/coverage, config, sourcepins, review, SHA256/MD5 and exactlauncher are archived in PR25:
`docs/SINGLETON_TRANSFER_RESULTS.md`, `docs/results/singleton_transfer_development_20261013/`.
Numeric predictions stay ignored locally, with hashes in the archive. No model/controller run remains.

Andres asked every change/finding be on GitHub so Claude can resume. Publication and independent checks are complete. Chat2 independently verified90 aggregate/paired
statistic pairs, folds, fitcounts, inneralpha choices, gate and progress; no discrepancies. Root
updated this shared state/live Mac STATE; no collaborator has outstanding experiment work. **Exact next:** read PR25's negative report
and preserve this closed grid; do not run conditional StageB or tune it after its outcomes. A next
model block needs a distinct prospective hypothesis and matched public-development control. Keep B1;
no supported replacement was found. Claim22/evaluator-account setup remains **deferred, not approved**;
no permissions changes. STOP/main4562af5b/private/splits/protected code unchanged, sharedledger
43.599822392/cap48, noAPIspend. B3 stays dropped. This latest decision supersedes the older account-first
next steps below; no additional automatic model or paid run is authorized by this completed plan.

**Latest follow-up, 2026-10-13 21:24 UTC — Claim [#22](https://github.com/andresloak100/Gene-Mila/issues/22),
draft [PR #23](https://github.com/andresloak100/Gene-Mila/pull/23):** Andres said “go test” then “use the
deepseek agents”; he is unsure of a separate evaluator account/host. Chat 1 owns
`astra/test-readiness-deepseek` / own `gene-mila-test-readiness`. Two sequential DeepSeek V4 Pro text
reviews completed under the published plan/prompts/config `d89e822`, existing LLMGateway, worker cap
$0.25 and unchanged cumulative cap $48. No retries/fallback/planner. Run `runs/test_readiness_20261013`:
3,209 input/1,466 output tokens; ledger increment **$0.01004124**, current total **$43.599822392**.
No model search, inference, fit, new score or label/efficacy read. STOP/main/data/protected code unchanged.
The cohort/source audit confirms incomplete target-specific frozen features and no verified pure
condition/control manifest. Missing profiles do not prove poor accuracy. The raw DeepSeek reviews
contain errors: output-gene measurement is not perturbation exposure; 19 targets are not 19 rejected
conditions; a hypothetical prediction probe is not a performance test. Preserve raw reviews and the
explicit corrections in `docs/TEST_READINESS_20261013.md`; do not adopt them uncritically.
Chat 2's useful metadata search and the independent source audit are complete. No further paid calls.
Current orchestration user is admin; proposed `genemilaeval` does not exist. Andres was asked approval
for a Standard evaluator account plus an actual access-denial/elevation check; no answer or account
change yet. PR #23 evidence head `645e21d` is published: full **467 passed**, no skips, 8 dependency
warnings (657.02 s), four synthetic privacy/error checks, independent source/runner review, hashes,
ledger arithmetic and secret scans pass. Raw review hard-break whitespace is intentionally preserved.
The exact next step is Andres's evaluator-account decision, design-only condition/guide/control
projection, and verified access denial before candidate responses; then freeze preprocessing, baseline
packages/query budget and a concrete uncertainty rule before scoring. Account setup alone is not proof.
Claim #22 stays open for that decision; no work runs now. B3 remains dropped; no new lab run is authorized.

Update this section when you start, after each milestone, and before you stop or run out of
tokens; commit it straight to the integration branch (AGENTS.md, "Git"). Times are UTC.

**Last updated:** 2026-10-14 01:21 UTC, Astra (Codex), chat “1”. Claim30 publishedsource/fulltests complete; sole fixed run starting.
STOP remains present; shared DeepSeek ledger **$43.599822392**, cap **$48**. Main Mac checkout remains
`4562af5b`, untouched. The 13 Oct console screenshot showed $28.20 cash available/$21.79 billed;
do not reprice the conservative ledger or infer a new paid block. The previous merged block incurred no API spend; the Claim #22 review cost is recorded above.

**Andres's latest decisions, 13 Oct:** “i need you to merge it as well” authorizes the completed changes;
then “please dont overengeneer” and “just make sure whatever is being merge is going to help our model
otherwise dont do it” narrow the merge to model-research necessities and the requested README/handoff.
This supersedes the earlier no-merge instruction only for this bounded work. No protected-code edit,
main-checkout update, paid experiment, permission change or new test-data acquisition is authorized.

**Merged into the lab branch:**
- [PR #27](https://github.com/andresloak100/Gene-Mila/pull/27), merge0db04e42, and
  [PR #29](https://github.com/andresloak100/Gene-Mila/pull/29), merge6e17ff8c: fixed B1 refit diagnosis
  and one supported two-member development screen, complete verified evidence and current documentation.
  No automatic frozen-package/delivered-model change; see the latest result above.
- [PR #13](https://github.com/andresloak100/Gene-Mila/pull/13), merge `491986ee`, claim #11: removes
  `best_sealed` from new warm starts and legacy planner context. Actual planner-request regressions,
  independent review and full **440 passed** (656.85 s). Historical exposure remains; this explicit
  feedback fix does not isolate files from the local controller.
- [PR #19](https://github.com/andresloak100/Gene-Mila/pull/19), merge `0fd91607`, claim #14: frozen
  numeric export/target-only inference, 27 focused cases and full **464 passed** (652.70 s), no skips.
  One stored-prediction replay at `gene-mila-export/runs/norman_frozen_export_20261013` completed in
  59.009 s. All three B1 members reproduce bit for bit on 119 original conditions × 2,083 genes;
  their equal average passes predeclared rtol=atol=1e-6 (max difference 5.960464477539063e-08).
  Full model-grid indices 0/1/4, exact order, hashes, runtime/core audit and independent raw-array
  checks pass. Data-free receipts/checksums/driver/report are in `docs/results/norman_frozen_export_20261013/`.
  Numeric models/context/predictions stay ignored locally. No labels, scoring, refitting or gain claim.
- [PR #20](https://github.com/andresloak100/Gene-Mila/pull/20), merge `9081e848`, claim #18, chat “2”:
  `docs/EXTERNAL_COHORT_METADATA.md` and its JSON guide-only audit. Neither cohort approved. Pacalin:
  19 putative promoter targets partition into 8 training, 2 other Norman-context, 4 outside context
  but inside the frozen gene universe, and 5 outside that universe. The four are FAM83A/GATA1/MYC/YY1,
  **not four eligible conditions**. Guide locus, observed configurations/controls, exposure and frozen
  feature-input coverage remain unresolved. Replogle exp8 is chiefly same-gene guide dosage; its exact
  target-only projection remains unverified. No expression/efficacy/per-cell response data was read.
- [PR #21](https://github.com/andresloak100/Gene-Mila/pull/21), claim #16: requested journal-style README/current-status documentation is merged.
  GitHub-native title/abstract/evidence/figure captions/references; no figure or numerical result change.
  README checker: 0 errors/0 warnings; GitHub CI, secret and diff checks pass. Mac snapshot/MD5 included.

**Completed, intentionally unmerged:**
- [PR #17](https://github.com/andresloak100/Gene-Mila/pull/17), claim #15, archival head `a699d44`:
  pre-specified public-training diagnostic; plan `fe98ed7` preceded outcomes, reviewed code `0fbb8ce`,
  full **447 passed** (646.95 s). Run `gene-mila-shrinkage/runs/norman_development_shrinkage_20261013`.
  Four fixed recipes, 10 metrics, three fold seeds; low-penalty ridge is identical. Calibration minus
  ridge top-20 MSE +0.001208 ± 0.002419 sample SD over the same-cohort fold seeds: no supported average
  benefit. All config/summary/results/checksums remain on its branch; no tool/model change is being
  integrated. Do not enlarge this closed grid from its results. Delivered B1 unchanged.
- Draft [PR #12](https://github.com/andresloak100/Gene-Mila/pull/12), claim #9, `c15034a`: optional
  handoff stop-evidence/reporting fix, full 445 passed/2 skipped, independently reviewed. Not prioritized
  for integration under the latest scope. Draft [PR #10](https://github.com/andresloak100/Gene-Mila/pull/10),
  claim #8: B2 verification/archival state. Its numerical verification is complete. PR #7 has one stale
  mutable STATE checksum; all scientific/config/summary/log hashes pass. Preserve the caveat.
- Claude archival PRs #6/#7 remain separate and unmerged. Do not silently merge them or rewrite their
  scientific outputs. Optional combined local test in `gene-mila-integration-check` finished 487 passed,
  8 dependency warnings,604.30 s; it included unmerged #10/#12/#17 and is **not** the live integration's
  test count. No further test repetition is needed absent a new change/failure.

**Cross-chat coordination:** Andres explicitly requested coordinating, then said to use chat “2” only
when useful. Chat “1” owns current export/shrinkage/README worktrees, commits/merges and shared
HANDOFF/live Mac STATE. Chat “2” finished claim #18 on its own `astra/external-cohort-metadata` branch;
it stopped overlapping writes/runs. Its independent archive review also verified the diagnostic's raw
statistics and checksums. No additional chat or implementation is needed for the finished audit.

**Earlier clean-test planning (deferred by the latest model-priority decision):** the selected merges and requested README are complete. Read the merged
`docs/FROZEN_TEST_PLAN.md`, `docs/FROZEN_EXPORT.md` and `docs/EXTERNAL_COHORT_METADATA.md` before new work.
Do not repeat B1/B2 readings, rerun the diagnostic, promote a model by the used sealed set, or restart B3.
A new own-branch Claim should own a **condition/guide/control-only** projection and exposure/feature-coverage
review of a suitable candidate. Responses and efficacy must stay out of eligibility choices. The
separate evaluator account/host is still unspecified; Andres was asked and has not named one. A clean
test needs that identity and demonstrated orchestration access denial, compatible cohort approval,
fixed preprocessing/controls/gene panel, baseline/model batch and shared-gene uncertainty before outcomes.
No cohort is currently ready for scoring and no superiority over CellForge is established.

**Paths and preservation:** all takeover clones/worktrees are under
`/Users/andresarriaga/.codex/.chatgpt-projects/g-p-6abd4598969c8191806ed119a5e711b5/`.
Own `gene-mila-export`/`gene-mila-shrinkage` runs have exclusive config/summary artifacts; never overwrite.
Live Mac notes: `~/Documents/Mila/Gene-Mila/genemila_scale_logs/STATE.md`. Numeric packages/public context
and prediction arrays stay out of Git. Continue from the lab branch's newest HANDOFF; source topic
branches remain available. Main checkout/data/historical runs/STOP/ledger/protected code remain unchanged.

**Scientific state:** B2 accepted arm r0/r2/r3: sealed Pearson delta 0.723882 ± 0.005414 sample SD;
primary gain over ridge-additive start +0.007758 ± 0.005414 across repeats, arm SE 0.005594, threshold
0.011780: no difference established. Watchdog-killed r1 remains separate. Delivered Norman model stays
B1's equal average of `runs/norman_ds_from_n2_w4_r1:EXP_0681`, `_r2:EXP_0729`, `_r3:EXP_0519`, selected
on visible validation (0.780139 versus B2 0.750482), saved sealed Pearson delta **0.722897**. B1's
constituent repeats are **0.718780 ± 0.007325 sample SD**. The ensemble's saved MSE is 0.005150,
expression PCC 0.989058, top-20 MSE 0.114444, top-20 R² 0.856186 and direction accuracy 0.904464.
Its top-20 MSE is worse than additive (0.109988). These ensemble points are not repeat means/SDs;
the report distinguishes metrics, paired SE and repeat SD. Current held-out scores are descriptive;
continuation planners had aggregate sealed feedback. Do not claim CellForge superiority: its published
row lacks Pearson delta, and a matched evaluator/model comparison has not been established.

**Andres's decisions and open gates (13 Oct):** The original request retained both bracketed spend
alternatives and requires asking before spending. He then requested understanding/careful improvements,
a test set inaccessible to orchestration, and "do the required changes in the github that you think
are necesessay, but document everything so the next agent can pick it up where you left when usage
runs out". This authorized the completed bounded GitHub work. He later offered a credential and said
"use the given key"; credential use is authorized, but no new paid experiment/budget was specified or
started. The value was not copied into tools, files, logs or GitHub; rotation was advised once. Any
future permitted run must use environment-only credentials and the shared ledger/caps. Do not treat
credential availability as a new research block or silently raise the cap. B3 remains dropped by the
11 Oct 22:50 amendment. Later explicit merge authorization is recorded above; protected-code and existing-data changes remain unauthorized.

**Untouched-test blockers and pending input:** no additional untouched real-data cohort was found
locally. Metadata-only research identified Replogle 2020 direct-capture exp8 (GSM4367986; single-target
activation/dosage) and Pacalin/Steinhart CRISPRai (GSE220974; singles and a very small activating-pair
subset). Both need compatibility, target/source-overlap and exposure audits; neither is yet a clean
Norman-equivalent test. No response data was downloaded. Andres was asked which separate machine or
OS account can hold labels and evaluate without orchestration access; no answer yet. The current
same-user oracle is not that boundary. Freeze and test the adapter, runtime, model receipt, complete
metric/baseline batch and uncertainty rule before any real evaluation. Investigate proposed remedies
only on development folds; do not tune exploration from the opened test's score.

The older narrative below is historical where this current state supersedes it. No paid call, real
lab run or new sealed query occurred in this takeover. Before the bounded merges recorded above, no branch had been merged. No protected code changed,
and the main checkout, STOP and all existing run/data files remain unchanged. Claims #8/#9/#11 are
implemented and await review; claims #14/#15/#16 now own the new work. Avoid duplicate implementations.

**Active agents**

| Agent | Since | Working on | Claim |
|---|---|---|---|
| Claude, "Autonomous research system" (lab-code owner) | 2026-10-03 | the paid block of `docs/PLAN_AFTER_N4.md` (repeats of N4, fresh Norman runs from the additive start, an Adamson re-split), on Andres's go of 11 Oct 19:10 to 19:17 | (predates claim issues) |
| Claude, "Repo description design" | 2026-10-04 | finished: PR #1 (README) merged 11 Oct as `ca35f88`; PR #5 (README Norman section with N4, B1 and B2) 12 Oct | |
| Astra (Codex), current takeover | 2026-10-13 | Claim24 negative transfer experiment complete/archived; B1 unchanged; no lab run active | [#8](https://github.com/andresloak100/Gene-Mila/issues/8), [#9](https://github.com/andresloak100/Gene-Mila/issues/9), [#11](https://github.com/andresloak100/Gene-Mila/issues/11) |
| Astra (ChatGPT), earlier campaigns | 2026-10-08 | not active now. Two DeepSeek continuation campaigns on Adamson (8 workers, 2 h each, about $21.50 together): sealed 0.599 to 0.602, +0.003 over the run they continued. Its branches `astra/deepseek-continuation-memory` (6a3e8a8e) and `astra/compact-master-selection` (74114d43, contains the first), both from lab commit 8261c57, are now on GitHub (remote heads verified 13 Oct: 6a3e8a8e and 74114d43); the old local-only note is superseded | none |

**On the Mac (23:50):** ledger $43.59 of the block's $48; nothing runs; the STOP file is in place. B2 is done and
read (docs/NORMAN_PLAN.md section 8; readings, the five runs' summaries and the logs in draft PR #7, md5s checked,
no key-shaped strings): seeds 2 (`runs/norman_ds_addstart_w4_r2`, $1.369) and 3 (`_r3`, $1.194) passed; the primary
reading (the arm over r0, r2, r3 against their start) is not established (G +0.0078, bar 0.0118, all runs positive);
B2's combined model scores 0.727 sealed, +0.014 ± 0.003 over the additive rule but worse on its top-20 DE genes; the
delivered Norman model stays B1's combined model (visible validation 0.7801 against 0.7505). B3 is dropped from the
block; the pin on ce1b530 can go (the main checkout may be pulled to the lab head; move aside, never delete, any
untracked file that blocks it). Next, free: whether ridge shrinkage is what costs the selected models the DE genes
(B2's r3, alpha 300,000, has the best pearson_delta and the worst DE scores). What follows is the state before B2's
end. B1 is finished and read (docs/NORMAN_PLAN.md section 8; the
readings and the three runs' summaries are in draft PR #6, waiting for Andres to merge): the agents' search adds
nothing to its start (arm G −0.0000, SE 0.0071), and the combined model of the three repeats scores 0.723 sealed,
+0.0041 ± 0.0011 over N2's selected model, not established over the additive rule; it is the delivered Norman model
unless B2's combined model scores higher on the visible validation perturbations. B2 (docs/PLAN_AFTER_N4.md; Andres
said "continue" at 20:56 UTC) runs on the pinned commit ce1b530 (recorded in
`genemila_scale_logs/block_after_n4_b2b3_commit.txt`; nobody pulls in the main checkout until B2 has ended). The free
control `runs/norman_control_addstart_w4_r0` and seed 0 `runs/norman_ds_addstart_w4_r0` ($1.293) passed. Seed 1
`runs/norman_ds_addstart_w4_r1` ($1.649) was killed by run_research.py's watchdog while finishing, after its full
search, and stopped the block. The plan's note of 22:50 UTC and its addendum of 23:00 write it up: r1 is its own
arm (its kill is recorded only in `genemila_scale_logs/norman_ds_addstart_w4_r1.log` and
`block_after_n4_stopped_r1.txt`, not in its run directory, so never pass r1 to `arm_reading.py`), and B2 continues
with seed 2 and then seed 3 in r1's place, run with `--no-watchdog` and a 90-minute backstop by
`docs/mac/block_after_n4/block_b2_resume.sh`. It was brought in without touching the checkout (`git fetch origin
claude/autonomous-research-system-3k435s`; `mkdir -p ../genemila_scale_logs/b2_resume`; `git show
FETCH_HEAD:docs/mac/block_after_n4/block_b2_run.sh > ../genemila_scale_logs/b2_resume/block_b2_run.sh`, the same for
`block_b2_resume.sh`; md5s abf9af19… and 79d80ef6…; the stop marker renamed `block_after_n4_stopped_r1.txt`) and
started at 22:52:00 UTC with the command in its header; seed 2 runs, seed 3 follows by itself, the end is expected
about 23:45 UTC. `--no-watchdog` is recorded only in the "command:" lines of `genemila_scale_logs/block_b2_resume.log`.
B3 is dropped from this block (plan note of 22:50). `progress.md` and `block_b2_resume.log` say where B2 is; a stop
writes `genemila_scale_logs/block_after_n4_stopped.txt` and ends the script. Every run's log in
`genemila_scale_logs/` ends with the rendered summary, which holds the finalists' sealed scores: read no B2 run's log
end and no `summary.md` before the readings; read the `.check.txt` files and `block_b2_resume.log` instead. Exact next steps
once seeds 2 and 3 have passed (all free, from the main checkout, with `.venv/bin/python`): `tools/sealed_reading.py
--runs runs/<run> --out docs/results/norman_b2_<r0|r2|r3|control>_sealed_reading.md` for the three arm runs and the
control, and `--out docs/results/norman_b2_r1_killed_sealed_reading.md` for r1 (a row of its own, never in the arm); for r0, r2 and r3 `tools/sealed_reading.py --versus --runs
runs/norman_ds_addstart_w4_r<S> runs/norman_control_addstart_w4_r0 --out docs/results/norman_b2_r<S>_versus_control.md`;
the primary reading `tools/arm_reading.py rule --readings docs/results/norman_b2_r0_sealed_reading.json
docs/results/norman_b2_r2_sealed_reading.json docs/results/norman_b2_r3_sealed_reading.json --against start --out
docs/results/norman_b2_arm_vs_start.md`, the same with `--against additive`, and `--against versus` over the three
versus JSON twins; the arm as first specified, `rule --readings` over r0 and r2 only `--against start --out
docs/results/norman_b2_arm_r0_r2_vs_start_reported.md`, reported and not read (addendum of 23:00); `tools/arm_reading.py combine --members runs/norman_ds_addstart_w4_r0
runs/norman_ds_addstart_w4_r2 runs/norman_ds_addstart_w4_r3 --reference R --out
docs/results/norman_b2_combined_vs_<name>.md` for R = `runs/norman_ds_addstart_w4_r0:start` (the start,
baseline_ridge_additive), `runs/norman_control_addstart_w4_r0`, `runs/norman_ds_addstart_w4_r0:additive`, and the B1
arm `runs/norman_ds_from_n2_w4_r1 runs/norman_ds_from_n2_w4_r2 runs/norman_ds_from_n2_w4_r3`; then the delivered
Norman model by the plan's rule (visible_validation in the combine JSONs, B2's against B1's); push the readings and
the runs' summaries like PR #6. Whether B3 (the Adamson re-split) runs later goes to Andres with B2's results; it
would need a cap above $48 and has no script yet, and it would run exactly as the plan's B3 says, on the pinned commit (bring later scripts in with
`git fetch` and `git show origin/claude/autonomous-research-system-3k435s:<path> > ../genemila_scale_logs/<file>`,
never by pulling). How to work on the Mac (paths, the
key, the STOP file, how results reach GitHub): `docs/mac/MAC_HANDOFF.md` and the running log `docs/mac/STATE.md` (in
PR #6 until it is merged). The lab now lives in `~/Documents/Mila/Gene-Mila/` (`gene-mila`,
`genemila_scale_logs`, `gene-mila-2492e11`, `data_downloads`); symlinks with those names stay in
`~/Documents/Loak-documents/` only because past runs record the old paths, so write nothing new there, and touch
nothing else in `~/Documents/Mila` (Andres's checkout of andresloak100/Mila). Two paid Norman runs today
(`docs/NORMAN_PLAN.md` section 8). N3 (`runs/norman_ds_replogle_w4_r0`, $1.03) selected its additive baseline: the
agents' best model scored 0.671 sealed against 0.713 for the additive rule, because no agent fed the plain
additive prediction to the model. N4 (`runs/norman_ds_from_n2_w4_r0`, $1.16, the same agents continuing the no-LLM
control N2) selected a ridge model of 11 features scoring **0.726** sealed pearson_delta, the best Norman number so
far, against 0.719 for its start and 0.713 for the additive rule; by the pre-set paired rule neither gain is
established (+0.008 ± 0.004 over the start, +0.014 ± 0.008 over the rule; `docs/results/norman_n4_sealed_reading.md`),
and on the most-changed genes it is worse than the rule (R²_DE 0.819 against 0.846). The Mac's reports are merged
(PR #3 and PR #4, under `docs/mac/` and `docs/results/`); Astra's two branches are on GitHub. N4's planner ran out
at 18.7 of its 20 minutes, when the ledger reached the $34 cap then in force (`summary.json`: `planner.mixed` true,
`exhausted_at_min` 18.7), so by the rules N4 is its own arm, "(lost its planner)", and is never pooled with its
repeats.

**Results on Adamson (CellForge's seed-42 split; read the files):** tables over 28 runs in
`docs/results/results_table.md` and `scaling.md`, the account in `docs/results/summary_for_collaborators.md`,
the full picture in `docs/LAB_STATE.md`. Sealed pearson_delta: start 0.520; no-LLM control 0.553; agent
arms 0.566 / 0.602 / 0.584 / 0.577 for 1 / 4 / 8 / 16 workers; best of any run without an external
screen under 0.604; noise ceiling 0.94 on the visible validation set. Every lever tested since 5 Oct
(more workers, longer runs, a DE-aware selection rule, a hand-written transfer feature, Astra's
continuation campaigns, a learned target similarity, refitting on all visible labels, feature pruning)
is closed: the limit is information about the targets, not search. The one lever with new information
is an external K562 screen, Replogle 2022 (Andres chose it on 11 Oct), read as knowledge in the bundle:
leave-one-out over the 50 training perturbations +0.072 ± 0.020 over gene-set kNN
(`docs/results/external_loo_replogle2022_k562*.md`); no-LLM runs with the screen score 0.621, 0.638 and
0.646 sealed (`control_replogle_w4_r0`, `control_replogle_from_opus_r0`, `control_replogle3_from_opus_r0`,
one run each, their files on the push list). The 0.646 is the fourth look at a sealed set already scored
for dozens of finalists across about 30 runs, so it is not established: Norman, or a fresh split, is the
clean test. Against CellForge's reported Adamson row nothing is comparable (their evaluation code is
unpublished, their split holds out guides rather than genes, their spreads exceed the differences), so
nothing is reported as "beats CellForge" (`docs/LAB_STATE.md`, "Against CellForge"). Two reported models
(in `scale_w8_r0` and `newcode_ds_w4_r0`) use an agent feature built on Python's salted `hash()`; the
guard now refuses it (`3d7c519`) and their table rows need a footnote at the next regeneration
(`docs/results/feature_audit_v3.md`).

**Norman 2019 (free steps done 11 Oct; `docs/NORMAN_PLAN.md` section 8,
`docs/results/norman_sealed_reading.md`):** bundle built (231 perturbations, gene-grouped split
`split_a391fa9e7b4eccb7`); the Replogle gate passes; the pre-specified leave-one-out shows the screen adds
information on Norman too (+0.023 ± 0.006); but on the sealed set the no-LLM control with the screen
scores 0.719 pearson_delta against 0.717 without it and 0.713 for the additive baseline: a null so far,
neither control beats the additive baseline beyond its error, and selection overfits the perturbations it
chooses on (+0.030 over the baseline on visible data). The two paid agent runs are above. Since `c6fadc0` a
fresh run on a bundle with pairs starts its agents from ridge on the additive rule (the built-in feature
`additive_response` and the baseline `baseline_ridge_additive`); no run has used it yet.

**DeepSeek ledger:** $33.97 after N4 (11 Oct 18:08; $31.78 before the Norman runs, N3 $1.03, N4 $1.16), $33.97
when B1's first repeat started. At 19:10 to 19:16 Andres put the rest of his balance at the lab-code owner's disposal
("you can spent as much as u want and you think is necessary we have in total 33 in deep seek"; "keep improving the
model spent those dolars well"); DeepSeek's console showed $33.01 left and $16.98 billed, so the ledger counts about
twice the bill (likely off-peak pricing; not checked call by call). The block in `docs/PLAN_AFTER_N4.md` lets the
ledger reach $48 and starts a run only when the ledger plus its own caps stays within it; spending beyond the block
is pre-specified in the repository first. `budget.max_total_usd` caps a run's workers only; the planner has its own cap
(`budget.max_planner_usd`, by default derived from `planner_usd_per_worker_hour`), so N4, given only
`max_total_usd=1.1`, cost $1.16. Every paid run sets both. Opus planner dollars are the Claude CLI's estimate of
subscription usage, not a bill.

**Claude usage:** one Claude Max window shared by the Mac's Claude Code session, the cloud Claude threads
and the Opus planner; nearly spent on 11 Oct. When it is out, Opus-planned runs wait; everything else uses
the DeepSeek planner (AGENTS.md, "Money and usage").

**The key:** Andres keeps it himself in `~/.zshenv` on the Mac as `API_KEY` (11 Oct 19:22); each run gets it as
`DEEPSEEK_API_KEY="$API_KEY" <command>`, in its own process environment only. He pasted keys in chat at 15:34 and
17:48; he asked that the 17:48 one be used ("use the same key", 19:17), and B1's first repeat ran on it. Nobody asks
him to paste a key anywhere.

**Code:** 419 tests pass at `c6fadc0` (the additive start model for pair bundles): Norman 2019 (gene-grouped
split, order-independent pair labels, additive baseline, CRISPRa-aware Replogle features, the `norman_v1`
leave-one-out, `tools/sealed_reading.py`), the external-screen arm (`run.external_knowledge` labels the
run; `tools/build_external_screen.py`, `tools/external_loo.py`), `tools/feature_audit.py`,
`tools/refit_visible.py`, `tools/noise_ceiling.py`, `tools/time_to_best.py`, `tools/compact_model_curve.py`,
reproducible feature runs (`PYTHONHASHSEED=0` in every experiment process; the guard refuses `hash()` and
`id()` in new agent plugins), `pytest.ini`, and the Mac paths above. The repository is public since
11 Oct: nothing secret goes into any branch, and every push from the Mac is scanned for key-shaped strings
first.

**Pull requests:** Andres chose "Merge both" on the build thread's card (11 Oct 15:52): PR #2 (this file,
AGENTS.md, CLAUDE.md) merged as `4356ca2`, PR #1 (README and its checker) as `ca35f88`. The Mac's reports went in
as PR #3 and PR #4 (N4), md5-verified and scanned for keys first. None is open.

**Next:** the block in `docs/PLAN_AFTER_N4.md`, in its order (B1: done; B2: a free control, then
three fresh Norman runs from the additive start, seeds 0, 2 and 3 after seed 1's stop; B3, the Adamson re-split, dropped
from this block), each read
by the rules fixed there, with `tools/sealed_reading.py` and `tools/arm_reading.py`; results go to Andres before
anything more is spent. After it: (1) free: measure the new additive start model on Norman with a no-LLM run on the
Mac (B2's control does this); (2) free: check whether
the heavy ridge penalty is why the selected Norman models lose to the additive rule on the most-changed genes, and if
so pre-specify a fix before any run; (3) better outside data for Norman: Replogle is a knockdown screen and Norman is
activation, so look for a public CRISPRa screen in K562, asking Andres before any download; (4) Srivatsan sci-Plex 3,
which needs drug and dose ingestion and Andres's design decision first; (5) the compact-model rules (Andres's ask,
11 Oct 00:32; `docs/LAB_STATE.md`, "In progress", item 2). An arriving
agent that is not the lab-code owner may take free code work on (2), (4) or (5), claimed with an issue. The
timeline given on 5 Oct (three datasets by 10 to 12 Oct) has slipped: Norman started on 11 Oct, Srivatsan has not.

**Decisions to respect.** Andres's own: the rest of his DeepSeek balance, spent as the lab-code owner judges
necessary (11 Oct 19:10 to 19:16), the key in `~/.zshenv` as `API_KEY` (19:22); before that the $34 cap (11 Oct
02:39); Replogle 2022 as the external screen (11 Oct); the compact-model rules (11 Oct 00:32); Norman to
Claude, "Claude now" (11 Oct 12:02) and "download norman" (12:04); the paid run goes to Norman, not
Adamson (started on his words, 15:34); N4, "start the paid run" (17:47); the lab lives in `~/Documents/Mila/Gene-Mila` and everything goes
up to GitHub (15:34 to 15:41); earlier: $10 for the comparison (4 Oct 00:04), "go, $15 cap" (4 Oct 19:16),
"Fix, then 1 run" (4 Oct 23:21); CellForge's published rows marked not comparable; no 44-worker run.
Claude's, under his delegation: the default selection rule stays; one full paid Norman run rather than two
short ones; the lab-code owner maintains the protected benchmark, split and guard code.

**Only Andres can (the blockers for any other agent):**
- Rotate the DeepSeek key when he chooses (two were pasted in chat on 11 Oct; he asked that the second be used).
- Create a `main` branch, if he wants one (PRs #1 to #4 are merged).
- Give outside agents write access to the repository (Astra's branches go up through the Mac session's
  `gh` login, which is his).
- Keep the Mac on mains power and awake while anything runs.
- Answer the comment in the summary doc.

Sections 7 to 9 below were written on 4 Oct while the comparison was still running; `docs/LAB_STATE.md`
and the files under `docs/results/` on the integration branch supersede their numbers and their plan.

**Live sources** (check them; they beat this section when they disagree):

| Question | Live source |
|---|---|
| The whole state in one file | `docs/LAB_STATE.md` on the integration branch (the lab-code owner updates it at every milestone; newest state wins) |
| Everything below in one command | `python handoff_state.py --runs ~/Documents/Mila/Gene-Mila/gene-mila/runs` from any clone at the integration branch head (read-only; since `28a8a37` it finds `genemila_scale_logs` beside the checkout or under `~/Documents/Mila/Gene-Mila`, else pass `--logs DIR`; `--fetch` compares against the remote first, `--json` for machines; `--ledger FILE` if the shared ledger is elsewhere). Prints how far your clone is ahead of or behind the integration branch; every run directory with arm, workers, seed, code and state (finished; in progress with minutes to its deadline; killed before its summary; excluded `_contaminated` / `_interrupted`; planner changed or lost) and headline numbers; ledger totals per provider and role; a WARNING listing paid runs whose `budget.ledger` is not the shared ledger (their spend does not count toward the cap); live `run_research.py` processes; the STOP file; the head of `STATE.md` and the tail of `progress.md` |
| What is running on the Mac, and what comes next there? | `~/Documents/Mila/Gene-Mila/genemila_scale_logs/STATE.md` (what is running, every run directory and its status, open decisions, exact next commands; written on the Mac by whoever runs there), `tail -n 30 .../progress.md` (the driver's step log), `pgrep -fl run_research.py` |
| How much DeepSeek money is spent? | `sqlite3 ~/Documents/Mila/Gene-Mila/gene-mila/runs/spend_ledger.sqlite "SELECT provider, ROUND(SUM(cost_usd),2) FROM spend GROUP BY provider"` |
| What did a run find? | `runs/<run>/summary.md` and `summary.json` (`best`, `generalization_query_only`, `llm_usage`, `completed_by_proposer`, `split_id`) |
| Who holds which task? | open issues titled `Claim:`, open pull requests |
| What changed in the code? | `git log origin/claude/autonomous-research-system-3k435s` |

## 2. Where things are

| What | Where |
|---|---|
| Repository (public since 2026-10-11, so nothing secret in any branch) | `https://github.com/andresloak100/gene-mila` |
| Integration branch (pull requests go here; there is no `main` yet) | `claude/autonomous-research-system-3k435s` |
| Main checkout on Andres's Mac: real data, runs (the key is stored nowhere on the Mac). **Don't touch its files or git state** | `~/Documents/Mila/Gene-Mila/gene-mila` (moved there from `~/Documents/Loak-documents/gene-mila` on 2026-10-11 after the paid Norman run; a shortcut stays at the old name) |
| Its Python environment | `~/Documents/Mila/Gene-Mila/gene-mila/.venv` |
| Data bundle in use (gitignored) | `data/adamson_cf/` in the main checkout |
| Runs (gitignored) | `runs/<run>/` in the main checkout |
| Shared spend ledger, cumulative across all runs | `runs/spend_ledger.sqlite` in the main checkout |
| Comparison driver: state, progress, stop switch | `~/Documents/Mila/Gene-Mila/genemila_scale_logs/` (`STATE.md`, `progress.md`; a file named `STOP` halts the driver after its current step; the driver script is `tools/scale_seq.sh` on the lab branch, no key inside) |
| Raw data | scPerturb archive on Zenodo, record 13350497: `https://zenodo.org/records/13350497/files/<file>?download=1` |
| CellForge | paper arXiv 2508.02276; code `https://github.com/gersteinlab/CellForge` (it has no evaluation code; we rebuilt the metrics from the paper) |
| Evaluation package | `https://github.com/ArcInstitute/cell-eval` |

The Claude session on the Mac is refused git pushes by its own permission system; `gh` there is
signed in as `andresloak100` with repo scope, so another agent working on the Mac should try to push.
Until someone there can, results reach the repository when an agent with push access commits the
files the Mac produced, exactly as they are on disk.

## 3. The data

`data/adamson_cf` is Adamson et al. 2016 Perturb-seq (CRISPRi in K562 cells), file
`AdamsonWeissman2016_GSM2406681_10X010.h5ad` (the unfolded-protein-response screen):
counts per 10k plus log1p, 2,055 genes (highly variable genes plus every target gene),
88 knockdowns, 3 non-targeting control guides pooled as control, and CellForge's split with
seed 42: 50 training perturbations, 17 visible validation (`val1`) and 21 query-only (`val2`,
CellForge's test perturbations). It also carries prior-knowledge files (gene sets, TF targets,
protein interactions).

Bundle layout: `manifest.json` (source, split id, file hashes; the lab verifies them at the start
of every run), `public.npz` (all that feature code may see), `private/val1.npz` (evaluator only),
`private/val2.npz` (query-only oracle only), `splits.json` (protected). Never read the last three.

Norman 2019 (`NormanWeissman2019_filtered.h5ad`, single and double CRISPRa perturbations) was built
into its own bundle on the Mac on 2026-10-11 (`docs/NORMAN_PLAN.md` section 8: gene-grouped split, 231
perturbations, pair labels, an additive baseline). Not yet loaded: `SrivatsanTrapnell2020_sciplex3.h5ad`
(drugs; needs drug metadata the lab doesn't model yet).
CellForge's paper states no exact split; it holds out whole perturbations. Its split code (one 20%
hold-out, fixed seed) disagrees with its documentation (five folds), so whatever you do for a new
dataset, record every assumption next to the bundle.

## 4. Set up your own clone

On the Mac, with your own GitHub access:

```bash
cd ~/Documents/Mila/Gene-Mila
git clone https://github.com/andresloak100/gene-mila.git gene-mila-<your-name>
cd gene-mila-<your-name>
git checkout -b <your-name>/<topic> origin/claude/autonomous-research-system-3k435s
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
# data: either point every run at the main checkout's bundle, read-only (runs write only into their
# own run directory):   --set run.data_dir=$HOME/Documents/Mila/Gene-Mila/gene-mila/data/adamson_cf
# or copy it once:
mkdir -p data && cp -R ../gene-mila/data/adamson_cf data/     # a copy; never modify the original
export LEDGER="$HOME/Documents/Mila/Gene-Mila/gene-mila/runs/spend_ledger.sqlite"
nice -n 19 python -m pytest -q
```

Your runs then land in your clone's `runs/`, away from the comparison; `run.data_dir` (since `1479ae9`)
is resolved to an absolute path, so the main checkout's bundle can be used in place. Off the Mac you
can do all code work; real runs need the bundle copied over (it contains private labels, so treat the
copy like the original) and network access to `api.deepseek.com`.

## 5. Run the lab

Every script defaults to the newest run under `runs/`; pass `--run runs/<run>` to choose one.

```bash
# free: scripted planner, mock workers (no LLM, no money); only when the Mac's driver is idle
python run_research.py --dataset adamson_cf --minutes 5 --workers 2 \
  --planner-provider scripted --worker-provider mock --run-dir runs/<your-name>_smoke \
  --set run.data_dir=$HOME/Documents/Mila/Gene-Mila/gene-mila/data/adamson_cf   # or omit, with data/ copied

# paid: DeepSeek plans and implements; only with Andres's approval and amount, never next to another paid run
# (a Claude-planned run, Claude sessions only while usage allows, uses --planner-provider claude_cli
#  --planner-model opus --set planner.fallback=deepseek:deepseek-v4-pro instead of the two planner flags below)
python run_research.py --dataset adamson_cf --minutes 20 --workers 4 --set run.seed=0 \
  --planner-provider deepseek --planner-model deepseek-v4-pro \
  --set budget.ledger="$LEDGER" --set budget.cumulative_usd.deepseek=34 \
  --set budget.max_total_usd=<worker cap> --set budget.max_planner_usd=<planner cap> \
  --run-dir runs/<your-name>_<topic>_r0

# warm start from an earlier run on the same split
python run_research.py ... --continue-from runs/<earlier run>

python handoff_state.py               # the whole checkout: git, runs, ledger, processes, progress.md
python status.py --watch 5            # live state of a run
python leaderboard.py                 # ranked experiments (--all includes failures)
python summarize.py                   # regenerate summary.md / summary.json (keeps stored sealed scores)
python analyze_run.py                 # utilisation, tokens, cost, bottlenecks (writes analysis.json)
python reproduce.py --experiment EXP_0012
python results_table.py build --runs <run dirs> --dataset-key adamson   # CellForge Table 1 layout, into docs/results/
python results_table.py calibrate --data data/adamson_cf --dataset-key adamson
python scaling_report.py --runs <run dirs>                              # mean ± sd per arm and worker count
```

Measured costs: a 20-minute, 4-worker run spends about $0.20 to $0.50 on DeepSeek workers; a
DeepSeek V4 Pro planner adds about $0.50. List run directories explicitly in the report commands,
and leave out anything ending in `_contaminated` or `_interrupted`.

## 6. Handing over

Starting a session (any agent):
1. `git fetch` and read section 1 of this file on the integration branch, the open `Claim:`
   issues and pull requests, and `progress.md` on the Mac.
2. Pick the next unclaimed task (section 8) or continue a stalled one: comment on its claim issue
   that you are taking it over, and branch from its pull request's head into a branch of your own.
3. Add yourself to "Active agents" in section 1 and push that change.

Stopping, or expecting to run out of tokens soon:
1. Push your branch, even if the work is half done, and say in the pull request description what
   works, what doesn't, and the exact next command.
2. Update section 1: move yourself out of "Active agents" (or mark "stopped at <time>"), update
   "In flight" and "Next", and push.
3. Leave nothing running that nobody owns. A run you started either finishes on its own with
   its `summary.json`, or section 1 says where it is and when it ends.

## 7. Results so far (Adamson, CellForge's split)

Primary metric `pearson_delta`: per held-out perturbation, the Pearson correlation of predicted and
true expression change across genes, averaged. "Visible" is what the agents select on; "held-out"
is the sealed query-only set, CellForge's test perturbations.

Starting model (OLS on three baseline features): 0.556 visible, 0.520 held-out.
Free no-LLM control on the old code: 0.571 / 0.554, identical over six seeds and finished after
about two minutes, so it is a fixed recipe and gives no noise estimate. On the current code
(`runs/newcode_control_r0` to `r5`, 2026-10-04) it scores 0.510 visible / 0.553 held-out, identical
over six runs, 23 experiments per run, still ending after about two minutes and keeping no ensemble.
Visible scores are not comparable across code versions: selection now averages 67 perturbations (the
visible set plus out-of-fold training perturbations) instead of 17, which is why the tables separate
code versions into arms. `schedule.exploit_depth` (`9044ece`)
added deeper deterministic search tiers, but the rerun `runs/newcode2_control_r0` still exhausted its
search in under three minutes (126 experiments, held-out 0.553, no better model), so the other five
reruns were skipped: the control is a fixed-recipe reference arm, and filling 20 minutes needs a source
of new features that only the agents provide.

Worker-scaling comparison, code `2492e11`, Opus planner, DeepSeek workers, 20 minutes each:

| workers | seed | completed experiments | best visible | best held-out | experiments / hour | DeepSeek $ |
|---|---|---|---|---|---|---|
| 1 | 0 | 82 | 0.627 | 0.544 | 261 | 0.19 |
| 1 | 1 | 93 | 0.619 | 0.589 | 291 | 0.17 |
| 4 | 0 | 159 | 0.629 | 0.601 | 486 | 0.46 |
| 4 | 1 | 112 | 0.609 | 0.604 | see note | 0.22 |
| 8 | 0 | 280 | 0.637 | 0.585 | 855 | 0.71 |
| 8 | 1 | 275 | 0.651 | 0.583 | 804 | 0.82 |
| 16 | 0 | 657 | 0.648 | 0.562 | 1,936 | 1.20 |

Note: the 4-worker seed-1 run was killed at its deadline and its summary rebuilt afterwards; its
stored duration was an artefact (fixed in `2370276`), so read its throughput against 20 minutes.

The honest reading: throughput and the visible score rise with workers, the held-out score does
not. Sixteen workers chose among 657 experiments using 17 visible perturbations and ended with
the best visible and nearly the worst held-out score, which is selection overfitting. The two
1-worker runs differ by 0.045 held-out, as much as the spread across worker counts, so no
ordering is established. The current code selects on 67 perturbations (the visible set plus
5-fold out-of-fold predictions on the training set) to address exactly this; the new-code runs
above are its first test.

Against the simple baselines refitted on CellForge's split, every agent run wins on the top-20 DE
genes: held-out MSE 0.11 to 0.12 against 0.16 for linear regression, R² 0.80 to 0.82 against 0.71.
All-gene PCC is about 0.985 to 0.989 for every model, plain OLS included, so it separates nothing.
CellForge's published Adamson numbers cannot be reproduced under any metric definition tried
(their Unperturbed row reports PCC 0.0001; that baseline scores 0.98 on this data), so their rows
are marked not comparable.

Excluded from every table: `runs/scale_w8_r0_contaminated` (its planner fell back to the scripted
one mid-run), `runs/scale_w1_r1_interrupted`, and the first Adamson run (most experiments failed on
a since-fixed output limit).

## 8. Open work, in Andres's priority order

1. **Raise our model's held-out scores on CellForge's Adamson split.** The top priority. Once the
   planner check shows whether DeepSeek V4 Pro can plan as well as Opus, a campaign of longer
   runs warm-started from the best run (`--continue-from`) with the DeepSeek planner can carry it
   without the Claude subscription. Paid: needs Andres's approval and amount, and the Mac's driver
   must be idle. Unassigned.
2. **Finish the 1/4/8/16-worker comparison with repeats.** The Claude "Autonomous research system"
   session and the Mac's driver (section 1). Don't duplicate it.
3. **Final tables and scaling report, committed to `docs/results/`.** Same owner. If that session
   has gone quiet and Andres asks you to, run the commands of section 5 over the full run list and
   commit the files exactly as produced.
4. **Norman.** Ingest `NormanWeissman2019_filtered.h5ad` with `prepare_data.py h5ad` into a new
   bundle following CellForge's split code, record every assumption, run the free control on it,
   and only then propose paid runs. Free to start and collides with nothing: a good first task.
   Unassigned.
5. **Srivatsan (sci-Plex 3).** Drug perturbations need drug metadata, a new kind of feature input.
   A design question for Andres before any code. Unassigned.
6. **Smaller items** (from `docs/ARCHITECTURE.md`): one factorisation shared by every ridge alpha,
   screening new features on a subset of genes, skipping features numerically identical to existing
   ones. Lab code: claim it first, because the integration branch's owner may be changing the same
   files. Known limits, not bugs: the guard is not an operating-system sandbox, and the lab predicts
   per-perturbation means, so cell-eval's distribution metrics would need cell-level output (a
   design call for Andres).

## 9. Taking over the comparison (only if Andres asks)

The comparison must keep its arms comparable. If Andres hands it to you because no Claude session
is available, keep these settings and check `progress.md` first so nothing runs twice:

- dataset `adamson_cf`, 20 minutes, the shared ledger, one paid run at a time, and the driver
  stopped (`pgrep -fl run_research.py` shows nothing) before you start;
- run from your own clone checked out at the arm's code version, with
  `--run-dir ~/Documents/Mila/Gene-Mila/gene-mila/runs/<run name>` so the comparison's runs stay
  together; the main checkout's files and git state stay untouched;
- the seed-1 repeats `scale_w8_r1` and `scale_w16_r1` run on code `2492e11` with the Opus planner,
  `--set run.seed=1`, worker caps $2 and $3 and `budget.cumulative_usd.deepseek=10`. They need the
  Claude CLI, so they wait while Andres's Claude usage is exhausted; that code has no failover, so
  one whose planner falls back to the scripted planner is renamed `_contaminated`;
- the planner check on the current code, 4 workers, seeds 0 and 1: `newcode_ds_w4_r*` with
  `--planner-provider deepseek --planner-model deepseek-v4-pro --set budget.max_total_usd=2.5`, and
  `newcode_opus_w4_r*` with `--set budget.max_total_usd=1.5 --set planner.fallback=deepseek:deepseek-v4-pro`,
  both with `budget.cumulative_usd.deepseek=15`; `python analyze_run.py --run <dir>` after each;
- then `scaling_report.py` and `results_table.py` over every `scale_*` and `newcode_*` directory
  except `_contaminated` and `_interrupted`;
- the driver script is `tools/scale_seq.sh` (`014daeb`, committed verbatim from the Mac's
  `genemila_scale_logs/scale_seq.sh`; no key inside: `DEEPSEEK_API_KEY` must be in the starting process's
  environment or it halts; DeepSeek-only ledger gate at $14; a Claude CLI probe before each Opus-planned
  run, with the DeepSeek-planned runs first when the window is out; a contamination check that renames
  an old-code run whose planner fell back). Start it detached,
  `nohup setsid caffeinate -i -s bash scale_seq.sh > ~/Documents/Mila/Gene-Mila/genemila_scale_logs/driver.log 2>&1 &`,
  with the key as a process variable; it appends to `progress.md`, waits for any other lab run on the
  machine to finish before each start, and stops when a `STOP` file appears. Update `STATE.md` before
  and after.
