# Does an external screen carry information the transfer features lack?

Leave-one-out over the 50 training perturbations of the `adamson_cf` bundle, visible data only: each training perturbation is held out in turn, its expression change (pseudobulk mean minus the control mean of public.npz) is predicted from the other 49 training perturbations and the public knowledge files, and the prediction is scored by pearson_delta, the Pearson correlation across all 2,055 genes between the predicted and the measured change. Nothing of the held-out perturbation's own label reaches any predictor. The protocol, the five predictors and the reading rule below were fixed before the external file was opened, and the result is reported whatever it shows. The sealed set is never read; this is a reading on whether the external screen deserves a labelled arm, not a benchmark score.

External screen: `replogle2022_k562`, External screen deltas: perts[gene].delta = mean over cells of log1p(10,000 x counts / cell total) of that screen's cells of the perturbation minus its own control mean, over this bundle's genes in bundle order (null where unmeasured there); source: Perturb-seq screen ReplogleWeissman2022_K562_gwps.h5ad. The file holds 83 target genes over 75,328 control cells; 2,035 of the bundle's 2,055 genes are measured in it, and 46 of the 50 training perturbations have a row (their first target gene with one).

Predictors (k = 5 for both neighbour rules):

- `mean_response`: mean change of the other training perturbations, the floor every feature must beat.
- `geneset_knn`: weighted mean of the other perturbations' changes, weights = Jaccard similarity of the targets' gene-set memberships (knowledge/gene_sets.json), top k with positive similarity, else mean_response. The in-bundle reference close to what the agents found.
- `external_direct`: the external change of the same target gene, unmeasured genes filled from mean_response; mean_response when the target has no external row.
- `external_knn`: weighted mean of the other perturbations' changes, weights = Pearson correlation between the external changes of the two targets over the genes measured in both, top k with positive correlation; geneset_knn when the held-out target has no external row or no neighbour correlates positively.
- `external_stack`: ridge over gene rows combining the four columns above (standardised with the training rows' statistics), trained on the other perturbations' rows, each row's columns computed without that perturbation and without the held-out one; alpha chosen by an inner leave-one-out over those perturbations from the grid [0.1, 1.0, 10.0, 100.0, 1000.0].

## Predictors

| predictor | pearson_delta, mean ± sd | median | min | max | better than mean_response | paired gain vs mean_response | better than geneset_knn | paired gain vs geneset_knn | coverage |
|---|---|---|---|---|---|---|---|---|---|
| mean_response | 0.474 ± 0.261 | 0.432 | -0.130 | 0.889 | – | – | 9 of 50 | -0.071 ± 0.019 | 50 of 50 (no external input) |
| geneset_knn | 0.545 ± 0.264 | 0.558 | -0.103 | 0.926 | 33 of 50 | +0.071 ± 0.019 | – | – | 50 of 50 (no external input) |
| external_direct | 0.463 ± 0.205 | 0.499 | -0.033 | 0.776 | 21 of 50 | -0.011 ± 0.036 | 17 of 50 | -0.082 ± 0.036 | 46 of 50 |
| external_knn | 0.568 ± 0.259 | 0.571 | -0.071 | 0.971 | 37 of 50 | +0.094 ± 0.020 | 31 of 50 | +0.023 ± 0.018 | 46 of 50 |
| external_stack | 0.616 ± 0.231 | 0.630 | 0.022 | 0.964 | 43 of 50 | +0.142 ± 0.022 | 35 of 50 | +0.071 ± 0.021 | 46 of 50 |
| external_krr | 0.590 ± 0.258 | 0.626 | -0.109 | 0.975 | 44 of 50 | +0.116 ± 0.017 | 33 of 50 | +0.045 ± 0.015 | 46 of 50 |
| external_stack_krr | 0.614 ± 0.239 | 0.642 | -0.044 | 0.970 | 41 of 50 | +0.140 ± 0.022 | 34 of 50 | +0.069 ± 0.021 | 46 of 50 |

"Better than" counts perturbations whose score is strictly higher, paired; the paired gain is the mean difference ± its standard error over the perturbations. Fallbacks taken: external_direct used mean_response for 4 perturbations without an external row; external_knn used geneset_knn for 4 without a row and 0 without a positively correlated neighbour; geneset_knn used mean_response for 8 without a positively similar perturbation. Stack alpha chosen per fold: 1000 for 50. The last 2 rows (external_krr, external_stack_krr) were added after the first reading; they are defined and read in the last section.

## Per perturbation

| perturbation | target | cells (bundle) | cells (external) | genes shared | same-target agreement | mean_response | geneset_knn | external_direct | external_knn | external_stack | alpha | external_krr | external_stack_krr | KRR lambda | alpha (stack_krr) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AMIGO3 | AMIGO3 | 715 | – | 0 | – | 0.367 | 0.496 | 0.367 | 0.496 | 0.483 | 1000 | 0.496 | 0.495 | – | 1000 |
| ASCC3 | ASCC3 | 1,756 | 128 | 2,035 | 0.664 | 0.249 | 0.253 | 0.663 | 0.244 | 0.518 | 1000 | 0.316 | 0.558 | 0.3 | 1000 |
| CAD | CAD | 281 | 58 | 2,035 | 0.576 | 0.035 | -0.048 | 0.569 | 0.310 | 0.606 | 1000 | 0.198 | 0.543 | 0.1 | 1000 |
| CARS | CARS | 501 | 28 | 2,035 | 0.664 | 0.880 | 0.880 | 0.661 | 0.891 | 0.908 | 1000 | 0.933 | 0.937 | 0.3 | 1000 |
| CHERP | CHERP | 479 | 116 | 2,035 | 0.642 | 0.311 | 0.442 | 0.639 | 0.282 | 0.527 | 1000 | 0.400 | 0.569 | 0.3 | 1000 |
| COPB1 | COPB1 | 225 | 64 | 2,035 | 0.342 | 0.684 | 0.832 | 0.343 | 0.557 | 0.607 | 1000 | 0.682 | 0.649 | 0.3 | 1000 |
| COPZ1 | COPZ1 | 282 | 304 | 2,035 | 0.094 | 0.773 | 0.790 | 0.104 | 0.619 | 0.622 | 1000 | 0.656 | 0.578 | 0.1 | 1000 |
| DDOST | DDOST | 382 | 174 | 2,035 | 0.684 | 0.534 | 0.620 | 0.683 | 0.539 | 0.725 | 1000 | 0.635 | 0.678 | 0.1 | 1000 |
| DDRGK1 | DDRGK1 | 607 | 136 | 2,035 | 0.388 | 0.435 | 0.602 | 0.387 | 0.543 | 0.601 | 1000 | 0.555 | 0.604 | 0.3 | 1000 |
| DERL2 | DERL2 | 656 | 82 | 2,035 | 0.541 | 0.662 | 0.408 | 0.540 | 0.635 | 0.719 | 1000 | 0.701 | 0.721 | 0.1 | 1000 |
| EIF2B2 | EIF2B2 | 615 | 123 | 2,035 | 0.594 | 0.865 | 0.855 | 0.592 | 0.922 | 0.867 | 1000 | 0.949 | 0.910 | 0.3 | 1000 |
| EIF2S1 | EIF2S1 | 511 | 89 | 2,035 | 0.778 | 0.848 | 0.926 | 0.776 | 0.935 | 0.959 | 1000 | 0.935 | 0.962 | 0.3 | 1000 |
| ERN1 | ERN1 | 83 | 361 | 2,035 | -0.033 | 0.056 | 0.051 | -0.033 | 0.070 | 0.057 | 1000 | 0.061 | 0.047 | 0.3 | 1000 |
| FECH | FECH | 683 | – | 0 | – | 0.424 | 0.446 | 0.424 | 0.446 | 0.447 | 1000 | 0.446 | 0.446 | – | 1000 |
| GBF1 | GBF1 | 958 | 82 | 2,035 | 0.530 | 0.722 | 0.724 | 0.531 | 0.587 | 0.676 | 1000 | 0.753 | 0.740 | 0.1 | 1000 |
| GMPPB | GMPPB | 606 | 347 | 2,035 | 0.378 | 0.171 | 0.263 | 0.373 | 0.528 | 0.529 | 1000 | 0.471 | 0.512 | 0.1 | 1000 |
| GNPNAT1 | GNPNAT1 | 503 | 244 | 2,035 | 0.276 | -0.130 | -0.103 | 0.271 | -0.071 | 0.028 | 1000 | -0.109 | -0.044 | 0.1 | 1000 |
| HARS | HARS | 325 | 153 | 2,035 | 0.713 | 0.815 | 0.815 | 0.713 | 0.836 | 0.895 | 1000 | 0.880 | 0.906 | 0.3 | 1000 |
| HSD17B12 | HSD17B12 | 404 | 137 | 2,035 | 0.634 | 0.615 | 0.490 | 0.628 | 0.517 | 0.631 | 1000 | 0.616 | 0.666 | 0.1 | 1000 |
| HSPA9 | HSPA9 | 894 | 212 | 2,035 | 0.751 | 0.857 | 0.889 | 0.750 | 0.951 | 0.964 | 1000 | 0.952 | 0.970 | 0.3 | 1000 |
| IARS2 | IARS2 | 1,111 | 94 | 2,035 | 0.702 | 0.880 | 0.734 | 0.701 | 0.947 | 0.951 | 1000 | 0.963 | 0.966 | 0.3 | 1000 |
| IER3IP1 | IER3IP1 | 1,830 | 95 | 2,035 | 0.527 | 0.541 | 0.819 | 0.527 | 0.821 | 0.796 | 1000 | 0.657 | 0.609 | 0.1 | 1000 |
| KCTD16 | KCTD16 | 464 | – | 0 | – | 0.353 | 0.353 | 0.353 | 0.353 | 0.353 | 1000 | 0.353 | 0.353 | – | 1000 |
| MANF | MANF | 554 | 402 | 2,035 | 0.212 | 0.199 | 0.199 | 0.214 | 0.295 | 0.329 | 1000 | 0.277 | 0.338 | 0.3 | 1000 |
| MRGBP | MRGBP | 570 | 129 | 2,035 | 0.578 | 0.179 | 0.202 | 0.577 | 0.299 | 0.528 | 1000 | 0.335 | 0.505 | 0.1 | 1000 |
| NEDD8 | NEDD8 | 506 | 122 | 2,035 | 0.704 | 0.377 | 0.405 | 0.703 | 0.353 | 0.629 | 1000 | 0.465 | 0.634 | 0.1 | 1000 |
| P4HB | P4HB | 560 | 215 | 2,035 | 0.203 | 0.357 | 0.424 | 0.205 | 0.211 | 0.240 | 1000 | 0.254 | 0.238 | 0.1 | 1000 |
| PPWD1 | PPWD1 | 234 | 28 | 2,035 | 0.077 | 0.532 | 0.533 | 0.079 | 0.533 | 0.541 | 1000 | 0.573 | 0.476 | 0.3 | 1000 |
| PSMD12 | PSMD12 | 60 | 210 | 2,035 | 0.086 | 0.308 | 0.237 | 0.088 | 0.279 | 0.273 | 1000 | 0.295 | 0.273 | 0.1 | 1000 |
| SAMM50 | SAMM50 | 817 | 103 | 2,035 | 0.418 | 0.693 | 0.781 | 0.418 | 0.839 | 0.753 | 1000 | 0.799 | 0.759 | 0.3 | 1000 |
| SEC61A1 | SEC61A1 | 1,191 | 207 | 2,035 | 0.497 | 0.742 | 0.735 | 0.498 | 0.794 | 0.810 | 1000 | 0.832 | 0.838 | 0.3 | 1000 |
| SEC63 | SEC63 | 654 | 115 | 2,035 | 0.413 | 0.367 | 0.263 | 0.412 | 0.583 | 0.566 | 1000 | 0.574 | 0.610 | 0.1 | 1000 |
| SEL1L | SEL1L | 443 | 348 | 2,035 | 0.693 | 0.246 | 0.514 | 0.690 | 0.671 | 0.778 | 1000 | 0.682 | 0.717 | 0.1 | 1000 |
| SLC35B1 | SLC35B1 | 621 | 112 | 2,035 | 0.262 | 0.448 | 0.448 | 0.262 | 0.545 | 0.515 | 1000 | 0.506 | 0.402 | 0.1 | 1000 |
| SLMO2 | SLMO2 | 637 | 105 | 2,035 | 0.567 | 0.826 | 0.826 | 0.567 | 0.959 | 0.906 | 1000 | 0.934 | 0.916 | 0.3 | 1000 |
| SRP68 | SRP68 | 699 | 111 | 2,035 | 0.610 | 0.534 | 0.705 | 0.608 | 0.474 | 0.636 | 1000 | 0.651 | 0.703 | 0.3 | 1000 |
| SRPR | SRPR | 591 | – | 0 | – | 0.022 | 0.022 | 0.022 | 0.022 | 0.022 | 1000 | 0.022 | 0.022 | – | 1000 |
| SRPRB | SRPRB | 703 | 244 | 2,035 | 0.517 | 0.143 | 0.400 | 0.514 | 0.234 | 0.395 | 1000 | 0.393 | 0.505 | 0.3 | 1000 |
| STT3A | STT3A | 500 | 66 | 2,035 | 0.196 | 0.388 | 0.538 | 0.195 | 0.482 | 0.454 | 1000 | 0.441 | 0.437 | 0.1 | 1000 |
| SYVN1 | SYVN1 | 650 | 169 | 2,035 | 0.483 | 0.288 | 0.544 | 0.483 | 0.712 | 0.713 | 1000 | 0.664 | 0.698 | 0.1 | 1000 |
| TARS | TARS | 803 | 175 | 2,035 | 0.481 | 0.727 | 0.727 | 0.481 | 0.814 | 0.769 | 1000 | 0.800 | 0.781 | 0.3 | 1000 |
| TELO2 | TELO2 | 691 | 80 | 2,035 | 0.415 | 0.405 | 0.757 | 0.413 | 0.707 | 0.579 | 1000 | 0.718 | 0.630 | 0.3 | 1000 |
| TIMM44 | TIMM44 | 590 | 63 | 2,035 | 0.660 | 0.889 | 0.913 | 0.658 | 0.971 | 0.933 | 1000 | 0.975 | 0.956 | 0.3 | 1000 |
| TMED10 | TMED10 | 626 | 315 | 2,035 | 0.501 | 0.477 | 0.609 | 0.501 | 0.635 | 0.680 | 1000 | 0.682 | 0.649 | 0.1 | 1000 |
| TMED2 | TMED2 | 505 | 353 | 2,035 | 0.547 | 0.386 | 0.515 | 0.546 | 0.558 | 0.652 | 1000 | 0.582 | 0.649 | 0.3 | 1000 |
| TMEM167A | TMEM167A | 468 | 77 | 2,035 | 0.279 | 0.644 | 0.686 | 0.281 | 0.805 | 0.734 | 1000 | 0.781 | 0.710 | 0.1 | 1000 |
| TTI1 | TTI1 | 526 | 241 | 2,035 | 0.748 | 0.429 | 0.726 | 0.741 | 0.633 | 0.783 | 1000 | 0.782 | 0.810 | 0.1 | 1000 |
| TTI2 | TTI2 | 653 | 93 | 2,035 | 0.397 | 0.174 | 0.571 | 0.396 | 0.590 | 0.595 | 1000 | 0.586 | 0.613 | 0.1 | 1000 |
| UFM1 | UFM1 | 692 | 260 | 2,035 | 0.606 | 0.428 | 0.578 | 0.604 | 0.621 | 0.720 | 1000 | 0.570 | 0.651 | 0.1 | 1000 |
| YIPF5 | YIPF5 | 1,400 | 75 | 2,035 | 0.446 | 0.553 | 0.849 | 0.445 | 0.825 | 0.784 | 1000 | 0.819 | 0.827 | 0.3 | 1000 |

Same-target agreement is the Pearson correlation across the genes measured in both screens between the bundle's change and the external change for the same target gene; cells are the perturbed cells behind each side's mean. A dash means no external row.

## Reading

Same-target agreement: for the 46 training perturbations the external screen also measured, the Pearson correlation across measured genes between the bundle's change and the external change has median 0.522 (range -0.033 to 0.778); that is how alike the two screens are for the same knockdown, and it bounds what external_direct can do. Against the floor, external_direct scores 0.463 versus mean_response 0.474 (paired difference -0.011 ± 0.036 standard error, better on 21 of 50). The external screen adds information beyond the gene sets on this check: geneset_knn 0.545, external_knn 0.568 (+0.023 ± 0.018, better on 31 of 50), external_stack 0.616 (+0.071 ± 0.021, better on 35 of 50). The best external predictor (external_stack) is ahead of geneset_knn by more than twice its paired standard error and on a majority of perturbations. Caveats: this is 50 perturbations of one bundle and one external screen (46 of the 50 targets have an external row; the rest fell back), the scores are leave-one-out on training perturbations rather than held-out validation, and a gain here must still be confirmed on the sealed set by a labelled arm that is given the knowledge file before it counts.

## Added after the first reading (a second look)

external_krr and external_stack_krr were designed after the first result of this check was seen, to ask whether signed weights on the other perturbations' responses, learned through the external screen, do better than the top-k neighbour weights; their numbers are therefore a second look, not pre-specified results, and the reading above does not rest on them. external_krr is kernel ridge regression through the screen: the mean change of the other training perturbations plus k^T (K + lambda I)^-1 (Y - mean), where K is the Pearson correlation between the external rows of the other training perturbations that have one, k their correlations with the held-out target's row and Y their measured changes, so each response enters with a signed weight; lambda is chosen in every fold by an inner leave-one-out over those perturbations from [0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0] (ties to the larger), and geneset_knn stands in when the held-out target has no external row (4 perturbations) or fewer than 3 other training perturbations have one (0). external_stack_krr is the ridge stack of external_stack over five columns, the four above plus external_krr, each training row's columns (its kernel ridge lambda included) computed without that perturbation and without the held-out one, alpha chosen as for external_stack from the same grid [0.1, 1.0, 10.0, 100.0, 1000.0]. external_krr scores 0.590 against external_knn 0.568 (paired difference +0.022 ± 0.010, more than twice its standard error; better on 29 of 50); external_stack_krr scores 0.614 against external_stack 0.616 (paired difference -0.001 ± 0.007, within twice its standard error; better on 28 of 50). Kernel ridge lambda chosen per fold: 0.1 for 23, 0.3 for 23; five-column stack alpha chosen per fold: 1000 for 50. Like every number here, a gain must still be confirmed on the sealed set by a labelled arm before it counts.
