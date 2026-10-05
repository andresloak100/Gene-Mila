# The next lever after the 0.60 plateau

Status at commit c8bd5b9 (26 runs on Adamson, CellForge's split, 20 minutes each). Every good configuration
ends near the same held-out score: 4 workers 0.602 ± 0.002 sealed pearson_delta, the new selection code 0.601
and 0.587, the DeepSeek-planned run that worked 0.601, the DE-aware selection rule 0.584. The starting model
scores 0.520 and the no-LLM control 0.554. Three things did not move the plateau: more workers (1/4/8/16),
another planner (DeepSeek V4 Pro), another selection rule (`pearson_delta+r2_top`). Details in
`docs/results/scaling.md` and `docs/results/summary_for_collaborators.md`.

## What the gain is made of

Every winning model carries one feature family: the response of training perturbations whose targets resemble
the new target, averaged over the k closest by co-expression, shared gene sets, protein interactions or symbol
family (`similar_pert_knn`, `knn_response_geneset`, `ppi_kernel_weighted_response`, `knn_perturbation_response_*`
in `docs/results/selection_replay.md`). pearson_delta is per perturbation and scale-free, so the per-perturbation
magnitude features the agents also found (`target_level`, `target_mean_abs_response`) cannot raise it. What is
missing is the *pattern* of the response for held-out perturbations whose target has no close training
neighbour: nearest-neighbour transfer has nothing to copy there, and the model falls back to the mean response.

## Two free checks first

1. **Were the runs still improving at minute 20?** `python tools/time_to_best.py --runs <run dirs> --out
   docs/results/time_to_best.md` follows each run's running best visible score and reports the minute of the
   last improvement, the share of the final gain reached at 25/50/75% of the budget, and how many experiments and
   planner rounds came after it (visible scores only; the sealed set is never read). If most runs went flat well
   before the deadline, longer runs alone will not help and the lever is a new family. If most were still
   rising in the final quarter, a 60-minute run is the cheaper test.
2. **A fitted transfer over a low-rank response basis**, `response_components`, now the eighth hypothesis of the
   scripted no-LLM control (`genemila/providers/mock.py`, `SCRIPTED_HYPOTHESES` and `TEMPLATES["components"]`).
   Leave-one-out SVD of the training perturbations' centred delta profiles gives a few response components; a
   kernel ridge from the target's annotations (shared gene sets, shared interaction partners, shared TF-network
   partners) to the training perturbations' weights predicts the new target's weight on each component; the
   feature's columns are weight × component. Unlike top-k transfer it can place a target with no close
   neighbour by its annotations, uses every training perturbation with fitted (possibly negative) weights, and
   denoises through the low-rank basis. One control run on the Mac costs nothing (no LLM calls, about three
   minutes of CPU) and, because the control is deterministic, a single run measures it: its sealed score is read
   once at the end as always, next to the control's 0.554 at the previous code versions. The new control is its
   own arm (code version in the label), as every code change is.

## The paid step, only on Andres's word

If the new family raises the control, promote `response_components` to a built-in feature so every arm starts
from it (the starting model then changes with the code version, and the tables must key the "start" row by code
version), and run two Opus-planned 4-worker 20-minute runs (seeds 0 and 1) at the new code version. Cost per
run: about $0.35 of DeepSeek worker calls plus about $3 of Claude Opus planner usage (the CLI's estimate); the
DeepSeek ledger stands at $10.25 of the $15 cap. What would count: both seeds above 0.61 sealed pearson_delta
with the DE columns no worse, compared against the two new-code Opus runs (0.601, 0.587) at the same worker
count. If the family does not raise the control, the result is still recorded (the control's row at this code
version) and the next candidate is tested the same free way before anything is paid for.

Nothing here touches the sealed set before a run's end-of-run oracle, and no selection rule or hyperparameter is
chosen on it.
