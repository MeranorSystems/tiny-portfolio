# Tiny Portfolio Data Model Reference

Use this reference when interpreting `tiny-portfolio.json`, explaining validation problems, or describing what is authoritative versus derived.

Schema version 1.0 is the current v0.1 record contract.

## Top-level record

The authoritative record contains:

```text
schema_version
portfolio
rules
milestones
ledger
snapshots
metadata
```

The portable record is user-controlled and designed to stand on its own without a Tiny Portfolio server, account system, brokerage connection, or exchange connection.

## Authoritative versus derived data

Authoritative data is what is persisted in the record:
- portfolio identity and base currency;
- user-defined machine rules and guidance notes;
- milestones;
- append-oriented ledger events;
- confirmed snapshots;
- metadata such as `record_revision`.

Derived data is recomputed:
- current selected snapshot;
- effective ledger after corrections;
- contribution totals;
- withdrawals;
- adjusted dollar P/L;
- rule outcomes;
- HOLD / WAIT / REVIEW;
- next-milestone distance.

Do not persist redundant derived caches merely to avoid recomputation.

## Money and quantities

Monetary values and numeric quantities in the portable JSON use decimal strings, for example:

```json
"total_value": "61.29"
```

Do not convert authoritative monetary strings into JSON binary floating-point values.

Version 0.1 uses one portfolio base currency and does not perform FX conversion.

## Portfolio object

The portfolio identifies:
- `portfolio_id`;
- name;
- base currency;
- creation time.

Do not require brokerage/exchange account identifiers.

## Rules

Rules contain:
- machine-evaluable rules;
- free-form guidance notes.

Only the five supported machine-rule types are deterministically evaluated in v0.1:
- `max_contribution_per_period`;
- `minimum_days_between_contributions`;
- `portfolio_value_review_threshold`;
- `milestone_review`;
- `scheduled_review_date`.

Guidance notes are user context. They are not automatically machine-enforced.

## Milestones

A milestone contains:
- stable milestone ID;
- label;
- target value;
- creation time;
- optional `reached_at`.

`reached_at` is durable historical acknowledgement.

Do not replace historical milestone achievement with a mutable derived status field.

## Ledger

Supported v0.1 event types:
- contribution;
- withdrawal;
- trade;
- fee;
- reward;
- note;
- correction.

Each event has:
- stable event ID;
- `occurred_at`;
- `recorded_at`;
- source;
- event-specific `data`.

The ledger is append-oriented. Do not silently rewrite confirmed historical events.

## Corrections

A correction uses:

```text
action: void
target_event_id: <earlier normal event>
```

The original event remains in history.

A correction:
- cannot target itself;
- cannot target another correction;
- cannot target an event that is not earlier in ledger order;
- cannot void the same target twice.

A corrected replacement is a separate new normal event.

## Confirmed snapshots

A snapshot records confirmed point-in-time portfolio state:
- snapshot ID;
- `captured_at`;
- `recorded_at`;
- total portfolio value;
- holdings;
- source;
- explicit confirmation metadata.

A holding includes:
- symbol;
- name;
- asset type;
- optional quantity;
- optional value.

At least one of quantity or value must be present for a holding.

Supported asset types:
- crypto;
- equity;
- fund;
- cash;
- other.

## Screenshot-derived information

Unconfirmed screenshot extraction is not authoritative record data.

Raw screenshots are not embedded in `tiny-portfolio.json`.

When screenshot-assisted workflows are implemented, extracted values remain proposals until the user explicitly confirms them. Only confirmed values become persisted snapshots/history.

Phase 4 does not yet implement screenshot persistence.

## Metadata and revision provenance

`metadata.record_revision` is a positive integer and identifies the authoritative record revision used for deterministic results.

`metadata.updated_at` records record update time.

Current state should be derived from the record rather than maintained through redundant pointers such as a cached "latest snapshot ID."

## Sources

Record sources may include:
- guided;
- screenshot;
- hybrid;
- manual import.

A source describes how information entered the record. It does not override validation or confirmation requirements.

## Validation order

Before accounting or status:
1. validate against the JSON Schema;
2. validate cross-record structural semantics.

If validation fails, stop deterministic analysis rather than guessing how to repair the record.

## Missing information

Absence is not permission to invent.

Keep missing quantities, values, events, timestamps, rules, or milestone facts unknown until authoritative information establishes them.
