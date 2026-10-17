Review based solely on the fixed facts supplied.

**Readiness assessment:** Neither candidate is now ready for the frozen model’s untouched unseen-perturbation evaluation.

**What the absent direct profiles establish:**  
The four candidate genes are absent from all original 231-context target sets and absent as direct profile keys in the frozen Replogle perts dictionary (`feature_membership_verified`). This establishes only missing direct external target rows for those genes. It does not establish that the candidates are unseen perturbations in the required sense, because the adapter still carries output-gene-side random projection information across 85 existing frozen profile rows, including the four genes as measured output genes (`feature_fallback_nuance`). Thus “unseen gene” is not cleanly established.

**What the known fallbacks establish and do not establish:**  
For r1, seven selected direct-target external features return raw zero when all query targets are from the four genes; raw zero is not standardized zero after frozen centering (`additional_source_audit`). r3 has an explicit zero residual feature for unseen conditions, while random-projection-control features can remain condition-invariant (`additional_source_audit`). r2 has a whole-batch prior-edge fallback, which is why anchors must be preserved (`additional_source_audit`). These facts establish that missing input is a prospective property of the frozen recipe. They do not establish poor accuracy, all-zero predictions, or eligibility to call the test untouched (`feature_fallback_nuance`, `additional_source_audit`).

**Unseen genes vs unseen combinations vs independent-cell replication:**  
The supplied facts do not verify that the Pacalin conditions are pure unseen genes or unseen combinations of known genes. Pacalin has 42 activation and 40 inhibition guides, with 38 other activation guides mapping 19 putative promoter genes whose loci are unverified (`pacalin`). The exact aa/ii/guide/locus/control assignments remain unknown (`pure_metadata_source_search`). Replogle exp8 is mostly same-gene single/dual activating guide dosage/TSS comparisons and is not automatically a distinct gene-pair test (`replogle2020`). Therefore neither candidate currently qualifies as an unseen genetic perturbation or an unseen combination test. Independent-cell replication is also not established because the control/condition/sample/replicate projection is unverified for both sources (`pacalin_conditions`, `replogle2020`).

**Smallest outcome-blind metadata projection required:**  
A pure condition/guide/control/sample/replicate design manifest, without expression, efficacy, DE ranks, or response-derived QC fields (`pacalin_conditions`). For Pacalin this must resolve exact aa/ii composition, guide-to-locus assignment, and controls. For Replogle exp8 it must resolve exact targets and the control subset (`replogle2020`).

**Mandatory exclusions:**  
Exclude any use of response, efficacy, DE ranking, or outcome-based filtering to determine eligibility (`constraints`). Exclude claims that a guide-library title proves condition composition (`pacalin_conditions`). Exclude treating missing direct rows as evidence of poor accuracy (`feature_fallback_nuance`). Exclude the 19 ineligible Pacalin conditions already identified (`pacalin`). Exclude claims that a new account name or hidden files alone isolate the evaluator; actual process-level negative read/list/report and elevation access must be tested (`boundary`).

**One concrete next action:**  
Obtain an author-provided, design-only manifest for Pacalin exact aa/ii/guide/locus/control assignments, or an evaluator-allowlisted projection of the mixed supplement; do not silently open the mixed source (`pure_metadata_source_search`).

**Score now?** No. Without verified pure condition composition and control projection, scoring would not be a trustworthy untouched external test. Eligibility is not established.