# CellForge C2: CPU failure and complete artifact index

Read [the CPU failure report](training_failure.md) ([JSON](training_failure.json)) first. The lead reversed the original checkpoint-2 rejection; the unchanged approved script executed once and failed before training. No predictions or score exists; no repair, retry or Block H followed.

Label: **CellForge (pinned release, checkpoint plan edited to the input as its README allows)**. The original C1 attempt is [preserved separately](../cellforge_c/README.md). All old raw records, failures, the original rejection, lead reversal and approval are retained.

The approved input is `/Users/andresarriaga/cellforge_adamson_export_corrected_20261028/cellforge_input.h5ad`, SHA-256 `ab43e03dc5ea2b73e057a38eac957222ab2a0dbe31627b7808d82c4149f0163a`. Its cohort caveat remains 1,770 extra controls and 10 training cells relative to the original bundle ingest. Raw input and work remain outside Git.

The original artifact_manifest.json and publication_audit_20261031.json are historical records of commit 35d9853. Their two authored indexes are retained byte for byte in the pre_reversal copies. The new completion_manifest_20261031_cpu_failure.json pins the current complete publication, excluding only itself and its new audit to avoid circular hashes. Raw records are unchanged.

| File | Record |
|---|---|
| [FREE_PREPARATION_STOP.json](FREE_PREPARATION_STOP.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [README.md](README.md) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [STOP_codegen_boundary_20261030.json](STOP_codegen_boundary_20261030.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [access_and_codegen_free_20261030.operator.txt](access_and_codegen_free_20261030.operator.txt) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [access_boundary_resumed_20261030.json](access_boundary_resumed_20261030.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [analysis_pipeline.exit](analysis_pipeline.exit) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [analysis_pipeline.live_method_design.json](analysis_pipeline.live_method_design.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [analysis_pipeline.live_task_analysis.json](analysis_pipeline.live_task_analysis.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [analysis_pipeline.operator.txt](analysis_pipeline.operator.txt) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [analysis_pipeline.started.json](analysis_pipeline.started.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [analysis_pipeline_final.json](analysis_pipeline_final.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [artifact_manifest.json](artifact_manifest.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [artifact_manifest_before_eof_fix.json](artifact_manifest_before_eof_fix.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [caffeinate.json](caffeinate.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [cap.json](cap.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [cap_authority_confirmation_20261029.json](cap_authority_confirmation_20261029.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [cap_authority_issue41_20261029.json](cap_authority_issue41_20261029.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [cap_authority_issue41_20261029.md](cap_authority_issue41_20261029.md) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [cellforge_analysis.sb](cellforge_analysis.sb) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [checkpoint1_approval.json](checkpoint1_approval.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [checkpoint1_approval_issue51.json](checkpoint1_approval_issue51.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [checkpoint1_approval_issue51.md](checkpoint1_approval_issue51.md) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [checkpoint1_candidate.diff](checkpoint1_candidate.diff) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [checkpoint1_candidate.json](checkpoint1_candidate.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [checkpoint1_candidate.md](checkpoint1_candidate.md) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [checkpoint1_diff_issue51.json](checkpoint1_diff_issue51.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [checkpoint1_diff_issue51.md](checkpoint1_diff_issue51.md) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [checkpoint1_edit_operations.json](checkpoint1_edit_operations.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [checkpoint1_exact.diff](checkpoint1_exact.diff) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [checkpoint2_approval.json](checkpoint2_approval.json) | Approval before the sole CPU execution |
| [checkpoint2_approval_reversal_issue51.json](checkpoint2_approval_reversal_issue51.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [checkpoint2_approval_reversal_issue51.md](checkpoint2_approval_reversal_issue51.md) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [checkpoint2_publication_index_20261031_pre_reversal.md](checkpoint2_publication_index_20261031_pre_reversal.md) | Byte-exact historical authored index before the reversal |
| [checkpoint2_rejection_issue51.json](checkpoint2_rejection_issue51.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [checkpoint2_rejection_issue51.md](checkpoint2_rejection_issue51.md) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [checkpoint2_review.json](checkpoint2_review.json) | Original static rejection; superseded by the lead reversal, retained unchanged |
| [checkpoint2_review.md](checkpoint2_review.md) | Original static rejection; superseded by the lead reversal, retained unchanged |
| [checkpoint2_review_before_eof_fix.md.txt](checkpoint2_review_before_eof_fix.md.txt) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [checkpoint2_stop_containment.json](checkpoint2_stop_containment.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen.command.json](codegen.command.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen.exit](codegen.exit) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen.log](codegen.log) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen.runtime.json](codegen.runtime.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen.started.json](codegen.started.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen_artifacts/AGENTS.md](codegen_artifacts/AGENTS.md) | Unchanged first-codegen artifact, prompt, contract, boundary or log |
| [codegen_artifacts/acceptance_contract.json](codegen_artifacts/acceptance_contract.json) | Unchanged first-codegen artifact, prompt, contract, boundary or log |
| [codegen_artifacts/backend_result.json](codegen_artifacts/backend_result.json) | Unchanged first-codegen artifact, prompt, contract, boundary or log |
| [codegen_artifacts/codegen_process_boundary.sb](codegen_artifacts/codegen_process_boundary.sb) | Unchanged first-codegen artifact, prompt, contract, boundary or log |
| [codegen_artifacts/controller_cli_command.json](codegen_artifacts/controller_cli_command.json) | Unchanged first-codegen artifact, prompt, contract, boundary or log |
| [codegen_artifacts/controller_delivery_override.txt](codegen_artifacts/controller_delivery_override.txt) | Unchanged first-codegen artifact, prompt, contract, boundary or log |
| [codegen_artifacts/controller_delivery_receipt.json](codegen_artifacts/controller_delivery_receipt.json) | Unchanged first-codegen artifact, prompt, contract, boundary or log |
| [codegen_artifacts/controller_effective_prompt.txt](codegen_artifacts/controller_effective_prompt.txt) | Unchanged first-codegen artifact, prompt, contract, boundary or log |
| [codegen_artifacts/controller_input_prompt.txt](codegen_artifacts/controller_input_prompt.txt) | Unchanged first-codegen artifact, prompt, contract, boundary or log |
| [codegen_artifacts/delivery_schema.json](codegen_artifacts/delivery_schema.json) | Unchanged first-codegen artifact, prompt, contract, boundary or log |
| [codegen_artifacts/logs/agent_events.jsonl](codegen_artifacts/logs/agent_events.jsonl) | Unchanged first-codegen artifact, prompt, contract, boundary or log |
| [codegen_artifacts/logs/codex_attempt_01.txt](codegen_artifacts/logs/codex_attempt_01.txt) | Unchanged first-codegen artifact, prompt, contract, boundary or log |
| [codegen_artifacts/logs/codex_events_raw_attempt_01.jsonl](codegen_artifacts/logs/codex_events_raw_attempt_01.jsonl) | Unchanged first-codegen artifact, prompt, contract, boundary or log |
| [codegen_artifacts/logs/codex_stderr_attempt_01.log](codegen_artifacts/logs/codex_stderr_attempt_01.log) | Unchanged first-codegen artifact, prompt, contract, boundary or log |
| [codegen_artifacts/research_plan.json](codegen_artifacts/research_plan.json) | Unchanged first-codegen artifact, prompt, contract, boundary or log |
| [codegen_artifacts/result.py](codegen_artifacts/result.py) | Unchanged first-codegen artifact, prompt, contract, boundary or log |
| [codegen_boundary_stop_issue51_20261030.json](codegen_boundary_stop_issue51_20261030.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen_boundary_stop_issue51_20261030.md](codegen_boundary_stop_issue51_20261030.md) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen_delivery.json](codegen_delivery.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen_effective_tools_free_20261030.json](codegen_effective_tools_free_20261030.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen_launch_20261031.json](codegen_launch_20261031.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen_once.operator.txt](codegen_once.operator.txt) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen_script_issue51.json](codegen_script_issue51.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen_script_issue51.md](codegen_script_issue51.md) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen_tool_check_corrected_20261030/authorized_fix.diff](codegen_tool_check_corrected_20261030/authorized_fix.diff) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen_tool_check_corrected_20261030/codegen_effective_tools_free_20261030.json](codegen_tool_check_corrected_20261030/codegen_effective_tools_free_20261030.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen_tool_check_corrected_20261030/codegen_tool_probe.command.json](codegen_tool_check_corrected_20261030/codegen_tool_probe.command.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen_tool_check_corrected_20261030/codegen_tool_probe.stderr.log](codegen_tool_check_corrected_20261030/codegen_tool_probe.stderr.log) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen_tool_check_corrected_20261030/codegen_tool_probe.stdout.log](codegen_tool_check_corrected_20261030/codegen_tool_probe.stdout.log) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen_tool_check_corrected_20261030/fix_authority.json](codegen_tool_check_corrected_20261030/fix_authority.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen_tool_check_corrected_20261030/operator.txt](codegen_tool_check_corrected_20261030/operator.txt) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen_tool_probe.command.json](codegen_tool_probe.command.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen_tool_probe.stderr.log](codegen_tool_probe.stderr.log) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codegen_tool_probe.stdout.log](codegen_tool_probe.stdout.log) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [codex_delivery_boundary.operator.txt](codex_delivery_boundary.operator.txt) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [completion_manifest_20261031_cpu_failure.json](completion_manifest_20261031_cpu_failure.json) | Current publication byte sizes and SHA-256 hashes |
| [delivery_boundary_free.operator.txt](delivery_boundary_free.operator.txt) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [delivery_boundary_free_20261030/command.json](delivery_boundary_free_20261030/command.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [delivery_boundary_free_20261030/exit](delivery_boundary_free_20261030/exit) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [delivery_boundary_free_20261030/report.json](delivery_boundary_free_20261030/report.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [delivery_boundary_free_20261030/request_capture.json](delivery_boundary_free_20261030/request_capture.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [delivery_boundary_free_20261030/runtime.json](delivery_boundary_free_20261030/runtime.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [delivery_boundary_free_20261030/stderr.log](delivery_boundary_free_20261030/stderr.log) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [delivery_boundary_free_20261030/stdout.log](delivery_boundary_free_20261030/stdout.log) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [existing_environment_imports.command.json](existing_environment_imports.command.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [existing_environment_imports.exit](existing_environment_imports.exit) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [existing_environment_imports.log](existing_environment_imports.log) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [existing_environment_imports.runtime.json](existing_environment_imports.runtime.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [free_preflight_runner.operator.txt](free_preflight_runner.operator.txt) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [free_preflight_stop_issue51.json](free_preflight_stop_issue51.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [free_preflight_stop_issue51.md](free_preflight_stop_issue51.md) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [handoff_publication_failure_metadata_20261030.json](handoff_publication_failure_metadata_20261030.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [index_before_eof_fix.md.txt](index_before_eof_fix.md.txt) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [lead_checkpoint2_reversal_20261031.json](lead_checkpoint2_reversal_20261031.json) | Lead decision approving the exact existing script |
| [lead_checkpoint2_reversal_20261031.md](lead_checkpoint2_reversal_20261031.md) | Lead decision approving the exact existing script |
| [method_design.command.txt](method_design.command.txt) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [method_design.exit](method_design.exit) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [method_design.log](method_design.log) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [method_design.runtime.json](method_design.runtime.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [network_boundary_free.command.json](network_boundary_free.command.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [network_boundary_free.exit](network_boundary_free.exit) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [network_boundary_free.log](network_boundary_free.log) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [network_boundary_free.runtime.json](network_boundary_free.runtime.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [network_boundary_free_checks.py](network_boundary_free_checks.py) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [network_boundary_free_tests.json](network_boundary_free_tests.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [operator_approval_receipt_correction_20261031.diff](operator_approval_receipt_correction_20261031.diff) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [operator_approval_receipt_correction_20261031.json](operator_approval_receipt_correction_20261031.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [operator_approval_receipt_failure_20261030.command.txt](operator_approval_receipt_failure_20261030.command.txt) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [operator_approval_receipt_failure_20261030.exit](operator_approval_receipt_failure_20261030.exit) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [operator_approval_receipt_failure_20261030.json](operator_approval_receipt_failure_20261030.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [operator_approval_receipt_failure_20261030.log](operator_approval_receipt_failure_20261030.log) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [operator_approval_receipt_failure_20261030.md](operator_approval_receipt_failure_20261030.md) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [operator_approval_receipt_failure_20261030.stdin.txt](operator_approval_receipt_failure_20261030.stdin.txt) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [operator_stop_issue51_20261030.json](operator_stop_issue51_20261030.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [operator_stop_issue51_20261030.md](operator_stop_issue51_20261030.md) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [planning_complete.json](planning_complete.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [preflight_resumed_20261030/authorized_checker_fix.diff](preflight_resumed_20261030/authorized_checker_fix.diff) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [preflight_resumed_20261030/existing_environment_imports.command.json](preflight_resumed_20261030/existing_environment_imports.command.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [preflight_resumed_20261030/existing_environment_imports.exit](preflight_resumed_20261030/existing_environment_imports.exit) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [preflight_resumed_20261030/existing_environment_imports.log](preflight_resumed_20261030/existing_environment_imports.log) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [preflight_resumed_20261030/existing_environment_imports.runtime.json](preflight_resumed_20261030/existing_environment_imports.runtime.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [preflight_resumed_20261030/free_preflight_runner.operator.txt](preflight_resumed_20261030/free_preflight_runner.operator.txt) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [preflight_resumed_20261030/network_boundary_free.command.json](preflight_resumed_20261030/network_boundary_free.command.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [preflight_resumed_20261030/network_boundary_free.exit](preflight_resumed_20261030/network_boundary_free.exit) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [preflight_resumed_20261030/network_boundary_free.log](preflight_resumed_20261030/network_boundary_free.log) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [preflight_resumed_20261030/network_boundary_free.runtime.json](preflight_resumed_20261030/network_boundary_free.runtime.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [preflight_resumed_20261030/network_boundary_free_checks_resumed_20261030.py](preflight_resumed_20261030/network_boundary_free_checks_resumed_20261030.py) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [preflight_resumed_20261030/network_boundary_free_tests.json](preflight_resumed_20261030/network_boundary_free_tests.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [preflight_resumed_20261030/resume_authority.json](preflight_resumed_20261030/resume_authority.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [preflight_resumed_20261030/strict_meter_free.command.json](preflight_resumed_20261030/strict_meter_free.command.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [preflight_resumed_20261030/strict_meter_free.exit](preflight_resumed_20261030/strict_meter_free.exit) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [preflight_resumed_20261030/strict_meter_free.log](preflight_resumed_20261030/strict_meter_free.log) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [preflight_resumed_20261030/strict_meter_free.runtime.json](preflight_resumed_20261030/strict_meter_free.runtime.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [preflight_resumed_20261030/strict_proxy_free_tests.json](preflight_resumed_20261030/strict_proxy_free_tests.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [preflight_resumed_20261030/test_strict_proxy_free_resumed_20261030.py](preflight_resumed_20261030/test_strict_proxy_free_resumed_20261030.py) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [prepaid_gates_20261030.json](prepaid_gates_20261030.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [proxy.command.txt](proxy.command.txt) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [proxy.jsonl](proxy.jsonl) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [proxy.process.log](proxy.process.log) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [proxy_start_health.json](proxy_start_health.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [publication_audit_20261031.json](publication_audit_20261031.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [publication_audit_20261031_cpu_failure.json](publication_audit_20261031_cpu_failure.json) | Current publication checks passed before push |
| [publication_check_corrected_20261030.json](publication_check_corrected_20261030.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [publication_checks.operator.txt](publication_checks.operator.txt) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [publication_cpu_failure.operator.txt](publication_cpu_failure.operator.txt) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [publication_precheck_failed.operator.txt](publication_precheck_failed.operator.txt) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [publication_precheck_failure_20261031.json](publication_precheck_failure_20261031.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [publication_precheck_failure_20261031.log](publication_precheck_failure_20261031.log) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [publication_stop_addendum_issue51_20261030.json](publication_stop_addendum_issue51_20261030.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [publication_stop_addendum_issue51_20261030.md](publication_stop_addendum_issue51_20261030.md) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [raw_plan_issue51.json](raw_plan_issue51.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [raw_plan_issue51.md](raw_plan_issue51.md) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [raw_planning/analyses/cellforge_input/retrieval/retrieval_trace.jsonl](raw_planning/analyses/cellforge_input/retrieval/retrieval_trace.jsonl) | Unchanged fresh C2 planning artifact |
| [raw_planning/analyses/cellforge_input/task_analysis_20261030_140934.json](raw_planning/analyses/cellforge_input/task_analysis_20261030_140934.json) | Unchanged fresh C2 planning artifact |
| [raw_planning/discussion/cellforge_input/discussion_round_6.json](raw_planning/discussion/cellforge_input/discussion_round_6.json) | Unchanged fresh C2 planning artifact |
| [raw_planning/discussion/cellforge_input/discussion_summary.json](raw_planning/discussion/cellforge_input/discussion_summary.json) | Unchanged fresh C2 planning artifact |
| [raw_planning/plans/cellforge_input/research_plan_20261030_141205.json](raw_planning/plans/cellforge_input/research_plan_20261030_141205.json) | Unchanged fresh C2 planning artifact |
| [raw_planning/plans/cellforge_input/research_plan_20261030_141205.md](raw_planning/plans/cellforge_input/research_plan_20261030_141205.md) | Unchanged fresh C2 planning artifact |
| [raw_planning/plans/cellforge_input/research_plan_20261030_141205.mmd](raw_planning/plans/cellforge_input/research_plan_20261030_141205.mmd) | Unchanged fresh C2 planning artifact |
| [raw_planning/plans/cellforge_input/research_plan_20261030_141205_consensus.png](raw_planning/plans/cellforge_input/research_plan_20261030_141205_consensus.png) | Unchanged fresh C2 planning artifact |
| [raw_planning/plans/cellforge_input/retrieval/retrieval_trace.jsonl](raw_planning/plans/cellforge_input/retrieval/retrieval_trace.jsonl) | Unchanged fresh C2 planning artifact |
| [result.raw.py](result.raw.py) | Exact generated script, executed once and unchanged |
| [results_index_20261031_pre_reversal.md](results_index_20261031_pre_reversal.md) | Byte-exact historical authored index before the reversal |
| [resumed_preflight_issue51_20261030.json](resumed_preflight_issue51_20261030.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [resumed_preflight_issue51_20261030.md](resumed_preflight_issue51_20261030.md) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [resumption_issue51_20261031.json](resumption_issue51_20261031.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [resumption_issue51_20261031.md](resumption_issue51_20261031.md) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [setup_preflight.json](setup_preflight.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [stop_receipt.json](stop_receipt.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [strict_meter_free.command.json](strict_meter_free.command.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [strict_meter_free.exit](strict_meter_free.exit) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [strict_meter_free.log](strict_meter_free.log) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [strict_meter_free.runtime.json](strict_meter_free.runtime.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [strict_proxy.py](strict_proxy.py) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [strict_proxy_free_tests.json](strict_proxy_free_tests.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [task_analysis.command.txt](task_analysis.command.txt) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [task_analysis.exit](task_analysis.exit) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [task_analysis.log](task_analysis.log) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [task_analysis.runtime.json](task_analysis.runtime.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [test_strict_proxy_free.py](test_strict_proxy_free.py) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [training.child.json](training.child.json) | Sole CPU execution command, traceback, exit or measured runtime |
| [training.command.txt](training.command.txt) | Sole CPU execution command, traceback, exit or measured runtime |
| [training.exit](training.exit) | Sole CPU execution command, traceback, exit or measured runtime |
| [training.log](training.log) | Sole CPU execution command, traceback, exit or measured runtime |
| [training.runtime.json](training.runtime.json) | Sole CPU execution command, traceback, exit or measured runtime |
| [training.started.json](training.started.json) | Sole CPU execution command, traceback, exit or measured runtime |
| [training_boundary.sb](training_boundary.sb) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [training_config.json](training_config.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [training_driver.exit](training_driver.exit) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [training_driver.operator.txt](training_driver.operator.txt) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [training_driver_final.json](training_driver_final.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [training_failure.json](training_failure.json) | Actual generated-script runtime failure and STOP report |
| [training_failure.md](training_failure.md) | Actual generated-script runtime failure and STOP report |
| [training_failure_issue51.json](training_failure_issue51.json) | Actual generated-script runtime failure and STOP report |
| [training_failure_issue51.md](training_failure_issue51.md) | Actual generated-script runtime failure and STOP report |
| [training_launch.json](training_launch.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [training_metadata_preflight.command.json](training_metadata_preflight.command.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [training_metadata_preflight.exit](training_metadata_preflight.exit) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [training_metadata_preflight.json](training_metadata_preflight.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [training_metadata_preflight.log](training_metadata_preflight.log) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [training_metadata_preflight.operator.txt](training_metadata_preflight.operator.txt) | Preserved command, output, provenance, runtime, check or coordination receipt |
| [training_post_exit_integrity.json](training_post_exit_integrity.json) | Preserved command, output, provenance, runtime, check or coordination receipt |
