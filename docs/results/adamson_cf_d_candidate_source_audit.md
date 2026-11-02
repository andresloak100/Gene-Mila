# Block D: candidate sources and pre-fit signs

The two pooled passes are supervised response-transfer features. Both directly read fold-specific public training responses and gene sets; neither is an annotation-only covariate. The tool marks found_tier1 when a passing plugin lacks the literal Replogle source name. That flag is retained; broader biological source admission and novelty remain the lead's assessment. No new feature was executed or fitted for this audit.

- r0 declares only train_delta in inputs, while its code also calls knowledge(gene_sets). It uses cosine weights, constructs membership vectors only for measured genes, and takes the first perturbation target.
- r3 declares train_delta and gene_sets, uses Jaccard weights and unions all target memberships.
- Both fall back to the current fold's unweighted training-response mean when a target has no usable memberships or positive total similarity. Full-view metadata does not establish per-fold fallback frequency.

The public gene-set file has 5578 sets. All 50 training targets are measured; 43 have membership and a shared set with another training target. The current public-input hashes are recorded in the JSON; these are completion-time hashes, not an invented original pre-score pin.

| Run/feature | Pre-fit record | Predicted sign | Fitted coefficients | Direction check |
|---|---|---|---|---|
| f_r0/train_delta_transfer_similarity_e267 | plan_023.json / EXP_0267 | positive | all six positive | matches |

train_delta_transfer_similarity_e267: Perturbations with similar target gene functions produce similar downstream expression changes.
Plan SHA256: 0c7c500b2cedc868e9e72549cb378be9ab6d37cc6967ba975defb07d5bf4697b. Proposal persisted before the experiment started; raw timestamps and proposal are in the JSON. novel_inputs=[] is preserved.
Derivability record: {"feature": "train_delta_transfer_similarity_e267", "novel_inputs": [], "r2": 0.87}.
| f_r3/gene_set_similarity_transfer_e177 | plan_014.json / EXP_0177 | unknown | all six positive | no predicted direction |

gene_set_similarity_transfer_e177: Perturbations of genes with similar functions (shared gene sets) may produce similar expression changes.
Plan SHA256: a9c1c9a32fd25bc03bdeea5ade959bf20a6e2c491a1b881e97a488827f1b0c20. Proposal persisted before the experiment started; raw timestamps and proposal are in the JSON. novel_inputs=[] is preserved.
Derivability record: {"feature": "gene_set_similarity_transfer_e177", "novel_inputs": [], "r2": 0.848}.

Six coefficients are six ordered fold-seed pairs, not independent search runs. A matching generic transfer mechanism/sign does not establish biological novelty, second-cohort replication, a fresh test or wet-lab validation. No sign is inferred retrospectively for r3.
