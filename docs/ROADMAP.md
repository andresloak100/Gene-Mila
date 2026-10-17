# Roadmap: the lead's decisions, 17 to 26 October 2026

Andres handed the lead of the project to the Claude session on claim [#41](https://github.com/andresloak100/Gene-Mila/issues/41)
on 16 October ("take the lead of the project, you know the goal; take the decision that will get us there"; recorded on
#41). This file is that session's decision record. It was written after a researched and reviewed decision process
(four fact-finders, three independent roadmaps, nine critics, one synthesis; 16 October, in the session) and it is
kept current: a decision changes only by a dated note at the end, never by editing the text above it. The goal and the
rule for "goal met" stay `docs/GOAL_CRITERIA.md`; the standing rules stay `AGENTS.md`.

## 1. The call

Where we stand. The biology path has no standing candidate. Block F's only pass of criterion A.1 (additive_response ×
the targets' promoter CpG) rested on a null that cannot fail for that class of feature: `tools/feature_compare.py`
permutes the candidate column across genes, which scrambles the additive_response factor the parent model already
holds, so every null replicate is worthless and the null distribution is a spike at zero (null sd 0.00001 against an
observed gain of 0.00056; 14 of the 20 tested rows, a random projection among them, hit the same p floor;
`docs/results/norman_f_stage2/feature_compare.json`). And with 20·m − 1 replicates the smallest pooled Holm p equals
the 0.05 cutoff by construction, so "found" was a flag for "no replicate exceeded", not a p-value. The mechanism is
known biology anyway (Konermann et al. 2015) and the fitted signs are mixed. Block G is merged (integration head
`baa7dfd`, PR #48) and its nine raw downloads are done (#47). The comparison path has every tool but no foreign system
has run, no held-out number exists, and the lab selects on the visible validation tier while the task package shows
foreign systems the out-of-fold tier only. Money: ledger $47.26; console $28.19 plus $16.25 granted credit.

What we will do. Block G runs first, unchanged, as the clean retest of A.1 and as the comparison's lab rows. Before any
G score is read, the fair test is fixed and the known biology is pre-registered out of the agents' view. Then one
comparison block on Adamson with equal feedback for every system. The fresh test is a Replogle K562 CRISPRi slice by
commit-then-reveal, held and scored once by Andres's ML collaborator, with no deposit date until the export adapter
proves itself. ENCODE, Norman package arms, STATE, native CellForge and the wet lab are deferred or dropped.

Odds, honest. Goal (a), a new feature testable in vitro and publishable in Nature Genetics: 3 to 5 percent in this
horizon (A.5 cannot happen in ten days, and every tier-1 family block G can produce has a known rule behind it); a
computational result meeting A.1 to A.4 and A.6: about 10 percent. Goal (b): B.1, B.2 and B.5-as-not-comparable about
65 percent by early November; B.3 about 40 percent (it needs the holder and the adapter); B.4 with our arm beating
every baseline about 20 percent (out of fold the F and B2 arms are level); a defensible "what wins" table on one fresh
CRISPRi cohort about 50 percent.

## 2. Decisions

**D1. Block G runs first, exactly as merged.** `<G_COMMIT>` = `baa7dfd`, named in the dated note of
`docs/PLAN_G_CLEAN_ARM.md` and filled into `docs/mac/block_g/block_g_run.sh`. Twelve runs, `adamson_cf` then
`norman`, g0 and g1 alternating, seeds 0, 2, 3; cap ledger + $20; per-run caps $1.00 and $1.50. The G1 runs are the
comparison's lab rows (A1 of `docs/FEATURE_COMPARISON_PROTOCOL.md`) and G0 their no-table ablation, so no second lab
block is paid. The chain waits for Andres's one-line cap confirmation on #41; the readings wait for D2 and D3. Chains
start outside DeepSeek's peak hours (01:00 to 04:00 and 06:00 to 10:00 UTC on weekdays) when the operator's session
allows. Cost: $20 cap, expected $14 to $16 on the ledger (PLAN_G, Money). Who: the lead writes the note, Astra runs.
Serves A.1 and B.1.

**D2. Fix the fair test before any G score is read.** `tools/feature_compare.py` (a tool, not protected code) gets:
(a) a perturbation-level null for any candidate that is, within each perturbation row, proportional to a parent
column: the per-perturbation factor is permuted across perturbations within deciles of the targets' mean control
expression, with the parent columns left in place; such a candidate must pass the gene null and this one;
(b) family-wise correction by a max-gain step-down permutation over the whole family at 999 or more replicates
(floor 0.001), in place of Holm on a floored p; (c) rows deduplicated by prediction hash before correction, so three
copies of one column count once; (d) the standardised add-one coefficient of the candidate saved per fold seed, so a
sign can be read on the common parent; (e) a test that a parent column times a random per-perturbation scalar is not
found. Block F's stage 2 is re-read under it (free, about an hour on the Mac). `docs/GOAL_CRITERIA.md` is restated:
A.1 pending the corrected test. Cost: $0. Who: the lead builds, Astra re-reads. Serves A.1, A.2, B.2.

**D3. Pre-register the known biology before reading, out of the agents' view.** `docs/PREREG_G_KNOWN_BIOLOGY.md`:
for each family the agents can build from the tables (promoter CpG or GC class; TSS distance and bidirectional
promoters; gnomAD constraint; signal peptide or transmembrane against the secretory-pathway knockdowns; gene length
and exon count) the formula, inputs, the sign per modality (CRISPRa negative for CpG; CRISPRi untested), the null, and
the verdict KNOWN or OPEN with citations in `docs/CANDIDATE_LITERATURE_CHECK.md`, each marked VERIFIED (fetched) or
UNVERIFIED (search summary). Minimum effect of practical interest: gain above max(2 SE_adj, 0.002), the task package's
noise rule. The one OPEN family with power is constraint residualised on control expression and on tier-1
essentiality proxies (CORUM core complexes, Reactome ribosome, proteasome and spliceosome sets); DepMap is tier 3 and
excluded. The run checkout is pinned at `baa7dfd`, which predates these files, so no hypothesis reaches the agents.
Cost: $0. Who: the lead; Astra checks the citations from the Mac. Serves A.2 and A.6.

**D4. G readings as the plan says**, with the D2 tool: readings 1 to 4 of PLAN_G per dataset. The block stops only on
a run failure, a run over $2.00, `planner.mixed`, or a recorded `external_knowledge`; never on a sealed score. The lead
also scores its own constraint hypothesis as a hand-written plugin, reported as a human hypothesis, never as A.1.
Cost: $0. Serves A.1 and A.6.

**D5. Equal feedback for every system.** `tools/export_task_package.py` adds a harness validation tier: the package's
`evaluate.py` reports the visible-validation score beside the out-of-fold one and applies the lab's combined selection
rule, with those labels under `harness/` and disclosed as readable from the shell; transcripts are scanned with the
literal caps as the guard. `feature_compare --with-val1` stays off: every arm is screened on out-of-fold seeds 101 to
103, and the fresh test is the one held-out tier. A one-worker lab row and the scripted no-LLM control join the table;
`program.md`'s sha256 is posted on #41 before block H; agent minutes, tokens, served model and spend are logged per
arm by the ledger proxy. Cost: $0. Who: the lead. Serves B.1 and B.2.

**D6. Block H, the comparison, Adamson only.** `docs/PLAN_H_COMPARISON.md` and `docs/mac/block_h/`: a probe first
(cap $0.05: one execute-to-observation round against deepseek-v4-pro), then Biomni three sessions (A1 agent,
`source="OpenAI"`, `llm="deepseek-v4-pro"`, no data lake, the ledger proxy as its endpoint), an autoresearch-style
Claude Code loop three sessions (DeepSeek's Anthropic-format endpoint through the proxy, web tools off), and the
one-worker lab row three runs, all on the clean G1 bundle, 20 minutes each, a $2.50 session cap enforced by
`tools/baselines/ledger_proxy.py`, block cap ledger + $15. Isolation is a precondition (protocol, fairness control 7):
Docker if the Mac has it, else a second macOS account that Andres creates holding only the package; otherwise the
arms wait. Norman package arms are a later dated section, only if the ledger after H is at or below $80. Cost: $15
cap, expected $8 to $13 (estimate: no such session has run yet). Who: the lead builds, Astra runs. Serves B.1.

**D7. The fresh test.** Replogle 2022 K562 CRISPRi, commit-then-reveal, held and scored once by Andres's ML
collaborator. `tools/replogle_slice_manifest.py` (metadata only) lists the eligible targets: at least 20 cells, not
among the 102 Norman or 90 Adamson targets, inside the frozen gene universe, retired symbols mapped; an
in-distribution subset is pre-registered from tier-1 metadata (the Reactome and CORUM classes of the Adamson training
panel) and the rest reported separately. Replication (A.3) and the fresh test (A.4) come from two different Replogle
experiments (the essential-gene library and the genome-wide library) when both are available; if not, two disjoint
slices of one file, with the weakness stated. The Mac deposits predictions for every eligible target with their
sha256 on #41 before any reveal; only clean arms are scored; the paper states that the raw file was physically on the
Mac. No deposit date until `tools/frozen_model.py` reproduces `docs/results/norman_frozen_export_20261013` bit for
bit on a new cohort path and passes synthetic tests. Norman gets no fresh test: the two CRISPRa cohorts audited give
four usable genes and a dosage series (`docs/EXTERNAL_COHORT_METADATA.md`). Cost: $0. Who: the lead builds, Andres
names the holder, Astra deposits. Serves A.3, A.4, B.3, B.4.

**D8. Scoring every arm's features alike (B.2).** One call per bundle over G1, G0, the one-worker row, the two foreign
arms, CellForge's translated ideas (C2) and the block F plugin directories, with the D2 tool, candidate hashes posted
before scoring, never during a paid run. The frozen batch for the fresh test (three system models per arm, at most
three single features per arm, the additive rule, the scripted control) is posted before any contact with the holder.
Cost: $0. Who: Astra. Serves B.2 and B.4.

**D9. CellForge and STATE.** CellForge enters as C2 only (`docs/comparison/cellforge_c2/`); B.5 is reported as not
comparable, with the discrepancy between the paper's versions recorded. STATE is out of this window: its public
weights were trained on Replogle K562, the fresh-test cohort, so it cannot be a fair row there; its zero-shot variant
is a different task; CPU inference and the non-commercial licence are unverified. Cost: $0. Serves B.5.

**D10. ENCODE K562 table: build later, run only if powered.** The cis question (same loop, same domain) is unpowered on
a gene-wide metric: 3 target-to-gene loop pairs and 13 same-domain pairs on Norman, counted from the ENCODE K562 Hi-C
files, in a prediction matrix of 471,471 cells. `tools/build_encode_k562.py` is built after D2 to D7, and a block on
it is proposed only if a cis-restricted metric with its own matched null can be pre-registered with enough pairs on
Adamson. Cost: $0 now. Serves A.6, conditionally.

**D11. Housekeeping.** Astra posts the one-worker block's sealed and arm readings and per-run costs
(`runs/norman_ds_addstart_w1_r0/r2/r3`, PR #39) and they go into `docs/results/`; the block G download receipts are
committed under `docs/mac/block_g/`; `HANDOFF.md` section 1 points here. Cost: $0.

**D12. Money rules.** Ceiling in this window: ledger $82.26 (47.26 + 20 + 15). Floor: no paid run when the console's
topped-up balance (granted credit excluded) is below $8, read by Astra before every block. One paid run at a time;
every cap written once before its block; the ledger is never edited; Astra posts the console reading after each block
so the ledger-to-bill ratio is measured, not assumed.

**D13. A.5 and the Nature Genetics claim are outside this window.** Without a wet-lab answer the biology result is
reported as methods-level (`docs/GOAL_CRITERIA.md`, after A.6). The wet-lab candidate tool is built only after the D7
adapter exists, since it needs the same new-target prediction path.

## 3. Budget (ledger dollars; real money at about half)

| Block | Runs | Expected / cap | Ledger at cap | Real at half | Source |
|---|---|---|---|---|---|
| After block F | | | 47.26 | | HANDOFF.md section 1 |
| G: clean tier-1, g0 and g1, seeds 0, 2, 3, two datasets | 12 | 14 to 16 / 20 | 67.26 | 7 to 10 | PLAN_G Money; B2 and F cost $1.19 to $1.37 per run |
| H: Adamson probe, Biomni ×3, Claude Code ×3, one worker ×3 | 10 | 8 to 13 / 15 | 82.26 | 4 to 6.5 | estimate |
| Free: readings, re-read, exports, adapter, manifests, scoring | 0 | 0 | 82.26 | 0 | Mac CPU and this container |
| Window total | 22 | 22 to 29 / 35 | 82.26 | 11 to 17.5 | |
| Available 16 October | | | | 44.44 (28.19 + 16.25 granted) | DeepSeek console; expiry of the grant unverified |
| Reserve after the window | | | | 27 to 33 expected | |
| Later, conditional: Norman package arms (cap 9), ENCODE block (cap 11) | 12 | / 20 | 102.26 | | dated sections, on Andres's word |

## 4. Sequence, next ten days (UTC)

- 17 Oct. Lead PR: this file, PLAN_G's dated note, `block_g_run.sh` filled, `GOAL_CRITERIA.md` restated, HANDOFF.
  Then a second PR: the D2 tool with tests. Then the D3 documents. Astra: tooling check, console reading, the free
  bundle preparation, the receipts PR, the one-worker readings. Andres: the cap line.
- 18 to 20 Oct. Block G chain, one run at a time, about six hours of runs across Astra's sessions. Lead meanwhile:
  the block H tooling (`tools/baselines/ledger_proxy.py`, `run_biomni.py`, `run_autoresearch.sh`,
  `collect_handback.py`, tests), the harness tier in `tools/export_task_package.py`, `docs/PLAN_H_COMPARISON.md`,
  `docs/mac/block_h/`.
- 20 to 21 Oct. Astra: block F re-read under D2, G readings 1 to 4, package exports from the two clean-table bundles
  with hashes on #41. Lead: the D7 tools (`tools/replogle_slice_manifest.py`, the adapter extension with tests,
  `docs/PLAN_R_FRESH_TEST.md`).
- 22 to 24 Oct. Block H after Andres's isolation answer and cap line: probe, Biomni, Claude Code, one worker. Lead:
  the constraint hypothesis plugin; `tools/build_encode_k562.py` if the earlier PRs are merged.
- 25 to 26 Oct. Astra: B.2 scoring, the frozen batch, the Adamson cis-pair count, the citation pass. Fresh-test
  deposit: undated, after the adapter passes.
- Slip rule: every gate slips day for day; no block starts before the previous one is read. Realistic end: 30 October
  to 2 November.

## 5. Stop and continue rules

- A.1: a family counts only if it passes both nulls, the family-wise max-gain p is at most 0.05 (floor 0.001), the gain
  is above max(2 SE_adj, 0.002), wins on more than half the perturbations, every fold seed positive, on the clean
  bundle. If no family passes on either dataset after G, the biology path pauses; the ENCODE block can reopen it only
  under D10.
- A.2: a sign that differs from the pre-registration in any fold seed or dataset drops the mechanism claim; the
  feature is reported as predictive but unexplained.
- A.6: a family on the KNOWN list is recorded as methods-level and gets no replication, no wet-lab list and no novelty
  sentence; an OPEN verdict resting on unverified citations stays provisional until the citation pass.
- A.3 and A.4: no replication bundle and no deposit until the adapter reproduces saved predictions; a scoring is void
  if the deposit hashes are not on #41 before the reveal; a family that fails replication ends the biology path for
  it.
- B.1: an arm counts with three completed 20-minute sessions under the same cap and harness. If the probe fails even
  with the proxy's message merging, Biomni is reported as "could not run on DeepSeek v4-pro"; if Claude Code rejects
  the model alias, the loop runs on deepseek-flash and the difference is disclosed. The arms wait without isolation.
- B.4: our arm beats a baseline only under `tools/arm_reading.py`'s rule on the fresh test after correction; otherwise
  the paper reports what wins, the additive rule included.
- Money: no run when the ledger plus $2.50 exceeds the cap or the console balance is under $8; never two paid runs.
- Integrity: `--with-val1` stays off in `feature_compare`; a run that read a sealed label for a choice is renamed
  `_contaminated`; worn sealed sets are descriptive only.

## 6. What Astra does next, in order

1. Post on #41 the output of `which docker gtimeout claude codex` and the DeepSeek console reading (topped-up
   balance, granted credit, the grant's expiry if shown).
2. In your own clone at `baa7dfd` or later, create the dedicated checkout `gene-mila-baa7dfd` (PLAN_G step 2) and run
   `docs/mac/block_g/prepare_clean_bundles.sh` (free; it builds the six tables and the four bundles). Post its output.
3. Open a draft PR with `docs/mac/block_g/downloads.md`: URL, UTC time and sha256 of the nine files, from #47.
4. Read `runs/norman_ds_addstart_w1_r{0,2,3}/summary.json` and their ledger rows; post the sealed scores, the arm
   reading and the per-run cost on #39. Reading only.
5. When Andres's cap line is on #41: write `block_g_cap.txt`, start `block_g_chain.sh` detached (PLAN_G step 5), and
   post each run's line from `progress.md`.
6. After the chain: pull the D2 tool; re-read block F stage 2 with it; run G readings 1 to 4; post the files on a
   results PR; post the console reading.
7. Export the task packages from `data/adamson_cf_clean_tables` and `data/norman_clean_tables` with the D5 tool;
   post the sha256 of `MANIFEST.json` and `program.md`.
8. Block H, only after Andres's isolation answer and cap line: the tooling check, the cap, the probe, then the three
   arms one session at a time.
9. B.2 scoring: post the candidate hashes first, then one call per bundle at `nice -n 19` with no paid run live.
10. Count the Adamson target-to-gene loop and same-domain pairs from the ENCODE K562 Hi-C files against the Adamson
    gene table; post the count.
11. From the Mac, check each UNVERIFIED citation in `docs/CANDIDATE_LITERATURE_CHECK.md` and post VERIFIED or
    UNVERIFIED per entry.
12. Keep `STATE.md` on the Mac and `HANDOFF.md` section 1 current after every step.

## 7. What only Andres can do

1. Write one line in your own words on #41 for each cap when asked: block G (ledger + $20) now; block H (ledger +
   $15) after G is read.
2. Name the fresh-test holder (your ML collaborator, with a GitHub handle), say yes or no to commit-then-reveal on a
   Replogle K562 CRISPRi slice, and whether the holder receives cells or per-perturbation means.
3. Say whether the foreign systems may run in Docker on the Mac, or whether you will create a second macOS user
   account holding only the package; veto D5's harness tier if you disagree with it.
4. Say whether a pre-registered CRISPRi or CRISPRa test of about ten genes in K562 is possible in your lab in the
   coming months; if not, the biology result is reported as methods-level now.

## 8. Still unverified, and how each is checked before it matters

- Docker, gtimeout, codex and claude on the Mac: Astra, step 1, before PLAN_H is finalised.
- The grant's expiry and the ledger-to-bill ratio: the console reading in step 1 and after G, before H's cap.
- DeepSeek v4-pro accepting Biomni's consecutive assistant messages: the probe, first command of block H.
- Claude Code accepting the model alias on a custom base URL, honouring it over the Mac's own login, and the flags
  that disable its web tools: the loop script refuses unless the proxy log shows the served model; checked in the
  probe.
- The usage fields on DeepSeek's Anthropic-format route: logged from the probe; the proxy refuses to price an unknown
  shape.
- Per-session cost of the foreign arms ($0.5 to $1.7 estimated): measured by the proxy on the first session; the
  session and block caps bound the error.
- Citations marked UNVERIFIED (Chavez 2016, Horlbeck 2016, Radzisheuskaya 2016, Kang and Brent 2020, Nadig 2024,
  Replogle 2022): Astra, step 11, before any A.6 verdict leaves "provisional".
- Availability and size of the Replogle K562 essential-library file: Astra checks the Mac and the public record before
  PLAN_R fixes the replication cohort; the fallback is two disjoint slices, stated as weaker.
- The number of eligible Replogle targets inside Adamson's gene universe and the in-distribution subset: the manifest
  tool reports it before the holder is engaged; under 30 in-distribution targets, B.3 and B.4 are reported as not
  powered.
- `prepare_data.py` on a file of about 1.9 million cells: Astra dry-runs it on a subset at `nice 19`, never during a
  paid run.

## 9. What we drop, and why

- "A.1 met at the letter" for block F: withdrawn; the null was degenerate for that feature class and its floor equalled
  the cutoff (section 1).
- A sealed-score abort rule for block G: steering spend on sealed scores is the adaptivity the frozen-test plan
  exists to prevent.
- The ENCODE block inside this window and the same-loop question on a gene-wide metric: 3 loop pairs and 13
  same-domain pairs cannot move a gene-wide correlation.
- The two CRISPRa cohorts as a Norman fresh test: four eligible genes and a dosage series cannot read "gain above
  twice the paired SE, wins on more than half".
- Norman package arms in this window: no fresh tier to read them on; a later dated section if money remains.
- CellForge's own pipeline and STATE: no weights or GPU hours, an unreproducible table, and a model trained on the
  fresh-test cohort.
- `feature_compare --with-val1`: equal feedback goes through the harness instead, and the out-of-fold tier screens
  every arm alike.
- A DepMap essentiality covariate: tier 3 under the approved policy.
- An evaluator account on the Mac as the holder: a test held by the orchestration identity is not held out.
- A.5 and the Nature Genetics framing for this window: methods-level unless Andres answers item 4 of section 7.

## Note, 2026-10-17 01:10 UTC: the D2 to D7 deliverables landed; small decisions they raised

- Landed in one pull request (five deliverables, each reviewed by two readers and fixed): the corrected fair test
  (`tools/feature_compare.py`, `tools/block_f_readings.py`; D2), the pre-registration and literature check
  (`docs/PREREG_G_KNOWN_BIOLOGY.md`, `docs/CANDIDATE_LITERATURE_CHECK.md`; D3), the block H tooling
  (`tools/baselines/`; D6), the block H plan, Mac scripts and the task package's harness tier
  (`docs/PLAN_H_COMPARISON.md`, `docs/mac/block_h/`, `tools/export_task_package.py`; D5, D6), and the fresh-test tooling
  (`tools/replogle_slice_manifest.py`, the new-target path in `tools/frozen_model.py`, `docs/PLAN_R_FRESH_TEST.md`; D7).
- D2, cost of the block F re-read: every status-ok row at 999 replicates, not the top 20, so about 66 × 999 × 0.33 s,
  six hours of free CPU at nice 19 on the Mac, not "about an hour" as D2 said. The replicate rule is 999 for every
  family size; `feature_compare.json` keeps format 1 with additive keys, so saved reports still load.
- D6, the Biomni probe: it runs first without the proxy's `--merge-consecutive-assistant` option; if the route
  rejects Biomni's consecutive assistant messages, one rerun with the option, disclosed in the arm's report; if that
  fails too, Biomni is reported as "could not run on DeepSeek v4-pro".
- D7: Adamson has 88 knockdowns (`README.md`), not 90; the manifest tool records the count it reads. In two-file
  mode the fresh-test slice (R2) excludes the replication slice's (R1) eligible targets, as `PLAN_R` section 2 says;
  the in-distribution floor of 30 is re-checked after the exclusion.
- D5: the harness tier is on by default in the exported package until Andres vetoes it (section 7, item 3); a package
  exported with `--no-harness-val1` keeps the protocol's earlier rules. The sentence recording this in `AGENTS.md`
  (Scientific integrity) carries his veto line.

## Note, 2026-10-17 02:00 UTC: Andres's answer to section 7, item 4

"If we have solid data and good evidence we can do a collab with a lab and they will do the wet lab" (Andres, 17 October;
recorded on #41). So A.5 is reachable through a collaboration and the biology path is not capped at methods-level by
the lack of a bench. The order of blocks does not change. What changes: the wet-lab candidate tool of D13 is built as
soon as the frozen adapter of D7 exists, because a collaborating lab needs the prediction package (about ten
perturbations in no dataset where the model with the feature and the model without it disagree most, matched
negatives, expected effect sizes, the power at the cell counts a Perturb-seq or qPCR readout gives), and "solid data"
means A.1 on the clean bundle under the corrected test, A.2, A.3, A.4 and A.6. The bottleneck for goal (a) is now
novelty (A.6) and replication (A.3, A.4), not A.5. The odds in section 1 do not move for this window: no candidate
exists yet.

## Note, 2026-10-17 02:10 UTC: the caps are confirmed; the ledger-to-bill ratio is measured

Andres, 17 October, 01:46 UTC, with the DeepSeek console in view (topped-up $28.19, granted $14.84, 30-day cost
$23.63): "this is what we hold in the deepseek agents, use as however you want; if we need more we can recharge, but
make sure we are doing the right thing" (recorded on #41). Section 7, item 1 is answered for block G (ledger + $20)
and block H (ledger + $15). Block F cost $2.82 on the ledger and $1.41 billed (the granted balance fell from $16.25 to
$14.84), so the ratio of D12 is 2.0, measured. Real money: $43.03; the window's ceiling of ledger $82.26 is about
$17.50 real; reserve after it about $25. The floor rule stands. "If we need more we can recharge" is noted and not
used: every block in this window fits the balance held today.

## Note, 2026-10-17 02:50 UTC: scoring the lead's family 8 plugin joins Astra's list

- D4's hand-written hypothesis is the plugin in `docs/comparison/lead_h8_constraint/` (README, tests), fixed before
  any block G score. Its scoring is step 6a of section 6, after the G readings: free, at `nice -n 19`, never beside a
  paid run, the README's pre-run command (the Reactome sets and counts the real bundle gives it, posted on #41) and
  then its `feature_compare` command per dataset at 999 replicates; the result is posted on the same results PR and
  reported as the lead's hypothesis, never as A.1. The dated note at the end of `docs/PREREG_G_KNOWN_BIOLOGY.md`
  records how family 8's wording was turned into code.

## Note, 2026-10-17 15:30 UTC: block G ran; the Adamson half is negative

All twelve runs passed cleanly (chain ended 07:05 UTC; $12.97 on the ledger, final ledger $60.23; #51). On Adamson the
corrected fair test finds no feature among the 221 the agents built from the three tables, and the arm with the
tables had the lower out-of-fold mean, inside run-to-run noise (G1 0.491 ± 0.004, G0 0.526 ± 0.035; `docs/GOAL_CRITERIA.md`
Status). So the three per-gene tables, on their own and on clean knowledge, gave the Adamson agents nothing that
survives the test, and may have cost them search time. Norman's reading is running. D1 to D13 stand: the block G runs
are block H's lab rows (g1 and g0) whatever the Norman reading says, and the decision on the biology path (pause, or
the ENCODE block under D10) is taken when Norman's reading and the block F re-read are in, not before.

## Note, 2026-10-17 16:50 UTC: block G's Norman half is negative too; the biology path pauses

Norman (operator's readings on [#51](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6236179594)):
none of the 174 table-reading features passes the corrected fair test (158 unique predictions, 999 replicates, both
nulls, complete family), and the tables made no measurable difference to the arm (G1 0.579 ± 0.008 against G0
0.578 ± 0.001 out of fold; `docs/GOAL_CRITERIA.md` Status). With the Adamson half (note of 15:30 UTC) block G is
negative on both datasets. The rule of section 5 applies: **the agents' biology path pauses.** What that means:

- No further paid block on tier-1 tables in this window. The two readings still owed, the corrected block F re-read
  (running, free) and the family 8 scoring (free), are read when they land; neither can produce a Nature Genetics
  candidate (F's family is KNOWN, so methods-level under A.6; family 8 is the lead's hypothesis, never A.1).
- D10 stands as written: the ENCODE block is proposed only if the Adamson cis-pair count (section 6, item 10, free)
  supports a pre-registered cis-restricted metric. Until then the biology result is reported as methods-level, as
  D13 says, and the wet-lab package tool stays unused.
- Block H is the next paid block, with the twelve block G runs as its lab rows (g1 and g0 on Adamson), the task
  package from `data/adamson_cf_clean_tables`. It still waits on section 7, items 1 and 3: Andres's isolation
  answer and his block H cap line (ledger + $15 from the reading when it starts; the ledger reads $60.23 now).
- The fresh test (D7) still waits on section 7, item 2: the holder's name.
- The operator's source-only question on the family 8 plugin's parent column is answered in the plugin's README
  (note of 16:45 UTC): on Adamson the parent has no `additive_response` column, so the row reads `mean_response`,
  fixed before any score and covered by a test.

## Note, 2026-10-17 19:33 UTC: the corrected block F and family 8 readings are in; PR #63 merged; block H's gaps

The operator's results PR [#63](https://github.com/andresloak100/Gene-Mila/pull/63) is merged after the lead
re-derived its numbers from the JSON (`docs/GOAL_CRITERIA.md`, Status entry of 19:33 UTC). Corrected block F: six rows
pass every gate, all six the sign-flipped Replogle 2022 response times an annotation column, a tier-3 source, so no
tier-1 feature; the 38 screen-free rows find nothing. Family 8, the lead's hypothesis: not supported on either
dataset, with a gain interval that excludes the minimum effect on both. **Every pre-registered reading of this window is
in and negative for a tier-1 feature; the pause of the biology path (note of 16:50 UTC) is final for this window**, and
D10's ENCODE question is the only route that reopens it. Wording fixed in the records: the test applies the gene null
to every row and the perturbation null to the rows proportional to a parent column; a lower mean inside run-to-run
noise is reported as such, never as "lower". Block H (reader's check of `docs/mac/block_h/` and the operator's tool
check of 17:53 UTC): `gtimeout` is inventoried but called by no script, `claude` is only the fallback client, so neither
blocks the Codex route; what blocks is Andres (section 7, items 1 and 3): the Docker daemon (Docker Desktop started, then
`check_tools.sh` again, then the image build) or the second account, his cap line, and the console reading (D12). Before
the probe the operator must also create the `gene-mila-h` clone at the integration head or export `H_CLONE`, write
`tier.txt` (`harness`, the D5 default) and `isolation.txt`; and the lead or the new agent fixes two things in the
scripts: a failed probe cannot be rerun (the refusal files `h_probe.log`, `proxy/h_probe.jsonl`, `work/out/handback`
`h_probe` and `block_h_stopped.txt` need a documented reset), and `run_biomni.py` cannot find `configs/default.toml` in
Docker or account mode, so its cost pre-estimate is silently off (copy the file or pass `--miss-usd-per-mtok`).
`docs/results/README.md` now lists PR #63's 1,200 files one by one; the next curation regroups it to one line per
reading (the publication manifests keep the per-file list).
