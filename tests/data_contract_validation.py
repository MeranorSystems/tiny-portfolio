"""Structural semantic validation for Tiny Portfolio schema version 1.0.

This module deliberately performs no portfolio accounting. It validates
relationships that JSON Schema cannot express cleanly across collections.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


def _parse_datetime(value: str) -> datetime:
    # Python 3.11 accepts RFC 3339 UTC timestamps ending in Z.
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _duplicate_values(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def validate_semantics(record: dict[str, Any]) -> list[str]:
    """Return deterministic human-readable structural semantic errors."""
    errors: list[str] = []

    portfolio = record.get("portfolio", {})
    base_currency = portfolio.get("base_currency")

    rules = record.get("rules", {})
    machine_rules = rules.get("machine_rules", [])
    guidance_notes = rules.get("guidance_notes", [])
    milestones = record.get("milestones", [])
    ledger = record.get("ledger", [])
    snapshots = record.get("snapshots", [])
    metadata = record.get("metadata", {})

    # IDs must be unique within each collection.
    collections = [
        ("machine rule", [item.get("rule_id") for item in machine_rules]),
        ("guidance note", [item.get("note_id") for item in guidance_notes]),
        ("milestone", [item.get("milestone_id") for item in milestones]),
        ("ledger event", [item.get("event_id") for item in ledger]),
        ("snapshot", [item.get("snapshot_id") for item in snapshots]),
    ]

    for label, values in collections:
        concrete = [value for value in values if isinstance(value, str)]
        for duplicate in _duplicate_values(concrete):
            errors.append(f"duplicate {label} id: {duplicate}")

    milestone_ids = {
        item.get("milestone_id")
        for item in milestones
        if isinstance(item.get("milestone_id"), str)
    }

    # Rule references.
    for rule in machine_rules:
        if rule.get("type") == "milestone_review":
            milestone_id = rule.get("config", {}).get("milestone_id")
            if milestone_id not in milestone_ids:
                errors.append(
                    f"milestone_review rule {rule.get('rule_id')} references "
                    f"missing milestone: {milestone_id}"
                )

    # Currency consistency and append-oriented correction references.
    prior_events: dict[str, dict[str, Any]] = {}
    voided_targets: set[str] = set()

    currency_event_types = {"contribution", "withdrawal", "fee", "reward"}

    for event in ledger:
        event_id = event.get("event_id")
        event_type = event.get("event_type")
        data = event.get("data", {})

        if event_type in currency_event_types:
            event_currency = data.get("currency")
            if (
                isinstance(base_currency, str)
                and isinstance(event_currency, str)
                and event_currency != base_currency
            ):
                errors.append(
                    f"ledger event {event_id} currency {event_currency} "
                    f"does not match portfolio base currency {base_currency}"
                )

        if event_type == "correction":
            target = data.get("target_event_id")

            if target == event_id:
                errors.append(f"correction event {event_id} cannot target itself")
            elif target not in prior_events:
                errors.append(
                    f"correction event {event_id} references missing or "
                    f"non-prior event: {target}"
                )
            else:
                target_event = prior_events[target]
                if target_event.get("event_type") == "correction":
                    errors.append(
                        f"correction event {event_id} cannot target correction event {target}"
                    )
                if target in voided_targets:
                    errors.append(
                        f"correction event {event_id} targets already-voided event {target}"
                    )

            if target in prior_events:
                voided_targets.add(target)

        if isinstance(event_id, str):
            prior_events[event_id] = event

        # Basic event timestamp ordering.
        occurred_at = event.get("occurred_at")
        recorded_at = event.get("recorded_at")
        if isinstance(occurred_at, str) and isinstance(recorded_at, str):
            if _parse_datetime(recorded_at) < _parse_datetime(occurred_at):
                errors.append(
                    f"ledger event {event_id} recorded_at is earlier than occurred_at"
                )

    # Milestone timestamp ordering.
    for milestone in milestones:
        created_at = milestone.get("created_at")
        reached_at = milestone.get("reached_at")
        if isinstance(created_at, str) and isinstance(reached_at, str):
            if _parse_datetime(reached_at) < _parse_datetime(created_at):
                errors.append(
                    f"milestone {milestone.get('milestone_id')} reached_at "
                    "is earlier than created_at"
                )

    # Snapshot timestamp ordering.
    snapshot_ids: set[str] = set()
    for snapshot in snapshots:
        snapshot_id = snapshot.get("snapshot_id")
        if isinstance(snapshot_id, str):
            snapshot_ids.add(snapshot_id)

        captured_at = snapshot.get("captured_at")
        recorded_at = snapshot.get("recorded_at")
        confirmed_at = snapshot.get("confirmation", {}).get("confirmed_at")

        if (
            isinstance(captured_at, str)
            and isinstance(recorded_at, str)
            and _parse_datetime(recorded_at) < _parse_datetime(captured_at)
        ):
            errors.append(
                f"snapshot {snapshot_id} recorded_at is earlier than captured_at"
            )

        if isinstance(captured_at, str) and isinstance(confirmed_at, str):
            if _parse_datetime(confirmed_at) < _parse_datetime(captured_at):
                errors.append(
                    f"snapshot {snapshot_id} confirmed_at is earlier than captured_at"
                )

        if isinstance(recorded_at, str) and isinstance(confirmed_at, str):
            if _parse_datetime(confirmed_at) > _parse_datetime(recorded_at):
                errors.append(
                    f"snapshot {snapshot_id} confirmed_at is later than recorded_at"
                )

    last_snapshot_id = metadata.get("last_confirmed_snapshot_id")
    if isinstance(last_snapshot_id, str) and last_snapshot_id not in snapshot_ids:
        errors.append(
            "metadata.last_confirmed_snapshot_id references missing snapshot: "
            f"{last_snapshot_id}"
        )

    return errors
