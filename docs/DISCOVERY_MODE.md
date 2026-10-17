# Discovery mode: hypothesis generation driven by the data

Claim [#69](https://github.com/andresloak100/Gene-Mila/issues/69), 17 October 2026. Code: `genemila/discovery.py`;
settings `schedule.discovery`, `schedule.discovery_dry_rounds`, `schedule.discovery_derived_r2` in
`configs/default.toml`; tests `tests/test_discovery.py`. Off by default: a run without `schedule.discovery=true` has
the same planner state, prompts, experiment hashes and summary as before, byte for byte (the frozen tests in
`tests/test_norman_templates.py` hold them).

## 1. What Andres asked for, and what this answers

On 17 October Andres asked the lab to find the biological feature the linear model lacks: "in what should we take a
look to be able to find a biological feature", automated rather than a fixed list ("this should be automatized not a
fixed number"), something that can eventually be tested in vitro, and relevant to a Nature Genetics paper (goal A of
`docs/GOAL_CRITERIA.md`, criterion A.1: a feature the agents found with no human-given hypothesis).

Blocks F and G show what the agents do with the current planner. Of the 499 features the block G agents built on the
clean bundles (`docs/results/*_g_plugins`), about 180 describe themselves as a product of two existing quantities or a
random projection of a table, 101 call `ctx.feature` to transform a feature the model already had, and none passed
the fair test. The planner had three gaps, all in the lab code rather than in the agents:

1. it never saw where its own model fails: the research state carries scores and coefficients, not residuals;
2. its "unexplored" list was a fixed bank of eleven idea areas matched by keyword (`research_state.IDEA_BANK`), with
   "interaction of existing features" among the ideas, so a hypothesis counted as new once its wording matched;
3. nothing measured whether a new feature was a transform of what the model already had.

Discovery mode closes the three gaps inside the run, so the number of hypotheses is decided by the data and the
bundle's inputs, never by a count, and the lab rather than the planner judges what is new.

## 2. What the planner gets

Each planner round in discovery mode replaces the UNEXPLORED IDEA AREAS section of the research state by two sections
(`discovery.state_sections`, rendered by `research_state.render_state` within its usual budgets):

**RESIDUAL EVIDENCE.** The current best modelled experiment's out-of-fold predictions of the training perturbations
(its `cv.npz`, the same folds the selection rule uses) are compared with the training labels, nothing else. The
section lists: the worst-predicted training perturbations with what the knowledge files hold about their targets
(gene sets, network partners, the nearest training perturbation by shared sets, the most co-expressed training target);
the genes that carry the squared residual, the control statistics and annotation columns their residual follows
(Spearman), the gene sets and regulator neighbourhoods they are enriched in (hypergeometric, uncorrected, for
generation only); the genes consistently under- and over-predicted; and whether the residual holds a low-rank shared
pattern (its first singular component against a permutation null) or is diffuse. It is recomputed only when the best
experiment changes and written to `runs/<run>/planner/discovery_<EXP>.json`. It is `tools/residual_mining.py`
(`docs/NOVEL_FEATURE_NEEDS.md`, M1) made live. Before any model has completed, the section says so and the planner
proposes from the inputs.

**INPUTS UNEXPLORED.** The bundle's inputs, enumerated rather than listed by hand: the control statistics
(`control_cells`, `control_mean`, `control_std`, `gene_corr`), the training labels (`train_delta`), the targets, every
knowledge file with its kind and size, and every column of a per-gene table (gene annotation, constraint, protein
tables). For each, how many completed features read it plainly and how many only inside a feature that transforms
another feature (`ctx.feature`), from the plugins' sources (`discovery.feature_reads`). The section ends with the forms
a feature can take and the rule: a feature is new when it reads an unread input plainly; a product, ratio, log, rank
or projection of existing columns is derived.

The planner prompt (`prompts.planner_user`) adds a note and three fields to `new_feature` when the state carries the
RESIDUAL EVIDENCE heading: `new_input` (the exact name of the unread input the feature reads), `mechanism` (the biology
it encodes) and `predicted_sign` (the sign its coefficient must have if the mechanism is right). The feature lists of
the state show `derived_r2` for every scored feature (section 3). The EXPLORE focus of concurrent planner rounds points
at the two sections instead of the idea list.

## 3. What the lab measures

**Novelty.** After each parsed round the lab, not the planner, decides which hypotheses name an input no completed
feature has read (`discovery.judge_plan`: the `new_input` field, or an unread input's name in the feature's text; a
table column counts by its bare name too). The verdict rides into each experiment as
`proposed_feature_json["novel_inputs"]`, the round goes to `runs/<run>/planner/discovery_rounds.json` and a
`discovery_round` event.

**Derivability.** For every new feature the pipeline fits the feature's columns from its parent's columns, their
squares and the pairwise products of the first ten, by ridge, out of fold by perturbation, on a seeded sample of
(perturbation, gene) rows of the standardised design matrix (`discovery.derivability`). The out-of-fold R² is stored in
`diagnostics_json["derivability"]`; a feature at or above `schedule.discovery_derived_r2` (0.8) is the lab meeting's
"stale" feature, measured: a product, log or interaction of what the model already had. The threshold labels; it does
not reject (a derived feature still runs and is scored like any other).

**The stop rule.** After `schedule.discovery_dry_rounds` (3) consecutive parsed rounds in which no hypothesis names an
unread input, the planner is dry (`Planner.dry`), a `discovery_dry` event is logged once, no further planner call is
made, and the exploit engine finishes the run. A round that names an unread input resets the count. So a run
generates as many hypotheses as the evidence and the inputs support, and stops when the planner has nothing new to
read.

`summary.json["discovery"]` records the rounds, how many hypotheses named an unread input and which inputs, the round
the planner went dry, every scored feature with its R² and its novel inputs, and the evidence files.

## 4. Integrity

- The evidence reads the training labels (`public.npz`) and the best experiment's out-of-fold predictions of the
  training perturbations. It never reads the visible validation tier, the sealed tiers, `splits.json` or the oracle;
  `tests/test_discovery.py` checks the source for those names and builds the state with the validation labels
  withdrawn. The evidence steers what the planner proposes; it is not used to select anything.
- Hypothesis generation only. A feature discovery mode leads to is evidence only when it passes the fair test
  (`tools/feature_compare.py`, `docs/FEATURE_COMPARISON_PROTOCOL.md`) on a tier the generator never read, and A.1 of
  `docs/GOAL_CRITERIA.md` is met only by that test, replicated (A.3), with its mechanism and sign (A.2) and a fresh
  test (A.4). `predicted_sign` is recorded so the sign can be checked against the fitted coefficient after the fact;
  `tools/wetlab_candidates.py` turns a passing feature into the wet-lab prediction package (`docs/WETLAB_CANDIDATES.md`).
- A run in discovery mode is its own arm. It is never pooled with runs of the same planner without it, in any table.
- Protected code (`genemila/benchmark/`, the split logic, `genemila/guard.py`) is untouched. The pipeline change is a
  diagnostic computed after the fit from the design matrix the fit already had.

## 5. How to run it

Free, no key, no approval (the scripted planner and the mock worker; the mock templates never name an input, so the
planner goes dry after `discovery_dry_rounds` rounds and the exploit engine finishes; what it shows is the mechanics):

```
python run_research.py --dataset synthetic --planner-provider scripted --worker-provider mock \
    --minutes 2 --set schedule.discovery=true
```

A real-data run is the lead's call (`docs/ROADMAP.md`), on Andres's written approval of its spend, on the Mac, with the
usual caps and the shared ledger, and `--set schedule.discovery=true` added to the arm's command. It needs an LLM
planner (the note and the fields are for it) and a bundle with knowledge files worth reading: the clean tier-1 bundles
of block G (`docs/PLAN_G_CLEAN_ARM.md`), whose three tables give the inputs list its columns. The honest odds: blocks F
and G found nothing that passes the fair test; this mode changes what the planner is shown and how the run judges
novelty, not the ceiling (`docs/NOVEL_FEATURE_NEEDS.md`: the hindsight transfer mix reaches 0.734 to 0.780 against about
0.60 out of fold, and that gap is the room a new feature has). A first run tells whether the planner, shown its errors
and the unread inputs, proposes features that read them (the summary's `hypotheses_naming_an_unread_input` and
`new_input_features`), and whether any of them helps out of fold; the fair test then says whether anything passes.

What a run in discovery mode reports, from its directory: `summary.json["discovery"]`, `planner/discovery_rounds.json`,
`planner/discovery_<EXP>.json` for each best experiment, `planner/plan_<round>.json` with the `new_input`, `mechanism`
and `predicted_sign` of every hypothesis, and `diagnostics_json["derivability"]` on each new-feature experiment.
