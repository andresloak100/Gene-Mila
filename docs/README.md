# Documentation map

Every document in this repository, by group, one line each. Documents are listed here; machines, paths
and external URLs are in [HANDOFF.md section 2](../HANDOFF.md#2-where-things-are); commands are in
[USAGE.md](USAGE.md). The live state is always [HANDOFF.md section 1](../HANDOFF.md#1-current-state-whoever-is-working-keeps-this-true)
(and `python handoff_state.py --fetch`), never an older narrative.

## Start here, in this order

0. [BRIEF_FOR_NEW_AGENTS.md](BRIEF_FOR_NEW_AGENTS.md): the plain-language brief for an agent joining the project
   (goals, the biology question, where things stand, how we work, what to take first).
1. [README.md](../README.md): the question, the results on Adamson and Norman, methods, limitations, quick start.
2. [AGENTS.md](../AGENTS.md): the rules every agent follows (secrets, money, the Mac, git, scientific integrity).
3. [HANDOFF.md section 1](../HANDOFF.md#1-current-state-whoever-is-working-keeps-this-true) and
   `python handoff_state.py --fetch`: what runs now, who is active, the ledger, the exact next step.
4. This map.
5. [GOAL_CRITERIA.md](GOAL_CRITERIA.md): when the goal is met, by criteria fixed before any score was read.
6. [ROADMAP.md](ROADMAP.md): the lead's decisions D1 to D13 (17 to 26 October); changed only by dated notes at the end.
7. [USAGE.md](USAGE.md): operational reference (quick start, scaling, data, configuration, providers, run outputs, tools).
8. [ARCHITECTURE.md](ARCHITECTURE.md): the design, with dated corrections at the top.

Before continuing someone else's work, read its claim issue and draft pull request: a draft's implementation is
not integrated merely because a document describes it.

## Protocols

- [FEATURE_COMPARISON_PROTOCOL.md](FEATURE_COMPARISON_PROTOCOL.md): how systems are compared on
  "feature + one fixed linear model", with `tools/feature_compare.py` and the task package.
- [PAPER_COMPARISON.md](PAPER_COMPARISON.md): the skeleton of the comparison paper (goal b): Methods final where the protocol is fixed, Results as a template with placeholders.
- [comparison/](comparison/): the comparison arms' feature plugins live beside their protocol because they are
  pre-registered records: [cellforge_c2/](comparison/cellforge_c2/README.md) (four features translated from
  CellForge's design ideas), [lead_h8_constraint/](comparison/lead_h8_constraint/README.md) (the lead's family-8
  hypothesis), [cellforge_notes.md](comparison/cellforge_notes.md) (what CellForge's public code specifies).
  Tests: `tests/test_cellforge_c2.py`, `tests/test_lead_h8_constraint.py`.
- [NOVEL_FEATURE_NEEDS.md](NOVEL_FEATURE_NEEDS.md): what it takes to find a new biological feature, and what is
  missing (D1 to D6).
- [PROMPTS.md](PROMPTS.md): every prompt, starting feature, control and worker setting the agents were given, by
  date and code version. Evidence of what ran, not permission to replay a paid campaign.

## Live blocks (plans fixed before any run; a change is a new dated section)

- Block G, the clean tier-1 arm: [PLAN_G_CLEAN_ARM.md](PLAN_G_CLEAN_ARM.md), with
  [PREREG_G_KNOWN_BIOLOGY.md](PREREG_G_KNOWN_BIOLOGY.md) and
  [CANDIDATE_LITERATURE_CHECK.md](CANDIDATE_LITERATURE_CHECK.md); Mac scripts and receipts in
  [mac/block_g/](mac/block_g/).
- Block H, the comparison on Adamson: [PLAN_H_COMPARISON.md](PLAN_H_COMPARISON.md); Mac scripts in
  [mac/block_h/](mac/block_h/).
- Plan R, the fresh test (commit, then reveal): [PLAN_R_FRESH_TEST.md](PLAN_R_FRESH_TEST.md), with
  [FROZEN_TEST_PLAN.md](FROZEN_TEST_PLAN.md), [FROZEN_EXPORT.md](FROZEN_EXPORT.md) and
  [EXTERNAL_COHORT_METADATA.md](EXTERNAL_COHORT_METADATA.md).
  [TEST_READINESS_20261013.md](TEST_READINESS_20261013.md): the untouched-test preparation of 13 October (two DeepSeek
  text reviews of fixed metadata; no cohort approved, no model scored); records in
  [results/test_readiness_20261013/](results/test_readiness_20261013/).
- [WETLAB_CANDIDATES.md](WETLAB_CANDIDATES.md): the wet-lab prediction package for pre-registration of ROADMAP D13
  and GOAL_CRITERIA A.5 (`tools/wetlab_candidates.py`).

## Completed blocks (pre-registered plans and their readings; records, never edited)

- Norman N1 to N4: [NORMAN_PLAN.md](NORMAN_PLAN.md) (section 8 is the log); scripts [mac/block_norman_n/](mac/block_norman_n/).
- B1 and B2, the paid block after N4: [PLAN_AFTER_N4.md](PLAN_AFTER_N4.md); scripts [mac/block_after_n4/](mac/block_after_n4/).
  Run records in [mac/README.md](mac/README.md), readings in [results/README.md](results/README.md); Astra's
  verification of the B2 records: [results/b2_handoff_verification_20261013.md](results/b2_handoff_verification_20261013.md).
- B4, one worker against four: [PLAN_B4_SINGLE_WORKER.md](PLAN_B4_SINGLE_WORKER.md); scripts [mac/block_b4/](mac/block_b4/);
  reading [results/b4_existing_readings_20261017.md](results/b4_existing_readings_20261017.md).
- Block F, genome annotation on Norman: [PLAN_F_GENOME_ANNOTATION.md](PLAN_F_GENOME_ANNOTATION.md); scripts
  [mac/block_f/](mac/block_f/); reading [results/norman_f_readings.md](results/norman_f_readings.md).
- Development screens of 13 October ($0, training folds only): [B1_DIAGNOSTIC_PLAN.md](B1_DIAGNOSTIC_PLAN.md) and
  [B1_DIAGNOSTIC_RESULTS.md](B1_DIAGNOSTIC_RESULTS.md); [B1_TWO_MEMBER_PLAN.md](B1_TWO_MEMBER_PLAN.md) and
  [B1_TWO_MEMBER_RESULTS.md](B1_TWO_MEMBER_RESULTS.md). Three more, each rejected by its predeclared gate:
  [B1_NESTED_BLEND_PLAN.md](B1_NESTED_BLEND_PLAN.md) and [B1_NESTED_BLEND_RESULTS.md](B1_NESTED_BLEND_RESULTS.md)
  (one nested error-calibration weight); [B1_R2_REGULARIZATION_PLAN.md](B1_R2_REGULARIZATION_PLAN.md) and
  [B1_R2_REGULARIZATION_RESULTS.md](B1_R2_REGULARIZATION_RESULTS.md) (r2's ridge penalty fixed at 20000);
  [B1_PAIR_BATCH_PLAN.md](B1_PAIR_BATCH_PLAN.md) and [B1_PAIR_BATCH_RESULTS.md](B1_PAIR_BATCH_RESULTS.md) (a per-pair
  fallback in the r2 prior-edge feature). [NORMAN_SHRINKAGE_PLAN.md](NORMAN_SHRINKAGE_PLAN.md): the training-only
  shrinkage diagnostic of four built-in features; its report is
  [results/norman_development_shrinkage_20261013/report.md](results/norman_development_shrinkage_20261013/report.md).
  The singleton-transfer comparison remains in draft PR [#25](https://github.com/andresloak100/Gene-Mila/pull/25).
  These plans stay at the top of `docs/` because `tools/b1_development_diagnostic.py`, `tools/b1_two_member_test.py`,
  `tools/b1_nested_blend.py`, `tools/b1_r2_regularization.py`, `tools/b1_pair_batch_correction.py` and
  `tools/shrinkage_diagnostic.py` hash them by path (`tests/test_b1_two_member_test.py` and the three screens' tests
  check the recorded paths), and code and test files cite `docs/NORMAN_PLAN.md` and `docs/PLAN_AFTER_N4.md` by path.

## Records

- [results/README.md](results/README.md): every result file, by block, with the file to read first.
- [mac/README.md](mac/README.md): what the Mac produced (block scripts, run records, inputs, upload checksums).
- [../tools/README.md](../tools/README.md): every tool, one line each (current instruments, dated one-off readings, drivers).

## History

- [LAB_STATE.md](LAB_STATE.md): the lab-code owner's catch-up narrative to 11 October 2026 (Adamson campaigns,
  the Norman ingest, the feature audits). Its "in progress" statements are history; the live state is HANDOFF section 1.
- [NEXT_LEVER.md](NEXT_LEVER.md): the 11 October analysis of the 0.60 plateau, cited by NOVEL_FEATURE_NEEDS and PLAN_F.
- [example_run/](example_run/README.md): the synthetic example run; CI rebuilds the README's example figure from it.
- [assets/](assets/DESIGN.md): the README's figures and their build script (`build_figures.py`).
- [archive/README.md](archive/README.md): superseded documents, status copies and as-run scripts, with what replaced each.

## The ten root scripts

| Script | What it does | Documented in |
|---|---|---|
| `run_research.py` | start a run (always with `--planner-provider`) | [USAGE: quick start](USAGE.md#quick-start) |
| `prepare_data.py` | build a data bundle (synthetic, Adamson, Norman) | [USAGE: data](USAGE.md#data) |
| `handoff_state.py` | one command for the shared state (`--fetch`) | AGENTS.md "How to coordinate" |
| `status.py`, `leaderboard.py`, `summarize.py` | live state, ranked experiments, the planner's research state | [USAGE: quick start](USAGE.md#quick-start) |
| `analyze_run.py` | worker independence, tokens, cost, bottlenecks (called by the block scripts) | [USAGE: quick start](USAGE.md#quick-start) |
| `reproduce.py` | re-run one experiment from its record | [USAGE: quick start](USAGE.md#quick-start) |
| `results_table.py` | results in CellForge's Table 1 layout, and the calibration against CellForge's numbers | [USAGE: outputs of a run](USAGE.md#outputs-of-a-run-runsid) |
| `scaling_report.py` | the worker-scaling report (`results/scaling.md`) | [USAGE: scaling](USAGE.md#scaling) |

## Checks

CI (`.github/workflows/readme-check.yml`) checks the README, its figures and `tests/test_readme_check.py` only.
Run `python -m pytest -q` locally (about 13 minutes) before every push of code, and `python tools/readme_check.py`
after any change to the public face.
