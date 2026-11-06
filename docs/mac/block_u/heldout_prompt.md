You are finishing the model that the files in this directory define (research_plan.json, acceptance_contract.json and
result.py are CellForge's output for this task). Read TASK.md first: it is the contract.

Write `predict_heldout.py` in this directory. It must:

1. Load the training data from the path given as `--data` (an .h5ad; `.obs['perturbation']`, with `control` for
   unperturbed cells; `.X` is counts per 10k, log1p). Use ALL of it for training: no out-of-distribution holdout of
   perturbations, no validation split except what early stopping in result.py needs.
2. Build and train exactly the model result.py defines, with the same hyperparameters and number of epochs, by
   importing from result.py or by copying its code. Do not design a new model.
3. Read the held-out perturbation keys from the JSON list given as `--heldout` (strings, in that order; a key with
   `+` is a combination of two genes). None of them has a training cell. Predict, for each key, the mean expression
   of every gene in the training file, in the file's gene order and on the same scale.
4. Write the result with `numpy.savez` to the path given as `--out`: `perts` (array of the keys, dtype str, same
   order) and `means` (float32 array, len(perts) x n_genes). Nothing else is required.
5. Run on CPU, or on `torch.device("mps")` when available. Do not download anything and do not read any file other
   than the two inputs. Do not open any file whose name contains `private`, `splits`, `val2` or `test`.

Before you finish, run a smoke test of your own script on a 2,000-cell random subsample of the training file with one
epoch and `--out smoke_predictions.npz`, confirm the arrays have the right shapes and no NaN, then delete
smoke_predictions.npz. Do not run the full training here; the operator runs it afterwards with:

    python predict_heldout.py --data <training.h5ad> --heldout heldout_perturbations.json --out predictions.npz

Reply with one paragraph: how predictions for unseen perturbations are formed by this model, and the expected
runtime of the full run.
