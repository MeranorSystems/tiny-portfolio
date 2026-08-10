"""Deterministic rules and status engine for Tiny Portfolio.

Phase 3B implements the accepted behavior documented in
``docs/rules-status-contract.md``.

Precondition:
    The input record has already passed Tiny Portfolio JSON Schema and
    structural-semantic validation.

This module evaluates only version 0.1 machine rules and derives the process
status HOLD, WAIT, or REVIEW. It does not interpret guidance notes, fetch market
data, recommend trades, or execute transactions.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, Inexact, Rounded, localcontext
from typing import Any, Iterable, Mapping, Sequence


PORTFOLIO_CHANGING_EVENT_TYPES = frozenset(
    {"contribution", "withdrawal", "trade", "fee", "reward"}
)
SUPPORTED_RULE_TYPES = frozenset(
    {
        "max_contribution_per_period",
        "minimum_days_between_contributions",
        "portfolio_value_review_threshold",
        "milestone_review",
        "scheduled_review_date",
    }
)


class RuleInputError(ValueError):
    """Raised when Phase 3 receives data that violates its preconditions."""


def _parse_timestamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise RuleInputError("timestamp must be a string")

    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise RuleInputError(f"invalid RFC 3339 timestamp: {value}") from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RuleInputError(f"timestamp lacks timezone information: {value}")

    return parsed


def _format_utc(value: datetime) -> str:
    normalized = value.astimezone(timezone.utc)
    return normalized.isoformat().replace("+00:00", "Z")


def _decimal(value: str) -> Decimal:
    if not isinstance(value, str):
        raise RuleInputError("monetary values must be decimal strings")

    try:
        result = Decimal(value)
    except Exception as exc:
        raise RuleInputError(f"invalid decimal string: {value}") from exc

    if not result.is_finite():
        raise RuleInputError(f"non-finite decimal is not supported: {value}")

    return result


def decimal_to_string(value: Decimal) -> str:
    if not isinstance(value, Decimal):
        raise TypeError("decimal_to_string requires Decimal")

    if not value.is_finite():
        raise RuleInputError("non-finite Decimal cannot be serialized")

    if value.is_zero():
        return "0"

    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _decimal_places(value: str) -> int:
    return len(value.partition(".")[2])


def _integer_places(value: str) -> int:
    return len(value.partition(".")[0].lstrip("-"))


def _money_strings(record: Mapping[str, Any]) -> list[str]:
    values: list[str] = []

    for snapshot in record.get("snapshots", []):
        total_value = snapshot.get("total_value")
        if isinstance(total_value, str):
            values.append(total_value)

    for milestone in record.get("milestones", []):
        target_value = milestone.get("target_value")
        if isinstance(target_value, str):
            values.append(target_value)

    for event in record.get("ledger", []):
        if event.get("event_type") != "contribution":
            continue
        amount = event.get("data", {}).get("amount")
        if isinstance(amount, str):
            values.append(amount)

    rules = record.get("rules", {}).get("machine_rules", [])
    for rule in rules:
        config = rule.get("config", {})
        for field in ("amount", "threshold_value"):
            value = config.get(field)
            if isinstance(value, str):
                values.append(value)

    return values


def _required_precision(record: Mapping[str, Any]) -> int:
    values = _money_strings(record)

    if not values:
        return 28

    max_integer_places = max(_integer_places(value) for value in values)
    max_decimal_places = max(_decimal_places(value) for value in values)
    term_count = max(1, len(values))
    carry_places = len(str(term_count))

    return max(
        28,
        max_integer_places + max_decimal_places + carry_places + 4,
    )


def _voided_event_ids(ledger: Sequence[Mapping[str, Any]]) -> frozenset[str]:
    targets: set[str] = set()

    for event in ledger:
        if event.get("event_type") != "correction":
            continue

        data = event.get("data", {})
        if data.get("action") != "void":
            raise RuleInputError("unsupported correction action")

        target_event_id = data.get("target_event_id")
        if not isinstance(target_event_id, str):
            raise RuleInputError("correction target_event_id must be a string")

        targets.add(target_event_id)

    return frozenset(targets)


def _effective_events(
    ledger: Sequence[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    voided = _voided_event_ids(ledger)

    return [
        event
        for event in ledger
        if event.get("event_type") != "correction"
        and event.get("event_id") not in voided
    ]


def _eligible_effective_events(
    effective_events: Sequence[Mapping[str, Any]],
    evaluation_at: datetime,
) -> list[Mapping[str, Any]]:
    return [
        event
        for event in effective_events
        if _parse_timestamp(event["occurred_at"]) <= evaluation_at
    ]


def _select_snapshot(
    snapshots: Sequence[Mapping[str, Any]],
    evaluation_at: datetime,
) -> tuple[Mapping[str, Any] | None, str | None]:
    eligible = [
        snapshot
        for snapshot in snapshots
        if _parse_timestamp(snapshot["captured_at"]) <= evaluation_at
    ]

    if not eligible:
        return None, "missing_confirmed_snapshot"

    latest_captured = max(
        _parse_timestamp(snapshot["captured_at"])
        for snapshot in eligible
    )
    captured_candidates = [
        snapshot
        for snapshot in eligible
        if _parse_timestamp(snapshot["captured_at"]) == latest_captured
    ]

    if len(captured_candidates) == 1:
        return captured_candidates[0], None

    latest_recorded = max(
        _parse_timestamp(snapshot["recorded_at"])
        for snapshot in captured_candidates
    )
    recorded_candidates = [
        snapshot
        for snapshot in captured_candidates
        if _parse_timestamp(snapshot["recorded_at"]) == latest_recorded
    ]

    if len(recorded_candidates) == 1:
        return recorded_candidates[0], None

    values = {_decimal(snapshot["total_value"]) for snapshot in recorded_candidates}
    if len(values) != 1:
        return None, "ambiguous_confirmed_value"

    selected = min(
        recorded_candidates,
        key=lambda snapshot: snapshot["snapshot_id"],
    )
    return selected, None


def _snapshot_states(
    snapshots: Sequence[Mapping[str, Any]],
    evaluation_at: datetime,
) -> list[dict[str, Any]]:
    """Return chronological snapshot states, including ambiguity markers.

    Each unique captured instant contributes one state. Same-capture candidates
    are resolved using greatest recorded_at, then numeric value equality and
    lexicographically smallest snapshot_id.
    """
    eligible = [
        snapshot
        for snapshot in snapshots
        if _parse_timestamp(snapshot["captured_at"]) <= evaluation_at
    ]

    grouped: dict[datetime, list[Mapping[str, Any]]] = {}
    for snapshot in eligible:
        instant = _parse_timestamp(snapshot["captured_at"])
        grouped.setdefault(instant, []).append(snapshot)

    states: list[dict[str, Any]] = []

    for captured_at in sorted(grouped):
        candidates = grouped[captured_at]
        latest_recorded = max(
            _parse_timestamp(snapshot["recorded_at"])
            for snapshot in candidates
        )
        recorded_candidates = [
            snapshot
            for snapshot in candidates
            if _parse_timestamp(snapshot["recorded_at"]) == latest_recorded
        ]

        if len(recorded_candidates) == 1:
            states.append(
                {
                    "captured_at": captured_at,
                    "snapshot": recorded_candidates[0],
                    "ambiguous": False,
                }
            )
            continue

        values = {
            _decimal(snapshot["total_value"])
            for snapshot in recorded_candidates
        }

        if len(values) != 1:
            states.append(
                {
                    "captured_at": captured_at,
                    "snapshot": None,
                    "ambiguous": True,
                }
            )
            continue

        selected = min(
            recorded_candidates,
            key=lambda snapshot: snapshot["snapshot_id"],
        )
        states.append(
            {
                "captured_at": captured_at,
                "snapshot": selected,
                "ambiguous": False,
            }
        )

    return states


def _has_portfolio_activity_after(
    effective_events: Sequence[Mapping[str, Any]],
    after: datetime,
    evaluation_at: datetime,
) -> bool:
    return any(
        event.get("event_type") in PORTFOLIO_CHANGING_EVENT_TYPES
        and after < _parse_timestamp(event["occurred_at"]) <= evaluation_at
        for event in effective_events
    )


def _period_bounds(
    evaluation_at: datetime,
    period: str,
) -> tuple[datetime, datetime]:
    current = evaluation_at.astimezone(timezone.utc)

    if period == "day":
        start = current.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, start + timedelta(days=1)

    if period == "week":
        start_of_day = current.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        start = start_of_day - timedelta(days=start_of_day.weekday())
        return start, start + timedelta(days=7)

    if period == "month":
        start = current.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
        return start, end

    if period == "quarter":
        first_month = ((current.month - 1) // 3) * 3 + 1
        start = current.replace(
            month=first_month,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        if first_month == 10:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=first_month + 3)
        return start, end

    if period == "year":
        start = current.replace(
            month=1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        return start, start.replace(year=start.year + 1)

    raise RuleInputError(f"unsupported contribution period: {period}")


def _rule_result(
    rule: Mapping[str, Any],
    outcome: str,
    reason_code: str,
    evidence: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "rule_id": rule["rule_id"],
        "type": rule["type"],
        "outcome": outcome,
        "reason_code": reason_code,
        "evidence": {} if evidence is None else dict(evidence),
    }


def _evaluate_max_contribution(
    rule: Mapping[str, Any],
    effective_events: Sequence[Mapping[str, Any]],
    evaluation_at: datetime,
) -> dict[str, Any]:
    config = rule["config"]
    limit = _decimal(config["amount"])
    period = config["period"]
    period_start, period_end = _period_bounds(evaluation_at, period)

    contributions = [
        event
        for event in effective_events
        if event.get("event_type") == "contribution"
        and period_start <= _parse_timestamp(event["occurred_at"]) < period_end
        and _parse_timestamp(event["occurred_at"]) <= evaluation_at
    ]

    used = sum(
        (_decimal(event["data"]["amount"]) for event in contributions),
        Decimal(0),
    )

    evidence = {
        "period": period,
        "period_start": _format_utc(period_start),
        "period_end": _format_utc(period_end),
        "limit_amount": decimal_to_string(limit),
        "used_amount": decimal_to_string(used),
    }

    if used < limit:
        evidence["remaining_amount"] = decimal_to_string(limit - used)
        return _rule_result(
            rule,
            "clear",
            "contribution_period_available",
            evidence,
        )

    evidence["wait_until"] = _format_utc(period_end)

    if used == limit:
        reason = "contribution_period_limit_reached"
    else:
        reason = "contribution_period_limit_exceeded"

    return _rule_result(rule, "wait", reason, evidence)


def _evaluate_minimum_days(
    rule: Mapping[str, Any],
    effective_events: Sequence[Mapping[str, Any]],
    evaluation_at: datetime,
) -> dict[str, Any]:
    days = rule["config"]["days"]
    candidates = [
        event
        for event in effective_events
        if event.get("event_type") == "contribution"
        and _parse_timestamp(event["occurred_at"]) <= evaluation_at
    ]

    if not candidates:
        return _rule_result(
            rule,
            "clear",
            "no_prior_contribution",
            {"days": days},
        )

    latest_instant = max(
        _parse_timestamp(event["occurred_at"])
        for event in candidates
    )
    latest_candidates = [
        event
        for event in candidates
        if _parse_timestamp(event["occurred_at"]) == latest_instant
    ]
    latest = min(
        latest_candidates,
        key=lambda event: event["event_id"],
    )
    cooldown_end = latest_instant + timedelta(days=days)

    evidence = {
        "days": days,
        "last_contribution_event_id": latest["event_id"],
        "last_contribution_at": _format_utc(latest_instant),
        "wait_until": _format_utc(cooldown_end),
    }

    if evaluation_at < cooldown_end:
        return _rule_result(
            rule,
            "wait",
            "minimum_contribution_interval_active",
            evidence,
        )

    return _rule_result(
        rule,
        "clear",
        "minimum_contribution_interval_elapsed",
        evidence,
    )


def _evaluate_value_threshold(
    rule: Mapping[str, Any],
    snapshots: Sequence[Mapping[str, Any]],
    effective_events: Sequence[Mapping[str, Any]],
    evaluation_at: datetime,
) -> dict[str, Any]:
    config = rule["config"]
    threshold = _decimal(config["threshold_value"])
    direction = config["direction"]

    selected, selection_reason = _select_snapshot(snapshots, evaluation_at)

    base_evidence = {
        "threshold_value": decimal_to_string(threshold),
        "direction": direction,
    }

    if selected is None:
        return _rule_result(
            rule,
            "wait",
            selection_reason or "missing_confirmed_snapshot",
            base_evidence,
        )

    current_value = _decimal(selected["total_value"])
    captured_at = _parse_timestamp(selected["captured_at"])
    evidence = {
        **base_evidence,
        "snapshot_id": selected["snapshot_id"],
        "snapshot_captured_at": _format_utc(captured_at),
        "current_value": decimal_to_string(current_value),
    }

    if direction == "at_or_above":
        met = current_value >= threshold
    elif direction == "at_or_below":
        met = current_value <= threshold
    else:
        raise RuleInputError(f"unsupported threshold direction: {direction}")

    if met:
        return _rule_result(
            rule,
            "review",
            "portfolio_value_threshold_met",
            evidence,
        )

    if _has_portfolio_activity_after(
        effective_events,
        captured_at,
        evaluation_at,
    ):
        return _rule_result(
            rule,
            "wait",
            "stale_confirmed_value",
            evidence,
        )

    return _rule_result(
        rule,
        "clear",
        "portfolio_value_threshold_not_met",
        evidence,
    )


def _evaluate_scheduled_review(
    rule: Mapping[str, Any],
    evaluation_at: datetime,
) -> dict[str, Any]:
    review_date = date.fromisoformat(rule["config"]["review_date"])
    evaluation_date = evaluation_at.astimezone(timezone.utc).date()

    evidence = {
        "review_date": review_date.isoformat(),
        "evaluation_date_utc": evaluation_date.isoformat(),
    }

    if evaluation_date >= review_date:
        return _rule_result(
            rule,
            "review",
            "scheduled_review_due",
            evidence,
        )

    return _rule_result(
        rule,
        "clear",
        "scheduled_review_not_due",
        evidence,
    )


def _evaluate_milestone(
    rule: Mapping[str, Any],
    milestones: Sequence[Mapping[str, Any]],
    snapshots: Sequence[Mapping[str, Any]],
    effective_events: Sequence[Mapping[str, Any]],
    evaluation_at: datetime,
) -> dict[str, Any]:
    milestone_id = rule["config"]["milestone_id"]

    try:
        milestone = next(
            item
            for item in milestones
            if item["milestone_id"] == milestone_id
        )
    except StopIteration as exc:
        raise RuleInputError(
            f"milestone rule references unknown milestone: {milestone_id}"
        ) from exc

    target = _decimal(milestone["target_value"])
    created_at = _parse_timestamp(milestone["created_at"])
    base_evidence = {
        "milestone_id": milestone_id,
        "target_value": decimal_to_string(target),
        "milestone_created_at": _format_utc(created_at),
    }

    reached_at_raw = milestone.get("reached_at")
    if reached_at_raw is not None:
        reached_at = _parse_timestamp(reached_at_raw)
        if reached_at <= evaluation_at:
            return _rule_result(
                rule,
                "clear",
                "milestone_already_acknowledged",
                {
                    **base_evidence,
                    "reached_at": _format_utc(reached_at),
                },
            )

    states = _snapshot_states(snapshots, evaluation_at)

    if not states:
        return _rule_result(
            rule,
            "wait",
            "missing_confirmed_snapshot",
            base_evidence,
        )

    baseline_states = [
        state
        for state in states
        if state["captured_at"] <= created_at
    ]
    post_creation_states = [
        state
        for state in states
        if state["captured_at"] >= created_at
    ]

    latest_usable_at: datetime | None = None
    history_to_scan: list[dict[str, Any]]
    ambiguous_history_seen = False

    if baseline_states:
        baseline = baseline_states[-1]

        # The latest state at or before milestone creation determines whether
        # the milestone was already satisfied when created. If that state is
        # ambiguous, later history cannot resolve the creation-time fact.
        if baseline["ambiguous"]:
            return _rule_result(
                rule,
                "wait",
                "ambiguous_confirmed_value",
                base_evidence,
            )

        baseline_snapshot = baseline["snapshot"]
        baseline_value = _decimal(baseline_snapshot["total_value"])
        latest_usable_at = baseline["captured_at"]

        baseline_evidence = {
            **base_evidence,
            "baseline_snapshot_id": baseline_snapshot["snapshot_id"],
            "baseline_value": decimal_to_string(baseline_value),
            "baseline_captured_at": _format_utc(baseline["captured_at"]),
        }

        if baseline_value >= target:
            return _rule_result(
                rule,
                "clear",
                "milestone_already_satisfied_at_creation",
                baseline_evidence,
            )

        history_to_scan = [
            state
            for state in post_creation_states
            if state["captured_at"] > baseline["captured_at"]
        ]
    else:
        if not post_creation_states:
            return _rule_result(
                rule,
                "wait",
                "missing_confirmed_snapshot",
                base_evidence,
            )

        # The first *usable* post-creation snapshot establishes the initial
        # observed milestone state. Ambiguous states are not usable, but they
        # are remembered because they could conceal an earlier crossing.
        first_usable_index: int | None = None
        for index, state in enumerate(post_creation_states):
            if state["ambiguous"]:
                ambiguous_history_seen = True
                continue
            first_usable_index = index
            break

        if first_usable_index is None:
            return _rule_result(
                rule,
                "wait",
                "ambiguous_confirmed_value",
                base_evidence,
            )

        first = post_creation_states[first_usable_index]
        first_snapshot = first["snapshot"]
        first_value = _decimal(first_snapshot["total_value"])
        latest_usable_at = first["captured_at"]

        first_evidence = {
            **base_evidence,
            "first_observed_snapshot_id": first_snapshot["snapshot_id"],
            "first_observed_value": decimal_to_string(first_value),
            "first_observed_at": _format_utc(first["captured_at"]),
        }

        if first_value >= target:
            return _rule_result(
                rule,
                "wait",
                "milestone_transition_unknown",
                first_evidence,
            )

        history_to_scan = post_creation_states[first_usable_index + 1 :]

    # At this point we have a definite below-target state. Ambiguous
    # intermediate states do not prevent a later definite at/above state from
    # proving that a crossing occurred. If no later crossing is proven,
    # however, an ambiguous state could conceal a historical crossing, so the
    # result must remain WAIT rather than incorrectly clearing the milestone.
    for state in history_to_scan:
        if state["ambiguous"]:
            ambiguous_history_seen = True
            continue

        current_snapshot = state["snapshot"]
        current_value = _decimal(current_snapshot["total_value"])
        latest_usable_at = state["captured_at"]

        if current_value >= target:
            return _rule_result(
                rule,
                "review",
                "milestone_newly_reached",
                {
                    **base_evidence,
                    "crossing_snapshot_id": current_snapshot["snapshot_id"],
                    "crossing_value": decimal_to_string(current_value),
                    "crossing_at": _format_utc(state["captured_at"]),
                },
            )

    if latest_usable_at is None:
        return _rule_result(
            rule,
            "wait",
            "missing_confirmed_snapshot",
            base_evidence,
        )

    if ambiguous_history_seen:
        return _rule_result(
            rule,
            "wait",
            "ambiguous_confirmed_value",
            {
                **base_evidence,
                "latest_snapshot_at": _format_utc(latest_usable_at),
            },
        )

    if _has_portfolio_activity_after(
        effective_events,
        latest_usable_at,
        evaluation_at,
    ):
        return _rule_result(
            rule,
            "wait",
            "stale_confirmed_value",
            {
                **base_evidence,
                "latest_snapshot_at": _format_utc(latest_usable_at),
            },
        )

    return _rule_result(
        rule,
        "clear",
        "milestone_not_yet_reached",
        {
            **base_evidence,
            "latest_snapshot_at": _format_utc(latest_usable_at),
        },
    )


def evaluate_rules(
    record: Mapping[str, Any],
    evaluation_at: str,
) -> dict[str, Any]:
    """Evaluate version 0.1 rules and derive HOLD, WAIT, or REVIEW."""
    try:
        machine_rules = record["rules"]["machine_rules"]
        milestones = record["milestones"]
        ledger = record["ledger"]
        snapshots = record["snapshots"]
        record_revision = record["metadata"]["record_revision"]
    except (KeyError, TypeError) as exc:
        raise RuleInputError(
            "record does not satisfy the Phase 3 validated-input precondition"
        ) from exc

    if not isinstance(machine_rules, list):
        raise RuleInputError("machine_rules must be an array")
    if not isinstance(milestones, list):
        raise RuleInputError("milestones must be an array")
    if not isinstance(ledger, list):
        raise RuleInputError("ledger must be an array")
    if not isinstance(snapshots, list):
        raise RuleInputError("snapshots must be an array")

    evaluated_at = _parse_timestamp(evaluation_at)
    normalized_evaluated_at = _format_utc(evaluated_at)
    precision = _required_precision(record)

    with localcontext() as context:
        context.prec = precision
        context.traps[Inexact] = True
        context.traps[Rounded] = True

        effective_events = _effective_events(ledger)
        results: list[dict[str, Any]] = []

        for rule in sorted(machine_rules, key=lambda item: item["rule_id"]):
            rule_type = rule["type"]

            if rule_type not in SUPPORTED_RULE_TYPES:
                raise RuleInputError(f"unsupported rule type: {rule_type}")

            if not rule["enabled"]:
                results.append(
                    _rule_result(
                        rule,
                        "ignored",
                        "disabled",
                        {},
                    )
                )
                continue

            if rule_type == "max_contribution_per_period":
                result = _evaluate_max_contribution(
                    rule,
                    effective_events,
                    evaluated_at,
                )
            elif rule_type == "minimum_days_between_contributions":
                result = _evaluate_minimum_days(
                    rule,
                    effective_events,
                    evaluated_at,
                )
            elif rule_type == "portfolio_value_review_threshold":
                result = _evaluate_value_threshold(
                    rule,
                    snapshots,
                    effective_events,
                    evaluated_at,
                )
            elif rule_type == "scheduled_review_date":
                result = _evaluate_scheduled_review(
                    rule,
                    evaluated_at,
                )
            elif rule_type == "milestone_review":
                result = _evaluate_milestone(
                    rule,
                    milestones,
                    snapshots,
                    effective_events,
                    evaluated_at,
                )
            else:
                raise RuleInputError(f"unsupported rule type: {rule_type}")

            results.append(result)

        review_rule_ids = sorted(
            result["rule_id"]
            for result in results
            if result["outcome"] == "review"
        )
        wait_rule_ids = sorted(
            result["rule_id"]
            for result in results
            if result["outcome"] == "wait"
        )

        if review_rule_ids:
            current_status = "REVIEW"
        elif wait_rule_ids:
            current_status = "WAIT"
        else:
            current_status = "HOLD"

        return {
            "current_status": current_status,
            "record_revision": record_revision,
            "evaluated_at": normalized_evaluated_at,
            "review_rule_ids": review_rule_ids,
            "wait_rule_ids": wait_rule_ids,
            "rule_results": results,
        }


__all__ = [
    "RuleInputError",
    "decimal_to_string",
    "evaluate_rules",
]
