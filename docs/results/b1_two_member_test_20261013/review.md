# Fixed two-member comparison review

Prospective plan `2fc1ab1` was published before any candidate score. This is one fixed r1+r2 average, not a subset or weight search. Diagnostic PR #27 is the dependency; its helper is unchanged.

An independent source/method reviewer found no remaining actionable defect. Both arms share the same 45 original-recipe refits on fold seeds 3/4/5. Candidate arrays are exactly the mean of member 0/1 arrays. Package checks, full gene-hide unions, fresh contexts/module state, original alphas/model seeds, training-only scaling and metadata strata remain in the reviewed base runner. Temporary seed/config overrides restore even after an exception. Configuration records plan, wrapper and parent-launcher hashes and the fixed gate before fitting.

The reviewer identified one parent-timeout reporting issue. It was fixed before publication or fitting: the parent preserves a completed baseline summary byte for byte if candidate scoring times out, and always records an incomplete/timed-out comparison. Two synthetic tests cover timeouts during refits and after completed baseline scoring.

The final focused suite passed **15 tests in 1.39 seconds**: 7 base-runner checks, 6 composition/gate/provenance/global-restoration cases and 2 parent-timeout cases. The implementation agent's original 6 wrapper cases passed in 0.96 seconds. Full suite on the final source passed **482 tests, no skips, 8 dependency deprecation warnings, in 654.28 seconds**. Command: `PYTHONHASHSEED=0 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 nice -n 19 <mainvenv>/bin/python -m pytest -q`. No candidate fits or scores had occurred at this pre-publication review milestone.

No candidate was calculated on diagnosis seeds 0/1/2. A pass is a development screening result on the same cohort after selection; it does not change the delivered B1 package or establish independent validation, a new frozen coefficient model or a CellForge win. No API, private/split reads, protected code/data, main checkout, STOP, permissions or ledger changes.
