# Tiny Portfolio Portable Data Contract

**Schema version:** 1.0
**Status:** Phase 1 design contract
**Authoritative file name:** `tiny-portfolio.json`

## Purpose

`tiny-portfolio.json` is the portable, user-controlled record used by Tiny Portfolio by Meranor.

It is designed to preserve the portfolio facts needed to continue a Tiny Portfolio workflow across conversations without requiring a Tiny Portfolio account, hosted portfolio database, brokerage connection, or exchange connection.

The file contains authoritative user-confirmed facts and historical records.

It does not contain unexplained derived calculations or transient screenshot extraction proposals.

## Top-level structure

Every version 1.0 record contains:

```json
{
  "schema_version": "1.0",
  "portfolio": {},
  "rules": {},
  "milestones": [],
  "ledger": [],
  "snapshots": [],
  "metadata": {}
}
```

The six data areas are:

- `portfolio` — portfolio identity and base settings;
- `rules` — deterministic user rules and non-deterministic guidance notes;
- `milestones` — user-defined portfolio-value checkpoints;
- `ledger` — append-oriented historical events;
- `snapshots` — confirmed portfolio states;
- `metadata` — portable-record revision information.

## Core invariants

### 1. Decimal values are strings

Money amounts and asset quantities must be stored as decimal strings.

Valid:

```json
"amount": "50.00"
```

```json
"quantity": "0.013421"
```

Invalid:

```json
"amount": 50.00
```

This prevents JSON floating-point representation from becoming the authoritative financial value.

Decimal strings:

- contain digits and an optional decimal point;
- do not contain commas;
- do not contain currency symbols;
- do not use scientific notation;
- are non-negative unless a future schema version explicitly permits otherwise.

Direction is represented by the event type rather than by using negative amounts.

### 2. Unknown information stays unknown

Tiny Portfolio must never fabricate missing information.

Optional unknown fields should normally be omitted.

A missing quantity does not become zero.

A missing value does not become zero.

A missing timestamp does not receive an invented historical timestamp.

### 3. One base currency per portfolio

Version 1.0 uses one portfolio base currency.

The base currency is represented by a three-letter uppercase currency code such as:

```json
"base_currency": "USD"
```

Version 1.0 does not perform foreign-exchange accounting.

### 4. Authoritative snapshots are confirmed

Only confirmed portfolio snapshots belong in the authoritative portable record.

Screenshot-derived values remain transient proposals until the user explicitly confirms or corrects them.

An unconfirmed screenshot extraction must not be written to `tiny-portfolio.json`.

### 5. Ledger history is append-oriented

Existing historical ledger events must not be silently rewritten to hide corrections.

If an existing event is wrong:

1. append a correction event identifying the event being corrected;
2. mark the original event as void through that correction;
3. if necessary, append a new correct event.

This preserves an auditable history.

### 6. Derived results are not authoritative state

Version 1.0 does not store derived values such as:

- contribution-adjusted profit/loss;
- HOLD, WAIT, or REVIEW status;
- distance to next milestone;
- current contributed-capital total;
- calculated fee totals;
- calculated reward totals.

Those values must be reproducible from the authoritative record.

### 7. IDs are stable

Records use opaque stable IDs.

IDs must be unique within their applicable collection and should not be reused after deletion or correction.

Human-readable sequential IDs may be used in examples, but implementations must not rely on IDs being sequential.

### 8. Timestamps contain timezone information

Timestamps use RFC 3339 / ISO 8601 date-time values with timezone information.

UTC `Z` timestamps are preferred.

Example:

```json
"occurred_at": "2026-08-09T19:45:00Z"
```

### 9. The portable record contains no account-access credentials

The format must not require:

- passwords;
- authentication codes;
- seed phrases;
- wallet private keys;
- brokerage credentials;
- exchange API secrets;
- Social Security numbers;
- complete financial account numbers.

## Portfolio object

The `portfolio` object identifies the portable portfolio.

Required fields:

```json
{
  "portfolio_id": "portfolio_demo_001",
  "name": "Demo Tiny Portfolio",
  "base_currency": "USD",
  "created_at": "2026-08-09T19:45:00Z"
}
```

### `portfolio_id`

Stable opaque identifier for this portfolio.

### `name`

User-facing portfolio name.

### `base_currency`

Three-letter uppercase base currency.

### `created_at`

Timestamp when the Tiny Portfolio record was created.

## Rules object

Rules are separated into deterministic machine rules and human-readable guidance notes.

```json
{
  "machine_rules": [],
  "guidance_notes": []
}
```

### Machine rules

Each machine rule contains:

```json
{
  "rule_id": "rule_001",
  "type": "minimum_days_between_contributions",
  "enabled": true,
  "created_at": "2026-08-09T19:45:00Z",
  "config": {
    "days": 14
  }
}
```

Version 1.0 supports these initial rule types:

- `max_contribution_per_period`
- `minimum_days_between_contributions`
- `portfolio_value_review_threshold`
- `milestone_review`
- `scheduled_review_date`

The rule `config` structure depends on the rule type.

### Machine-rule configuration contract

All monetary rule values are expressed in the portfolio `base_currency`.

#### `max_contribution_per_period`

```json
{
  "rule_id": "rule_002",
  "type": "max_contribution_per_period",
  "enabled": true,
  "created_at": "2026-08-09T19:45:00Z",
  "config": {
    "amount": "25.00",
    "period": "month"
  }
}
```

Required config fields:

- `amount` — non-negative decimal string in the portfolio base currency;
- `period` — one of `day`, `week`, `month`, `quarter`, or `year`.

Version 1.0 evaluates these as UTC calendar periods:

- `day` — 00:00:00Z through the end of that UTC day;
- `week` — Monday 00:00:00Z through Sunday 23:59:59.999...Z;
- `month` — UTC calendar month;
- `quarter` — UTC calendar quarter beginning January, April, July, or October;
- `year` — UTC calendar year.

Only non-voided `contribution` ledger events whose `occurred_at` timestamp falls inside the active period count toward the limit.

#### `minimum_days_between_contributions`

```json
{
  "rule_id": "rule_003",
  "type": "minimum_days_between_contributions",
  "enabled": true,
  "created_at": "2026-08-09T19:45:00Z",
  "config": {
    "days": 14
  }
}
```

Required config field:

- `days` — positive integer.

Version 1.0 interprets one day as 24 elapsed hours. The rule compares a proposed contribution time with the most recent prior non-voided contribution `occurred_at` timestamp.

#### `portfolio_value_review_threshold`

```json
{
  "rule_id": "rule_004",
  "type": "portfolio_value_review_threshold",
  "enabled": true,
  "created_at": "2026-08-09T19:45:00Z",
  "config": {
    "threshold_value": "75.00",
    "direction": "at_or_above"
  }
}
```

Required config fields:

- `threshold_value` — non-negative decimal string in the portfolio base currency;
- `direction` — `at_or_above` or `at_or_below`.

The rule evaluates the `total_value` of the most recent confirmed snapshot. If no confirmed snapshot exists, the threshold cannot be evaluated.

#### `milestone_review`

```json
{
  "rule_id": "rule_005",
  "type": "milestone_review",
  "enabled": true,
  "created_at": "2026-08-09T19:45:00Z",
  "config": {
    "milestone_id": "milestone_001"
  }
}
```

Required config field:

- `milestone_id` — ID of a milestone in the same portable record.

The rule is intended to request review when the referenced milestone is newly reached. Detailed evaluation and transition behavior is defined by the rule engine rather than duplicated in the data contract.

#### `scheduled_review_date`

```json
{
  "rule_id": "rule_006",
  "type": "scheduled_review_date",
  "enabled": true,
  "created_at": "2026-08-09T19:45:00Z",
  "config": {
    "review_date": "2026-09-01"
  }
}
```

Required config field:

- `review_date` — RFC 3339 full-date value in `YYYY-MM-DD` form.

Version 1.0 treats the review date as a UTC calendar date. The rule becomes due on that date and remains due until the user updates, disables, or replaces the rule.

Rules must be deterministic. Free-form prose must not be interpreted as though it were a machine-enforceable rule.

### Guidance notes

Guidance notes preserve user preferences or reminders that are useful context but are not deterministically evaluated.

Example:

```json
{
  "note_id": "guidance_001",
  "text": "Prefer slow contributions rather than reacting to daily price movement.",
  "created_at": "2026-08-09T19:45:00Z"
}
```

Guidance notes must never be presented as if they were machine-enforced rules.

## Milestones

Milestones are user-defined portfolio-value checkpoints.

Example:

```json
{
  "milestone_id": "milestone_001",
  "label": "First checkpoint",
  "target_value": "75.00",
  "created_at": "2026-08-09T19:45:00Z"
}
```

If the milestone has historically been reached, it may also contain:

```json
"reached_at": "2026-08-20T15:00:00Z"
```

Version 1.0 does not store a separate `status` field.

Whether a milestone is unreached or reached can be determined from `reached_at`, and UI concepts such as "next milestone" are derived.

Once recorded, `reached_at` should not disappear merely because portfolio value later falls below the milestone.

## Ledger

The ledger preserves portfolio events in append-oriented history.

Each event contains common fields:

```json
{
  "event_id": "event_001",
  "event_type": "contribution",
  "occurred_at": "2026-08-09T19:45:00Z",
  "recorded_at": "2026-08-09T19:46:00Z",
  "source": "guided",
  "data": {}
}
```

Version 1.0 event types are:

- `contribution`
- `withdrawal`
- `trade`
- `fee`
- `reward`
- `note`
- `correction`

### Event source

Initial source values are:

- `guided`
- `screenshot`
- `hybrid`
- `manual_import`

The source describes how the confirmed fact entered Tiny Portfolio.

It does not change the accounting meaning of the event.

### Contribution

```json
{
  "event_id": "event_001",
  "event_type": "contribution",
  "occurred_at": "2026-08-09T19:45:00Z",
  "recorded_at": "2026-08-09T19:46:00Z",
  "source": "guided",
  "data": {
    "amount": "50.00",
    "currency": "USD"
  }
}
```

Contributions represent outside capital entering the portfolio.

### Withdrawal

```json
{
  "event_id": "event_002",
  "event_type": "withdrawal",
  "occurred_at": "2026-08-12T15:00:00Z",
  "recorded_at": "2026-08-12T15:01:00Z",
  "source": "guided",
  "data": {
    "amount": "5.00",
    "currency": "USD"
  }
}
```

Withdrawals represent capital leaving the portfolio.

### Trade

```json
{
  "event_id": "event_003",
  "event_type": "trade",
  "occurred_at": "2026-08-13T15:00:00Z",
  "recorded_at": "2026-08-13T15:01:00Z",
  "source": "guided",
  "data": {
    "from_asset": "USD",
    "to_asset": "BTC",
    "from_quantity": "5.00",
    "to_quantity": "0.000041"
  }
}
```

Trades and conversions represent value moving within the portfolio.

They do not represent outside contributed capital.

### Fee

```json
{
  "event_id": "event_004",
  "event_type": "fee",
  "occurred_at": "2026-08-13T15:00:00Z",
  "recorded_at": "2026-08-13T15:01:00Z",
  "source": "guided",
  "data": {
    "amount": "0.10",
    "currency": "USD",
    "asset_symbol": "BTC"
  }
}
```

`asset_symbol` is optional when the associated asset is unknown or irrelevant.

### Reward

```json
{
  "event_id": "event_005",
  "event_type": "reward",
  "occurred_at": "2026-08-14T15:00:00Z",
  "recorded_at": "2026-08-14T15:01:00Z",
  "source": "guided",
  "data": {
    "reward_type": "staking",
    "amount": "0.08",
    "currency": "USD",
    "asset_symbol": "ETH"
  }
}
```

Initial reward types are:

- `staking`
- `dividend`
- `interest`
- `other`

### Note

```json
{
  "event_id": "event_006",
  "event_type": "note",
  "occurred_at": "2026-08-14T15:00:00Z",
  "recorded_at": "2026-08-14T15:01:00Z",
  "source": "guided",
  "data": {
    "text": "User reviewed the portfolio but made no changes."
  }
}
```

Notes do not affect accounting.

### Correction

A correction explicitly voids an earlier ledger event.

```json
{
  "event_id": "event_007",
  "event_type": "correction",
  "occurred_at": "2026-08-15T15:00:00Z",
  "recorded_at": "2026-08-15T15:01:00Z",
  "source": "guided",
  "data": {
    "target_event_id": "event_002",
    "action": "void",
    "reason": "The withdrawal was recorded in error."
  }
}
```

Version 1.0 supports the correction action:

```text
void
```

If corrected replacement information is required, a new normal ledger event is appended separately.

Correction events do not erase the original historical event.

## Snapshots

Snapshots represent confirmed portfolio state at a point in time.

Example:

```json
{
  "snapshot_id": "snapshot_001",
  "captured_at": "2026-08-09T20:00:00Z",
  "recorded_at": "2026-08-09T20:01:00Z",
  "total_value": "61.29",
  "holdings": [
    {
      "symbol": "ETH",
      "name": "Ethereum",
      "asset_type": "crypto",
      "quantity": "0.0142",
      "value": "53.44"
    },
    {
      "symbol": "BTC",
      "name": "Bitcoin",
      "asset_type": "crypto",
      "value": "7.41"
    },
    {
      "symbol": "USD",
      "name": "Cash",
      "asset_type": "cash",
      "value": "0.44"
    }
  ],
  "source": "hybrid",
  "confirmation": {
    "confirmed_at": "2026-08-09T20:01:00Z"
  }
}
```

### Supported asset types

Version 1.0 supports:

- `crypto`
- `equity`
- `fund`
- `cash`
- `other`

### Holding requirements

Every holding requires:

- `symbol`;
- `name`;
- `asset_type`.

A holding must contain at least one of:

- `quantity`;
- `value`.

Both may be present.

Unknown quantity or value should be omitted rather than fabricated.

### Snapshot total

`total_value` is the user-confirmed total portfolio value in the portfolio base currency.

The sum of individually known holding values is not required to equal `total_value` when some holdings are partially known or omitted.

Tiny Portfolio may surface such differences for review but must not silently invent balancing values.

### Confirmation

The presence of a snapshot in the authoritative portable record means the portfolio state was explicitly confirmed.

`confirmation.confirmed_at` records when that confirmation occurred.

There is intentionally no `"status": "unconfirmed"` state in version 1.0 authoritative snapshots.

## Metadata

Metadata describes the portable record itself.

Example:

```json
{
  "record_revision": 1,
  "updated_at": "2026-08-09T20:01:00Z",
  "last_confirmed_snapshot_id": "snapshot_001"
}
```

### `record_revision`

Positive integer incremented when an authoritative portable record is updated.

It is intended to help identify older copies of the same portable record.

### `updated_at`

Timestamp of the most recent authoritative record update.

### `last_confirmed_snapshot_id`

Optional ID of the most recently confirmed snapshot.

It may be omitted when the record does not yet contain a snapshot.

## Cross-record semantic invariants

Some version 1.0 requirements depend on relationships between separate objects and cannot be fully expressed by JSON Schema alone.

Tiny Portfolio validation must also enforce these structural semantic rules.

### Collection ID uniqueness

The following IDs must be unique within their own collections:

- machine-rule `rule_id`;
- guidance-note `note_id`;
- `milestone_id`;
- ledger `event_id`;
- `snapshot_id`.

Version 1.0 does not require IDs to be globally unique across different collections.

### Base-currency consistency

Version 1.0 uses one portfolio base currency.

For these ledger event types, `data.currency` must equal `portfolio.base_currency`:

- `contribution`;
- `withdrawal`;
- `fee`;
- `reward`.

Milestone `target_value`, snapshot `total_value`, holding `value`, and monetary machine-rule values are interpreted in the portfolio base currency.

Version 1.0 does not perform foreign-exchange conversion.

### Milestone-rule references

A `milestone_review` rule must reference a `milestone_id` that exists in the same portable record.

### Correction references

A `correction` event must:

- target an event that exists earlier in the ledger array;
- not target itself;
- not target another `correction` event;
- not void an event that has already been voided by an earlier correction.

This keeps correction history simple and append-oriented.

A corrected replacement fact is represented by a separate new normal ledger event.

### Snapshot metadata reference

If `metadata.last_confirmed_snapshot_id` is present, it must reference a snapshot that exists in the same portable record.

### Timestamp ordering

Where both timestamps are present:

- an event `recorded_at` must not be earlier than its `occurred_at`;
- a milestone `reached_at` must not be earlier than its `created_at`;
- a snapshot `recorded_at` must not be earlier than its `captured_at`;
- `confirmation.confirmed_at` must not be earlier than the snapshot `captured_at`;
- `confirmation.confirmed_at` must not be later than the snapshot `recorded_at`.

These checks describe record consistency only. They do not perform portfolio accounting.

## Record evolution

`schema_version` identifies the data-contract version.

Version 1.0 readers must not silently reinterpret incompatible future schema versions as version 1.0.

Schema migrations must be explicit and testable.

The version 1.0 JSON Schema should be strict enough to catch misspelled or unsupported properties rather than silently accepting arbitrary fields.

## Security boundary

The portable record contains portfolio-tracking information and may still be financially sensitive.

Users should treat their own `tiny-portfolio.json` files as private financial records.

Public repository fixtures must always use fictional or deliberately synthetic data.

No real user portfolio record may be committed to this repository.

## Phase 1 acceptance requirements

Phase 1 is complete only when:

- this contract is reviewed;
- `tiny-portfolio.schema.json` implements this contract;
- a fictional full example portfolio validates;
- a minimal valid portfolio validates;
- invalid money values fail;
- missing required schema information fails;
- an unconfirmed snapshot representation fails;
- schema validation tests pass;
- no real portfolio data is present;
- explicit correction events are structurally supported and broken correction references are rejected.
