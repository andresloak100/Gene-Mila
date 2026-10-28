# Plan: non-agentic deep-learning baselines on our split (GEARS first)

Written 2026-10-28 by the lead (claim #41) on Andres's "go b" (project chat, 28 October), after plan C stopped at
CellForge's first checkpoint (`docs/PLAN_C_CELLFORGE.md`, #51). Nothing below has run on real data. A change after
the first run is a dated note at the end, never an edit.

## Why

The lab meeting of 17 October asked for a benchmark against non-agentic deep-learning models as well as CellForge.
CellForge's public release produced a templated plan unfit for this task, so its row is recorded as "could not produce
a model for this task" with that evidence. The standard deep-learning baselines ship working code and run on our
inputs unchanged. GEARS (Roohani et al. 2023) is the reference model for unseen genetic perturbations and is one of
CellForge's own baselines, so it goes first; CPA and scGPT follow only after GEARS has a score.

## What runs, where

Everything is free (no LLM, no paid call) and runs on Andres's Mac, operated by Astra, at `nice -n 19`, never beside a
paid run, in Astra's own clone at the integration head. The sealed labels never leave the Mac.

1. **Input:** the existing plan C export `~/cellforge_adamson_export` (control and training cells only, the bundle's
   2,055 genes and normalisation, the held-out list; `export.json` on PR #84). It is reused, not rebuilt.
2. **Environment:** its own virtual environment from `tools/baselines_dl/requirements.txt` (GEARS 0.1.2, PyTorch,
   pandas 2; GEARS 0.1.2 does not run on pandas 3). GEARS downloads its Gene Ontology graph from Harvard Dataverse
   on first use, about 10 MB.
3. **Runs:** three seeds, each with a fresh work folder:

   ```
   for s in 0 2 3; do
     nice -n 19 ~/gm_dlenv/bin/python tools/baselines_dl/run_gears.py --export ~/cellforge_adamson_export \
       --work ~/gears_work_s$s --out ~/gears_adamson_s$s --seed $s --epochs 20 --device cpu
   done
   ```

   Twenty epochs is GEARS's own default. `--device mps` may be used if the CPU run takes more than 6 hours per seed;
   the device is recorded in each receipt.
4. **Score, once per seed**, on the Mac:

   ```
   python tools/cellforge_bridge.py score --bundle <MAIN>/data/adamson_cf --pred ~/gears_adamson_s$s/predictions.npz \
     --name gears_s$s --versus <MAIN>/runs/newcode_opus_w4_r0 --out docs/results/gears_adamson_s$s.md
   ```

## Reading

- GEARS is reported as mean ± sd over its three seeds of the sealed pearson_delta, MSE, the top-20 metrics and
  CellForge's DE-gene MSE/PCC/R², beside the lab's arms on the same sealed set (start 0.520, no-LLM control 0.554,
  four-worker agents 0.602 ± 0.002). The sealed set is worn, so the comparison is descriptive; the paired query of
  each seed against the Opus-planned run is read by the lab's rule (gain above twice its paired SE, wins on more
  than half the perturbations).
- Held-out perturbations whose target is outside GEARS's gene graph get the fallback prediction (control mean plus
  the mean training change) and are listed in each receipt; the report says how many.
- GEARS trains on the training cells only, with 10 percent of the training perturbations as its validation set; it
  never sees a held-out perturbation's cells, as the lab's agents never see their labels.

## Tested before the first real run

On 28 October in the cloud: a synthetic export with 24 perturbations of genes in GEARS's graph; GEARS trained on 13
conditions and predicted all 10 held-out ones in 45 seconds on CPU, and `cellforge_bridge.py score --name gears` scored
them through the oracle (`tests/test_cellforge_bridge.py`, `tests/test_run_gears.py`). Three compatibility fixes are in
the runner: a sparse matrix GEARS can index with a pandas mask, anndata's string-writing setting, and a refusal to
reuse a work folder.

## After GEARS

CPA (`cpa-tools`) and scGPT fine-tuning, each with its own runner on the same export and the same scoring, as dated
sections here. scGPT needs a pretrained checkpoint and is better run on a Mila GPU.
