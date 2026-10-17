# When the goal is met: the criteria, fixed in advance

Andres, 16 October 2026: "you will decide when we are good to publish something in Nature Genetics or the machine
learning thing; you need to tell me when we have met our goal." This file is that decision rule, written before any
block F score was read, so the call is made by numbers fixed in advance. The Claude session on claim
[#41](https://github.com/andresloak100/Gene-Mila/issues/41) reports against it at every milestone, in
`HANDOFF.md` section 1 and on #41, as "goal met" or "not yet" with the criterion that is missing.

## A. Biology paper (the Nature Genetics path): all of these must hold

1. **Found by the agents.** A feature built from an allowed source (tier 1 of `docs/NOVEL_FEATURE_NEEDS.md` §7), with
   no human hypothesis given to the agents, passes the fair test of `tools/feature_compare.py` under the block's
   pre-registered rule: pooled Holm p ≤ 0.05 against the matched gene-permutation null, mean gain above twice its
   overlap-robust standard error, wins on more than half the perturbations, every fold-seed report positive, a
   gain outside the targets, and `mse_top` not worse; its source reads no perturbation screen.
2. **A named mechanism with a predicted sign**, written down before any replication: what biology the feature
   encodes and the direction its coefficient must have.
3. **Replication** on a second cohort of the matched modality (Adamson CRISPRi, or a Replogle K562 slice that
   excludes Adamson's and Norman's targets), same rule, predicted sign.
4. **A fresh test set held outside the Mac** (`docs/FROZEN_TEST_PLAN.md`), scored once on frozen predictions:
   gain above twice its paired standard error and wins on more than half the perturbations.
5. **A wet-lab confirmation** of a prediction the feature makes and the old model does not: a pre-registered
   experiment on perturbations in no dataset, where the two models disagree most, with matched negatives.
6. **Not already known.** The mechanism of 2 is not established in the literature for this perturbation modality:
   a literature check with citations, written down before the replication of 3, finds no published result that
   already predicts the feature's sign. (Added 2026-10-16 22:05 UTC, after block F's feature-level reading and before
   any replication. It can only make "goal met" harder. The lab's goal of 15 October asks for a feature that is new,
   and 1 to 5 never said so; the first feature to pass 1 encodes a known dependence, see Status.)

Without 5, the result is a strong computational paper (methods-level), not Nature Genetics; it is reported as such.

## B. Machine-learning paper (the comparison, `docs/FEATURE_COMPARISON_PROTOCOL.md`): all five must hold

1. At least three systems ran on the identical task package (ours; a single-agent autoresearch-style loop;
   Biomni), three search seeds each, same wall time and dollar cap; CellForge's translated ideas
   (`docs/comparison/cellforge_c2/`) as a fourth row.
2. Every system's features scored by `tools/feature_compare.py` with the same parent, fold seeds and null.
3. Every system's final model scored once on the fresh test set of A.4.
4. Our arm's mean over seeds beats each baseline on the fresh test by more than twice the paired standard error,
   with wins on more than half the perturbations. If it does not, the paper reports what wins.
5. CellForge's own model run through our evaluator on our split (needs a GPU), or stated as not comparable.

## Status (updated at each milestone)

- 2026-10-16: **not yet**, on either path. A.1 is under test (block F, three Norman runs ended, readings pending).
  A.2 to A.5 and B.1 to B.5 are not met. Blocking both paths: the fresh-test holder (A.4, B.3) and the budget and
  owner for the autoresearch-style and Biomni arms (B.1), both Andres's decisions.

- 2026-10-16 22:05 UTC, block F read (`docs/PLAN_F_GENOME_ANNOTATION.md`; the operator's unedited tables, with every
  run directory, are on [#41](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6224750231)):
  **not yet**, on either path.
  - **A.1 is met at the letter, by one feature family, at the test's resolution limit.** Of the 66 `gene_annotation`
    add-one rows (status ok) from runs `norman_ga_ds_addstart_w4_r0`, `_r2` and `_r3` on Andres's Mac, the 20 ranked
    highest were tested against 1,319 matched gene permutations. Ten pass every criterion with raw p = 1/1320 (no
    permutation matched them), the smallest p the test can give, so their pooled Holm p is 66/1320 = 0.05 exactly.
    Four of the ten read no perturbation screen: additive_response × the targets' mean promoter CpG
    observed/expected, found independently in r0 (e428, e666) and r3 (e412), stage-1 gain 3.7 standard errors; and
    additive_response × a TSS-distance number, once (r0 e541, 3.1 standard errors), whose code ignores chromosome and
    strand and never reads the bidirectional-pair table, so its name is not its mechanism. The other six multiply the
    Replogle screen's response by the same promoter CpG or GC columns: the agents found one thing, from two bases.
  - **A.2 is not met, and the candidate is known biology.** CRISPRa raises highly expressed genes the least, and
    CpG-island promoters are the highly expressed, broadly active class (Konermann et al. 2015; Chavez et al. 2016);
    the feature scales the additive prediction by the targets' promoter class. Known biology predicts a negative
    coefficient; the fitted sign is not yet reported (reading 4). A.6, added now, is therefore the open criterion
    even before A.3 to A.5: no replication, no fresh-test holder, no wet-lab test.
  - **Arm level, descriptive only (the plan makes no sealed arm test):** the F runs' selected models score 0.720,
    0.718 and 0.720 sealed (against the additive rule +0.008 ± 0.002, +0.006 ± 0.002 and +0.008 ± 0.002); B2's
    three runs without the table (`norman_ds_addstart_w4_r0`, `_r2`, `_r3`; `docs/results/norman_b2_*` on PR #7)
    score 0.722, 0.720 and 0.730. The genome table did not raise the sealed score. Reading 3, the out-of-fold arm
    comparison, is running on the Mac.
  - **B.1 to B.5:** unchanged, not met.
  - **Meaning.** The first allowed source gave the agents a feature that passes the fair test and that nobody told
    them to build, but it restates a published dependence: a methods-level result for the comparison paper (the
    system recovers known biology from sequence alone), not a new rule. The biology path continues with block G
    (`docs/PLAN_G_CLEAN_ARM.md`): the curated tier-1 sources together, no screen in the bundle. Block F cost $2.82
    on the ledger (ledger $47.26 after; operator's report on #41).
- 2026-10-16 22:55 UTC, block F readings 3 and 4 in (operator's PR #46, merged: `docs/results/norman_f_readings.md`,
  `norman_f_coefficient_signs.md`): still **not yet**. Out of fold, descriptively, the F arm's selected models score
  0.5805 ± 0.0023 against B2's 0.5825 ± 0.0081 (mean ± sd over seeds 0, 2, 3): no arm gain. The found CpG family's
  gain over the parent is +0.00056 ± 0.00015 pearson_delta (the TSS-distance row +0.0014 ± 0.0005): detectable, and a
  thousandth of the score. The coefficient of the CpG term in the runs' own fits was +0.0147 (r0 e428), +0.0143
  (r0 e666) and −0.0100 (r3 e412), each conditional on that model's other columns; the add-one coefficient of the fair
  test is not saved. No sign can be stated, so A.2 stays unmet and the mechanism stays "known biology, direction not
  tested here".
- 2026-10-16 23:40 UTC, correction after the lead's review (`docs/ROADMAP.md`, section 1): **A.1 is not met; it is
  pending a corrected test.** The entry of 22:05 UTC above is withdrawn on two points. First, the gene-permutation
  null of `tools/feature_compare.py` cannot fail for a feature that is a parent column times a per-perturbation
  number: permuting the product across genes scrambles the additive_response factor the parent already holds, so the
  null gain is a spike at zero (null sd 0.00001 against the observed 0.00056), and 14 of the 20 tested rows, a random
  projection among them, hit the same p floor (`docs/results/norman_f_stage2/feature_compare.json`). Second, with
  20·m − 1 replicates the smallest pooled Holm p equals the 0.05 cutoff by construction, so "found" was a flag for "no
  replicate exceeded", not a p-value; that rule was this session's amendment of 04:20 UTC, and the error is its. The
  tool gets a perturbation-level null and a family-wise max-gain correction before any block G score is read, and
  block F's stage 2 is re-read under it (ROADMAP D2). Everything else above stands: known biology, mixed signs, no arm
  gain, not yet on either path.
- 2026-10-17 02:00 UTC: Andres says a collaborating lab would do the wet-lab step given solid data and good evidence
  (#41), so A.5 is reachable; the computational case (A.1 to A.4, A.6) and the prediction package are what we owe.
  Still **not yet** on either path: no candidate exists.
- 2026-10-17 15:30 UTC, block G, Adamson half read (operator's readings on
  [#51](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6233130270), tool at `2f2e683`, the corrected
  fair test; runs `adamson_cf_g1_ds_w4_r0`, `_r2`, `_r3` and the `g0` controls on Andres's Mac): still **not yet**.
  - **A.1 on Adamson is not met.** 221 add-one rows that read the genome, constraint or protein table, from the three
    G1 runs, were tested at 999 replicates under both nulls with the family-wise correction (210 unique predictions);
    none passes. Twenty-three further plugins could not be scored (missing keys, constant features, literal caps) and
    are listed, not repaired.
  - **Descriptive:** the arm with the tables scored lower out of fold than the arm without them, G1 0.491 ± 0.004
    against G0 0.526 ± 0.035 (mean ± sd over seeds 0, 2, 3; no test with three runs a side), and the G1 agents did use
    the tables (reading 4). The worn Adamson sealed set, indicative only: G0 0.566 ± 0.036, G1 0.491 ± 0.069.
  - Norman's family-wise test is running (174 rows, 999 replicates); the block F re-read and the family 8 scoring
    follow. Block G cost $12.97 on the ledger (final ledger $60.23).
