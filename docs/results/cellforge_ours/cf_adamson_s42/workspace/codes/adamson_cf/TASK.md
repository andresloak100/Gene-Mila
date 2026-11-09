# Task for CellForge (Gene-Mila matched comparison)

Predict, for each perturbation listed in `heldout_perturbations.json`, the mean expression of every gene in
`cellforge_input.h5ad` (same genes, same order, same normalisation: counts per 10k, log1p) in K562 cells carrying
that CRISPR perturbation. None of these perturbations has any cell in the training file: this is the unseen-
perturbation setting. Train only on `cellforge_input.h5ad`; do not download or use any other copy of this screen.

Output: `predictions.npz` with `perts` (the held-out keys, as listed) and `means` (n_perts x n_genes, float).
Scored by Gene-Mila's evaluator: pearson_delta (correlation of predicted and true change from control, per
perturbation), MSE, and MSE/PCC/R2 on the top-20 DE genes.
