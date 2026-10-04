# Example autonomous run (synthetic data)

`python run_research.py --minutes 10 --workers 4 --worker-provider claude_cli --worker-model haiku
--planner-provider claude_cli --planner-model opus --budget 1.5 --max-planner-calls 4`

Claude Opus planned and Claude Haiku wrote the feature code. This run was made in the build
environment, where DeepSeek was unreachable; the DeepSeek worker path is the same code with
`--worker-provider deepseek`. The run stopped early, after 5.6 minutes, once its 4 planner
rounds were used up.

Data: `python prepare_data.py synthetic` (seed 0), 80 single-gene knockouts split into 48
training, 16 visible-validation and 16 query-only perturbations (`split_3ad9ac2956087b2f`).
Every pearson_delta here is a mean over 16 perturbations.

* `summary.md`: the automatic end-of-run report (baseline 0.6054 → best 0.7775 pearson_delta;
  query-only 0.7764)
* `analysis.md`: scaling analysis (`analyze_run.py`)
* `planner_round1.json`: the planner's first hypothesis batch, as returned
* `research_state_round3.txt`: the compressed state the planner received in round 3
* `tf_gated_coexpression_e26.py`: the feature written by a worker in the best model
* `control_scripted_summary.md`: a control on the same split with no LLM at all, the offline
  dry run from the main README (`--worker-provider mock --planner-provider scripted`,
  2 minutes, $0). A scripted planner proposes seven fixed hypotheses, mock workers paste
  hand-written template features (`genemila/providers/mock.py`), and Python combines the ones
  that helped and sweeps alpha. Best 0.7702 pearson_delta on visible validation, 0.7776
  query-only. Run on later code (`dee5bb55b0`); the same command gave the same numbers at
  commit `4ace15e` and once more after the lab's results-table merge. A second rerun after that
  merge stopped one step earlier, at 0.7683 and 0.7744 (the `EXP_0016` row of the summary),
  because the scripted planner combines only finished results and a 2-minute run is
  timing-sensitive.
