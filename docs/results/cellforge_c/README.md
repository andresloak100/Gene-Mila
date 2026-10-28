# Plan C evidence, 28 October 2026

Read [the final checkpoint review](checkpoint1_review.md) and [JSON twin](checkpoint1_review.json). The plan was posted and rejected at checkpoint 1. Task analysis and method design exited 0; no coding, training or score followed. This folder records that outcome, not a matched CellForge result.

The requested export adapter correction is commit c384e66. Full tests passed: 681 passed, 1 skipped, 8 warnings. Source pin, input/cohort disclosure, caps, usage and containment limits are retained. No raw data, package, environment, predictions or credential is committed. Earlier preparation/status files are immutable historical snapshots and are superseded by the final checkpoint review.

Every file is listed below; [publication_manifest.json](publication_manifest.json) gives the exact hash and size of every other file in this folder. The manifest omits itself to avoid a circular hash.

| File | Purpose |
|---|---|
| [README.md](README.md) | Reading guide and exhaustive per-file index |
| [access_boundary_free_tests.json](access_boundary_free_tests.json) | Free filesystem boundary checks |
| [analysis_pipeline.exit](analysis_pipeline.exit) | Controller exit marker |
| [analysis_pipeline.py](analysis_pipeline.py) | Executed controller snapshot; stops before code generation |
| [analysis_pipeline_final.json](analysis_pipeline_final.json) | Final meter health after 59 calls |
| [balance_after.json](balance_after.json) | Free post-run balance API reading; not console |
| [balance_before.json](balance_before.json) | Free pre-run balance API reading; not console |
| [cap.json](cap.json) | Fixed authorized ledger baseline and five-dollar ceiling |
| [cellforge_analysis.sb](cellforge_analysis.sb) | Executed OS filesystem/network boundary profile |
| [checkpoint1_audit.json](checkpoint1_audit.json) | 16 checks: pinned literal templates, provenance, phase exits and artifact hashes |
| [checkpoint1_issue51.json](checkpoint1_issue51.json) | Posting receipt |
| [checkpoint1_issue51.md](checkpoint1_issue51.md) | Complete unchanged plan and rejection as posted before approval |
| [checkpoint1_review.json](checkpoint1_review.json) | Machine-readable final decision, phase status, ledger and limitations |
| [checkpoint1_review.md](checkpoint1_review.md) | Final checkpoint decision and interpretation (read first) |
| [completion_process_check.json](completion_process_check.json) | No matching paid, lab, reader or controller process at completion |
| [corrected_export.command.txt](corrected_export.command.txt) | corrected export exact invocation |
| [corrected_export.exit](corrected_export.exit) | corrected export exit status |
| [corrected_export.json](corrected_export.json) | Valid export receipt with source/cohort disclosure |
| [corrected_export.log](corrected_export.log) | corrected export unchanged output |
| [corrected_export_audit.json](corrected_export_audit.json) | Corrected export shape, gene order and no-held-out-cell checks |
| [export.command.txt](export.command.txt) | export exact invocation |
| [export.exit](export.exit) | export exit status |
| [export.json](export.json) | Original empty export receipt, preserved exactly |
| [export.log](export.log) | export unchanged output |
| [export_label_audit.json](export_label_audit.json) | Public label/source-count audit explaining adapter correction and extra cells |
| [generated_artifact_manifest.json](generated_artifact_manifest.json) | Source paths and byte hashes of generated artifacts copied unchanged |
| [install.command.txt](install.command.txt) | install exact invocation |
| [install.exit](install.exit) | install exit status |
| [install.log](install.log) | install unchanged output |
| [ledger_after.json](ledger_after.json) | Read-only shared ledger totals and rounding audit |
| [method_design.command.txt](method_design.command.txt) | method design exact invocation |
| [method_design.exit](method_design.exit) | method design exit status |
| [method_design.log](method_design.log) | method design unchanged output |
| [network_boundary_free_checks.py](network_boundary_free_checks.py) | Free network boundary check script snapshot |
| [network_boundary_free_tests.json](network_boundary_free_tests.json) | Free network boundary checks |
| [operator_preflight.md](operator_preflight.md) | Preparation narrative before the checkpoint; superseded by final review |
| [phase_imports.exit](phase_imports.exit) | Free phase import check exit marker |
| [phase_imports.log](phase_imports.log) | Free phase import check output |
| [pip_freeze.txt](pip_freeze.txt) | Separate CellForge environment packages |
| [prepaid_protocol.json](prepaid_protocol.json) | Historical preparation snapshot while full tests were running |
| [proxy.command.txt](proxy.command.txt) | Exact meter invocation, variable reference only |
| [proxy.jsonl](proxy.jsonl) | Meter events and actual usage, no credential values |
| [proxy.process.log](proxy.process.log) | Meter process output (empty) |
| [publication_manifest.json](publication_manifest.json) | Hashes and sizes of all other evidence files |
| [pytest.command.txt](pytest.command.txt) | pytest exact invocation |
| [pytest.exit](pytest.exit) | pytest exit status |
| [pytest.log](pytest.log) | pytest unchanged output |
| [research_plan_20261027_232337.json](research_plan_20261027_232337.json) | Unchanged generated research plan artifact |
| [research_plan_20261027_232337.md](research_plan_20261027_232337.md) | Unchanged generated research plan artifact |
| [research_plan_20261027_232337.mmd](research_plan_20261027_232337.mmd) | Unchanged generated research plan artifact |
| [research_plan_20261027_232337_consensus.png](research_plan_20261027_232337_consensus.png) | Unchanged generated research plan artifact |
| [retrieval_trace.jsonl](retrieval_trace.jsonl) | Unchanged method-design retrieval trace |
| [runtime_start.json](runtime_start.json) | Pre-paid runtime/source/input provenance |
| [stop.json](stop.json) | Historical empty-export stop; preserved, not the final checkpoint status |
| [strict_proxy.py](strict_proxy.py) | Snapshot of executed external strict metering proxy |
| [strict_proxy_free_checks.py](strict_proxy_free_checks.py) | Snapshot of executed free fake-upstream tests, renamed to avoid suite collection |
| [strict_proxy_free_tests.json](strict_proxy_free_tests.json) | Free fake-upstream test receipt |
| [task_analysis.command.txt](task_analysis.command.txt) | task analysis exact invocation |
| [task_analysis.exit](task_analysis.exit) | task analysis exit status |
| [task_analysis.log](task_analysis.log) | task analysis unchanged output |
| [task_analysis_20261027_232055.json](task_analysis_20261027_232055.json) | Unchanged generated task analysis |
