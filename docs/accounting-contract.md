# Tiny Portfolio Accounting Contract

**Phase:** 2A — Accounting Contract
**Status:** Accepted
**Input contract:** `tiny-portfolio.json` schema version 1.0

## Purpose

This document defines the accounting behavior that Tiny Portfolio must implement before the accounting engine is written.

The goal is narrow: derive contribution-adjusted dollar performance and explanatory activity from a validated Tiny Portfolio record without inventing missing facts, double-counting activity, or using binary floating-point arithmetic for money.

This is portfolio tracking and decision support. It is not brokerage execution, tax-lot accounting, cost-basis reporting, or individualized investment advice.

## Design principles

The accounting engine must be:

- deterministic — the same valid input produces the same result;
- Decimal-safe — monetary arithmetic uses Python `Decimal`, never binary `float`;
- contribution-aware — outside contributions are not investment profit;
- withdrawal-aware — withdrawals are not investment losses;
- correction-aware — voided ledger events do not affect derived totals;
- snapshot-based — performance uses a confirmed portfolio total rather than reconstructing market value from holdings;
- time-consistent — performance activity is evaluated as of the selected confirmed snapshot;
- conservative about unknowns — unavailable information remains unavailable rather than being guessed;
- explainable — every derived result can be traced to confirmed snapshots and effective ledger events.

## Preconditions

Phase 2 accounting operates on a version 1.0 record that has already passed:

1. JSON Schema validation; and
2. Tiny Portfolio structural-semantic validation.

The accounting engine must not silently repair an invalid record.

Invalid currency relationships, malformed timestamps, broken correction references, duplicate IDs, or unsupported schema fields are validation errors rather than accounting decisions.

## Authoritative inputs

Phase 2 uses only these version 1.0 facts for accounting:

- `portfolio.base_currency`;
- confirmed `snapshots[].total_value`;
- snapshot timestamps and IDs;
- non-voided `contribution` events;
- non-voided `withdrawal` events;
- non-voided `fee` events;
- non-voided `reward` events;
- valid `correction` events that void earlier ledger events.

These fields do not change contribution-adjusted dollar P/L directly:

- holdings quantities;
- individually known holding values;
- trades or conversions;
- notes;
- milestones;
- rules;
- guidance notes.

Trades, fees, rewards, and other activity may still be surfaced as explanatory information or freshness signals as described below.

## Effective ledger

Before calculating totals, Tiny Portfolio derives the effective ledger.

### Voided events

A valid `correction` event with action `void` causes its targeted normal ledger event to be excluded from accounting totals.

The original event remains in the portable record for audit history.

Correction events themselves have no monetary effect.

Because structural-semantic validation rejects corrections that target another correction or void an already-voided event, Phase 2 may treat the validated correction set as authoritative.

### Effective event

An effective event is a normal ledger event that is not targeted by a valid correction.

Only effective events participate in accounting totals.

## Selected confirmed snapshot

Contribution-adjusted P/L requires a confirmed total portfolio value.

Version 1.0 authoritative snapshots are already confirmed by the data contract.

### Selection order

The accounting engine selects the latest portfolio state by:

1. greatest `captured_at`;
2. if multiple snapshots have that same `captured_at`, greatest `recorded_at`;
3. if multiple snapshots still tie:
   - if their `total_value` values are numerically equal, the value is usable and the lexicographically smallest `snapshot_id` is used only as deterministic provenance;
   - if their `total_value` values differ, performance is unavailable because the latest confirmed value is ambiguous.

`captured_at` takes priority over `recorded_at`. A snapshot recorded later does not replace a snapshot representing a newer portfolio state merely because it was entered later.

### No confirmed snapshot

If the record contains no confirmed snapshot:

- `current_confirmed_value` is unavailable;
- contribution-adjusted P/L is unavailable;
- the engine must not infer current value from holdings, trades, rewards, or prior assumptions.

Ledger activity totals may still be derived independently.

## Timestamp comparison

All RFC 3339 date-time comparisons use parsed timezone-aware instants.

Implementations must not compare timestamp strings lexicographically.

Equivalent instants expressed with different offsets are equal for accounting purposes. For example:

```text
2026-08-09T18:00:00Z
2026-08-09T13:00:00-05:00
```

represent the same instant.

Snapshot ordering, event cutoffs, timestamp ties, and post-snapshot activity checks must compare actual instants.

## Accounting time boundary

Performance is calculated **as of the selected snapshot's `captured_at` instant**.

For performance totals:

- an effective event with `occurred_at <= snapshot.captured_at` is included when its event type affects that total;
- an effective event with `occurred_at > snapshot.captured_at` is excluded from that performance cut.

`occurred_at`, not `recorded_at`, determines whether a normal event belongs to the performance period.

A later correction may void an earlier event even when the correction itself was recorded after the selected snapshot. The current portable record represents corrected history, so the void applies to the derived historical calculation.

## Core accounting terms

All monetary source values are converted directly from their schema-valid decimal strings to Python `Decimal`.

### Total outside contributions

`total_contributions_as_of` is the sum of effective `contribution.data.amount` values whose `occurred_at` is on or before the selected snapshot time.

Contributions are outside capital entering the portfolio.

They are not profit.

### Total withdrawals

`total_withdrawals_as_of` is the sum of effective `withdrawal.data.amount` values whose `occurred_at` is on or before the selected snapshot time.

Withdrawals are capital leaving the portfolio.

They are not investment losses.

### Net outside capital

```text
net_outside_capital_as_of =
    total_contributions_as_of
    - total_withdrawals_as_of
```

Net outside capital may be negative when cumulative withdrawals exceed cumulative contributions.

### Current confirmed value

`current_confirmed_value` is the selected confirmed snapshot's `total_value`.

Tiny Portfolio does not calculate current confirmed value by summing holding values.

The data contract intentionally allows some holdings to be partially known or omitted, so the confirmed snapshot total remains authoritative.

### Contribution-adjusted dollar P/L

```text
adjusted_profit_loss =
    current_confirmed_value
    + total_withdrawals_as_of
    - total_contributions_as_of
```

Equivalent form:

```text
adjusted_profit_loss =
    current_confirmed_value
    - net_outside_capital_as_of
```

A positive result represents contribution-adjusted dollar gain.

A negative result represents contribution-adjusted dollar loss.

Zero means confirmed portfolio value equals net outside capital at the accounting cut.

## Opening capital

Tiny Portfolio must never invent an opening contribution from the first snapshot.

If a user begins tracking an already-funded portfolio, the outside capital that funded that starting portfolio must be represented explicitly by one or more `contribution` events.

A snapshot is a statement of portfolio value, not proof of how much outside capital was contributed.

Phase 2 can calculate only from facts present in the authoritative record. It cannot detect every real-world transaction that a user failed to record.

Later setup workflows must therefore obtain enough contribution history to support meaningful performance accounting.

## Trades and conversions

`trade` events represent internal movement of portfolio value.

They do not increase or decrease:

- total outside contributions;
- total withdrawals;
- net outside capital;
- contribution-adjusted P/L by separate arithmetic.

Version 0.1 does not calculate realized gain, tax lots, cost basis, or per-trade investment return.

Trade activity can make the selected snapshot stale for current holdings, so post-snapshot trades are included in the freshness signal described below.

## Fees

An effective `fee` event records known fee activity in the portfolio base currency.

### Explanatory total

`known_fees_as_of` is the sum of effective fee amounts occurring on or before the selected snapshot time.

An all-record `known_fees_total` may also be derived for activity reporting.

### No double counting

Fees are **not separately subtracted** from contribution-adjusted P/L.

The selected confirmed portfolio value is authoritative. If a fee reduced the portfolio value, that effect is already present in the snapshot total.

Subtracting the fee again would double-count it.

Fee totals explain performance; they do not independently modify the core P/L formula.

## Rewards

An effective `reward` event records known portfolio-generated return such as:

- staking;
- dividends;
- interest;
- other supported reward types.

### Explanatory total

`known_rewards_as_of` is the sum of effective reward amounts occurring on or before the selected snapshot time.

An all-record `known_rewards_total` may also be derived for activity reporting.

### No double counting

Rewards are **not separately added** to contribution-adjusted P/L.

If a reward increased portfolio value and is represented in the selected snapshot, that effect is already present in the confirmed value.

Adding the reward again would double-count it.

Reward totals explain performance; they do not independently modify the core P/L formula.

## All-record activity totals

The engine may derive ledger activity totals across all effective events, independent of the selected snapshot:

- `total_contributions_recorded`;
- `total_withdrawals_recorded`;
- `known_fees_total`;
- `known_rewards_total`.

These totals describe the currently recorded effective ledger.

They must not be substituted into the snapshot-based P/L formula when some of those events occurred after the selected snapshot.

## Post-snapshot activity

The selected confirmed snapshot may be older than the latest portfolio-changing ledger activity.

`has_post_snapshot_activity` is true when any effective event of these types has `occurred_at > selected_snapshot.captured_at`:

- `contribution`;
- `withdrawal`;
- `trade`;
- `fee`;
- `reward`.

`note` and `correction` events do not by themselves set this flag.

A true freshness flag does not make the historical P/L calculation invalid. It means the result is explicitly an **as-of-snapshot** result and should not be presented as if it reflects later portfolio-changing activity.

The engine may also return the count of effective post-snapshot portfolio-changing events.

## Missing and unknown information

Tiny Portfolio must distinguish zero from unknown.

### Known zero

If a validated record has no effective contributions in the relevant accounting cut, the derived contribution total is zero.

If it has no effective withdrawals, fees, or rewards in the relevant cut, those derived totals are zero.

### Unknown current value

If there is no selected confirmed snapshot, current confirmed value and contribution-adjusted P/L are unavailable.

### Ambiguous latest value

If snapshot selection reaches an unresolved tie with different total values, current confirmed value and contribution-adjusted P/L are unavailable.

### Unrecorded real-world history

The engine must not guess transactions that are absent from the authoritative record.

A mathematically available result means “calculated from the validated recorded facts.” It is not a claim that the user recorded every real-world transaction.

## Decimal requirements

All monetary arithmetic must use Python `decimal.Decimal`.

### Exactness and Decimal context

Using `Decimal` is necessary but not sufficient: Python Decimal arithmetic is governed by a precision context.

The engine must perform monetary addition and subtraction in a local Decimal context whose precision is high enough to represent the validated input values and their sums exactly.

It must not rely blindly on the process-wide default Decimal precision.

For a calculation, the implementation must choose precision from the actual input set with enough integer/significant-digit headroom for accumulation. A valid implementation may, for example, derive precision from the maximum significant digits present plus sufficient growth for the number of terms being summed.

No Phase 2 monetary total may be rounded merely because a Decimal context was too small.

The engine must not quantize monetary values to two decimal places unless a later presentation layer explicitly formats them for display.

Forbidden for monetary calculations:

- `float`;
- conversion through `float`;
- binary floating-point accumulation;
- rounding based on binary floating-point intermediates.

Source values must be converted directly:

```python
Decimal("0.10")
```

not:

```python
Decimal(0.10)
```

The engine must not impose a hard-coded two-decimal currency scale in version 0.1.

## Derived decimal serialization

When Phase 2 results are serialized as text or JSON, derived decimal values use canonical plain decimal notation:

- no scientific notation;
- no leading `+`;
- no unnecessary leading zeros;
- trailing fractional zeros removed;
- zero serialized as `"0"`;
- negative derived results permitted.

Examples:

```text
Decimal("60.00")     -> "60"
Decimal("0.300")     -> "0.3"
Decimal("-5.00")     -> "-5"
Decimal("0.00")      -> "0"
Decimal("1000.000")  -> "1000"
```

Presentation layers may later format those values for a user's base currency. Presentation formatting must not change the underlying Decimal result.

## Accounting result contract

The Phase 2 engine must expose enough provenance to explain its result.

Because later correction events can change derived historical totals without changing the selected snapshot itself, every accounting result includes `metadata.record_revision`.

The pair of the portable-record revision and the selected snapshot provenance identifies the authoritative record state used for the calculation.

Conceptual result:

```json
{
  "calculation_status": "available",
  "record_revision": 8,
  "base_currency": "USD",
  "snapshot_id": "snapshot_demo_001",
  "as_of": "2026-08-09T18:30:00Z",
  "current_confirmed_value": "66",
  "total_contributions_as_of": "60",
  "total_withdrawals_as_of": "0",
  "net_outside_capital_as_of": "60",
  "adjusted_profit_loss": "6",
  "known_fees_as_of": "0.1",
  "known_rewards_as_of": "0.25",
  "has_post_snapshot_activity": false,
  "post_snapshot_activity_count": 0
}
```

When performance is unavailable:

```json
{
  "calculation_status": "unavailable",
  "reason": "no_confirmed_snapshot",
  "record_revision": 8,
  "base_currency": "USD",
  "snapshot_id": null,
  "as_of": null,
  "current_confirmed_value": null,
  "adjusted_profit_loss": null
}
```

Initial unavailable reason codes:

- `no_confirmed_snapshot`;
- `ambiguous_latest_snapshot`.

The implementation may include additional explanatory fields, but it must not silently change the meaning of the core fields defined here.

## Required Phase 2 accounting scenarios

The implementation must eventually prove at least these cases with synthetic tests.

### Contribution is not profit

```text
contributions: 50
withdrawals: 0
confirmed value: 50
adjusted P/L: 0
```

### Market gain

```text
contributions: 50
withdrawals: 0
confirmed value: 55
adjusted P/L: +5
```

### Additional contribution is not profit

```text
contributions: 50 + 10
withdrawals: 0
confirmed value: 66
adjusted P/L: +6
```

### Withdrawal is not loss

```text
contributions: 60
withdrawals: 10
confirmed value: 55
adjusted P/L: +5
```

### Trade neutrality

Adding an internal trade without changing the confirmed snapshot value or outside cash flows must not change contribution-adjusted P/L.

### Fee is not double-counted

If confirmed value already reflects a fee, adding the corresponding fee ledger event must change the explanatory fee total but must not subtract the fee again from adjusted P/L.

### Reward is not double-counted

If confirmed value already reflects a reward, adding the corresponding reward ledger event must change the explanatory reward total but must not add the reward again to adjusted P/L.

### Correction removes accounting effect

If a contribution, withdrawal, fee, or reward event is validly voided, that event must not contribute to derived monetary totals.

### Post-snapshot activity uses an as-of cut

An effective portfolio-changing event after the selected snapshot must not alter that snapshot's P/L calculation and must set the post-snapshot freshness signal.

### Snapshot state time beats entry time

Given two confirmed snapshots where one has a later `captured_at` but the other has a later `recorded_at`, the snapshot with the later `captured_at` must be selected.

This proves that a later-entered older state cannot replace a newer portfolio state.

### Backfilled event uses occurrence time

An effective contribution, withdrawal, fee, or reward that was recorded after the selected snapshot but whose `occurred_at` is on or before the snapshot must be included in that snapshot's accounting cut.

This proves that `occurred_at`, not `recorded_at`, controls the economic period.

### Decimal safety

A case using values such as `0.1` and `0.2` must produce exact Decimal arithmetic rather than a binary floating-point artifact.

A high-precision or large-value accumulation case must also prove that the engine does not silently round because of Python's default Decimal context.

### Timestamp-offset equivalence

Equivalent RFC 3339 instants expressed with different timezone offsets must compare as the same instant for snapshot selection and event cutoffs.

### No confirmed snapshot

A valid record with no snapshot must return unavailable performance rather than inventing a current value.

### Ambiguous latest snapshot

An unresolved latest-snapshot tie with conflicting total values must return unavailable performance rather than silently selecting one.

## Out of scope for Phase 2

Phase 2 does not implement:

- HOLD, WAIT, or REVIEW classification;
- machine-rule evaluation;
- BUY or SELL classification;
- live market prices;
- exchange or brokerage connections;
- asset price lookup;
- percentage return;
- time-weighted return;
- money-weighted return;
- Modified Dietz return;
- realized/unrealized gain reporting;
- tax lots or tax basis;
- automatic purchase recommendations;
- trade execution.

Those omissions are intentional.

## Phase 2A acceptance requirements

Phase 2A is complete only when:

- this accounting contract is reviewed;
- the core adjusted P/L formula is unambiguous;
- contribution, withdrawal, trade, fee, reward, and correction behavior is explicit;
- snapshot selection and accounting time boundaries are explicit;
- post-snapshot activity behavior is explicit;
- missing/ambiguous current-value behavior is explicit;
- Decimal requirements, exactness context, and derived serialization are explicit;
- timestamp comparisons are defined in terms of parsed timezone-aware instants;
- accounting results include portable-record revision provenance;
- the implementation scenarios are accepted before `portfolio_engine.py` is written;
- no Phase 3 classification or rule-engine behavior is introduced.

After Phase 2A acceptance, Phase 2B may implement the deterministic accounting engine against this contract.
