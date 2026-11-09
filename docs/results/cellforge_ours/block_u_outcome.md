# Block U outcome: CellForge's pipeline on our exports, six runs, one finished

Block U (`docs/PLAN_U_CELLFORGE.md`) ran CellForge's published pipeline (gersteinlab/CellForge `6585ff9`, code
unchanged, every agent DeepSeek v4-pro through the lab's spend proxy) on the Mac (24 GB, Apple silicon, no CUDA)
against the same Adamson and Norman exports our GEARS and linear baselines used. Each run goes probe, task
analysis, method design, code generation, then CellForge's autorun (the agent's training script, with CellForge's
own repair loop), then our held-out prediction and the bridge's sealed score. Every step has receipts beside this
file (`cf_<dataset>_s<seed>/<step>.{command.txt,log,exit,runtime.json}`); a step killed for memory also leaves
`<step>.memkill.txt`, a `ps` snapshot of its process tree.

Limits per step: a 6-hour wall clock for autorun and, from the restart of 5 Nov 22:02 UTC (Andres, "Restart,
12 GB cap"), 12 GB physical footprint for the step's whole process tree, sampled every 10 s. A killed step fails
its run and the chain goes on; nothing is patched or retried by hand.

## The six runs

| Run | Analysis + design + code | Cost (proxy ledger) | Script's model | Autorun outcome |
|---|---|---:|---|---|
| `cf_adamson_s42` (4 Nov) | 25 min | $1.86 | transformer over 512 HVG tokens, 20.8M parameters | **finished** in 80 min (after three 20-second failures fixed by configuration, see `autorun_attempt*`); scored, `cf_adamson_s42.md` |
| `cf_norman_s42` attempt 1 (4-5 Nov) | 2 h 32 min (code generation 2 h 18 min) | $0.78 + $0.27 autorun | transformer over gene tokens, CPU | reached 46.9 GB on the 24 GB Mac, killed with the session at 03:13 UTC (`autorun_attempt1_killed.note.md`) |
| `cf_norman_s42` attempt 2 (5-6 Nov) | reused | $0.84 autorun | repaired script (T02): 1,024 gene tokens, Apple GPU (MPS), 50 epochs max, patience 15 | **killed at the 6-hour wall clock**, still training; peak footprint 4.7 GB |
| `cf_norman_s0` | 36 min | $1.34 | transformer over gene tokens, CPU, 30 epochs max | **killed for memory** 27 s into the script (12.4 GB) |
| `cf_norman_s2` | 39 min | $1.32 | transformer over 512 HVG tokens, CPU | **killed for memory** 85 s into the script, 12.4 GB |
| `cf_adamson_s0` | 56 min | $1.51 | transformer over 2,048 HVG tokens, CPU | **killed at the 6-hour wall clock**, still training; peak footprint 8.7 GB |
| `cf_adamson_s2` | 42 min | $1.28 | transformer over 2,000 HVG tokens, CPU | **killed for memory** 24 s into the script, 21.6 GB |

Costs are the proxy ledger's differences between the run's start and end lines in
`~/Documents/Mila/Gene-Mila/cellforge_runs/progress.md` (peak-rate pricing, the lab's convention). Block total
$9.20 of the $15 cap, 1,005 calls, none refused; the proxy was stopped at 13:47 UTC on 6 Nov. Chain timeline
(UTC, 6 Nov): `cf_norman_s42` killed 04:02, `cf_norman_s0` 04:56, `cf_norman_s2` 05:52, `cf_adamson_s0` 12:49,
`cf_adamson_s2` 13:44; `block_u_chain.done` written 13:44:54.

## What the runs have in common

- Every run got through CellForge's three LLM phases and produced a 1,000 to 1,500-line PyTorch script. The method
  design is the same each time: the plan's 4-layer, 8-head, 512-wide transformer encoder over gene tokens, an MLP
  perturbation encoder, cross-attention, an MLP decoder; batch 64, early stopping with patience 15.
- The scripts look for CUDA and otherwise train on the CPU; one (`cf_norman_s42` T02) also accepts Apple's MPS
  backend. None of them sizes the model to the machine: three passed 12 GB within 90 s of starting, before any
  epoch could have finished. The training files are small (Norman 64,869 cells x 2,083 genes, Adamson 40,890 x
  2,055, sparse; 0.5 and 0.3 GB dense in float32), so the data is not what filled memory. The cause was not
  measured; the likely one is the first forward pass of a transformer over about 2,000 gene tokens at batch 64,
  whose attention scores alone take about 9 GB per layer in float32 (`cf_adamson_s2` used 2,000 tokens and
  `cf_norman_s0` its gene count; `cf_norman_s2` used 512 tokens and its cause is unknown). An earlier version of
  this note blamed densifying the count matrix; that was an inference from timing alone and is withdrawn.
- CellForge's repair loop never saw the memory or time kills: the harness kills the whole process tree, CellForge
  included, so a killed run has no second script. That is the cap's intended behaviour (plan, notes of 5 Nov); a
  variant that kills only the training script and lets the loop repair it was not tried.
- No prediction and no metric exists for the five failed runs. The table's Norman CellForge row is empty and its
  Adamson row rests on one run, whose model did not vary its output with the perturbation (`cf_adamson_s42.md`).

## For the comparison of agentic flows

On this machine, with this budget: CellForge's flow produced a scored model in 1 of 6 attempts; the lab's flow
(ridge over agent-written features, CPU, 20 minutes per run) produced one in 6 of 6 in blocks G0 and T0 on the
same bundles (`docs/results/cellforge_table1_ours/table.md`). That is a statement about fit to a 24 GB laptop and
a $15 cap, not about either flow on the GPU servers CellForge was written for. Whether to spend the cap's
remaining $5.80 on a rerun whose task text states the machine's limits is Andres's decision (open as of
2026-11-06).
