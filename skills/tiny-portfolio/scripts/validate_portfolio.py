"""Production validation for Tiny Portfolio schema version 1.0.

Validation is intentionally separate from accounting and rule evaluation.
Records must pass JSON Schema validation and Tiny Portfolio structural-semantic
validation before deterministic engines are run.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:  # pragma: no cover - only in missing-dependency environments.
    Draft202012Validator = None
    FormatChecker = None


DEFAULT_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "tiny-portfolio.schema.json"
)


class ValidationDependencyError(RuntimeError):
    """Raised when a required runtime validation dependency is unavailable."""


class ValidationInputError(ValueError):
    """Raised when a portfolio file cannot be loaded as a JSON object."""


def _parse_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _duplicate_values(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def validate_semantics(record: Mapping[str, Any]) -> list[str]:
    """Return deterministic structural-semantic validation errors."""
    errors: list[str] = []

    portfolio = record.get("portfolio", {})
    base_currency = portfolio.get("base_currency")

    rules = record.get("rules", {})
    machine_rules = rules.get("machine_rules", [])
    guidance_notes = rules.get("guidance_notes", [])
    milestones = record.get("milestones", [])
    ledger = record.get("ledger", [])
    snapshots = record.get("snapshots", [])

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

    for rule in machine_rules:
        if rule.get("type") == "milestone_review":
            milestone_id = rule.get("config", {}).get("milestone_id")
            if milestone_id not in milestone_ids:
                errors.append(
                    f"milestone_review rule {rule.get('rule_id')} references "
                    f"missing milestone: {milestone_id}"
                )

    prior_events: dict[str, Mapping[str, Any]] = {}
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
                        f"correction event {event_id} cannot target correction event "
                        f"{target}"
                    )
                if target in voided_targets:
                    errors.append(
                        f"correction event {event_id} targets already-voided event "
                        f"{target}"
                    )

            if target in prior_events:
                voided_targets.add(target)

        if isinstance(event_id, str):
            prior_events[event_id] = event

        occurred_at = event.get("occurred_at")
        recorded_at = event.get("recorded_at")
        if isinstance(occurred_at, str) and isinstance(recorded_at, str):
            if _parse_datetime(recorded_at) < _parse_datetime(occurred_at):
                errors.append(
                    f"ledger event {event_id} recorded_at is earlier than occurred_at"
                )

    for milestone in milestones:
        created_at = milestone.get("created_at")
        reached_at = milestone.get("reached_at")
        if isinstance(created_at, str) and isinstance(reached_at, str):
            if _parse_datetime(reached_at) < _parse_datetime(created_at):
                errors.append(
                    f"milestone {milestone.get('milestone_id')} reached_at "
                    "is earlier than created_at"
                )

    for snapshot in snapshots:
        snapshot_id = snapshot.get("snapshot_id")
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

    return errors


def _json_path(parts: Sequence[Any]) -> str:
    if not parts:
        return "$"

    result = "$"
    for part in parts:
        if isinstance(part, int):
            result += f"[{part}]"
        else:
            result += f".{part}"
    return result


@lru_cache(maxsize=4)
def _load_validator(schema_path_text: str):
    if Draft202012Validator is None or FormatChecker is None:
        raise ValidationDependencyError(
            "Tiny Portfolio validation requires the 'jsonschema' package."
        )

    schema_path = Path(schema_path_text)
    try:
        with schema_path.open("r", encoding="utf-8") as handle:
            schema = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationInputError(
            f"Unable to load Tiny Portfolio schema: {schema_path}"
        ) from exc

    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(
        schema,
        format_checker=FormatChecker(),
    )


def _schema_errors(
    record: Mapping[str, Any],
    *,
    schema_path: Path,
) -> list[dict[str, str]]:
    validator = _load_validator(str(schema_path.resolve()))
    errors = sorted(
        validator.iter_errors(record),
        key=lambda error: (
            tuple(str(part) for part in error.absolute_path),
            error.validator or "",
            error.message,
        ),
    )
    return [
        {
            "path": _json_path(list(error.absolute_path)),
            "message": error.message,
            "validator": str(error.validator or ""),
        }
        for error in errors
    ]


def validate_portfolio(
    record: Mapping[str, Any],
    *,
    schema_path: Path | str | None = None,
) -> dict[str, Any]:
    """Validate a record and return a deterministic JSON-serializable result."""
    if not isinstance(record, Mapping):
        raise ValidationInputError("Tiny Portfolio record must be a JSON object.")

    resolved_schema = (
        DEFAULT_SCHEMA_PATH
        if schema_path is None
        else Path(schema_path)
    )

    schema_errors = _schema_errors(
        record,
        schema_path=resolved_schema,
    )

    semantic_errors: list[str] = []
    if not schema_errors:
        semantic_errors = validate_semantics(record)

    valid = not schema_errors and not semantic_errors

    return {
        "validation_status": "valid" if valid else "invalid",
        "schema_version": record.get("schema_version"),
        "schema_errors": schema_errors,
        "semantic_errors": semantic_errors,
    }


def load_portfolio(path: Path | str) -> dict[str, Any]:
    """Load one Tiny Portfolio JSON object from disk."""
    record_path = Path(path)
    try:
        with record_path.open("r", encoding="utf-8") as handle:
            record = json.load(handle)
    except OSError as exc:
        raise ValidationInputError(
            f"Unable to read Tiny Portfolio record: {record_path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValidationInputError(
            f"Tiny Portfolio record is not valid JSON: {record_path}"
        ) from exc

    if not isinstance(record, dict):
        raise ValidationInputError("Tiny Portfolio record must be a JSON object.")

    return record


def validate_file(
    path: Path | str,
    *,
    schema_path: Path | str | None = None,
) -> dict[str, Any]:
    return validate_portfolio(
        load_portfolio(path),
        schema_path=schema_path,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate a Tiny Portfolio schema 1.0 record."
    )
    parser.add_argument("record", type=Path)
    parser.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="Optional schema path; defaults to the skill asset.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        result = validate_file(
            args.record,
            schema_path=args.schema,
        )
    except (ValidationDependencyError, ValidationInputError) as exc:
        print(
            json.dumps(
                {
                    "validation_status": "error",
                    "error": str(exc),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["validation_status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "DEFAULT_SCHEMA_PATH",
    "ValidationDependencyError",
    "ValidationInputError",
    "load_portfolio",
    "validate_file",
    "validate_portfolio",
    "validate_semantics",
]
