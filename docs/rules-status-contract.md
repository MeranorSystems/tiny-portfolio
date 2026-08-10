# Tiny Portfolio Rules & Status Contract

**Phase:** 3A — Rules & Status Contract
**Status:** Accepted
**Input contract:** `tiny-portfolio.json` schema version 1.0
**Accounting baseline:** Phase 2 deterministic accounting

## Purpose

This document defines how Tiny Portfolio evaluates version 0.1 machine rules and derives the current process status before rule-engine code is written.

The rule engine is deterministic decision support. It evaluates only the machine-readable rules the user has explicitly stored in the portable record.

It does not interpret free-form guidance as machine rules, predict markets, recommend trades, or classify the portfolio as BUY or SELL.

## Current-status vocabulary

Version 0.1 exposes exactly three current statuses:

- `HOLD`
- `WAIT`
- `REVIEW`

These are **process statuses**, not trading instructions.

### HOLD

`HOLD` means no enabled machine rule currently requires review or waiting based on the validated recorded facts.

It does not mean “never sell,” “do not change the portfolio,” or “the assets are expected to rise.”

### WAIT

`WAIT` means no enabled rule currently requires `REVIEW`, but at least one enabled rule is time-gated or cannot be cleared because required authoritative information is missing, stale, or ambiguous.

Examples include:

- a contribution-period limit has been reached;
- a minimum contribution interval has not elapsed;
- a value-based rule has no usable confirmed snapshot;
- a value-based rule has a stale confirmed value because known portfolio-changing activity occurred later;
- a milestone transition cannot be determined from the available snapshot history.

`WAIT` does not promise that a later contribution or trade will be appropriate. It only describes the current rule state.

### REVIEW

`REVIEW` means at least one enabled user-defined rule has reached a condition that explicitly requests review.

Examples include:

- a portfolio-value review threshold is met;
- a milestone crossing is proven and has not been acknowledged with `reached_at`;
- a scheduled review date is due.

`REVIEW` means **evaluate the situation**. It is not an instruction to buy, sell, convert, stake, withdraw, or contribute.

## Status precedence

When multiple enabled rules produce different outcomes, version 0.1 uses this fixed precedence:

```text
REVIEW > WAIT > HOLD
```

Therefore:

- any `REVIEW` rule makes the global current status `REVIEW`;
- otherwise, any `WAIT` rule makes the global current status `WAIT`;
- otherwise the global current status is `HOLD`.

A waiting/cooldown rule must never suppress a review condition that is already due.

## Evaluation time

The rule engine must receive an explicit timezone-aware `evaluation_at` timestamp from its caller.

The engine must not call the system clock internally to decide rule outcomes.

All timestamp comparisons use parsed timezone-aware instants rather than lexicographic string comparison.

The output normalizes `evaluation_at` to UTC using `Z` notation.

This makes tests and repeated evaluations reproducible.

### Future-dated facts

For operational rule evaluation, normal ledger events and confirmed snapshots whose economic/state time is after `evaluation_at` are ignored until that time is reached.

- ledger rules use `occurred_at`;
- snapshot/value rules use `captured_at`.

`recorded_at` does not move an economic event into a different rule period.

As with Phase 2 accounting, later corrections in the current record may void earlier events because the current portable record represents corrected history.

## Preconditions

Phase 3 operates on a version 1.0 portable record that has already passed:

1. JSON Schema validation; and
2. Tiny Portfolio structural-semantic validation.

The rules engine must not silently repair invalid rule configuration, invalid timestamps, duplicate IDs, broken correction relationships, or invalid milestone references.

## Effective ledger

Rule evaluation uses the same correction-aware effective-ledger concept as Phase 2 accounting.

A normal ledger event is effective when it is not targeted by a valid `correction` event with action `void`.

Correction events themselves do not count as contributions or portfolio-changing activity.

Rules that inspect contribution history must use effective contribution events only.

## Deterministic rule-result ordering

The engine returns a result for every machine rule in the record, including disabled rules.

Rule results are sorted lexicographically by `rule_id` rather than depending on array order.

Each rule result has one of four outcomes:

- `clear`
- `wait`
- `review`
- `ignored`

`ignored` is used for disabled rules and never affects the global current status.

## Disabled rules

A rule with `enabled: false` is not evaluated for a trigger.

Its rule result is:

```text
outcome: ignored
reason_code: disabled
```

Disabled rules do not cause `HOLD`, `WAIT`, or `REVIEW` by themselves.

Free-form `guidance_notes` are not machine rules and do not appear as triggered rule results.

## Contribution rules

### `max_contribution_per_period`

This rule limits outside contributions during the active UTC calendar period.

Supported periods remain those defined by the data contract:

- `day`
- `week`
- `month`
- `quarter`
- `year`

The active period is represented as a half-open interval:

```text
[period_start, period_end)
```

Only effective contribution events satisfying both conditions count:

```text
period_start <= contribution.occurred_at < period_end
contribution.occurred_at <= evaluation_at
```

The engine sums contribution amounts with `Decimal` arithmetic.

#### Clear condition

If:

```text
used_amount < configured_limit
```

then the rule outcome is `clear`.

The result may report the derived remaining allowance:

```text
remaining_amount = configured_limit - used_amount
```

This is accounting evidence, not a recommendation to contribute that amount.

#### Wait condition

If:

```text
used_amount >= configured_limit
```

then the rule outcome is `wait`.

If the total equals the limit, the reason code is:

```text
contribution_period_limit_reached
```

If the effective contribution total is greater than the configured limit, the reason code is:

```text
contribution_period_limit_exceeded
```

The rule result reports `wait_until` as the active UTC period end.

A configured limit of zero therefore produces `wait` for the active period.

This rule does not return `review` in version 0.1.

### `minimum_days_between_contributions`

This rule treats `evaluation_at` as the time at which another contribution is being considered.

The engine finds the most recent effective contribution satisfying:

```text
contribution.occurred_at <= evaluation_at
```

If no prior effective contribution exists, the rule outcome is `clear`.

The cooldown end is:

```text
cooldown_end = most_recent_contribution.occurred_at + (days * 24 hours)
```

#### Wait condition

If:

```text
evaluation_at < cooldown_end
```

then the rule outcome is `wait` with reason code:

```text
minimum_contribution_interval_active
```

The result reports `wait_until = cooldown_end`.

#### Clear boundary

If:

```text
evaluation_at >= cooldown_end
```

then the rule outcome is `clear`.

Equality therefore clears the cooldown.

This rule does not return `review` in version 0.1.

## Confirmed-value selection for value rules

Value-based rules use confirmed snapshots whose:

```text
captured_at <= evaluation_at
```

Snapshot selection follows the Phase 2 deterministic ordering among eligible snapshots:

1. greatest parsed `captured_at` instant;
2. if tied, greatest parsed `recorded_at` instant;
3. if still tied and numeric `total_value` values are equal, lexicographically smallest `snapshot_id` for provenance;
4. if still tied but `total_value` values conflict, the latest confirmed value is ambiguous.

If no eligible confirmed snapshot exists, a value rule cannot be cleared from current authoritative value evidence.

### Stale confirmed value

A selected confirmed value is stale for current-value decisions when an effective portfolio-changing event occurred after the selected snapshot and on or before `evaluation_at`.

Portfolio-changing event types are:

- `contribution`
- `withdrawal`
- `trade`
- `fee`
- `reward`

A `note` or `correction` event does not by itself make the selected value stale.

A later correction can, however, remove the portfolio-changing event that would otherwise have made the snapshot stale.

## `portfolio_value_review_threshold`

This rule evaluates the selected confirmed snapshot `total_value` against the configured threshold.

Directions are:

- `at_or_above`
- `at_or_below`

All value comparisons use `Decimal`.

### Review condition

For `at_or_above`:

```text
current_value >= threshold_value
```

produces `review`.

For `at_or_below`:

```text
current_value <= threshold_value
```

produces `review`.

The review condition is checked against the selected confirmed snapshot before stale-value fallback is considered.

If a confirmed snapshot proves the threshold condition was reached, known later activity must not erase that already-proven review condition.

### Wait conditions

If no eligible confirmed snapshot exists, the outcome is `wait` with reason code:

```text
missing_confirmed_snapshot
```

If latest-snapshot selection is ambiguous because tied snapshots contain conflicting values, the outcome is `wait` with reason code:

```text
ambiguous_confirmed_value
```

If the selected confirmed snapshot does **not** meet the review threshold but known effective portfolio-changing activity occurred after that snapshot and on or before `evaluation_at`, the outcome is `wait` with reason code:

```text
stale_confirmed_value
```

Otherwise the outcome is `clear`.

A threshold rule remains `review` whenever the current selected confirmed snapshot meets its configured condition. It is not a one-shot event and stores no acknowledgement state in version 0.1.

## `scheduled_review_date`

This rule compares the UTC calendar date of `evaluation_at` with the configured `review_date`.

### Clear condition

If:

```text
evaluation_date_utc < review_date
```

then the outcome is `clear`.

### Review condition

If:

```text
evaluation_date_utc >= review_date
```

then the outcome is `review` with reason code:

```text
scheduled_review_due
```

The rule remains due until the user updates, disables, removes, or replaces the rule in the authoritative record.

There is no automatic “review completed” timestamp in schema version 1.0.

This rule does not return `wait` in version 0.1.

## `milestone_review`

This rule requests review for a **proven, unacknowledged milestone crossing**.

The referenced milestone is authoritative and belongs to the same portable record.

A milestone is considered acknowledged when it has `reached_at` at or before `evaluation_at`.

An acknowledged milestone produces `clear` with reason code:

```text
milestone_already_acknowledged
```

### Milestone crossing semantics

A crossing is a transition from a confirmed portfolio value below the milestone target to a confirmed value at or above the target.

A crossing endpoint must satisfy:

```text
snapshot.captured_at >= milestone.created_at
snapshot.captured_at <= evaluation_at
snapshot.total_value >= milestone.target_value
```

The engine evaluates eligible snapshots in chronological state order using parsed `captured_at` instants and the deterministic tie handling defined above.

### Baseline at milestone creation

The engine first looks for the latest usable confirmed snapshot with:

```text
snapshot.captured_at <= milestone.created_at
```

If that baseline exists and its value is already at or above the target, the milestone was already satisfied when created. The rule outcome is `clear` with reason code:

```text
milestone_already_satisfied_at_creation
```

It must not fabricate a newly reached event.

If that baseline exists below the target, it can serve as the initial below-target state for detecting a later crossing.

### No creation-time baseline

If no usable confirmed snapshot exists at or before milestone creation, the first usable post-creation snapshot establishes the initial observed state.

If that first observed state is below the target, later snapshots can prove a crossing normally.

If the first observed state is already at or above the target, the engine cannot determine whether the milestone was crossed after creation or was already satisfied before the first observation. The rule outcome is `wait` with reason code:

```text
milestone_transition_unknown
```

The engine must not guess.

### Proven crossing

Once the ordered usable snapshot history proves a below-to-at/above transition after milestone creation, and `reached_at` is still absent, the rule outcome is `review` with reason code:

```text
milestone_newly_reached
```

That `review` remains due even if a later snapshot falls back below the target. Milestones preserve historical achievement rather than behaving like current-value thresholds.

The review remains due until the authoritative milestone receives `reached_at` or the rule is disabled/removed.

### Missing or ambiguous snapshot history

If there are no usable confirmed snapshots needed to establish milestone state, the outcome is `wait` with reason code:

```text
missing_confirmed_snapshot
```

If a required snapshot state is ambiguous because tied latest-state candidates conflict, the rule outcome is `wait` with reason code:

```text
ambiguous_confirmed_value
```

### Stale history after last snapshot

If no crossing has been proven, but effective portfolio-changing activity occurred after the latest usable snapshot and on or before `evaluation_at`, the milestone rule outcome is `wait` with reason code:

```text
stale_confirmed_value
```

If a crossing has already been proven, the outcome remains `review`; later activity cannot erase a historical crossing.

## Global status derivation

After evaluating every machine rule:

1. collect enabled rule results with outcome `review`;
2. collect enabled rule results with outcome `wait`;
3. derive current status using fixed precedence.

Pseudocode:

```text
if any review results:
    current_status = REVIEW
else if any wait results:
    current_status = WAIT
else:
    current_status = HOLD
```

No asset, market, or guidance-note heuristic may override this precedence.

## Result contract

The Phase 3 engine should return JSON-serializable deterministic output.

Conceptual result:

```json
{
  "current_status": "REVIEW",
  "record_revision": 12,
  "evaluated_at": "2026-08-10T13:00:00Z",
  "review_rule_ids": ["rule_review_001"],
  "wait_rule_ids": ["rule_cooldown_001"],
  "rule_results": [
    {
      "rule_id": "rule_cooldown_001",
      "type": "minimum_days_between_contributions",
      "outcome": "wait",
      "reason_code": "minimum_contribution_interval_active",
      "evidence": {
        "wait_until": "2026-08-15T12:00:00Z"
      }
    },
    {
      "rule_id": "rule_review_001",
      "type": "portfolio_value_review_threshold",
      "outcome": "review",
      "reason_code": "portfolio_value_threshold_met",
      "evidence": {
        "snapshot_id": "snapshot_demo_001",
        "current_value": "75",
        "threshold_value": "75",
        "direction": "at_or_above"
      }
    }
  ]
}
```

### Provenance requirements

Every global result includes:

- `record_revision`;
- normalized UTC `evaluated_at`;
- `review_rule_ids` sorted lexicographically;
- `wait_rule_ids` sorted lexicographically;
- deterministic `rule_results` sorted lexicographically by `rule_id`.

Rule evidence must contain only authoritative facts and deterministic derived values relevant to explaining that rule result.

The engine must not write derived rule results or current status back into `tiny-portfolio.json`.

## Reason-code baseline

Initial version 0.1 reason codes include:

```text
disabled
contribution_period_available
contribution_period_limit_reached
contribution_period_limit_exceeded
no_prior_contribution
minimum_contribution_interval_active
minimum_contribution_interval_elapsed
portfolio_value_threshold_met
portfolio_value_threshold_not_met
missing_confirmed_snapshot
ambiguous_confirmed_value
stale_confirmed_value
scheduled_review_not_due
scheduled_review_due
milestone_already_acknowledged
milestone_already_satisfied_at_creation
milestone_not_yet_reached
milestone_transition_unknown
milestone_newly_reached
```

Reason codes are machine-stable identifiers. Human-readable explanations may be added separately and must not change the deterministic meaning of the code.

## Decimal requirements

All monetary arithmetic and comparisons use Python `decimal.Decimal` with the same exactness requirements established by Phase 2.

No rule may use binary floating-point arithmetic for money.

Derived decimal evidence is serialized using the Phase 2 canonical plain-decimal format.

## No BUY or SELL classification

Version 0.1 must never emit any of the following as current status, rule outcome, or reason code:

- `BUY`
- `SELL`
- automatic purchase instruction;
- automatic sale instruction.

`HOLD`, `WAIT`, and `REVIEW` are process classifications only.

## Required Phase 3 test scenarios

The implementation must eventually prove at least these synthetic cases:

### Global status

- no enabled trigger -> `HOLD`;
- one waiting rule -> `WAIT`;
- one review rule -> `REVIEW`;
- simultaneous wait and review -> `REVIEW`;
- disabled rules never affect global status;
- rule array reordering does not change deterministic output ordering.

### Maximum contribution per period

- below limit -> clear;
- exactly at limit -> wait;
- above limit -> wait with exceeded reason;
- corrected/voided contribution does not count;
- event at the exact UTC period start counts;
- event at the next period start does not count in the prior period;
- future contribution after `evaluation_at` does not count yet.

### Minimum contribution interval

- no prior contribution -> clear;
- inside cooldown -> wait;
- exact cooldown end -> clear;
- corrected/voided contribution is ignored;
- future contribution is ignored.

### Portfolio value threshold

- at-or-above below threshold -> clear;
- exact at-or-above threshold -> review;
- at-or-below above threshold -> clear;
- exact at-or-below threshold -> review;
- missing snapshot -> wait;
- conflicting latest snapshots -> wait;
- stale snapshot below threshold -> wait;
- threshold already proven at selected snapshot remains review despite later activity;
- equivalent timezone offsets compare as the same instant.

### Scheduled review

- day before -> clear;
- exact UTC review date -> review;
- later date -> review;
- disabled scheduled rule -> ignored.

### Milestone review

- acknowledged `reached_at` -> clear;
- target already satisfied at milestone creation -> clear without fabricated crossing;
- creation baseline below + later crossing -> review;
- first observed post-creation state above with no baseline -> wait/unknown;
- below-target history without crossing -> clear;
- proven crossing remains review after later value decline;
- stale value without proven crossing -> wait;
- corrected history is honored where applicable.

### Safety and determinism

- no output contains BUY or SELL classifications;
- source record is not mutated;
- same input + same `evaluation_at` produces identical output;
- output is JSON serializable;
- `record_revision` is preserved as provenance.

## Out of scope for Phase 3

Phase 3 does not implement:

- natural-language interpretation of guidance notes;
- discretionary asset recommendations;
- BUY or SELL classification;
- live market data;
- price forecasts;
- automatic trading;
- brokerage/exchange connections;
- check-in conversation flows;
- screenshot extraction;
- persistence changes to acknowledge reviews automatically.

Those belong elsewhere or are intentionally excluded.

## Phase 3A acceptance requirements

Phase 3A is complete only when:

- the three status meanings are accepted;
- `REVIEW > WAIT > HOLD` precedence is accepted;
- evaluation time is explicit and deterministic;
- disabled-rule behavior is explicit;
- each of the five machine-rule types has deterministic semantics;
- missing, stale, and ambiguous data behavior is explicit;
- milestone crossing and acknowledgement behavior is explicit;
- result ordering, evidence, and provenance are explicit;
- Decimal behavior is consistent with Phase 2;
- required synthetic scenarios are accepted;
- BUY and SELL classifications are explicitly prohibited;
- no Phase 3B engine code is written before this contract is accepted.

After Phase 3A acceptance, Phase 3B may implement the deterministic rules/status engine against this contract.
