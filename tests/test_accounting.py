from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from decimal import Decimal
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = (
    REPO_ROOT
    / "skills"
    / "tiny-portfolio"
    / "scripts"
    / "portfolio_engine.py"
)

_spec = importlib.util.spec_from_file_location(
    "tiny_portfolio_portfolio_engine",
    ENGINE_PATH,
)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"Unable to load accounting engine from {ENGINE_PATH}")

_engine = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_engine)

AccountingInputError = _engine.AccountingInputError
calculate_accounting = _engine.calculate_accounting
decimal_to_string = _engine.decimal_to_string


def make_record(
    *,
    ledger: list[dict] | None = None,
    snapshots: list[dict] | None = None,
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
            "machine_rules": [],
            "guidance_notes": [],
        },
        "milestones": [],
        "ledger": [] if ledger is None else ledger,
        "snapshots": [] if snapshots is None else snapshots,
        "metadata": {
            "record_revision": revision,
            "updated_at": "2026-08-10T00:00:00Z",
        },
    }


def make_event(
    event_id: str,
    event_type: str,
    *,
    amount: str | None = None,
    occurred_at: str = "2026-08-01T00:00:00Z",
    recorded_at: str = "2026-08-01T00:01:00Z",
    data: dict | None = None,
) -> dict:
    payload = {} if data is None else dict(data)

    if amount is not None:
        payload["amount"] = amount
        payload["currency"] = "USD"

    return {
        "event_id": event_id,
        "event_type": event_type,
        "occurred_at": occurred_at,
        "recorded_at": recorded_at,
        "source": "guided",
        "data": payload,
    }


def contribution(
    event_id: str,
    amount: str,
    *,
    occurred_at: str = "2026-08-01T00:00:00Z",
    recorded_at: str = "2026-08-01T00:01:00Z",
) -> dict:
    return make_event(
        event_id,
        "contribution",
        amount=amount,
        occurred_at=occurred_at,
        recorded_at=recorded_at,
    )


def withdrawal(
    event_id: str,
    amount: str,
    *,
    occurred_at: str = "2026-08-01T00:00:00Z",
    recorded_at: str = "2026-08-01T00:01:00Z",
) -> dict:
    return make_event(
        event_id,
        "withdrawal",
        amount=amount,
        occurred_at=occurred_at,
        recorded_at=recorded_at,
    )


def fee(
    event_id: str,
    amount: str,
    *,
    occurred_at: str = "2026-08-01T00:00:00Z",
    recorded_at: str = "2026-08-01T00:01:00Z",
) -> dict:
    return make_event(
        event_id,
        "fee",
        amount=amount,
        occurred_at=occurred_at,
        recorded_at=recorded_at,
    )


def reward(
    event_id: str,
    amount: str,
    *,
    occurred_at: str = "2026-08-01T00:00:00Z",
    recorded_at: str = "2026-08-01T00:01:00Z",
) -> dict:
    return make_event(
        event_id,
        "reward",
        amount=amount,
        occurred_at=occurred_at,
        recorded_at=recorded_at,
        data={"reward_type": "staking"},
    )


def trade(
    event_id: str,
    *,
    occurred_at: str = "2026-08-01T00:00:00Z",
    recorded_at: str = "2026-08-01T00:01:00Z",
) -> dict:
    return make_event(
        event_id,
        "trade",
        occurred_at=occurred_at,
        recorded_at=recorded_at,
        data={
            "from_asset": "USD",
            "to_asset": "BTC",
            "from_quantity": "5",
            "to_quantity": "0.00004",
        },
    )


def note(
    event_id: str,
    *,
    occurred_at: str = "2026-08-01T00:00:00Z",
    recorded_at: str = "2026-08-01T00:01:00Z",
) -> dict:
    return make_event(
        event_id,
        "note",
        occurred_at=occurred_at,
        recorded_at=recorded_at,
        data={"text": "Synthetic note."},
    )


def correction(
    event_id: str,
    target_event_id: str,
    *,
    occurred_at: str = "2026-08-02T00:00:00Z",
    recorded_at: str = "2026-08-02T00:01:00Z",
) -> dict:
    return make_event(
        event_id,
        "correction",
        occurred_at=occurred_at,
        recorded_at=recorded_at,
        data={
            "target_event_id": target_event_id,
            "action": "void",
            "reason": "Synthetic correction.",
        },
    )


def snapshot(
    snapshot_id: str,
    total_value: str,
    *,
    captured_at: str = "2026-08-09T12:00:00Z",
    recorded_at: str = "2026-08-09T12:01:00Z",
) -> dict:
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
        "confirmation": {
            "confirmed_at": recorded_at,
        },
    }


class TinyPortfolioAccountingTests(unittest.TestCase):
    def test_contribution_is_not_profit(self) -> None:
        record = make_record(
            ledger=[contribution("event_001", "50")],
            snapshots=[snapshot("snapshot_001", "50")],
        )

        result = calculate_accounting(record)

        self.assertEqual(result["total_contributions_as_of"], "50")
        self.assertEqual(result["adjusted_profit_loss"], "0")

    def test_market_gain_is_reported_in_dollars(self) -> None:
        record = make_record(
            ledger=[contribution("event_001", "50")],
            snapshots=[snapshot("snapshot_001", "55")],
        )

        result = calculate_accounting(record)

        self.assertEqual(result["adjusted_profit_loss"], "5")

    def test_additional_contribution_is_not_profit(self) -> None:
        record = make_record(
            ledger=[
                contribution("event_001", "50"),
                contribution("event_002", "10"),
            ],
            snapshots=[snapshot("snapshot_001", "66")],
        )

        result = calculate_accounting(record)

        self.assertEqual(result["total_contributions_as_of"], "60")
        self.assertEqual(result["adjusted_profit_loss"], "6")

    def test_withdrawal_is_not_loss(self) -> None:
        record = make_record(
            ledger=[
                contribution("event_001", "60"),
                withdrawal("event_002", "10"),
            ],
            snapshots=[snapshot("snapshot_001", "55")],
        )

        result = calculate_accounting(record)

        self.assertEqual(result["total_withdrawals_as_of"], "10")
        self.assertEqual(result["net_outside_capital_as_of"], "50")
        self.assertEqual(result["adjusted_profit_loss"], "5")

    def test_trade_is_neutral_to_outside_capital(self) -> None:
        baseline = make_record(
            ledger=[contribution("event_001", "50")],
            snapshots=[snapshot("snapshot_001", "55")],
        )
        with_trade = copy.deepcopy(baseline)
        with_trade["ledger"].append(trade("event_002"))

        baseline_result = calculate_accounting(baseline)
        trade_result = calculate_accounting(with_trade)

        self.assertEqual(
            baseline_result["net_outside_capital_as_of"],
            trade_result["net_outside_capital_as_of"],
        )
        self.assertEqual(
            baseline_result["adjusted_profit_loss"],
            trade_result["adjusted_profit_loss"],
        )

    def test_fee_is_explanatory_and_not_double_counted(self) -> None:
        record = make_record(
            ledger=[
                contribution("event_001", "50"),
                fee("event_002", "0.10"),
            ],
            snapshots=[snapshot("snapshot_001", "49.90")],
        )

        result = calculate_accounting(record)

        self.assertEqual(result["known_fees_as_of"], "0.1")
        self.assertEqual(result["adjusted_profit_loss"], "-0.1")

    def test_reward_is_explanatory_and_not_double_counted(self) -> None:
        record = make_record(
            ledger=[
                contribution("event_001", "50"),
                reward("event_002", "0.20"),
            ],
            snapshots=[snapshot("snapshot_001", "50.20")],
        )

        result = calculate_accounting(record)

        self.assertEqual(result["known_rewards_as_of"], "0.2")
        self.assertEqual(result["adjusted_profit_loss"], "0.2")

    def test_voided_contribution_is_removed_from_totals(self) -> None:
        record = make_record(
            ledger=[
                contribution("event_001", "50"),
                correction("event_002", "event_001"),
            ],
            snapshots=[snapshot("snapshot_001", "50")],
            revision=2,
        )

        result = calculate_accounting(record)

        self.assertEqual(result["total_contributions_as_of"], "0")
        self.assertEqual(result["total_contributions_recorded"], "0")
        self.assertEqual(result["adjusted_profit_loss"], "50")

    def test_voided_withdrawal_fee_and_reward_are_removed(self) -> None:
        events = [
            contribution("event_001", "50"),
            withdrawal("event_002", "5"),
            fee("event_003", "0.50"),
            reward("event_004", "1.00"),
            correction("event_005", "event_002"),
            correction("event_006", "event_003"),
            correction("event_007", "event_004"),
        ]
        record = make_record(
            ledger=events,
            snapshots=[snapshot("snapshot_001", "50")],
        )

        result = calculate_accounting(record)

        self.assertEqual(result["total_withdrawals_recorded"], "0")
        self.assertEqual(result["known_fees_total"], "0")
        self.assertEqual(result["known_rewards_total"], "0")
        self.assertEqual(result["adjusted_profit_loss"], "0")

    def test_later_correction_changes_historical_accounting(self) -> None:
        record = make_record(
            ledger=[
                contribution("event_001", "50"),
                correction(
                    "event_002",
                    "event_001",
                    occurred_at="2026-08-10T00:00:00Z",
                    recorded_at="2026-08-10T00:01:00Z",
                ),
            ],
            snapshots=[
                snapshot(
                    "snapshot_001",
                    "50",
                    captured_at="2026-08-09T12:00:00Z",
                )
            ],
            revision=9,
        )

        result = calculate_accounting(record)

        self.assertEqual(result["record_revision"], 9)
        self.assertEqual(result["total_contributions_as_of"], "0")
        self.assertEqual(result["adjusted_profit_loss"], "50")
        self.assertFalse(result["has_post_snapshot_activity"])

    def test_no_snapshot_returns_unavailable_but_keeps_recorded_totals(self) -> None:
        record = make_record(
            ledger=[
                contribution("event_001", "50"),
                withdrawal("event_002", "5"),
                fee("event_003", "0.25"),
                reward("event_004", "0.50"),
            ]
        )

        result = calculate_accounting(record)

        self.assertEqual(result["calculation_status"], "unavailable")
        self.assertEqual(result["reason"], "no_confirmed_snapshot")
        self.assertIsNone(result["current_confirmed_value"])
        self.assertIsNone(result["adjusted_profit_loss"])
        self.assertEqual(result["total_contributions_recorded"], "50")
        self.assertEqual(result["total_withdrawals_recorded"], "5")
        self.assertEqual(result["known_fees_total"], "0.25")
        self.assertEqual(result["known_rewards_total"], "0.5")

    def test_latest_snapshot_prefers_captured_at_over_recorded_at(self) -> None:
        record = make_record(
            snapshots=[
                snapshot(
                    "older_state_entered_later",
                    "40",
                    captured_at="2026-08-08T12:00:00Z",
                    recorded_at="2026-08-10T12:00:00Z",
                ),
                snapshot(
                    "newer_state",
                    "50",
                    captured_at="2026-08-09T12:00:00Z",
                    recorded_at="2026-08-09T12:01:00Z",
                ),
            ]
        )

        result = calculate_accounting(record)

        self.assertEqual(result["snapshot_id"], "newer_state")
        self.assertEqual(result["current_confirmed_value"], "50")

    def test_same_capture_time_prefers_later_recorded_at(self) -> None:
        record = make_record(
            snapshots=[
                snapshot(
                    "snapshot_early_entry",
                    "40",
                    captured_at="2026-08-09T12:00:00Z",
                    recorded_at="2026-08-09T12:01:00Z",
                ),
                snapshot(
                    "snapshot_late_entry",
                    "50",
                    captured_at="2026-08-09T12:00:00Z",
                    recorded_at="2026-08-09T12:02:00Z",
                ),
            ]
        )

        result = calculate_accounting(record)

        self.assertEqual(result["snapshot_id"], "snapshot_late_entry")
        self.assertEqual(result["current_confirmed_value"], "50")

    def test_equal_latest_snapshot_values_choose_smallest_id(self) -> None:
        record = make_record(
            snapshots=[
                snapshot(
                    "snapshot_b",
                    "50.00",
                    captured_at="2026-08-09T18:00:00Z",
                    recorded_at="2026-08-09T18:01:00Z",
                ),
                snapshot(
                    "snapshot_a",
                    "50",
                    captured_at="2026-08-09T18:00:00Z",
                    recorded_at="2026-08-09T18:01:00Z",
                ),
            ]
        )

        result = calculate_accounting(record)

        self.assertEqual(result["calculation_status"], "available")
        self.assertEqual(result["snapshot_id"], "snapshot_a")

    def test_conflicting_latest_snapshot_values_are_unavailable(self) -> None:
        record = make_record(
            snapshots=[
                snapshot(
                    "snapshot_a",
                    "50",
                    captured_at="2026-08-09T18:00:00Z",
                    recorded_at="2026-08-09T18:01:00Z",
                ),
                snapshot(
                    "snapshot_b",
                    "51",
                    captured_at="2026-08-09T18:00:00Z",
                    recorded_at="2026-08-09T18:01:00Z",
                ),
            ]
        )

        result = calculate_accounting(record)

        self.assertEqual(result["calculation_status"], "unavailable")
        self.assertEqual(result["reason"], "ambiguous_latest_snapshot")
        self.assertIsNone(result["adjusted_profit_loss"])

    def test_equivalent_timezone_offsets_compare_as_same_instant(self) -> None:
        record = make_record(
            snapshots=[
                snapshot(
                    "snapshot_b",
                    "50.00",
                    captured_at="2026-08-09T18:00:00Z",
                    recorded_at="2026-08-09T18:01:00Z",
                ),
                snapshot(
                    "snapshot_a",
                    "50",
                    captured_at="2026-08-09T13:00:00-05:00",
                    recorded_at="2026-08-09T13:01:00-05:00",
                ),
            ]
        )

        result = calculate_accounting(record)

        self.assertEqual(result["snapshot_id"], "snapshot_a")

    def test_backfilled_event_uses_occurred_at_not_recorded_at(self) -> None:
        record = make_record(
            ledger=[
                contribution(
                    "event_001",
                    "50",
                    occurred_at="2026-08-08T00:00:00Z",
                    recorded_at="2026-08-10T00:00:00Z",
                )
            ],
            snapshots=[
                snapshot(
                    "snapshot_001",
                    "55",
                    captured_at="2026-08-09T12:00:00Z",
                )
            ],
        )

        result = calculate_accounting(record)

        self.assertEqual(result["total_contributions_as_of"], "50")
        self.assertEqual(result["adjusted_profit_loss"], "5")

    def test_post_snapshot_activity_is_excluded_from_as_of_totals(self) -> None:
        record = make_record(
            ledger=[
                contribution("event_001", "50"),
                contribution(
                    "event_002",
                    "10",
                    occurred_at="2026-08-10T00:00:00Z",
                    recorded_at="2026-08-10T00:01:00Z",
                ),
            ],
            snapshots=[
                snapshot(
                    "snapshot_001",
                    "55",
                    captured_at="2026-08-09T12:00:00Z",
                )
            ],
        )

        result = calculate_accounting(record)

        self.assertEqual(result["total_contributions_as_of"], "50")
        self.assertEqual(result["total_contributions_recorded"], "60")
        self.assertEqual(result["adjusted_profit_loss"], "5")
        self.assertTrue(result["has_post_snapshot_activity"])
        self.assertEqual(result["post_snapshot_activity_count"], 1)

    def test_post_snapshot_note_does_not_set_freshness_flag(self) -> None:
        record = make_record(
            ledger=[
                contribution("event_001", "50"),
                note(
                    "event_002",
                    occurred_at="2026-08-10T00:00:00Z",
                    recorded_at="2026-08-10T00:01:00Z",
                ),
            ],
            snapshots=[
                snapshot(
                    "snapshot_001",
                    "55",
                    captured_at="2026-08-09T12:00:00Z",
                )
            ],
        )

        result = calculate_accounting(record)

        self.assertFalse(result["has_post_snapshot_activity"])
        self.assertEqual(result["post_snapshot_activity_count"], 0)

    def test_voided_post_snapshot_event_does_not_set_freshness_flag(self) -> None:
        post_snapshot_contribution = contribution(
            "event_002",
            "10",
            occurred_at="2026-08-10T00:00:00Z",
            recorded_at="2026-08-10T00:01:00Z",
        )
        record = make_record(
            ledger=[
                contribution("event_001", "50"),
                post_snapshot_contribution,
                correction(
                    "event_003",
                    "event_002",
                    occurred_at="2026-08-10T01:00:00Z",
                    recorded_at="2026-08-10T01:01:00Z",
                ),
            ],
            snapshots=[
                snapshot(
                    "snapshot_001",
                    "55",
                    captured_at="2026-08-09T12:00:00Z",
                )
            ],
        )

        result = calculate_accounting(record)

        self.assertFalse(result["has_post_snapshot_activity"])
        self.assertEqual(result["total_contributions_recorded"], "50")

    def test_decimal_point_one_plus_point_two_is_exact(self) -> None:
        record = make_record(
            ledger=[
                contribution("event_001", "0.1"),
                contribution("event_002", "0.2"),
            ],
            snapshots=[snapshot("snapshot_001", "1.3")],
        )

        result = calculate_accounting(record)

        self.assertEqual(result["total_contributions_as_of"], "0.3")
        self.assertEqual(result["adjusted_profit_loss"], "1")

    def test_high_precision_accumulation_does_not_round(self) -> None:
        record = make_record(
            ledger=[
                contribution(
                    "event_001",
                    "123456789012345678901234567890.12345678901234567890",
                ),
                contribution("event_002", "0.2"),
                contribution("event_003", "0.1"),
            ],
            snapshots=[
                snapshot(
                    "snapshot_001",
                    "123456789012345678901234567891.42345678901234567890",
                )
            ],
        )

        result = calculate_accounting(record)

        self.assertEqual(
            result["total_contributions_as_of"],
            "123456789012345678901234567890.4234567890123456789",
        )
        self.assertEqual(result["adjusted_profit_loss"], "1")

    def test_decimal_serialization_is_canonical(self) -> None:
        cases = {
            Decimal("60.00"): "60",
            Decimal("0.300"): "0.3",
            Decimal("-5.00"): "-5",
            Decimal("0.00"): "0",
            Decimal("-0.000"): "0",
            Decimal("1000.000"): "1000",
            Decimal("0.00000100"): "0.000001",
        }

        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(decimal_to_string(value), expected)

    def test_result_includes_record_revision_provenance(self) -> None:
        record = make_record(
            snapshots=[snapshot("snapshot_001", "50")],
            revision=17,
        )

        result = calculate_accounting(record)

        self.assertEqual(result["record_revision"], 17)

    def test_engine_does_not_mutate_authoritative_record(self) -> None:
        record = make_record(
            ledger=[
                contribution("event_001", "50"),
                fee("event_002", "0.1"),
            ],
            snapshots=[snapshot("snapshot_001", "49.9")],
        )
        before = copy.deepcopy(record)

        calculate_accounting(record)

        self.assertEqual(record, before)

    def test_same_input_produces_same_output(self) -> None:
        record = make_record(
            ledger=[
                contribution("event_001", "50"),
                reward("event_002", "0.5"),
                trade("event_003"),
            ],
            snapshots=[snapshot("snapshot_001", "51")],
            revision=4,
        )

        first = calculate_accounting(record)
        second = calculate_accounting(copy.deepcopy(record))

        self.assertEqual(first, second)

    def test_result_is_json_serializable(self) -> None:
        record = make_record(
            ledger=[contribution("event_001", "50")],
            snapshots=[snapshot("snapshot_001", "55")],
        )

        result = calculate_accounting(record)

        serialized = json.dumps(result, sort_keys=True)
        self.assertIn('"adjusted_profit_loss": "5"', serialized)

    def test_naive_timestamp_is_rejected_defensively(self) -> None:
        record = make_record(
            ledger=[
                contribution(
                    "event_001",
                    "50",
                    occurred_at="2026-08-01T00:00:00",
                )
            ],
            snapshots=[snapshot("snapshot_001", "55")],
        )

        with self.assertRaises(AccountingInputError):
            calculate_accounting(record)


if __name__ == "__main__":
    unittest.main()
