# Linear AE Adamson: artifact index

One deterministic default CPU run and one bridge invocation, 30 October 2026. Read [the result](../linear_ae_adamson.md) and [unchanged score JSON](../linear_ae_adamson.json). Raw predictions, work and inputs are outside Git.

The approved corrected export path and input SHA-256 are in [receipt.json](receipt.json). The original empty export is untouched. The first focused-test launcher failure is preserved alongside the successful single operator correction; no baseline or scoring retry occurred.

Every file in this directory is indexed below. The manifest pins every publication artifact except itself and the final publication audit, which are excluded to avoid circular hashes. The index and root result files are covered.

| File | Record |
|---|---|
| [README.md](README.md) | This every-file index |
| [artifact_manifest.json](artifact_manifest.json) | SHA-256 and byte count of publication artifacts; self and final audit explicitly excluded |
| [chain.exit](chain.exit) | Unchanged command, log, runtime, validation, provenance or issue record |
| [chain.final.json](chain.final.json) | Unchanged command, log, runtime, validation, provenance or issue record |
| [chain.live.json](chain.live.json) | Unchanged command, log, runtime, validation, provenance or issue record |
| [focused_tests.command.txt](focused_tests.command.txt) | Preserved first test launcher failure: pytest absent from runner environment |
| [focused_tests.exit](focused_tests.exit) | Preserved first test launcher failure: pytest absent from runner environment |
| [focused_tests.log](focused_tests.log) | Preserved first test launcher failure: pytest absent from runner environment |
| [focused_tests.runtime.json](focused_tests.runtime.json) | Preserved first test launcher failure: pytest absent from runner environment |
| [focused_tests_corrected.command.txt](focused_tests_corrected.command.txt) | Authorized corrected test launcher; eight tests passed |
| [focused_tests_corrected.exit](focused_tests_corrected.exit) | Authorized corrected test launcher; eight tests passed |
| [focused_tests_corrected.log](focused_tests_corrected.log) | Authorized corrected test launcher; eight tests passed |
| [focused_tests_corrected.runtime.json](focused_tests_corrected.runtime.json) | Authorized corrected test launcher; eight tests passed |
| [full_result_issue51.json](full_result_issue51.json) | Unchanged command, log, runtime, validation, provenance or issue record |
| [full_result_issue51.md](full_result_issue51.md) | Unchanged command, log, runtime, validation, provenance or issue record |
| [handoff_publication_check.json](handoff_publication_check.json) | Unchanged command, log, runtime, validation, provenance or issue record |
| [input_authority.json](input_authority.json) | Unchanged command, log, runtime, validation, provenance or issue record |
| [input_confirmed_issue51.json](input_confirmed_issue51.json) | Unchanged command, log, runtime, validation, provenance or issue record |
| [input_confirmed_issue51.md](input_confirmed_issue51.md) | Unchanged command, log, runtime, validation, provenance or issue record |
| [input_preflight_issue51.json](input_preflight_issue51.json) | Unchanged command, log, runtime, validation, provenance or issue record |
| [input_preflight_issue51.md](input_preflight_issue51.md) | Unchanged command, log, runtime, validation, provenance or issue record |
| [postrun_ledger.json](postrun_ledger.json) | Unchanged command, log, runtime, validation, provenance or issue record |
| [prediction_validation.json](prediction_validation.json) | Unchanged command, log, runtime, validation, provenance or issue record |
| [prescore_protocol.json](prescore_protocol.json) | Unchanged command, log, runtime, validation, provenance or issue record |
| [publication_audit.json](publication_audit.json) | Final pre-push scope, raw staged bytes, hash, JSON, secret and documentation checks |
| [reading_audit.json](reading_audit.json) | Unchanged command, log, runtime, validation, provenance or issue record |
| [ready_issue51.json](ready_issue51.json) | Unchanged command, log, runtime, validation, provenance or issue record |
| [ready_issue51.md](ready_issue51.md) | Unchanged command, log, runtime, validation, provenance or issue record |
| [receipt.json](receipt.json) | Operator receipt with approved export path, input SHA-256 and unchanged nested runner receipt |
| [run.command.txt](run.command.txt) | Unchanged command, log, runtime, validation, provenance or issue record |
| [run.exit](run.exit) | Unchanged command, log, runtime, validation, provenance or issue record |
| [run.log](run.log) | Unchanged command, log, runtime, validation, provenance or issue record |
| [run.runtime.json](run.runtime.json) | Unchanged command, log, runtime, validation, provenance or issue record |
| [run_once.operator.txt](run_once.operator.txt) | Unchanged command, log, runtime, validation, provenance or issue record |
| [runner_receipt.raw.json](runner_receipt.raw.json) | Unchanged original runner receipt |
| [score.command.txt](score.command.txt) | Unchanged command, log, runtime, validation, provenance or issue record |
| [score.exit](score.exit) | Unchanged command, log, runtime, validation, provenance or issue record |
| [score.log](score.log) | Unchanged command, log, runtime, validation, provenance or issue record |
| [score.raw.json](score.raw.json) | Unchanged bridge report before the provenance appendix |
| [score.raw.md](score.raw.md) | Unchanged bridge report before the provenance appendix |
| [score.runtime.json](score.runtime.json) | Unchanged command, log, runtime, validation, provenance or issue record |
