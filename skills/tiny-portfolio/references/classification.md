# Tiny Portfolio Classification Reference

Use this reference for machine-rule evaluation and HOLD / WAIT / REVIEW explanations.

The authoritative implementation is `scripts/rules_engine.py`.

## Process status, not trade status

Tiny Portfolio has exactly three v0.1 process statuses:

```text
HOLD
WAIT
REVIEW
```

It must not emit BUY or SELL as current portfolio status.

Global precedence is:

```text
REVIEW > WAIT > HOLD
```

A REVIEW condition therefore remains visible even when another rule is also waiting.

## HOLD

HOLD means no enabled machine rule currently requires REVIEW or WAIT based on validated recorded facts.

HOLD is not:
- a prediction;
- a claim that an asset will rise;
- individualized advice to keep every holding;
- a prohibition on user action.

It is the current Tiny Portfolio process state.

## WAIT

WAIT applies when no enabled rule requires REVIEW, but at least one enabled rule:
- is currently time/limit gated; or
- cannot be safely cleared because required authoritative information is missing, stale, or ambiguous.

WAIT does not promise that an action will become appropriate later.

## REVIEW

REVIEW applies when at least one enabled user-defined review condition is due or proven reached.

REVIEW means evaluate the situation.

It does not mean:
- BUY;
- SELL;
- contribute;
- rebalance.

## Evaluation time

Rule evaluation requires explicit timezone-aware `evaluation_at`.

The engine does not choose the current time itself.

For current requests, use a reliable host/runtime timestamp.

For historical requests, use the user's requested evaluation time.

All rule calendar semantics are UTC.

Future-dated normal events with `occurred_at` after `evaluation_at` do not affect current rule evaluation.

Valid corrections represent the record's corrected history and void their targets for evaluation.

## Rule: max contribution per period

Configuration:
- decimal-string amount;
- period: day, week, month, quarter, or year.

Periods are UTC calendar periods:
- day: UTC calendar day;
- week: Monday through Sunday in UTC;
- month: UTC calendar month;
- quarter: Jan–Mar, Apr–Jun, Jul–Sep, Oct–Dec;
- year: UTC calendar year.

Count effective contribution events by `occurred_at`.

If current-period contributions remain below the maximum, the rule is clear.

At or above the maximum, the rule produces WAIT until the next period boundary.

Exceeding the historical maximum is surfaced with an exceeded reason, but this v0.1 rule remains a current gating rule rather than producing a BUY/SELL-style action.

Remaining contribution allowance is not a recommendation to contribute that amount.

## Rule: minimum days between contributions

Configuration:
- positive integer number of days.

This is exact elapsed time:

```text
latest effective contribution occurred_at + days * 24 hours
```

Before the cooldown end: WAIT.

At the exact cooldown end or later: clear.

No prior contribution: clear.

Do not reinterpret this rule as a market-timing signal.

## Rule: portfolio value review threshold

Configuration:
- threshold value;
- direction `at_or_above` or `at_or_below`.

Use the latest usable confirmed snapshot at or before `evaluation_at`.

If the threshold condition is proven true: REVIEW.

If it is false and the confirmed value remains current enough to evaluate: clear.

If no confirmed snapshot exists: WAIT.

If the required current value is ambiguous: WAIT.

If the snapshot would otherwise clear the rule but portfolio-changing activity occurred after it: WAIT because the value is stale.

A threshold already proven true remains REVIEW even if later activity means the old snapshot may no longer describe the current value; do not suppress a proven review condition.

## Rule: scheduled review date

Configuration:
- UTC calendar date.

Before that date: clear.

On or after that UTC date: REVIEW.

Once due, it remains due until the user changes, disables, removes, or replaces the rule.

## Rule: milestone review

The milestone target and durable `reached_at` history determine whether review is needed.

If `reached_at` is already acknowledged at or before `evaluation_at`: clear.

If the milestone was already at/above target when created: do not fabricate a new achievement review.

A proven below-target state followed by a definite at/above state proves a crossing: REVIEW.

If the first usable post-creation state is already above target and no baseline establishes where the crossing occurred: WAIT because the transition is unknown.

Ambiguous intermediate history does not erase a later crossing that is independently proven by definite states.

If ambiguity could conceal an unacknowledged crossing and no later crossing is proven: WAIT.

Once a crossing is proven, later decline below the target does not erase that historical achievement; it remains REVIEW until acknowledged through the milestone history.

## Disabled rules

Disabled rules are ignored.

A disabled rule does not create WAIT merely because its inputs are missing.

## Reason/evidence output

Use engine evidence to explain:
- which rule triggered;
- whether its outcome is clear, wait, review, or ignored;
- relevant boundary/timestamp;
- snapshot used;
- threshold or limit;
- missing/stale/ambiguous reason.

Keep explanations user-facing. Do not dump implementation detail unless asked.

## Free-form guidance

Guidance notes are not machine rules.

Never say Python enforced a prose note unless that same requirement exists as a supported machine rule.

## Safety guard

Classification is deterministic workflow support.

Do not transform HOLD, WAIT, or REVIEW into asset-selection or trade advice.

Never relabel REVIEW as BUY or SELL to satisfy a user's requested answer.
