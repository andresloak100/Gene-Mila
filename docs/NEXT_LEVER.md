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

## Results of the two free checks (02:30 UTC 2026-10-05, code 74e07ca)

- **Time to best, 26 runs** (`tools/time_to_best.py`, visible scores only; its first version measured from the
  "predict no change" baseline and overstated how early the gain arrived, fixed in bee2106): 60 to 92% of each agent
  run's final gain is there after five minutes and 74 to 97% after ten; the last quarter adds +0.000 to +0.004 in 11
  of 13 agent runs. The two exceptions (+0.007 and +0.011) are 8- and 16-worker runs on the old code, the same runs
  whose visible gains did not carry to the sealed set. On the new code with the Opus planner the curve is flat after
  the midpoint (+0.003 and +0.005 in the last ten minutes). Longer runs are not the lever.
- **The control with `response_components`** (`control_components_w4_r0`, 182 s, 179 experiments, deterministic):
  sealed pearson_delta **0.593**, against 0.554 for the seven-hypothesis control and 0.584 to 0.602 for the agent arms
  at 4 workers; MSE_DE 0.142, PCC_DE 0.943, R²_DE 0.755 (agents 0.117 to 0.124, 0.953 to 0.955, 0.79 to 0.80). Best
  model: ridge, alpha 41,310, on mean_response, is_target, response_components, target_level. On its own the feature
  scored +0.020 visible over its parent. Its selection score (0.531) underestimates its sealed score by 0.062, the
  largest gap of any run; the agent runs on the same code are within 0.014.

What it changes: on sealed pearson_delta the agents' margin over a no-LLM control is gone once the control has one
good transfer feature; on the DE-gene metrics the agents still lead. Two cautions travel with the number: the feature
was written after the agent runs had shown that transfer between related targets is what works, so it is a
hand-written feature informed by the agents' findings, not what one gets without agents; and it was designed after
26 sealed results on this split had been read, so 0.593 is not as clean a held-out number as the agent runs' are.
One run, one seed, untuned (n_components 4, kernel alpha 1.0). Its clean test is Norman.

## The warm start settles it (03:10 UTC 2026-10-05, code bee2106)

`control_components_from_opus_r0`: the scripted control continued from `newcode_opus_w4_r0`, so it started from the
agents' 12 features and best model and re-searched without an LLM for the full 20 minutes (1,316 experiments, 1,304 of
them the exploit engine's; 211 included `response_components`, 36 of those together with the agents' kNN features).
Best model: ridge, alpha 4,590, eleven of the agents' features plus the scripted `target_level`; `response_components`
was not selected, and the best model that included it scored 0.5846 visible against 0.5908 without it. Sealed
pearson_delta 0.5997 against 0.6007 for the agents' own run; MSE_DE 0.119 against 0.118, R²_DE 0.800 against 0.802.
In the tables this run is "no-LLM continuation of newcode_opus_w4_r0": its result is the agents' model re-searched,
not a control's (the generators were fixed in 0774b42 after the first regeneration labelled it a control and the
scaling report took it for the equal-time no-LLM reference).

What follows:

- The hand-written feature and the agents' kNN features carry the same signal. Alone, either reaches 0.59 to 0.60;
  together they reach no further. About 0.60 sealed pearson_delta is where transfer between related targets tops out
  on this split, and 1,300 further experiments around the agents' feature set moved nothing.
- The paid step proposed above (agent runs starting from the new feature) is withdrawn: the free warm start already
  shows it would buy nothing. Nothing paid is running; the DeepSeek ledger stays at $10.25.
- Next is Norman et al. 2019, where the lab and the hand-written feature both get a clean test. Raising Adamson
  further would need information of a different kind, such as responses measured for the same or related targets in
  other K562 screens (Replogle et al. 2022 is in the same scPerturb archive); that is a different task from
  predicting an unseen perturbation from this dataset alone, would not be comparable with CellForge's protocol, and
  is Andres's call to make before any of it is built.
