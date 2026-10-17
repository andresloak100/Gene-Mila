**Smallest defensible test honor:** Run the fixed frozen ensemble on the four candidate genes only as an *internal, condition-level descriptive probe*, clearly labelled “not an untouched external test.” No new platform is required.

**Evaluator-account proof required before labels:** A separate standard Mac account (`genemilaeval`) must demonstrate, from the actual agent process: (a) negative read/list/report on test-data paths; (b) no membership in elevation/admin groups; (c) no inherited ACL or sharing/sync access; (d) logs showing the agent cannot read evaluator-held files. Account name or hidden-file placement alone is insufficient.

**Fixed model/baseline batch:** Equal-weight ensemble of `EXP_0681 alpha20000`, `EXP_0729 alpha0.00198`, `EXP_0519 alpha300`; merged numeric-only adapter; never fit/select; byte-for-byte stored-prediction reproduction verified. Additive baseline and scripted reference run in one predefined batch.

**Metrics/uncertainty:** Mean per-condition Pearson delta is primary; MSE, expression PCC/R², top-20 DE counterparts, direction accuracy secondary. Report repeat mean ± sample SD across the three members; ensemble point with condition/gene-dependent uncertainty. No tuning from test score.

**CellForge:** Published table lacks Pearson delta; matched cohort/preprocessing/immutable predictions/evaluator unavailable. Published numbers are contextual only; no superiority claim can be made.

**Training repeats vs. independent replicates:** `n2_w4_r1`, `r2`, `r3` are three training-repeat members of one frozen ensemble, not independent test replicates. They estimate member variability only; they cannot supply biological or external-cohort replication.

**Evaluator handoff checklist:**
1. Create `genemilaeval` standard account; verify no admin/elevation.
2. Place test data/answers in evaluator-only paths; disable sharing/sync.
3. From the actual agent process, run negative read/list/report and elevation checks; log results.
4. Predefine batch: frozen ensemble + three members, additive baseline, scripted reference.
5. Fix condition/gene projection from design-only manifest; do not open mixed supplement silently.
6. Run without score queries, private/split reads, expression/efficacy eligibility, new profile insertion, or protected-code changes.
7. Report repeat mean ± sample SD and ensemble point; mark as internal probe unless untouchedness is proven.

**Exact remaining blockers:**
- No verified pure condition/guide/control/sample/replicate projection for Pacalin (`docs/EXTERNAL_COHORT_METADATA.md`, `external_cohort_metadata_20261013.json`).
- No verified Replogle exp8 target/control subset.
- No separate evaluator identity or access-isolation proof.
- No author-provided design-only manifest or allowlisted projection.
- No exposure audit for prior LLM/lab exposure.
- No CellForge matched evaluator.

**Can a new performance score be honestly reported now?** No. The four candidates are not an eligible untouched external cohort; condition composition and evaluator isolation are unverified. Only a clearly labelled internal descriptive probe is defensible.