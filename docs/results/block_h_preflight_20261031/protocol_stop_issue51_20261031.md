Block H: budget resolved, current-source probe gate still fails to enforce the fixed plan — STOP before paid launch.

Andres authorized cumulative **$76.562649372** (#41/comment6550695646, #51/comment6550695786), using only the existing DeepSeek balance with no top-up/additional purchase. His current screenshot shows topped-up $28.19 plus granted $7.61, so the required $8 topped-up floor is satisfied (#51/comment6550702479). This stop is **not a money shortage**.

Own fresh clone `Project/gene-mila-block-h`, branch `astra/block-h-comparison`, integration20ac06bdd65729def50d78657ae5257be93dd666, unchanged source. Before any paid call I rechecked the known probe-controller gap at current head:
- [Plan line329](https://github.com/andresloak100/Gene-Mila/blob/20ac06bdd65729def50d78657ae5257be93dd666/docs/PLAN_H_COMPARISON.md#L329) requires at least two Codex status200 rows and no400.
- `block_h_probe.sh:56` calls `session_after h_probe`; `block_h_common.sh:208–234` pools matching probe logs, counts error statuses, but rejects only zero pooled successes or the wrong served model. It does not enforce the Codex-specific count/no400 condition.
- `block_h_common.sh:240` creates the passed marker when its other checks pass; `block_h_chain.sh:15–16` then automatically advances to full arms after probe exit0.
- I extracted the **unchanged log-checker fragment** and ran it on clearly labeled synthetic fixtures only. A single expected-model200 returned0; a200 followed by400 also returned0; pooled Biomni200 with zero Codex200 also returned0. These are source-level counterexamples, **not live probe results**. Client/other session checks were not executed, and no live route failure is inferred.

Standing instruction says report an unresolved protocol inability and do not silently patch scripts, add gates or work around it. Running the prescribed detached chain now would not ensure the plan's probe gate. No script patch or replacement gate was added.

**Stopped before paid work.** No H probe/arm/C0, Docker setup/build, cap helper or paid call has run; no H cap file was written. Docker daemon itself is available(version29.2.1 read-only query), no screen session was present. Shared ledger remains61.562649372 and approved cumulative ceiling76.562649372. C2 remains closed.

Exact synthetic fixtures, copied checker, outputs/exits and source hashes are preserved under `Project/block_h_ops/probe_gate_source_check_20261031/`. I will publish the preflight evidence after all publication checks, synchronize HANDOFF/live state and keep the heartbeat paused. The lead/code owner needs to resolve this current controller/plan mismatch before the paid chain can start as written.
