# Methods note (draft): permutation nulls cannot reject features that rescale an existing prediction

Draft started 2026-10-28 by the lead (claim #41), companion to `docs/PREPRINT_DRAFT.md`. Simulation:
`tools/null_degeneracy_sim.py`, results `docs/results/null_degeneracy_sim/summary.{json,md}`.

## The problem in one paragraph

Feature-discovery pipelines often ask whether an engineered feature adds predictive value to a fixed model by
comparing its out-of-fold gain with a null made by shuffling the feature's values across genes. For one class of
feature that null is degenerate: a feature that is an existing prediction (a column the model already has) multiplied
by one number per perturbation. Shuffling it across genes destroys the existing prediction's shape, so every null copy
gains nothing, and the real feature, which keeps that shape, beats all of them whenever its own gain is positive, even
when the per-perturbation number is pure noise. LLM agents produce this class constantly ("the additive prediction
scaled by the targets' X"), so automated discovery needs a null matched to it: shuffle the per-perturbation number
across perturbations, keeping the shape.

## How we met it

In block F (Norman CRISPRa), agents built the additive prediction scaled by the targets' promoter CpG content in two
of three runs. It passed the pre-registered gene-null test. The gene null's standard deviation was 0.00001, against a
gain of 0.00056; the test could not have failed it. Under a perturbation null it fails (pooled p 0.363;
`docs/results/norman_f_corrected_pooled_holm/pooled_holm.json`).

## Simulation

200 features, each `mean_response` (a column of the fixed parent model) times a pseudo-random number per
perturbation drawn from the perturbation's name and a seed, so none carries information about the response. Each was
scored by `tools/feature_compare.py` out of fold (fold seeds 101 and 102) on a synthetic screen (120 genes, 30
perturbations), against both nulls with 999 replicates. Every pass is a false positive.

| null | false-positive rate at 0.05 | 95% CI (Wilson) |
|---|---:|---|
| gene permutation | 0.285 (57 of 200) | 0.23–0.35 |
| perturbation permutation | 0.09 (18 of 200) | 0.06–0.14 |

Of the 63 features whose out-of-fold gain happened to be positive, 57 passed the gene null: it rejects almost only
the features that hurt. The perturbation null is far closer to its nominal level; at 9 percent with 30 perturbations
it is still somewhat liberal, which is why the lab's corrected rule adds a family-wise step-down and a minimum effect
(gain above max(2 × SE, 0.002)) on top of both nulls (`docs/GOAL_CRITERIA.md` A.1).

## Still to do before submission

- The same simulation at 100 and 300 perturbations, to show how the perturbation null's level approaches 0.05 with
  more perturbations, and the false-positive rate of the full corrected rule (both nulls, step-down, minimum effect).
- Features rescaling other parent columns (additive_response on a pair screen).
- The real-data case and its numbers, and a short literature note on permutation tests for engineered features.
