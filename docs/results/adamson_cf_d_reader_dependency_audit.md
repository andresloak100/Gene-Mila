# Block D reader dependency provenance

PR81 head predates discovery integration. The scientific tool files are byte-identical to the original reading checkout. Among audited fitting/data/oracle modules only pipeline.run differs, adding optional derivability diagnostics after worker model persistence; the readers do not call pipeline.run. They use unchanged smoke/feature_blocks/CV helpers and fit in feature_audit. Lab stored-artifact prediction, feature context, registry, sandbox, guard, bundle, oracle and evaluator are byte-identical. Integration was merged only after all scientific calls; no score was repeated.

The full suite started on the resolved staged merge tree before the merge commit was recorded. write-tree and committed tree are identical; no executable file changed during tests.

Exact module hashes and AST comparisons are in the JSON twin. No retrospective scientific rerun occurred.

Independent source-only audit confirms byte-identical six tools and supporting feature/built-in/sandbox/guard/spec/database/config/gateway/isolation/bundle/oracle modules, identical 11 pipeline helpers, discovery-only config differences, and no pipeline.run reachability on these reader paths.

Static source reachability/identity audit, not runtime tracing or proof of identical historical third-party libraries. Captured reader uses the same project Python path as original D commands.
