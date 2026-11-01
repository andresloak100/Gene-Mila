# Block H: free checks complete, initial probe stopped

Block H stopped at its first live probe. Biomni constructed successfully, then refused before sending an API request because its first-call estimate exceeded the fixed probe session cap. The combined probe failed, so no full H comparison arm or reading ran. This is a partial operational record, not a completed comparison or an agent-performance result.

The lead's [1 November decision](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6551319171) resolved the earlier Docker dependency and probe-gate defects through PR98/99. Andres instructed Astra to pull, rebuild, rerun the free checks and start H. Execution used integration `ae9c2b009e05e2a6ea7472cf6ca9d27b3b46c392`; the publication branch subsequently fast-forwarded to the integration state recorded in receipt_provenance.json. No scientific source, native H script, package or image dependency was patched by the operator. Earlier stopped receipts remain in [the 31 October record](../block_h_preflight_20261031/README.md).

## Rebuilt image and free checks

The prescribed updated Dockerfile built once, exit0. New image ID: `sha256:b15af00eb763c5fb0fa8cb8001c3cd2d8b649492b11910ac0b90d5b799466a09`, Linux arm64. Imports, pip check, offline Biomni A1 construction, versions and host-versus-baked runner hashes passed; the focused H suite passed six tests in6.73seconds. The actual isolation check showed blocked internet egress and a reachable relay; all27 pinned package file hashes matched, including the harness17 metadata/hash record. The package was reused, not re-exported. [Image receipt](resumption/image_preflight.json), [free-check receipt](resumption/free_checks_complete.json), [resumption source hashes](resumption/resumption.json).

Installed versions include Biomni0.0.8 and Codex0.166.0; every captured dependency version and five host/baked runner hashes are preserved in image_preflight.json. The Dockerfile remains unpinned beyond the recorded source and actual installed image versions; this publication does not claim a reproducible future unpinned rebuild.

One free operator image-name lookup failed even though Docker listed the name and could inspect the validated immutable image ID. Cause was not established. The one allowed correction was posted [before rerunning](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6551896514): reapplying the tag to that same immutable ID. The corrected lookup passed with no image payload, source or dependency change; original failure/correction receipts remain unchanged. No scientific run was repeated for this check.

## Free C0, each seed once

All three prescribed scripted-planner/mock-worker controls ran from untouched frozen code `baa7dfdbf17abd17a306d4dcfccb297baaf63b52` using the existing project Python. Settings remained CPU, four workers and20minute maximum budget; actual completion occurred earlier. The existing controller validated code, settings and config/summary hashes, then advanced sequentially. No extra score or sealed reading was run for this publication.

| Seed | Run directory, under main checkout runs/ | Actual wall seconds | Exit and validation |
|---|---|---|---|
|0|adamson_cf_h_c0_scripted_w4_r0|279.3147355830297|0, passed|
|2|adamson_cf_h_c0_scripted_w4_r2|288.09387920890003|0, passed|
|3|adamson_cf_h_c0_scripted_w4_r3|279.01530866743997|0, passed|

The full absolute run paths, start/end timestamps, source/settings checks and config/summary SHA-256 values are in each `c0/*.receipt.json`. Final C0 driver exit0 at2026-11-01T01:41:30.589326UTC. Shared ledger stayed61.562649371999996 (23865rows) through all free C0 work. Original per-seed command/log/exit/runtime and #51 completion receipts are indexed below. Do not rerun C0.

## Once-only cap and actual probe

Andres approved absolute cumulative ceiling **$76.562649372** on [#41](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6550695646). The native helper wrote its cap once, flooring within that ceiling:

```
76.56 61.562649 2026-11-01T01:43Z
```

The detached native chain ran once from01:43:23 to01:43:41UTC, using Docker/harness and A3_CLIENT=codex, nice19/caffeinate and the existing environment credential only. No top-up, screen/UI interaction or further balance check was made. The chain exited3 and preserved `h_probe: runner exit code biomni=1,codex=0` in block_h_stopped.txt. [Actual outcome](resumption/probe_failure_outcome.json), [chain log](native/block_h_chain.log), [full #51 stop report](resumption/probe_failure_issue51.md).

Biomni's [transcript](native/biomni/transcript.txt) records successful A1 construction and a156031character system prompt. Its first main-call lower-bound estimate was156031/4tokens at$1.32per million =about$0.0515, excluding the retriever call. That exceeds the prescribed **$0.05 probe session cap**. It refused before sending anything; run.json records childexit2, ended_by=refused, wall1.9seconds, while the parent runner returned1. Its proxy JSONL has only a start record: **zero Biomni API calls**. This is a per-probe limit refusal, separate from the available global block allowance. It does not demonstrate a failed Biomni/DeepSeek message route.

The native probe script performed the Codex subprobe before checking combined runner exits. Codex completed0 with two HTTP200 rows from deepseek-v4-pro on `/v1/responses` and no400. Totals:17361input tokens,8704cached,207output. Proxy logs report **$0.012629940**; the actual shared ledger after is **$61.575279308** (23867rows), a delta of approximately$0.012629936000004 from the earlier reading. These raw figures are retained separately; no cause is assigned to the approximately4e-9difference and the ledger was not repriced. Total cost is about$0.01263. [Codex run](native/codex/run.json), [proxy records](native/proxy/h_probe_codex.jsonl).

The combined runner exit check stopped the native script before its new per-log probe gate. There is no overall passed marker or gate receipt. The native scan reports three files naming harness/val1.npz; this filename scan is not itself proof that labels were read. No full Biomni/Codex seed arm, one-worker arm, H reading, feature comparison or sealed score followed. No retry, reset, cap change, fallback, hand repair or workaround was attempted. H remains stopped pending an explicit lead decision about the fixed probe allowance and authorized resumption. The monitor is paused.

## Publication boundary

Only reports, indexes and exact operational receipt copies are published. Raw runs, task-package files, harness matrices, data, predictions, codex_home/auth/config caches, images and credentials remain outside Git. Each preserved receipt is linked in README.md and hashed in the artifact manifest. The provenance manifest maps copies back to their original files. All publication checks must pass before pushing; previous raw receipts are preserved unchanged. C2 is closed; GEARS, linear AE and D are complete and were not repeated.
