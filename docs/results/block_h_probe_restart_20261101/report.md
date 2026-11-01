# H probe reset succeeded; restart refused before the new probe

The authorized dated reset completed successfully. The restarted native chain then stopped in its Docker image-name check before a new probe, proxy or paid call. The shared ledger is unchanged. H remains stopped; the new spending authorization is recorded separately from this technical refusal.

## Adopted lead decision and reset

The [lead's 1 November decision](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6552107893) adopted merged PR102: Biomni's probe session becomes $0.25 and the combined probe ledger check $0.30. A3's probe remains $0.05, full-arm sessions $2.50, and the acceptance gate is unchanged. PR101, containing the completed C0 and first stopped probe, was also merged.

Andres directly instructed the operator to pull integration, copy the scripts, run `bash block_h_reset_probe.sh '2026-11-01'`, then restart the chain. Own clone `astra/block-h-comparison` fast-forwarded to execution source `f39c60e`; all ten operational scripts/Dockerfile were copied byte-identically and shell syntax checks passed. The Dockerfile and image payload were not rebuilt or changed during this resumption.

The exact native reset exited 0 at 02:07 UTC and moved 15 files/directories into `L/block_h/failed/h_probe_20261101T0207Z/`, never deleting them. The first chain's outer log was separately moved into these operator receipts because the native reset moves only probe files and the next chain uses the same log path. The completed C0 receipts remained unchanged. No C0, baseline, planning or scoring run was repeated.

Read [resumption and copied-file hashes](receipts/resumption.json), [exact reset command](receipts/reset.command.json), [reset output](receipts/reset.log), [exit/runtime](receipts/reset.runtime.json), [preservation receipt](receipts/reset.receipt.json) and [moved-path list](receipts/reset_moved.txt). The first probe's complete unchanged record remains in [the merged partial publication](../block_h_20261101/README.md).

## Actual native restart refusal

The fresh detached wrapper 21712 started the native chain once, with explicit own H_CLONE and A3_CLIENT=codex, nice19/caffeinate and the existing Mac environment key only. It ran from 02:08:17 to 02:08:18 UTC and exited 3. Its entire native chain log is:

```
2026-11-01T02:08:17Z block H started
NOT STARTED: no image genemila-h (check_tools.sh)
2026-11-01T02:08:18Z block H stopped at the probe
```

No new probe log, proxy record, session or API request was created. Shared ledger before and after remains **$61.575279308, 23867 rows**. No agent container remained active. This is the native controller's pre-session refusal, not a new Biomni/provider failure and not a completed probe. [Exact outcome and read-only diagnostics](receipts/restart_refusal.json), [native log](receipts/failed_native_chain.log), [#51 report](receipts/refusal_issue51.md).

Read-only Docker diagnostics after the stop still listed `genemila-h:latest` at image `sha256:b15af00eb763c5fb0fa8cb8001c3cd2d8b649492b11910ac0b90d5b799466a09`. Inspecting that immutable ID succeeded and reported RepoTags `[genemila-h:latest]`. The native name lookup nevertheless failed; its cause is **not established**. The earlier prelaunch image-name lookup correction is preserved in the merged previous publication; it is not treated as a new unused correction here. No additional name-check invocation, retag, rebuild, source change, workaround or chain retry followed this native refusal.

## New cumulative budget authority

Andres directly authorized cumulative ledger spending up to **$95 for block H and plan DK**, with no further spending approval needed within that ceiling; [authority on #41](https://github.com/andresloak100/Gene-Mila/issues/41#issuecomment-6552139819), [receipt](receipts/budget_authority95.json). His approximately $17 real-money estimate is recorded as his estimate, not a verified conversion between ledger and provider charges. This supersedes the older absolute $76.562649372 authorization for the H/DK scope.

The already-written native H block cap remains `76.56 61.562649 2026-11-01T01:43Z`. Neither it nor the block's starting ledger was reset or silently raised. The native per-session limits remain as prescribed above. Existing funds only, no top-up, no screen/UI interaction and no additional balance inquiry. This stop is unrelated to funds. One paid job at a time; no DK job began during this resumption. The separately requested DK metadata-only check is already complete on #41.

## State and publication

The restarted chain is stopped and its monitor remains paused. Next: explicit resolution of the Docker image-name refusal and authorized resumption, without repeating completed controls or resetting the block cap. Main and synced sources remain untouched. No full H arm, one-worker run, reading or sealed score followed the refusal.

This publication contains reports, indexes and exact operator receipts only. Prior partial records, scripts and science remain unchanged. No task package, data, harness matrix, raw run, image, credential or codex_home cache is included. Every preserved file is indexed and hashed; the provenance maps each copy to its original. All publication checks must pass before push.
