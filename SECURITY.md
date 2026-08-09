# Security & Privacy

Tiny Portfolio is built around a simple security principle:

> **A portfolio companion should not need control of your financial accounts in order to be useful.**

Tiny Portfolio by Meranor is designed to help users track manually maintained investment and crypto portfolios while minimizing the financial information the project needs to handle.

Security and privacy are product requirements, not optional features added later.

## Our security mission

Tiny Portfolio is designed to:

- collect only the information needed to maintain a user-controlled portfolio record;
- avoid credentials or permissions that could provide access to financial accounts;
- keep portfolio history portable and understandable;
- require confirmation before screenshot-derived information becomes part of the authoritative record;
- keep calculations deterministic and auditable where possible;
- make security and privacy limitations visible rather than hiding them behind vague promises.

Privacy before convenience is a core design rule.

## What Tiny Portfolio does not do

Tiny Portfolio v0.1 does not:

- connect directly to brokerage or exchange accounts;
- execute trades;
- hold funds or assets;
- request or store passwords;
- request authentication or verification codes;
- request seed phrases or wallet private keys;
- request exchange API secrets;
- request Social Security numbers or tax identifiers;
- require complete financial account numbers;
- operate a Tiny Portfolio user-account system;
- operate a hosted Tiny Portfolio portfolio database;
- automatically retrieve live market or account data.

Any future feature that would materially change these boundaries must receive explicit public design and security review before it is merged.

## User-controlled portfolio records

Tiny Portfolio uses a portable `tiny-portfolio.json` record as its authoritative portfolio format.

The record is intended to contain portfolio facts required by Tiny Portfolio, such as:

- manually recorded holdings and values;
- contributions and withdrawals;
- trades or conversions;
- known fees and portfolio-generated rewards;
- milestones;
- user-defined portfolio rules;
- confirmed historical snapshots.

The format must not require financial-account credentials or identifiers that are unnecessary for portfolio tracking.

Derived calculations and statuses should be reproducible from the underlying record rather than stored as unexplained authoritative values.

## Screenshot safety

Screenshot Assist and Hybrid Check-In are designed around explicit confirmation.

Information extracted from a screenshot is considered **proposed information**, not accounting truth.

Tiny Portfolio should:

1. extract only information relevant to the requested portfolio update;
2. identify uncertainty when information cannot be read confidently;
3. present extracted values to the user for review;
4. require explicit confirmation or correction;
5. record only the confirmed portfolio facts.

Raw screenshots are not part of the portable `tiny-portfolio.json` format.

Users should crop or remove unrelated account details and other sensitive information whenever practical before uploading a screenshot.

## Public repository data boundary

The Tiny Portfolio repository is public.

Examples, tests, fixtures, documentation, screenshots, and demonstrations must therefore use fictional, synthetic, or deliberately sanitized information.

Do not commit or publish:

- passwords or authentication codes;
- seed phrases or private keys;
- API credentials or secrets;
- complete account numbers;
- Social Security numbers or tax identifiers;
- private financial journals or exports;
- identifying transaction histories;
- unsanitized portfolio screenshots;
- confidential or proprietary user information.

Real personal financial data is not acceptable test data for this repository.

## Development security requirements

Contributions must preserve Tiny Portfolio's security boundaries.

New code should favor:

- minimum necessary data collection;
- explicit user confirmation before persistence;
- deterministic and reviewable processing;
- clear separation between user-provided facts and derived results;
- synthetic fixtures for automated testing;
- safe handling of malformed or incomplete portfolio records;
- failures that leave uncertain information unknown rather than invented.

Changes that introduce account access, credentials, external persistence, remote services, financial integrations, or other expanded data handling require dedicated security review.

## No misleading privacy claims

Tiny Portfolio should describe its privacy architecture precisely.

The project should not make unsupported claims such as:

- "your data never leaves your device";
- "bank-level security";
- "completely anonymous";
- "100% secure."

For v0.1, the accurate product boundary is that Tiny Portfolio does not operate its own hosted portfolio database, user-account system, brokerage connection, or exchange connection.

## Reporting a security issue

Please do not publish exploitable details, credentials, or personal financial information in a public GitHub issue.

A dedicated private security-reporting channel will be published before the first public release.

Until that channel is available, public issues may be used only for sanitized security discussions that do not disclose exploitable details, credentials, or private user information.

## Security is part of the product contract

Tiny Portfolio's privacy and security boundaries are part of its public architecture.

A feature is not considered successful if it makes portfolio tracking more convenient by weakening those boundaries without deliberate review.

**Tiny Portfolio should know enough to help manage a portfolio — and no more than it reasonably needs.**
