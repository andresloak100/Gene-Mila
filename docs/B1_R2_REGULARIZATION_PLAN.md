# One fixed r2 ridge penalty

Claim #32; own astra/b1-r2-regularization/gene-mila-r2-regularization.
Andres continues to request model improvement. This distinct free test follows rejected Claim30;
it does not reuse or retune that scalar experiment.

## Fixed hypothesis and inputs

Replace ONLY r2 alpha0.00198 with **20000**, the already fixed r1 penalty. Keep r1, both original
feature recipes/parameters/columns/model seeds, training-only scaling, and half/half composition.
No inner selection, alpha grid, new feature, weight/objective tuning or old-seed candidate scores.

Original r2's penalty is tiny relative to dominant standardized training directions and its errors
are unstable. This motivates a regularization hypothesis, not an established cause or OLS equivalence.
Source audit found whole-batch prior-edge fallback (e34/e401), a kernel not guaranteed PSD (e14),
neighbor behavior at k20 and projection/measurement assumptions. Do not repair these in this test,
claim they are resolved, or alter the prescribed train-then-whole-query-fold batch rule.

Pinned original B1 package: gene-mila-export/runs/norman_frozen_export_20261013/package.
Manifest SHA256:225adc3079251f3cd17f16999b3bc92ab18ae20e9fcde9ee0617b8f350869b45.
r1 index0 EXP_0681/ridge alpha20000/model seed1, r2 index1 EXP_0729/ridge alpha0.00198/model seed2.
The variant deep-copies r2's specification and changes alpha only. Original package/manifest unchanged;
unused r3 remains pinned but is not fit.

## Shared fits and controls

Outer seeds **9,10,11**, five existing gene folds each,112public-training conditions/2083genes.
Full gene-sharing hide unions, fresh restricted contexts/modules per fit, original seed reset,
training batch before complete predicted-fold batch, and training-only scaling via reviewed base helper.

Fit shared r1, original r2 and modified r2 on every fold: **45 fits total**,7200s parent deadline.
Fixed control E=(r1+originalr2)/2; candidate=(r1+modifiedr2)/2; additive uses the same allowed view.
Retain each member as context. All are newly generated; no old-run arrays or held-out scores used.

## Metrics and fixed advancement screen

Same ten metrics/metadata strata as B1_DIAGNOSTIC_PLAN. All metrics/arms/seeds/strata and paired
mean +/- sample SD retained. Top20 is absolute development delta, not cell-derived DE.
Same historically used cohort; partition SD is not independent replication or fresh-test evidence.

All checks must pass:
1. FixedE-minus-candidate all-gene MSE positive in everyseed; mean improvement>its sampleSD.
2. Candidate mean MSE/additive mean and top20MSE/additive mean<=1.01; top20MSE/fixedE mean<=1.01.
3. Candidate-minus-fixedE Pearson>=-.01 in everyseed and mean>=-.002.

Ratios of means, not means of ratios. Practical error/correlation screen, not significance or
noninferiority claims. Being within1% of additive is not beating it. No general multi-metric win
or CellForge claim from one successful metric. Failure closes this block; no more penalties, feature
repairs/seeds/margins after outcomes. Passing nominates a candidate for independent validation,
without automatic new full-training/frozen package or delivered-model promotion.

## Execution and review

Root owns plan/launcher/docs/Git/shared HANDOFF/live MacSTATE. Implementation agent owns only new
tools/b1_r2_regularization.py and tests/test_b1_r2_regularization.py. Reviewer read-only.
Existing reviewed helper/core/protected files unchanged. Publish plan before outcomes and independently
reviewed source/fullpytest before fits. Focused tests must verify alpha-only deep copy/identicalfeatures/
originalseeds, sharedr1/prediction averaging/exact45fits, full hidden-answer poisoning, config/sourcepins
beforefitting, gates, exclusive output/checkpoint/failure and parent timeout.

One own-clone/mainvenv/nice19/PYTHONHASHSEED0/single-thread BLAS process, parent7200s:
python docs/results/b1_r2_regularization_20261013/run_with_deadline.py
  --package <absolute pinned original package> --out runs/b1_r2_regularization_20261013

Exclusive output; preserve config/source/plan/input/runtime hashes beforefits, every fold membership,
all member/ensemble numeric arrays, full summary/progress/status/error and exactcommand. No retries.
Independent raw-array mean/metrics/strata/gate/hash verification; Chat2 data-free statistics review.
Archive all outcomes/reviews/receipts/SHA256/MD5, scanned first. Numeric models/context/arrays stay ignored.

No paid calls, new data, oracle/held-out/private/split reads, protected/data/main/STOP/account changes.
Original B1 remains delivered. Merge only reviewed useful changes under Andres's standing instruction;
preserve negative results separately. Exact Claude continuation stays in current HANDOFF.
