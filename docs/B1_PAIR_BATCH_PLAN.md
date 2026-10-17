# One per-pair correction to the r2 prior-edge feature

Claim #34, own astra/b1-pair-batch-correction/gene-mila-pair-batch.
Andres continues to request model improvement. Claims30 and32 are closed failures and stay unchanged.
This is a distinct source-correctness hypothesis, identified before the penalty run's outcomes.

## Source evidence and exact correction

Original pair_target_prior_edge_e34 version2 enables correlation fallback only if its whole compute
batch contains no nonzero prior edge. An unmatched pair can therefore change when an unrelated matched
pair joins its batch. AdditiveSinglesTimesPairPriorEdge e401 inherits this dependency.
Metadata-only activation check:3 nonzero matched and38 unmatched public-training pairs;
Claim32 folds14/15 training and7/15 predicted batches mix them. No response/correlation values were
inspected for that check; it establishes activation, not predictive efficacy or a label leak.

Publish a copied e34 version3 with one per-row rule: preserve that row's finite nonzero prior weight;
otherwise use its finite control correlation when both targets exist, else zero. Singletons stay zero.
Missing and zero-weight edges use fallback, matching the original nonzero-match convention and every
row's original standalone behavior. Add control_cells to input metadata and explain the fallback.
No change to parsing, caches, e401 or another feature. Preserve original snapshot/package bytes.

The fresh corrected-r2 snapshot is copied into the exclusive ignored run directory before fitting;
only the one e34 source is replaced by the published variant. Pin original/variant source hashes and
all copied plugin files in config before any fit. Do not install it in the main checkout or deliveredB1.

## Models, permitted views and fixed comparison

Original B1 manifest SHA256:
225adc3079251f3cd17f16999b3bc92ab18ae20e9fcde9ee0617b8f350869b45.
r1 index0 EXP_0681 alpha20000 seed1; r2 index1 EXP_0729 alpha0.00198 seed2.
Original features/parameters/expected columns/seeds, training-only scaling and half/half weights fixed.
The alpha20000 r2 from failedClaim32 is NOT used. All remaining source/kernel/external assumptions persist.

New outer seeds12/13/14 x five existing gene folds over112public-training conditions/2083genes.
Full gene-sharing hide unions, fresh restricted context/modules for every fit, original seed reset.
Preserve train-batch then whole-predicted-fold batch processing; corrected e34 is now row-invariant.
One shared r1, originalr2, correctedr2 per fold:45fits total,7200s parent deadline.
Control E=(r1+originalr2)/2; candidate=(r1+correctedr2)/2; additive on the same allowed training view.
Original/corrected r2 share the same specification; their plugin snapshot differs only in e34.
No hyperparameter/grid/weight/new subset, old-seed candidate scores or extra model fits.

## Fixed advancement screen

All must pass:
1. Candidate-minus-control Pearson delta positive in eachseed; mean>max(0.002, sampleSD).
2. Ratios of across-seed mean candidate/control MSE and top20MSE<=1.01.
3. Ratios of mean candidate/additive MSE and top20MSE<=1.01.

Same ten metrics and metadata strata as B1_DIAGNOSTIC_PLAN; all arms/seeds/strata and paired mean±sampleSD.
Top20 is largest absolute public-development delta, not cell-derived DE. Partition SD is sensitivity
on a historically selected cohort, not independent replication. Practical screening rule, not
significance/noninferiority or fresh-test/CellForge evidence. No difference inside noise is a gain.
Behavioral correctness alone does not establish improved accuracy. Failure closes this candidate
without tuning fallback values, penalties, seeds, features, objectives or margins after outcomes.
Pass nominates independent validation only; original delivered frozenB1 and fullfit package unchanged.

## Implementation, verification and continuation

Root owns plan/parentlauncher/docs/Git/sharedHANDOFF/liveMacSTATE. Implementation agent owns only
new runner, published copied e34 variant and synthetic tests. Reviewer read-only. Existing helper,
core, benchmark/split/guard/data/private/main/STOP remain untouched; no API providers/cost.

Tests must prove matched positive/negative weights preserved; unmatched rows invariant under
batch composition/order; missing/zero edges, missing targets/nonfinite correlations and singleton
handling; e401 composition; only e34 source differs; shared predictions/45fits; actual full-hide
poisoning; exclusive output/prefit source pins; failure/timeout checkpoint preservation; fixed gates.
Independent source/method review plus full nice19 pytest before code push and any real-data fit.

One own-clone/mainvenv/nice19/single-threadBLAS/PYTHONHASHSEED0 process:
python docs/results/b1_pair_batch_20261013/run_with_deadline.py
  --package <absolute original pinned package> --out runs/b1_pair_batch_20261013
No retry/duplicate. Save all arrays, config/source/runtime/input/plugin pins, memberships, progress,
all outcomes/status/errors. Independent raw numerical/provenance verification and Chat2 data-free
arithmetic/report review before advancement. Archive report/all outcomes/receipts/SHA256/MD5 after
key-shaped scan; numeric arrays, copied plugins and package/context stay ignored locally.

Record closed negativeClaims30/32 in README/documentation map and exact current HANDOFF.
Merge only independently reviewed useful change under Andres's standing instruction. If this
candidate fails, preserve its findings separately and do not merge unused research code.
Separate evaluator account/host/cohort setup remains deferred, not approved. A compatible unseen
perturbation comparison is still required before delivered-model/fresh-test claims.
