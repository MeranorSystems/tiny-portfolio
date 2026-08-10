from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "tiny-portfolio" / "scripts"
VALID_DIR = ROOT / "tests" / "fixtures" / "valid"
INVALID_DIR = ROOT / "tests" / "fixtures" / "invalid"
EXAMPLE = (
    ROOT
    / "skills"
    / "tiny-portfolio"
    / "assets"
    / "tiny-portfolio.example.json"
)


def load_module(name: str, filename: str):
    path = SCRIPTS / filename
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_module(
    "tiny_portfolio_validate_runtime_test",
    "validate_portfolio.py",
)
runtime = load_module(
    "tiny_portfolio_runtime_test",
    "tiny_portfolio_runtime.py",
)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class TinyPortfolioSkillRuntimeFoundationTests(unittest.TestCase):
    def test_production_validator_accepts_valid_fixture(self):
        record = load_json(VALID_DIR / "minimal-valid.json")
        result = validator.validate_portfolio(record)
        self.assertEqual(result["validation_status"], "valid")
        self.assertEqual(result["schema_errors"], [])
        self.assertEqual(result["semantic_errors"], [])

    def test_production_validator_reports_schema_error(self):
        record = load_json(INVALID_DIR / "unsupported-property.json")
        result = validator.validate_portfolio(record)
        self.assertEqual(result["validation_status"], "invalid")
        self.assertTrue(result["schema_errors"])
        self.assertEqual(result["semantic_errors"], [])

    def test_production_validator_reports_semantic_error(self):
        record = load_json(INVALID_DIR / "mismatched-currency.json")
        result = validator.validate_portfolio(record)
        self.assertEqual(result["validation_status"], "invalid")
        self.assertEqual(result["schema_errors"], [])
        self.assertTrue(
            any(
                "does not match portfolio base currency" in message
                for message in result["semantic_errors"]
            )
        )

    def test_runtime_stops_when_record_is_invalid(self):
        record = load_json(INVALID_DIR / "mismatched-currency.json")
        result = runtime.analyze_portfolio(
            record,
            evaluation_at="2026-08-10T12:00:00Z",
        )
        self.assertEqual(result["analysis_status"], "invalid_record")
        self.assertIsNone(result["accounting"])
        self.assertIsNone(result["rules_status"])

    def test_runtime_runs_accounting_for_valid_record(self):
        record = load_json(EXAMPLE)
        result = runtime.analyze_portfolio(record)
        self.assertEqual(result["analysis_status"], "available")
        self.assertEqual(result["validation"]["validation_status"], "valid")
        self.assertIsNotNone(result["accounting"])
        self.assertIsNone(result["rules_status"])

    def test_runtime_runs_rules_only_with_explicit_evaluation_time(self):
        record = load_json(EXAMPLE)
        result = runtime.analyze_portfolio(
            record,
            evaluation_at="2026-12-31T12:00:00-05:00",
        )
        self.assertEqual(result["analysis_status"], "available")
        self.assertIn(
            result["rules_status"]["current_status"],
            {"HOLD", "WAIT", "REVIEW"},
        )
        self.assertEqual(
            result["rules_status"]["evaluated_at"],
            "2026-12-31T17:00:00Z",
        )

    def test_runtime_does_not_mutate_authoritative_record(self):
        record = load_json(EXAMPLE)
        before = copy.deepcopy(record)
        runtime.analyze_portfolio(
            record,
            evaluation_at="2026-12-31T12:00:00Z",
        )
        self.assertEqual(record, before)

    def test_runtime_result_is_json_serializable(self):
        record = load_json(EXAMPLE)
        result = runtime.analyze_portfolio(
            record,
            evaluation_at="2026-12-31T12:00:00Z",
        )
        serialized = json.dumps(result, sort_keys=True)
        self.assertIn('"analysis_status": "available"', serialized)

    def test_runtime_never_introduces_buy_or_sell_status(self):
        record = load_json(EXAMPLE)
        result = runtime.analyze_portfolio(
            record,
            evaluation_at="2026-12-31T12:00:00Z",
        )
        status = result["rules_status"]["current_status"]
        self.assertNotIn(status, {"BUY", "SELL"})


if __name__ == "__main__":
    unittest.main()
