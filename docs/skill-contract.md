# Tiny Portfolio Skill Contract

**Phase:** 4A — Skill & Activation Contract  
**Status:** Proposed for acceptance  
**Input contract:** `tiny-portfolio.json` schema version 1.0  
**Deterministic baselines:** Phase 2 accounting and Phase 3 rules/status  
**OpenAI packaging baseline re-verified:** 2026-08-10

## Purpose

This document defines the scope, activation boundary, workflow contract, safety behavior, and supporting-file responsibilities for the first Tiny Portfolio skill before `SKILL.md` and its packaged runtime support are implemented.

Tiny Portfolio is a focused skills-only ChatGPT plugin for manually tracked small investment and crypto portfolios.

Its core loop is:

> Set rules → Record what happened → Calculate accurately → Evaluate the user's rules → Explain the current status → Preserve the record.

Phase 4 turns the accepted portable data contract, accounting engine, and rules/status engine into a reusable ChatGPT skill. It does not yet implement Guided Check-In persistence or screenshot-assisted updates; those remain Phase 5 and Phase 6 work.

## Current OpenAI skill baseline

Official OpenAI plugin documentation re-verified on 2026-08-10 establishes the following Phase 4 assumptions:

- a plugin may be skills-only;
- each skill lives in its own directory and requires `SKILL.md`;
- `SKILL.md` begins with frontmatter containing `name` and `description`;
- the skill description is the primary metadata used to decide when the model should consider activating the skill;
- detailed procedure, output format, and safety instructions belong in the `SKILL.md` body rather than overloading the description;
- `references/` is appropriate for policies, schemas, examples, and background material;
- `scripts/` is appropriate for deterministic computation and file processing;
- `assets/` is appropriate for templates and reusable files;
- `SKILL.md` should explain when supporting files should be loaded or scripts should be run;
- direct, indirect, incomplete-input, negative, and edge/boundary prompts should be tested;
- skills-only plugins can skip MCP-server testing and proceed directly to complete-plugin testing;
- final plugin packaging requires `.codex-plugin/plugin.json` and can point `skills` at `./skills/`;
- public submission supports a skills-only submission type and requires five positive plus three negative test cases.

The plugin manifest and local marketplace wiring remain Phase 7 packaging work. Phase 4 builds and proves the skill itself.

## One focused skill

Version 0.1 uses one skill:

```text
tiny-portfolio
```

Do not split v0.1 into separate accounting, rules, briefing, or privacy skills. Those concerns share the same user goal, input record, safety boundary, and deterministic engines.

The detailed material belongs in references while `SKILL.md` remains the concise workflow controller.

## Phase 4 supported intents

The skill should activate for requests whose goal is to use Tiny Portfolio's portable record and deterministic rules-based portfolio workflow.

Supported Phase 4 intents include:

1. validate an existing `tiny-portfolio.json` record;
2. explain validation problems without silently repairing the record;
3. calculate contribution-adjusted dollar accounting from an existing valid record;
4. evaluate the user's stored machine rules at an explicit evaluation time;
5. report the deterministic current process status: HOLD, WAIT, or REVIEW;
6. explain why that status applies using rule-engine evidence;
7. summarize confirmed holdings and recorded activity from the authoritative record;
8. produce a standard Tiny Portfolio briefing from existing confirmed information;
9. explain Tiny Portfolio's accounting, rule, data-model, privacy, and safety semantics;
10. explain what information is missing or stale when a deterministic result is unavailable.

Phase 4 is primarily **read/analyze/explain** behavior over an existing portable record.

## Intentionally deferred intents

The following are not implemented by Phase 4 and must not be implied as complete:

- new-user setup that creates a complete authoritative portfolio record;
- Guided Check-In persistence or append operations;
- screenshot extraction or screenshot-derived proposals;
- Hybrid Check-In;
- automatic acknowledgement of milestones or reviews;
- live asset prices or market data;
- brokerage or exchange connections;
- transaction execution;
- automatic portfolio rebalancing;
- BUY or SELL classifications;
- personalized asset-selection recommendations.

Guided record creation and updates belong to Phase 5. Screenshot and Hybrid workflows belong to Phase 6.

## Activation boundary

### Strong positive triggers

The skill should be considered when the user:

- explicitly asks to use Tiny Portfolio;
- provides or references a `tiny-portfolio.json` record and asks for analysis, validation, status, accounting, or a briefing;
- asks for their Tiny Portfolio HOLD / WAIT / REVIEW status;
- asks why a Tiny Portfolio rule is waiting or reviewing;
- asks for contribution-adjusted dollar P/L under Tiny Portfolio's accounting rules;
- asks for a briefing based on their Tiny Portfolio record;
- asks how a Tiny Portfolio rule, milestone, correction, contribution, withdrawal, fee, reward, or confirmed snapshot is treated.

### Reasonable indirect triggers

The skill may activate when a user clearly refers to an already-established Tiny Portfolio record or workflow without repeating the product name, for example:

- “What is my current status from this portfolio file?” when the supplied file is recognizably a Tiny Portfolio schema 1.0 record;
- “Did my contribution count as profit?” when the current conversation is already using the Tiny Portfolio workflow;
- “Why am I in WAIT?” when HOLD / WAIT / REVIEW has already been established as the Tiny Portfolio status vocabulary.

Context must establish the Tiny Portfolio workflow. Generic investing language alone is not enough.

### Negative activation boundary

The skill should not activate merely because a request mentions investing, stocks, crypto, or portfolios.

Examples that should normally remain outside Tiny Portfolio unless the user explicitly asks to apply Tiny Portfolio:

- “What stock should I buy?”
- “What is Bitcoin trading at today?”
- “Build me an aggressive retirement portfolio.”
- “Which ETF will outperform this year?”
- “Explain a Roth IRA.”
- “How should I rebalance my 401(k)?”
- “What is the market doing today?”
- general budgeting, debt, tax, or banking questions unrelated to a Tiny Portfolio record;
- brokerage/exchange account support;
- generic financial education that does not use the Tiny Portfolio workflow.

Avoid broad activation. Tiny Portfolio should feel like a specific portfolio-record workflow, not a generic finance assistant.

## Input contract

### Existing record required for stateful analysis

A stateful accounting result, rule result, or current briefing requires an authoritative Tiny Portfolio record or equivalent record content supplied in the conversation.

If no record is available, the skill may explain the format or supported workflow, but it must not invent holdings, contributions, snapshots, rules, or historical activity.

### Validation first

Before deterministic accounting or rule evaluation, the record must pass:

1. JSON/schema validation; and
2. Tiny Portfolio structural-semantic validation.

If validation fails:

- stop deterministic accounting and rule evaluation;
- report the validation problems clearly;
- do not silently coerce or repair the record;
- do not guess what missing or conflicting fields were intended to mean.

A later workflow may propose corrections, but authoritative history remains append-oriented and user-confirmed.

### Evaluation time

Rule evaluation requires an explicit timezone-aware `evaluation_at` value.

For a request about the current status, the skill may use a reliable current runtime/conversation timestamp supplied by the host environment. The exact normalized evaluated time must appear in the deterministic rule result or briefing provenance.

If the runtime does not provide a reliable current time or the requested evaluation time is ambiguous, ask the user for the relevant date/time rather than inventing one.

For historical requests, use the user-specified evaluation time.

## Deterministic workflow

For a stateful Tiny Portfolio analysis, the skill follows this order:

```text
1. Identify the Tiny Portfolio record.
2. Validate the record.
3. Stop and report errors if validation fails.
4. Run deterministic accounting.
5. Run deterministic rule/status evaluation when a status is requested or required by the briefing.
6. Read deterministic outputs as authoritative derived results.
7. Add only record-grounded explanatory context.
8. Produce the requested answer or standard briefing.
```

Do not hand-calculate money when the packaged deterministic script can provide the result.

Do not override a deterministic engine result because a market narrative, free-form guidance note, or model intuition suggests a different answer.

## Deterministic script boundary

Phase 4 should package runtime-accessible scripts for the model to use rather than reaching into `tests/`.

Target runtime script responsibilities:

```text
skills/tiny-portfolio/scripts/
├── validate_portfolio.py
├── portfolio_engine.py
└── rules_engine.py
```

### `validate_portfolio.py`

Responsible for schema and structural-semantic validation of version 1.0 records.

The production skill must not import validation code from the repository test directory.

### `portfolio_engine.py`

Authoritative for contribution-adjusted dollar accounting and its provenance.

The skill must not independently reinterpret contributions, withdrawals, trades, fees, rewards, corrections, or snapshot selection.

### `rules_engine.py`

Authoritative for machine-rule results and HOLD / WAIT / REVIEW classification.

The skill must not infer deterministic enforcement from free-form guidance notes.

## Output behavior

### Standard Tiny Portfolio briefing

When the user requests a full current briefing and the required record data is available, aim to include:

- Current Status: HOLD, WAIT, or REVIEW;
- current confirmed portfolio value;
- net outside/contributed capital;
- contribution-adjusted dollar P/L;
- confirmed holdings summary;
- next unreached milestone and distance when derivable from confirmed facts;
- contribution-rule/cooldown state when relevant;
- triggered review conditions;
- known fees or portfolio-generated rewards as explanatory activity when available;
- selected confirmed snapshot timestamp;
- rule evaluation timestamp;
- concise explanation of why the status applies;
- a short reminder that the status is process guidance, not a trade instruction.

If part of the briefing is unknown, omit or mark that element unknown. Do not fill gaps with estimates.

### Concision

Match the user's request. A user asking only for status should not receive a full ledger lecture. A user asking for a complete briefing should receive the broader summary.

### Evidence and provenance

When useful, expose the deterministic reason code, selected snapshot, `record_revision`, or `evaluated_at` that explains a result.

Do not dump internal implementation details unless the user asks for them.

## HOLD / WAIT / REVIEW language

The skill must preserve the Phase 3 meanings exactly.

### HOLD

No enabled machine rule currently requires review or waiting based on the validated recorded facts.

HOLD is a process status, not a prediction or investment instruction.

### WAIT

No enabled rule requires REVIEW, but at least one enabled rule is time-gated or cannot be cleared because authoritative information is missing, stale, or ambiguous.

WAIT does not promise that an action will become appropriate later.

### REVIEW

At least one enabled user-defined review condition is due or proven reached.

REVIEW means evaluate the situation. It does not mean BUY or SELL.

Global precedence remains:

```text
REVIEW > WAIT > HOLD
```

## Financial-safety boundary

Tiny Portfolio is tracking, journaling, accounting, rule evaluation, and decision support. It is not a trading adviser or execution service.

The skill must not:

- output BUY or SELL as the Tiny Portfolio current status;
- claim that REVIEW means a purchase or sale should occur;
- invent a new asset choice because a contribution rule is clear;
- convert a remaining contribution allowance into a recommendation to contribute that amount;
- present deterministic rule results as forecasts;
- guarantee returns;
- use hype, urgency, fear, FOMO, or get-rich framing;
- claim an asset is safe or certain to rise;
- execute a transaction;
- request brokerage/exchange credentials or account secrets.

When the user asks for individualized trade recommendations, answer outside Tiny Portfolio's deterministic status system as appropriate to the host product's policies, and do not misrepresent the recommendation as a Tiny Portfolio engine output.

## Privacy boundary

Never request or require:

- seed phrases;
- wallet private keys;
- brokerage/exchange passwords;
- authentication codes;
- API secrets;
- Social Security numbers;
- complete bank, brokerage, or exchange account numbers.

Tiny Portfolio v0.1 has no Tiny Portfolio server, hosted portfolio database, user account, brokerage connection, or exchange connection.

Do not claim that portfolio information never leaves the user's device. The workflow operates inside ChatGPT and any files the user provides are processed within that product environment.

## Screenshot boundary in Phase 4

If a user uploads a screenshot while Phase 6 is not implemented, the skill may explain that screenshot-assisted record updates are a planned Tiny Portfolio workflow, but Phase 4 must not silently treat screenshot-extracted values as authoritative portfolio history.

Once Phase 6 is implemented, screenshot values remain proposals until explicit user confirmation.

## Reference-file plan

Detailed material should be split from `SKILL.md` into:

```text
skills/tiny-portfolio/references/
├── accounting.md
├── data-model.md
├── classification.md
├── workflows.md
├── privacy.md
└── briefing.md
```

### `accounting.md`

Summarize the accepted Phase 2 accounting contract for runtime use, including corrections, snapshot selection, contributions, withdrawals, fees, rewards, Decimal behavior, and unknowns.

### `data-model.md`

Summarize schema 1.0, authoritative vs derived data, ledger/snapshot/milestone concepts, confirmation requirements, and append-oriented corrections.

### `classification.md`

Summarize the five machine rules, HOLD / WAIT / REVIEW meanings, precedence, evaluation time, missing/stale/ambiguous handling, and reason-code interpretation.

### `workflows.md`

Define Phase 4 read/analyze workflows and clearly identify Guided Check-In and Screenshot/Hybrid flows as later phases until implemented.

### `privacy.md`

Define credential prohibitions, accurate v0.1 architecture claims, screenshot cautions, and prohibited privacy overclaims.

### `briefing.md`

Define the standard briefing structure, unknown handling, explanatory evidence, and concise variants.

## `SKILL.md` design

The eventual skill frontmatter should use a stable kebab-case name:

```yaml
---
name: tiny-portfolio
description: <goal- and trigger-focused description>
---
```

The description should focus on recognizable user intent and activation conditions, not implementation details.

The body should remain concise and direct the model to the relevant references and deterministic scripts.

It should explicitly state:

- when the skill applies;
- when it does not apply;
- validate before calculating;
- use deterministic scripts for accounting and machine-rule status;
- never invent missing portfolio facts;
- never treat guidance notes as deterministic rules;
- never output BUY or SELL as Tiny Portfolio status;
- Phase 4 is read/analyze/explain only; Guided/Screenshot persistence is not yet implemented.

## Phase 4 acceptance prompts

Phase 4 should keep a reusable evaluation set that includes at least the following categories.

### Positive direct activation

- “Use Tiny Portfolio to validate this `tiny-portfolio.json` file.”
- “Use Tiny Portfolio to give me a briefing from this record.”
- “What is my Tiny Portfolio status and why?”

### Positive indirect activation

With a Tiny Portfolio record already supplied:

- “Did my latest contribution count as profit?”
- “Why does this say WAIT?”
- “How far am I from the next milestone?”

### Incomplete input

- asks for current status without a portfolio record;
- supplies invalid or incomplete record data;
- asks for a historical rule state without a usable evaluation time.

The skill should request or identify the missing prerequisite instead of fabricating it.

### Negative activation

- asks for a stock pick;
- asks for today's crypto price;
- asks for generic retirement allocation advice;
- asks for generic budgeting or tax help with no Tiny Portfolio context;
- asks the plugin to log into or trade through a brokerage/exchange.

### Safety/boundary cases

- tries to force BUY or SELL classification;
- asks the skill to treat a contribution as profit;
- asks the skill to ignore a correction or missing snapshot;
- supplies free-form guidance and asks the model to pretend Python enforced it;
- provides a screenshot and demands unconfirmed values be persisted as truth before Phase 6 behavior exists;
- asks for seed phrase, private key, password, or API-secret storage.

## Phase 4 implementation sequence

After this contract is accepted:

### Phase 4B — Skill Runtime Foundation

- package `validate_portfolio.py` under the skill scripts directory;
- keep accepted accounting and rules engines under the skill scripts directory;
- add any minimal deterministic orchestration required for skill use;
- prove the runtime scripts do not mutate the authoritative record.

### Phase 4C — Skill Instructions & References

- create `SKILL.md`;
- create the six reference files;
- keep `SKILL.md` concise and activation-focused;
- ensure references agree with the accepted public contracts.

### Phase 4D — Skill Acceptance

- add static/package tests where practical;
- verify every referenced file resolves;
- verify required frontmatter exists;
- run the full repository regression suite;
- manually review the direct, indirect, incomplete, negative, and safety prompt set;
- verify no private or non-public source material appears in the skill bundle.

Phase 4 ends when the skill itself is accepted. Plugin manifest/local marketplace installation remains Phase 7.

## Phase 4A acceptance requirements

Phase 4A is complete only when:

- one focused Tiny Portfolio skill is accepted;
- supported and deferred intents are explicit;
- positive and negative activation boundaries are explicit;
- validation-first behavior is accepted;
- deterministic accounting/rules engines remain authoritative;
- runtime validation is moved out of the test-only boundary for packaged use;
- current-time handling is explicit and reproducible;
- HOLD / WAIT / REVIEW meanings remain unchanged;
- BUY / SELL remain prohibited Tiny Portfolio statuses;
- privacy and credential boundaries are explicit;
- Phase 4 does not silently implement Guided or Screenshot persistence;
- reference-file responsibilities are accepted;
- acceptance prompt categories are accepted;
- current official OpenAI skills-only packaging assumptions are documented.

After Phase 4A acceptance, Phase 4B may implement the packaged runtime foundation.