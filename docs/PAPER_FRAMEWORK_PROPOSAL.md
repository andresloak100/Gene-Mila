# Gene-Mila: a framework for agent-built, interpretable perturbation features

Proposal written 2026-10-15 on Andres's requests of 13 and 15 October. It sets out what the paper would claim, how
the claim is tested, and what has to be built or decided first. It is a proposal: nothing here has run.

## 1. The claim the paper would make

LLM agents, working in a fixed harness, can discover **features** (small, readable pieces of code that use public
biological knowledge) that make a **simple linear model** predict post-perturbation expression as well as, or
better than, much larger systems, and the features themselves say which biological signal carries the prediction.

The unit of contribution is the feature, not the model. A feature counts as meaningful only if:
1. adding it to a fixed linear model improves a held-out score that the agents never saw;
2. the gain repeats across independent seeds of the search;
3. it is not a copy of a feature the base model already has (redundancy check);
4. a reader can say what biology it encodes (its knowledge source and formula).

## 2. The framework (an autoresearch-style harness for features)

Modelled on karpathy/autoresearch: one fixed harness, one file the agent may edit, a fixed time budget, and a
keep-or-discard rule on one metric.

| part | autoresearch | Gene-Mila |
|---|---|---|
| fixed harness, never edited by agents | `prepare.py`: data, loader, evaluation | data bundles, splits, evaluator, ridge fit, cross-validation, guard (all in `genemila/`) |
| what the agent edits | `train.py` | one feature plugin per experiment (`feature_store/<name>.py`) |
| instructions written by the human | `program.md` | planner and worker prompts, knowledge files |
| budget | 5 minutes per experiment | fixed wall time per run (20 min), cost caps |
| keep or discard | validation bits per byte improves | visible score improves by more than fold noise, under gene-grouped CV |
| hidden test | none | sealed set behind an oracle, plus a test set held outside the Mac (section 4) |

What the lab already has and the paper can use as is: the harness, the guard (no label leakage, no `hash()`/`id()`,
no set-order dependence), the sealed oracle with a query cap, pre-specified readings with paired statistics, the
feature audit (redundancy, drop-one, Lasso stability, compact set), and full provenance of every feature and run.

What tonight's and earlier results say must change for a publishable loop:
- **Overfitting to the visible set is the main failure.** Gains on visible data shrink on held-out data (B2: +0.030
  visible against +0.004 sealed for a single model; N4: +0.008 that did not repeat over three seeds).
- **Fixes, all already tested in part:** start from the strongest simple rule (the additive start helped: B2's arm
  beat the additive rule on held-out data, +0.011, where every earlier arm did not); admit a feature only when its
  gain exceeds fold noise under two fold seeds; average the models of several independent searches (the combined
  model was the most stable result in both B1 and B2); cap model size (the audit shows most features add nothing).
- **Exploration balance:** a fixed share of each run's budget for new feature families (knowledge sources not yet
  used) and the rest for refining kept features, so the search does not spend its time on near-duplicates (the
  audit found most of Astra's 176 columns were re-mixes of the same few signals).

## 3. Baselines and comparisons

| system | what it produces | how we run it | status |
|---|---|---|---|
| mean response, additive rule, ridge on built-in features | fixed predictors | in the lab, free | done |
| hand-written features (scripted control) | ~10 fixed templates | in the lab, free | done |
| **Gene-Mila multi-agent loop** (ours) | features plus ridge | in the lab, DeepSeek | done on Adamson and Norman |
| single-agent autoresearch-style loop | features plus ridge | same harness, one agent, same budget | to build (small) |
| Biomni | general biomedical agent | given the same task and budget | to run; CellForge reports it produced no executable code on Norman |
| CellForge | an agent-designed deep model | their code on our splits | needs a GPU |
| STATE (Arc, bioRxiv 2025.06.26.661135) | pretrained transition model | their released model, if available | needs a GPU; their Cell-Eval is already our evaluator |
| GEARS, CPA, linear models of Ahlmann-Eltze et al. | published methods | their code on our splits | GEARS needs a GPU; linear ones are free |

**Feature-level comparison**, the part that is new: for each system that produces features (ours, the
single-agent loop, Biomni if it runs, CellForge's design notes), list the features or signals it used, then test
each one by the same rule: add it to the same fixed ridge on the same split and read the held-out gain.

## 4. Evaluation protocol

**Data, three tiers.**
1. Development: training plus visible validation perturbations. The agents see these.
2. Sealed test: scored only through the oracle at the end of a run. Agents never see it, but the people running
   the lab have read it many times on Adamson, so a fresh one is needed for the paper.
3. **Fresh test held outside the orchestration** (Andres's 13 October request): a split, or a second dataset,
   whose labels are not on the Mac at all. A separate evaluator (a different account or machine) holds them and
   scores frozen predictions once. Candidates: a new gene-grouped split of Norman never scored; Replogle 2022 K562
   essential-gene screen genes not in Adamson; or a different cell line (Replogle RPE1) for transfer.

**Metrics, reported for every system and every test tier.**

| metric | what it measures | why |
|---|---|---|
| pearson_delta (primary) | correlation of predicted and measured change from control, all genes | the lab's selection metric |
| pearson_delta without own targets | the same, excluding the perturbed genes | removes the trivial knockdown signal |
| MSE, all genes | absolute error in expression | CellForge's table |
| PCC and R2 on the top 20 changed genes | accuracy where the biology is | CellForge's DE metrics |
| direction accuracy on changed genes | sign of change right or wrong | VCWorld's task |
| Cell-Eval overlap@N and DE recall | whether the right genes are called changed | STATE's evaluator |
| by category: singles, pairs with 0, 1, 2 genes seen | where the gain comes from | Norman's structure |

Reading rule, fixed in advance as now: a gain counts only when it exceeds twice its paired standard error and wins
on more than half the perturbations, pooled and per category; spreads over seeds are always reported.

## 5. Where the results stand now (held-out sets already used, so indicative only)

| dataset | model | pearson_delta | MSE | PCC | R2 | MSE_DE | PCC_DE | R2_DE |
|---|---|---|---|---|---|---|---|---|
| Norman | additive rule | 0.713 | 0.0059 | 0.988 | 0.972 | 0.102 | 0.941 | 0.846 |
| Norman | scripted features + Replogle (N2) | 0.719 | 0.0054 | 0.989 | 0.975 | 0.110 | 0.937 | 0.842 |
| Norman | agents from additive start, combined (B2) | 0.727 | – | – | – | – | – | – |
| Norman | CellForge, as reported (other split) | – | 0.0034 | 0.985 | 0.961 | 0.174 | 0.811 | 0.598 |
| Adamson | start | 0.520 | 0.0070 | 0.985 | 0.966 | 0.154 | 0.932 | 0.734 |
| Adamson | agents' features + Replogle, no LLM | 0.646 | 0.0044 | 0.990 | 0.979 | 0.074 | 0.970 | 0.868 |
| Adamson | CellForge, as reported (other split) | – | 0.0051 | 0.988 | 0.976 | 0.201 | 0.947 | 0.891 |

CellForge's rows are not comparable: their split, scale and evaluation code are unpublished, and the additive rule
alone beats their reported Norman DE metrics on our split, which points to different evaluations. A fair comparison
needs their model run through our evaluator on our splits.

## 6. Decisions needed from Andres

1. **Who holds the fresh test set** (section 4, tier 3): a second account or machine that the agents and this Mac
   cannot read. Without it the paper's main number is not clean.
2. **A GPU** for the deep baselines (CellForge, STATE, GEARS): a rented machine for a few days.
3. **Which external dataset** for the fresh test and for transfer.
4. **Budget** for the comparison runs (our loop over several seeds and datasets, the single-agent loop, Biomni):
   roughly $10 to $30 of DeepSeek at tonight's real cost of about $0.6 per run.

## 7. Order of work

1. Write this protocol into the repository and freeze it before any new run (the paper's preregistration).
2. Build the single-agent autoresearch-style variant and the feature-level comparison tool (free).
3. Set up the fresh test holder; build the fresh split there.
4. Run every system on development data; freeze predictions; score once on the fresh test.
5. Run the deep baselines on a GPU through the same evaluator.
6. Write the paper around the feature table: which features, which knowledge, how much each adds, how stable.

Sources: karpathy/autoresearch (github.com/karpathy/autoresearch); Biomni (biomni.stanford.edu; Huang et al.,
PubMed 40501924); CellForge (arXiv 2508.02276, which reports Biomni producing no executable code on Norman);
STATE (Adduri et al., bioRxiv 10.1101/2025.06.26.661135, Arc Institute; introduces Cell-Eval).
