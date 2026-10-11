# Does an external screen carry information the transfer features lack?

Leave-one-out over the 8 training perturbations of the `synthetic` bundle, visible data only: each training perturbation is held out in turn, its expression change (pseudobulk mean minus the control mean of public.npz) is predicted from the other 7 training perturbations and the public knowledge files, and the prediction is scored by pearson_delta, the Pearson correlation across all 40 genes between the predicted and the measured change. Nothing of the held-out perturbation's own label reaches any predictor. The protocol, the five predictors and the reading rule below were fixed before the external file was opened, and the result is reported whatever it shows. The sealed set is never read; this is a reading on whether the external screen deserves a labelled arm, not a benchmark score.

External screen: `ext_v1`, synthetic external screen (signal). The file holds 6 target genes over 1,000 control cells; 36 of the bundle's 40 genes are measured in it, and 6 of the 8 training perturbations have a row (their first target gene with one). The file also lists 1 bundle target with zero cells (G0006); such a row is no measurement and was treated as missing.

Predictors (k = 3 for both neighbour rules):

- `mean_response`: mean change of the other training perturbations, the floor every feature must beat.
- `geneset_knn`: weighted mean of the other perturbations' changes, weights = Jaccard similarity of the targets' gene-set memberships (knowledge/gene_sets.json), top k with positive similarity, else mean_response. The in-bundle reference close to what the agents found.
- `external_direct`: the external change of the same target gene, unmeasured genes filled from mean_response; mean_response when the target has no external row.
- `external_knn`: weighted mean of the other perturbations' changes, weights = Pearson correlation between the external changes of the two targets over the genes measured in both, top k with positive correlation; geneset_knn when the held-out target has no external row or no neighbour correlates positively.
- `external_stack`: ridge over gene rows combining the four columns above (standardised with the training rows' statistics), trained on the other perturbations' rows, each row's columns computed without that perturbation and without the held-out one; alpha chosen by an inner leave-one-out over those perturbations from the grid [0.1, 1.0, 10.0, 100.0, 1000.0].

## Predictors

| predictor | pearson_delta, mean ± sd | median | min | max | better than mean_response | paired gain vs mean_response | better than geneset_knn | paired gain vs geneset_knn | coverage |
|---|---|---|---|---|---|---|---|---|---|
| mean_response | 0.367 ± 0.153 | 0.388 | 0.099 | 0.609 | – | – | 2 of 8 | -0.011 ± 0.037 | 8 of 8 (no external input) |
| geneset_knn | 0.378 ± 0.197 | 0.333 | 0.099 | 0.665 | 2 of 8 | +0.011 ± 0.037 | – | – | 8 of 8 (no external input) |
| external_direct | 0.786 ± 0.244 | 0.933 | 0.427 | 0.977 | 6 of 8 | +0.419 ± 0.114 | 7 of 8 | +0.408 ± 0.126 | 6 of 8 |
| external_knn | 0.485 ± 0.112 | 0.495 | 0.238 | 0.608 | 7 of 8 | +0.118 ± 0.038 | 5 of 8 | +0.107 ± 0.057 | 6 of 8 |
| external_stack | 0.793 ± 0.226 | 0.925 | 0.469 | 0.977 | 8 of 8 | +0.426 ± 0.108 | 7 of 8 | +0.416 ± 0.119 | 6 of 8 |

"Better than" counts perturbations whose score is strictly higher, paired; the paired gain is the mean difference ± its standard error over the perturbations. Fallbacks taken: external_direct used mean_response for 2 perturbations without an external row; external_knn used geneset_knn for 2 without a row and 0 without a positively correlated neighbour; geneset_knn used mean_response for 4 without a positively similar perturbation. Stack alpha chosen per fold: 0.1 for 5, 10 for 3.

## Per perturbation

| perturbation | target | cells (bundle) | cells (external) | genes shared | same-target agreement | mean_response | geneset_knn | external_direct | external_knn | external_stack | alpha |
|---|---|---|---|---|---|---|---|---|---|---|---|
| G0000_KO | G0000 | 12 | – | 0 | – | 0.609 | 0.608 | 0.609 | 0.608 | 0.646 | 10 |
| G0006_KO | G0006 | 12 | – | 0 | – | 0.427 | 0.499 | 0.427 | 0.499 | 0.475 | 10 |
| G0010_KO | G0010 | 12 | 102 | 36 | 0.996 | 0.307 | 0.307 | 0.460 | 0.571 | 0.469 | 0.1 |
| G0011_KO | G0011 | 12 | 103 | 36 | 0.998 | 0.250 | 0.250 | 0.977 | 0.537 | 0.977 | 0.1 |
| G0014_KO | G0014 | 12 | 104 | 36 | 0.998 | 0.099 | 0.099 | 0.912 | 0.238 | 0.908 | 10 |
| G0021_KO | G0021 | 12 | 105 | 36 | 0.998 | 0.467 | 0.665 | 0.954 | 0.491 | 0.956 | 0.1 |
| G0027_KO | G0027 | 12 | 106 | 36 | 0.999 | 0.360 | 0.360 | 0.974 | 0.456 | 0.974 | 0.1 |
| G0037_KO | G0037 | 12 | 107 | 36 | 0.997 | 0.416 | 0.233 | 0.976 | 0.479 | 0.942 | 0.1 |

Same-target agreement is the Pearson correlation across the genes measured in both screens between the bundle's change and the external change for the same target gene; cells are the perturbed cells behind each side's mean. A dash means no external row.

## Reading

Same-target agreement: for the 6 training perturbations the external screen also measured, the Pearson correlation across measured genes between the bundle's change and the external change has median 0.998 (range 0.996 to 0.999); that is how alike the two screens are for the same knockdown, and it bounds what external_direct can do. Against the floor, external_direct scores 0.786 versus mean_response 0.367 (paired difference +0.419 ± 0.114 standard error, better on 6 of 8). The external screen adds information beyond the gene sets on this check: geneset_knn 0.378, external_knn 0.485 (+0.107 ± 0.057, better on 5 of 8), external_stack 0.793 (+0.416 ± 0.119, better on 7 of 8). The best external predictor (external_stack) is ahead of geneset_knn by more than twice its paired standard error and on a majority of perturbations. Caveats: this is 8 perturbations of one bundle and one external screen (6 of the 8 targets have an external row; the rest fell back), the scores are leave-one-out on training perturbations rather than held-out validation, and a gain here must still be confirmed on the sealed set by a labelled arm that is given the knowledge file before it counts.
