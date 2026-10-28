# Plan C: CellForge on our split, scored by our evaluator (GOAL_CRITERIA B.5)

Written 2026-10-28 by the lead (claim #41) on Andres's request in the project chat: "run cell forge in the computer
and compare it". Nothing below has run. A change after the first run is a dated note at the end, never an edit.

## Why

CellForge's published Adamson numbers (PCC 0.988 in its Table 1) are not comparable with ours: its split holds out
guides rather than genes, which is easier, and no metric definition we tried reproduces its own baseline rows
(`docs/comparison/cellforge_notes.md`). The only fair comparison is CellForge's own system, trained on our training
perturbations only, predicting our held-out perturbations, scored once by our evaluator. That is criterion B.5.

## What runs where

The sealed labels never leave Andres's Mac. CellForge needs a GPU (4 to 8 GPU-hours per end-to-end run, its README),
an LLM for its agents, and its Codex code-generation backend; the Mila cluster has the GPUs.

1. **Mac, free:** export CellForge's input from the Adamson bundle and the three scPerturb Adamson files the bundle
   was built from. The export holds control cells and training-perturbation cells only, on the bundle's 2,055 genes,
   normalised as the bundle was, plus the list of the 38 held-out perturbations (visible and sealed together, so the
   sealed membership is not revealed) and a task text.

   ```
   python tools/cellforge_bridge.py export --bundle data/adamson_cf \
       --h5ad <the three AdamsonWeissman2016_*.h5ad files> --out ~/cellforge_adamson_export
   ```

2. **Copy** `~/cellforge_adamson_export/` (no labels of held-out perturbations are in it) to the Mila cluster.
3. **Mila GPU node:** install CellForge at a pinned commit (`6585ff9`, 2 October 2026, the one inspected here), then
   run it end to end on `cellforge_input.h5ad` with the task text of `TASK.md`; the held-out perturbations are
   simply absent from the file, so no CellForge split option hides them. LLM: DeepSeek through `DEEPSEEK_API_KEY` set in that
   shell's environment from a key Andres creates for this (never pasted into a chat or a file). Its two human
   checkpoints (the research plan, then the training script) are approved by the person running it, who records
   each approval on #41. CellForge's generated `result.py` must write `predictions.npz` with `perts` (the held-out keys)
   and `means` on the export's genes, in the export's gene order (`TASK.md`).
4. **Copy** `predictions.npz` back to the Mac and score it once:

   ```
   python tools/cellforge_bridge.py score --bundle data/adamson_cf --pred predictions.npz \
       --versus runs/newcode_opus_w4_r0 --out docs/results/cellforge_adamson_matched.md
   ```

   The report gives CellForge's sealed pearson_delta, MSE, top-20 metrics and CellForge's own DE-gene MSE/PCC/R2, and
   the paired comparison against the lab's Opus-planned run (mean difference, paired SE, wins).

## Arms and reading

- CellForge: three end-to-end runs (seeds 0, 2, 3 of its `--split-seed`, which here only seeds its internal
  validation split), reported as mean ± sd; one run first, the other two only if the first completes.
- Compared with: the lab's arms already scored on the same sealed set (Adamson, `split_450515be1a0d8d2e`): the start
  0.520, the no-LLM control 0.554, the 4-worker agent arm 0.602 ± 0.002. These sealed numbers are worn (the set was
  read many times), so the comparison is descriptive; the reading rule (gain above twice its paired SE, wins on more
  than half) is applied to the paired query only.
- Money: CellForge's own estimate is 40k to 80k prompt and 200k to 400k completion tokens per run, well under $1 on
  DeepSeek; each run is still a paid run and starts only on Andres's words with a cap line on #41 (AGENTS.md).

## What can go wrong

- The generated model may not run or may not write the required output: reported as such, never repaired by hand.
- CellForge's code generation uses Codex and needs an OpenAI or ChatGPT login on the node; if that is unavailable,
  `--codegen-backend` is the documented swap and the change is recorded here before the run.
- A run that reads any other copy of Adamson (its downloader fetches the full screen) is void: the node gets only
  the export folder, and CellForge's dataset downloader is not run there.
