# Untouched test readiness — 13 October 2026

**Status: preparation completed; no new model evaluation.** Neither candidate has a verified eligible
condition/control manifest, and no evaluator boundary exists. Do not report an accuracy result from
this work. Claim [#22](https://github.com/andresloak100/Gene-Mila/issues/22), own branch
`astra/test-readiness-deepseek`. Andres said “go test” and “use the deepseek agents”; when asked which
separate evaluator account or machine to use, he answered “im not sure”. No account changes were made.

The delivered B1 model, selected on visible validation, is unchanged. Its verified frozen package at
`gene-mila-export/runs/norman_frozen_export_20261013/package` is reused. This work inspected frozen
plugin code and knowledge metadata; it did not run inference, fit, score, open private/split files,
read candidate expression or efficacy, or change the existing data. STOP and the main checkout remain.

## What the audit adds

Chat 2 checked primary paper methods/design text, GEO descriptions and paper-linked author repositories.
It found no verified pure exact-condition design manifest in those bounded sources. This is not a claim
that no such manifest exists anywhere. Pacalin still needs exact activation/activation versus
inhibition/inhibition pair assignments, guide loci and matched controls. Replogle experiment 8 still
needs its exact guide/target/control subset. Mixed workbooks and per-cell response-bearing files were
not opened. Sources and the previous verified guide dictionary remain in
[the metadata audit](EXTERNAL_COHORT_METADATA.md).

A separate source-only review verified the frozen package manifest, all selected plugin hashes and
all six knowledge-file hashes against the archived export. The four candidate target names below
are schema-compatible, but their real experimental conditions are unverified.

| Candidate target | Direct frozen Replogle perturbation row | Training-single response | Gene-set memberships | PPI neighbours | Prior-network neighbours |
|---|---|---|---:|---:|---:|
| FAM83A | absent | absent | 5 | 0 | 0 |
| GATA1 | absent | absent | 47 | 7 | 35 |
| MYC | absent | absent | 158 | 19 | 257 |
| YY1 | absent | absent | 61 | 15 | 47 |

Graph neighbour counts are distinct, restricted to the frozen output-gene universe, excluding self.
All four names are in the 2,083-gene universe and absent from the original 231-condition target context.
All four are marked measured **output genes** in the existing Replogle knowledge. That is not the same
as having their own perturbation-response rows. The 85 stored perturbation rows are limited to the
original target context; this audit makes no claim about their presence in the full original screen.

- The selected additive-single feature supplies the same mean-training-single fallback for each of
  these four singleton targets; pairs containing only these names sum two such fallbacks.
- For B1 member r1, seven selected direct-target external features, covering 15 of 24 raw columns,
  return raw zero when all query targets are from these four names. Raw zero does **not** mean a zero
  fitted contribution after frozen centering/scaling.
- Some r2 random-projection features use output-gene profiles across the existing 85 perturbations.
  Their input channel remains available despite absent own-target rows. Annotation and original-control
  features also remain available. No numeric feature values or predictive accuracy were calculated.
- r3's selected residual feature is explicitly zero for new conditions. Some other selected features
  are condition-invariant or use generic fallbacks.
- r2's `pair_target_prior_edge_e34` also has a whole-batch fallback. Preserve the already fixed
  original-anchors-plus-one-new-condition recipe; do not change it after seeing a result.

The [coverage receipt](results/test_readiness_20261013/feature_coverage.json) records sources and the
scope of these statements. Missing inputs must be reported prospectively. They neither prove failure
nor justify changing the frozen package or selecting targets by their eventual outcomes.

## DeepSeek reviews and corrections

The [prospective plan](results/test_readiness_20261013/plan.md), fixed prompts/config and driver hash
were published in commit `d89e822` before any API call. An independent reviewer checked the driver.
Two sequential text-only DeepSeek V4 Pro calls completed, with no retries, fallback or planner.

Run directory: `gene-mila-test-readiness/runs/test_readiness_20261013`.
The [summary](results/test_readiness_20261013/summary.json) and
[usage](results/test_readiness_20261013/usage.json) retain exact token counts and hashes.
Worker cap $0.25; cumulative cap $48; original shared ledger **$43.589781152 → $43.599822392**,
an increment of **$0.01004124** at the repository's unchanged conservative peak rates. This is not a
measured cash charge. There were 3,209 input and 1,466 output tokens in total. These are two advisory
reviews, not model-training repeats or independent biological replicates.

The raw [cohort review](results/test_readiness_20261013/cohort_review.md) and
[protocol review](results/test_readiness_20261013/protocol_review.md) are preserved without rewriting.
Their supported conclusion is that cohort eligibility and access isolation remain unresolved.
The following suggestions/inferences are **not accepted**:

1. Measured output-gene expression under other interventions does not itself establish prior exposure
   to that gene's perturbation. “Thus unseen gene is not cleanly established” does not follow from the
   output-gene channel. Direct target/context absence is verified; broader provenance remains open.
2. The cohort review invented “19 ineligible Pacalin conditions”. The evidence is 19 putative promoter
   **target names**, not 19 rejected conditions. No eligible/rejected observed condition count is known.
3. The protocol review proposes an internal descriptive probe of four names. There are no verified
   matching conditions or labels; predictions on hypothetical target names would not be a performance
   test. No such probe was executed, and it is not a substitute for the requested untouched test.
4. Its shortened member run names omit `norman_ds_from_`. The canonical identities remain the frozen
   receipt, not the generated prose. Its account checklist is advisory; account creation alone proves
   no boundary, and its uncertainty language is not a finalized statistical method.

Validation: **467 passed**, no skips, eight dependency deprecation warnings (657.02 s). Four synthetic
credential/error sanitization cases passed without API calls or shared-ledger writes. Independent
source and runner review, fixed-input hashes, response hashes and ledger arithmetic checks passed.

A first local startup failed before any API request because the new worktree's ignored `runs/` parent
was absent. The parent was created and the unchanged reviewed driver was launched; no run directory
or output was overwritten. Both actual requests completed with `finish_reason=stop`.

## Concrete evaluator setup to review

The current orchestration process is `andresarriaga`, effective UID 501, a member of `admin`.
The proposed `genemilaeval` account does not exist. No sudo/elevation test was performed, and no
permissions were changed. A second standard account is a candidate arrangement, not an isolation claim.

If this Mac is chosen, Andres would create a **Standard** account named `genemilaeval` through
System Settings → Users & Groups → Add User, using a password kept outside agent sessions.
[Apple's account instructions](https://support.apple.com/guide/mac-help/add-a-user-or-group-mchl3e281fc9/mac).
The evaluator's private directory, label files, logs and final report need owner-only access and no
sharing/sync path visible to the orchestration. [Apple's permissions instructions](https://support.apple.com/guide/mac-help/change-permissions-for-files-folders-or-disks-mchlp1203/mac).

Before any test answers arrive, create a harmless sentinel in that private directory from the evaluator
account. From the actual agent/controller identity verify that listing and opening it fail, and inspect
ACLs, group access, shared mounts and available elevation routes. A successful read or available route
means **do not download the answers there**. Because the current orchestration account is an
administrator, its actual elevation routes need review; a non-admin orchestration account or another
machine may be required. Do not remove Andres's admin rights or change accounts automatically.
Keep the evaluator login and storage credentials out of this chat and all agent environments.

Only the target/guide/control projection travels to the prediction side. Frozen predictions, manifests
and hashes travel to the evaluator; response data and reports remain with the evaluator until the
predeclared batch is complete. The same LLM agent must not log in to the evaluator account to inspect
answers while remaining part of the search/orchestration. This document is a setup proposal, not a
permission test or an implemented scoring service.

## Exact next step

1. Obtain a design-only condition/guide/control manifest from the study authors, or have the separate
   evaluator project an allowlist from the supplementary materials. Required columns: source/sample,
   condition ID, guide IDs, target IDs, direction per guide, promoter/enhancer/TSS locus class, dosage
   versus distinct-gene configuration, replicate and matched control IDs. Exclude expression, efficacy,
   DE ranks, embeddings/cell-state labels and response-derived QC. No author message has been sent.
2. Establish the evaluator identity and demonstrate access denial with the harmless sentinel. Record
   the tested identity, paths, permissions and elevation check. Do not open candidate responses before
   this succeeds. Account setup still needs Andres's concrete choice/approval.
3. Resolve source overlap, modality/timing, control alignment, common measured gene panel and the frozen
   missing-feature policy. Fix preprocessing and control/delta handling before outcomes. Do not silently
   compare incompatible normalized expression scales or add new profiles to the model.
4. Freeze the full ensemble/three-members/additive/scripted-reference batch and exact evaluator versions.
   The verified B1 export exists; an external-cohort baseline package and evaluator wiring are not yet
   complete. Specify query budget and a concrete shared-gene uncertainty method from the verified design.
5. Score once on the evaluator side with Pearson delta plus MSE, expression PCC/R², top-20 counterparts
   and direction accuracy, using explicit ranking definitions. Report three members as mean ± sample SD
   and the ensemble separately with appropriate uncertainty. No CellForge superiority claim without
   matched immutable predictions through the same evaluator/preprocessing.

Do not restart B3, repeat the old held-out readings, tune the model from test results, or treat additional
DeepSeek opinions as a replacement for the missing experimental design and access boundary.
