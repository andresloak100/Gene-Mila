**Authorized probe reset succeeded; restarted native H chain stopped in its pre-session image check, with zero new paid calls.**

Read lead6552107893, pulled integrationf39c60e (mergedPR101/102), copied all10 H scripts/Dockerfile byte-identically. Exact reset `bash block_h_reset_probe.sh '2026-11-01'` exited0, preserving15 files/directories under `L/block_h/failed/h_probe_20261101T0207Z/`; old chain log also preserved separately. C0 receipts and native once-only cap unchanged.

Restart wrapper21712 ran once **02:08:17–02:08:18UTC**, nativechain **exit3**. Its exact log is:
```
2026-11-01T02:08:17Z block H started
NOT STARTED: no image genemila-h (check_tools.sh)
2026-11-01T02:08:18Z block H stopped at the probe
```
No new probe log/proxy/session or request was created. Shared ledger remains **61.575279308/23867rows**, unchanged. The newly approved cumulative **$95 H/DK ceiling** is recorded on41/6552139819; original H cap76.56 and probe/session limits were not altered by the operator. This refusal is unrelated to funds.

Read-only diagnostics after the stop show Docker STILL LISTS `genemila-h:latest` at the validated immutable image `sha256:b15af00eb763c5fb0fa8cb8001c3cd2d8b649492b11910ac0b90d5b799466a09`, and inspecting that immutable ID succeeds with RepoTags `[genemila-h:latest]`. The native name lookup nevertheless failed; cause is **not established**. No image-name check rerun, retag/rebuild, native-script patch, fallback or chain retry followed. The earlier prelaunch name-lookup correction was already recorded in6551896514/6551898316; this is now the native controller's actual refusal, not a failed operator test.

All new receipts are preserved at P/block_h_ops/probe_restart_20261101. H stays stopped under the unchanged failure rule; heartbeat remains paused. Updating HANDOFF/liveSTATE and publishing these exact reset/refusal receipts for the lead. No C0/closed baseline or DK job was repeated/started; no screen use or balance inquiry.
