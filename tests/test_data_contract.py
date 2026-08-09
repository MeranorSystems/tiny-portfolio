import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from data_contract_validation import validate_semantics


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "skills" / "tiny-portfolio" / "assets" / "tiny-portfolio.schema.json"
EXAMPLE_PATH = ROOT / "skills" / "tiny-portfolio" / "assets" / "tiny-portfolio.example.json"
VALID_DIR = ROOT / "tests" / "fixtures" / "valid"
INVALID_DIR = ROOT / "tests" / "fixtures" / "invalid"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class TinyPortfolioDataContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_json(SCHEMA_PATH)
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(
            cls.schema,
            format_checker=FormatChecker(),
        )

    def assert_schema_valid(self, record):
        errors = sorted(
            self.validator.iter_errors(record),
            key=lambda error: [str(part) for part in error.absolute_path],
        )
        self.assertEqual([], errors, "\n".join(error.message for error in errors))

    def assert_semantically_valid(self, record):
        errors = validate_semantics(record)
        self.assertEqual([], errors, "\n".join(errors))

    def test_full_example_passes_schema_and_semantics(self):
        record = load_json(EXAMPLE_PATH)
        self.assert_schema_valid(record)
        self.assert_semantically_valid(record)

    def test_minimal_fixture_passes_schema_and_semantics(self):
        record = load_json(VALID_DIR / "minimal-valid.json")
        self.assert_schema_valid(record)
        self.assert_semantically_valid(record)

    def test_schema_invalid_fixtures_are_rejected(self):
        names = [
            "missing-schema-version.json",
            "invalid-money-number.json",
            "unconfirmed-snapshot.json",
        ]
        for name in names:
            with self.subTest(name=name):
                record = load_json(INVALID_DIR / name)
                errors = list(self.validator.iter_errors(record))
                self.assertTrue(errors, f"{name} unexpectedly passed JSON Schema")

    def test_semantic_invalid_fixtures_are_rejected(self):
        expectations = {
            "mismatched-currency.json": "does not match portfolio base currency",
            "duplicate-event-id.json": "duplicate ledger event id",
            "bad-milestone-reference.json": "references missing milestone",
            "forward-correction-target.json": "missing or non-prior event",
            "missing-last-snapshot-reference.json": "references missing snapshot",
        }

        for name, expected_text in expectations.items():
            with self.subTest(name=name):
                record = load_json(INVALID_DIR / name)
                self.assert_schema_valid(record)
                errors = validate_semantics(record)
                self.assertTrue(errors, f"{name} unexpectedly passed semantics")
                self.assertTrue(
                    any(expected_text in error for error in errors),
                    f"{name} did not produce expected error; got: {errors}",
                )


if __name__ == "__main__":
    unittest.main()
