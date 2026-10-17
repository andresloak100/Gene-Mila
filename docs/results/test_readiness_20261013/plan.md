# Prospective two-review block — Claim #22

Fixed before requests. User authorization on 13 October 2026: “go test”, then “use the deepseek agents”.
Scope: prepare an untouched evaluation; agents critique metadata/design only. No gene-expression/model
score experiment is part of this block. Original main checkout, STOP, protected code/data and historic
runs remain untouched. No account or permission changes. A separate evaluator is still missing.

- Provider: DeepSeek; requested model `deepseek-v4-pro`; two independent text-review roles run sequentially.
- Roles: cohort/feature eligibility reviewer, and frozen-test/access-boundary reviewer.
- Inputs: same fixed public-metadata facts plus role-specific questions; no candidate responses, efficacy,
  DE rankings, stored performance scores, raw expression arrays, credentials or private/split files.
- Maximum two calls, 2,000 output tokens each, thinking disabled, no retries/fallback or planner.
- Existing LLMGateway enforces worker $0.25 cap and cumulative DeepSeek $48 cap against the original shared
  ledger. Planner cap is $0.001 solely to avoid the gateway's zero-cap auto-scaling; no planner calls occur.
- Existing repository peak prices remain unchanged: input-cache-hit $0.044, cache-miss $1.32 and output
  $3.96 per million tokens. Verified against https://api-docs.deepseek.com/quick_start/pricing/ on 13 Oct.
  These are ledger estimates, not measured cash charges. Historical entries are not repriced.
- Before calls verify the original ledger exists, remaining cap covers $0.251, no lab process is running,
  prompt SHA256s, and summed worst-case input/output reservations <=$0.25. Estimate input by UTF-8 bytes
  plus 1,024 tokens of message overhead. No secrets enter prompts, config, saved errors or source files.
- Request timeout 120 seconds; controller alarm 300 seconds; do not begin a second call with insufficient
  time. Stop on missing credential, error, empty/truncated output, unknown source facts or budget refusal.
  No automatic extra request. An API failure can leave uncertain provider billing; record it explicitly.
- Preserve all outputs and usage in an exclusive ignored run directory with config.json and summary.json;
  publish data-free copies, exact driver/prompts, hashes, review limitations and accepted/rejected findings.
  Reviewer opinions are not new evidence or empirical test scores.

This new user-requested text-only review is separate from stopped lab model-search runs; STOP is not
removed or bypassed by any run_research/controller execution. No lab controller is invoked. Future
model-search or protected-code work needs its own plan and authorization. Actual scoring needs the
condition manifest, compatible inputs, prospective metric/baseline/uncertainty choices, and verified
isolation before candidate expression is acquired. Do not silently change the frozen B1 predictor.
