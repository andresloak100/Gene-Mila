"""All LLM prompts in one place. Kept compact on purpose: workers get only
what one experiment needs, the planner gets the compressed research state."""

from __future__ import annotations

import json

PLANNER_SYSTEM = """You are the principal investigator of an autonomous computational biology lab.
The lab predicts post-perturbation gene expression (pseudobulk of perturbed cells, unpaired with controls)
for UNSEEN perturbations using deliberately simple linear models (ridge/lasso/OLS). One linear model is shared
across all (perturbation p, gene g) rows and predicts delta[p,g] = perturbed - control expression of g.
Scientific progress must come from FEATURES of (p, g): biologically or statistically motivated signals.

You do not run experiments. Python workers implement and test them; numbers decide what is better.
Rules you must respect:
- Each experiment tests ONE clear idea (one new feature, or one combination/ablation, or one sweep).
- Never propose touching data splits, evaluation, metrics, or hidden/query-only labels.
- Features may use training labels only leave-one-out (excluding the row's own perturbation).
- Parameter sweeps are run by Python without LLM workers: use action "sweep" for them.
- Balance exploration, exploitation and a few high-risk ideas as instructed.
- Learn from failed and negative results; don't repeat them.
Respond with a single JSON object and nothing else."""

PLANNER_SCHEMA = {
    "synthesis": "2-5 sentences: what the evidence says so far",
    "hypotheses": [{
        "title": "short name",
        "hypothesis": "testable statement",
        "rationale": "biological/statistical reasoning",
        "category": "explore | exploit | risky",
        "action": "new_feature | combine | ablate | sweep",
        "parent": "EXP_xxxx whose feature set to start from, or null for the current best",
        "new_feature": {"name": "snake_case_name", "description": "what (p,g) -> value(s) it computes",
                        "implementation_hint": "concise algorithm", "params": {"param": "default"}},
        "add_features": ["for combine: existing feature names to add"],
        "remove_features": ["for ablate: feature names to remove"],
        "model_type": "ridge | lasso | elasticnet | ols",
        "sweep": {"target": "alpha_grid | feature_params.<feature>.<param>", "values": [1, 2, 3]},
        "replicates": "1-3; >1 sends the same idea to independent workers for diverse implementations",
    }],
}


# ----------------------------------------------- bundles with pairs of genes or a recorded modality (Norman 2019)
# docs/NORMAN_PLAN.md section 4, item 11. A bundle whose perturbations include pairs of genes, or whose manifest records
# the screen's modality, gets a longer DATASET line (dataset_line, written by lab.data_summary) and, with pairs, a
# note on pairs in the planner's user message and in the worker's API text. The notes are keyed on the DATASET line
# the prompts already carry (dataset_flags), and PAIR_KEYS is written by dataset_line alone, so every other bundle
# (Adamson's: single targets, no modality) gets the prompts above and below byte for byte as before. PLANNER_SYSTEM
# is a constant the providers send as it is, so the pair note goes in the user message.

PAIR_KEYS = ("a perturbation of several genes is named by its genes in alphabetical order joined by '+' (A+B), a "
             "single by its gene's name")
MODALITY_MARK = "; modality "
MODALITY_TEXT = {"crispra": "CRISPR activation: a perturbation raises its target genes' expression",
                 "crispri": "CRISPR interference: a perturbation lowers its target genes' expression",
                 "crisprko": "CRISPR knockout: a perturbation disrupts its target genes"}


def bundle_has_pairs(targets: dict) -> bool:
    """Whether any perturbation of a bundle's targets.json targets more than one gene."""
    return any(len(set(v or [])) > 1 for v in targets.values())


def dataset_line(manifest: dict, targets: dict, train: list[str]) -> str:
    """The DATASET line of a bundle with pairs or a recorded modality: with pairs, the training perturbations counted
    by their number of target genes and the key rule (PAIR_KEYS); the modality when the manifest records one, glossed
    when it is a CRISPR modality the lab knows. Counts are of training perturbations only, so nothing is said about
    the held-out sets beyond that they hold singles and pairs, as targets.json, public to every feature, shows."""
    pairs = bundle_has_pairs(targets)
    if pairs:
        sizes = [len(set(targets.get(p) or [])) for p in train]
        counts = [(sum(s == 1 for s in sizes), "single genes"), (sum(s == 2 for s in sizes), "pairs of two genes"),
                  (sum(s > 2 for s in sizes), "of three or more genes"),
                  (sum(s == 0 for s in sizes), "without a measured target")]
        kind = ", ".join(f"{n} {what}" for i, (n, what) in enumerate(counts) if n or i < 2) + f"; {PAIR_KEYS}"
    else:
        kind = "single-gene targets"
    modality = str(manifest.get("modality") or "").strip()
    gloss = MODALITY_TEXT.get(modality.lower().replace(" ", "").replace("-", ""))
    mod = f"{MODALITY_MARK}{modality}" + (f" ({gloss})" if gloss else "") if modality else ""
    unseen = "unseen perturbations, single genes and pairs" if pairs else "unseen perturbations"
    return (f"{manifest['name']}: {manifest['n_genes']} genes, {manifest['n_control_cells']} control cells, "
            f"{manifest['n_train']} training perturbations ({kind}){mod}; predict {unseen}.")


def dataset_flags(text: str) -> dict:
    """What the DATASET line in `text` says beyond Adamson's: {"pairs": the bundle has pairs, "modality": it records
    its modality}, both False for any line dataset_line did not write. `text` is a research state (the line after its
    "## DATASET" heading is read) or the line itself, as a worker task carries it; nothing else in a state is read,
    so a hypothesis that happens to quote these words changes nothing."""
    _, heading, rest = text.partition("## DATASET\n")
    line = (rest if heading else text).split("\n", 1)[0]
    return {"pairs": PAIR_KEYS in line, "modality": MODALITY_MARK in line}


PAIRS_PLANNER_NOTE = (" Perturbations here are single genes and pairs of genes (see DATASET): say how a feature treats "
                      "a pair, using both of its genes so their order does not matter; the action \"combine\" means "
                      "a feature-set combination (existing features added to one model), never a combination of "
                      "genes. The baselines in the state are reference predictions, not features: no model contains "
                      "the additive baseline's prediction (a perturbation's change as the sum of its genes' single-gene "
                      "training changes) unless one of its features computes it, as the built-in feature "
                      "additive_response does.")
PLANNER_SCHEMA_PAIRS = {**PLANNER_SCHEMA, "hypotheses": [
    {**PLANNER_SCHEMA["hypotheses"][0],
     "add_features": ["for combine (a feature-set combination): existing feature names to add"]}]}


def planner_user(research_state: str, n: int, mix: dict) -> str:
    pairs = dataset_flags(research_state)["pairs"]
    return (
        f"RESEARCH STATE\n{research_state}\n\n"
        f"Propose {n} experiments. Target mix: about {mix.get('explore', 0):.0%} explore (new ideas), "
        f"{mix.get('exploit', 0):.0%} exploit (refine/combine what works), {mix.get('risky', 0):.0%} risky "
        "(unusual, high-variance ideas). Prefer new_feature actions for exploration. Only reference features "
        "listed in the state." + (PAIRS_PLANNER_NOTE if pairs else "") + " Return JSON with this shape:\n"
        + json.dumps(PLANNER_SCHEMA_PAIRS if pairs else PLANNER_SCHEMA, indent=1)
    )


WORKER_SYSTEM = """You are a careful research engineer. You implement exactly ONE feature for a linear model
that predicts perturbation responses. Output exactly one Python code block containing the complete plugin file
and nothing else. Use only numpy/scipy/sklearn and genemila.features.api. No file, network or OS access.
Vectorise with numpy; the feature must run in seconds."""

FEATURE_API_DOC = """from genemila.features.api import Feature, FeatureContext, register

@register
class MyFeature(Feature):
    name = "<feature_name>"   # must equal the requested name
    version = 1
    description = "..."; rationale = "..."
    inputs = ["control_cells", ...]    # which ctx inputs are used
    params = {"k": 10}                 # defaults; actual values arrive in `params`
    dim = 1                            # number of output columns
    def compute(self, ctx: FeatureContext, perts: list[str], params: dict) -> np.ndarray:
        # return float array of shape (len(perts), ctx.n_genes, dim), finite values only
        ...

FeatureContext (read-only):
  ctx.genes: list[str]; ctx.n_genes; ctx.gene_index: dict gene->column
  ctx.control_cells: (n_cells, n_genes) float control expression (log-normalised)
  ctx.control_mean, ctx.control_std: (n_genes,)
  ctx.gene_corr: (n_genes, n_genes) Pearson correlation across control cells (cached)
  ctx.perts: all perturbation ids; ctx.train_perts: training perturbation ids
  ctx.target_indices(p) -> list[int] gene columns targeted by p (may be empty if target not measured)
  ctx.target_genes(p) -> list[str]
  ctx.train_delta(exclude=p) -> (pert_ids, array (n, n_genes)) training deltas WITHOUT p.
      LEAKAGE RULE: when computing rows for perturbation p you MUST call train_delta(exclude=p).
  ctx.knowledge(name) -> parsed JSON prior knowledge or None; ctx.available_knowledge() -> names
  ctx.feature(name, perts, params=None) -> another registered feature's array (composition)
  ctx.cache: dict you may use to memoise work shared across perturbations"""

EXAMPLE_FEATURE = '''import numpy as np
from genemila.features.api import Feature, register

@register
class MeanResponse(Feature):
    name = "mean_response"
    description = "Average delta of gene g across training perturbations, leaving p out."
    rationale = "Many perturbations share a generic stress/response program."
    inputs = ["train_delta"]
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            out[i, :, 0] = d.mean(axis=0)
        return out
'''


TARGET_API_LINE = "  ctx.target_genes(p) -> list[str]\n"
PAIRS_API_NOTE = """  PAIRS: perturbations here are single genes and pairs. ctx.target_genes(p) is an unordered set of 1 or 2 genes
      (the list's order means nothing): use every target (a sum, mean or max over them, or a block of gene_corr),
      never only [0], so a pair gives the same values whichever order its genes are listed in. Ids: a single is
      its gene's name, a pair is "A+B" with A and B in alphabetical order; gene g's single, when there is one, is
      the perturbation whose id equals g.
"""


def feature_api_doc(pairs: bool = False) -> str:
    """FEATURE_API_DOC, with PAIRS_API_NOTE after the target_genes line for a bundle with pairs."""
    return FEATURE_API_DOC.replace(TARGET_API_LINE, TARGET_API_LINE + PAIRS_API_NOTE, 1) if pairs else FEATURE_API_DOC


def worker_implement(task: dict) -> str:
    # Static reference material first, task-specific text last: providers with prefix caching
    # (DeepSeek, OpenAI, Anthropic) then bill the shared prefix at the cache-hit rate.
    nf = task["new_feature"]
    api = feature_api_doc(dataset_flags(task.get("data_summary") or "")["pairs"])
    return (
        f"API:\n{api}\n\nEXAMPLE PLUGIN:\n```python\n{EXAMPLE_FEATURE}```\n\n"
        f"DATA: {task['data_summary']}\n"
        f"Prior knowledge files: {task['knowledge_summary']}\n\n"
        f"EXPERIMENT {task['experiment_id']}\n"
        f"Hypothesis: {task['hypothesis']}\nRationale: {task['rationale']}\n"
        f"Other features in this model (do not duplicate them): {task['existing_features']}\n\n"
        f"Implement feature `{nf['name']}`: {nf.get('description', '')}\n"
        f"Implementation hint: {nf.get('implementation_hint', '')}\n"
        f"Suggested params: {json.dumps(nf.get('params', {}))}\n"
        f"Write the file genemila/features/plugins/{nf['name']}.py."
    )


def worker_diagnose(task: dict, code: str, error: str) -> str:
    nf = task["new_feature"]
    api = feature_api_doc(dataset_flags(task.get("data_summary") or "")["pairs"])
    return (
        f"API:\n{api}\n\n"
        f"Hypothesis being tested: {task['hypothesis']}\n"
        f"YOUR CODE for feature `{nf['name']}`:\n```python\n{code}```\n\n"
        f"It failed validation with this ERROR:\n{error[-1500:]}\n\n"
        "Return the complete corrected file in one python code block."
    )


SUMMARY_SYSTEM = ("Summarise the research state for a scientist in under 200 words: what works, what failed, "
                  "and the most promising next direction. Plain text.")
