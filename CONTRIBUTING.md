# Contributing to Tiny Portfolio

Tiny Portfolio is an open Meranor Labs project. Early contributions should focus on clarity, privacy, deterministic calculations, test coverage, and transparent product decisions.

## Before contributing

- Read `docs/project-charter.md`.
- Do not submit real account data, private portfolio screenshots, credentials, identifiers, or personal financial records.
- Use fictional or clearly synthetic fixtures in tests and examples.
- Keep Tiny Portfolio separate from the private Tiny Portfolio Command Center.
- Open or reference an issue before beginning substantial feature work.

## Development workflow

1. Create a focused branch from `main`.
2. Keep changes limited to one issue or product decision.
3. Add or update tests for deterministic behavior.
4. Update documentation and `CHANGELOG.md` when behavior changes.
5. Open a pull request describing scope, risks, test results, and unresolved decisions.

## Product safety

Tiny Portfolio must not:

- request passwords, seed phrases, private keys, or authentication codes;
- execute or automate trades;
- present REVIEW as an instruction to buy or sell;
- count outside contributions as portfolio profit;
- save screenshot-derived values without explicit user confirmation;
- fabricate missing values or silently overwrite conflicting history.

## Reporting concerns

Please open a GitHub issue for bugs, privacy concerns, accounting inconsistencies, unclear behavior, or documentation gaps. Do not include personal financial information in reports.
