# Handoff contracts

The three skills form a chain. Each stage consumes the previous stage's artifact.
These contracts are normative: if a downstream skill cannot find a required field,
it says so rather than inventing it.

```
sources ──> /signal-scout ──> signal-report.md ──> /content-strategist ──> strategy-memo.md ──> /brief-builder ──> content-brief.md + claim-ledger.csv
```

## ID formats

| Entity | Format | Created by |
|---|---|---|
| Source | `SRC-001` | user or signal-scout |
| Signal | `SIG-001` | signal-scout |
| Concept | `CON-001` | content-strategist |
| Claim | `CLM-001` | brief-builder |

IDs are stable within a run and never reused. Downstream artifacts cite upstream
IDs verbatim so a claim in a finished brief can be traced back to a source line.

## Contract 1: signal-scout to content-strategist

`signal-report.md` must contain a `## Handoff shortlist` section. Each row:

```
| signal_id | title | confidence | opportunity_score | source_ids |
```

content-strategist must:
- reject any signal whose `source_ids` are empty or unresolvable
- preserve `signal_id` when it builds a concept
- surface, not silently drop, any signal it declines to use

## Contract 2: content-strategist to brief-builder

`strategy-memo.md` must contain a `## Selected concepts` section. Each concept:

```
- concept_id: CON-001
  source_signals: [SIG-003, SIG-007]
  channel: youtube | linkedin | x | newsletter | short-form | blog
  promise: one sentence
  cta: one CTA, or the literal string "no CTA"
```

brief-builder must:
- accept exactly one `concept_id` per invocation
- fail loudly if `source_signals` do not resolve in the referenced signal report
- carry `channel` through rather than re-deciding it

## Contract 3: brief-builder output

`content-brief.md` plus `claim-ledger.csv`. Every externally checkable factual
sentence in the brief has a `claim_id` in the ledger, and every ledger row cites
at least one `source_id` and a locator.

A brief may only be marked `approved-for-production` when the ledger contains no
row with `publication_safe = no|unknown` and no row with
`approval_status = needs-review|rejected`.

## Degraded operation

If an upstream artifact is missing, the skill asks for it once, then offers to
proceed in a clearly labelled provisional mode. Provisional runs must stamp
`status: provisional` in the artifact metadata and list what was missing. They
must never fabricate the missing upstream data.
