# Example autonomous run (synthetic data)

`python run_research.py --minutes 10 --workers 4 --worker-provider claude_cli --worker-model haiku
--planner-provider claude_cli --planner-model opus --budget 1.5 --max-planner-calls 4`

Claude Opus planned and Claude Haiku wrote the feature code. This run was made in the build
environment, where DeepSeek was unreachable; the DeepSeek worker path is the same code with
`--worker-provider deepseek`. The run stopped early, after 5.6 minutes, once its 4 planner
rounds were used up.

* `summary.md`: the automatic end-of-run report (baseline 0.6054 → best 0.7775 pearson_delta;
  query-only 0.7764)
* `analysis.md`: scaling analysis (`analyze_run.py`)
* `planner_round1.json`: the planner's first hypothesis batch, as returned
* `research_state_round3.txt`: the compressed state the planner received in round 3
* `tf_gated_coexpression_e26.py`: the feature written by a worker in the best model
