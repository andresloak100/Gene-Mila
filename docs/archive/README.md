# Archive

Documents, status copies and scripts that the live tree no longer needs but that a record cites, a checksum list
names or a provenance header verifies against. Nothing here is edited; a file arrives with one line below saying
what it was, when it was superseded and by what. Relative links inside archived documents were re-pointed to work
from this directory; nothing else in them changed.

The rule for what stays in the live tree and what comes here: a file stays where a record links it or a manifest
lists it; a checksum line alone keeps nothing in place (the line is noted here instead); a duplicate, a scratch file
or a stale status copy is deleted. Run results under `docs/results/`, pre-registered plans, the Mac scripts that ran a
block, ledger records, `HANDOFF.md` and `docs/LAB_STATE.md` are never deleted.

| Path | What it was | Superseded on | By |
|---|---|---|---|
| `plans/PAPER_FRAMEWORK_PROPOSAL.md` | the paper framework proposal (draft PR #38, 15 to 16 October) | 2026-10-17 | its section 1 became `docs/GOAL_CRITERIA.md`, sections 2 to 4 `docs/FEATURE_COMPARISON_PROTOCOL.md`, sections 6 and 7 `docs/ROADMAP.md` |
| `status/DOCUMENTATION_STATUS_20261017.md` | the documentation status and continuation map (13 to 17 October); PR states as of 17 October 2026, later merges are not reflected. Its blob links to PR heads `3f78618` (#25) and `645e21d` (#23) stop resolving if those branches are deleted after a squash merge; `docs/TEST_READINESS_20261013.md` is now in the tree (PR #23 merged 17 October); `docs/SINGLETON_TRANSFER_RESULTS.md` arrives with PR #25 when it merges | 2026-10-17 | `docs/README.md` (the map) |
| `records/deepseek_test_2026-10-03.md` | the synthetic DeepSeek worker validation of 3 October on code `f4e3480`; its cost correction entered the price table in `7787cb7`. Its commands name `reprice_ledger.py` at the root, where it was until 17 October (now `tools/reprice_ledger.py`) | 2026-10-17 | `docs/USAGE.md` ("Cheaper workers, same rules") |
| `results/feature_audit.{md,json}`, `results/feature_audit_feature_box.json` | feature audit v1 (11 October; AUDIT_FORMAT 3) | 2026-10-11 | `docs/results/feature_audit_v3.*` |
| `results/feature_audit_v2.{md,json}`, `results/feature_audit_v2_feature_box.json` | feature audit v2 (11 October; the merge-test and required-input fixes) | 2026-10-11 | `docs/results/feature_audit_v3.*` (stable under three hash seeds) |
| `mac/STATE_20261014.md` | the GitHub snapshot of the Mac `STATE.md`, copied 2026-10-14 02:53 UTC (`docs/mac/STATE.md` until 17 October; `HANDOFF.md` section 1 notes of 13 to 14 October mention it by the old path) | 2026-10-14 | `HANDOFF.md` section 1, the mirror AGENTS.md prescribes |
| `mac/STATE_astra_20261014T0221Z.md` | Astra's snapshot of the same file at 2026-10-14 02:21 UTC, 20 lines that exist nowhere else (claim #34 and PR #35 in progress, ledger "DeepSeek 43.599822392/cap48"); saved from branch `astra/b1-pair-batch-correction` before its merge | 2026-10-14 | the 02:53 snapshot above |
| `mac/push_to_github.sh` | the copy list that brought the 11 October Mac outputs into `docs/mac/` and `docs/results/` (ran once); it is their provenance | 2026-10-11 | nothing: the files are committed |
| `mac/pytest_macos_newpath.log` | the Mac test log of 11 October (369 passed) that `MD5SUMS_n4.txt` lists and `STATE_20261014.md` cites | 2026-10-17 | later suites (`docs/results/norman_f_pytest.log`, 540 passed) |
| `mac/external_stack_control.{py,json}` | the control for `tools/external_loo.py`'s stacking (result 0.543, `STATE_20261014.md`); imports `tools/external_loo.py` from the Mac checkout | 2026-10-17 | no reading cites it |
| `mac/feature_block_hashes.py` | the per-process feature-block hash check behind the PYTHONHASHSEED finding (`STATE_20261014.md`); its outputs were never committed | 2026-10-17 | the guard and `sandbox.HASH_SEED` (`docs/LAB_STATE.md`) |
| `mac/as_run/ceiling_analysis.py`, `mac/as_run/compact_model_curve.py`, `mac/as_run/learned_kernel_experiment.py`, `mac/as_run/nondeterminism_scan.py` | the scripts exactly as they ran on the Mac on 11 October; `MD5SUMS.txt` lists them and each `tools/` copy's provenance header cites their md5 | 2026-10-17 | `tools/ceiling_analysis.py`, `tools/compact_model_curve.py`, `tools/learned_kernel_experiment.py`, `tools/nondeterminism_scan.py` (same code, repository-root paths and an output argument) |

## Paths in `docs/mac/MD5SUMS.txt` and `MD5SUMS_n4.txt` that moved on 17 October

The lists name paths as uploaded on 11 October. Verify a moved file at its new path:

| Listed as | Now |
|---|---|
| `docs/mac/STATE.md` | `docs/archive/mac/STATE_20261014.md` (its md5 never matched the lists: the snapshot changed after each upload) |
| `docs/mac/ceiling_analysis.py`, `compact_model_curve.py`, `learned_kernel_experiment.py`, `nondeterminism_scan.py` | `docs/archive/mac/as_run/` |
| `docs/mac/external_stack_control.py`, `.json`, `feature_block_hashes.py`, `push_to_github.sh`, `pytest_macos_newpath.log` | `docs/archive/mac/` |
| `docs/mac/selection_replay.json`, `calibration_adamson_cf_val2.md`, `.json` | `docs/results/` |
| `docs/mac/cellforge_notes.md` | `docs/comparison/cellforge_notes.md` |
| `docs/mac/norman_n3.sh`, `norman_n4.sh` | `docs/mac/block_norman_n/` |
| `docs/results/feature_audit.*`, `feature_audit_v2.*` (six files) | `docs/archive/results/` |
| `docs/mac/norman/norman_splits.json`, `norman_manifest.json`, `norman_check_public.txt` | deleted: byte-identical to `docs/results/norman_splits.json`, `norman_manifest.json`, `norman_check.txt` (`cmp`), which the lists also name |

Deleted outright on 17 October (no record cites them): `docs/mac/MD5SUMS_state_20261013.txt` (one line, the md5 of a
status copy that changed on 14 October). `HANDOFF.md` section 1's history and the comparison takeover notes (section 9)
move under `handoff/` when the lead trims HANDOFF after block G.
