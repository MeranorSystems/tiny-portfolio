# Tiny Portfolio Manual Build Roadmap

**Baseline:** 2026-08-09
**Build mode:** Manual, phase-gated development
**Current phase:** Phase 3A — Rules & Status Contract
**Development branch:** `feat/rules-status-engine`
**Accepted baseline:** Phase 2 promoted to `main` at `0c32e01`

Tiny Portfolio is built in small, reviewable phases. A phase advances only after its acceptance criteria are checked and the current work is reviewed.

## Phase 0 — Public Reset & Foundation

Create a clean public repository foundation for the manual build.

- create the fresh manual-development branch;
- normalize line endings with `.gitattributes`;
- replace broken README WebP references with approved PNG assets;
- place approved public branding under `assets/`;
- publish the locked architecture;
- establish the phase-based build plan;
- create the plugin directory skeleton without implementing business logic;
- confirm `.gitignore` protects user portfolio files and private data;
- record the OpenAI packaging baseline verified on 2026-08-09;
- verify the branch contains no personal financial data.

**Exit:** accepted and promoted to `main`; the repository renders correctly, documents the current architecture, contains no production accounting implementation, and is ready for the data contract.

## Phase 1 — Portable Data Contract

Define `tiny-portfolio.json` before writing accounting logic.

- schema version 1.0;
- portfolio, rules, milestones, ledger, snapshots, and metadata;
- append-oriented event structure;
- confirmation state for screenshot-derived proposals;
- JSON Schema;
- fictional example portfolio;
- invalid validation fixtures;
- structural validation.

**Exit:** accepted and promoted to `main` at `a522dd5`; valid examples pass, invalid examples fail clearly, and no real portfolio data is used.

## Phase 2 — Deterministic Accounting Engine

Implement contribution-adjusted dollar accounting with `Decimal`-safe arithmetic.

### Phase 2A — Accounting Contract

Accepted accounting behavior includes:

- correction-aware effective-ledger behavior;
- confirmed-snapshot selection by portfolio-state time;
- accounting as-of boundaries;
- outside contributions and withdrawals;
- trade neutrality;
- fee/reward explanatory totals without double counting;
- contribution-adjusted dollar P/L;
- post-snapshot activity signaling;
- missing/ambiguous value handling;
- exact Decimal arithmetic and deterministic serialization;
- portable-record revision provenance.

**Status:** Complete.

### Phase 2B — Accounting Engine

`portfolio_engine.py` implements the accepted accounting contract, including current confirmed value, contributed capital, withdrawals, trade neutrality, fee/reward explanation, contribution-adjusted P/L, correction-aware history, post-snapshot freshness, missing-data handling, and deterministic output.

**Status:** Complete.

### Phase 2C — Accounting Tests & Acceptance

Accounting tests cover contribution-not-profit, withdrawal-not-loss, trade neutrality, fee/reward non-double-counting, corrections, Decimal exactness, timestamp offsets, snapshot ordering, backfilled events, stale-snapshot behavior, source-record non-mutation, deterministic repeatability, and unavailable-result cases.

**Exit:** accepted and promoted to `main` at `0c32e01`; 35 total repository tests pass on the promoted baseline.

## Phase 3 — Rules + HOLD / WAIT / REVIEW

Implement the deterministic user-rule and current-status system.

### Phase 3A — Rules & Status Contract

Define and accept rule evaluation semantics before implementation.

The five version 0.1 machine-rule types are:

- `max_contribution_per_period`;
- `minimum_days_between_contributions`;
- `portfolio_value_review_threshold`;
- `milestone_review`;
- `scheduled_review_date`.

The contract must also define:

- HOLD, WAIT, and REVIEW meanings;
- deterministic status precedence when multiple rules apply;
- missing-data behavior;
- rule evaluation time semantics;
- milestone transition behavior;
- disabled-rule behavior;
- explanation/provenance returned with evaluations;
- explicit prohibition on BUY or SELL classifications in version 0.1.

**Status:** Active. Proposed contract is `docs/rules-status-contract.md` and must be accepted before Phase 3B code begins.

### Phase 3B — Rules & Status Engine

Implement the deterministic rule evaluator against the accepted Phase 3A contract.

### Phase 3C — Rules & Status Tests & Acceptance

Prove each machine-rule type, HOLD/WAIT/REVIEW classification, precedence, missing-data behavior, time boundaries, milestone transitions, disabled rules, deterministic output, and the absence of BUY/SELL classifications.

**Exit:** the rules/status engine passes Phase 3 acceptance and is promoted to `main`.

## Phase 4 — Tiny Portfolio Skill

Create the single focused Tiny Portfolio skill package.

Planned structure:

```text
skills/tiny-portfolio/
├── SKILL.md
├── references/
│   ├── accounting.md
│   ├── data-model.md
│   ├── classification.md
│   ├── workflows.md
│   ├── privacy.md
│   └── briefing.md
├── scripts/
│   ├── portfolio_engine.py
│   └── validate_portfolio.py
└── assets/
    ├── tiny-portfolio.example.json
    └── tiny-portfolio.schema.json
```

## Phase 5 — Guided Check-In

Implement and manually test new-user setup and prompt-based updates.

The workflow must ask only required questions, propose changes, obtain confirmation, produce the standard briefing, and preserve the portable record.

## Phase 6 — Screenshot + Hybrid Check-In

Add screenshot-assisted workflows without treating extraction as truth.

- screenshot privacy guidance;
- visible-value extraction;
- uncertainty handling;
- proposed values;
- explicit confirmation;
- accounting-context follow-ups;
- no raw screenshots in `tiny-portfolio.json`.

## Phase 7 — Local Plugin Packaging

Package and install the plugin using the current OpenAI plugin model.

- `.codex-plugin/plugin.json`;
- `skills: "./skills/"`;
- install-surface metadata;
- approved PNG branding;
- local marketplace configuration if needed;
- installation/testing in the ChatGPT desktop app;
- fresh-conversation testing.

## Phase 8 — Evaluation

Prove activation, safety, and correctness.

Test categories include direct activation, indirect activation, incomplete inputs, should-not-activate prompts, accounting edge cases, screenshot uncertainty, conflicting history, credential-sensitive prompts, and attempts to force BUY/SELL advice.

Submission preparation must include at least **five positive** and **three negative** test cases.

## Phase 9 — Public Alpha / Submission

Prepare a truthful skills-only public release.

- final documentation review;
- privacy/support/terms destinations as required;
- listing copy and starter prompts;
- approved logo/icon assets;
- final synthetic fixtures;
- release notes/changelog;
- submission test cases;
- final public-data/privacy audit;
- skills-only plugin submission.

## Stop rule

Files existing is not proof that a phase is complete. Each phase must satisfy its acceptance criteria before the project advances.
