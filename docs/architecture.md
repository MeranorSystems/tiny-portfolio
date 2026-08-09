# Tiny Portfolio Architecture

**Status:** Locked baseline for the manual v0.1 build  
**Baseline date:** 2026-08-09  
**Owner:** Meranor Systems  
**Project class:** Meranor Labs

## Product definition

Tiny Portfolio by Meranor is a public ChatGPT plugin that helps users maintain a small manually tracked investment and crypto portfolio through a calm, rules-based workflow.

The product loop is:

> Set rules → Record what happened → Calculate accurately → Evaluate the user's rules → Explain the current status → Preserve the record.

Tiny Portfolio is not a brokerage, exchange client, trading bot, live market terminal, or market-prediction service.

## v0.1 architecture

Version 0.1 is a **skills-only ChatGPT plugin** built around one focused Tiny Portfolio skill.

The current official OpenAI plugin model, re-verified on 2026-08-09, supports this shape directly. The required plugin entry point is `.codex-plugin/plugin.json`; plugins may package skills under `skills/`; and skills may include `references/`, `scripts/`, and `assets/` for detailed documentation, deterministic computation, and workflow resources.

### v0.1 components

- one Tiny Portfolio skill;
- portable user-controlled `tiny-portfolio.json` records;
- deterministic Python validation, accounting, and rule evaluation;
- Guided Check-In;
- Screenshot Assist;
- Hybrid Check-In;
- HOLD, WAIT, and REVIEW statuses;
- explicit confirmation before screenshot-derived values become confirmed history.

### Explicit v0.1 exclusions

Do not add:

- an MCP server;
- hosted backend infrastructure;
- a database;
- user accounts;
- Google authentication;
- exchange or brokerage authentication;
- live market-data feeds;
- automated trading;
- automatic BUY or SELL classifications.

## Portable portfolio record

The authoritative portfolio state is a user-controlled file named `tiny-portfolio.json`.

Schema version begins at `1.0`.

Conceptual top-level areas:

- `schema_version`
- `portfolio`
- `rules`
- `milestones`
- `ledger`
- `snapshots`
- `metadata`

The portfolio format must not require brokerage/exchange account identifiers, private keys, API secrets, seed phrases, passwords, authentication codes, SSNs, or full financial-account numbers.

## Ledger model

The ledger is append-oriented.

Initial event concepts:

- contribution
- withdrawal
- trade
- fee
- reward
- correction / adjustment
- note

Reward subtypes may include staking, dividend, interest, and other.

Confirmed history must never be silently overwritten. Corrections remain explicit and auditable.

## Accounting model

Primary v0.1 performance is contribution-adjusted **dollar** performance:

```text
Adjusted P/L = Current confirmed portfolio value
             + Total withdrawals
             - Total outside contributions
```

Opening portfolio capital is treated as contributed capital.

Rules:

- contributions are not investment profit;
- withdrawals are not investment losses;
- trades and conversions move value within the portfolio and do not change outside contributed capital;
- fees reduce portfolio performance but must not be double-counted when already reflected in the confirmed portfolio value;
- rewards, dividends, staking income, and interest are portfolio-generated returns but must not be double-counted when already reflected in confirmed value;
- missing information remains unknown;
- money calculations use `Decimal`-safe arithmetic instead of binary floating point.

Version 0.1 intentionally does not publish percentage-return calculations. A documented time-aware methodology may be added later.

## Confirmed snapshots

A confirmed snapshot records point-in-time portfolio state.

Conceptual fields:

- timestamp;
- total portfolio value;
- holdings;
- source;
- confirmation state.

A holding may include asset name, symbol, asset type, quantity when known, and value when known.

Generic v0.1 asset types:

- crypto
- equity
- fund
- cash
- other

No live market-price service is required.

## Update workflows

### Guided Check-In

The user answers a small set of structured questions about current value and relevant activity since the prior confirmed state.

### Screenshot Assist

The user uploads a selected screenshot. Tiny Portfolio extracts visible portfolio information, labels uncertainty, and presents proposed values for confirmation. Screenshot-derived values cannot become confirmed history without explicit user confirmation.

### Hybrid Check-In

Tiny Portfolio starts with a screenshot and then asks only for accounting context that the screenshot cannot establish, such as contributions, withdrawals, trades, fees, rewards, or missing holdings information.

Raw screenshots are not embedded into `tiny-portfolio.json`.

## Rule model

Rules are divided into two categories.

### Machine-evaluable rules

The initial set should remain intentionally small and explicit:

- maximum contribution per period;
- minimum days between contributions;
- portfolio-value review threshold;
- milestone review;
- scheduled review date.

### User guidance notes

Free-form guidance may be displayed and discussed, but Tiny Portfolio must not pretend arbitrary prose is deterministically enforced by Python.

## Status model

Tiny Portfolio reports **Current Status**, not a trading call.

### HOLD

No confirmed user-defined review condition is active and required information is available.

### WAIT

Required information is missing or ambiguous, or a time/limit rule means the user's own rules do not permit the contemplated action yet.

### REVIEW

One or more user-defined review conditions have been reached and deserve the user's attention.

`REVIEW` is not `BUY` or `SELL`. Version 0.1 must never output `BUY` or `SELL` as a portfolio status.

## Standard briefing

A routine Tiny Portfolio briefing should include:

- Current Status;
- total confirmed portfolio value;
- net contributed capital;
- contribution-adjusted dollar P/L;
- holdings summary;
- next milestone and distance;
- contribution/rule status;
- triggered review conditions;
- known activity such as rewards or fees when available;
- last confirmed timestamp;
- a concise explanation of why the current status applies.

## Privacy and safety contract

Tiny Portfolio must never request private keys, seed phrases, brokerage/exchange passwords, authentication codes, API secrets, SSNs, or full financial-account numbers.

Screenshot workflows should encourage users to crop unrelated private information when practical.

An accurate v0.1 public claim is:

> Tiny Portfolio operates without a Tiny Portfolio server, user account, exchange connection, or hosted portfolio database.

Do not claim that information never leaves the user's device, because Tiny Portfolio operates within ChatGPT.

Do not use guaranteed-return language, urgency, fear, hype, or get-rich framing.

## OpenAI packaging baseline

Official OpenAI documentation verified on 2026-08-09 establishes the current baseline used by this project:

- `.codex-plugin/plugin.json` is the required plugin entry point;
- skills live under `skills/` at the plugin root;
- skills may include `references/`, `scripts/`, and `assets/`;
- `scripts/` is appropriate for deterministic computation and file processing;
- skills-only plugins are a supported public submission type;
- local plugin installation/testing is supported through the ChatGPT desktop app;
- public submission requires at least five positive and three negative test cases.

This document is the authoritative v0.1 public architecture unless intentionally superseded by a documented project decision.
