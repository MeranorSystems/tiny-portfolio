from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = (
    REPO_ROOT
    / "skills"
    / "tiny-portfolio"
    / "scripts"
    / "rules_engine.py"
)

_spec = importlib.util.spec_from_file_location(
    "tiny_portfolio_rules_engine",
    ENGINE_PATH,
)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"Unable to load rules engine from {ENGINE_PATH}")

_engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_engine)

RuleInputError = _engine.RuleInputError
evaluate_rules = _engine.evaluate_rules


def make_record(
    *,
    rules: list[dict] | None = None,
    ledger: list[dict] | None = None,
    snapshots: list[dict] | None = None,
    milestones: list[dict] | None = None,
    revision: int = 1,
) -> dict:
    return {
        "schema_version": "1.0",
        "portfolio": {
            "portfolio_id": "portfolio_synthetic_001",
            "name": "Synthetic Portfolio",
            "base_currency": "USD",
            "created_at": "2026-08-01T00:00:00Z",
        },
        "rules": {
            "machine_rules": [] if rules is None else rules,
            "guidance_notes": [],
        },
        "milestones": [] if milestones is None else milestones,
        "ledger": [] if ledger is None else ledger,
        "snapshots": [] if snapshots is None else snapshots,
        "metadata": {
            "record_revision": revision,
            "updated_at": "2026-08-10T00:00:00Z",
        },
    }


def make_rule(
    rule_id: str,
    rule_type: str,
    config: dict,
    *,
    enabled: bool = True,
) -> dict:
    return {
        "rule_id": rule_id,
        "type": rule_type,
        "enabled": enabled,
        "created_at": "2026-08-01T00:00:00Z",
        "config": config,
    }


def make_event(
    event_id: str,
    event_type: str,
    *,
    occurred_at: str,
    data: dict,
    recorded_at: str | None = None,
) -> dict:
    return {
        "event_id": event_id,
        "event_type": event_type,
        "occurred_at": occurred_at,
        "recorded_at": recorded_at or occurred_at,
        "source": "guided",
        "data": data,
    }


def contribution(
    event_id: str,
    amount: str,
    occurred_at: str,
    *,
    recorded_at: str | None = None,
) -> dict:
    return make_event(
        event_id,
        "contribution",
        occurred_at=occurred_at,
        recorded_at=recorded_at,
        data={"amount": amount, "currency": "USD"},
    )


def withdrawal(
    event_id: str,
    amount: str,
    occurred_at: str,
) -> dict:
    return make_event(
        event_id,
        "withdrawal",
        occurred_at=occurred_at,
        data={"amount": amount, "currency": "USD"},
    )


def fee(
    event_id: str,
    amount: str,
    occurred_at: str,
) -> dict:
    return make_event(
        event_id,
        "fee",
        occurred_at=occurred_at,
        data={"amount": amount, "currency": "USD"},
    )


def reward(
    event_id: str,
    amount: str,
    occurred_at: str,
) -> dict:
    return make_event(
        event_id,
        "reward",
        occurred_at=occurred_at,
        data={
            "reward_type": "staking",
            "amount": amount,
            "currency": "USD",
        },
    )


def trade(
    event_id: str,
    occurred_at: str,
) -> dict:
    return make_event(
        event_id,
        "trade",
        occurred_at=occurred_at,
        data={
            "from_asset": "USD",
            "to_asset": "BTC",
            "from_quantity": "5",
            "to_quantity": "0.00004",
        },
    )


def note(
    event_id: str,
    occurred_at: str,
) -> dict:
    return make_event(
        event_id,
        "note",
        occurred_at=occurred_at,
        data={"text": "Synthetic note."},
    )


def correction(
    event_id: str,
    target_event_id: str,
    occurred_at: str,
) -> dict:
    return make_event(
        event_id,
        "correction",
        occurred_at=occurred_at,
        data={
            "target_event_id": target_event_id,
            "action": "void",
            "reason": "Synthetic correction.",
        },
    )


def snapshot(
    snapshot_id: str,
    total_value: str,
    captured_at: str,
    *,
    recorded_at: str | None = None,
) -> dict:
    recorded_at = recorded_at or captured_at
    return {
        "snapshot_id": snapshot_id,
        "captured_at": captured_at,
        "recorded_at": recorded_at,
        "total_value": total_value,
        "holdings": [
            {
                "symbol": "USD",
                "name": "Cash",
                "asset_type": "cash",
                "value": total_value,
            }
        ],
        "source": "guided",
        "confirmation": {"confirmed_at": recorded_at},
    }


def milestone(
    milestone_id: str = "milestone_001",
    *,
    target_value: str = "75",
    created_at: str = "2026-08-05T00:00:00Z",
    reached_at: str | None = None,
) -> dict:
    result = {
        "milestone_id": milestone_id,
        "label": "Synthetic checkpoint",
        "target_value": target_value,
        "created_at": created_at,
    }
    if reached_at is not None:
        result["reached_at"] = reached_at
    return result


class TinyPortfolioRulesStatusTests(unittest.TestCase):
    def test_no_enabled_triggers_is_hold(self) -> None:
        result = evaluate_rules(
            make_record(),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "HOLD")

    def test_one_wait_rule_is_wait(self) -> None:
        rule = make_rule(
            "rule_001",
            "minimum_days_between_contributions",
            {"days": 2},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                ledger=[
                    contribution(
                        "event_001",
                        "5",
                        "2026-08-10T11:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "WAIT")

    def test_one_review_rule_is_review(self) -> None:
        rule = make_rule(
            "rule_001",
            "scheduled_review_date",
            {"review_date": "2026-08-10"},
        )
        result = evaluate_rules(
            make_record(rules=[rule]),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "REVIEW")

    def test_review_precedes_wait(self) -> None:
        wait_rule = make_rule(
            "rule_wait",
            "minimum_days_between_contributions",
            {"days": 2},
        )
        review_rule = make_rule(
            "rule_review",
            "scheduled_review_date",
            {"review_date": "2026-08-10"},
        )
        result = evaluate_rules(
            make_record(
                rules=[wait_rule, review_rule],
                ledger=[
                    contribution(
                        "event_001",
                        "5",
                        "2026-08-10T11:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "REVIEW")
        self.assertEqual(result["wait_rule_ids"], ["rule_wait"])
        self.assertEqual(result["review_rule_ids"], ["rule_review"])

    def test_disabled_rule_is_ignored(self) -> None:
        rule = make_rule(
            "rule_001",
            "scheduled_review_date",
            {"review_date": "2026-08-01"},
            enabled=False,
        )
        result = evaluate_rules(
            make_record(rules=[rule]),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "HOLD")
        self.assertEqual(result["rule_results"][0]["outcome"], "ignored")
        self.assertEqual(result["rule_results"][0]["reason_code"], "disabled")

    def test_rule_results_are_sorted_by_rule_id(self) -> None:
        rules = [
            make_rule(
                "rule_z",
                "scheduled_review_date",
                {"review_date": "2026-08-11"},
            ),
            make_rule(
                "rule_a",
                "scheduled_review_date",
                {"review_date": "2026-08-11"},
            ),
        ]
        result = evaluate_rules(
            make_record(rules=rules),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(
            [item["rule_id"] for item in result["rule_results"]],
            ["rule_a", "rule_z"],
        )

    def test_evaluation_at_is_normalized_to_utc(self) -> None:
        result = evaluate_rules(
            make_record(),
            "2026-08-10T07:00:00-05:00",
        )
        self.assertEqual(result["evaluated_at"], "2026-08-10T12:00:00Z")

    def test_max_contribution_below_limit_is_clear(self) -> None:
        rule = make_rule(
            "rule_001",
            "max_contribution_per_period",
            {"amount": "10", "period": "week"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                ledger=[
                    contribution(
                        "event_001",
                        "9.99",
                        "2026-08-10T10:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        item = result["rule_results"][0]
        self.assertEqual(item["outcome"], "clear")
        self.assertEqual(
            item["reason_code"],
            "contribution_period_available",
        )
        self.assertEqual(item["evidence"]["remaining_amount"], "0.01")

    def test_max_contribution_exact_limit_is_wait(self) -> None:
        rule = make_rule(
            "rule_001",
            "max_contribution_per_period",
            {"amount": "10", "period": "week"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                ledger=[
                    contribution(
                        "event_001",
                        "10",
                        "2026-08-10T10:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        item = result["rule_results"][0]
        self.assertEqual(item["outcome"], "wait")
        self.assertEqual(
            item["reason_code"],
            "contribution_period_limit_reached",
        )

    def test_max_contribution_above_limit_uses_exceeded_reason(self) -> None:
        rule = make_rule(
            "rule_001",
            "max_contribution_per_period",
            {"amount": "10", "period": "week"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                ledger=[
                    contribution(
                        "event_001",
                        "10.01",
                        "2026-08-10T10:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(
            result["rule_results"][0]["reason_code"],
            "contribution_period_limit_exceeded",
        )

    def test_zero_contribution_limit_waits_even_with_no_activity(self) -> None:
        rule = make_rule(
            "rule_001",
            "max_contribution_per_period",
            {"amount": "0", "period": "day"},
        )
        result = evaluate_rules(
            make_record(rules=[rule]),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "WAIT")
        self.assertEqual(
            result["rule_results"][0]["reason_code"],
            "contribution_period_limit_reached",
        )

    def test_voided_contribution_does_not_count_toward_limit(self) -> None:
        rule = make_rule(
            "rule_001",
            "max_contribution_per_period",
            {"amount": "10", "period": "week"},
        )
        record = make_record(
            rules=[rule],
            ledger=[
                contribution(
                    "event_001",
                    "10",
                    "2026-08-10T10:00:00Z",
                ),
                correction(
                    "event_002",
                    "event_001",
                    "2026-08-11T10:00:00Z",
                ),
            ],
        )
        result = evaluate_rules(
            record,
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "HOLD")
        self.assertEqual(
            result["rule_results"][0]["evidence"]["used_amount"],
            "0",
        )

    def test_day_period_exact_start_counts(self) -> None:
        rule = make_rule(
            "rule_001",
            "max_contribution_per_period",
            {"amount": "5", "period": "day"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                ledger=[
                    contribution(
                        "event_001",
                        "5",
                        "2026-08-10T00:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "WAIT")

    def test_next_day_start_is_not_in_prior_day(self) -> None:
        rule = make_rule(
            "rule_001",
            "max_contribution_per_period",
            {"amount": "5", "period": "day"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                ledger=[
                    contribution(
                        "event_001",
                        "5",
                        "2026-08-09T00:00:00Z",
                    )
                ],
            ),
            "2026-08-10T00:00:00Z",
        )
        self.assertEqual(result["current_status"], "HOLD")

    def test_week_starts_monday_utc(self) -> None:
        rule = make_rule(
            "rule_001",
            "max_contribution_per_period",
            {"amount": "5", "period": "week"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                ledger=[
                    contribution(
                        "event_001",
                        "5",
                        "2026-08-10T00:00:00Z",
                    )
                ],
            ),
            "2026-08-10T00:00:00Z",
        )
        evidence = result["rule_results"][0]["evidence"]
        self.assertEqual(evidence["period_start"], "2026-08-10T00:00:00Z")
        self.assertEqual(evidence["period_end"], "2026-08-17T00:00:00Z")

    def test_month_boundary_is_calendar_based(self) -> None:
        rule = make_rule(
            "rule_001",
            "max_contribution_per_period",
            {"amount": "5", "period": "month"},
        )
        result = evaluate_rules(
            make_record(rules=[rule]),
            "2026-12-31T23:59:59Z",
        )
        evidence = result["rule_results"][0]["evidence"]
        self.assertEqual(evidence["period_start"], "2026-12-01T00:00:00Z")
        self.assertEqual(evidence["period_end"], "2027-01-01T00:00:00Z")

    def test_quarter_boundary_is_calendar_based(self) -> None:
        rule = make_rule(
            "rule_001",
            "max_contribution_per_period",
            {"amount": "5", "period": "quarter"},
        )
        result = evaluate_rules(
            make_record(rules=[rule]),
            "2026-10-15T12:00:00Z",
        )
        evidence = result["rule_results"][0]["evidence"]
        self.assertEqual(evidence["period_start"], "2026-10-01T00:00:00Z")
        self.assertEqual(evidence["period_end"], "2027-01-01T00:00:00Z")

    def test_year_boundary_is_calendar_based(self) -> None:
        rule = make_rule(
            "rule_001",
            "max_contribution_per_period",
            {"amount": "5", "period": "year"},
        )
        result = evaluate_rules(
            make_record(rules=[rule]),
            "2026-06-01T12:00:00Z",
        )
        evidence = result["rule_results"][0]["evidence"]
        self.assertEqual(evidence["period_start"], "2026-01-01T00:00:00Z")
        self.assertEqual(evidence["period_end"], "2027-01-01T00:00:00Z")

    def test_future_contribution_does_not_count_yet(self) -> None:
        rule = make_rule(
            "rule_001",
            "max_contribution_per_period",
            {"amount": "5", "period": "day"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                ledger=[
                    contribution(
                        "event_001",
                        "5",
                        "2026-08-10T13:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "HOLD")

    def test_backfilled_contribution_uses_occurred_at(self) -> None:
        rule = make_rule(
            "rule_001",
            "max_contribution_per_period",
            {"amount": "5", "period": "day"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                ledger=[
                    contribution(
                        "event_001",
                        "5",
                        "2026-08-10T10:00:00Z",
                        recorded_at="2026-08-11T10:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "WAIT")

    def test_minimum_days_no_prior_contribution_is_clear(self) -> None:
        rule = make_rule(
            "rule_001",
            "minimum_days_between_contributions",
            {"days": 2},
        )
        result = evaluate_rules(
            make_record(rules=[rule]),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "HOLD")
        self.assertEqual(
            result["rule_results"][0]["reason_code"],
            "no_prior_contribution",
        )

    def test_minimum_days_inside_cooldown_is_wait(self) -> None:
        rule = make_rule(
            "rule_001",
            "minimum_days_between_contributions",
            {"days": 2},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                ledger=[
                    contribution(
                        "event_001",
                        "5",
                        "2026-08-09T12:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "WAIT")

    def test_minimum_days_exact_cooldown_end_is_clear(self) -> None:
        rule = make_rule(
            "rule_001",
            "minimum_days_between_contributions",
            {"days": 2},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                ledger=[
                    contribution(
                        "event_001",
                        "5",
                        "2026-08-08T12:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "HOLD")
        self.assertEqual(
            result["rule_results"][0]["reason_code"],
            "minimum_contribution_interval_elapsed",
        )

    def test_minimum_days_voided_latest_contribution_is_ignored(self) -> None:
        rule = make_rule(
            "rule_001",
            "minimum_days_between_contributions",
            {"days": 2},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                ledger=[
                    contribution(
                        "event_old",
                        "5",
                        "2026-08-07T12:00:00Z",
                    ),
                    contribution(
                        "event_new",
                        "5",
                        "2026-08-10T11:00:00Z",
                    ),
                    correction(
                        "event_correction",
                        "event_new",
                        "2026-08-10T11:30:00Z",
                    ),
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "HOLD")

    def test_minimum_days_future_contribution_is_ignored(self) -> None:
        rule = make_rule(
            "rule_001",
            "minimum_days_between_contributions",
            {"days": 2},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                ledger=[
                    contribution(
                        "event_001",
                        "5",
                        "2026-08-10T13:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "HOLD")

    def test_threshold_at_or_above_below_is_clear(self) -> None:
        rule = make_rule(
            "rule_001",
            "portfolio_value_review_threshold",
            {"threshold_value": "75", "direction": "at_or_above"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                snapshots=[
                    snapshot(
                        "snapshot_001",
                        "74.99",
                        "2026-08-10T10:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "HOLD")

    def test_threshold_at_or_above_exact_is_review(self) -> None:
        rule = make_rule(
            "rule_001",
            "portfolio_value_review_threshold",
            {"threshold_value": "75", "direction": "at_or_above"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                snapshots=[
                    snapshot(
                        "snapshot_001",
                        "75",
                        "2026-08-10T10:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "REVIEW")

    def test_threshold_at_or_below_above_is_clear(self) -> None:
        rule = make_rule(
            "rule_001",
            "portfolio_value_review_threshold",
            {"threshold_value": "50", "direction": "at_or_below"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                snapshots=[
                    snapshot(
                        "snapshot_001",
                        "50.01",
                        "2026-08-10T10:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "HOLD")

    def test_threshold_at_or_below_exact_is_review(self) -> None:
        rule = make_rule(
            "rule_001",
            "portfolio_value_review_threshold",
            {"threshold_value": "50", "direction": "at_or_below"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                snapshots=[
                    snapshot(
                        "snapshot_001",
                        "50",
                        "2026-08-10T10:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "REVIEW")

    def test_threshold_missing_snapshot_is_wait(self) -> None:
        rule = make_rule(
            "rule_001",
            "portfolio_value_review_threshold",
            {"threshold_value": "75", "direction": "at_or_above"},
        )
        result = evaluate_rules(
            make_record(rules=[rule]),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "WAIT")
        self.assertEqual(
            result["rule_results"][0]["reason_code"],
            "missing_confirmed_snapshot",
        )

    def test_threshold_conflicting_latest_snapshots_is_wait(self) -> None:
        rule = make_rule(
            "rule_001",
            "portfolio_value_review_threshold",
            {"threshold_value": "75", "direction": "at_or_above"},
        )
        snapshots = [
            snapshot(
                "snapshot_a",
                "70",
                "2026-08-10T10:00:00Z",
                recorded_at="2026-08-10T10:01:00Z",
            ),
            snapshot(
                "snapshot_b",
                "80",
                "2026-08-10T10:00:00Z",
                recorded_at="2026-08-10T10:01:00Z",
            ),
        ]
        result = evaluate_rules(
            make_record(rules=[rule], snapshots=snapshots),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "WAIT")
        self.assertEqual(
            result["rule_results"][0]["reason_code"],
            "ambiguous_confirmed_value",
        )

    def test_threshold_stale_clear_snapshot_becomes_wait(self) -> None:
        rule = make_rule(
            "rule_001",
            "portfolio_value_review_threshold",
            {"threshold_value": "75", "direction": "at_or_above"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                snapshots=[
                    snapshot(
                        "snapshot_001",
                        "70",
                        "2026-08-10T10:00:00Z",
                    )
                ],
                ledger=[
                    trade(
                        "event_001",
                        "2026-08-10T11:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "WAIT")
        self.assertEqual(
            result["rule_results"][0]["reason_code"],
            "stale_confirmed_value",
        )

    def test_threshold_proven_review_survives_later_activity(self) -> None:
        rule = make_rule(
            "rule_001",
            "portfolio_value_review_threshold",
            {"threshold_value": "75", "direction": "at_or_above"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                snapshots=[
                    snapshot(
                        "snapshot_001",
                        "75",
                        "2026-08-10T10:00:00Z",
                    )
                ],
                ledger=[
                    withdrawal(
                        "event_001",
                        "5",
                        "2026-08-10T11:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "REVIEW")

    def test_threshold_voided_post_snapshot_activity_does_not_make_stale(self) -> None:
        rule = make_rule(
            "rule_001",
            "portfolio_value_review_threshold",
            {"threshold_value": "75", "direction": "at_or_above"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                snapshots=[
                    snapshot(
                        "snapshot_001",
                        "70",
                        "2026-08-10T10:00:00Z",
                    )
                ],
                ledger=[
                    trade(
                        "event_trade",
                        "2026-08-10T11:00:00Z",
                    ),
                    correction(
                        "event_correction",
                        "event_trade",
                        "2026-08-10T11:30:00Z",
                    ),
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "HOLD")

    def test_threshold_post_snapshot_note_does_not_make_stale(self) -> None:
        rule = make_rule(
            "rule_001",
            "portfolio_value_review_threshold",
            {"threshold_value": "75", "direction": "at_or_above"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                snapshots=[
                    snapshot(
                        "snapshot_001",
                        "70",
                        "2026-08-10T10:00:00Z",
                    )
                ],
                ledger=[
                    note(
                        "event_note",
                        "2026-08-10T11:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "HOLD")

    def test_threshold_future_snapshot_is_ignored(self) -> None:
        rule = make_rule(
            "rule_001",
            "portfolio_value_review_threshold",
            {"threshold_value": "75", "direction": "at_or_above"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                snapshots=[
                    snapshot(
                        "snapshot_future",
                        "100",
                        "2026-08-10T13:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "WAIT")
        self.assertEqual(
            result["rule_results"][0]["reason_code"],
            "missing_confirmed_snapshot",
        )

    def test_threshold_equivalent_offsets_compare_as_same_instant(self) -> None:
        rule = make_rule(
            "rule_001",
            "portfolio_value_review_threshold",
            {"threshold_value": "75", "direction": "at_or_above"},
        )
        snapshots = [
            snapshot(
                "snapshot_b",
                "75.00",
                "2026-08-10T18:00:00Z",
                recorded_at="2026-08-10T18:01:00Z",
            ),
            snapshot(
                "snapshot_a",
                "75",
                "2026-08-10T13:00:00-05:00",
                recorded_at="2026-08-10T13:01:00-05:00",
            ),
        ]
        result = evaluate_rules(
            make_record(rules=[rule], snapshots=snapshots),
            "2026-08-10T19:00:00Z",
        )
        self.assertEqual(result["current_status"], "REVIEW")
        self.assertEqual(
            result["rule_results"][0]["evidence"]["snapshot_id"],
            "snapshot_a",
        )

    def test_scheduled_review_day_before_is_clear(self) -> None:
        rule = make_rule(
            "rule_001",
            "scheduled_review_date",
            {"review_date": "2026-08-10"},
        )
        result = evaluate_rules(
            make_record(rules=[rule]),
            "2026-08-09T23:59:59Z",
        )
        self.assertEqual(result["current_status"], "HOLD")

    def test_scheduled_review_exact_date_is_review(self) -> None:
        rule = make_rule(
            "rule_001",
            "scheduled_review_date",
            {"review_date": "2026-08-10"},
        )
        result = evaluate_rules(
            make_record(rules=[rule]),
            "2026-08-10T00:00:00Z",
        )
        self.assertEqual(result["current_status"], "REVIEW")

    def test_scheduled_review_later_date_remains_review(self) -> None:
        rule = make_rule(
            "rule_001",
            "scheduled_review_date",
            {"review_date": "2026-08-10"},
        )
        result = evaluate_rules(
            make_record(rules=[rule]),
            "2026-08-15T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "REVIEW")

    def test_scheduled_review_uses_utc_calendar_date(self) -> None:
        rule = make_rule(
            "rule_001",
            "scheduled_review_date",
            {"review_date": "2026-08-10"},
        )
        result = evaluate_rules(
            make_record(rules=[rule]),
            "2026-08-09T20:00:00-05:00",
        )
        self.assertEqual(result["current_status"], "REVIEW")

    def test_milestone_acknowledged_is_clear(self) -> None:
        rule = make_rule(
            "rule_001",
            "milestone_review",
            {"milestone_id": "milestone_001"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                milestones=[
                    milestone(
                        reached_at="2026-08-06T00:00:00Z",
                    )
                ],
                snapshots=[
                    snapshot(
                        "snapshot_001",
                        "80",
                        "2026-08-06T00:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "HOLD")
        self.assertEqual(
            result["rule_results"][0]["reason_code"],
            "milestone_already_acknowledged",
        )

    def test_future_milestone_acknowledgement_does_not_clear_early(self) -> None:
        rule = make_rule(
            "rule_001",
            "milestone_review",
            {"milestone_id": "milestone_001"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                milestones=[
                    milestone(
                        reached_at="2026-08-11T00:00:00Z",
                    )
                ],
                snapshots=[
                    snapshot(
                        "snapshot_before",
                        "70",
                        "2026-08-04T00:00:00Z",
                    ),
                    snapshot(
                        "snapshot_cross",
                        "80",
                        "2026-08-06T00:00:00Z",
                    ),
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "REVIEW")

    def test_milestone_already_satisfied_at_creation_is_clear(self) -> None:
        rule = make_rule(
            "rule_001",
            "milestone_review",
            {"milestone_id": "milestone_001"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                milestones=[milestone()],
                snapshots=[
                    snapshot(
                        "snapshot_001",
                        "80",
                        "2026-08-04T00:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "HOLD")
        self.assertEqual(
            result["rule_results"][0]["reason_code"],
            "milestone_already_satisfied_at_creation",
        )

    def test_milestone_baseline_below_then_crossing_is_review(self) -> None:
        rule = make_rule(
            "rule_001",
            "milestone_review",
            {"milestone_id": "milestone_001"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                milestones=[milestone()],
                snapshots=[
                    snapshot(
                        "snapshot_before",
                        "70",
                        "2026-08-04T00:00:00Z",
                    ),
                    snapshot(
                        "snapshot_cross",
                        "75",
                        "2026-08-06T00:00:00Z",
                    ),
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "REVIEW")
        self.assertEqual(
            result["rule_results"][0]["reason_code"],
            "milestone_newly_reached",
        )

    def test_milestone_first_observed_above_without_baseline_is_wait(self) -> None:
        rule = make_rule(
            "rule_001",
            "milestone_review",
            {"milestone_id": "milestone_001"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                milestones=[milestone()],
                snapshots=[
                    snapshot(
                        "snapshot_001",
                        "80",
                        "2026-08-06T00:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "WAIT")
        self.assertEqual(
            result["rule_results"][0]["reason_code"],
            "milestone_transition_unknown",
        )

    def test_milestone_first_observed_below_then_crossing_is_review(self) -> None:
        rule = make_rule(
            "rule_001",
            "milestone_review",
            {"milestone_id": "milestone_001"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                milestones=[milestone()],
                snapshots=[
                    snapshot(
                        "snapshot_first",
                        "70",
                        "2026-08-06T00:00:00Z",
                    ),
                    snapshot(
                        "snapshot_cross",
                        "76",
                        "2026-08-07T00:00:00Z",
                    ),
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "REVIEW")

    def test_milestone_below_target_without_crossing_is_clear(self) -> None:
        rule = make_rule(
            "rule_001",
            "milestone_review",
            {"milestone_id": "milestone_001"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                milestones=[milestone()],
                snapshots=[
                    snapshot(
                        "snapshot_before",
                        "60",
                        "2026-08-04T00:00:00Z",
                    ),
                    snapshot(
                        "snapshot_after",
                        "70",
                        "2026-08-07T00:00:00Z",
                    ),
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "HOLD")
        self.assertEqual(
            result["rule_results"][0]["reason_code"],
            "milestone_not_yet_reached",
        )

    def test_milestone_proven_crossing_remains_review_after_decline(self) -> None:
        rule = make_rule(
            "rule_001",
            "milestone_review",
            {"milestone_id": "milestone_001"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                milestones=[milestone()],
                snapshots=[
                    snapshot(
                        "snapshot_before",
                        "70",
                        "2026-08-04T00:00:00Z",
                    ),
                    snapshot(
                        "snapshot_cross",
                        "80",
                        "2026-08-06T00:00:00Z",
                    ),
                    snapshot(
                        "snapshot_decline",
                        "65",
                        "2026-08-08T00:00:00Z",
                    ),
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "REVIEW")

    def test_milestone_stale_without_crossing_is_wait(self) -> None:
        rule = make_rule(
            "rule_001",
            "milestone_review",
            {"milestone_id": "milestone_001"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                milestones=[milestone()],
                snapshots=[
                    snapshot(
                        "snapshot_before",
                        "60",
                        "2026-08-04T00:00:00Z",
                    ),
                    snapshot(
                        "snapshot_after",
                        "70",
                        "2026-08-07T00:00:00Z",
                    ),
                ],
                ledger=[
                    reward(
                        "event_001",
                        "1",
                        "2026-08-08T00:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "WAIT")
        self.assertEqual(
            result["rule_results"][0]["reason_code"],
            "stale_confirmed_value",
        )

    def test_milestone_voided_stale_event_is_ignored(self) -> None:
        rule = make_rule(
            "rule_001",
            "milestone_review",
            {"milestone_id": "milestone_001"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                milestones=[milestone()],
                snapshots=[
                    snapshot(
                        "snapshot_before",
                        "60",
                        "2026-08-04T00:00:00Z",
                    ),
                    snapshot(
                        "snapshot_after",
                        "70",
                        "2026-08-07T00:00:00Z",
                    ),
                ],
                ledger=[
                    reward(
                        "event_reward",
                        "1",
                        "2026-08-08T00:00:00Z",
                    ),
                    correction(
                        "event_correction",
                        "event_reward",
                        "2026-08-09T00:00:00Z",
                    ),
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "HOLD")

    def test_milestone_missing_snapshots_is_wait(self) -> None:
        rule = make_rule(
            "rule_001",
            "milestone_review",
            {"milestone_id": "milestone_001"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                milestones=[milestone()],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "WAIT")
        self.assertEqual(
            result["rule_results"][0]["reason_code"],
            "missing_confirmed_snapshot",
        )

    def test_milestone_ambiguous_required_state_is_wait(self) -> None:
        rule = make_rule(
            "rule_001",
            "milestone_review",
            {"milestone_id": "milestone_001"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                milestones=[milestone()],
                snapshots=[
                    snapshot(
                        "snapshot_a",
                        "60",
                        "2026-08-04T00:00:00Z",
                        recorded_at="2026-08-04T00:01:00Z",
                    ),
                    snapshot(
                        "snapshot_b",
                        "80",
                        "2026-08-04T00:00:00Z",
                        recorded_at="2026-08-04T00:01:00Z",
                    ),
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "WAIT")
        self.assertEqual(
            result["rule_results"][0]["reason_code"],
            "ambiguous_confirmed_value",
        )

    def test_milestone_ambiguous_intermediate_then_definite_crossing_is_review(self) -> None:
        rule = make_rule(
            "rule_001",
            "milestone_review",
            {"milestone_id": "milestone_001"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                milestones=[milestone()],
                snapshots=[
                    snapshot(
                        "snapshot_before",
                        "70",
                        "2026-08-04T00:00:00Z",
                    ),
                    snapshot(
                        "snapshot_ambiguous_a",
                        "72",
                        "2026-08-06T00:00:00Z",
                        recorded_at="2026-08-06T00:01:00Z",
                    ),
                    snapshot(
                        "snapshot_ambiguous_b",
                        "80",
                        "2026-08-06T00:00:00Z",
                        recorded_at="2026-08-06T00:01:00Z",
                    ),
                    snapshot(
                        "snapshot_cross",
                        "78",
                        "2026-08-07T00:00:00Z",
                    ),
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "REVIEW")
        self.assertEqual(
            result["rule_results"][0]["reason_code"],
            "milestone_newly_reached",
        )

    def test_milestone_ambiguous_intermediate_without_later_crossing_is_wait(self) -> None:
        rule = make_rule(
            "rule_001",
            "milestone_review",
            {"milestone_id": "milestone_001"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                milestones=[milestone()],
                snapshots=[
                    snapshot(
                        "snapshot_before",
                        "70",
                        "2026-08-04T00:00:00Z",
                    ),
                    snapshot(
                        "snapshot_ambiguous_a",
                        "72",
                        "2026-08-06T00:00:00Z",
                        recorded_at="2026-08-06T00:01:00Z",
                    ),
                    snapshot(
                        "snapshot_ambiguous_b",
                        "80",
                        "2026-08-06T00:00:00Z",
                        recorded_at="2026-08-06T00:01:00Z",
                    ),
                    snapshot(
                        "snapshot_later_below",
                        "71",
                        "2026-08-07T00:00:00Z",
                    ),
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "WAIT")
        self.assertEqual(
            result["rule_results"][0]["reason_code"],
            "ambiguous_confirmed_value",
        )

    def test_milestone_no_baseline_ambiguous_then_below_then_crossing_is_review(self) -> None:
        rule = make_rule(
            "rule_001",
            "milestone_review",
            {"milestone_id": "milestone_001"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                milestones=[milestone()],
                snapshots=[
                    snapshot(
                        "snapshot_ambiguous_a",
                        "72",
                        "2026-08-06T00:00:00Z",
                        recorded_at="2026-08-06T00:01:00Z",
                    ),
                    snapshot(
                        "snapshot_ambiguous_b",
                        "80",
                        "2026-08-06T00:00:00Z",
                        recorded_at="2026-08-06T00:01:00Z",
                    ),
                    snapshot(
                        "snapshot_below",
                        "70",
                        "2026-08-07T00:00:00Z",
                    ),
                    snapshot(
                        "snapshot_cross",
                        "76",
                        "2026-08-08T00:00:00Z",
                    ),
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "REVIEW")
        self.assertEqual(
            result["rule_results"][0]["reason_code"],
            "milestone_newly_reached",
        )

    def test_milestone_no_baseline_ambiguous_then_below_only_is_wait(self) -> None:
        rule = make_rule(
            "rule_001",
            "milestone_review",
            {"milestone_id": "milestone_001"},
        )
        result = evaluate_rules(
            make_record(
                rules=[rule],
                milestones=[milestone()],
                snapshots=[
                    snapshot(
                        "snapshot_ambiguous_a",
                        "72",
                        "2026-08-06T00:00:00Z",
                        recorded_at="2026-08-06T00:01:00Z",
                    ),
                    snapshot(
                        "snapshot_ambiguous_b",
                        "80",
                        "2026-08-06T00:00:00Z",
                        recorded_at="2026-08-06T00:01:00Z",
                    ),
                    snapshot(
                        "snapshot_below",
                        "70",
                        "2026-08-07T00:00:00Z",
                    ),
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["current_status"], "WAIT")
        self.assertEqual(
            result["rule_results"][0]["reason_code"],
            "ambiguous_confirmed_value",
        )


    def test_rule_array_reordering_does_not_change_output(self) -> None:
        rules_a = [
            make_rule(
                "rule_b",
                "scheduled_review_date",
                {"review_date": "2026-08-11"},
            ),
            make_rule(
                "rule_a",
                "minimum_days_between_contributions",
                {"days": 2},
            ),
        ]
        rules_b = list(reversed(rules_a))
        ledger = [
            contribution(
                "event_001",
                "5",
                "2026-08-10T11:00:00Z",
            )
        ]
        first = evaluate_rules(
            make_record(rules=rules_a, ledger=ledger),
            "2026-08-10T12:00:00Z",
        )
        second = evaluate_rules(
            make_record(rules=rules_b, ledger=ledger),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(first, second)

    def test_same_input_and_time_produce_same_output(self) -> None:
        rule = make_rule(
            "rule_001",
            "scheduled_review_date",
            {"review_date": "2026-08-10"},
        )
        record = make_record(rules=[rule], revision=9)
        first = evaluate_rules(record, "2026-08-10T12:00:00Z")
        second = evaluate_rules(
            copy.deepcopy(record),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(first, second)

    def test_source_record_is_not_mutated(self) -> None:
        rule = make_rule(
            "rule_001",
            "minimum_days_between_contributions",
            {"days": 2},
        )
        record = make_record(
            rules=[rule],
            ledger=[
                contribution(
                    "event_001",
                    "5",
                    "2026-08-10T11:00:00Z",
                )
            ],
        )
        before = copy.deepcopy(record)
        evaluate_rules(record, "2026-08-10T12:00:00Z")
        self.assertEqual(record, before)

    def test_result_is_json_serializable(self) -> None:
        result = evaluate_rules(
            make_record(),
            "2026-08-10T12:00:00Z",
        )
        serialized = json.dumps(result, sort_keys=True)
        self.assertIn('"current_status": "HOLD"', serialized)

    def test_record_revision_is_preserved(self) -> None:
        result = evaluate_rules(
            make_record(revision=17),
            "2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["record_revision"], 17)

    def test_output_contains_no_buy_or_sell_classification(self) -> None:
        rules = [
            make_rule(
                "rule_wait",
                "minimum_days_between_contributions",
                {"days": 2},
            ),
            make_rule(
                "rule_review",
                "scheduled_review_date",
                {"review_date": "2026-08-10"},
            ),
        ]
        result = evaluate_rules(
            make_record(
                rules=rules,
                ledger=[
                    contribution(
                        "event_001",
                        "5",
                        "2026-08-10T11:00:00Z",
                    )
                ],
            ),
            "2026-08-10T12:00:00Z",
        )
        serialized = json.dumps(result, sort_keys=True).upper()
        self.assertNotIn('"BUY"', serialized)
        self.assertNotIn('"SELL"', serialized)

    def test_naive_evaluation_timestamp_is_rejected(self) -> None:
        with self.assertRaises(RuleInputError):
            evaluate_rules(
                make_record(),
                "2026-08-10T12:00:00",
            )


if __name__ == "__main__":
    unittest.main()
