# Frozen-model evaluation: prospective requirements, 13 October 2026

Status: proposed protocol, not an executed clean test. Andres asked for a test set the orchestration
cannot access, the best model evaluated against CellForge using Pearson delta and at least three other
metrics, and measures against overfitting if performance drops. He subsequently authorized necessary
GitHub changes with a complete handoff. He subsequently offered a credential and explicitly requested
its use; no credential value is recorded here. No new paid experiment or budget has been specified,
and none has started. Downloads, account changes and PR merges are not part of these changes. Claim: [#11](https://github.com/andresloak100/Gene-Mila/issues/11).

This protocol is prospective for a future untouched cohort. It cannot make the already inspected Norman
or Adamson sets clean again. It does not amend the completed block's frozen reading rules.

## What is fixed now

- Fit and select on development data only. A test set is never fitted, used for selecting alpha/features,
  used to choose the ensemble, or fed back to the exploration planner.
- The currently delivered Norman model is B1's equal-weight average of
  `norman_ds_from_n2_w4_r1:EXP_0681`, `norman_ds_from_n2_w4_r2:EXP_0729`, and
  `norman_ds_from_n2_w4_r3:EXP_0519`. B2 did not replace it because the fixed visible-validation rule
  selected B1. Do not substitute the numerically highest sealed run.
- The [fingerprint and saved evidence](results/norman_b1_frozen_test_review_20261013.json) record member
  identities, selected alphas, base commits, equal weights and SHA256 hashes of fitted artifacts,
  feature-source files and public inputs. Verify those hashes before a future evaluation. This receipt
  is not an exported inference package and does not itself isolate anything.
- Primary metric: mean per-perturbation Pearson correlation of predicted and true changes from control,
  `pearson_delta`. Report MSE, expression PCC, expression R², and their top-20 DE counterparts; also
  report direction accuracy on the top-20 changed genes. Use the protected evaluator's unchanged
  definitions and name the exact gene-ranking definition beside every DE metric.
- Report all pre-specified metrics, including unfavorable results. Report the three constituent models
  as mean ± sample SD across repeats, and the fixed ensemble as one model with appropriately labelled
  perturbation-level uncertainty. Paired SE is not repeat SD. Do not turn secondary metrics into new
  selection objectives after viewing a test result.

## Two different access guarantees

The current code gives worker features public inputs and imposes AST restrictions, but the controller
owns a local `QueryOracle` and its processes share an OS user. This is not a filesystem security boundary.
The explicit continuation-feedback defect is addressed by omitting `best_sealed` in new warm-start
metadata and excluding it from planner context when reading legacy metadata. Historical runs and reports
are preserved; the change does not erase their previous exposure.

To satisfy Andres's stronger requirement, a separate evaluator account or host must hold the new test
labels and resulting sealed report. The orchestration identity must be unable to open those files,
mount their storage, access their service credentials, or read evaluator logs. An API query cap,
`final.max_queries=0`, a hidden filename, or a prompt instruction alone is insufficient. No machine
permissions or existing bundle files are changed by this proposal.

The boundary needs an explicit implementation and review before real use:

1. A development/inference side receives only authorized inputs plus the frozen model and its training
   context. It has no new test expression labels, cell-level responses or DE reference. It may not refit
   estimators, retune alphas, select members, or adjust preprocessing from test responses.
2. A versioned export/prediction adapter validates feature order, gene order, training provenance and
   hashes, then writes immutable predictions with condition IDs and a receipt. None exists yet for a
   genuinely new cohort; `arm_reading.py combine` averages stored same-bundle predictions and is not that
   adapter. Test the adapter first on synthetic data and saved visible predictions, never real test labels.
3. The evaluator validates identity, coverage, dimensions, finite values and hashes; it then invokes the
   existing scoring implementation unchanged. Test response files exist only on this side. A negative
   permissions test from the orchestration identity must demonstrate that label/report reads fail.
4. A fixed evaluation batch contains the frozen ensemble, its three constituent models for repeat
   reporting, the additive rule and the scripted reference. Every submitted model and metric is declared
   before outcomes are released. Preserve the existing oracle's query limits; a separate authorized plan
   must budget the complete batch and its paired comparisons, not create fresh unlimited oracle instances.
5. Release a dated report to the human reviewer after the batch ends. Do not import it into planner
   memory, worker prompts, failure archives, future warm starts or automated exploration decisions.

## Data and comparability gates

No unused real-data bundle was found locally: the available real bundles cover previously developed
Adamson and Norman data, and the downloads are Norman plus the already used Replogle screen. A new split
of these observations is a reused-data sensitivity experiment, not an untouched test. B3 remains dropped
from the previous block. A new cohort must be identified and approved, with its provenance and any target,
guide, cell and study overlap audited without exposing its response labels to the search.

Two external candidates have been identified through primary-source metadata only; neither is approved
or verified untouched. No response files were downloaded or inspected:

| Candidate | Evidence and possible use | Required audit / limitation |
|---|---|---|
| Replogle et al. 2020 direct-capture experiment 8, [GSM4367986](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSM4367986), within GSE146194 | K562 CRISPRa of 49 genes using single versus dual activating guides; processed expression and guide identities are publicly listed. [Primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7416462/). This is distinct from Replogle 2022 CRISPRi. | Primarily single-gene activation with different guide dosage, rather than Norman's gene-pair task. Verify target/guide/source overlap, controls and feature availability; predefine eligible guide configurations. |
| Pacalin, Steinhart et al. CRISPRai Perturb-seq, [GSE220974](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE220974) | Independent K562 experiments using inducible VPR-dSaCas9 activation; 42 single CRISPRa guides in a 19-gene panel. GEO lists CRISPRa single sample S1 and mixed single sample S3. A small CRISPRaa subset also exists among double conditions. [Primary paper](https://www.nature.com/articles/s41587-024-02213-3). | Only CRISPRa-only singles or CRISPRaa pairs with suitable controls are candidates. Exclude mixed activation/repression and CRISPRii. Of 22 designed doubles, 18 are mixed and four unidirectional controls include both aa and ii, implying at most four possible aa conditions; their exact count/identities are unverified. Pair coverage is limited. |

Independent cells do not by themselves test an unseen perturbation. The next audit should use public
study and guide metadata to establish eligible targets and compare those identities with development
and feature-source provenance, without inspecting expression outcomes. The target-only audit inputs are Replogle's Supplementary Table 6 and GEO cell identities, and
Pacalin's Supplementary Tables 1–2, GEO features and guide-call metadata. Build an eligibility manifest
with source/sample, guide identity, target gene set, activation direction, control status, same-gene
dosage versus two-gene intervention, and development/feature-source overlap. Do not inspect expression
or efficacy columns to decide eligibility. Neither cohort is a direct substitute for Norman's held-out
gene-pair task. A failed compatibility audit is a reason to reject a
cohort before scoring, not to change the frozen model after observing its score.

Before any label release, fix cohort inclusion, modality, preprocessing, gene universe, control treatment,
aggregation, target grouping, baseline definitions and inference compatibility. For Norman's overlapping
gene pairs, uncertainty must account for shared genes under a pre-specified method; do not assume all
pairs are independent. A claimed clean test needs a written exposure/overlap audit. Changes to protected
split/evaluation code still require an explicit reviewed proposal and Andres's agreement.

A valid CellForge superiority comparison requires both methods' immutable predictions on this same
locked cohort, through this same evaluator and preprocessing. The published Table 1 is contextual only:
it lacks Pearson delta, its precise evaluation cannot be reconstructed from the inspected release,
and its split and DE documentation differ. We have not located the paper's fixed evaluator or distributed
model weights. Do not invent a matched comparison from the paper's means, compare different metrics as if
identical, or authorize a GPU/paid run implicitly. Sources and existing descriptive numbers are in the
[saved-evaluation review](results/norman_b1_frozen_test_review_20261013.md).

## Frozen adapter implementation notes for the next agent

Repository-only inspection establishes the following constraints; the selected B1 plugins have not yet
been reviewed for new-cohort compatibility:

- `FeatureContext.target_genes()` and feature computation can represent query target identities, but
  `Lab._predict()` only looks up stored `predictions.npz`; it cannot infer new perturbations.
  `pipeline.run()` refits estimators and must not be used as a frozen prediction adapter.
- `models.pkl` contains every fitted alpha-grid estimator, ordered feature columns and `x_mean`/`x_std`.
  The worker prunes `predictions.npz` to the chosen alpha but does not prune `models.pkl`. Resolve the
  estimator against the already frozen `best_alpha`, requiring exactly one match; using index zero from
  a pruned prediction file to index the model list can silently select the wrong estimator.
- Preserve original feature order, gene universe, control context, training responses, knowledge and
  plugin snapshots. Extend only public query target metadata. Disable shared feature caches or use an
  isolated cache keyed by the new metadata. Evaluator-side alignment uses a prospectively fixed common
  gene panel and external-study controls; it must not alter how frozen features are computed.
- First export and validate coefficients, intercept, scaling arrays, feature columns and alpha with
  hashes. Synthetic tests must fail on changed order, ambiguous/missing alpha, missing feature inputs,
  non-finite predictions and hash mismatches, and demonstrate no estimator fitting or selection.
  Reproduce saved visible predictions before considering external data. Freeze the environment/runtime
  versions as part of that verified export; the present fingerprint receipt does not lock them.

## If performance drops

The existing B1 visible-validation-to-held-out Pearson-delta gap is descriptive, not a causal diagnosis.
Possible explanations include adaptive validation reuse, different perturbation difficulty, differing
category composition, feature redundancy and distribution shift. The observed continuation feedback
is a concrete information-flow defect, not proof that it caused a particular score.

Use development data to investigate and compare remedies. Pre-specify a bounded experiment before running
it: gene-grouped outer development folds to measure generalization, inner folds for feature/alpha selection,
multiple fixed seeds, and the unchanged reference recipe. Candidate remedies are feature-count control,
redundancy checks, shrinkage/calibration diagnostics and a fixed limit on adaptive validation checks.
The earlier DE-aware selection change and compact-model audits were not reliably better; do not assume
they now work or repeat closed investigations without a new development-only hypothesis.

The exploration/exploitation allocation stays unchanged until a development-only comparison supports a
different one. A test-score drop must not automatically tune this allocation. Freeze any successful
revision before evaluating it; once a test has informed development, a new superiority/generalization
claim needs another untouched cohort. Null results and worsening metrics remain in the record.

## Exact next steps

1. Review the minimal continuation-feedback fix and the saved-evidence report in this draft PR. Exact
   check results and publication links live in HANDOFF section 1. Do not deploy into the main checkout
   or alter historical runs; Andres merges.
2. Complete the metadata-only compatibility/exposure audit of the candidates above. Record inclusion
   rules and blockers before acquiring response data. If neither can answer the unseen-perturbation
   question with the frozen predictor, identify a suitable cohort before scoring anything.
3. Obtain approval for the concrete cohort and separate evaluator account/host, then implement and review
   the frozen export/boundary components above with synthetic data and saved visible predictions. No
   download or permissions change has run. The existing-set descriptive evaluation is already reported;
   rescoring the same predictions would add reproducibility evidence, not a new untouched test.
4. Fix the complete evaluation batch, uncertainty rule and access checks before outcomes exist; request
   any required spend/protected-code authorization against that concrete plan. Only then schedule real
   evaluation. If permission or data is unavailable, record the exact blocker and continue only work
   that does not need it.
