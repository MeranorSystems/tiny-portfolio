"""Deterministic accounting engine for Tiny Portfolio.

Phase 2B implements the accepted accounting behavior documented in
``docs/accounting-contract.md``.

Precondition:
    The input record has already passed the Tiny Portfolio JSON Schema and
    structural-semantic validation.

This module performs portfolio tracking calculations only. It does not evaluate
portfolio rules, classify HOLD/WAIT/REVIEW, fetch prices, or execute trades.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, Inexact, Rounded, localcontext
from typing import Any, Iterable, Mapping, Sequence


PORTFOLIO_CHANGING_EVENT_TYPES = frozenset(
    {"contribution", "withdrawal", "trade", "fee", "reward"}
)
MONEY_EVENT_TYPES = frozenset(
    {"contribution", "withdrawal", "fee", "reward"}
)


class AccountingInputError(ValueError):
    """Raised when Phase 2 receives data that violates its validated precondition."""


def _parse_timestamp(value: str) -> datetime:
    """Parse an RFC 3339 timestamp into a timezone-aware instant."""
    if not isinstance(value, str):
        raise AccountingInputError("timestamp must be a string")

    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise AccountingInputError(f"invalid RFC 3339 timestamp: {value}") from exc

    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise AccountingInputError(f"timestamp lacks timezone information: {value}")

    return parsed


def _decimal(value: str) -> Decimal:
    """Convert a schema-valid decimal string directly to Decimal."""
    if not isinstance(value, str):
        raise AccountingInputError("monetary values must be decimal strings")

    try:
        result = Decimal(value)
    except Exception as exc:
        raise AccountingInputError(f"invalid decimal string: {value}") from exc

    if not result.is_finite():
        raise AccountingInputError(f"non-finite decimal is not supported: {value}")

    return result


def decimal_to_string(value: Decimal) -> str:
    """Serialize Decimal using canonical plain-decimal notation."""
    if not isinstance(value, Decimal):
        raise TypeError("decimal_to_string requires Decimal")

    if not value.is_finite():
        raise AccountingInputError("non-finite Decimal cannot be serialized")

    if value.is_zero():
        return "0"

    text = format(value, "f")

    if "." in text:
        text = text.rstrip("0").rstrip(".")

    return text


def _decimal_places(value: str) -> int:
    return len(value.partition(".")[2])


def _integer_places(value: str) -> int:
    integer_part = value.partition(".")[0]
    return len(integer_part.lstrip("-"))


def _money_strings(record: Mapping[str, Any]) -> list[str]:
    """Collect every monetary source string that can participate in Phase 2."""
    values: list[str] = []

    for snapshot in record.get("snapshots", []):
        total_value = snapshot.get("total_value")
        if isinstance(total_value, str):
            values.append(total_value)

    for event in record.get("ledger", []):
        if event.get("event_type") not in MONEY_EVENT_TYPES:
            continue
        amount = event.get("data", {}).get("amount")
        if isinstance(amount, str):
            values.append(amount)

    return values


def _required_precision(record: Mapping[str, Any]) -> int:
    """Choose a Decimal precision sufficient for exact Phase 2 accumulation."""
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
    """Return IDs of normal events voided by correction events."""
    targets: set[str] = set()

    for event in ledger:
        if event.get("event_type") != "correction":
            continue

        data = event.get("data", {})
        if data.get("action") != "void":
            raise AccountingInputError("unsupported correction action")

        target = data.get("target_event_id")
        if not isinstance(target, str):
            raise AccountingInputError("correction target_event_id must be a string")

        targets.add(target)

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


def _select_snapshot(
    snapshots: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any] | None, str | None]:
    """Select the latest confirmed state according to the Phase 2A contract."""
    if not snapshots:
        return None, "no_confirmed_snapshot"

    captured_instants = [
        (_parse_timestamp(snapshot["captured_at"]), snapshot)
        for snapshot in snapshots
    ]
    latest_captured = max(instant for instant, _ in captured_instants)
    captured_candidates = [
        snapshot
        for instant, snapshot in captured_instants
        if instant == latest_captured
    ]

    if len(captured_candidates) == 1:
        return captured_candidates[0], None

    recorded_instants = [
        (_parse_timestamp(snapshot["recorded_at"]), snapshot)
        for snapshot in captured_candidates
    ]
    latest_recorded = max(instant for instant, _ in recorded_instants)
    recorded_candidates = [
        snapshot
        for instant, snapshot in recorded_instants
        if instant == latest_recorded
    ]

    if len(recorded_candidates) == 1:
        return recorded_candidates[0], None

    values = {_decimal(snapshot["total_value"]) for snapshot in recorded_candidates}
    if len(values) != 1:
        return None, "ambiguous_latest_snapshot"

    selected = min(recorded_candidates, key=lambda snapshot: snapshot["snapshot_id"])
    return selected, None


def _sum_event_amounts(
    events: Iterable[Mapping[str, Any]],
    event_type: str,
    *,
    on_or_before: datetime | None = None,
) -> Decimal:
    total = Decimal(0)

    for event in events:
        if event.get("event_type") != event_type:
            continue

        if on_or_before is not None:
            occurred_at = _parse_timestamp(event["occurred_at"])
            if occurred_at > on_or_before:
                continue

        total += _decimal(event["data"]["amount"])

    return total


def _all_record_totals(
    effective_events: Sequence[Mapping[str, Any]],
) -> dict[str, Decimal]:
    return {
        "total_contributions_recorded": _sum_event_amounts(
            effective_events, "contribution"
        ),
        "total_withdrawals_recorded": _sum_event_amounts(
            effective_events, "withdrawal"
        ),
        "known_fees_total": _sum_event_amounts(effective_events, "fee"),
        "known_rewards_total": _sum_event_amounts(effective_events, "reward"),
    }


def _serialize_totals(totals: Mapping[str, Decimal]) -> dict[str, str]:
    return {
        name: decimal_to_string(value)
        for name, value in totals.items()
    }


def calculate_accounting(record: Mapping[str, Any]) -> dict[str, Any]:
    """Calculate deterministic Phase 2 accounting from a validated record."""
    try:
        base_currency = record["portfolio"]["base_currency"]
        record_revision = record["metadata"]["record_revision"]
        ledger = record["ledger"]
        snapshots = record["snapshots"]
    except (KeyError, TypeError) as exc:
        raise AccountingInputError(
            "record does not satisfy the Phase 2 validated-input precondition"
        ) from exc

    if not isinstance(ledger, list) or not isinstance(snapshots, list):
        raise AccountingInputError("ledger and snapshots must be arrays")

    precision = _required_precision(record)

    with localcontext() as context:
        context.prec = precision
        context.traps[Inexact] = True
        context.traps[Rounded] = True

        effective_events = _effective_events(ledger)
        all_record_totals = _all_record_totals(effective_events)
        selected_snapshot, unavailable_reason = _select_snapshot(snapshots)

        result: dict[str, Any] = {
            "calculation_status": (
                "unavailable" if unavailable_reason is not None else "available"
            ),
            "record_revision": record_revision,
            "base_currency": base_currency,
            **_serialize_totals(all_record_totals),
        }

        if selected_snapshot is None:
            result.update(
                {
                    "reason": unavailable_reason,
                    "snapshot_id": None,
                    "as_of": None,
                    "current_confirmed_value": None,
                    "total_contributions_as_of": None,
                    "total_withdrawals_as_of": None,
                    "net_outside_capital_as_of": None,
                    "adjusted_profit_loss": None,
                    "known_fees_as_of": None,
                    "known_rewards_as_of": None,
                    "has_post_snapshot_activity": None,
                    "post_snapshot_activity_count": None,
                }
            )
            return result

        as_of = _parse_timestamp(selected_snapshot["captured_at"])

        contributions_as_of = _sum_event_amounts(
            effective_events, "contribution", on_or_before=as_of
        )
        withdrawals_as_of = _sum_event_amounts(
            effective_events, "withdrawal", on_or_before=as_of
        )
        fees_as_of = _sum_event_amounts(
            effective_events, "fee", on_or_before=as_of
        )
        rewards_as_of = _sum_event_amounts(
            effective_events, "reward", on_or_before=as_of
        )

        net_outside_capital = contributions_as_of - withdrawals_as_of
        current_value = _decimal(selected_snapshot["total_value"])
        adjusted_profit_loss = (
            current_value + withdrawals_as_of - contributions_as_of
        )

        post_snapshot_events = [
            event
            for event in effective_events
            if event.get("event_type") in PORTFOLIO_CHANGING_EVENT_TYPES
            and _parse_timestamp(event["occurred_at"]) > as_of
        ]

        result.update(
            {
                "snapshot_id": selected_snapshot["snapshot_id"],
                "as_of": selected_snapshot["captured_at"],
                "current_confirmed_value": decimal_to_string(current_value),
                "total_contributions_as_of": decimal_to_string(
                    contributions_as_of
                ),
                "total_withdrawals_as_of": decimal_to_string(
                    withdrawals_as_of
                ),
                "net_outside_capital_as_of": decimal_to_string(
                    net_outside_capital
                ),
                "adjusted_profit_loss": decimal_to_string(
                    adjusted_profit_loss
                ),
                "known_fees_as_of": decimal_to_string(fees_as_of),
                "known_rewards_as_of": decimal_to_string(rewards_as_of),
                "has_post_snapshot_activity": bool(post_snapshot_events),
                "post_snapshot_activity_count": len(post_snapshot_events),
            }
        )

        return result


__all__ = [
    "AccountingInputError",
    "calculate_accounting",
    "decimal_to_string",
]
