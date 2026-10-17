# Handoff: the state of the lab and the open work

Read [`AGENTS.md`](AGENTS.md) first; its rules apply to everything here.

## 1. Current state (whoever is working keeps this true)

**Lead (Claude, #41), 2026-10-17 15:30 UTC: block G's Adamson half is negative; Norman's test running; a brief for new
agents.** Adamson: none of 221 table-reading features passes the corrected fair test; the arm with the tables scored
lower out of fold than the arm without (`docs/GOAL_CRITERIA.md` Status, ROADMAP note of 15:30 UTC). Still not yet on
either path. Norman's family-wise test (174 rows, 999 replicates) is running at `nice 19`; then the block F re-read and
the family 8 scoring (Astra, #51). Block G cost $12.97 on the ledger (final $60.23). The merged branches were deleted by
Andres; `docs/BRIEF_FOR_NEW_AGENTS.md` is the plain-language brief Andres hands to a new agent. **Next:** the Norman
reading, then the lead's decision on the biology path (ROADMAP D10) and block H's free preparation (#51).

**Lead (Claude, #41), 2026-10-17 05:30 UTC: curation and block H tooling landed; block G running.** The repository was
curated ([PR #58](https://github.com/andresloak100/Gene-Mila/pull/58)): nine old draft PRs' records merged, superseded
documents under `docs/archive/`, `docs/README.md` is the documentation map, `docs/results/README.md`,
`docs/mac/README.md` and `tools/README.md` index the records and tools; `docs/mac/STATE.md` is archived (section 1 here
is the live mirror). Block H's tooling is complete ([PR #59](https://github.com/andresloak100/Gene-Mila/pull/59)): the
autoresearch-style arm runs through the Codex CLI the Mac has, the ledger proxy serves the Responses API; the lead's
family 8 hypothesis plugin is in `docs/comparison/lead_h8_constraint/` (PR #57). Block G: 6 of 12 runs passed by 04:50
UTC (all Adamson; Norman running), ledger $53.61 against the $67.26 cap. **Next:** Astra finishes the chain, then the G
readings, the block F re-read and the family 8 scoring with the tool at `1a95873` or later, then the block H free
preparation (#51, lead's note of 05:20 UTC); the lead reads G against `docs/GOAL_CRITERIA.md`. Still open for Andres:
the fresh-test holder and the isolation route (ROADMAP section 7, items 2 and 3).

**Andres's current handoff — Astra, 2026-10-17 15:35 UTC; claim and reporting issue #51.**
The direct instruction is recorded in [comment6228976763](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6228976763).
It replaces the old #41 destination and F-first order. Existing G progress was backfilled on #51; subsequent
posted lines are recorded in append-only `genemila_scale_logs/block_g_posted_progress_51.txt`. The old #41 receipt
is history and must not suppress #51 posts.

**G status: COMPLETE.** All 12 runs passed; the chain explicitly finished at
2026-10-17T07:05:40Z. No lab/chain/scale driver/test/build job was active at the 07:10 UTC
completion check; STOP is present. Final ledger 60.232225 from original 47.264645,
block spend 12.967580 ledger dollars, below the unchanged 67.26 cap. The final progress line
was posted on [#51/comment6231063486](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6231063486)
and appended to the issue-51 receipt. Never restart G, recopy scripts, reset the cap or redo preparation.
Research pin baa7dfd, main checkout, data, scripts and ledger are unchanged. Adamson prescribed readings complete; Norman active.

**Reading phase: Adamson G readings 1–4 COMPLETE; Norman G reading 1 COMPLETE; Norman reading 2 RUNNING once.**
Own results clone `gene-mila-g-f-h8-readings`, branch `astra/g-f-h8-readings`, remains frozen at
`2f2e6838316915198c52abeb34cf02f2b3aacc87`; scientific reader behavior unchanged from 1a95873.
Adamson stage1/select/stage2/pool/one six-run OOF call/all six separate sealed calls exited 0.
Primary: 221 tested, 210 unique after 11 cross-source duplicates, 999 replicates, complete family,
found=[]/tier1=[]. Original 276 plugins/32 stage1 duplicates/23 exclusions remain preserved.
Independent full-family/hash/null/gate audit PASSED. Raw pool retains its legacy Block F heading.
OOF M1 over independent r0/r2/r3: G0 0.525950139 ± sampleSD 0.035263074; G1 0.490964428 ± 0.004435578.
Adamson sealed readings are worn/indicative; each selected model was read only against its own start.
The static audit distinguishes text mentions from direct table calls (g1r2 GA raw2/direct1);
all planner maxima <20000, DeepSeek mixed=False, external knowledge empty. Total experiments are
NOT emitted by permitted .check receipts and reported missing, never inferred from EXP IDs.
All JSON/Markdown twins, source/key/column evidence, unchanged plugins, hashes and commands/logs/exits
are retained. Complete Adamson results/limitations posted
[#51/comment6233130270](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6233130270).

**Norman G primary COMPLETE, stage2 and corrected pool explicit exit 0 by 2026-10-17 15:31 UTC.**
Stage1: 276 rows = 223 primary + 47 descriptive selected-model add-one + 6 sets.
Eligible 174 (44 r0 / 62 r2 / 68 r3), 40 within-source duplicates (5/22/13), 9 exclusions
(6 dependency KeyErrors, 1 constant smoke, 2 literal caps); no repair/substitution/retry.
All 174 status-ok members selected exactly once; k=null, m_total=174, null_reps=999.
Selection SHA256 `207753289a71171edd801b1c4475cf073acaeb6058527f04fe9804ed7c94f4f4`.
Stage2 is finished, not to restart: 177 rows = 174 ok add-one + 3 sets, 999 replicates.
Corrected pool: 174 tested, 16 cross-source duplicates, 158 unique; partial=false, untested=[],
null_too_coarse_need=null, found=[]/tier1=[]. No row passes the fixed complete-family criteria.
Outputs norman_g_stage1/top/stage2/pooled_holm and unchanged norman_g_plugins/input manifest
plus commands/logs/exits are retained. Both applicable nulls, coefficient signs and all gates remain fixed.
Independent source/selection and post-score full-family/null/gate audits PASSED. All raw/pooled p values
were reconstructed from stored gains; coefficient signs and all fixed gates match. 59 proportional rows,
56 with valid perturbation nulls; 3 full-view-only proportional rows correctly fail and remain excluded.
Raw pool retains legacy Block F/gene_annotation heading; scope here is Norman G/all three tables.

**Current detached screen 69356.gm-g-norman-arm; actual Python PID 69359, nice 19.**
Norman reading2 launched ONCE 2026-10-17T15:33:24.652297Z: exact six-run descriptive OOF call,
null-reps 0, credentials unset, caffeinate active, no --with-val1. Output docs/results/norman_g1_vs_g0,
adjacent exclusive .command.txt/.log/.exit; input manifest records 1,757 source DB/config/summary/plugin
file hashes before scores, SHA256 `1382f71acae94eefdb1f74b7f1df1f588bbea0e4de5a48fe8adc30189545946d`.
Source runs M/runs/norman_g1_ds_w4_r0,r2,r3 and M/runs/norman_g0_ds_w4_r0,r2,r3.
Primary completion and reading2 launch posted [#51/comment6235837421](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6235837421).
**Exact next:** monitor EXISTING reading2 at five-minute cadence. No duplicate/restart/source update,
branch pull-switch or competing heavy job. After explicit exit 0, report set-row emitted M1–M7/M12,
arm mean and sample SD over independent r0/r2/r3; no within-noise/fresh-test/CellForge victory claim.
Then six prescribed separate per-run sealed reading3 calls, g0 r0/r2/r3 then g1 r0/r2/r3, each exit0
before next, only each selected model vs its own start. Norman fifth/worn reading, n<10 reported only.
Then source/count/planner audit4 (counts missing from .check reported missing, never inferred),
corrected F stage2, lead H8 both after pre-score clarification, consolidated draft PR/results #51,
then Adamson export. Do not rerun Adamson or Norman primary. No Norman arm/sealed verdict, F/H8/export yet.
Actual scientific refusal/nonzero/dead-without-status: preserve/secret-scan/report/update/PAUSE;
no retry/workaround/tool change. Exit-0 candidate errors remain exclusions. Heartbeat ACTIVE.
No new paid run or next-block decision; Claude reads all results and decides next block.
**After all12 pass, clean chain finish and no other lab/driver/heavy job, follow this exact order:**
1. G readings1–4 for Adamson and Norman per PLAN_G, tool1a95873 or later. Use the corrected full status-ok family,
   999 null replicates, no --k or --with-val1; preserve every JSON/Markdown twin, plugin hash and command receipt.
2. Corrected F stage2 over every original status-ok row (66), 999 replicates, then pool into new output paths.
3. Lead H8 README's pre-run and scoring commands on BOTH datasets; label the lead's hypothesis, never agent A.1.
4. Post all results on #51 with run directories and arm mean±sampleSD; open one consolidated draft PR with files,
   proposed own branch `astra/g-f-h8-readings`, tool commit pinned before scoring. Do not merge.
5. Then export Adamson task package from `data/adamson_cf_clean_tables` with the existing export tool and post the
   MANIFEST.json/program.md SHA256 lines. Check both output and sibling export-record paths absent; no raw package,
   harness or data in Git and no manual private/split/label reads. Export-only does not start H or an agent.

A source-only H8 parent-name question is recorded in [comment6229018744](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6229018744):
Adamson's parent omits additive_response, so a proportional row may name mean_response; README names additive_response.
Claude was asked to clarify before H8. No formula, parent or acceptance rule will be changed silently; G/F proceed first.

**No paid run beyond G. Claude reads the results and decides the next block.** While G runs, only safe monitoring,
posting and state work: no evaluation/H8 pre-run/export/heavy jobs. Stop/report/pause on actual command/check failures;
no retries, criteria/source/data/script/cap changes, summaries/log endings/seals or handoff_state before prescribed reads.
The heartbeat is active with this new order. Older checkpoints below are history.

**G milestone — Astra, 2026-10-17 03:01 UTC, claim #51: 1/12 passed; Adamson table arm seed0 active.**
`adamson_cf_g0_ds_w4_r0` finished02:59UTC rc0, ledger47.712116, runcost.447471; .passed/check good,
DeepSeek planner mixedFalse, externalknowledge empty. **Current `adamson_cf_g1_ds_w4_r0` started02:59UTC,
actualPython83910**, screen67366.blockg/chain67368 alive. Both source run dirs under `gene-mila/runs/`.
Both new verbatim progress lines posted[#41/comment6228801516](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6228801516),
then appended to `genemila_scale_logs/block_g_posted_progress.txt`; no duplicate post. No stopped marker.
Cap67.26/originalrecord and researchpinbaa7dfd/scripts/data unchanged. No sealed reading/model comparison.
**Exact next:** safe5min process/progress/chain/.check/.passed monitoring; post each new line+appendreceipt;
next expected g1r0finish then g0r2. Current90minbackstop04:29UTC if same run stillalive; planstop/report rules apply.
Do not touch main/source/scripts/cap, run heavyjobs/F, readsummary.md/runlogend/seals or handoff_state.
Afterall12passed/cleanend/nojob: correctedF1a95873 all66rows999reps/nice19/newoutputs. Older checkpoints historical.

**Block G RUNNING — Astra, 2026-10-17 02:38 UTC, sole operator, claim #51.**
Exact chain launch02:38:01UTC succeeded; detachedscreen **67366.blockg**, chainbash67368, actualPython **67404**.
Current run **`adamson_cf_g0_ds_w4_r0`**, dir `~/Documents/Mila/Gene-Mila/gene-mila/runs/adamson_cf_g0_ds_w4_r0`,
first of12 sequential runs (Adamson g0/g1r0,r2,r3,thenNorman). PlannedDeepSeekv4pro planner/flash4workers/20min.
Merged rebuild source a77e0ff; unchanged preparation EXIT0/all4bundles and all prescribed checks; independent
public-only MD5/manifest/sharedbytes/source audit PASSED. Record commitfee11dd, [draft PR56](https://github.com/andresloak100/Gene-Mila/pull/56),
full output41/comment6228590413. Own `gene-mila-g-prep-a77e0ff` / `astra/block-g-preparation` holds docs only afterbuild.
First unused outputs/log preserved `.stale-20261017T023543Z`, sameinode receipts committed; original bundles untouched.
**Cap immutable:** `67.26 47.264645 2026-10-17T01:52Z`; researchWT **baa7dfd** clean; copied scripts byte-identical.
Startup log says all checks passed; no competinglab/driver/Freader/heavyjob. STOP lifted/restored by unchangedchain.
First02:38UTC started line POSTED on41; append-only receipt `genemila_scale_logs/block_g_posted_progress.txt`.
**Exact next:** monitor ONLY progress.md,block_g_chain.log,.check.txt/.passed and actual process health; post each
newG start/finish line41 then append receipt; don't duplicate posts. Do not rerun/archive/rebuild or copy scripts again.
No summary.md/individualrunlog ending/sealedscore/handoff_state while Gactive. No source/script/data/cap changes,
no F evaluation or otherheavyjob.90min manual backstop/stop rules perPLAN_G; any actualrefusal/failingcheck/death
report permitted evidence41/Andres/update state/pauseheartbeat; no automaticretry/workaround/budgetraise.
After12passed+cleanchainend+noactive lab/driver, run correctedF in fixed `gene-mila-f-corrected` at1a95873:
all66statusokrows,select without --k,newpaths,one999repstage2 nice19/detached/keysunset,thenpool/publish.
Existingheartbeat remains ACTIVE5min, quietunchanged; no H/R/newpaidarm/modelpromotion. Older checkpoints historical.

**Merged-source G rebuild ACTIVE — Astra, 2026-10-17 02:35 UTC, claim #51.**
Claude merged orderingPR55 at02:31:40UTC, **a77e0ff2d79dc27924eeab08cfad390c076cc1d3**. Own clean rebuild
checkout `gene-mila-g-prep-a77e0ff`, branch `astra/block-g-preparation`, exact merge; code matches testedb8d80fe.
Independent source/pin/script audit approved. Original research checkout stays clean atbaa7dfd.
Our unused first-attempt Norman bundles, both table directories and prepare log were RENAMED unchanged with
suffix `.stale-20261017T023543Z`; same device+inode verified, no child/private/split reads, no deletions/overwrites.
Archive receipt `genemila_scale_logs/block_g_prepare_archive_20261017T023543Z.jsonl`; cap untouched
`67.26 47.264645 2026-10-17T01:52Z`. Original source bundles not moved/edited. No paid G or F fit.
Unchanged preparation NOW active once from exact merge/keysunset, managedsession19476; new exclusive
`genemila_scale_logs/block_g_prepare.log`. DO NOT archive/recreate/reinvoke while this job is active.
**Exact next:** await session19476; require exit0/all4bundles/checks/fullMD5 output, independently audit safe
preparation evidence; post full output41 and dated PLAN_G note/receipt draftPR. Copy unchanged filled scripts,
verify process/bundle/pin/cap gates, start detachedscreenblockg EXACTplan command in separate launch shell.
Post every G progress line41; correctedF only after Gends. On another failure preserve/report/pause, no retry.
This supersedes WAIT_MERGE and all first-attempt state below. Heartbeat remains ACTIVE, quiet unchanged.

**Ordering fix published; waiting for Claude's merge — Astra, 2026-10-17 02:19 UTC, claim #51.**
[Draft PR #55](https://github.com/andresloak100/Gene-Mila/pull/55), commitb8d80fe, own branch
`astra/clean-go-ordering` in `gene-mila-string-header`. Independent source review approved; focused16passed;
coherent full suite590passed/1optional Biomni skip/8existing warnings,721.05s,exit0. New source/test delta only;
headerPR54 merged81bf6f5, docsPR52 merged94841b7. Readiness posted41/comment6228409740; CI README checks pass.
Andres directly requires Claude to merge55 before rebuilding. No archive/rebuild/paid G/F evaluation yet.
Immutable cap `67.26 47.264645 2026-10-17T01:52Z`; STOPpresent; first preparation outputs/log preserved.
**Exact next:** wait actual PR55 MERGED SHA, fetch from ownrepo/create clean own rebuild checkout at that SHA;
source matches reviewed fixes, then preserve OUR UNUSED new outputs/log by dated rename (no child/private reads,
no deletions/overwrites/original data changes), run original preparation once, post all checks and md5s.
Only if all pass copy unchanged scripts/start detachedG atbaa7dfd,post every progress line; correctedF after Gends.
No self-merge, unmerged-source rebuild, cap reset, script/evidence/criterion change or newpaidarm.
Existing heartbeat `finish-block-f-and-publish-its-readings` resumed ACTIVE at5min with this merge→prepare→G→F scope;
quiet while unchanged, posts eachG progress line and stops/reports on failing checks. Current fullsuite complete;
no active test/build/lab/driver/F process. A later verified milestone supersedes this WAIT_MERGE checkpoint.

**Andres requires integration merge before rebuilding — Astra, 2026-10-17 02:15 UTC.**
Direct instruction: open ordering-fix PR; Claude merges after tests pass; rebuild ONLY from own clean checkout
at that actual merge, then start G, then corrected F after G ends. No unmerged-source rebuild/archive yet.
Current source fix is independently approved, focused16passed; single fullsuite nice19/keysunset remains active
session36739/Python36024, `/tmp/gene-mila-go-order-pytest-20261017.log` and `.exit` on completion. Do not duplicate.
**Exact next:** on exit0 create own `astra/clean-go-ordering` branch atd34bd93, commit reviewedGOdelta, push/open
separate draftPR intointegration; dependency headerPR54. Ask Claude via41 to merge54 then orderingPR (and docs52).
Verify actual orderingPR merged SHA before creating clean own rebuild checkout. Preserve our unused new outputs
unchanged under dated names, original preparation script once, post checks; only then G atbaa7dfd, cap67.26 unchanged.
No paid G/F process active, original source bundles untouched; all first-attempt outputs/log preserved.

**G preparation refused; ordering recovery under review — Astra, 2026-10-17 02:06 UTC, claim #51.**
First preparation session44048 exited1: `gene_sets.json differs between norman_clean and norman_clean_tables;
the builder is not deterministic`. Full output/hashes/diagnosis in own PR #52 at5a8d34f and
[#41/comment6228278298](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6228278298).
All6 tables plus both individually checked Norman clean bundles exist; Adamson clean bundles not built.
No G run/script copy/paidcall/F fit started. STOP present, cap immutable `67.26 47.264645 2026-10-17T01:52Z`.
Independent read-only diagnosis:5773 identical gene-set keys/list values,2293 key positions differ; other4shared
knowledge files byte-identical. Ancestor-set hash iteration controls dict order, unsorted serialization persists it.
Never bypass the byte-equality gate: plugins can observe order. Original existing source bundles untouched.
Minimal one-line deterministic ancestor traversal + cross-hash-seed regression is now on own header-fix branch
`astra/string-physical-header-compat` (PR54); independently approved; focused16checks passed in1.16s. Full suite NOW active nice19/keysunset,
session36739/Python36024; log `/tmp/gene-mila-go-order-pytest-20261017.log`, `.exit` on completion.
Source frozen; do not duplicate or push before pass. No GO-fix commit/push yet.
**Exact next:** complete focused/full required tests nice19 with keys unset and publish the reviewed fix. Only
then preserve OUR NEW UNUSED failed-preparation directories unchanged under unique dated archive names
(`data/norman_clean`, `data/norman_clean_tables`, clean_knowledge/tables/norman and /adamson_cf) plus prepare log;
no deletions, content/manifest edits, original bundle changes or cap reset. Rename preserves directory contents.
Reinvoke unchanged prepare once from validated own clone into now-unused paths; post full output or failure,
then launch G atbaa7dfd only if every gate passes/no F/lab/driver, and post each safe progress line.
Corrected F remains unstarted and waits for G to finish. No new scientific arm, criterion, raw-header or script change.

**Free G preparation active — Astra, 2026-10-17 02:01 UTC, claim #51.**
Reviewed compatibility fix d34bd93 is published as [draft PR #54](https://github.com/andresloak100/Gene-Mila/pull/54),
attached to Astra's chat: exact STRING `experimental` alias plus regression and Darwin-only fixture adjustment.
Coherent full suite PASSED:589passed/1optional Biomni skip/8existing warnings,720.81s,exit0. No research/script rule changed.
Unchanged `prepare_clean_bundles.sh` is NOW running once from clean own checkout `gene-mila-string-header`
atd34bd93, keys unset, managed session44048; exclusive log `genemila_scale_logs/block_g_prepare.log`.
No G chain or corrected F fit active. Immutable cap remains `67.26 47.264645 2026-10-17T01:52Z`.
**Exact next:** await this preparation's status; on success post FULL output/checks on #41 and append dated PLAN_G note;
copy unchanged scripts from this own clone, verify no lab/driver/F reader, start detached G as planned atbaa7dfd.
On actual refusal/failure preserve all partials/evidence and report; no blind rebuild/retry/cleanup. G precedes corrected F.

**Block G cap recorded; G precedes corrected F — Astra, 2026-10-17 01:55 UTC, claim #51.**
Andres directly confirmed the recorded cap decision and ordered the start under the no-overlap timing rule.
Confirmation dated17October01:46UTC: [#41/comment6228138730](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6228138730).
The exact line/date are appended to PLAN_G in own prep branch commit66a32d3, [draft PR #52](https://github.com/andresloak100/Gene-Mila/pull/52).
Money's write-once command succeeded: **`67.26 47.264645 2026-10-17T01:52Z`** in live `block_g_cap.txt`.
Never rewrite/reset it. Progress receipt appended. No paid G run or corrected F evaluation has started.
Coherent compatibility suite remains active nice19/session67466/Python12175; no failures at last check.
Wait for its complete pass before pushing the independently reviewed three-file compatibility patch.
**Exact next:** publish tested compatibility PR; run unchanged `prepare_clean_bundles.sh` from that own clone,
post full output/checks and append to PLAN_G; copy the unchanged filled-in run/chain scripts; verify no F/lab/driver,
then start detached `screen blockg` per PLAN_G, pinned clean research checkout `gene-mila-baa7dfd`, cap67.26.
Post each new G run line from `progress.md` to #41; on refusal/failing check report evidence, do not blind retry.
G now runs FIRST because corrected F has not started. After G ends and no lab/driver remains, run corrected F
all66 status-ok rows at999replicates with tool1a95873, no --k or --with-val1, new output paths/nice19/detached.
No source/run-pin/script/criteria/raw-data/header rewrites. Earlier no-cap/F-first notes below are historical.

**Compatibility validation checkpoint — Astra, 2026-10-17 01:50 UTC, claim #51.**
Reviewed patch in `gene-mila-string-header` / `astra/string-physical-header-compat`: one parser alias
(`experimental` beside `experiments`), actual physical-header regression, and a Darwin-only test-fixture
exception for macOS-injected `__CF_USER_TEXT_ENCODING`. Production environment allowlist/security
assertions, evidence channels and scoring rule unchanged. Independent source reviews approved both.
Targeted baselines+clean-bundle checks:20passed/1optional Biomni skip,7.73s. The first full suite found
that fixture portability failure; it was explicitly interrupted (exit143), logs preserved, no pass claimed.
The coherent full suite is NOW active at nice19, **session67466/Python12175**, new log
`/tmp/gene-mila-string-header-pytest-20261017-coherent.log`, exitmarker sameprefix `.exit`.
Do not duplicate; do not push code unless this required check passes. No commit/push on fix branch yet.
PR #52/raw receipts and existing B4 readings remain published; own prep branch clean. Dedicated G
checkout baa7dfd clean. Corrected F worktree1a95873 preflight verified all142 old result hashes and all66
inputs (r0=40/r2=1/r3=25); new output paths unused, no select or fit yet.
**Exact next:** await coherent test result, publish reviewed compatibility PR, execute unchanged prepare
from the validated own clone and post output/refusal; then corrected F select(no --k), one999-rep call
on every source and pool, new output paths/nice19/detached. No paid chain/cap file until Andres cap line,
never overlapping F; no raw-header/plan/null-tool/run-pin changes. Safari control stopped for this turn;
console reading already captured, no further UI use. Old process/test notes below are historical.

**ROADMAP free preparation progress — Astra, 2026-10-17 01:45 UTC, claim #51.**
Steps1/3 are posted: console/tooling #41/comment6228055333; receipts [draft PR #52](https://github.com/andresloak100/Gene-Mila/pull/52),
branch `astra/roadmap-preparation`, commit ecd8085. All12 raw inputs ready; original nine receipts preserved.
Step4 existing B4 JSON/MD is in that PR and [on #39](https://github.com/andresloak100/Gene-Mila/pull/39#issuecomment-6228077802):
r0/r2 clean stored sealed Pearson .722960087/.719890613, n2 mean±sampleSD .721425350±.002170446;
r3 separate lost-planner arm, costs .389612324/.451021668/0 (total .840633992). Planned paired combined
B4-versus-B2 result was not found; no verdict/scoring/retry fabricated. Exactsource hashes/ledger rows preserved.
Step2 still held BEFORE any prepare invocation/partial outputs for confirmed STRING header mismatch.
A necessary compatibility-only patch is under review in isolated `gene-mila-string-header`, branch
`astra/string-physical-header-compat` at1a95873: accept `experimental` as an alias of `experiments`, same
planned channels/threshold. Actual-header regression passes all15 clean-bundle tests; independent review
approved. Full required suite is active nice19, session59542/Python4991; log
`/tmp/gene-mila-string-header-pytest-20261017.log`, exitmarker sameprefix `.exit`. An early F/skip was
observed; await final traceback, do not silently ignore it or push code without required checks passing.
No source commit/push for this patch yet; no plan/null-tool/raw-header/run-pin/cap change.
**Exact next:** finish validation/diagnose actual failure, publish a minimal reviewed compatibility PR;
then run unchanged prepare from validated own clone, post exact output/refusal, and launch corrected F
all66 stage1-ok rows at999reps/nice19 in separate fixed1a95873 worktree only after prep step is resolved.
No paid chain/cap file until Andres's cap line; never overlap chain and corrected F. No F fit started.
Dedicated `gene-mila-baa7dfd` stays clean atbaa7dfd; main/existing bundles/runs/ledger untouched.

**Astra ROADMAP steps 1–4 / corrected F handoff ACTIVE, 2026-10-17 01:40 UTC; claim #51.**
Direct Andres instruction: read lead comments6226276557/6227968135, do ROADMAP section6 steps1–4,
then corrected F re-read with tool1a95873 (999 replicates, EVERY status-ok row). Paid G chain only
with Andres's own cap line on #41 and NEVER overlapping the re-read. This supersedes old F-positive
notes below: A.1 is withdrawn/pending the corrected test; old results remain historical evidence.
Step1 posted on #41/comment6228055333: docker `/usr/local/bin/docker`; gtimeout/claude not found;
codex app CLI found. Refreshed console topped-up28.19/granted14.84, expiry not shown, totalcost23.63.
Own clone `gene-mila-roadmap` at1a95873, branch `astra/roadmap-preparation`. Dedicated clean run checkout
`~/Documents/Mila/Gene-Mila/gene-mila-baa7dfd` created atbaa7dfd from own clone. Main untouched.
Corrected-reader worktree `gene-mila-f-corrected`, branch `astra/block-f-corrected-readings`, at1a95873;
no evaluation has started. Old output paths will not be replaced; select without --k, 999reps, then pool.
**Step2 preflight BLOCKER, reported to lead before partial builds:** actual STRING physical v12 header
is `protein1 protein2 experimental database textmining combined_score`; unchanged knowledge_clean.py:234
asks `_header_index(head, 'experiments')` and raises ValueError. No script/builder/raw-source edits or
prepare invocation yet. Raw aliases + three additional source receipts are finishing under clean_knowledge;
original nine files and receipt preserved. Need lead compatibility correction before exact prepare.
B4 step4 reading-only audit also finds r3 mixed/lost planner (exhausted0.2min, zero workers/cost0), so
it cannot join r0/r2 as three clean repeats; no missing paired arm reading will be fabricated or scored.
**Exact next:** finish raw readiness/report; draft receipts PR, post existing B4 evidence/limitations;
resolve STRING header via lead, then unchanged exact prepare/post log, and only then launch corrected F
nice19/detached/no paid overlap. Do not write a G cap, start chain, change tests/criteria or retry fits.
Keep live STATE/#41/#39 current. Existing F heartbeat stays paused until a corrected re-read is active.

**The lead's roadmap is [`docs/ROADMAP.md`](docs/ROADMAP.md) (Claude, 2026-10-16 23:40 UTC); read it first.** Block G
runs first at `baa7dfd` (PLAN_G's dated note; `block_g_run.sh` filled); **Andres confirmed the cap on 17 October,
01:46 UTC (#41): the chain may start**, under the timing rule of #41 (never beside the block F re-read);
the readings wait for the corrected fair test (ROADMAP D2: the gene-permutation null cannot fail for a parent-times-
scalar candidate, and 20·m − 1 replicates put the p floor at the cutoff; `GOAL_CRITERIA.md` corrected: A.1 pending).
Then block H, the Adamson comparison (ROADMAP D6), and the Replogle commit-then-reveal fresh test (D7). Astra's ordered
list is ROADMAP section 6; the four things only Andres can do are section 7. Landed 17 October (ROADMAP's note of
01:10 UTC): the corrected fair test, the pre-registration and literature check, the block H tooling, plan and Mac
scripts with the task package's harness tier, and the fresh-test tooling with `docs/PLAN_R_FRESH_TEST.md`.

**Block G code and plan land with this pull request (Claude, lead, 2026-10-16 23:00 UTC).** `tools/build_clean_bundle.py`,
`genemila/data/knowledge_clean.py` (GO codes EXP, IDA, IPI, IMP, IGI, HDA, TAS, IC, NAS; STRING experiments and database
channels; CORUM; Reactome; CollecTRI), `docs/PLAN_G_CLEAN_ARM.md`, `docs/mac/block_g/`, and
`genemila/research_state.py` (`KNOWLEDGE_SECTION_CHARS = 8000`; one constant and three lines, announced on Astra's #40).
Block F is closed: results merged (PR #46), readings 3 and 4 read in `docs/GOAL_CRITERIA.md` (still not yet). Andres
handed the lead to this session (16 October, #41): the roadmap `docs/ROADMAP.md` is being written and decides whether
block G runs as planned or amended; **`<G_COMMIT>` and the cap are named in the plan's dated note only after that**, so
the chain waits. **Astra next, free:** clone the integration branch at or after this merge, run
`docs/mac/block_g/prepare_clean_bundles.sh` (the nine downloads are done and hash-verified, receipts on #47; the plan's
`corum_allComplexes.txt` is the file the receipt calls `allComplexes.txt`, renamed or linked into the download directory
under the plan's name, and the STRING file likewise `string_physical_detailed.txt.gz`), post its output on #41, and start
no paid run.
**Astra follow-up COMPLETE — 2026-10-16 21:51 UTC; claim #47 closed.**
Block F readings 3/4 and original results remain preserved. Coefficient addendum **b9d550a** is pushed
in [draft PR #46](https://github.com/andresloak100/Gene-Mila/pull/46), posted on
[#41/comment6225228232](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6225228232).
Existing creation-fit standardized interaction coefficients (ridge alpha100): F r0 EXP_0428/e428
+.014724067753942987; EXP_0666/e666 +.01434165272419911; F r3 EXP_0412/e412 -.00996105446986751.
These original multifeature fits have mixed conditional signs, not a universal negative-CpG mechanism;
the primary common-parent OOF coefficient was not saved. No refit or new score. Selected r0 retains
e666 positively; e428 and selected r3/e412 are absent. Full artifact hashes/model columns and addendum
manifest are in `docs/results/norman_f_coefficient_signs.*` / `norman_f_coefficient_manifest.json`.
All 142 original result hashes remain unchanged; independent addendum audit and PR checks passed.
All **9** requested public references are downloaded, **4,483,967,213 bytes** total, in
`~/Documents/Mila/Gene-Mila/data_downloads/clean_knowledge/`. Every SHA256/size independently verified;
HTTP200/curl0/TLS verification succeeded, all transfer processes ended normally and no partial remains.
`downloads.md` records requested/final URLs, UTC dates and SHA256, including CORUM official API move
(current5.3/date2026-04-14; old static ZIP path serves HTML) and GO OBO redirect. Document SHA256:
`cd22243dcaba2b3e4c169b08f5919ea4894b8a69881213b428d12a4f848217da`.
[Full exact receipt on #47](https://github.com/andresloak100/Gene-Mila/issues/47#issuecomment-6225365762);
[completion cross-link on #41](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6225366353).
The initial pending receipt entries are retained as history and explicitly resolved by final completion.
**Exact next:** review PR #46 and the download receipt. No transfer, coefficient extraction, F reading,
paid run or test needs repeating. No Block G preprocessing, bundle/build or run occurred; start nothing
for G until `docs/PLAN_G_CLEAN_ARM.md` on integration has the dated note naming its commit, as Andres
explicitly directed. This completed task initiates no later work. STOP present, Block F cap/hash unchanged,
no lab/driver active, main checkout/existing bundles/runs/ledger untouched, F heartbeat remains PAUSED.
Earlier ACTIVE download/process notes are historical; do not restart them.

**Coefficient addendum published; free downloads active — Astra, 2026-10-16 21:42 UTC, claim #47.**
Reading 4 saved-fit sign addendum **b9d550a** is pushed to draft PR #46 and posted on #41,
[comment 6225228232](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6225228232).
Creation fits (all ridge alpha100): F r0 EXP_0428/e428 +.014724067753942987,
EXP_0666/e666 +.01434165272419911; F r3 EXP_0412/e412 -.00996105446986751.
Selected r0 EXP_0715 retains e666 positively; e428 and selected r3 EXP_0603/e412 are absent.
These are original standardized interaction-column coefficients, not the unsaved common-parent OOF
coefficient; signs vary with model context and do not confirm a universal negative-CpG mechanism.
No new fit, label access, scoring, alpha/model choice or lab/tool code change. All 142 original artifact
hashes remain unchanged; separate addendum JSON/MD/manifest and independent audit pass; PR checks pass.
Seven of nine named downloads are complete with local receipts. GTF and FASTA remain active in
`data_downloads/clean_knowledge/`: managed download session8677, Python76820, GTFcurl76876,
FASTAcurl76958. Preserve those processes/partials; do not duplicate or restart.
Partial names: `gencode.v27.primary_assembly.annotation.gtf.partial-34e2f95ac2` and
`Homo_sapiens_assembly38.fasta.partial-c13bc1f84e`; per-file header/transfer receipts share suffixes.
Downloader `download_sources.py` writes exclusive completed receipts; `download_receipts.json` appears
when all nine finish. Local `downloads.md` already records seven completions and two pending entries.
CORUM official release/file APIs independently verified:5.3/date2026-04-14, complete/allComplexes/txt;
legacy ZIP path returns HTML, actual API path and GO OBO redirect are recorded.
**Exact next:** download worker completes both existing transfers, appends final URL/UTC/SHA256 receipts;
root verifies receipts, posts full downloads.md to #47/links #41, updates state and stops. No G build/run,
API spend or additional experiment. The direct gate remains: no G action before its integration-plan
dated note names a commit; this free-preparation task itself authorizes no later run.

**Astra follow-up authorized — coefficient-sign addendum and free downloads, 2026-10-16 21:38 UTC; claim #47.**
Andres directly requested the fitted coefficient signs for promoter-CpG e428/e666 (F r0) and e412
(F r3), plus the named public-reference downloads into `data_downloads/clean_knowledge/` with
requested/final URL, date and SHA256 receipts in `downloads.md`; verify the current CORUM path.
Block F readings 3/4, results commit 7e02a4f and draft PR #46 are already complete and stay preserved.
Astra will extract existing saved fitted coefficients read-only where available, label the model/alpha
and rounding context, append an addendum to PR #46 and post it on #41. No scientific reading or sealed
scoring is repeated. A delegated download worker touches only the new clean_knowledge directory.
**Exact next:** finish coefficient provenance/sign report and download receipts; document results on
#41/#47, this section and live STATE. No paid call, Block G bundle/build/run, model selection or merge.
Andres explicitly said start nothing for G until the integration plan has a dated note naming its commit;
this task does not authorize that later start. Main checkout, existing data/runs and cap stay unchanged.

**Block F COMPLETE and published — Astra, 2026-10-16 21:29 UTC.**
All three paid runs passed; all approved two-stage readings 1–4 exited 0. Results commit
**7e02a4f1def95c95cac6766ee56cb1f03897828b**, branch `astra/block-f-results`,
[draft PR #46](https://github.com/andresloak100/Gene-Mila/pull/46) into integration. The PR is attached to
Astra's chat; no merge or model promotion. Final interpretation/run-directory table
[on #41](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6225044026); full unedited
pooled table and sealed readings [in comment 6224750231](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6224750231).
Primary: 94 unchanged plugins; 66 usable family rows, 20 null-tested, 10 passing, four tier-1-labelled
rows representing two computational families. All passing pooled p = .05 at permutation-resolution limit;
CpG reports repeat identically, numeric TSS feature ignores chromosome/strand and includes self-distance 0.
Twenty-eight plugins unassessable (25 missing-key errors, three constant-feature smoke failures), unrepaired.
F OOF Pearson delta **0.580526 ± 0.002321**; B2 **0.582457 ± 0.008062**, sample SD across search seeds
0/2/3: no established arm gain. F selected sealed **0.719579 ± 0.001206** on inspected cohort; only r0
establishes gain over its start. Mixed error metrics; no fresh-test/CellForge/biological-discovery claim.
Raw JSON/Markdown twins, all copied plugins, source/count/usage inventory and MD5/SHA256 evidence are in
`docs/results/norman_f_*`; entry point `docs/results/norman_f_readings.md`. Independent audit passed.
Required full pytest: **540 passed, eight existing cell_eval/Polars deprecation warnings, 685.48 s**, exit 0.
Artifact and staged credential scans, 142 artifact-hash checks and whitespace check passed; own clone clean.
F recorded cost **2.824188224** ledger USD (r0 1.288493084, r2 .288033672, r3 1.247661468);
original cap 52.44/hash unchanged. STOP present; no active lab/driver/evaluator/test from this block.
No main-checkout, existing data/run, split, guard or ledger modification. No extra paid reading call,
no summary.md or original run-log end read; no scientific reading needs rerunning.
**Exact next for the next agent:** review PR #46's report, pooled/sealed tables and source limitations.
Any replication or clean-source arm needs its own authorized plan/commit; this completed Block F handoff
starts nothing further. Pause the Block F heartbeat after this completion receipt; preserve all evidence.
Earlier ACTIVE notes below are history, not commands to restart anything.

**Block F all readings complete; final validation/publication active — Astra, 2026-10-16 21:25 UTC.**
Readings 1–4 all exited 0, including the six-run descriptive OOF comparison and source/count/usage audit.
F OOF M1 = 0.580526 ± 0.002321; B2 = 0.582457 ± 0.008062 (sample SD across search seeds 0/2/3).
F has no established arm gain. Primary: 10 passing rows, four tier-1-labelled rows representing two
computational families; CpG reports repeat identically, and the numeric TSS code ignores chromosome/strand,
includes self-target distance 0 and never reads the bidirectional map. No biological-discovery claim.
Selected sealed Pearson = 0.719579 ± 0.001206 on the already inspected split; only r0 establishes a gain
against its start. Full unedited pooled/sealed tables are already on #41, comment 6224750231.
Own `gene-mila-block-f`, branch `astra/block-f-results`, evaluation source b6638c3; all raw JSON/Markdown,
94 unchanged plugins, manifests, metadata collector and final report are in `docs/results/norman_f_*`.
Independent final arithmetic/source/report audit passes; two reproduction wording corrections applied.
Required full pytest is running at nice 19, managed session 15408 / Python 50906; do not duplicate.
**Exact next:** await test exit; on success save checks/artifact hashes, secret-scan, commit/push results,
open/attach a draft PR into integration, post final arm/cost interpretation with run directories on #41,
update this section/live STATE and pause the Block F monitor. Do not rerun any scientific reading.
No model promotion, merge, further paid run or follow-on arm is part of this handoff. Main checkout,
existing data/runs, cap and ledger untouched; STOP remains present. Earlier notes below are history.

**Block F read against [`docs/GOAL_CRITERIA.md`](docs/GOAL_CRITERIA.md): not yet (Claude, claim #41, 2026-10-16 22:05 UTC).**
A.1 is met at the letter by one family, additive_response × the targets' promoter CpG (r0 e428/e666, r3 e412;
pooled Holm p = 0.05, the test's resolution limit, raw p = 1/1320), and once by additive × a TSS-distance number
(r0 e541, code flagged by the operator). The mechanism is known biology (CRISPRa gains least at CpG-island
promoters), so A.6 (not already published) was added, stricter only; A.2 to A.5 and B.1 to B.5 are not met. The F
runs' sealed scores (0.720, 0.718, 0.720) are no higher than B2's (0.722, 0.720, 0.730); descriptive, no arm test.
Full reading in GOAL_CRITERIA.md (Status) and on #41.
**Block G, the clean arm** (tier-1 sources only, no screen and no Enrichr in the bundle; Andres's approval of 21:08
UTC on #41), is being built on `claude/youthful-dijkstra-459nhj`: `genemila/data/knowledge_clean.py`,
`tools/build_clean_bundle.py`, `docs/PLAN_G_CLEAN_ARM.md`, `docs/mac/block_g/`, and one planner change
(`genemila/research_state.py`: the knowledge section's budget rises to 8,000 characters so the planner sees every
knowledge file; that file is in Astra's claim #40, coordinated there). **Astra next:** finish block F readings 3
and 4, the results commit and the draft PR; then start nothing until the block G plan's dated note names its commit.
Free preparation meanwhile: the raw downloads the plan lists, into
`~/Documents/Mila/Gene-Mila/data_downloads/clean_knowledge/`.

**Block F primary pooled / sealed readings complete; reading3 ACTIVE, 2026-10-16 21:10UTC:**
Stage2 exited0 at21:05:40UTC (38min wall from log creation); exact helperpool exited0. Family66,
tested20, passing10rows, tier1-labelled4rows. All passing rawp=1/1320, pooledp=.05 exactly at
permutation-resolution boundary. Independent arithmetic/non-null/hash audit passed. Tier1rows are
two computational families: CpG×additive repeated3times with identical saved reports; numeric
TSS-distance×additive once. TSS code ignores chromosome/strand, includes self-target distance 0 and does not use
bidirectional mapping; do not claim a bidirectional-promoter mechanism or novel discovery.
Allthree ce1b530 sealed readings exited0, JSON/MD in ownclone; tooldiscloses4oracle scorings/run
outside run caps, one previously unscored start/run. No sealed outcome used for selection/change.
Full unedited pooledtable and sealedreadings [on #41](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6224750231).
Reading3 six-run descriptive OOF comparison is running, managedsession**24627**, Python**47291**,
output `docs/results/norman_f_arm_vs_b2/` (not yet written at21:10:25UTC). Do not duplicate/restart
stage1/select/stage2/pool/sealed reads. Ownresultsbranch astra/block-f-results/sourceb6638c3.
**Exact next:** await session24627; any refusal report/hold without workaround. Then reading4
source/count/usage metadata, final mean+/-sampleSD over runseeds0/2/3 and all tool metrics, independent
report audit, secret-scan/requiredchecks/resultscommit/draftPR; post finalinterpretation on41.
No fresh-test/CellForge win, sealed F-versusB2 comparison, modelpromotion or follow-on arm. Original
cap/data/run dirs/maincode untouched, STOPpresent; root owns evaluator/shared/live state. Prior
notes below preserved; active nullscreen29493/PID29504 ended normally and must not be restarted.


**Block F amended stage2 ACTIVE, 2026-10-16 20:27UTC — leave running at nice19:**
Own clone `gene-mila-block-f`, astra/block-f-results atb6638c3. Stage1 exited0 (156reportrows;
JSON/MD in norman_f_stage1); exact helperselect exited0: **66status-ok annotation add-one rows**,
**20selected**, **1319null replicates/feature**. Sources10f_r0/0f_r2/10f_r3; emptyr2 omitted in
stage2 as plan permits. Original single-stage not run. Pluginmanifest records94copied unchanged
files(r0=60,r2=1,r3=33) and MD5/SHA256. No operator selection or threshold change.
Stage2 launched20:27UTC, detached **screen29493.blockfnull**, PythonPID**29504**, `ps` verified
**NI19**, running. Output ownclone `docs/results/norman_f_stage2/`; log
`docs/results/norman_f_stage2.log`; exit-code marker `docs/results/norman_f_stage2.exit` appears
only on exit. Credentials unset for CPU process. Source/branch must remain unchanged while active.
Receipt [on #41](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6224090858).
**Exact next:** lightweight existing monitor; takes hours, no arbitrary timeout/reduction/retry or
duplicate/heavy job. On nonzeroexit/refusal preserve evidence/report/hold. On exit0 exact helperpool
into norman_f_pooled_holm, then readings2–4 unchanged (ce1b530 sealedtool, six-run OOF, source/count
and cost description), secret-scanned resultscommit/draftPR and pooledtable/sealedreadings on41.
No primary null verdict yet, summary.md/run-log-ending/sealed reading, val1opt-in, model promotion
or paid call. Direct human authority comment6223988752; shared/live state owned by root. Prior
notes below preserved as history; session77318 completed successfully and must not be restarted.


**Block F amended stage1 ACTIVE, 2026-10-16 20:26UTC:** exact OOF/null0 comparison in own
`gene-mila-block-f`, branch astra/block-f-results atb6638c3; managed execsession77318, process27213,
active3minutes at20:26:13UTC. No output JSON yet; do not duplicate/restart. Directtwo-stage decision
and94unchanged plugin/MD5manifest remain as below. Monitor reactivated with resolved-choice/current
stage checkpoint. **Exact next:** await session77318 exit; any refusal report/hold. On success run
exact helperselect, then stage2 nice19 detached with fixed helperrepcount, pool, readings2–4.
No sealed/log-end/summary.md read. Root is sole evaluator; no additional heavy job or paid run.


**Direct two-stage decision received, 2026-10-16 20:22 UTC — Block F readings starting:**
Andres explicitly said use PR44/b6638c3 two-stage test, do not run original single-stage, follow
comments6223733089/6223972936 exactly, stage2 at nice19, then readings2–4 and draftresultsPR.
Full direct message [on #41](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6223988752).
This supersedes the pending-choice notes below. Own operator clone now at **b6638c3**, branch
**astra/block-f-results**. Exact reading1 copy produced94unchanged annotation plugins: r0=60,
r2=1,r3=33; byte equality and secret-pattern scan passed, MD5/SHA256 in
`docs/results/norman_f_plugin_manifest.json`. No primary/sealed evaluation has run yet.
Allthreepaidruns passed; no lab/scale/feature_compare process before evaluation, STOPpresent.
**Exact next:** exact amended stage1 OOF `--null-reps 0` into norman_f_stage1; helper select top20
with fixed tie rule/replicate count; stage2 nice19 with sources that have topfiles, leave running;
helper pool over full stage1 family, then readings2–4 unchanged. No original all-feature null,
val1 opt-in, threshold/k change, new paid run, private-label/manual sealed access or model selection.
After success, commit all norman_f_* artifacts/plugins on own results branch, secret-scan, draftPR,
post pooled_holm.md and sealed readings with run directories on41. Keep state current at each stage.
Root owns sole evaluation/shared/live state. Prior operator0db run scripts/maincode/data/cap intact.


**All three Block F runs PASSED, 2026-10-16 20:17:25 UTC; readings await the direct plan choice:**
`gene-mila/runs/norman_ga_ds_addstart_w4_r0`: finished19:30UTC, rc0,1203s,60annotation plugins,
selected EXP_0715 ridge28features, ledgercost1.288493. `_r2`: finished19:54UTC,rc0,1231.2s,
1annotation plugin,selected EXP_0260 ridge11features,cost0.288034. `_r3`: finished20:17UTC,rc0,
1231s,33annotation plugins,selected EXP_0603 ridge24features,cost1.247662. All three `.passed`
markers present; every check codece1b530431/fourworkers/exactknowledge/DeepSeek mixedFalse/no
exhaustion, no failed/stopped marker. Counts/selection are process evidence, not improvement.
Total ledger accounting **$2.824189** rounded; ending **$47.264645**; original cap52.44 untouched.
At20:18UTC no screen session or lab/chain/scale process. **STOP PRESENT**, normal exit trap.
Completion [on #41](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6223930718).
**Exact next:** direct Andres choice already pending in Astra chat: original all-feature null
reading versus PR44 two-stage amendment. No evaluation/source update/sealed or summary.md/log-end
read until his choice is recorded on41/HANDOFF1/liveSTATE. Monitor
`finish-block-f-and-publish-its-readings` paused after clean completion; do not start another run.
Then execute only the chosen exact plan in own clone, remaining readings, astra/block-f-results,
secret-scanned draftPR and numeric findings. Operator clone0db8091, amendedtool/planb6638c3.
No original-data/main-code/script/cap change or model promotion. Earlier notes below are history.


**Reading-version clarification pending, 2026-10-16 20:11 UTC — seed3 continues unchanged:**
Routine state check found mergedPR44 **b6638c3**, operator comment6223733089: a two-stage primary
reading (all-row OOF screen, null only for top20, full status-ok stage1 family with untested p=1)
plus faster null engine/helper. This changes the original primary procedure/family definition;
no primary/sealed F reading has occurred. Current direct handoff/heartbeat says original unchanged
reading. Astra presented Andres one explicit choice in this chat: adopt PR44 or keep original.
**No new procedure/approval is inferred from another agent's comment or broad merge permission.**
Paid run3 remains untouched/active; this is not a lab failure and no STOP/kill/retry is requested.
Actual amendment commit times19:45:48/19:52:37/20:04:35UTC, merge20:06:41UTC, while runs in flight;
plan headings04:20/05:05/05:30 differ. Preserve actual provenance; do not say before runs began.
Source-only audit: scientific non-null gates unchanged, untested rows cannot pass; helper retains
max(199,20*m_total-1). [Operator receipt](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6223793338).
**Exact next:** continue only allowed monitoring to allthreepass or report an actual run failure.
**Do not start any evaluation until Andres's direct reading-version choice arrives and is recorded**
on41/HANDOFF1/liveSTATE. If runs finish while choice pending, report completion and hold readings;
no sealed/runlog/summary.md read, new paid arm or method change. Earlier entries below preserved.


**Block F milestone, 2026-10-16 19:57 UTC — seeds0/2 PASSED, seed3 active:**
Run `gene-mila/runs/norman_ga_ds_addstart_w4_r2` finished19:54UTC rc0, codece1b530431,1231.2s,
seed2/four workers, exact knowledge pair, DeepSeek planner mixedFalse/no exhaustion; `.passed`
present. Selected EXP_0260 ridge11features by visible rule; one annotation-reading plugin. Ledger
seed2cost **$0.288034**, ending **$46.016983**, completed seeds0+2 cost **$1.576527** rounded;
cap52.44 unchanged, accounting not invoice. No model-improvement claim. Seed3 started19:54UTC at
`gene-mila/runs/norman_ga_ds_addstart_w4_r3`; preflightpassed, process1094 active at19:57:57UTC,
screen65924.blockf/chain65926 active. Both earlier passed markers present; no failed/stopped check.
Milestone [on #41](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6223591100).
**Exact next:** existing five-minute monitor, allowed progress/chain/check/process reads only until
allthreepass and no lab/driver. Then unchanged PLAN_F primary OOF pooled shuffled-gene criterion,
per-run sealed and six-run descriptive readings, results branch/draftPR. No val1 opt-in inferred,
early sealed reading/scoring, overlapping lab/heavy job, script/cap/code/data edit or new arm.
Any failure: report exact evidence and hold, no retry. Root owns Block F/shared/live state; prior
entries below retained as history.


**Block F milestone, 2026-10-16 19:30 UTC — seed0 PASSED, seed2 started:**
Run `gene-mila/runs/norman_ga_ds_addstart_w4_r0` finished rc0; permitted check: codece1b530431,
duration1203s, seed0/four workers, exact knowledge pair, planner DeepSeek mixedFalse, no duration
note or exhaustion; `.passed` exists. Selected EXP_0715 ridge28features;60plugins read annotation.
This is process evidence, not a feature-level gain or discovery. Ledger run cost **$1.288493**,
ending **$45.728949** (accounting, not invoice); cap unchanged52.44. `progress.md`: seed2 started
19:30UTC at `gene-mila/runs/norman_ga_ds_addstart_w4_r2`; seed3 queued. Detached chain remains active,
seed2 preflight passed, no refusal/stopped marker. No early run-log/summary.md/sealed reading,
plugin audit/evaluation, script/cap/main-code edit, overlapping run or heavy job.
Receipt [on #41](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6223149272).
**Exact next:** continue existing five-minute monitor; only allowed progress/chain/check/process
reads while active. On failure report and hold without retry. Allthreepass and no lab/driver before
unchanged PLAN_F primary shuffled-gene/pooled-Holm reading, then sealed/descriptive readings,
branch astra/block-f-results and draft PR. Root owns Block F and shared/live state. Earlier entries
below are preserved history; fixed cap and follow-up remain as recorded.


**Block F RUNNING, 2026-10-16 19:07 UTC — Claim [#41](https://github.com/andresloak100/Gene-Mila/issues/41):**
Andres directly requested the restart in [comment6207417201](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6207417201).
Astra/chat1 fetched and detached own operator clone at **0db809154b11d2d4b1e7c764dd0bbd6b5f318da9**.
Archived old run script and refusal log unchanged to `.stale-20261016T0313Z`, then copied/byte-verified
the corrected run script; chain unchanged. STOP/cap/data retained; preparation/cap not repeated.
Preflight handoff --fetch: no lab/scale/chain process or screen session; no F run directory/log;
STOP present, no stopped-block marker, immutable cap hash unchanged. Exact login-zsh detached-screen
launch **19:07:45UTC**: screen **65924.blockf**, chain65926, caffeinate65935. All checks passed:
knowledge2109<=2500 chars; B2 state15822+897=16719<=20000; starting ledger44.440456<=cap52.44.
`progress.md`: **gene-mila/runs/norman_ga_ds_addstart_w4_r0** started19:07UTC; seeds2/3 queued
sequentially at `runs/norman_ga_ds_addstart_w4_r2` and `_r3`. Research code remains pinned ce1b530.
Cap stays **52.44 44.440456 2026-10-16T01:55Z**. Chain lifts STOP for the block and restores it on exit.
No other lab/heavy job. No early run-log ending/summary.md/sealed-score reading. Full receipts and
four operator recommendations [on #41](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6222778776).
Recommendations do not invent human approvals: tier1 now/tier2 later; validation ranking conditional
on approval with fixed OOF primary; no extra comparison-arm budget; no appointed fresh-test holder.
Follow-up in this chat is active every5minutes via heartbeat `finish-block-f-and-publish-its-readings`: quiet on unchanged state, report failure or complete the prescribed readings/PR after allthreepass; pause after failure/completion. No heavy job until the chain ends.
**Exact next:** monitor only progress.md, block_f_chain.log and allowed checks. On any refusal/failure,
report exact chain/check evidence on41 and hold without retry/script edits. After allthreepass and no
lab/driver active, execute unchanged PLAN_F Readings in own clone, OOF-only unless Andres actually
approves val1, branch astra/block-f-results, secret-scan and draft PR into integration; report each
number with its run directory and mean+/-sampleSD over repeats. Primary is pooled-Holm shuffled-gene
feature test; no sealed selection, new model promotion or unapproved follow-on block. Root owns sole
Block F operation/shared/live state; chat2 Claim40 separate. Earlier notes preserved as history.


**Block F restart authorised, 2026-10-16 03:45 UTC — Claim [#41](https://github.com/andresloak100/Gene-Mila/issues/41):**
the 03:13 refusal was a bug in a new pre-spend check (`sqlite3 -readonly` cannot open the lab's write-ahead
`lab.db` without creating its `-shm` file), not a problem with B2's run directories; fixed in `0db8091`, which copies
each database and its `-wal` to a temporary directory and queries the copy. No spend; the block was not stopped
(`block_f_stopped.txt` is written only after a run). The operator restarts the chain from a clone at `0db8091` or
later with the steps in [#41, comment 6207417201](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6207417201)
(archive the old run script and the refusal log with dated suffixes, copy the new `norman_f_run.sh`, same detached
`screen` command). [PR #43](https://github.com/andresloak100/Gene-Mila/pull/43) (`e082d0c`, second batch of #41:
gnomAD constraint and UniProt builders, residual mining, CellForge-translated features; 537 tests) is merged on
Andres's "keep everything updated". The constraint file cannot join block F's bundle (planner knowledge section cut,
`docs/NOVEL_FEATURE_NEEDS.md` §10). Astra's hold entries below are history as of this fix.

**Block F STOPPED before any run, 2026-10-16 03:13 UTC — Claim [#41](https://github.com/andresloak100/Gene-Mila/issues/41):**
Andres authorized one detached-screen retry, with STOP restored, the prior startup log renamed
unchanged to `block_f_chain.log.stale-20261016T0157Z`, and the existing cap kept; his full decision
and pre-launch receipts are [recorded on #41](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6207215151).
Both requested `ls | grep norman_ga` checks found no run directory/log; no lab/chain/scale process
or screen session was active. Executed his exact login-zsh `screen -dmS blockf zsh -lc` command,
without attaching. New chain log: `2026-10-16T03:13:03Z block F started`, then SQLite
`Error: in prepare, unable to open database file (14)`, then
`NOT STARTED: cannot read planner_rounds.state_chars of norman_ds_addstart_w4_r0`, then
`2026-10-16T03:13:04Z block F stopped at seed 0`.
At03:13:38UTC all three pgrep checks returned no match; screen had no sockets. **STOP present**
(restored by exit trap). No F run directory/log, `.check.txt` or reading was created. DeepSeek ledger
unchanged **44.440456384**, **F spend $0**; cap unchanged **52.44 44.440456 2026-10-16T01:55Z**,
SHA256 `beea162caed4540e4f506d931558459653318db7182d00bfe98e8862fe27c080`.
New refusal log remains `block_f_chain.log`; all stale archives retained. No third retry, script
edit, sealed reading, cap reset, file deletion, original-data/main-codecheckout change or model
selection. Operator clone remains f95111a, scripts identical to986c4d6. Full refusal and process
receipt [on #41](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6207232510).
**Exact next:** hold Block F with STOP/cap/data/scripts/logs preserved. The lab-code owner must
resolve/document the inaccessible B2 seed-0 planner-state database prerequisite before any new
launch; filesystem cause is not established and no workaround is authorized. Do not rerun
preparation, weaken a check, retry or make readings. Root owns Block F operation/shared/live state;
chat2 Claim40 remains separate. Earlier notes below are chronological history.


**Block F operator HOLD after startup,2026-10-16 01:59UTC — Claim [#41](https://github.com/andresloak100/Gene-Mila/issues/41):**
Authorized archival, cap and preparation completed as recorded below. The exact login-zsh launch
printed only **2026-10-16T01:57:02Z block F started**, then disappeared: no caffeinate/chain/run/model
process by01:57:45 or01:58:39. No F run directory, .passed, .check.txt, block_f_stopped.txt or run-start
progress entry exists. No refusal/exit/signal is recorded, so cause is unestablished; do not infer one.
DeepSeek ledger still **44.440456384**, no F spending. Valid cap stays **52.44 44.440456 2026-10-16T01:55Z**.
STOP is **absent** after chain entry; normal restoration did not happen. Operator has not created
STOP, killed a process, edited a script, overwritten/deleted a file or retried. Current startup-only
block_f_chain.log and cap are preserved; detailed evidence posted on41.
**Exact next:** WAIT for Andres's decision before restoring STOP, archiving this new startup-only log
or relaunching. Proposed persistent login-zsh terminal with the unchanged command and same cap is
not yet approved. No automatic retry/reset/spend/readings. Own clone f95111a; main codecheckout and
originaldata/norman unchanged; approveddata/norman_ga and verified script copies remain ready.
Root owns operation/shared/live state. Earlier preparation/HOLD notes below are chronological history.


**Block F operator preparation complete, 2026-10-16 01:56UTC — Claim [#41](https://github.com/andresloak100/Gene-Mila/issues/41):**
Andres directly authorized renaming both false-start files to their exact .stale-20261016T0013Z names,
then the plan's write-once cap and unchanged preparation/copy/launch. Decision also in
[comment6206200655](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6206200655)
and the dated PLAN_F note. Both renames completed with identical SHA256 before/after; deleted nothing.
Cap record **52.44 44.440456 2026-10-16T01:55Z**. This is the confirmed+$8 block, not another allowance.
Own gene-mila-block-f at **f95111a4c78f124ced5def568f4221708cc2775e**, authorized986c4d6 descendant;
all block_f script bytes unchanged from986c4d6. Preparation exited0:2083genes=2041annotated+42unmatched,
copy byte-for-byte and exact knowledge inventory/md5 checks PASS. Original data/norman unchanged;
approved data/norman_ga created. Both scripts copied/byte-verified in genemila_scale_logs.
No F paid run started yet; no lab/scaling driver active before preparation; B4 ended15Oct18:44UTC.
**Exact next:** operator's exact login-zsh chain command, seeds0/2/3, then monitor progress.md,
block_f_chain.log and .check.txt only. No run-log ending/summary.md before readings. Stop/report any
refusal without edits/retry; readings only after allthreepass, results branch astra/block-f-results.
Root owns operation/shared/live state; no main codecheckout changes or script edits.


**Block F operator HOLD, 2026-10-16 01:27 UTC — Claim [#41](https://github.com/andresloak100/Gene-Mila/issues/41), draft [PR #42](https://github.com/andresloak100/Gene-Mila/pull/42):**
Andres explicitly handed the Mac block to Astra/chat1 and confirmed **+$8 over the starting DeepSeek
ledger**, requiring exact execution and stopping to ask on any unclear/failing condition. His whole
message is recorded [on #41](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6205851106).
Own clone gene-mila-block-f under the project workspace, detached exact **986c4d693eec01cdac73df2c6f9d176ee3b7b3d8**;
plan/scripts unchanged. Required handoff/pgrep: no lab run or scaling driver; B4 ended15Oct18:44UTC with
spend recorded. STOP present. No F preparation or paid run has started.

Preflight found pre-existing block_f_cap.txt and block_f_chain.log (both16Oct00:13:36UTC).
Cap contains ONLY **52.44**, lacking the starting ledger and UTC-date fields required by the final plan;
the write-once command refuses existing files and the run script rejects the incomplete format.
Chain-log tail: **bash: norman_f_chain.sh: No such file or directory**.
No F .check.txt exists. F scripts in logs and data/norman_ga(.partial) are absent. Existing files are
preserved; no cap rewrite, file deletion/overwrite, launch/retry, script edit, sealed run-log-ending/
summary.md read, main-checkout mutation or paid call occurred. Failure details posted on issue41.

**Exact next:** wait for Andres's decision on preserving/archiving those two failed-start files and
creating the required three-field cap before continuing the unchanged plan. Do not remove/overwrite
them, create STOP, retry, infer a fresh allowance or start any paid run without his answer. Root owns
BlockF operation/shared/live state; chat2's Claim40 remains separate. The current block is F, on hold.


**Merged, 2026-10-16 01:55 UTC, on Andres's words "start merging, I want everything to be updated":**
[PR #42](https://github.com/andresloak100/Gene-Mila/pull/42) (`f2ff718`), [PR #39](https://github.com/andresloak100/Gene-Mila/pull/39)
(`1b3243e`) and [PR #38](https://github.com/andresloak100/Gene-Mila/pull/38) (`1f990c7`) are in this branch; the archival
research records (#6, #7, #10, #12, #17, #23, #25, #31, #33, #35) stay unmerged as before. Block F is running on the Mac
under Astra as operator (Andres's handoff and +$8 confirmation on #41; a false start of 00:13 UTC left two stale files,
archived by the dated note in `docs/PLAN_F_GENOME_ANNOTATION.md`). DeepSeek console, 16 October: balance $28.19,
granted credit $16.25, 30-day cost $22.22. In the cloud, claim #41 continues on `claude/youthful-dijkstra-459nhj` (now
equal to this head): builders for gnomAD constraint and UniProt protein annotation, a training-only residual-mining
tool and CellForge-translated features (arm A5-C2), each with tests and reviews, as the next PR.

**Claim [#41](https://github.com/andresloak100/Gene-Mila/issues/41), [PR #42](https://github.com/andresloak100/Gene-Mila/pull/42)
(merged): framework to find and fairly test new biological features.** A Claude cloud session on `claude/youthful-dijkstra-459nhj` (final block F commit `986c4d6`), on Andres's
requests of 15 and 16 October (a framework for the agents to find a useful feature; compare "feature + linear model"
against Biomni, CellForge, autoresearch and STATE with one metrics table; a data-source policy; "you have permission
to run the deep seek agents", 16 October). New files only, plus one Money paragraph in `AGENTS.md`, the README and the
documentation map: `tools/feature_compare.py` (any system's features against one fixed ridge, matched gene-permutation
null, Holm per system), `tools/export_task_package.py` + `tools/task_package/` (autoresearch-style task folder for
Claude Code/Codex, Biomni), `tools/build_gene_annotation.py` (GENCODE/hg38 per-gene knowledge file; Norman table
committed gzipped, md5 `99e0eccb3caae76bc98f1c2e5730cfc0`), `tools/knowledge_coverage.py` (retired-symbol check, R0),
`docs/NOVEL_FEATURE_NEEDS.md`, `docs/FEATURE_COMPARISON_PROTOCOL.md`, `docs/PLAN_F_GENOME_ANNOTATION.md` with
`docs/mac/block_f/`; four test files; full suite 510 passed. Protected code, `planner.py`/`prompts.py`/
`research_state.py` (Astra's #40), data, ledger and the Mac untouched. **Nothing has run on real perturbation data.**
**Block F is the current paid block** (`docs/PLAN_F_GENOME_ANNOTATION.md`): B2's Norman settings on code ce1b530
with one change, `data/norman_ga` = `data/norman` plus `knowledge/gene_annotation.json`, seeds 0, 2, 3; cap = ledger
reading at start + $8 (about $4 billed); feature-level reading by pooled Holm over the `gene_annotation` features of
the three runs; nothing runs beside it. It runs on the Mac (Astra may run it as the operator, exactly as written) once
Andres has confirmed the cap in writing on #41 and B4 (PR #39) has finished. Open for Andres: the cap; the data-source
policy (NOVEL §7); `feature_compare --with-val1`; who pays for the autoresearch and Biomni arms; the fresh-test holder
(#22). **Exact next:** Andres confirms the cap → operator follows PLAN_F "Exact commands" from a clone at `986c4d6`
or later → readings per PLAN_F "Readings" on a results branch → results on #41. In the cloud: README redesign in
journal style (Andres, 16 October) pushed to PR #42; then builders for the next tier-1 sources (gnomAD constraint,
signal peptides, CORUM) and a training-only residual tool.

**Active, 2026-10-15 22:04 UTC — Claim [#40](https://github.com/andresloak100/Gene-Mila/issues/40): automated biological feature discovery.**
Andres on15October explicitly requested200precise biological hypotheses, matched control comparison,
one biological feature missing from the current linear model, and agents that choose/search/test it
automatically without his specifying what to examine. Astra/Codex chat2 owns
`astra/biology-feature-discovery` in own `gene-mila-cohort-audit`, base2ac8507.
Scope: minimal molecular hypothesis contract, available-input/existing-feature inventory, automatic
reject/defer/eligible decisions, one-feature parent comparison and persisted findings in the existing
planner/worker workflow; dedicated reproducible configuration, synthetic tests and documented200idea bank.
No generic workflow platform, default budget change, paid call, new cohort, model search, benchmark/
split/guard/data/private read or edit, STOP change or main-checkout mutation. No run is active.
Baseline fullpytest atnice19 running in own clone; read-only handoff --fetch completed. Current Mac
progress includes15October B4one-worker runs underPR39; older STATE/HANDOFF block below predates them,
so consult that owner’s evidence before any run. Their results are not being read or changed here.
**Exact next:** finish read-only integration audit; implement and independently review the bounded
biology mode; run focused and full tests; publish a secret-scanned draftPR and exact continuation.
This user authorization covers implementation/documentation, not spend or protected changes.


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
key, the STOP file, how results reach GitHub): `docs/mac/MAC_HANDOFF.md` (in
PR #6 until it is merged) and the dated Mac snapshot `docs/archive/mac/STATE_20261014.md`. The lab now lives in `~/Documents/Mila/Gene-Mila/` (`gene-mila`,
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
