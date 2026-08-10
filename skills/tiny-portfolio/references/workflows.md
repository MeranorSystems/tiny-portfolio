# Tiny Portfolio Workflows Reference

Phase 4 is read / analyze / explain over an existing Tiny Portfolio record.

It does not yet write authoritative portfolio history.

## Validate a record

When the user asks whether a record is valid:

1. identify the record file;
2. run `scripts/validate_portfolio.py`;
3. report `valid` when both schema and structural-semantic validation pass;
4. if invalid, explain schema and semantic errors;
5. do not silently repair the record.

Do not continue into accounting or status when validation fails.

## Accounting analysis

When the user asks for Tiny Portfolio accounting:

1. identify the record;
2. run `scripts/tiny_portfolio_runtime.py <record-path>`;
3. use the returned accounting object;
4. explain contribution-adjusted dollar performance using `accounting.md`;
5. mention unavailable/stale conditions when relevant.

Do not require rule evaluation for a pure accounting question.

## Current status

When the user asks for HOLD / WAIT / REVIEW:

1. identify and validate the record;
2. obtain a reliable current timezone-aware timestamp from the host/runtime;
3. run `scripts/tiny_portfolio_runtime.py <record-path> --evaluation-at "<timestamp>"`;
4. report the returned `current_status`;
5. explain the relevant rule outcomes/reason codes;
6. keep the result framed as process status, not trade advice.

If a reliable current time is not available, ask for the relevant date/time instead of inventing one.

## Historical status

When the user asks what status applied at a historical time:

1. use the user's supplied historical timezone-aware time;
2. run the same deterministic runtime with that time;
3. explain that the current authoritative record includes its corrections;
4. report the deterministic result.

Do not guess an unspecified historical time.

## Full briefing

When the user asks for a full Tiny Portfolio briefing:

1. validate;
2. run deterministic accounting;
3. run deterministic rules/status with explicit evaluation time;
4. summarize selected confirmed holdings from the record;
5. identify next milestone/distance only when derivable from confirmed facts;
6. include relevant rule/review evidence;
7. follow `briefing.md`.

Do not pad unknown fields with estimates.

## Explain one rule or result

If the user asks "why WAIT?", "why REVIEW?", or about one rule:

- focus on that rule/result;
- use deterministic evidence first;
- load `classification.md` as needed;
- avoid sending a full briefing unless requested.

## Explain accounting semantics

For questions like:
- "Did my contribution count as profit?"
- "Why isn't this withdrawal a loss?"
- "How are rewards treated?"
- "What did the correction do?"

Use the accepted accounting semantics from `accounting.md` and, when the answer depends on the user's record, run the deterministic runtime.

## Explain the data format

For schema, event, snapshot, correction, or milestone questions, use `data-model.md`.

If the question is conceptual and does not require portfolio state, a record is not required.

## Invalid or incomplete record

If the record fails validation:
- stop;
- report the errors;
- distinguish schema errors from semantic errors when useful;
- do not infer intended values;
- do not calculate on a partially repaired mental copy.

A later write workflow may propose corrections, but Phase 4 does not persist them.

## No record supplied

If a user asks for a stateful Tiny Portfolio result without a record:
- say the record is required;
- ask them to provide `tiny-portfolio.json` or equivalent record content;
- do not invent a sample portfolio and answer as though it were theirs.

You may explain Tiny Portfolio concepts without a record.

## Guided Check-In — deferred

New-user setup, proposing ledger/snapshot changes, user confirmation, and authoritative record persistence belong to Phase 5.

Phase 4 must not claim those write workflows are implemented.

## Screenshot Assist / Hybrid — deferred

Screenshot extraction, proposed screenshot values, confirmation, and Hybrid follow-up belong to Phase 6.

If a screenshot appears during Phase 4:
- do not silently treat extracted values as confirmed history;
- do not write them into the authoritative record;
- explain that screenshot-assisted updating is outside the current Phase 4 workflow.

## No external market workflow

Tiny Portfolio v0.1 does not fetch live prices or use a live market feed.

Do not invent current market prices to fill missing portfolio values.

Generic market or investing requests without Tiny Portfolio context belong outside this skill.
