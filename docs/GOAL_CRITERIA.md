# When the goal is met: the criteria, fixed in advance

Andres, 16 October 2026: "you will decide when we are good to publish something in Nature Genetics or the machine
learning thing; you need to tell me when we have met our goal." This file is that decision rule, written before any
block F score was read, so the call is made by numbers fixed in advance. The Claude session on claim
[#41](https://github.com/andresloak100/Gene-Mila/issues/41) reports against it at every milestone, in
`HANDOFF.md` section 1 and on #41, as "goal met" or "not yet" with the criterion that is missing.

## A. Biology paper (the Nature Genetics path): all five must hold

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
