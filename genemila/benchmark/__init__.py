"""PROTECTED benchmark components: evaluator, metric definitions, query-only
oracle. Experiments whose code diff touches this package are rejected, and
the controller always evaluates with its own copy, never a worktree copy."""

PRIMARY_METRIC = "pearson_delta"
PRIMARY_HIGHER_IS_BETTER = True
TOP_DE = 20

# Model-selection rules (`experiment.selection`, a lab setting agents cannot change). The selection score
# ("primary") is a weighted sum of per-perturbation metrics from the evaluator, each averaged over the visible
# perturbations; every rule is higher-is-better. pearson_delta is blind to the size of the predicted change,
# so under it alone a heavily regularised model that shrinks every change wins as long as the pattern is
# right; r2_top is R² of the predicted expression on each perturbation's 20 most changed genes (CellForge's
# R²_DE on the visible means), which that shrinkage loses.
SELECTION_RULES = {
    "pearson_delta": {"pearson_delta": 1.0},
    "pearson_delta+r2_top": {"pearson_delta": 0.5, "r2_top": 0.5},
}
METRIC_TEXT = {
    "pearson_delta": "Pearson correlation between predicted and true expression change over all genes",
    "r2_top": "R² between predicted and true expression on the perturbation's 20 most changed genes "
              "(the size of the change matters here: shrunken changes lose)",
}


def selection_score(metrics: dict, rule: str = PRIMARY_METRIC) -> float:
    """The selection score of one evaluation under `rule` (metrics already averaged over perturbations)."""
    return float(sum(w * metrics[m] for m, w in SELECTION_RULES[rule].items()))
