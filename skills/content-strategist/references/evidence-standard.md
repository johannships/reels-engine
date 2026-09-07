# Evidence standard

Normative for all three skills. The point of this suite is that every claim can be
traced. A confident sentence with no source is the failure mode we are designing
against.

## Evidence classes

1. **Primary public source** — official docs, release notes, filings, original
   research, first-party product pages, direct public statements.
2. **Authorized owned source** — the user's own notes, analytics, transcripts, or
   artifacts they confirm may be used for the stated purpose.
3. **Credible secondary source** — reputable reporting or analysis with clear
   attribution.
4. **Discovery-only source** — a search snippet, aggregator entry, social repost,
   or page metadata you could not actually open. A clue, not evidence.
5. **Interpretation** — your analysis or hypothesis. Never evidence of a fact.

## Claim rules

- Every externally checkable factual claim cites one or more source IDs **and** a
  precise locator: heading, page, paragraph, timestamp, line range, or URL fragment.
- Every source record carries publisher, publication date (or `unknown`), access
  date, path/URL, authorization, and access status.
- **Unknown stays unknown.** Never infer a date from a URL slug or a search result.
- Time-sensitive claims carry an "as of" date.
- Vendor claims stay attributed to the vendor unless independently verified.
- User-supplied claims stay `user-assertion` until corroborated by another class.
- Inferences are labelled and show the facts they rest on.
- Contradictions get surfaced, not silently resolved in favour of the tidier story.
- **Secondary repetition is not corroboration.** Five outlets rewriting one press
  release is one source, not five.
- Exact quotes need exact text plus a locator. Otherwise paraphrase and attribute.
- A blocked or partial source cannot support details you did not actually observe.

## Confidence

| Level | Means |
|---|---|
| `high` | two or more independent sources of class 1-3, no contradictions |
| `medium` | one solid source of class 1-3, or several that agree but share an origin |
| `low` | discovery-only, stale, user-assertion, or partially blocked evidence |

Confidence describes the *evidence*, not your enthusiasm for the idea.

## Publication safety

Before marking anything publication-safe, confirm:

- the source was accessed legitimately and is authorized for this use
- no confidentiality or client permission problem
- quote permission where applicable
- no personal data, credentials, or secrets
- no unsupported regulated claim (financial, legal, medical, security)
- no misleading tense — a planned thing is not described as a done thing
- no fictional sample presented as real

## What this suite will not do

- bypass logins, paywalls, robots rules, or rate limits
- treat a search snippet as a read source
- call something "viral", "growing", or "high-performing" without comparable data
- promise reach, revenue, leads, or ranking outcomes
