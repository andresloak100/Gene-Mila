# Brief for a new agent: what Gene-Mila is for, where it stands, how we work

Written 2026-10-17 by the lead (Claude, claim [#41](https://github.com/andresloak100/Gene-Mila/issues/41)) for an agent
joining the project: a Claude session, Astra, or any other. It is the plain-language overview. The live state is
always [`HANDOFF.md`](../HANDOFF.md) section 1; the rules are [`AGENTS.md`](../AGENTS.md); the decisions are
[`ROADMAP.md`](ROADMAP.md). When this brief and those three disagree, they win, and this brief gets a dated note.

## 1. The project in one paragraph

Gene-Mila is an autonomous laboratory. LLM agents (a planner and several workers) write small Python "features" for a
deliberately simple linear model (ridge in the fair test and the comparison; the lab also allows lasso, elastic net
and OLS) that predicts how every gene's expression changes when one gene is switched off or on in K562 cells (the
Adamson CRISPRi and Norman CRISPRa Perturb-seq screens). The model is scored on perturbations it has never seen. A
Python controller, never an LLM, owns the clock, the money and the scoring. Because the model is linear and the
features are code, every gain is a feature a person can read. The owner is Andres (GitHub `andresloak100`, a biologist). The real
data live only on his Mac; this public repository is the single source of state for every agent.

## 2. The two goals, set by Andres and his machine-learning collaborator on 15 October 2026

- **Goal (a), the biology paper.** The agents discover a genuinely new, biologically meaningful rule about how cells
  respond to a genetic perturbation, testable in the wet lab, publishable in Nature Genetics. Andres said on
  17 October that a collaborating lab would run the wet-lab test if our computational evidence is solid.
- **Goal (b), the methods paper.** Otherwise, a comparison of our system against other agent systems (Biomni, an
  autoresearch-style coding agent, CellForge's ideas) on the identical task, "feature plus one linear model", with one
  fair metrics table.

The decision rule for "goal met" is [`GOAL_CRITERIA.md`](GOAL_CRITERIA.md): six criteria for (a) and five for (b).
Five of (a)'s and all of (b)'s were fixed before any block F score was read; the sixth, novelty, was added after block
F's reading and before any replication, and can only make "goal met" harder. The lead reports "goal met" or "not yet"
against it at every milestone. As of this brief: **not yet, on either path**.

## 3. The biology question, precisely

What the agents get: a bundle with the expression data (training perturbations only; validation and test are held
out), the genes each perturbation targets, and knowledge files. Since block G the knowledge is "tier 1" only: curated
pathways and complexes (Reactome, GO restricted to curated and experimental evidence codes, CORUM), a curated
regulator network (CollecTRI), physical protein interactions (STRING, experiments and database channels only), and, in
half the runs, three per-gene tables built from the genome (GENCODE and hg38), population genetics (gnomAD constraint)
and protein annotation (UniProt). No perturbation screen, no expression atlas: nothing that could encode the answer.
The policy is section 7 of [`NOVEL_FEATURE_NEEDS.md`](NOVEL_FEATURE_NEEDS.md).

What "found" means: a feature passes the fair test ([`tools/feature_compare.py`](../tools/feature_compare.py)): a gain
over the parent model out of fold, above twice its standard error and above a minimum effect of 0.002, positive in
every fold seed, wins on more than half the perturbations, beats two matched permutation nulls with a family-wise
correction, with its coefficient sign saved. What "new" means: the mechanism is not already published for this
modality. The known rules are written down before any score is read, in
[`PREREG_G_KNOWN_BIOLOGY.md`](PREREG_G_KNOWN_BIOLOGY.md), with citations in
[`CANDIDATE_LITERATURE_CHECK.md`](CANDIDATE_LITERATURE_CHECK.md): CRISPRa raises highly expressed, CpG-island
promoters least; dCas9 acts in cis on a neighbouring promoter; gene length and TSS density proxy basal expression;
essential and constrained genes respond most; secretory-pathway knockdowns hit ER-targeted messages. One family is
genuinely open and pre-registered as the lead's own hypothesis: whether a gene's population constraint predicts its
response once basal expression and essentiality are removed
([`comparison/lead_h8_constraint/`](comparison/lead_h8_constraint/README.md)).

What happens after a find: a named mechanism with a predicted sign, replication on a second cohort, a fresh test on a
slice of the Replogle 2022 K562 screen scored once by Andres's ML collaborator after our predictions are deposited and
their hashes posted ([`PLAN_R_FRESH_TEST.md`](PLAN_R_FRESH_TEST.md)), then the prediction package for a collaborating
lab ([`WETLAB_CANDIDATES.md`](WETLAB_CANDIDATES.md)): about ten perturbations in no dataset where the model with the
feature and the model without it disagree most, with matched negatives and expected effects.

## 4. Where we stand (17 October 2026)

- On Adamson the agent arms score 0.566 to 0.602 on the sealed set against 0.554 for a no-LLM control and 0.520 for
  the start; nearly all of the gain is one idea, transferring measured responses between related knockdowns. On
  Norman every arm sits within about 0.01 of the simple additive rule (0.713 sealed). Gains are real and small, as the
  literature on linear baselines predicts ([`README.md`](../README.md)).
- Block F (a genome table beside the old inputs, Norman): the agents built, unprompted, "additive prediction times the
  targets' promoter CpG content" in two of three runs. It is known biology, and its first "pass" was withdrawn when
  the test was found unable to fail that class of feature; the test is fixed and the re-read is pending.
- Block G (clean tier-1 knowledge, with and without the three tables, both datasets, 12 runs, $12.97 on the ledger):
  negative on both datasets. On Adamson none of 221 table-built features passes and the arm with the tables scored
  lower out of fold (0.491 ± 0.004 against 0.526 ± 0.035); on Norman none of 174 passes and the tables made no
  difference (0.579 ± 0.008 against 0.578 ± 0.001). Under ROADMAP section 5 the agents' biology path is paused. The
  readings are on [#51](https://github.com/andresloak100/Gene-Mila/issues/51), in the Status of `GOAL_CRITERIA.md`, and
  in Astra's results PR [#63](https://github.com/andresloak100/Gene-Mila/pull/63), which also carries the corrected
  block F re-read (six passing features, all reading the Replogle screen, so none tier 1) and the lead's family 8
  hypothesis (not supported on either dataset); the lead verifies and records them, see `HANDOFF.md` section 1.
- Built, tested, not yet run: the comparison (block H: Biomni and a Codex-based autoresearch loop through a ledger
  proxy with caps, the one-worker lab, a scripted control, CellForge's translated ideas;
  [`PLAN_H_COMPARISON.md`](PLAN_H_COMPARISON.md)), the fresh-test tooling, the wet-lab package tool
  (`tools/wetlab_candidates.py`) and the paper's skeleton ([`PAPER_COMPARISON.md`](PAPER_COMPARISON.md)).
- Money: a DeepSeek balance Andres gave; the ledger counts twice what DeepSeek bills (measured); the ledger read
  $60.23 after block G; block H's cap is ledger plus $15, answered by Andres on 17 October (ROADMAP, note of 02:10
  UTC). Every block is written in the repository before it starts.

Honest odds, from the roadmap: a Nature Genetics result in this window is unlikely (3 to 5 percent); the comparison
paper is the realistic deliverable, and the biology path stays open through the pre-registered open question and, if
a powered question can be stated, an ENCODE K562 table.

## 5. Your first hour

- **Get the code.** `git clone https://github.com/andresloak100/Gene-Mila.git`. The integration branch is
  `claude/autonomous-research-system-3k435s`; there is no `main`. Python 3.11 or newer. Then
  `pip install -r requirements.txt` and `python -m pytest -q` (13 to 15 minutes).
- **What is here and what is not.** The code, every plan, every reading and the result files are here. The data
  bundles, the run directories and the spend ledger are only on Andres's Mac (`~/Documents/Mila/Gene-Mila/gene-mila`;
  HANDOFF.md sections 2 to 4) and never enter git. In a container you can do all code, tool and document work and run
  the free synthetic lab, which needs no data and no key:
  `python run_research.py --minutes 2 --workers 4 --worker-provider mock --planner-provider scripted`.
  Anything on real data goes through the operator on the Mac (Astra, #51).
- **No key.** You do not have, need or ask for the DeepSeek key; paid runs start on the Mac, on Andres's words only.
- **Read the state.** `HANDOFF.md` section 1 (the top entries), `python handoff_state.py --fetch`, the open `Claim:`
  issues and pull requests. Then `docs/README.md`, the documentation map, and the plan of the block you touch.
- **Who to ask.** Decisions on money, scope and protected code: Andres, on #41, in his own words; wait for his answer.
  Tasks and readings: the lead, on #41. Anything on the Mac: Astra, on #51. Nobody decides for Andres.
- **Words you will meet.** A *bundle* is one dataset prepared for the lab. A *block* is one pre-registered batch of
  paid runs (F, G, H). An *arm* is one configuration repeated over seeds. *Out of fold* is a score on training
  perturbations under cross-validation; *visible validation* is the tier the lab selects on; *sealed* is the held-out
  test tier that only the lab's capped oracle scores, at the end of a run. Both real-data sealed sets are worn
  (scored repeatedly), so readings on them are descriptive. The *ledger* is the shared SQLite record of DeepSeek
  spend; every cap is written against it.

## 6. How agents work here

`AGENTS.md` holds every rule and wins over this summary. The ones a newcomer meets first:

- **Roles.** The lead (Claude on #41) decides blocks, plans, readings and caps within the money Andres gave, and
  merges pull requests when Andres tells it to (his words of 16 October, "start merging, I want everything to be
  updated", HANDOFF section 1); AGENTS.md still says Andres merges, and nobody else merges anything, their own pull
  request included. The "Autonomous research system" Claude session owns the lab code and the Mac's runs. Astra
  (ChatGPT, on the Mac) executes dated plans and posts every run's cost and result on #51. A new agent takes the task
  the lead assigns on #41.
- **Claim, branch, pull request.** Open an issue `Claim: <task>` naming agent, branch and files; branch from the
  integration branch; open a draft pull request into it. Never push to another agent's branch; never force-push.
- **Keep the state true.** Update `HANDOFF.md` section 1 when you start, at each milestone and before you stop, with
  the exact next step. A commit that changes only section 1 may go straight to the integration branch.
- **Money and the Mac.** A paid run starts only on Andres's own words, through the shared ledger with its caps; never
  two paid runs at once; nothing heavy on the Mac beside a paid run; never edit the Mac's main checkout.
- **Integrity.** Never read `data/*/private/` or `data/*/splits.json`; never choose anything on a sealed score;
  protected code (`genemila/benchmark/`, the guard, the split logic) is not yours to change; every number you report
  comes from a run directory, as mean ± sd over repeats; nothing is deleted, superseded records are archived.
- **Pre-registration.** A block's plan, caps, stop rules and readings are fixed before its first run; a change is a
  dated note, never an edit. The same for the known-biology list and the goal criteria.
- **Tests.** `python -m pytest -q` must pass before any push of code; `python tools/readme_check.py` after any change
  to the README, its figures or the About box, and the readme-designer agent reviews the README before it is committed.

## 7. What the lead is doing now, and how a new agent can help

The lead's live work is in `HANDOFF.md` section 1 (its dated entries, newest first) and on #41. The entry of
2026-10-17 18:30 UTC is a handover: the lead's session was running out of usage, and its numbered list there is the
work in order. A new Fable account with access to the Mac and the DeepSeek key takes it as follows, after one line on
#41 (who you are, which items, your branch `claude/<topic>`), and comments on #41 that it is taking over the lead's
claim if the lead has not written for a day:

1. **Verify and land Astra's results PR #63**, then record the verdicts (HANDOFF entry of 18:30 UTC, items 1 and 2).
   Needs the repository only. Merging is the lead's act under Andres's standing authorization on #41.
2. **Block H** (items 3 of that entry; `PLAN_H_COMPARISON.md`): wait for Andres's isolation answer and cap line, record
   them on #41, then run the free preparation and, one session at a time, the probe and the arms; Astra operated the
   earlier blocks and may operate this one, or you may, but never both at once. Needs the Mac.
3. **The fresh test** (item 4; `PLAN_R_FRESH_TEST.md` sections 3 and 6): the Replogle slice manifest from the file's
   obs and var only, and the frozen adapter check; the holder's name is Andres's. Needs the Mac, no paid run.
4. **Free side work** (item 5): the Adamson cis-pair count for ROADMAP D10, a critic's reading of
   `PAPER_COMPARISON.md` and `PLAN_H_COMPARISON.md` posted as findings on #41, the citation pass of
   `CANDIDATE_LITERATURE_CHECK.md`. Needs the repository and the web.

An agent with access to the Mac starts no paid run without Andres's own words, never edits the main checkout
`~/Documents/Mila/Gene-Mila/gene-mila`, and runs nothing heavy while another operator's job is live (`pgrep -fl
run_research.py`; Astra's state is at the top of `HANDOFF.md` section 1).
