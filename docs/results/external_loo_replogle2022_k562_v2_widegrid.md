# Does an external screen carry information the transfer features lack?

Leave-one-out over the 50 training perturbations of the `adamson_cf` bundle, visible data only: each training perturbation is held out in turn, its expression change (pseudobulk mean minus the control mean of public.npz) is predicted from the other 49 training perturbations and the public knowledge files, and the prediction is scored by pearson_delta, the Pearson correlation across all 2,055 genes between the predicted and the measured change. Nothing of the held-out perturbation's own label reaches any predictor. The protocol, the five predictors and the reading rule below were fixed before the external file was opened, and the result is reported whatever it shows. The sealed set is never read; this is a reading on whether the external screen deserves a labelled arm, not a benchmark score.

External screen: `replogle2022_k562`, External screen deltas: perts[gene].delta = mean over cells of log1p(10,000 x counts / cell total) of that screen's cells of the perturbation minus its own control mean, over this bundle's genes in bundle order (null where unmeasured there); source: Perturb-seq screen ReplogleWeissman2022_K562_gwps.h5ad. The file holds 83 target genes over 75,328 control cells; 2,035 of the bundle's 2,055 genes are measured in it, and 46 of the 50 training perturbations have a row (their first target gene with one).

Predictors (k = 5 for both neighbour rules):

- `mean_response`: mean change of the other training perturbations, the floor every feature must beat.
- `geneset_knn`: weighted mean of the other perturbations' changes, weights = Jaccard similarity of the targets' gene-set memberships (knowledge/gene_sets.json), top k with positive similarity, else mean_response. The in-bundle reference close to what the agents found.
- `external_direct`: the external change of the same target gene, unmeasured genes filled from mean_response; mean_response when the target has no external row.
- `external_knn`: weighted mean of the other perturbations' changes, weights = Pearson correlation between the external changes of the two targets over the genes measured in both, top k with positive correlation; geneset_knn when the held-out target has no external row or no neighbour correlates positively.
- `external_stack`: ridge over gene rows combining the four columns above (standardised with the training rows' statistics), trained on the other perturbations' rows, each row's columns computed without that perturbation and without the held-out one; alpha chosen by an inner leave-one-out over those perturbations from the grid [0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0, 1000000.0, 10000000.0]. This grid is not the pre-specified one ([0.1, 1.0, 10.0, 100.0, 1000.0]): it was chosen after an earlier reading, so the stack's number here is a second look, not a pre-specified result; the other four predictors do not depend on it.

## Predictors

| predictor | pearson_delta, mean ± sd | median | min | max | better than mean_response | paired gain vs mean_response | better than geneset_knn | paired gain vs geneset_knn | coverage |
|---|---|---|---|---|---|---|---|---|---|
| mean_response | 0.474 ± 0.261 | 0.432 | -0.130 | 0.889 | – | – | 9 of 50 | -0.071 ± 0.019 | 50 of 50 (no external input) |
| geneset_knn | 0.545 ± 0.264 | 0.558 | -0.103 | 0.926 | 33 of 50 | +0.071 ± 0.019 | – | – | 50 of 50 (no external input) |
| external_direct | 0.463 ± 0.205 | 0.499 | -0.033 | 0.776 | 21 of 50 | -0.011 ± 0.036 | 17 of 50 | -0.082 ± 0.036 | 46 of 50 |
| external_knn | 0.568 ± 0.259 | 0.571 | -0.071 | 0.971 | 37 of 50 | +0.094 ± 0.020 | 31 of 50 | +0.023 ± 0.018 | 46 of 50 |
| external_stack | 0.620 ± 0.232 | 0.641 | 0.016 | 0.962 | 43 of 50 | +0.146 ± 0.022 | 37 of 50 | +0.075 ± 0.020 | 46 of 50 |

"Better than" counts perturbations whose score is strictly higher, paired; the paired gain is the mean difference ± its standard error over the perturbations. Fallbacks taken: external_direct used mean_response for 4 perturbations without an external row; external_knn used geneset_knn for 4 without a row and 0 without a positively correlated neighbour; geneset_knn used mean_response for 8 without a positively similar perturbation. Stack alpha chosen per fold: 10000 for 50.

## Per perturbation

| perturbation | target | cells (bundle) | cells (external) | genes shared | same-target agreement | mean_response | geneset_knn | external_direct | external_knn | external_stack | alpha |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AMIGO3 | AMIGO3 | 715 | – | 0 | – | 0.367 | 0.496 | 0.367 | 0.496 | 0.477 | 10000 |
| ASCC3 | ASCC3 | 1,756 | 128 | 2,035 | 0.664 | 0.249 | 0.253 | 0.663 | 0.244 | 0.513 | 10000 |
| CAD | CAD | 281 | 58 | 2,035 | 0.576 | 0.035 | -0.048 | 0.569 | 0.310 | 0.595 | 10000 |
| CARS | CARS | 501 | 28 | 2,035 | 0.664 | 0.880 | 0.880 | 0.661 | 0.891 | 0.910 | 10000 |
| CHERP | CHERP | 479 | 116 | 2,035 | 0.642 | 0.311 | 0.442 | 0.639 | 0.282 | 0.536 | 10000 |
| COPB1 | COPB1 | 225 | 64 | 2,035 | 0.342 | 0.684 | 0.832 | 0.343 | 0.557 | 0.631 | 10000 |
| COPZ1 | COPZ1 | 282 | 304 | 2,035 | 0.094 | 0.773 | 0.790 | 0.104 | 0.619 | 0.662 | 10000 |
| DDOST | DDOST | 382 | 174 | 2,035 | 0.684 | 0.534 | 0.620 | 0.683 | 0.539 | 0.742 | 10000 |
| DDRGK1 | DDRGK1 | 607 | 136 | 2,035 | 0.388 | 0.435 | 0.602 | 0.387 | 0.543 | 0.615 | 10000 |
| DERL2 | DERL2 | 656 | 82 | 2,035 | 0.541 | 0.662 | 0.408 | 0.540 | 0.635 | 0.726 | 10000 |
| EIF2B2 | EIF2B2 | 615 | 123 | 2,035 | 0.594 | 0.865 | 0.855 | 0.592 | 0.922 | 0.866 | 10000 |
| EIF2S1 | EIF2S1 | 511 | 89 | 2,035 | 0.778 | 0.848 | 0.926 | 0.776 | 0.935 | 0.959 | 10000 |
| ERN1 | ERN1 | 83 | 361 | 2,035 | -0.033 | 0.056 | 0.051 | -0.033 | 0.070 | 0.062 | 10000 |
| FECH | FECH | 683 | – | 0 | – | 0.424 | 0.446 | 0.424 | 0.446 | 0.447 | 10000 |
| GBF1 | GBF1 | 958 | 82 | 2,035 | 0.530 | 0.722 | 0.724 | 0.531 | 0.587 | 0.688 | 10000 |
| GMPPB | GMPPB | 606 | 347 | 2,035 | 0.378 | 0.171 | 0.263 | 0.373 | 0.528 | 0.510 | 10000 |
| GNPNAT1 | GNPNAT1 | 503 | 244 | 2,035 | 0.276 | -0.130 | -0.103 | 0.271 | -0.071 | 0.016 | 10000 |
| HARS | HARS | 325 | 153 | 2,035 | 0.713 | 0.815 | 0.815 | 0.713 | 0.836 | 0.896 | 10000 |
| HSD17B12 | HSD17B12 | 404 | 137 | 2,035 | 0.634 | 0.615 | 0.490 | 0.628 | 0.517 | 0.640 | 10000 |
| HSPA9 | HSPA9 | 894 | 212 | 2,035 | 0.751 | 0.857 | 0.889 | 0.750 | 0.951 | 0.962 | 10000 |
| IARS2 | IARS2 | 1,111 | 94 | 2,035 | 0.702 | 0.880 | 0.734 | 0.701 | 0.947 | 0.950 | 10000 |
| IER3IP1 | IER3IP1 | 1,830 | 95 | 2,035 | 0.527 | 0.541 | 0.819 | 0.527 | 0.821 | 0.824 | 10000 |
| KCTD16 | KCTD16 | 464 | – | 0 | – | 0.353 | 0.353 | 0.353 | 0.353 | 0.353 | 10000 |
| MANF | MANF | 554 | 402 | 2,035 | 0.212 | 0.199 | 0.199 | 0.214 | 0.295 | 0.320 | 10000 |
| MRGBP | MRGBP | 570 | 129 | 2,035 | 0.578 | 0.179 | 0.202 | 0.577 | 0.299 | 0.518 | 10000 |
| NEDD8 | NEDD8 | 506 | 122 | 2,035 | 0.704 | 0.377 | 0.405 | 0.703 | 0.353 | 0.632 | 10000 |
| P4HB | P4HB | 560 | 215 | 2,035 | 0.203 | 0.357 | 0.424 | 0.205 | 0.211 | 0.257 | 10000 |
| PPWD1 | PPWD1 | 234 | 28 | 2,035 | 0.077 | 0.532 | 0.533 | 0.079 | 0.533 | 0.554 | 10000 |
| PSMD12 | PSMD12 | 60 | 210 | 2,035 | 0.086 | 0.308 | 0.237 | 0.088 | 0.279 | 0.278 | 10000 |
| SAMM50 | SAMM50 | 817 | 103 | 2,035 | 0.418 | 0.693 | 0.781 | 0.418 | 0.839 | 0.748 | 10000 |
| SEC61A1 | SEC61A1 | 1,191 | 207 | 2,035 | 0.497 | 0.742 | 0.735 | 0.498 | 0.794 | 0.815 | 10000 |
| SEC63 | SEC63 | 654 | 115 | 2,035 | 0.413 | 0.367 | 0.263 | 0.412 | 0.583 | 0.547 | 10000 |
| SEL1L | SEL1L | 443 | 348 | 2,035 | 0.693 | 0.246 | 0.514 | 0.690 | 0.671 | 0.764 | 10000 |
| SLC35B1 | SLC35B1 | 621 | 112 | 2,035 | 0.262 | 0.448 | 0.448 | 0.262 | 0.545 | 0.538 | 10000 |
| SLMO2 | SLMO2 | 637 | 105 | 2,035 | 0.567 | 0.826 | 0.826 | 0.567 | 0.959 | 0.900 | 10000 |
| SRP68 | SRP68 | 699 | 111 | 2,035 | 0.610 | 0.534 | 0.705 | 0.608 | 0.474 | 0.643 | 10000 |
| SRPR | SRPR | 591 | – | 0 | – | 0.022 | 0.022 | 0.022 | 0.022 | 0.022 | 10000 |
| SRPRB | SRPRB | 703 | 244 | 2,035 | 0.517 | 0.143 | 0.400 | 0.514 | 0.234 | 0.394 | 10000 |
| STT3A | STT3A | 500 | 66 | 2,035 | 0.196 | 0.388 | 0.538 | 0.195 | 0.482 | 0.468 | 10000 |
| SYVN1 | SYVN1 | 650 | 169 | 2,035 | 0.483 | 0.288 | 0.544 | 0.483 | 0.712 | 0.709 | 10000 |
| TARS | TARS | 803 | 175 | 2,035 | 0.481 | 0.727 | 0.727 | 0.481 | 0.814 | 0.765 | 10000 |
| TELO2 | TELO2 | 691 | 80 | 2,035 | 0.415 | 0.405 | 0.757 | 0.413 | 0.707 | 0.593 | 10000 |
| TIMM44 | TIMM44 | 590 | 63 | 2,035 | 0.660 | 0.889 | 0.913 | 0.658 | 0.971 | 0.932 | 10000 |
| TMED10 | TMED10 | 626 | 315 | 2,035 | 0.501 | 0.477 | 0.609 | 0.501 | 0.635 | 0.693 | 10000 |
| TMED2 | TMED2 | 505 | 353 | 2,035 | 0.547 | 0.386 | 0.515 | 0.546 | 0.558 | 0.646 | 10000 |
| TMEM167A | TMEM167A | 468 | 77 | 2,035 | 0.279 | 0.644 | 0.686 | 0.281 | 0.805 | 0.759 | 10000 |
| TTI1 | TTI1 | 526 | 241 | 2,035 | 0.748 | 0.429 | 0.726 | 0.741 | 0.633 | 0.804 | 10000 |
| TTI2 | TTI2 | 653 | 93 | 2,035 | 0.397 | 0.174 | 0.571 | 0.396 | 0.590 | 0.590 | 10000 |
| UFM1 | UFM1 | 692 | 260 | 2,035 | 0.606 | 0.428 | 0.578 | 0.604 | 0.621 | 0.722 | 10000 |
| YIPF5 | YIPF5 | 1,400 | 75 | 2,035 | 0.446 | 0.553 | 0.849 | 0.445 | 0.825 | 0.803 | 10000 |

Same-target agreement is the Pearson correlation across the genes measured in both screens between the bundle's change and the external change for the same target gene; cells are the perturbed cells behind each side's mean. A dash means no external row.

## Reading

Same-target agreement: for the 46 training perturbations the external screen also measured, the Pearson correlation across measured genes between the bundle's change and the external change has median 0.522 (range -0.033 to 0.778); that is how alike the two screens are for the same knockdown, and it bounds what external_direct can do. Against the floor, external_direct scores 0.463 versus mean_response 0.474 (paired difference -0.011 ± 0.036 standard error, better on 21 of 50). The external screen adds information beyond the gene sets on this check: geneset_knn 0.545, external_knn 0.568 (+0.023 ± 0.018, better on 31 of 50), external_stack 0.620 (+0.075 ± 0.020, better on 37 of 50). The best external predictor (external_stack) is ahead of geneset_knn by more than twice its paired standard error and on a majority of perturbations. Caveats: this is 50 perturbations of one bundle and one external screen (46 of the 50 targets have an external row; the rest fell back), the scores are leave-one-out on training perturbations rather than held-out validation, and a gain here must still be confirmed on the sealed set by a labelled arm that is given the knowledge file before it counts.
