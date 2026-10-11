# Does an external screen carry information the transfer features lack?

Leave-one-out over the 50 training perturbations of the `adamson_cf` bundle, visible data only: each training perturbation is held out in turn, its expression change (pseudobulk mean minus the control mean of public.npz) is predicted from the other 49 training perturbations and the public knowledge files, and the prediction is scored by pearson_delta, the Pearson correlation across all 2,055 genes between the predicted and the measured change. Nothing of the held-out perturbation's own label reaches any predictor. The protocol, the five predictors and the reading rule below were fixed before the external file was opened, and the result is reported whatever it shows. The sealed set is never read; this is a reading on whether the external screen deserves a labelled arm, not a benchmark score.

External screen: `replogle2022_k562`, External screen deltas: perts[gene].delta = mean over cells of log1p(10,000 x counts / cell total) of that screen's cells of the perturbation minus its own control mean, over this bundle's genes in bundle order (null where unmeasured there); source: Perturb-seq screen ReplogleWeissman2022_K562_gwps.h5ad.. The file holds 82 target genes over 75,328 control cells; 1,938 of the bundle's 2,055 genes are measured in it, and 46 of the 50 training perturbations have a row (their first target gene with one).

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
| external_direct | 0.461 ± 0.211 | 0.504 | -0.015 | 0.826 | 21 of 50 | -0.013 ± 0.035 | 17 of 50 | -0.084 ± 0.035 | 46 of 50 |
| external_knn | 0.572 ± 0.257 | 0.590 | -0.075 | 0.966 | 36 of 50 | +0.098 ± 0.020 | 31 of 50 | +0.027 ± 0.017 | 46 of 50 |
| external_stack | 0.616 ± 0.233 | 0.642 | 0.009 | 0.959 | 41 of 50 | +0.142 ± 0.022 | 34 of 50 | +0.072 ± 0.020 | 46 of 50 |

"Better than" counts perturbations whose score is strictly higher, paired; the paired gain is the mean difference ± its standard error over the perturbations. Fallbacks taken: external_direct used mean_response for 4 perturbations without an external row; external_knn used geneset_knn for 4 without a row and 0 without a positively correlated neighbour; geneset_knn used mean_response for 8 without a positively similar perturbation. Stack alpha chosen per fold: 1000 for 50.

## Per perturbation

| perturbation | target | cells (bundle) | cells (external) | genes shared | same-target agreement | mean_response | geneset_knn | external_direct | external_knn | external_stack | alpha |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AMIGO3 | AMIGO3 | 715 | – | 0 | – | 0.367 | 0.496 | 0.367 | 0.496 | 0.483 | 1000 |
| ASCC3 | ASCC3 | 1,756 | 128 | 1,938 | 0.658 | 0.249 | 0.253 | 0.650 | 0.244 | 0.496 | 1000 |
| CAD | CAD | 281 | 58 | 1,938 | 0.581 | 0.035 | -0.048 | 0.559 | 0.311 | 0.584 | 1000 |
| CARS | CARS | 501 | 28 | 1,938 | 0.669 | 0.880 | 0.880 | 0.661 | 0.903 | 0.920 | 1000 |
| CHERP | CHERP | 479 | 116 | 1,938 | 0.621 | 0.311 | 0.442 | 0.595 | 0.282 | 0.492 | 1000 |
| COPB1 | COPB1 | 225 | 64 | 1,938 | 0.338 | 0.684 | 0.832 | 0.349 | 0.631 | 0.670 | 1000 |
| COPZ1 | COPZ1 | 282 | 304 | 1,938 | 0.101 | 0.773 | 0.790 | 0.142 | 0.620 | 0.642 | 1000 |
| DDOST | DDOST | 382 | 174 | 1,938 | 0.687 | 0.534 | 0.620 | 0.681 | 0.540 | 0.729 | 1000 |
| DDRGK1 | DDRGK1 | 607 | 136 | 1,938 | 0.387 | 0.435 | 0.602 | 0.387 | 0.542 | 0.605 | 1000 |
| DERL2 | DERL2 | 656 | 82 | 1,938 | 0.543 | 0.662 | 0.408 | 0.542 | 0.635 | 0.723 | 1000 |
| EIF2B2 | EIF2B2 | 615 | 123 | 1,938 | 0.594 | 0.865 | 0.855 | 0.589 | 0.935 | 0.880 | 1000 |
| EIF2S1 | EIF2S1 | 511 | 89 | 1,938 | 0.778 | 0.848 | 0.926 | 0.771 | 0.930 | 0.958 | 1000 |
| ERN1 | ERN1 | 83 | 361 | 1,938 | -0.030 | 0.056 | 0.051 | -0.015 | 0.069 | 0.062 | 1000 |
| FECH | FECH | 683 | 6 | 1,938 | 0.109 | 0.424 | 0.446 | 0.113 | 0.476 | 0.420 | 1000 |
| GBF1 | GBF1 | 958 | 82 | 1,938 | 0.529 | 0.722 | 0.724 | 0.531 | 0.638 | 0.705 | 1000 |
| GMPPB | GMPPB | 606 | 347 | 1,938 | 0.387 | 0.171 | 0.263 | 0.374 | 0.528 | 0.528 | 1000 |
| GNPNAT1 | GNPNAT1 | 503 | 244 | 1,938 | 0.276 | -0.130 | -0.103 | 0.244 | -0.075 | 0.009 | 1000 |
| HARS | HARS | 325 | 153 | 1,938 | 0.712 | 0.815 | 0.815 | 0.705 | 0.848 | 0.891 | 1000 |
| HSD17B12 | HSD17B12 | 404 | 137 | 1,938 | 0.633 | 0.615 | 0.490 | 0.620 | 0.511 | 0.617 | 1000 |
| HSPA9 | HSPA9 | 894 | 212 | 1,938 | 0.752 | 0.857 | 0.889 | 0.745 | 0.941 | 0.959 | 1000 |
| IARS2 | IARS2 | 1,111 | 94 | 1,938 | 0.700 | 0.880 | 0.734 | 0.695 | 0.951 | 0.953 | 1000 |
| IER3IP1 | IER3IP1 | 1,830 | 95 | 1,938 | 0.527 | 0.541 | 0.819 | 0.525 | 0.821 | 0.811 | 1000 |
| KCTD16 | KCTD16 | 464 | – | 0 | – | 0.353 | 0.353 | 0.353 | 0.353 | 0.353 | 1000 |
| MANF | MANF | 554 | 402 | 1,938 | 0.214 | 0.199 | 0.199 | 0.203 | 0.295 | 0.321 | 1000 |
| MRGBP | MRGBP | 570 | 129 | 1,938 | 0.579 | 0.179 | 0.202 | 0.568 | 0.299 | 0.510 | 1000 |
| NEDD8 | NEDD8 | 506 | 122 | 1,938 | 0.705 | 0.377 | 0.405 | 0.694 | 0.376 | 0.642 | 1000 |
| P4HB | P4HB | 560 | 215 | 1,938 | 0.210 | 0.357 | 0.424 | 0.218 | 0.211 | 0.244 | 1000 |
| PPWD1 | PPWD1 | 234 | 28 | 1,938 | 0.072 | 0.532 | 0.533 | 0.083 | 0.532 | 0.547 | 1000 |
| PSMD12 | PSMD12 | 60 | 210 | 1,938 | 0.099 | 0.308 | 0.237 | 0.110 | 0.279 | 0.280 | 1000 |
| SAMM50 | SAMM50 | 817 | 103 | 1,938 | 0.419 | 0.693 | 0.781 | 0.418 | 0.815 | 0.746 | 1000 |
| SEC61A1 | SEC61A1 | 1,191 | 207 | 1,938 | 0.497 | 0.742 | 0.735 | 0.509 | 0.794 | 0.811 | 1000 |
| SEC63 | SEC63 | 654 | 115 | 1,938 | 0.414 | 0.367 | 0.263 | 0.406 | 0.583 | 0.555 | 1000 |
| SEL1L | SEL1L | 443 | 348 | 1,938 | 0.701 | 0.246 | 0.514 | 0.681 | 0.671 | 0.771 | 1000 |
| SLC35B1 | SLC35B1 | 621 | 112 | 1,938 | 0.269 | 0.448 | 0.448 | 0.267 | 0.544 | 0.528 | 1000 |
| SLMO2 | SLMO2 | 637 | – | 0 | – | 0.826 | 0.826 | 0.826 | 0.826 | 0.826 | 1000 |
| SRP68 | SRP68 | 699 | 111 | 1,938 | 0.609 | 0.534 | 0.705 | 0.601 | 0.506 | 0.640 | 1000 |
| SRPR | SRPR | 591 | – | 0 | – | 0.022 | 0.022 | 0.022 | 0.022 | 0.022 | 1000 |
| SRPRB | SRPRB | 703 | 244 | 1,938 | 0.520 | 0.143 | 0.400 | 0.507 | 0.235 | 0.381 | 1000 |
| STT3A | STT3A | 500 | 66 | 1,938 | 0.203 | 0.388 | 0.538 | 0.205 | 0.487 | 0.468 | 1000 |
| SYVN1 | SYVN1 | 650 | 169 | 1,938 | 0.497 | 0.288 | 0.544 | 0.490 | 0.711 | 0.719 | 1000 |
| TARS | TARS | 803 | 175 | 1,938 | 0.476 | 0.727 | 0.727 | 0.477 | 0.819 | 0.776 | 1000 |
| TELO2 | TELO2 | 691 | 80 | 1,938 | 0.410 | 0.405 | 0.757 | 0.407 | 0.707 | 0.590 | 1000 |
| TIMM44 | TIMM44 | 590 | 63 | 1,938 | 0.660 | 0.889 | 0.913 | 0.656 | 0.966 | 0.933 | 1000 |
| TMED10 | TMED10 | 626 | 315 | 1,938 | 0.508 | 0.477 | 0.609 | 0.500 | 0.635 | 0.683 | 1000 |
| TMED2 | TMED2 | 505 | 353 | 1,938 | 0.549 | 0.386 | 0.515 | 0.538 | 0.591 | 0.664 | 1000 |
| TMEM167A | TMEM167A | 468 | 77 | 1,938 | 0.280 | 0.644 | 0.686 | 0.291 | 0.806 | 0.757 | 1000 |
| TTI1 | TTI1 | 526 | 241 | 1,938 | 0.747 | 0.429 | 0.726 | 0.732 | 0.727 | 0.805 | 1000 |
| TTI2 | TTI2 | 653 | 93 | 1,938 | 0.396 | 0.174 | 0.571 | 0.390 | 0.590 | 0.594 | 1000 |
| UFM1 | UFM1 | 692 | 260 | 1,938 | 0.608 | 0.428 | 0.578 | 0.596 | 0.619 | 0.717 | 1000 |
| YIPF5 | YIPF5 | 1,400 | 75 | 1,938 | 0.451 | 0.553 | 0.849 | 0.454 | 0.825 | 0.802 | 1000 |

Same-target agreement is the Pearson correlation across the genes measured in both screens between the bundle's change and the external change for the same target gene; cells are the perturbed cells behind each side's mean. A dash means no external row.

## Reading

Same-target agreement: for the 46 training perturbations the external screen also measured, the Pearson correlation across measured genes between the bundle's change and the external change has median 0.514 (range -0.030 to 0.778); that is how alike the two screens are for the same knockdown, and it bounds what external_direct can do. Against the floor, external_direct scores 0.461 versus mean_response 0.474 (paired difference -0.013 ± 0.035 standard error, better on 21 of 50). The external screen adds information beyond the gene sets on this check: geneset_knn 0.545, external_knn 0.572 (+0.027 ± 0.017, better on 31 of 50), external_stack 0.616 (+0.072 ± 0.020, better on 34 of 50). The best external predictor (external_stack) is ahead of geneset_knn by more than twice its paired standard error and on a majority of perturbations. Caveats: this is 50 perturbations of one bundle and one external screen (46 of the 50 targets have an external row; the rest fell back), the scores are leave-one-out on training perturbations rather than held-out validation, and a gain here must still be confirmed on the sealed set by a labelled arm that is given the knowledge file before it counts.
