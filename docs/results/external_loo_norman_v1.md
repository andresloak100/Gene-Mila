# External screen leave-one-out, protocol norman_v1

Pre-specified in docs/NORMAN_PLAN.md section 5 and committed before the bundle's expression values were read; the result is reported whatever it shows. Leave-one-out over the 112 training perturbations of the `norman` bundle (71 singles, 41 of two or more genes), visible data only: public.npz, knowledge/targets.json, knowledge/gene_sets.json and the external knowledge file (md5: public.npz 0a08a92953c914620e1ecb6fbc280e7e; knowledge/targets.json 3d2d0315668bd31b7b1949d0c2d3dc68; knowledge/gene_sets.json cc7dcac906639821067cc28d6d69f347; knowledge/replogle2022_k562.json d9eff528143dcd4d72c87393df724084). Holding out a perturbation hides it and, when it is a single, every training pair containing its gene, as on the sealed set; each stack training row is computed under the same rule, without that row and without the held-out perturbation. The primary score is pearson_delta, the Pearson correlation across all 2,083 genes between the predicted and the measured change (pseudobulk mean minus the control mean of public.npz); the secondary score is the same without the perturbation's own target genes. The sealed set is never read; this is a reading on whether the external screen deserves a labelled arm, not a benchmark score.

External screen: `replogle2022_k562`. Its description: CRISPRi screen deltas, sign -1 (this bundle is CRISPRa): perts[gene].delta = mean over cells of log1p(10,000 x counts / cell total) of that screen's cells of the perturbation minus its own control mean, over this bundle's genes in bundle order (null where unmeasured there); source: CRISPRi Perturb-seq screen ReplogleWeissman2022_K562_gwps.h5ad. The screen's modality (CRISPRi) differs from this bundle's (CRISPRa), so a target's response here is expected to point the other way: multiply a target's delta by sign (-1) before using it as that target's predicted change; correlations between rows do not depend on the sign. A perturbation of several genes has a row only when every target has one: the sum of its targets' deltas.

The file holds 85 target genes over 75,328 control cells; 2,028 of the bundle's 2,083 genes are measured in it. A perturbation's external row is the sum of its targets' rows, present only when every target has one (a gene unmeasured in any of them stays unmeasured), with the smallest of its targets' cell counts: 91 of the 112 training perturbations have a row (60 of 71 singles, 31 of 41 pairs). The protocol fixes s = -1 in external_direct (a CRISPRi screen read for a CRISPRa bundle: the same target's response is expected to point the other way); s = +1 is reported only as the diagnostic external_direct_unsigned. The file records sign -1, screen modality CRISPRi, and the bundle's manifest records modality CRISPRa.

## Gate

The comparison is read only if at least half the training perturbations and at least 10 training singles have an external row: 91 of 112 perturbations and 60 singles do, so the gate holds.

## Primary comparison

external_stack against stack_inbundle, paired over the 112 held-out perturbations: external_stack 0.627, stack_inbundle 0.604. Reading rule: a gain counts only if the mean paired gain exceeds twice its paired standard error and the better side wins on more than half the perturbations. The external screen adds information beyond the in-bundle predictors on this check (external_stack minus stack_inbundle +0.023 ± 0.006 paired standard error, external_stack better on 68 and worse on 44 of 112): the gain exceeds twice its paired standard error and external_stack is better on more than half the perturbations.

On the secondary score, without each perturbation's own targets (not the verdict): +0.023 ± 0.006, external_stack better on 69 and worse on 43 of 112 (ahead).

## Predictors (secondary: each against mean_response and geneset_knn)

| predictor | pearson_delta, mean ± sd | median | min | max | better than mean_response | paired gain vs mean_response | better than geneset_knn | paired gain vs geneset_knn | coverage | without own targets, mean |
|---|---|---|---|---|---|---|---|---|---|---|
| mean_response | 0.506 ± 0.328 | 0.609 | -0.593 | 0.855 | – | – | 47 of 112 | -0.038 ± 0.026 | 112 of 112 | 0.511 |
| geneset_knn | 0.545 ± 0.333 | 0.627 | -0.538 | 0.968 | 58 of 112 | +0.038 ± 0.026 | – | – | 112 of 112 | 0.547 |
| additive_singles | 0.578 ± 0.348 | 0.654 | -0.538 | 0.970 | 62 of 112 | +0.072 ± 0.030 | 29 of 112 | +0.033 ± 0.008 | 41 of 112 | 0.580 |
| external_direct | 0.188 ± 0.267 | 0.124 | -0.374 | 0.781 | 14 of 112 | -0.318 ± 0.041 | 16 of 112 | -0.357 ± 0.039 | 91 of 112 | 0.175 |
| external_knn | 0.548 ± 0.345 | 0.648 | -0.452 | 0.968 | 61 of 112 | +0.041 ± 0.031 | 54 of 112 | +0.003 ± 0.020 | 91 of 112 | 0.551 |
| external_krr | 0.617 ± 0.318 | 0.703 | -0.527 | 0.968 | 70 of 112 | +0.110 ± 0.025 | 64 of 112 | +0.072 ± 0.016 | 91 of 112 | 0.620 |
| stack_inbundle | 0.604 ± 0.326 | 0.672 | -0.544 | 0.969 | 67 of 112 | +0.098 ± 0.025 | 87 of 112 | +0.060 ± 0.010 | 112 of 112 | 0.606 |
| external_stack | 0.627 ± 0.319 | 0.699 | -0.539 | 0.970 | 76 of 112 | +0.121 ± 0.025 | 81 of 112 | +0.083 ± 0.013 | 112 of 112 | 0.629 |
| external_direct_unsigned (diagnostic, s = +1) | 0.048 ± 0.323 | -0.017 | -0.504 | 0.781 | 8 of 112 | -0.458 ± 0.035 | 13 of 112 | -0.496 ± 0.038 | 91 of 112 | 0.062 |

Predictors (k = 5 for both neighbour rules): `mean_response`, the mean change of the available training perturbations; `geneset_knn`, the weighted mean of their changes with weights the Jaccard similarity of the union of the targets' gene-set memberships, top k with positive similarity, else mean_response; `additive_singles`, the sum of the targets' singles' changes when the perturbation has several targets and every target's single is available, else geneset_knn; `external_direct`, the perturbation's external row times s = -1, unmeasured genes from mean_response, mean_response without a row; `external_knn`, the weighted mean of the available changes with weights the Pearson correlation between external rows, top k positive, else geneset_knn; `external_krr`, kernel ridge through the screen, mean_response + k^T (K + lambda I)^-1 (Y - mean) over the available perturbations with a row, lambda from [0.01, 0.03, 0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0] by an inner leave-one-out, geneset_knn without a row or with fewer than 3 others; `stack_inbundle`, a ridge over gene rows of mean_response, geneset_knn, additive_singles; `external_stack`, the same over mean_response, geneset_knn, additive_singles, external_direct, external_knn, external_krr. Both stacks standardise with the training rows' statistics and choose alpha by an inner leave-one-out from the fixed grid [0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0, 100000.0, 1000000.0, 10000000.0]. "Better than" counts perturbations whose score is strictly higher, paired; the paired gain is the mean difference ± its standard error. Fallbacks taken: geneset_knn used mean_response for 7; additive_singles used geneset_knn for 71 singles and 0 pairs with a single not available; 21 perturbations had no external row; external_knn found no positively correlated neighbour for 0; external_krr fell back for 21 without a row and 0 with too few others. Alpha chosen per fold, stack_inbundle: 0.1 for 111, 100 for 1; external_stack: 0.1 for 99, 10 for 1, 100 for 4, 1000 for 8. Kernel ridge lambda chosen per fold: 0.1 for 90, 0.3 for 1.

## Strata (secondary, not the verdict)

| stratum | n | with external row | mean_response | geneset_knn | additive_singles | external_direct | external_knn | external_krr | stack_inbundle | external_stack | external_direct_unsigned | external_stack − stack_inbundle | external_stack better on |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| single | 71 | 60 | 0.495 | 0.415 | 0.415 | 0.161 | 0.391 | 0.487 | 0.464 | 0.491 | 0.026 | +0.027 ± 0.009 | 43 of 71 |
| pair | 41 | 31 | 0.525 | 0.769 | 0.860 | 0.234 | 0.819 | 0.841 | 0.847 | 0.862 | 0.087 | +0.015 ± 0.008 | 25 of 41 |
| expressed | 75 | 69 | 0.454 | 0.503 | 0.530 | 0.158 | 0.507 | 0.574 | 0.553 | 0.582 | -0.051 | +0.029 ± 0.008 | 49 of 75 |
| silent | 21 | 10 | 0.625 | 0.506 | 0.520 | 0.285 | 0.459 | 0.571 | 0.586 | 0.589 | 0.345 | +0.003 ± 0.013 | 9 of 21 |
| mixed | 16 | 12 | 0.594 | 0.791 | 0.877 | 0.202 | 0.857 | 0.875 | 0.868 | 0.887 | 0.124 | +0.019 ± 0.010 | 10 of 16 |

Single and pair are the number of target genes; expressed means every target is nonzero in at least 5% of the public control cells, silent that none is, mixed a pair with one of each, unknown a target outside the bundle's genes.

## Diagnostics (secondary, not the verdict)

- Same-target agreement, the Pearson correlation between a single's change and its unsigned external row over the genes measured in both without the target gene, expected below 0 for a CRISPRi screen against a CRISPRa bundle: median -0.056 over 60 singles (range -0.508 to 0.387); over pairs, with the summed row, median -0.097 over 31.
- external_direct with s = +1 (external_direct_unsigned), expected below mean_response: 0.048 against 0.506 (paired difference -0.458 ± 0.035, better on 8 of 112); with s = -1, external_direct scores 0.188.
- Share of a training perturbation's summed squared change that lies on its own targets: median 0.013 (singles 0.009, pairs 0.016); the secondary score leaves that share out.
- Runtime: 35 s.

## Per perturbation

| perturbation | targets | kind | expression | hidden | cells (bundle) | cells (external) | genes shared | agreement without targets | target share | mean_response | geneset_knn | additive_singles | external_direct | external_knn | external_krr | stack_inbundle | external_stack | external_direct_unsigned | alpha (in-bundle) | alpha (external) | KRR lambda |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AHR | AHR | single | silent | 3 | 558 | 128 | 2,028 | 0.027 | 0.004 | 0.768 | 0.078 | 0.078 | -0.025 | -0.209 | 0.727 | 0.432 | 0.561 | 0.034 | 0.1 | 1000 | 0.1 |
| AHR+FEV | AHR+FEV | pair | mixed | 1 | 276 | 128 | 2,028 | -0.024 | 0.032 | 0.707 | 0.657 | 0.901 | 0.029 | 0.908 | 0.915 | 0.909 | 0.909 | -0.020 | 0.1 | 0.1 | 0.1 |
| AHR+KLF1 | AHR+KLF1 | pair | mixed | 1 | 481 | 128 | 2,028 | -0.258 | 0.028 | 0.131 | 0.504 | 0.837 | 0.269 | 0.873 | 0.852 | 0.793 | 0.880 | -0.267 | 0.1 | 0.1 | 0.1 |
| ARID1A | ARID1A | single | expressed | 1 | 232 | 271 | 2,028 | -0.134 | 0.000 | 0.787 | 0.658 | 0.658 | 0.139 | 0.692 | 0.733 | 0.704 | 0.729 | -0.129 | 0.1 | 0.1 | 0.1 |
| ARRDC3 | ARRDC3 | single | expressed | 1 | 495 | 129 | 2,028 | -0.276 | 0.001 | 0.637 | 0.479 | 0.479 | 0.279 | 0.619 | 0.654 | 0.535 | 0.628 | -0.272 | 0.1 | 0.1 | 0.1 |
| ATL1 | ATL1 | single | silent | 1 | 379 | – | 0 | – | 0.000 | 0.781 | 0.794 | 0.794 | 0.781 | 0.794 | 0.794 | 0.819 | 0.808 | 0.781 | 0.1 | 0.1 | – |
| BAK1 | BAK1 | single | expressed | 3 | 1,457 | 92 | 2,028 | -0.151 | 0.183 | -0.227 | -0.184 | -0.184 | 0.143 | 0.043 | -0.210 | -0.208 | -0.193 | -0.145 | 0.1 | 0.1 | 0.1 |
| BAK1+BCL2L11 | BAK1+BCL2L11 | pair | expressed | 1 | 175 | 92 | 2,028 | -0.097 | 0.019 | -0.282 | 0.224 | 0.396 | 0.099 | 0.316 | 0.440 | 0.185 | 0.410 | -0.101 | 0.1 | 0.1 | 0.1 |
| BAK1+KLF1 | BAK1+KLF1 | pair | expressed | 1 | 395 | 92 | 2,028 | -0.266 | 0.057 | -0.038 | 0.600 | 0.937 | 0.276 | 0.907 | 0.890 | 0.912 | 0.937 | -0.277 | 0.1 | 0.1 | 0.1 |
| BCL2L11 | BCL2L11 | single | expressed | 2 | 582 | 252 | 2,028 | 0.036 | 0.118 | 0.005 | -0.013 | -0.013 | -0.019 | -0.010 | 0.028 | -0.007 | 0.004 | 0.014 | 0.1 | 0.1 | 0.1 |
| BCORL1 | BCORL1 | single | expressed | 1 | 533 | 212 | 2,028 | -0.043 | 0.016 | 0.388 | 0.278 | 0.278 | 0.043 | 0.247 | 0.355 | 0.315 | 0.333 | -0.040 | 0.1 | 0.1 | 0.1 |
| CBFA2T3 | CBFA2T3 | single | expressed | 2 | 658 | 305 | 2,028 | -0.508 | 0.003 | 0.577 | 0.631 | 0.631 | 0.509 | 0.651 | 0.701 | 0.644 | 0.706 | -0.504 | 0.1 | 0.1 | 0.1 |
| CBFA2T3+FEV | CBFA2T3+FEV | pair | expressed | 1 | 159 | 305 | 2,028 | -0.009 | 0.027 | 0.698 | 0.530 | 0.857 | 0.015 | 0.819 | 0.857 | 0.854 | 0.840 | -0.012 | 0.1 | 0.1 | 0.1 |
| CBL | CBL | single | expressed | 4 | 663 | 206 | 2,028 | -0.382 | 0.005 | 0.568 | 0.340 | 0.340 | 0.387 | 0.746 | 0.789 | 0.430 | 0.711 | -0.383 | 0.1 | 0.1 | 0.1 |
| CBL+CNN1 | CBL+CNN1 | pair | expressed | 1 | 348 | 206 | 2,028 | -0.358 | 0.015 | 0.680 | 0.919 | 0.881 | 0.360 | 0.896 | 0.893 | 0.887 | 0.877 | -0.353 | 0.1 | 0.1 | 0.1 |
| CBL+PTPN9 | CBL+PTPN9 | pair | expressed | 1 | 306 | 78 | 2,028 | -0.191 | 0.003 | 0.742 | 0.936 | 0.884 | 0.194 | 0.945 | 0.925 | 0.871 | 0.883 | -0.189 | 0.1 | 0.1 | 0.1 |
| CBL+UBASH3B | CBL+UBASH3B | pair | expressed | 1 | 410 | – | 0 | – | 0.002 | 0.758 | 0.968 | 0.882 | 0.758 | 0.968 | 0.968 | 0.872 | 0.934 | 0.758 | 0.1 | 0.1 | – |
| CDKN1A | CDKN1A | single | silent | 1 | 360 | – | 0 | – | 0.017 | 0.708 | 0.647 | 0.647 | 0.708 | 0.647 | 0.647 | 0.670 | 0.659 | 0.708 | 0.1 | 0.1 | – |
| CDKN1B | CDKN1B | single | expressed | 1 | 550 | 222 | 2,028 | -0.136 | 0.000 | 0.769 | 0.805 | 0.805 | 0.137 | 0.536 | 0.732 | 0.807 | 0.793 | -0.130 | 0.1 | 100 | 0.1 |
| CEBPA | CEBPA | single | expressed | 5 | 460 | 89 | 2,028 | -0.057 | 0.002 | 0.625 | 0.905 | 0.905 | 0.060 | 0.651 | 0.575 | 0.875 | 0.749 | -0.049 | 0.1 | 0.1 | 0.1 |
| CEBPA+CEBPE | CEBPA+CEBPE | pair | mixed | 1 | 180 | 89 | 2,028 | -0.031 | 0.023 | 0.706 | 0.956 | 0.970 | 0.038 | 0.963 | 0.965 | 0.969 | 0.970 | -0.021 | 0.1 | 0.1 | 0.1 |
| CEBPA+JUN | CEBPA+JUN | pair | expressed | 1 | 54 | 89 | 2,028 | 0.018 | 0.002 | 0.692 | 0.947 | 0.931 | -0.017 | 0.951 | 0.945 | 0.924 | 0.937 | 0.026 | 0.1 | 0.1 | 0.1 |
| CEBPA+KLF1 | CEBPA+KLF1 | pair | expressed | 1 | 311 | 89 | 2,028 | 0.111 | 0.005 | 0.657 | 0.963 | 0.944 | -0.105 | 0.965 | 0.934 | 0.921 | 0.919 | 0.116 | 0.1 | 0.1 | 0.1 |
| CEBPA+ZC3HAV1 | CEBPA+ZC3HAV1 | pair | expressed | 1 | 86 | 89 | 2,028 | -0.097 | 0.007 | 0.617 | 0.946 | 0.946 | 0.109 | 0.946 | 0.952 | 0.938 | 0.947 | -0.098 | 0.1 | 0.1 | 0.1 |
| CEBPE | CEBPE | single | silent | 7 | 1,233 | 166 | 2,028 | 0.031 | 0.042 | 0.616 | 0.733 | 0.733 | -0.019 | 0.418 | 0.604 | 0.718 | 0.685 | 0.037 | 0.1 | 1000 | 0.1 |
| CEBPE+CNN1 | CEBPE+CNN1 | pair | mixed | 1 | 237 | 166 | 2,028 | -0.111 | 0.082 | 0.704 | 0.836 | 0.890 | 0.127 | 0.796 | 0.894 | 0.881 | 0.891 | -0.089 | 0.1 | 0.1 | 0.1 |
| CEBPE+KLF1 | CEBPE+KLF1 | pair | mixed | 1 | 468 | 157 | 2,028 | -0.159 | 0.112 | 0.162 | 0.543 | 0.692 | 0.174 | 0.838 | 0.871 | 0.658 | 0.784 | -0.156 | 0.1 | 1000 | 0.1 |
| CEBPE+SET | CEBPE+SET | pair | mixed | 1 | 658 | 54 | 2,028 | -0.098 | 0.043 | 0.548 | 0.844 | 0.872 | 0.120 | 0.849 | 0.907 | 0.848 | 0.888 | -0.100 | 0.1 | 100 | 0.1 |
| CEBPE+SPI1 | CEBPE+SPI1 | pair | mixed | 1 | 179 | 82 | 2,028 | -0.021 | 0.015 | 0.744 | 0.955 | 0.950 | 0.031 | 0.927 | 0.920 | 0.945 | 0.935 | -0.019 | 0.1 | 0.1 | 0.1 |
| CEBPE+ZC3HAV1 | CEBPE+ZC3HAV1 | pair | mixed | 1 | 410 | 166 | 2,028 | -0.054 | 0.118 | 0.142 | 0.653 | 0.773 | 0.093 | 0.681 | 0.859 | 0.727 | 0.793 | -0.070 | 0.1 | 1000 | 0.1 |
| CELF2 | CELF2 | single | expressed | 1 | 475 | 217 | 2,028 | -0.013 | 0.000 | 0.424 | 0.235 | 0.235 | 0.023 | 0.171 | 0.400 | 0.306 | 0.351 | -0.011 | 0.1 | 0.1 | 0.1 |
| CITED1 | CITED1 | single | expressed | 1 | 215 | 166 | 2,028 | -0.245 | 0.006 | 0.822 | 0.649 | 0.649 | 0.250 | 0.649 | 0.776 | 0.746 | 0.788 | -0.240 | 0.1 | 0.1 | 0.1 |
| CKS1B | CKS1B | single | expressed | 1 | 241 | – | 0 | – | 0.001 | 0.679 | 0.622 | 0.622 | 0.679 | 0.622 | 0.622 | 0.667 | 0.649 | 0.679 | 0.1 | 0.1 | – |
| CLDN6 | CLDN6 | single | expressed | 1 | 670 | 101 | 2,028 | 0.010 | 0.044 | 0.698 | 0.469 | 0.469 | 0.004 | 0.584 | 0.670 | 0.530 | 0.598 | 0.002 | 0.1 | 0.1 | 0.1 |
| CNN1 | CNN1 | single | expressed | 4 | 765 | 432 | 2,028 | 0.000 | 0.061 | 0.428 | 0.313 | 0.313 | 0.007 | 0.185 | 0.378 | 0.369 | 0.353 | 0.002 | 0.1 | 0.1 | 0.1 |
| CNN1+MAPK1 | CNN1+MAPK1 | pair | expressed | 1 | 398 | 305 | 2,028 | -0.284 | 0.039 | 0.630 | 0.848 | 0.879 | 0.316 | 0.879 | 0.896 | 0.859 | 0.882 | -0.300 | 0.1 | 0.1 | 0.1 |
| CNNM4 | CNNM4 | single | silent | 1 | 470 | – | 0 | – | 0.000 | 0.475 | 0.174 | 0.174 | 0.475 | 0.174 | 0.174 | 0.281 | 0.231 | 0.475 | 0.1 | 0.1 | – |
| COL1A1 | COL1A1 | single | silent | 1 | 328 | – | 0 | – | 0.066 | 0.519 | 0.754 | 0.754 | 0.519 | 0.754 | 0.754 | 0.758 | 0.759 | 0.519 | 0.1 | 0.1 | – |
| COL2A1 | COL2A1 | single | expressed | 2 | 598 | 121 | 2,028 | 0.096 | 0.099 | 0.341 | 0.604 | 0.604 | -0.045 | 0.285 | 0.281 | 0.574 | 0.472 | 0.055 | 0.1 | 0.1 | 0.1 |
| COL2A1+KLF1 | COL2A1+KLF1 | pair | expressed | 1 | 298 | 121 | 2,028 | 0.090 | 0.082 | 0.269 | 0.844 | 0.866 | -0.066 | 0.698 | 0.827 | 0.845 | 0.820 | 0.069 | 0.1 | 0.1 | 0.1 |
| CSRNP1 | CSRNP1 | single | expressed | 1 | 478 | 216 | 2,028 | -0.113 | 0.010 | -0.521 | -0.538 | -0.538 | 0.110 | -0.452 | -0.527 | -0.544 | -0.539 | -0.114 | 0.1 | 0.1 | 0.1 |
| DLX2 | DLX2 | single | silent | 2 | 732 | 311 | 2,028 | 0.119 | 0.008 | 0.518 | 0.255 | 0.255 | -0.113 | 0.135 | 0.358 | 0.337 | 0.316 | 0.120 | 0.1 | 10 | 0.1 |
| DLX2+SNAI1 | DLX2+SNAI1 | pair | mixed | 1 | 131 | 178 | 2,028 | -0.006 | 0.002 | 0.729 | 0.867 | 0.870 | 0.011 | 0.883 | 0.901 | 0.879 | 0.889 | -0.004 | 0.1 | 0.1 | 0.1 |
| DUSP9 | DUSP9 | single | expressed | 3 | 731 | 1,351 | 2,028 | -0.219 | 0.052 | 0.537 | -0.062 | -0.062 | 0.200 | 0.280 | 0.624 | 0.233 | 0.496 | -0.204 | 0.1 | 1000 | 0.1 |
| DUSP9+PRTG | DUSP9+PRTG | pair | mixed | 1 | 297 | – | 0 | – | 0.020 | 0.696 | 0.882 | 0.959 | 0.696 | 0.882 | 0.882 | 0.962 | 0.959 | 0.696 | 0.1 | 0.1 | – |
| DUSP9+SNAI1 | DUSP9+SNAI1 | pair | expressed | 1 | 183 | 178 | 2,028 | -0.147 | 0.015 | 0.803 | 0.904 | 0.824 | 0.148 | 0.900 | 0.914 | 0.821 | 0.871 | -0.142 | 0.1 | 0.1 | 0.1 |
| EGR1 | EGR1 | single | expressed | 1 | 322 | 374 | 2,028 | 0.016 | 0.001 | 0.721 | 0.669 | 0.669 | -0.002 | 0.604 | 0.634 | 0.701 | 0.691 | 0.016 | 0.1 | 0.1 | 0.1 |
| ELMSAN1 | ELMSAN1 | single | expressed | 2 | 937 | 551 | 2,028 | -0.069 | 0.006 | -0.251 | -0.251 | -0.251 | 0.064 | -0.395 | -0.239 | -0.251 | -0.275 | -0.071 | 0.1 | 0.1 | 0.1 |
| ELMSAN1+MAP2K3 | ELMSAN1+MAP2K3 | pair | expressed | 1 | 581 | 174 | 2,028 | -0.372 | 0.007 | -0.330 | 0.648 | 0.917 | 0.368 | 0.889 | 0.877 | 0.911 | 0.913 | -0.371 | 0.1 | 0.1 | 0.1 |
| FEV | FEV | single | expressed | 3 | 704 | 314 | 2,028 | -0.055 | 0.082 | 0.339 | 0.315 | 0.315 | 0.069 | 0.396 | 0.415 | 0.334 | 0.390 | -0.064 | 0.1 | 0.1 | 0.1 |
| FOXF1 | FOXF1 | single | silent | 2 | 874 | 240 | 2,028 | -0.082 | 0.001 | 0.611 | 0.659 | 0.659 | 0.085 | 0.595 | 0.610 | 0.669 | 0.671 | -0.077 | 0.1 | 0.1 | 0.1 |
| FOXF1+HOXB9 | FOXF1+HOXB9 | pair | mixed | 1 | 200 | 240 | 2,028 | -0.046 | 0.013 | 0.823 | 0.903 | 0.900 | 0.078 | 0.923 | 0.909 | 0.908 | 0.909 | -0.071 | 0.1 | 0.1 | 0.1 |
| FOXL2 | FOXL2 | single | expressed | 2 | 652 | 375 | 2,028 | -0.319 | 0.013 | 0.743 | 0.623 | 0.623 | 0.331 | 0.700 | 0.767 | 0.683 | 0.773 | -0.322 | 0.1 | 0.1 | 0.1 |
| FOXL2+HOXB9 | FOXL2+HOXB9 | pair | expressed | 1 | 96 | 273 | 2,028 | -0.118 | 0.014 | 0.824 | 0.914 | 0.908 | 0.150 | 0.918 | 0.915 | 0.915 | 0.915 | -0.142 | 0.1 | 0.1 | 0.1 |
| FOXO4 | FOXO4 | single | expressed | 1 | 215 | 293 | 2,028 | 0.123 | 0.005 | 0.767 | 0.557 | 0.557 | -0.118 | 0.738 | 0.756 | 0.601 | 0.681 | 0.129 | 0.1 | 0.1 | 0.1 |
| GLB1L2 | GLB1L2 | single | silent | 1 | 463 | 196 | 2,028 | 0.060 | 0.004 | 0.644 | 0.441 | 0.441 | -0.058 | 0.111 | 0.595 | 0.519 | 0.535 | 0.064 | 0.1 | 0.1 | 0.1 |
| HK2 | HK2 | single | expressed | 1 | 303 | 229 | 2,028 | 0.054 | 0.044 | 0.527 | 0.324 | 0.324 | -0.041 | -0.320 | 0.382 | 0.395 | 0.355 | 0.047 | 0.1 | 0.1 | 0.1 |
| HOXB9 | HOXB9 | single | expressed | 3 | 701 | 273 | 2,028 | -0.016 | 0.040 | 0.780 | 0.623 | 0.623 | 0.085 | 0.128 | 0.774 | 0.724 | 0.762 | -0.076 | 0.1 | 0.1 | 0.1 |
| HOXC13 | HOXC13 | single | expressed | 2 | 385 | 103 | 2,028 | -0.071 | 0.003 | 0.851 | 0.396 | 0.396 | 0.072 | 0.834 | 0.864 | 0.666 | 0.832 | -0.064 | 0.1 | 0.1 | 0.1 |
| HOXC13+ZC3HAV1 | HOXC13+ZC3HAV1 | pair | expressed | 1 | 618 | 103 | 2,028 | -0.113 | 0.040 | 0.677 | 0.580 | 0.891 | 0.139 | 0.748 | 0.884 | 0.883 | 0.892 | -0.135 | 0.1 | 0.1 | 0.1 |
| IER5L | IER5L | single | silent | 2 | 405 | 216 | 2,028 | 0.041 | 0.008 | 0.810 | 0.810 | 0.810 | -0.036 | 0.806 | 0.817 | 0.810 | 0.828 | 0.047 | 0.1 | 0.1 | 0.1 |
| IER5L+LYL1 | IER5L+LYL1 | pair | mixed | 1 | 623 | 87 | 2,028 | 0.249 | 0.043 | 0.846 | 0.744 | 0.898 | -0.191 | 0.864 | 0.806 | 0.916 | 0.873 | 0.195 | 0.1 | 0.1 | 0.1 |
| IGDCC3 | IGDCC3 | single | silent | 4 | 613 | – | 0 | – | 0.045 | 0.662 | 0.662 | 0.662 | 0.662 | 0.662 | 0.662 | 0.662 | 0.662 | 0.662 | 0.1 | 0.1 | – |
| IGDCC3+MAPK1 | IGDCC3+MAPK1 | pair | mixed | 1 | 368 | – | 0 | – | 0.064 | 0.547 | 0.779 | 0.835 | 0.547 | 0.779 | 0.779 | 0.814 | 0.824 | 0.547 | 0.1 | 0.1 | – |
| IGDCC3+PRTG | IGDCC3+PRTG | pair | silent | 1 | 140 | – | 0 | – | 0.026 | 0.688 | 0.688 | 0.902 | 0.688 | 0.688 | 0.688 | 0.905 | 0.905 | 0.688 | 0.1 | 0.1 | – |
| IGDCC3+ZBTB25 | IGDCC3+ZBTB25 | pair | silent | 1 | 141 | – | 0 | – | 0.012 | 0.756 | 0.823 | 0.908 | 0.756 | 0.823 | 0.823 | 0.923 | 0.922 | 0.756 | 0.1 | 0.1 | – |
| IRF1 | IRF1 | single | expressed | 2 | 427 | 274 | 2,028 | -0.059 | 0.010 | 0.366 | 0.218 | 0.218 | 0.069 | 0.327 | 0.377 | 0.269 | 0.341 | -0.053 | 0.1 | 0.1 | 0.1 |
| IRF1+SET | IRF1+SET | pair | expressed | 1 | 444 | 54 | 2,028 | -0.070 | 0.006 | 0.520 | 0.884 | 0.924 | 0.087 | 0.803 | 0.869 | 0.918 | 0.912 | -0.073 | 0.1 | 0.1 | 0.1 |
| JUN | JUN | single | expressed | 2 | 266 | 216 | 2,028 | 0.110 | 0.016 | 0.693 | -0.049 | -0.049 | -0.098 | 0.534 | 0.631 | 0.277 | 0.489 | 0.103 | 0.1 | 0.1 | 0.1 |
| KIF18B | KIF18B | single | expressed | 2 | 254 | 141 | 2,028 | 0.093 | 0.010 | 0.606 | 0.648 | 0.648 | -0.089 | 0.477 | 0.592 | 0.666 | 0.635 | 0.092 | 0.1 | 0.1 | 0.1 |
| KIF18B+KIF2C | KIF18B+KIF2C | pair | expressed | 1 | 96 | 141 | 2,028 | 0.003 | 0.015 | 0.481 | 0.590 | 0.582 | 0.019 | 0.585 | 0.534 | 0.600 | 0.579 | -0.015 | 0.1 | 0.1 | 0.1 |
| KIF2C | KIF2C | single | expressed | 2 | 634 | 209 | 2,028 | -0.136 | 0.175 | 0.452 | 0.529 | 0.529 | 0.236 | 0.369 | 0.453 | 0.521 | 0.496 | -0.228 | 0.1 | 0.1 | 0.1 |
| KLF1 | KLF1 | single | expressed | 7 | 1,960 | 157 | 2,028 | -0.351 | 0.038 | -0.061 | -0.099 | -0.099 | 0.363 | -0.057 | 0.019 | -0.088 | -0.022 | -0.363 | 0.1 | 1000 | 0.1 |
| KLF1+SET | KLF1+SET | pair | expressed | 1 | 667 | 54 | 2,028 | -0.256 | 0.043 | 0.353 | 0.625 | 0.893 | 0.277 | 0.670 | 0.807 | 0.886 | 0.892 | -0.274 | 0.1 | 0.1 | 0.1 |
| KMT2A | KMT2A | single | expressed | 1 | 241 | 205 | 2,028 | -0.201 | 0.043 | 0.508 | 0.327 | 0.327 | 0.250 | 0.571 | 0.559 | 0.364 | 0.461 | -0.247 | 0.1 | 0.1 | 0.1 |
| LYL1 | LYL1 | single | expressed | 2 | 432 | 87 | 2,028 | -0.126 | 0.226 | 0.424 | 0.249 | 0.249 | 0.212 | 0.415 | 0.483 | 0.316 | 0.462 | -0.210 | 0.1 | 0.1 | 0.1 |
| MAP2K3 | MAP2K3 | single | expressed | 3 | 579 | 174 | 2,028 | -0.391 | 0.017 | -0.548 | -0.479 | -0.479 | 0.384 | -0.168 | -0.425 | -0.509 | -0.457 | -0.389 | 100 | 0.1 | 0.3 |
| MAP2K3+SLC38A2 | MAP2K3+SLC38A2 | pair | expressed | 1 | 338 | 140 | 2,028 | -0.421 | 0.016 | -0.593 | 0.633 | 0.877 | 0.421 | 0.660 | 0.896 | 0.807 | 0.882 | -0.424 | 0.1 | 0.1 | 0.1 |
| MAP4K5 | MAP4K5 | single | expressed | 1 | 366 | 167 | 2,028 | -0.141 | 0.001 | 0.586 | 0.587 | 0.587 | 0.145 | 0.649 | 0.613 | 0.601 | 0.635 | -0.142 | 0.1 | 0.1 | 0.1 |
| MAPK1 | MAPK1 | single | expressed | 4 | 765 | 305 | 2,028 | -0.318 | 0.011 | 0.352 | 0.447 | 0.447 | 0.334 | 0.512 | 0.477 | 0.458 | 0.528 | -0.321 | 0.1 | 0.1 | 0.1 |
| MAPK1+PRTG | MAPK1+PRTG | pair | mixed | 1 | 500 | – | 0 | – | 0.026 | 0.578 | 0.705 | 0.828 | 0.578 | 0.705 | 0.705 | 0.814 | 0.811 | 0.578 | 0.1 | 0.1 | – |
| MIDN | MIDN | single | expressed | 1 | 298 | 568 | 2,028 | 0.027 | 0.006 | 0.810 | 0.810 | 0.810 | -0.013 | 0.579 | 0.774 | 0.810 | 0.789 | 0.028 | 0.1 | 0.1 | 0.1 |
| NCL | NCL | single | expressed | 1 | 237 | 443 | 2,028 | 0.112 | 0.077 | 0.317 | 0.041 | 0.041 | 0.027 | 0.331 | 0.313 | 0.247 | 0.344 | -0.021 | 0.1 | 0.1 | 0.1 |
| NIT1 | NIT1 | single | expressed | 1 | 192 | 237 | 2,028 | -0.005 | 0.000 | 0.598 | 0.598 | 0.598 | 0.013 | 0.574 | 0.619 | 0.598 | 0.612 | -0.001 | 0.1 | 0.1 | 0.1 |
| OSR2 | OSR2 | single | expressed | 2 | 1,003 | 109 | 2,028 | 0.017 | 0.021 | 0.290 | 0.456 | 0.456 | -0.015 | -0.014 | 0.227 | 0.428 | 0.373 | 0.020 | 0.1 | 0.1 | 0.1 |
| OSR2+UBASH3B | OSR2+UBASH3B | pair | expressed | 1 | 796 | – | 0 | – | 0.070 | 0.230 | 0.358 | 0.718 | 0.230 | 0.358 | 0.358 | 0.671 | 0.594 | 0.230 | 0.1 | 0.1 | – |
| PLK4 | PLK4 | single | expressed | 2 | 113 | 43 | 2,028 | 0.205 | 0.000 | 0.561 | 0.533 | 0.533 | -0.204 | 0.581 | 0.558 | 0.565 | 0.568 | 0.208 | 0.1 | 0.1 | 0.1 |
| PLK4+STIL | PLK4+STIL | pair | expressed | 1 | 81 | 43 | 2,028 | 0.345 | 0.000 | 0.698 | 0.716 | 0.691 | -0.345 | 0.753 | 0.615 | 0.723 | 0.666 | 0.347 | 0.1 | 0.1 | 0.1 |
| PRDM1 | PRDM1 | single | silent | 1 | 297 | 216 | 2,028 | 0.032 | 0.001 | 0.730 | 0.462 | 0.462 | -0.029 | 0.671 | 0.714 | 0.511 | 0.592 | 0.037 | 0.1 | 0.1 | 0.1 |
| PRTG | PRTG | single | silent | 4 | 685 | – | 0 | – | 0.009 | 0.632 | 0.632 | 0.632 | 0.632 | 0.632 | 0.632 | 0.632 | 0.632 | 0.632 | 0.1 | 100 | – |
| PTPN1 | PTPN1 | single | expressed | 1 | 419 | 371 | 2,028 | -0.226 | 0.002 | 0.749 | 0.922 | 0.922 | 0.230 | 0.895 | 0.813 | 0.924 | 0.911 | -0.228 | 0.1 | 0.1 | 0.1 |
| PTPN13 | PTPN13 | single | silent | 1 | 270 | – | 0 | – | 0.001 | 0.601 | 0.407 | 0.407 | 0.601 | 0.407 | 0.407 | 0.471 | 0.440 | 0.601 | 0.1 | 0.1 | – |
| PTPN9 | PTPN9 | single | expressed | 3 | 445 | 78 | 2,028 | 0.049 | 0.013 | 0.592 | 0.669 | 0.669 | -0.046 | -0.029 | 0.526 | 0.673 | 0.615 | 0.051 | 0.1 | 0.1 | 0.1 |
| PTPN9+UBASH3B | PTPN9+UBASH3B | pair | expressed | 1 | 325 | – | 0 | – | 0.005 | 0.748 | 0.942 | 0.904 | 0.748 | 0.942 | 0.942 | 0.917 | 0.933 | 0.748 | 0.1 | 0.1 | – |
| SET | SET | single | expressed | 4 | 986 | 54 | 2,028 | -0.082 | 0.006 | 0.523 | 0.461 | 0.461 | 0.102 | -0.034 | 0.457 | 0.489 | 0.481 | -0.093 | 0.1 | 100 | 0.1 |
| SGK1 | SGK1 | single | expressed | 2 | 483 | 142 | 2,028 | 0.151 | 0.013 | 0.763 | 0.779 | 0.779 | -0.148 | 0.352 | 0.726 | 0.793 | 0.771 | 0.153 | 0.1 | 0.1 | 0.1 |
| SGK1+TBX2 | SGK1+TBX2 | pair | mixed | 1 | 349 | 142 | 2,028 | 0.079 | 0.007 | 0.737 | 0.935 | 0.947 | -0.078 | 0.942 | 0.929 | 0.949 | 0.943 | 0.084 | 0.1 | 0.1 | 0.1 |
| SLC38A2 | SLC38A2 | single | expressed | 2 | 332 | 140 | 2,028 | -0.287 | 0.024 | -0.298 | -0.094 | -0.094 | 0.302 | -0.284 | -0.249 | -0.189 | -0.230 | -0.305 | 0.1 | 1000 | 0.1 |
| SLC4A1 | SLC4A1 | single | silent | 1 | 1,000 | – | 0 | – | 0.007 | 0.246 | 0.105 | 0.105 | 0.246 | 0.105 | 0.105 | 0.210 | 0.169 | 0.246 | 0.1 | 0.1 | – |
| SLC6A9 | SLC6A9 | single | silent | 1 | 558 | – | 0 | – | 0.013 | 0.513 | -0.001 | -0.001 | 0.513 | -0.001 | -0.001 | 0.339 | 0.176 | 0.513 | 0.1 | 0.1 | – |
| SNAI1 | SNAI1 | single | expressed | 4 | 467 | 178 | 2,028 | -0.257 | 0.001 | 0.571 | 0.630 | 0.630 | 0.259 | 0.597 | 0.558 | 0.627 | 0.621 | -0.253 | 0.1 | 0.1 | 0.1 |
| SNAI1+UBASH3B | SNAI1+UBASH3B | pair | expressed | 1 | 299 | – | 0 | – | 0.005 | 0.760 | 0.840 | 0.909 | 0.760 | 0.840 | 0.840 | 0.903 | 0.905 | 0.760 | 0.1 | 0.1 | – |
| SPI1 | SPI1 | single | expressed | 2 | 613 | 82 | 2,028 | -0.143 | 0.004 | 0.823 | 0.759 | 0.759 | 0.149 | 0.755 | 0.841 | 0.807 | 0.882 | -0.143 | 0.1 | 0.1 | 0.1 |
| STIL | STIL | single | expressed | 2 | 309 | 345 | 2,028 | 0.387 | 0.003 | 0.716 | 0.643 | 0.643 | -0.374 | 0.708 | 0.740 | 0.688 | 0.735 | 0.383 | 0.1 | 0.1 | 0.1 |
| TBX2 | TBX2 | single | silent | 2 | 690 | 207 | 2,028 | -0.017 | 0.007 | 0.476 | 0.335 | 0.335 | 0.021 | 0.470 | 0.494 | 0.378 | 0.469 | -0.011 | 0.1 | 0.1 | 0.1 |
| TMSB4X | TMSB4X | single | expressed | 1 | 543 | 173 | 2,028 | -0.099 | 0.536 | 0.304 | 0.282 | 0.282 | 0.505 | 0.294 | 0.332 | 0.296 | 0.346 | -0.502 | 0.1 | 0.1 | 0.1 |
| TP73 | TP73 | single | silent | 1 | 248 | 196 | 2,028 | 0.366 | 0.000 | 0.855 | 0.832 | 0.832 | -0.364 | 0.491 | 0.854 | 0.850 | 0.863 | 0.369 | 0.1 | 1000 | 0.1 |
| UBASH3B | UBASH3B | single | expressed | 6 | 1,202 | – | 0 | – | 0.013 | 0.630 | 0.853 | 0.853 | 0.630 | 0.853 | 0.853 | 0.821 | 0.840 | 0.630 | 0.1 | 0.1 | – |
| UBASH3B+ZBTB25 | UBASH3B+ZBTB25 | pair | mixed | 1 | 255 | – | 0 | – | 0.002 | 0.702 | 0.900 | 0.905 | 0.702 | 0.900 | 0.900 | 0.915 | 0.930 | 0.702 | 0.1 | 0.1 | – |
| ZBTB25 | ZBTB25 | single | silent | 3 | 740 | 62 | 2,028 | 0.053 | 0.000 | 0.509 | 0.333 | 0.333 | -0.050 | 0.473 | 0.533 | 0.424 | 0.494 | 0.053 | 0.1 | 0.1 | 0.1 |
| ZC3HAV1 | ZC3HAV1 | single | expressed | 4 | 516 | 183 | 2,028 | -0.146 | 0.084 | -0.320 | -0.244 | -0.244 | 0.195 | 0.133 | -0.238 | -0.276 | -0.255 | -0.200 | 0.1 | 0.1 | 0.1 |
| ZNF318 | ZNF318 | single | expressed | 1 | 650 | 80 | 2,028 | -0.075 | 0.009 | 0.465 | 0.418 | 0.418 | 0.086 | 0.528 | 0.518 | 0.441 | 0.511 | -0.082 | 0.1 | 0.1 | 0.1 |

Hidden counts the perturbations the hiding rule removes for that fold, itself included. A dash means no external row or no value.

## Reading

The external screen adds information beyond the in-bundle predictors on this check (external_stack minus stack_inbundle +0.023 ± 0.006 paired standard error, external_stack better on 68 and worse on 44 of 112): the gain exceeds twice its paired standard error and external_stack is better on more than half the perturbations. The strata, the diagnostics and each predictor against mean_response and geneset_knn describe the result and are not the verdict. Caveats: this is one bundle and one external screen, the scores are leave-one-out on training perturbations rather than held-out validation, and a gain here must still be confirmed on the sealed set by a labelled arm (the scripted control with the screen against the one without) before it counts.
