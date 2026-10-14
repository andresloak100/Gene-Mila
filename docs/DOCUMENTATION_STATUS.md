# Documentation status and continuation map

Status reviewed 13 October 2026; model-development continuation updated 14 October 00:32 UTC by Astra (Codex). Original documentation claim
[#16](https://github.com/andresloak100/Gene-Mila/issues/16). Andres explicitly requested an up-to-date
README and documentation after authorizing the free frozen-export and development diagnostic work.
This review preserves dated scientific results and distinguishes them from current operational state.

## Start here

1. Read [AGENTS.md](../AGENTS.md) for boundaries and coordination rules.
2. Read [HANDOFF section 1](../HANDOFF.md#1-current-state-whoever-is-working-keeps-this-true) on the
   integration branch for the newest commits, active claims, PRs, check results, budgets and exact next
   step. It takes precedence over an older campaign narrative.
3. Read [README.md](../README.md) for the research question, evidence and free quick start.
4. For Mac activity, read `~/Documents/Mila/Gene-Mila/genemila_scale_logs/STATE.md` and the current
   progress/log tails. The main checkout is separate from takeover worktrees. Keep the STOP marker
   and existing data/runs intact.
5. Inspect the relevant claim and draft PR before creating an own-branch continuation. A draft PR's
   implementation is not installed in the main checkout or integrated merely because it is documented.

## Current scientific and code status

| Topic | Status and source | Meaning for a continuation |
|---|---|---|
| Fixed B1 recipe diagnosis | [PR #27](https://github.com/andresloak100/Gene-Mila/pull/27), [complete findings](https://github.com/andresloak100/Gene-Mila/blob/0e2ec6a/docs/B1_DIAGNOSTIC_RESULTS.md), claim #26 closed; source07a3baa, evidence0e2ec6a; full474 tests passed | Original three recipes were refit under full gene-hide unions on public-training seeds0/1/2. The equal ensemble trails additive; r3 is weak and has high error. This does not rescore the delivered frozen B1. All ten metrics, metadata strata, source audit, independent checks and checksums are archived. Do not screen more subsets on these diagnosis seeds. |
| One fixed B1 two-member screen | [PR #29](https://github.com/andresloak100/Gene-Mila/pull/29), claim #28, prospective plan2fc1ab1, reviewed source5467687; full482 tests passed | Completed 45 shared refits in307.875s. Fixed gate passed: paired Pearson gain+0.125342±0.015775, lower control MSE/top20 MSE; candidate mean errors remain higher than additive. [Complete findings](B1_TWO_MEMBER_RESULTS.md). Same-cohort post-selection screen only, no automatic delivered-model change or CellForge claim. Independent raw and Chat2 statistical checks pass; all outcomes/receipts/checksums are preserved. Current HANDOFF records integration status and the exact continuation. |
| Missing-singleton transfer comparison | [PR #25](https://github.com/andresloak100/Gene-Mila/pull/25), [negative findings](https://github.com/andresloak100/Gene-Mila/blob/3f78618/docs/SINGLETON_TRANSFER_RESULTS.md), claim #24 closed | Negative primary gain (−0.003245 ± 0.001620 sample SD), conditional StageB skipped, no model change. Source/evidence remain an unmerged research record. Do not reopen that grid or run the skipped stage after its outcomes. |
| DeepSeek test-readiness reviews | [PR #23](https://github.com/andresloak100/Gene-Mila/pull/23), [corrected findings](https://github.com/andresloak100/Gene-Mila/blob/645e21d/docs/TEST_READINESS_20261013.md), claim #22 deferred | Two text reviews cost0.01004124 ledgerUSD; raw reviews and corrections are preserved. No test cohort or access boundary is approved. Account setup remains deferred while model research proceeds; never treat the old account-first next step as permission to change accounts or permissions. |
| Adamson campaigns | [README results](../README.md#results-on-adamson), [LAB_STATE](LAB_STATE.md) and dated result reports | The held-out set has been used repeatedly. Its later readings are descriptive. |
| Norman B1/B2 paid block | Complete. Rules and amendments are in [PLAN_AFTER_N4](PLAN_AFTER_N4.md) and [NORMAN_PLAN section 8](NORMAN_PLAN.md#8-log-steps-2-and-3-on-the-mac-11-oct-2026). B1 remains the delivered ensemble by visible validation. | Neither repeated arm establishes a mean gain over its start. B3 was dropped; do not restart it from an old briefing. |
| Saved B1 multi-metric evidence | [Merged PR #13](https://github.com/andresloak100/Gene-Mila/pull/13), `docs/results/norman_b1_frozen_test_review_20261013.{md,json}` | Existing saved evaluation, model/source hashes and explicit unfavorable top-20 error. No fresh untouched test or matched CellForge win is claimed. |
| B1/B2 raw archival reports | [Draft PR #6](https://github.com/andresloak100/Gene-Mila/pull/6) and [draft PR #7](https://github.com/andresloak100/Gene-Mila/pull/7) | Preserve their summaries, configurations and source hashes. Correct PR #7's mutable STATE checksum at integration as documented in PR #10. |
| Independent B2 handoff verification | [Draft PR #10](https://github.com/andresloak100/Gene-Mila/pull/10), claim #8 | Completed verification; no repeat scoring needed. The interrupted r1 remains excluded from the accepted r0/r2/r3 arm. |
| Interrupted-run reporting | [Draft PR #12](https://github.com/andresloak100/Gene-Mila/pull/12), claim #9 | Implemented/tested, pending integration. A stored summary can coexist with external interruption evidence. |
| Continuation aggregate-score feedback | [Merged PR #13](https://github.com/andresloak100/Gene-Mila/pull/13), claim #11 | Merged removal of `best_sealed` from new metadata and legacy planner requests. Old exposure cannot be undone. |
| Fresh test inaccessible to orchestration | Prospective `docs/FROZEN_TEST_PLAN.md` in [merged PR #13](https://github.com/andresloak100/Gene-Mila/pull/13) | The current local oracle shares an OS user with orchestration. A reviewed separate evaluator account/host and compatible untouched cohort are still needed. |
| Frozen inference/export | [Merged PR #19](https://github.com/andresloak100/Gene-Mila/pull/19), [saved verification](https://github.com/andresloak100/Gene-Mila/blob/5ea5d31/docs/results/norman_frozen_export_20261013/report.md), [claim #14](https://github.com/andresloak100/Gene-Mila/issues/14), source `1ec08e6`, archival head `5ea5d31`; 464 tests passed | Merged and verified. All three saved B1 members reproduce bit for bit across 119 original conditions and 2,083 genes; the equal ensemble passes the predeclared tolerance. Anchor-batch recipe and runtime/source pins are explicit. No fresh test, gain, OS isolation, scoring or fitting is claimed. |
| Development-only shrinkage diagnostic | [Unmerged PR #17](https://github.com/andresloak100/Gene-Mila/pull/17), [saved report](https://github.com/andresloak100/Gene-Mila/blob/a699d449050e5aee8def1e9eed848df720b5ce96/docs/results/norman_development_shrinkage_20261013/report.md), [claim #15](https://github.com/andresloak100/Gene-Mila/issues/15). Method plan `fe98ed7` fixed before outcomes; tool `0fbb8ce`, 447 tests passed; archival head `a699d44`. | Tool remains unmerged: no supported calibration benefit, so it is not being integrated under Andres's model-usefulness rule. The free real-data diagnostic completed at `runs/norman_development_shrinkage_20261013` with four built-in features and three fold seeds on the same cohort; no calibration benefit is supported. It does not diagnose B1's larger feature models or change B1. Fold-seed SDs are not independent repeat SDs; no fresh held-out evaluation or API call was made. |
| External cohort compatibility audit | [Merged PR #20](https://github.com/andresloak100/Gene-Mila/pull/20), [audit](https://github.com/andresloak100/Gene-Mila/blob/66ed4c69462b723bf2b800fb8a503ee198cc15c9/docs/EXTERNAL_COHORT_METADATA.md), [claim #18](https://github.com/andresloak100/Gene-Mila/issues/18), chat “2” | Completed target/guide/source audit; no response or efficacy data, cohort approval, fresh test or permissions change. Chat “1” owns the export, README and shared handoff to avoid overlapping runs/edits. |

The integration branch is `claude/autonomous-research-system-3k435s`; there is no `main` branch.
README design PRs #1 and #5 have been merged. This documentation change is based on integration
`3075dc7`; check the current PR state before acting because review/merge status can change.
Andres explicitly authorized merging on 13 October, then narrowed it to useful model-research changes
without overengineering. Chat “1” merged #13/#19/#20 and handles this requested README/current handoff.
The unsuccessful diagnostic #17 and optional reporting #12 remain unmerged. This is bounded authorization;
future agents still follow AGENTS and the current HANDOFF for any new merge/spend/scope decision.
The earlier Astra branches `astra/deepseek-continuation-memory` (`6a3e8a8e`) and
`astra/compact-master-selection` (`74114d43`) were verified on `origin` on 13 October; an older
Mac-only HANDOFF note is superseded by that remote verification. Their existence on GitHub does not mean
their code has been merged into the integration branch.

## How to read older documents

- [LAB_STATE](LAB_STATE.md) preserves the lab owner's 11 October campaign narrative. Its new current
  pointer resolves old “in progress,” upload and branch statements without rewriting the scientific
  history. Active instructions come from current HANDOFF section 1.
- [ARCHITECTURE](ARCHITECTURE.md) preserves design and build notes. Its current pointer supersedes the
  old unavailable-real-data and Welch-reference statements and notes the current 20,000-character
  planner state cap. The stored DE reference and paired top-change subsets are different metric contexts. The
  current pointer records the integrated PR #13 feedback fix while preserving the dated design narrative.
- [PROMPTS](PROMPTS.md) records prompts, templates and reported-run settings with their dates and code
  versions. It is evidence of what ran, not permission to replay an old paid campaign.
- `docs/results/`, `docs/mac/` and `docs/example_run/` contain dated outputs. Preserve those outputs;
  append a separately named verification/report when a new check is needed. A mutable status snapshot
  is not a scientific result, and its checksum must follow its actual final bytes.
- [PLAN_AFTER_N4](PLAN_AFTER_N4.md) is the block fixed before its readings, including dated amendments.
  The original briefing and earlier next-step paragraphs are superseded where those amendments or
  current HANDOFF state say the block finished or a step was dropped.

## Public-face audit in this change

The existing README already contained B1/B2 results from the merged design PR. This change uses a journal-style title, abstract, figure captions, reproducibility/availability statement
and references, following the hierarchy inspected in a [Nature Methods article](https://www.nature.com/articles/s41592-025-02772-6).
It uses GitHub-native Markdown, preserves the existing result tables and figure files, relocates the
Adamson figure into its evidence section, and adds a dated current-status entry point. It repairs
concrete operational instructions: explicit planner selection, a free quick start, realistic test duration, approved-block
budget pointers, the audited external-screen exception and read-only ledger discrepancy preview.
The Adamson table and figure retain archived scores; visible qualifiers identify the two historically
hash-sensitive selected models, so the archived 4-versus-8-worker Welch statement cannot stand as
reproducible accuracy evidence. The CellForge wording records that a fixed Table 1 evaluator was not
located in the inspected release, rather than asserting absence of all evaluation code.
No code, configuration, scientific result, data bundle or figure file is changed. No journal branding or
affiliation is implied; GitHub controls the page typography and theme.

Mechanical validation: `python tools/readme_check.py` checks README links, anchors, commands, flags,
configuration keys, score provenance, sanitizer constraints and the existing SVG assets/profile.
`git diff --check` checks the documentation diff. This is a documentation-only change, so no new lab run
or API call is needed. Final command results and PR links are recorded in the claim and current HANDOFF.

## Maintaining this map

At each milestone, update the two new free tasks above with their actual PR links, verified limits
and acceptance results. Keep the README current-status paragraph concise. Update
HANDOFF section 1 and the Mac state at every milestone; do not present a draft feature as integrated or
turn a successful prediction replay into a new generalization result. A revision still needs a frozen
model and an independently isolated evaluation before a fresh-test claim.
