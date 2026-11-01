Block H budget gate — STOP before launch (31 October 2026).

I read the lead's [C2 closure](https://github.com/andresloak100/Gene-Mila/issues/51#issuecomment-6550203502), pulled integration to `fd97ee3270a5051e82d70ee5e487246a76059999`, and read the current H plan and cap/check scripts. CellForge C2 is closed; no repair or regeneration.

[PLAN_H_COMPARISON.md, Money](https://github.com/andresloak100/Gene-Mila/blob/fd97ee3270a5051e82d70ee5e487246a76059999/docs/PLAN_H_COMPARISON.md#L116) prescribes a **$15 block allowance**, expected $8–13, and $2.50 per-session caps (two separate $0.05 probes; A2 worker1.0 + planner1.5). The actual shared ledger is **$61.562649372**, leaving **$4.677884660** under Andres's unchanged **$66.240534032** ceiling. The prescribed block allowance does **not** fit.

The existing cap helper would write **$76.56** after rounding down to cents, above the authorized ceiling. I did **not** execute it, write a cap file, alter scripts, launch any H job or make a paid call. This is the full block allowance mismatch, not a claim that all sequential session caps must be reserved simultaneously.

A full $15 allowance at today's ledger would require cumulative ceiling **$76.562649372**, which is **$10.322115340** above the currently authorized ceiling. I asked Andres whether to keep the current ceiling and await a revised H plan, or expressly authorize that new ceiling. Neither a budget increase nor a reduced H protocol is inferred. H remains stopped pending the answer; heartbeat stays paused.

Budget/source receipt:
```json
{
  "utc": "2026-10-31T22:54:25.618315+00:00",
  "integration_head": "fd97ee3270a5051e82d70ee5e487246a76059999",
  "lead_C2_closure_id": 6550203502,
  "ledger_sql_sum_cost_usd": 61.562649371999996,
  "ledger_rows": 23865,
  "ledger_display_9dp": "61.562649372",
  "cumulative_ceiling": "66.240534032",
  "remaining_9dp": "4.677884660",
  "H_prescribed_block_allowance": "15.00",
  "H_expected_cost_range": [
    "8",
    "13"
  ],
  "H_proxy_session_cap": "2.50",
  "H_A2_worker_cap": "1.0",
  "H_A2_planner_cap": "1.5",
  "H_probe_per_route_cap": "0.05",
  "full_15_allowance_ceiling_9dp": "76.562649372",
  "increase_above_current_ceiling_9dp": "10.322115340",
  "cap_helper_would_write_2dp": "76.56",
  "budget_fits": false,
  "paid_calls": 0,
  "H_jobs_started": 0,
  "cap_file_written": false,
  "script_modified": false,
  "status": "STOP awaiting explicit budget or revised-plan decision",
  "sources": [
    {
      "path": "docs/PLAN_H_COMPARISON.md",
      "sha256": "693b5ef574620ad599ffea92b25cb671dee070e01a9ee9a43dde5ea26380990b"
    },
    {
      "path": "docs/mac/block_h/block_h_cap.sh",
      "sha256": "14ab42501f6abbee9d773b934a3f30c22b631830f286c5ecbd664bd39ba461ae"
    },
    {
      "path": "docs/mac/block_h/block_h_common.sh",
      "sha256": "5522ec8e4013d89e280f3ace7e338b0676b14fa349b85dc7926afe83ee0e100b"
    }
  ],
  "question": "Keep current ceiling and await revised H plan, or authorize cumulative ceiling76.562649372 for prescribed15 allowance?",
  "note": "9dp figures are display rounding only; ledger is read-only and unchanged. Session caps are not summed as simultaneous reservations."
}
```
