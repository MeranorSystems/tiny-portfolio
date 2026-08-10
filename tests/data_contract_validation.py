"""Compatibility shim for data-contract tests.

Production structural-semantic validation lives under the Tiny Portfolio skill.
This module keeps the original test import stable while ensuring the tests
exercise the packaged runtime validator rather than a second implementation.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    ROOT
    / "skills"
    / "tiny-portfolio"
    / "scripts"
    / "validate_portfolio.py"
)

_spec = importlib.util.spec_from_file_location(
    "tiny_portfolio_production_validator",
    VALIDATOR_PATH,
)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"Unable to load production validator: {VALIDATOR_PATH}")

_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

validate_semantics = _module.validate_semantics

__all__ = ["validate_semantics"]
