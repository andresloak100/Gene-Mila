# Brief for the Mila-server agent: set-up, access and the first task

Written 2026-11-03 by the lead (claim #41) for the OpenChamber agent Andres runs on the Mila cluster. Read
`AGENTS.md` first: its rules apply to you unchanged. Then `docs/BRIEF_FOR_NEW_AGENTS.md`, `HANDOFF.md` section 1 and
this page. Your name in the repository is `mila` (branches `mila/<topic>`, claim issues "Claim: ... (mila)").

## 1. What the Mila server is for

The Mac has the real data and runs the lab's paid 20-minute searches. The Mila server has storage and GPUs. It takes
the jobs the Mac cannot: deep-learning baselines (GEARS is done on the Mac's CPU; State, CPA and scGPT need a GPU),
the third dataset (Srivatsan, drugs), the Replogle work of plans R and DK, and any run that needs more than the Mac's
disk. It never runs a paid lab search while the Mac runs one (AGENTS.md: never two paid runs at once).

## 2. Access you need, and what you must never have

| Need | How | Rule |
|---|---|---|
| The repository | `git clone https://github.com/andresloak100/Gene-Mila` into your own folder; `gh auth login` with Andres's token of `repo` scope, or a deploy key he adds | Push only to `mila/<topic>` branches, open draft PRs into `claude/autonomous-research-system-3k435s`, never merge |
| Python | `python3.12 -m venv .venv && pip install -r requirements-lock.txt`; GPU baselines get their own venv from `tools/baselines_dl/requirements.txt` | `python -m pytest -q` passes before every push of code |
| The DeepSeek key, only if Andres assigns you a paid block | the environment variable `DEEPSEEK_API_KEY` in your shell only, set by Andres (`export DEEPSEEK_API_KEY=...` in his own session, never pasted in chat, never in a file) | Never print, log, commit or echo it; every paid run carries the ledger caps of AGENTS.md and starts only on Andres's cap line on #41 |
| The shared spend ledger | `runs/spend_ledger.sqlite` lives on the Mac; a paid run on Mila needs the ledger copied before and merged after, which is not built yet | Until it is, Mila runs nothing paid |
| Disk | a project directory with at least 200 GB (Replogle genome-wide is 9 GB, Tahoe-scale files are far larger) | Never commit `data/`, `runs/`, `*.h5ad` |

## 3. Datasets: download, build, keep private

Download every raw file from the public record, never from the Mac, and record each file's sha256 on your claim issue.

| Dataset | Source | Builds into |
|---|---|---|
| Adamson 2016 (3 files), Norman 2019, Srivatsan 2020 (sci-Plex 3) | scPerturb RNA archive, Zenodo 13350497 | `genemila.data.real` bundles |
| Replogle 2022 K562 genome-wide | same archive, `ReplogleWeissman2022_K562_gwps.h5ad`, md5 `13db594f8f1d2ccb88fec44a13e414dc` | plans R and DK |
| Knowledge sources (Reactome, GO, CORUM, CollecTRI, STRING, GENCODE, gnomAD, UniProt) | `tools/build_clean_bundle.py` and the `tools/build_*.py` scripts download them | the clean bundles |

**Do not rebuild the Adamson and Norman bundles.** The lab's numbers are tied to `split_450515be1a0d8d2e` (Adamson)
and the Norman split id in `HANDOFF.md`. Ask Andres to copy `data/adamson_cf`, `data/adamson_cf_clean_tables` and
`data/norman_cf` from the Mac (`rsync`), so your bundles are byte-identical. They contain the sealed labels in
`private/`: the same rules as on the Mac apply, you never read `data/*/private/` or `data/*/splits.json`, and only the
lab's `QueryOracle` scores the sealed set, once per model. Srivatsan has no bundle yet: build it with
`genemila.data.real` on the perturbation split, seed 42, and post its `split_id`; that is a new bundle, the lead fixes
its reading before any score is read.

## 4. The first task: CellForge's Table 1 with our rows (claim it on #41 first)

CellForge's paper (arXiv 2508.02276, Table 1; our copy `docs/results/cellforge_table1.json`) reports MSE, PCC and R²
on all genes and on the top-20 DE genes, on Adamson, Norman and Srivatsan. Their rows are not reproducible and their
split holds out guides, not genes (`docs/comparison/cellforge_notes.md`), so the paper marks them "not comparable",
but the lab needs its own rows in that exact layout, on its own gene-level splits, for every system it has run or can
run. Free, no LLM.

1. **Adamson and Norman, existing systems:** the lab's arms already have sealed numbers for every column
   (`docs/results/summary_for_collaborators.md`, `docs/results/norman_b1_arm_vs_additive.md`); GEARS and the
   Ahlmann-Eltze linear baseline have Adamson (`docs/results/gears_adamson/aggregate.md`, `linear_ae_adamson.md`).
   Run GEARS and the linear baseline on Norman the same way (`docs/PLAN_DL_BASELINES.md`; the export is
   `tools/cellforge_bridge.py export`, the score `tools/cellforge_bridge.py score`, once per model).
2. **State** (Arc Institute, bioRxiv 10.1101/2025.06.26.661135): train State Transition on each export (control and
   training cells only) with ESM2 embeddings for the held-out genes, on a GPU; write `predictions.npz` as the bridge
   expects; score once. Write the runner as `tools/baselines_dl/run_state.py` with a test, like `run_gears.py`, and a
   dated note in `docs/PLAN_DL_BASELINES.md` before the first real run. Record the State checkpoint, its pretraining
   data and whether it could have seen the held-out genes.
3. **CPA and scGPT**, the same way, after State.
4. **Srivatsan:** the lab's systems need a drug representation; that is a design question for the lead. Run only
   the baselines that take drugs natively (CPA, scGen, State) and the Ahlmann-Eltze model with a drug embedding, and
   report the lab's rows as "not run" until the lead fixes the design.
5. **The table:** `docs/results/cellforge_table1_ours.md` in CellForge's layout, their rows in grey (copied, marked
   not comparable), ours in full, every number with its run directory and `split_id`. One draft PR per dataset.

## 5. How you report

Every milestone: one comment on your claim issue and a line in `HANDOFF.md` section 1 (a commit that changes only
section 1 may go straight to the integration branch). Every number cites its file. A failed run is reported as it is,
never repaired by hand, and a run is never deleted.
