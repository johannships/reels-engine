<!--
signal-report.md
Produced by /signal-scout. Consumed by /content-strategist.
The `## Handoff shortlist` section below is a contract. Keep the heading and the
column order exactly as written, or the next skill cannot read it.
Delete every comment block before sharing.
-->

# Signal report: <topic or brand>

## Run metadata

<!-- status: complete | provisional
     provisional means an input was missing. Say what, and never fill the gap. -->

- report_id: `SIG-RUN-001`
- status: `complete`
- topic / audience: <who this is for and what they care about>
- window searched: `YYYY-MM-DD` to `YYYY-MM-DD`
- run date: `YYYY-MM-DD`
- access notes: <what you could and could not open>

<!-- If there was no web access, paste this verbatim: -->
<!-- Live search was unavailable in this run. All signals come from supplied local sources. -->

## Source register

<!-- Every source gets a row before it can support a signal.
     date: real publication date, or the literal `unknown`. Never infer a date from
     a URL slug or a search result. Unknown stays unknown.
     class: 1 primary | 2 authorized owned | 3 credible secondary | 4 discovery-only | 5 interpretation
     access: opened | partial | blocked. A blocked source cannot support detail you
     did not observe. -->

| source_id | publisher | title | date | accessed | path or URL | class | access | authorization |
|---|---|---|---|---|---|---|---|---|
| `SRC-001` | <publisher> | <title> | `YYYY-MM-DD` or `unknown` | `YYYY-MM-DD` | <url or local path> | 1 | opened | public |
| `SRC-002` | <publisher> | <title> | `unknown` | `YYYY-MM-DD` | <...> | 4 | blocked | public |

## Signals

<!-- One block per signal. Repeat as needed.
     Score every factor 1-5 with evidence. If you have no evidence for a factor,
     write `unknown` and say the total is partial. Weights and the formula live in
     references/opportunity-scoring.md. -->

### `SIG-001`: <short title>

- what it is: <one or two sentences, plainly stated>
- evidence: `SRC-001` at <locator: heading / page / paragraph / timestamp / line range>
- confidence: `high` | `medium` | `low`
  <!-- high = 2+ independent class 1-3 sources, no contradictions
       medium = one solid class 1-3 source, or several sharing one origin
       low = discovery-only, stale, user-assertion, or partly blocked
       Five outlets rewriting one press release is ONE source, not five. -->
- as of: `YYYY-MM-DD` <!-- required for any time-sensitive claim -->
- contradictions: <what disagrees, or `none found`. Surface it, do not resolve it silently.>
- why the audience cares: <...>

| Factor | Weight | Score | Why |
|---|---|---|---|
| audience_relevance | 0.30 | <1-5> | <evidence> |
| evidence_strength | 0.25 | <1-5> | <evidence> |
| novelty_tension | 0.20 | <1-5> | <evidence> |
| timeliness | 0.15 | <1-5> | <evidence> |
| execution_feasibility | 0.10 | <1-5> | <evidence> |

**opportunity_score: <0-100>** <!-- round(sum(factor * weight) / 5 * 100). Always show the breakdown above; a score without it is not reviewable. -->

## Handoff shortlist

<!-- CONTRACT SECTION. Exact heading, exact columns, exact order.
     Only signals with at least one resolvable source_id belong here.
     75-100 strong | 50-74 viable, needs a sharper angle | 25-49 weak, state why | 0-24 reject -->

| signal_id | title | confidence | opportunity_score | source_ids |
|---|---|---|---|---|
| `SIG-001` | <short title> | high | 82 | `SRC-001; SRC-004` |
| `SIG-003` | <short title> | medium | 64 | `SRC-002` |

## Considered and rejected

<!-- Rejection is an output. Knowing what was dismissed and why is most of what
     makes the ranking trustworthy, and it stops the same weak idea coming back
     every run. -->

| candidate | score | reason rejected |
|---|---|---|
| <candidate> | 18 | Only support was a search snippet nobody could open (class 4). |
| <candidate> | 41 | Real, but the audience has heard it. No tension. |

## What this run could not establish

- <open question>. Would need: <what source or access would settle it>
