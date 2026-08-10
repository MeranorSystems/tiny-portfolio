# Tiny Portfolio Briefing Reference

Use this reference when the user asks for a Tiny Portfolio briefing or a broad current-status summary.

The briefing explains deterministic results. It must not create new accounting or status logic.

## Full briefing

When available and relevant, include:

1. **Current Status** — HOLD, WAIT, or REVIEW.
2. **Confirmed Value** — selected confirmed portfolio value.
3. **Outside Capital** — contribution/withdrawal-aware contributed-capital context.
4. **Adjusted P/L** — contribution-adjusted dollar performance.
5. **Holdings** — concise confirmed holdings summary.
6. **Next Milestone** — target and distance when derivable from confirmed facts.
7. **Rules** — active wait/review conditions and useful clear-state context.
8. **Activity** — relevant fees or portfolio-generated rewards as explanatory recorded activity.
9. **Freshness** — selected snapshot time and any post-snapshot/stale caveat.
10. **Evaluation Time** — rules/status `evaluated_at`.
11. **Why** — one concise explanation of the status.
12. **Boundary** — remind the user that Tiny Portfolio status is process guidance, not a trade instruction when that distinction is useful.

Do not force every field into every answer. Omit or mark unavailable information rather than fabricating it.

## Recommended concise shape

A routine briefing can read conceptually like:

```text
Status: WAIT
Confirmed value: <value or unavailable>
Adjusted P/L: <value or unavailable>
Next milestone: <target/distance when known>
Rules: <important wait/review condition>
Last confirmed: <snapshot time>
Why: <one-sentence deterministic explanation>
```

Add holdings or activity when the user asked for a broader summary or when they materially explain the result.

## Status-only answer

If the user asks only for current status:

```text
Current Status: <HOLD / WAIT / REVIEW>

<one or two sentences explaining the controlling deterministic rule evidence>
```

Do not attach a full accounting lecture unless needed to answer "why."

## Accounting-only answer

If the user asks only for performance/accounting:
- current confirmed value when available;
- outside contributions;
- withdrawals where relevant;
- adjusted dollar P/L;
- freshness caveat if the selected snapshot is stale relative to recorded activity.

Rule status is optional unless the user asked for it.

## Unknown/unavailable behavior

Use plain language:
- "Current confirmed value is unavailable because no confirmed snapshot exists."
- "The latest confirmed value is ambiguous."
- "The last confirmed snapshot predates recorded portfolio-changing activity."
- "This rule cannot be cleared until a current confirmed value is available."

Do not replace unknown values with estimates.

## Review conditions

When status is REVIEW:
- identify the review-triggering rule or rules;
- explain what condition was reached;
- do not recommend a transaction merely because review is due.

When both review and wait rules exist, global status remains REVIEW. You may mention the wait condition as secondary context.

## WAIT conditions

When status is WAIT:
- identify whether the reason is a contribution limit, cooldown, missing value, stale snapshot, ambiguous state, or unresolved milestone transition;
- include a deterministic boundary such as `wait_until` when available;
- do not promise what the user should do after the wait expires.

## HOLD explanation

When status is HOLD:
- say no enabled machine rule currently requires review or waiting based on the validated recorded facts;
- avoid language implying guaranteed safety or market confidence.

## Provenance

When useful include:
- `record_revision`;
- selected snapshot ID/time;
- `evaluated_at`;
- deterministic reason code.

Prefer human-readable explanation first. Show raw reason codes when they help auditability or the user asks for details.

## Tone

Keep routine briefings calm and compact.

Avoid:
- hype;
- alarmism;
- celebratory investment claims;
- fear-based language;
- pressure to act.

Milestones can be acknowledged positively without turning the achievement into a buy/sell prompt.
