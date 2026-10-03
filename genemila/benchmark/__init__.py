"""PROTECTED benchmark components: evaluator, metric definitions, query-only
oracle. Experiments whose code diff touches this package are rejected, and
the controller always evaluates with its own copy, never a worktree copy."""

PRIMARY_METRIC = "pearson_delta"
PRIMARY_HIGHER_IS_BETTER = True
TOP_DE = 20
