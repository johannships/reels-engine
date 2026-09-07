---
name: signal-scout
description: Find, normalise, cluster, and rank evidence-backed content signals from a bounded corpus of supplied or researched sources, then emit signal-report.md with a handoff shortlist. Use when the user asks what to talk about, write about, or post about; asks to scan supplied sources, notes, transcripts, call recordings, docs, or comment exports; asks to find audience questions, objections, repeated pains, emerging themes, or contrarian tensions; or asks for a source-backed idea shortlist to feed a content strategy. Do not use for drafting a post whose topic is already decided, for answering a general web question, or for ongoing monitoring.
argument-hint: <objective and audience> [+ paths, URLs, or pasted sources] [+ date window]
---

# Signal Scout

Stage 1 of the content-research-team chain:

```
sources -> /signal-scout -> signal-report.md -> /content-strategist -> /brief-builder
```

## What a signal is

A signal is something **observed in a source**. Six kinds count:

1. an audience question, asked in the corpus
2. a market change with a date
3. a repeated pain, seen more than once
4. a contrarian tension, where two sources disagree or evidence contradicts a common belief
5. a useful proof point, a number, an outcome, or an artifact
6. a timely development inside the stated window

A signal is **not** a topic you generated from model memory. "People are confused
about agent memory" is a topic. "Three of the eight support transcripts (SRC-004
L88-L131, SRC-006 L12-L40, SRC-009 L210-L233) ask how to stop the agent forgetting
context between sessions" is a signal.

This distinction is the entire value of the skill. If you cannot point at a locator
in a source, you do not have a signal. Say so instead of filling the gap. A ranked
list of confident-sounding inventions is worse than a short honest one, because the
user will publish it and be wrong in public.

## Scope

This skill runs when invoked and then stops. It does not schedule, monitor, watch
feeds, or publish. If the user wants recurring scans, they re-invoke it; tell them
that plainly rather than implying a standing agent.

It also never bypasses a login, paywall, robots rule, or rate limit. A blocked
source is recorded as blocked.

## Read first

These three files in the suite's `references/` directory are normative. Read them
before scoring anything, and do not restate their rules from memory:

- `references/evidence-standard.md` for evidence classes, claim rules, confidence, publication safety
- `references/opportunity-scoring.md` for the 5-factor weighted model
- `references/handoff-contracts.md` for ID formats and the shortlist table

> **Where these live:** `references/` and `templates/` are bundled inside this
> skill's own directory, so they resolve wherever the skill is installed. If a
> file is genuinely missing, say so plainly and continue with the method
> described in this file. Never invent the contents of a reference you could
> not read.


From this skill directory they are at `references/` inside this skill directory.

## Workflow

### 1. Confirm the frame before reading anything

Get four things. Ask once, in a single message, then proceed.

- **Objective**: what the content is meant to do
- **Audience**: who specifically, in their own words if possible
- **Date window**: what counts as current, for example "last 90 days"
- **Corpus boundary**: exactly which sources are in play, and whether you may search beyond them

If the user does not answer, state the assumptions you are using at the top of the
report and stamp `status: provisional`. Never silently guess an audience. Audience
relevance carries the heaviest scoring weight, so a guessed audience corrupts the
whole ranking.

### 2. Inventory every source before extracting a single conclusion

Build the source table first. This ordering is deliberate: if you start extracting
insights while reading, you will over-weight whichever source you opened first and
you will lose track of what you never actually opened.

Assign `SRC-001`, `SRC-002`, ... in the order supplied. For each source record:

| field | notes |
|---|---|
| `source_id` | `SRC-nnn`, stable for the run |
| `title` | as published |
| `publisher` | or author |
| `type` | doc, transcript, thread, repo, analytics export, article, video |
| `evidence_class` | 1-5 per the evidence standard |
| `publication_date` | or `unknown`. Never infer it from a URL slug |
| `access_date` | UTC date you actually opened it |
| `path_or_url` | local path or URL |
| `authorization` | public, owned-authorized, restricted, unclear |
| `access_status` | read, partial, blocked, not-attempted |

Mark, do not drop:

- **inaccessible**: blocked, 404, paywalled, login-walled. Record it and move on.
- **partial**: you saw an abstract, a preview, or the first screen only. It can support only what you actually observed.
- **stale**: published outside the date window. Usable as background, not as a timeliness claim.
- **duplicated**: same underlying origin as another source. Note the parent. Five outlets rewriting one press release is one source.
- **unauthorized or unclear**: do not extract from it. Ask the user.

### 3. Extract atomic observations

One observation per line, each with an exact locator: heading, paragraph, page,
line range, timestamp, or URL fragment. Keep the source's own words for anything
you may later quote.

Tag each observation with what it actually is:

- `fact`: directly stated in a class 1-3 source
- `attributed`: a claim the source attributes to someone else, including vendor claims
- `user-assertion`: the user told you, not yet corroborated
- `inference`: your reading of the facts, with the facts it rests on named

Keep these separate all the way through. Most bad content research collapses
`attributed` into `fact` at this step, and the error is invisible by the time it
reaches a draft.

### 4. Cluster without inflating the count

Group observations that describe the same underlying thing into one candidate
signal. When you merge, carry every distinct locator, but count **independent
origins**, not documents. Three transcripts from three different customers is three
origins. Three articles citing the same launch post is one.

Record every merge in the duplicates section. The user needs to see that a signal
backed by "six sources" is not secretly one source repeated.

### 5. Score

Apply the 5-factor model in `references/opportunity-scoring.md`. Score each factor
1-5, or `unknown` where you have no evidence, and publish the breakdown next to
every score. A total with no breakdown is not reviewable and does not go in the
report.

### 6. Contradiction and recency check

Before ranking, sweep the candidate set:

- Does any source contradict another? Surface it as a counter-signal on the affected signal. Do not quietly pick the tidier version.
- Is the newest supporting source older than the date window? Downgrade `timeliness` and say so.
- Does any signal rest entirely on class 4 discovery-only evidence? Its confidence is `low`, whatever the score says.
- Does any signal rest entirely on the user's own assertion? It stays `user-assertion` until something else corroborates it.

### 7. Produce 5 to 10 ranked signals

Not twenty. The constraint is the product. A shortlist a user can actually act on
beats an idea dump they have to re-triage, and anything past roughly ten is usually
padding that dilutes the top three.

If fewer than five survive, ship fewer and explain why in the evidence gaps section.

### 8. Validate before writing the file

Walk the ranked section sentence by sentence. Every externally checkable factual
sentence must either cite a `SRC-nnn` with a locator, or be labelled inference. If
a sentence does neither, cut it or fix it. Then confirm:

- every signal has at least one resolvable `source_id`
- every score has its factor breakdown
- every date is either real or the literal word `unknown`
- no reach, revenue, lead, or ranking outcome is promised anywhere
- no source marked blocked is supporting a detail you did not observe
- the shortlist table matches `references/handoff-contracts.md` exactly

## Output: signal-report.md

Write these sections in this order.

```markdown
# Signal report

## 1. Run metadata
generated_utc: YYYY-MM-DDTHH:MM:SSZ
scope: <objective, audience, date window, corpus boundary>
sources_supplied: N
sources_read: N
sources_unavailable: N
web_search_available: yes | no
status: complete | provisional
provisional_reason: <only if provisional>

## 2. Objective and audience
<Two or three sentences. State assumptions explicitly if the user did not confirm them.>

## 3. Source coverage
| source_id | title | publisher | type | evidence_class | publication_date | access_date | authorization | access_status |
|---|---|---|---|---|---|---|---|---|

## 4. Ranked signals

### SIG-001 <title>
- **Observed signal**: what the sources actually show
- **Why it matters to <audience>**: tied to the stated audience, not a general one
- **Sources**: SRC-004 (L88-L131), SRC-006 (12:40-14:05)
- **Dates**: published <date | unknown>; accessed <date>
- **Evidence class**: 1-5
- **Confidence**: high | medium | low
- **Timeliness**: in-window | background | stale
- **Opportunity score**: NN
  - audience_relevance N x 0.30
  - evidence_strength N x 0.25
  - novelty_tension N x 0.20
  - timeliness N x 0.15
  - execution_feasibility N x 0.10
- **Safe angle possibilities**: two or three angles the evidence actually supports
- **Caveats and counter-signals**: contradictions, gaps, what would falsify this

## 5. Duplicates and merged themes
| merged_into | absorbed | shared_origin | independent_origins |
|---|---|---|---|

## 6. Rejected candidates
| candidate | reason | score_if_scored |
|---|---|---|

## 7. Evidence gaps and recommended verification
<What is missing, which specific source or check would close it.>

## 8. Handoff shortlist
| signal_id | title | confidence | opportunity_score | source_ids |
|---|---|---|---|---|
```

Signal numbering is `SIG-001` upward in final ranked order. IDs are stable for the
run and never reused, because `/content-strategist` and `/brief-builder` cite them
verbatim.

## Failure behaviour

Degrade honestly. Every one of these is a normal outcome, not an error to hide.

**Sources are blocked.** Record `access_status: blocked` with the reason, count it
in `sources_unavailable`, and extract nothing from it. Do not reconstruct a blocked
page from its title, its slug, or a search snippet. Ask the user for an accessible
copy or an authorized export.

**No web access.** Say it in one line in the metadata (`web_search_available: no`)
and in the report body. Process the supplied local sources fully, mark
`status: provisional`, and list what live search would have been used to check.
Never present model memory as a source. If you have no local sources either, stop
and ask for some; there is no useful degraded mode with an empty corpus.

**Corpus too small.** Below roughly three independent origins, no signal can reach
`high` confidence, because `high` requires two or more independent class 1-3
sources. Produce whatever the evidence supports, cap confidence honestly, say the
corpus was thin, and name the specific sources that would strengthen it.

**Everything is stale.** If no source falls inside the date window, do not inflate
`timeliness` to keep scores looking healthy. Score timeliness 1, flag the whole run
`status: provisional`, and tell the user plainly that the corpus supports evergreen
angles but not a "this just happened" framing.

**Nothing survives.** Zero ranked signals is a legitimate result. Ship sections 1,
2, 3, 6, and 7, state that no candidate cleared the evidence bar, and list what to
gather next.
