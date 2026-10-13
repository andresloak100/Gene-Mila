# B2 handoff verification, 13 October 2026

B2 does not establish that agent search improves its starting model. Across its three accepted repeats,
selected-model sealed pearson_delta is **0.723882 ± 0.005414 (mean ± sample SD)**. The primary gain over the
ridge additive start is **+0.007758 ± 0.005414 across repeats**; the plan's arm SE is 0.005594 and its
decision threshold is 0.011780. The gain is below that threshold. B1's combined model remains the delivered
Norman model because its visible-validation score is higher. No model was chosen by a sealed score.

This is verification of existing results, not another experiment. No new lab run, API spend, sealed scoring,
data build, main-checkout edit or protected-code change was performed. Claim:
[#8](https://github.com/andresloak100/Gene-Mila/issues/8). Sources are the frozen plan and its dated amendments,
[B2 draft PR #7](https://github.com/andresloak100/Gene-Mila/pull/7) at
`084eaeaaebd0f19aa5def98e42813cfc29c0c528`, B1 draft PR #6, and the Mac's existing logs and run summaries.
The earlier 11 October 21:40 briefing describes an intermediate state, not the state found on arrival.

## Completion and stop history

The original B2 chain stopped at seed 1 on 11 October at 22:38 UTC (exit 247). Its 20-minute search had
finished; the external watchdog killed it during finalization. The plan's 22:50 amendment and 23:00
addendum documented the cause, excluded seed 1, and specified seeds 2 and 3 using `--no-watchdog` with
a 90-minute backstop. The resume log records both passing and completion at 23:39 UTC; the reading log
records completion at 23:41 UTC. The accepted arm is exactly r0, r2, r3, all on `ce1b53043125cad78d060d1155e5ffe6efab5c0a`,
split `split_a391fa9e7b4eccb7`, with unchanged planners. Seed 1 stays separate and decides nothing.

At verification, no lab process was active, STOP was present, and the shared DeepSeek ledger read
**$43.589781152** (planner $15.696982400; workers $27.892798752), unchanged from completion. B2 cost
$5.505436 by the ledger, including seed 1. These are ledger amounts, not independently verified bills.
The main checkout is now `4562af5b`, following the prior owner's recorded 23:58 lifting of the pin;
this verification did not change it.

## Run readings

Every run path below is under `/Users/andresarriaga/Documents/Mila/Gene-Mila/gene-mila/`.
For this table, `rS` abbreviates `runs/norman_ds_addstart_w4_rS`; `control` is
`runs/norman_control_addstart_w4_r0`. Each run has a `summary.json` archived under `docs/mac/<run>/`
in PR #7. The paired readings are `docs/results/norman_b2_{r0,r2,r3,control}_sealed_reading.{md,json}`,
the separate `norman_b2_r1_killed_sealed_reading.{md,json}`, and the three
`norman_b2_r{0,2,3}_versus_control.{md,json}` files at that PR's head.

The primary start is **baseline_ridge_additive, EXP_0007, 0.716124**. The analytic additive reference is
**EXP_0003, 0.712592**. They are different references. All ± values in the following table are **paired
standard errors over perturbations**, not standard deviations over repeated runs.

| Run | Selected model | Sealed pearson_delta | Gain vs start ± paired SE | Gain vs additive ± paired SE | Gain vs control ± paired SE | Ledger cost |
|---|---|---:|---:|---:|---:|---:|
| control | EXP_0157 | 0.718805 | +0.002681 ± 0.006860 | +0.006213 ± 0.006933 | — | $0 |
| r0 | EXP_0724 | 0.721601 | +0.005477 ± 0.001945 | +0.009009 ± 0.001847 | +0.002796 ± 0.006367 | $1.292618 |
| r2 | EXP_0715 | 0.719982 | +0.003858 ± 0.002177 | +0.007390 ± 0.001691 | +0.001177 ± 0.006172 | $1.369457 |
| r3 | EXP_0625 | 0.730063 | +0.013939 ± 0.006532 | +0.017471 ± 0.007046 | +0.011259 ± 0.008515 | $1.194029 |
| r1: watchdog-killed, excluded | EXP_0875 | 0.727402* | +0.011278 ± 0.004464 | +0.014810 ± 0.003627 | Not prescribed | $1.649332 |

Under the per-run rule, r0 and r3 pass against their start; r2 does not. All three pass against the analytic
additive reference, and none passes against the control. The control passes neither comparison.

*Seed 1 provenance: its reading records `stored_sealed_pearson_delta: null` for EXP_0875 and identifies
that selected model and EXP_0007 as first sealed-scored by the reading. Its 0.727402 therefore comes from
the saved reading, not a stored end-of-run selected-model score. The earlier account of five queries before
the kill must not be taken to mean the selected model was one of those five. Its generated reading body
and clean planner record do not record the watchdog kill; the filename, separate watchdog log, stop record
and plan establish its exclusion. It must never be pooled merely because `summary.json` exists.

## Arm readings and repeat spread

These are the saved `norman_b2_arm_vs_{start,additive,control}.{md,json}` and
`norman_b2_arm_r0_r2_vs_start_reported.{md,json}` outputs. Independent recomputation reproduced the
selected-model means and sample SDs, G, S and arm SE. All input SHA256 references in the four arm JSONs
match the actual stored input JSONs. Sample SD uses ddof=1. The arm SE combines perturbation uncertainty
and variation across repeats by the pre-specified rule; it is not the repeat SD.

| Comparison | Mean gain ± sample SD over repeats | Arm SE | k × SE threshold | Wins | Pre-specified reading |
|---|---:|---:|---:|---:|---|
| r0/r2/r3 vs start — primary | +0.007758 ± 0.005414 | 0.005594 | 0.011780 | 110/168 | No difference established |
| r0/r2/r3 vs additive — secondary | +0.011290 ± 0.005414 | 0.005265 | 0.011267 | 117/168 | Narrow pass |
| r0/r2/r3 vs control — secondary | +0.005077 ± 0.005414 | 0.009507 | 0.019104 | 86/168 | No difference established |
| Original r0/r2 vs start — descriptive only | +0.004667 ± 0.001145 | 0.002673 | 0.005392 | 74/112 | No difference established |

The secondary additive pass exceeds its threshold by only 0.00002253. The original-jackknife sensitivity
reported alongside it is null (threshold 0.012179). This fragile secondary result does not override the
primary null result.

| B2 selected-model metric | Mean ± sample SD, r0/r2/r3 |
|---|---:|
| pearson_delta | 0.723882 ± 0.005414 |
| MSE_DE | 0.119552 ± 0.021739 |
| PCC_DE | 0.931425 ± 0.010875 |
| R²_DE | 0.828320 ± 0.026850 |

## Four combined-model readings and delivery

Every `norman_b2_combined_vs_{start,control,additive,b1_combined}.{md,json}` uses exactly the three
accepted members. Their plain average scores **0.726914** sealed. It is one combined model, so its paired
comparisons below are not repeat means or repeat SDs.

| Combined B2 against | Gain ± paired SE | Wins | Secondary reading |
|---|---:|---:|---|
| Ridge additive start | +0.010790 ± 0.002393 | 44/56 | Passes |
| Control | +0.008109 ± 0.006303 | 34/56 | No difference established |
| Analytic additive rule | +0.014322 ± 0.002507 | 45/56 | Passes |
| B1 combined | +0.004017 ± 0.005960 | 32/56 | No difference established |

The delivery rule compares only the same 63 visible-validation perturbations: **B1 0.780139; B2 0.750482**.
Deliver B1, the equal average of `runs/norman_ds_from_n2_w4_r1:EXP_0681`,
`runs/norman_ds_from_n2_w4_r2:EXP_0729`, and `runs/norman_ds_from_n2_w4_r3:EXP_0519`.
B1's individual repeats score **0.718780 ± 0.007325 (mean ± sample SD)**; their primary gain over their start
is −0.000022 ± 0.007325 across repeats (arm SE 0.007067), not established. Its combined model scores 0.722897
sealed, +0.004095 ± 0.001133 paired SE over N2, and +0.010305 ± 0.006584 over the additive rule (not established).
Sources: PR #6's B1 arm/combined readings and PR #7's combined B2-versus-B1 reading.

The repeat-mean DE metrics above come from the selected models' own stored end-of-run scores. The
combined-model paired-query DE numbers use a different reporting context and should not be substituted
into that repeat-mean table. Neither block supports a claim of beating CellForge. The plan treats subsequent
comparisons on Norman's repeatedly scored sealed set as descriptive.

## Artifact integrity and readiness

**Needs one checksum correction before checksum-complete archival approval.** At PR #7 head `084eaea`,
all 58 archived source files matched their Mac originals byte for byte before the verification appended to
the live state. Of the 58 entries in `docs/mac/MD5SUMS_b2.txt`, 57 match. The only mismatch is `STATE.md`:

- Recorded: `6062179a6d0b0e9f47e51bb0798e5b44`.
- Actual archived file: `f4236da549cfeb39e50f56cf1eb6f3af`.
- Cause reproduced: the recorded hash matches the state file through its 23:50 entry; PR #7 also contains
  the 23:58 entry. All results, configurations, summaries and evidence logs pass their checksums.

Correct the STATE.md line to the actual archived hash when PR #7 is integrated. If the newer state from
this verification is integrated as well, regenerate that line for the final state file. This is a mutable
state-document checksum, not a changed scientific result. Another agent's branch was not modified.

All 59 PR #7 changed files, including the checksum list, were scanned for `sk-` keys of at least 16
characters, GitHub token prefixes, AWS access-key patterns and private-key headers: zero matches.
The PR contains only `docs/results/` and `docs/mac/` paths; no data, runs or databases. This is a pattern
scan, not a guarantee that every possible credential format is detectable.

Validation commands: `python handoff_state.py --fetch` in the separate clone at lab head `051f71d`
succeeded and found no live lab process plus STOP. Its default run/ledger paths point into that data-free
clone, so the real shared ledger was checked separately via a read-only SQLite connection. The required
`nice -n 19 python -m pytest -q` passed: **435 passed, 2 skipped in 800.55 s**. This was the initial
lab-head baseline suite in the own clone; the separate reporting patch is tested separately.

## Completed improvements and next step

B3 was dropped from this block by the dated plan after the r1 stop. STOP remains in place; no B3 build
or run starts. Andres subsequently authorized careful GitHub improvements and a test boundary with a
complete handoff. The bounded free changes are now reviewable:

- [PR #12](https://github.com/andresloak100/Gene-Mila/pull/12), claim #9, fixes stop-evidence reporting;
  full suite 445 passed, 2 skipped. It does not change scientific membership or historical outputs.
- [PR #13](https://github.com/andresloak100/Gene-Mila/pull/13), claim #11, removes explicit sealed-score
  feedback from continuation metadata/planner requests; full suite 440 passed. It also records the
  frozen B1 multi-metric evidence, member/source hashes and prospective isolated-evaluation protocol.
  This removes a feedback path but does not undo old exposure or establish a filesystem boundary.

Andres later requested credential use; no new paid experiment was specified or started, and no
credential value was copied into tools or artifacts. Reopening B3, raising the cap or changing protected
code still requires an explicit decision. Main checkout, STOP and existing run/data files remain unchanged.

The next agent should read current HANDOFF section 1 and PR #13's `docs/FROZEN_TEST_PLAN.md`, claim a
new own-branch task, audit external cohort target/guide eligibility without response labels, and
implement a verified frozen inference adapter with synthetic checks. A separate evaluator account/host
is needed for the requested inaccessible test; Andres has been asked which to use. No fresh clean test
or CellForge superiority is claimed. The synchronized Mac state in this PR records the latest milestone.
