# Tiny Portfolio Accounting Reference

Use this reference when explaining or interpreting deterministic accounting results.

The authoritative implementation is `scripts/portfolio_engine.py`. Do not reproduce its calculations manually when the script can be run.

## Core dollar-performance model

Version 0.1 uses contribution-adjusted dollar performance:

```text
Adjusted P/L =
    Current confirmed portfolio value
    + Total withdrawals
    - Total outside contributions
```

Opening portfolio capital is treated as contributed capital.

Version 0.1 intentionally does not publish percentage-return calculations.

## Outside capital

### Contributions

A contribution is new value supplied from outside the tracked portfolio.

Contributions:
- increase outside contributed capital;
- are not investment profit.

A later contribution must not make performance look better merely because more money was added.

### Withdrawals

A withdrawal removes value from the tracked portfolio to the outside.

Withdrawals:
- reduce net outside capital still present;
- are not investment losses.

The accounting formula adds withdrawals back when measuring contribution-adjusted dollar performance.

## Internal movement

Trades and conversions move value within the portfolio.

They do not change outside contributed capital merely because one asset became another asset.

Do not treat a purchase or conversion as a new contribution unless outside money actually entered the portfolio.

## Fees and portfolio-generated returns

Fees, staking rewards, dividends, interest, and similar activity may explain why portfolio value changed.

They must not be double-counted when the selected confirmed portfolio value already reflects them.

The accounting engine treats supported fee and reward events as explanatory totals rather than independently adding them again to adjusted P/L.

Reward subtypes in schema 1.0 include:
- staking;
- dividend;
- interest;
- other.

## Corrections

The ledger is append-oriented.

A valid correction event uses action `void` to invalidate an earlier normal ledger event while preserving the original history.

Corrections:
- do not erase the original event;
- cannot target themselves;
- cannot target another correction;
- cannot target an event already voided;
- must point to an earlier ledger event.

A replacement fact is recorded as a separate new normal event.

For deterministic derived accounting, a valid void correction removes its target from the effective ledger, including when the correction was recorded later than the historical event.

## Confirmed snapshot selection

Accounting uses confirmed snapshots as point-in-time portfolio state.

The selected current snapshot is determined by:
1. greatest `captured_at` instant;
2. if tied, greatest `recorded_at` instant;
3. if still tied and numeric `total_value` values are equal, lexicographically smallest `snapshot_id` for deterministic provenance;
4. if an exact latest tie has conflicting values, current confirmed value is unavailable because the state is ambiguous.

Timezone-aware timestamps are compared as actual instants, not raw strings.

## Accounting as-of boundary

When a confirmed snapshot is selected, contribution-adjusted accounting is computed as of that snapshot's `captured_at`.

An effective ledger event counts in snapshot-as-of accounting when its `occurred_at` is at or before that captured instant.

Use `occurred_at`, not `recorded_at`, for economic timing. Backfilled history therefore belongs to the time the event actually occurred.

## Post-snapshot activity

If an effective contribution, withdrawal, trade, fee, or reward occurred after the selected snapshot and before the analysis time represented by the current record, the accounting result can flag that the selected snapshot may no longer represent the latest economic state.

A note alone does not make a snapshot economically stale.

A voided event does not create post-snapshot activity.

## Missing and ambiguous value

Do not substitute zero for unknown current value.

No confirmed snapshot means current-value-dependent accounting is unavailable.

A conflicting exact latest snapshot tie means current value is ambiguous and current-value-dependent accounting is unavailable.

Recorded totals that are independently knowable may still be reported even when current value is unavailable.

## Decimal behavior

Money is stored in JSON as decimal strings, not JSON floating-point numbers.

The engine parses monetary values directly into Python `Decimal`.

Derived decimal strings are deterministic plain-number strings:
- no scientific notation;
- unnecessary trailing zeros removed;
- zero serialized as `"0"`.

Do not perform binary floating-point replacements for engine results.

## Provenance

Accounting results include `record_revision`.

When useful, also explain:
- the selected snapshot ID;
- selected snapshot captured time;
- whether post-snapshot activity exists;
- the reason an accounting result is unavailable.

## Interpretation guard

Accounting output describes recorded portfolio performance under Tiny Portfolio's rules.

It is not:
- a market forecast;
- tax accounting;
- a guaranteed return;
- a recommendation to buy, sell, or contribute.
