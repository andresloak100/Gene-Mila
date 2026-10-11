# How high can pearson_delta go on Adamson? Two ceilings, measured on the training perturbations

Generated from docs/results/ceiling_analysis.json (tools/ceiling_analysis.py, run on the Mac at lab checkout 047595d on 2026-10-11; inputs: the public bundle data/adamson_cf/public.npz and the raw cells of the 50 training perturbations from the Adamson 10X010 file; no private file and no split file opened). Seeded, 20 random half-splits per perturbation. The learned-similarity numbers at the end come from tools/learned_kernel_experiment.py, run the same day on the same inputs plus the bundle's knowledge files.

## Summary

| Quantity, mean over the 50 training perturbations | pearson_delta |
|---|---|
| Split-half agreement of a perturbation's own measured response (two random halves of its cells) | 0.720 |
| Noise ceiling: what a perfect predictor of the expected response would score against the measured one (sqrt of the Spearman-Brown reliability) | 0.889 (median 0.942, range 0.34 to 0.996) |
| Predict the mean response of the other 49 perturbations (leave-one-out) | 0.474 |
| Copy the single most similar other perturbation, chosen with hindsight | 0.657 |
| Best non-negative mix of the other 49 responses, weights fitted on the truth (transfer ceiling) | 0.734 |
| Best linear mix of the other 49 responses, any sign, fitted on the truth | 0.780 |
| The lab's models, out of fold on the same perturbations (docs/results/scaling.md) | about 0.60 |

## Reading

The two halves of one perturbation's cells agree with each other at only 0.72 on average, so even a perfect model would score about 0.89 against the measured responses, and far less on weakly measured knockdowns (PSMD12 with 60 cells caps at 0.34, ERN1 with 83 cells at 0.47). Every feature that has helped so far transfers responses between related knockdowns; with perfect hindsight that family tops out at 0.73 (non-negative mixes) to 0.78 (any mix), and the lab's models sit near 0.60. So about 0.13 to 0.18 is left in the transfer family on this split, and it lives in perturbations whose response is unlike the average and unlike any close relative in training (GNPNAT1, CAD, ERN1, MRGBP, ASCC3, MANF): for CAD and ASCC3 the measurement is clean (ceiling 0.98 to 0.99) but no mix of the other knockdowns reaches 0.45. Getting there needs better information about which knockdowns behave alike than the bundle's gene sets and interaction network carry, not more search. A score of 0.99 is not attainable on this metric; CellForge's 0.988 is a correlation of whole expression profiles, on which the lab's models and plain OLS already score 0.987 to 0.989.

## Learned similarity between targets (leave-one-out, tuning inside each fold)

As printed by tools/learned_kernel_experiment.py on the Mac (its JSON is to be committed when pasted): a ridge model from gene-set overlap, interaction-network overlap, co-expression and gene family to response similarity, used to weight the other perturbations' responses.

| Transfer predictor, leave-one-out over the 50 training perturbations | pearson_delta |
|---|---|
| Mean response | 0.474 |
| Co-expression-profile similarity | 0.485 |
| Gene-set similarity (what the agents found) | 0.540 |
| Learned similarity | 0.551 |

The learned similarity adds +0.010 and is better in 27 of 50 perturbations: inside the noise. Combining the bundle's prior knowledge more cleverly does not create the missing information.

## Per perturbation

| perturbation | cells | RMS of true delta | noise ceiling | LOO mean response | best single neighbour (hindsight) | best non-negative mix (hindsight) |
|---|---|---|---|---|---|---|
| GNPNAT1 | 503 | 0.029 | 0.735 | -0.130 | 0.135 | 0.144 |
| SRPR | 591 | 0.046 | 0.908 | 0.022 | 0.791 | 0.806 |
| CAD | 281 | 0.121 | 0.975 | 0.035 | 0.320 | 0.400 |
| ERN1 | 83 | 0.062 | 0.471 | 0.056 | 0.135 | 0.177 |
| SRPRB | 703 | 0.062 | 0.955 | 0.143 | 0.791 | 0.845 |
| GMPPB | 606 | 0.029 | 0.767 | 0.171 | 0.514 | 0.637 |
| TTI2 | 653 | 0.030 | 0.830 | 0.174 | 0.562 | 0.655 |
| MRGBP | 570 | 0.059 | 0.945 | 0.179 | 0.326 | 0.435 |
| MANF | 554 | 0.025 | 0.638 | 0.199 | 0.299 | 0.423 |
| SEL1L | 443 | 0.046 | 0.881 | 0.246 | 0.727 | 0.769 |
| ASCC3 | 1756 | 0.079 | 0.990 | 0.249 | 0.362 | 0.448 |
| SYVN1 | 650 | 0.031 | 0.827 | 0.288 | 0.727 | 0.772 |
| PSMD12 | 60 | 0.080 | 0.338 | 0.308 | 0.335 | 0.397 |
| CHERP | 479 | 0.117 | 0.986 | 0.311 | 0.522 | 0.596 |
| KCTD16 | 464 | 0.035 | 0.738 | 0.353 | 0.573 | 0.639 |
| P4HB | 560 | 0.034 | 0.839 | 0.357 | 0.427 | 0.562 |
| SEC63 | 654 | 0.028 | 0.794 | 0.367 | 0.559 | 0.652 |
| AMIGO3 | 715 | 0.025 | 0.738 | 0.367 | 0.514 | 0.681 |
| NEDD8 | 506 | 0.116 | 0.984 | 0.377 | 0.500 | 0.570 |
| TMED2 | 505 | 0.042 | 0.890 | 0.386 | 0.615 | 0.661 |
| STT3A | 500 | 0.030 | 0.721 | 0.388 | 0.509 | 0.650 |
| TELO2 | 691 | 0.044 | 0.924 | 0.405 | 0.736 | 0.794 |
| FECH | 683 | 0.065 | 0.967 | 0.424 | 0.602 | 0.677 |
| UFM1 | 692 | 0.034 | 0.875 | 0.428 | 0.633 | 0.702 |
| TTI1 | 526 | 0.105 | 0.980 | 0.429 | 0.736 | 0.816 |
| DDRGK1 | 607 | 0.036 | 0.876 | 0.435 | 0.633 | 0.690 |
| SLC35B1 | 621 | 0.027 | 0.755 | 0.448 | 0.498 | 0.666 |
| TMED10 | 626 | 0.037 | 0.881 | 0.477 | 0.615 | 0.718 |
| PPWD1 | 234 | 0.107 | 0.950 | 0.532 | 0.631 | 0.752 |
| SRP68 | 699 | 0.070 | 0.962 | 0.534 | 0.696 | 0.873 |
| DDOST | 382 | 0.062 | 0.912 | 0.534 | 0.682 | 0.797 |
| IER3IP1 | 1830 | 0.068 | 0.986 | 0.541 | 0.872 | 0.905 |
| YIPF5 | 1400 | 0.059 | 0.978 | 0.553 | 0.884 | 0.926 |
| HSD17B12 | 404 | 0.077 | 0.953 | 0.615 | 0.644 | 0.769 |
| TMEM167A | 468 | 0.061 | 0.939 | 0.644 | 0.884 | 0.913 |
| DERL2 | 656 | 0.053 | 0.919 | 0.662 | 0.631 | 0.829 |
| COPB1 | 225 | 0.080 | 0.904 | 0.684 | 0.835 | 0.875 |
| SAMM50 | 817 | 0.088 | 0.985 | 0.693 | 0.903 | 0.923 |
| GBF1 | 958 | 0.037 | 0.903 | 0.722 | 0.657 | 0.833 |
| TARS | 803 | 0.092 | 0.983 | 0.727 | 0.827 | 0.856 |
| SEC61A1 | 1191 | 0.138 | 0.994 | 0.742 | 0.696 | 0.866 |
| COPZ1 | 282 | 0.112 | 0.957 | 0.773 | 0.835 | 0.893 |
| HARS | 325 | 0.186 | 0.986 | 0.815 | 0.865 | 0.898 |
| SLMO2 | 637 | 0.126 | 0.990 | 0.826 | 0.922 | 0.978 |
| EIF2S1 | 511 | 0.206 | 0.994 | 0.848 | 0.925 | 0.952 |
| HSPA9 | 894 | 0.195 | 0.996 | 0.857 | 0.957 | 0.971 |
| EIF2B2 | 615 | 0.140 | 0.990 | 0.865 | 0.967 | 0.974 |
| IARS2 | 1111 | 0.167 | 0.996 | 0.880 | 0.957 | 0.977 |
| CARS | 501 | 0.220 | 0.994 | 0.880 | 0.915 | 0.951 |
| TIMM44 | 590 | 0.149 | 0.991 | 0.889 | 0.967 | 0.982 |
