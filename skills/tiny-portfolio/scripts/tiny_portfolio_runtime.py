"""Deterministic runtime orchestration for the Tiny Portfolio skill.

This module does not contain portfolio math or rule logic. It validates first,
then delegates to the accepted Phase 2 and Phase 3 engines.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent


def _load_sibling_module(module_name: str):
    path = SCRIPT_DIR / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(
        f"tiny_portfolio_runtime_{module_name}",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load Tiny Portfolio runtime module: {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_validator = _load_sibling_module("validate_portfolio")
_accounting = _load_sibling_module("portfolio_engine")
_rules = _load_sibling_module("rules_engine")

load_portfolio = _validator.load_portfolio
validate_portfolio = _validator.validate_portfolio
calculate_accounting = _accounting.calculate_accounting
evaluate_rules = _rules.evaluate_rules


def analyze_portfolio(
    record: Mapping[str, Any],
    *,
    evaluation_at: str | None = None,
) -> dict[str, Any]:
    """Validate first, then return deterministic accounting and optional status."""
    validation = validate_portfolio(record)

    if validation["validation_status"] != "valid":
        return {
            "analysis_status": "invalid_record",
            "validation": validation,
            "accounting": None,
            "rules_status": None,
        }

    accounting = calculate_accounting(record)
    rules_status = (
        None
        if evaluation_at is None
        else evaluate_rules(record, evaluation_at)
    )

    return {
        "analysis_status": "available",
        "validation": validation,
        "accounting": accounting,
        "rules_status": rules_status,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate and analyze a Tiny Portfolio record with deterministic "
            "accounting and optional rules/status evaluation."
        )
    )
    parser.add_argument("record", type=Path)
    parser.add_argument(
        "--evaluation-at",
        default=None,
        help=(
            "Timezone-aware RFC 3339 timestamp. When omitted, rules/status "
            "evaluation is not run."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    record = load_portfolio(args.record)

    result = analyze_portfolio(
        record,
        evaluation_at=args.evaluation_at,
    )
    print(json.dumps(result, indent=2, sort_keys=True))

    return 0 if result["analysis_status"] == "available" else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["analyze_portfolio"]
