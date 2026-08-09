# Tiny Portfolio Manual Build Roadmap

**Baseline:** 2026-08-09
**Build mode:** Manual, phase-gated development
**Current phase:** Phase 2B — Accounting Engine
**Development branch:** `feat/deterministic-accounting`
**Accepted baseline:** Phase 1 promoted to `main` at `a522dd5`

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

Define and accept the deterministic accounting behavior before implementation:

- effective-ledger and correction behavior;
- confirmed-snapshot selection;
- accounting as-of boundary;
- contributions and withdrawals;
- trade neutrality;
- fee/reward explanatory totals without double counting;
- contribution-adjusted dollar P/L;
- post-snapshot activity signaling;
- missing/ambiguous value handling;
- Decimal requirements and deterministic derived serialization;
- required synthetic accounting scenarios.

**Exit:** accepted. `docs/accounting-contract.md` is the implementation contract for Phase 2B.

### Phase 2B — Accounting Engine

**Status:** Active

Implement `portfolio_engine.py` against the accepted Phase 2A contract.

Required behavior includes:

- current confirmed value;
- contributed capital;
- withdrawals;
- trade/conversion neutrality for outside capital;
- known fees/rewards as explanatory activity;
- contribution-adjusted dollar P/L;
- correction-aware effective ledger;
- post-snapshot freshness signaling;
- missing-data handling;
- deterministic output.

### Phase 2C — Accounting Tests & Acceptance

Required tests include contribution-not-profit, withdrawal-not-loss, trade neutrality, no fee/reward double counting, correction behavior, Decimal safety, as-of snapshot behavior, ambiguous snapshot handling, and missing-data behavior.

**Exit:** the accounting engine passes its Phase 2 acceptance review and is promoted to `main`.

## Phase 3 — Rules + HOLD / WAIT / REVIEW

Implement the small deterministic rule/status system.

Initial machine-rule types:

- maximum contribution per period;
- minimum days between contributions;
- portfolio-value review threshold;
- milestone review;
- scheduled review date.

Version 0.1 must never output BUY or SELL as a portfolio status.

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
