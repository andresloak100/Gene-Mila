# GEARS Adamson artifacts

Read [aggregate.md](aggregate.md) ([JSON](aggregate.json)) for the result and limitations. The original training work and predictions remain outside Git. Training source d5e842f; scoring source37d991d, with scientific source unchanged. All three seed reports are one level above, at their exact prescribed output paths.

Each bridge command internally makes three oracle scorings (one standalone and two paired); three seeds remain the three replicates. No rescore or tuning followed. This index includes all files in this directory, including final publication audit/manifest.

| File | Purpose |
|---|---|
| [README.md](README.md) | This complete artifact index |
| [aggregate.json](aggregate.json) | Three-seed full-precision aggregation, narrative or its operator/issue receipt |
| [aggregate.md](aggregate.md) | Three-seed full-precision aggregation, narrative or its operator/issue receipt |
| [aggregate.operator.txt](aggregate.operator.txt) | Three-seed full-precision aggregation, narrative or its operator/issue receipt |
| [aggregate_issue51.json](aggregate_issue51.json) | Three-seed full-precision aggregation, narrative or its operator/issue receipt |
| [aggregate_issue51.md](aggregate_issue51.md) | Three-seed full-precision aggregation, narrative or its operator/issue receipt |
| [continuation_monitor.json](continuation_monitor.json) | Authorization, progress or posted issue/monitor receipt |
| [environment_import_check.command.txt](environment_import_check.command.txt) | Separate baseline environment install/import/provenance record |
| [environment_import_check.json](environment_import_check.json) | Separate baseline environment install/import/provenance record |
| [environment_import_check.operator.txt](environment_import_check.operator.txt) | Separate baseline environment install/import/provenance record |
| [environment_install.command.txt](environment_install.command.txt) | Separate baseline environment install/import/provenance record |
| [environment_install.exit](environment_install.exit) | Separate baseline environment install/import/provenance record |
| [environment_install.log](environment_install.log) | Separate baseline environment install/import/provenance record |
| [environment_install.runtime.json](environment_install.runtime.json) | Separate baseline environment install/import/provenance record |
| [focused_tests.command.txt](focused_tests.command.txt) | Seven focused pre-training tests and exclusive command/log/exit/runtime |
| [focused_tests.exit](focused_tests.exit) | Seven focused pre-training tests and exclusive command/log/exit/runtime |
| [focused_tests.log](focused_tests.log) | Seven focused pre-training tests and exclusive command/log/exit/runtime |
| [focused_tests.runtime.json](focused_tests.runtime.json) | Seven focused pre-training tests and exclusive command/log/exit/runtime |
| [input_preflight.json](input_preflight.json) | Approved export training-only shape/identity/hash preflight |
| [input_preflight.operator.txt](input_preflight.operator.txt) | Approved export training-only shape/identity/hash preflight |
| [pip_freeze.txt](pip_freeze.txt) | Separate baseline environment install/import/provenance record |
| [pip_install_report.json](pip_install_report.json) | Separate baseline environment install/import/provenance record |
| [post_gears_ledger.json](post_gears_ledger.json) | Read-only shared ledger check after free GEARS jobs |
| [prescore_issue51.json](prescore_issue51.json) | Authorization, progress or posted issue/monitor receipt |
| [prescore_issue51.md](prescore_issue51.md) | Authorization, progress or posted issue/monitor receipt |
| [prescore_protocol.json](prescore_protocol.json) | Pre-score source and protocol audit |
| [publication_audit.json](publication_audit.json) | Final scope, secret, hash, source and staged-blob checks |
| [publication_manifest.json](publication_manifest.json) | SHA-256 and byte inventory of publication artifacts; explicitly excludes itself and final audit |
| [scoring_chain.exit](scoring_chain.exit) | Once-only sequential bridge scoring command/log/exit/runtime/operator/issue receipt |
| [scoring_chain.final.json](scoring_chain.final.json) | Once-only sequential bridge scoring command/log/exit/runtime/operator/issue receipt |
| [scoring_chain.live.json](scoring_chain.live.json) | Once-only sequential bridge scoring command/log/exit/runtime/operator/issue receipt |
| [scoring_chain.operator.txt](scoring_chain.operator.txt) | Once-only sequential bridge scoring command/log/exit/runtime/operator/issue receipt |
| [seed0_completion_issue51.json](seed0_completion_issue51.json) | Authorization, progress or posted issue/monitor receipt |
| [seed0_completion_issue51.md](seed0_completion_issue51.md) | Authorization, progress or posted issue/monitor receipt |
| [seed0_graph_artifacts.json](seed0_graph_artifacts.json) | Downloaded graph file sizes and hashes |
| [seed0_prediction_validation.json](seed0_prediction_validation.json) | All 17 prediction shape/order/hash/settings checks |
| [seed0_runner_receipt.json](seed0_runner_receipt.json) | Unchanged runner receipt copied from the external output folder |
| [seed0_score.command.txt](seed0_score.command.txt) | Once-only sequential bridge scoring command/log/exit/runtime/operator/issue receipt |
| [seed0_score.exit](seed0_score.exit) | Once-only sequential bridge scoring command/log/exit/runtime/operator/issue receipt |
| [seed0_score.log](seed0_score.log) | Once-only sequential bridge scoring command/log/exit/runtime/operator/issue receipt |
| [seed0_score.runtime.json](seed0_score.runtime.json) | Once-only sequential bridge scoring command/log/exit/runtime/operator/issue receipt |
| [seed0_score_issue51.json](seed0_score_issue51.json) | Once-only sequential bridge scoring command/log/exit/runtime/operator/issue receipt |
| [seed0_score_issue51.md](seed0_score_issue51.md) | Once-only sequential bridge scoring command/log/exit/runtime/operator/issue receipt |
| [seed0_training.command.txt](seed0_training.command.txt) | Original sequential training command/log/exit/runtime/operator/final-state receipt |
| [seed0_training.exit](seed0_training.exit) | Original sequential training command/log/exit/runtime/operator/final-state receipt |
| [seed0_training.log](seed0_training.log) | Original sequential training command/log/exit/runtime/operator/final-state receipt |
| [seed0_training.runtime.json](seed0_training.runtime.json) | Original sequential training command/log/exit/runtime/operator/final-state receipt |
| [seed2_completion_issue51.json](seed2_completion_issue51.json) | Authorization, progress or posted issue/monitor receipt |
| [seed2_completion_issue51.md](seed2_completion_issue51.md) | Authorization, progress or posted issue/monitor receipt |
| [seed2_graph_artifacts.json](seed2_graph_artifacts.json) | Downloaded graph file sizes and hashes |
| [seed2_prediction_validation.json](seed2_prediction_validation.json) | All 17 prediction shape/order/hash/settings checks |
| [seed2_runner_receipt.json](seed2_runner_receipt.json) | Unchanged runner receipt copied from the external output folder |
| [seed2_score.command.txt](seed2_score.command.txt) | Once-only sequential bridge scoring command/log/exit/runtime/operator/issue receipt |
| [seed2_score.exit](seed2_score.exit) | Once-only sequential bridge scoring command/log/exit/runtime/operator/issue receipt |
| [seed2_score.log](seed2_score.log) | Once-only sequential bridge scoring command/log/exit/runtime/operator/issue receipt |
| [seed2_score.runtime.json](seed2_score.runtime.json) | Once-only sequential bridge scoring command/log/exit/runtime/operator/issue receipt |
| [seed2_score_issue51.json](seed2_score_issue51.json) | Once-only sequential bridge scoring command/log/exit/runtime/operator/issue receipt |
| [seed2_score_issue51.md](seed2_score_issue51.md) | Once-only sequential bridge scoring command/log/exit/runtime/operator/issue receipt |
| [seed2_slow_progress_issue51.json](seed2_slow_progress_issue51.json) | Authorization, progress or posted issue/monitor receipt |
| [seed2_slow_progress_issue51.md](seed2_slow_progress_issue51.md) | Authorization, progress or posted issue/monitor receipt |
| [seed2_training.command.txt](seed2_training.command.txt) | Original sequential training command/log/exit/runtime/operator/final-state receipt |
| [seed2_training.exit](seed2_training.exit) | Original sequential training command/log/exit/runtime/operator/final-state receipt |
| [seed2_training.log](seed2_training.log) | Original sequential training command/log/exit/runtime/operator/final-state receipt |
| [seed2_training.runtime.json](seed2_training.runtime.json) | Original sequential training command/log/exit/runtime/operator/final-state receipt |
| [seed3_graph_artifacts.json](seed3_graph_artifacts.json) | Downloaded graph file sizes and hashes |
| [seed3_prediction_validation.json](seed3_prediction_validation.json) | All 17 prediction shape/order/hash/settings checks |
| [seed3_runner_receipt.json](seed3_runner_receipt.json) | Unchanged runner receipt copied from the external output folder |
| [seed3_score.command.txt](seed3_score.command.txt) | Once-only sequential bridge scoring command/log/exit/runtime/operator/issue receipt |
| [seed3_score.exit](seed3_score.exit) | Once-only sequential bridge scoring command/log/exit/runtime/operator/issue receipt |
| [seed3_score.log](seed3_score.log) | Once-only sequential bridge scoring command/log/exit/runtime/operator/issue receipt |
| [seed3_score.runtime.json](seed3_score.runtime.json) | Once-only sequential bridge scoring command/log/exit/runtime/operator/issue receipt |
| [seed3_score_issue51.json](seed3_score_issue51.json) | Once-only sequential bridge scoring command/log/exit/runtime/operator/issue receipt |
| [seed3_score_issue51.md](seed3_score_issue51.md) | Once-only sequential bridge scoring command/log/exit/runtime/operator/issue receipt |
| [seed3_training.command.txt](seed3_training.command.txt) | Original sequential training command/log/exit/runtime/operator/final-state receipt |
| [seed3_training.exit](seed3_training.exit) | Original sequential training command/log/exit/runtime/operator/final-state receipt |
| [seed3_training.log](seed3_training.log) | Original sequential training command/log/exit/runtime/operator/final-state receipt |
| [seed3_training.runtime.json](seed3_training.runtime.json) | Original sequential training command/log/exit/runtime/operator/final-state receipt |
| [source_and_authority_review.json](source_and_authority_review.json) | Authorization, progress or posted issue/monitor receipt |
| [training_chain.exit](training_chain.exit) | Original sequential training command/log/exit/runtime/operator/final-state receipt |
| [training_chain.final.json](training_chain.final.json) | Original sequential training command/log/exit/runtime/operator/final-state receipt |
| [training_chain.live.json](training_chain.live.json) | Original sequential training command/log/exit/runtime/operator/final-state receipt |
| [training_chain.operator.txt](training_chain.operator.txt) | Original sequential training command/log/exit/runtime/operator/final-state receipt |
| [training_completion_and_prescore.json](training_completion_and_prescore.json) | Original sequential training command/log/exit/runtime/operator/final-state receipt |
| [training_completion_issue51.json](training_completion_issue51.json) | Original sequential training command/log/exit/runtime/operator/final-state receipt |
| [training_completion_issue51.md](training_completion_issue51.md) | Original sequential training command/log/exit/runtime/operator/final-state receipt |
| [updated_three_job_authority.json](updated_three_job_authority.json) | Authorization, progress or posted issue/monitor receipt |
| [updated_three_job_authority.md](updated_three_job_authority.md) | Authorization, progress or posted issue/monitor receipt |
