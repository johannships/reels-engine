# Opportunity scoring

Used by `signal-scout` to rank signals and by `content-strategist` to sanity-check
a selection. The purpose is to make ranking arguable rather than vibes-based, so a
reader can disagree with a specific factor instead of the whole list.

## Factors

Score each 1-5. Never score a factor you have no evidence for; mark it `unknown`
and note that the total is partial.

| Factor | Weight | 1 | 5 |
|---|---|---|---|
| `audience_relevance` | 0.30 | tangential to the stated audience | names a pain the audience has stated in the sources |
| `evidence_strength` | 0.25 | discovery-only or single stale source | multiple independent class 1-3 sources |
| `novelty_tension` | 0.20 | everyone has said this already | a real contradiction, or a widely held belief the evidence disputes |
| `timeliness` | 0.15 | evergreen, no reason to publish now | dated development inside the stated window |
| `execution_feasibility` | 0.10 | needs proof or access the user does not have | the user already owns the proof |

`opportunity_score = round(sum(factor * weight) / 5 * 100)` → 0-100.

Always publish the factor breakdown next to the score. A score without its
breakdown is not reviewable.

## Reading the score

- **75-100** strong candidate; shortlist it
- **50-74** viable, usually needs a sharper angle or better proof
- **25-49** weak; include only with a stated reason
- **0-24** reject and record why

## Deliberate biases

These are choices, not accidents. Document them so users can override.

- **Evidence outranks excitement.** A thrilling idea with one weak source loses to
  a duller one with two strong sources. Content that cannot be defended costs more
  than it earns.
- **Novelty is not contrarianism.** Score tension high when the *evidence*
  conflicts with the common view, not when a take is merely spicy.
- **Feasibility is weighted lowest** because it is the easiest to change. A great
  signal the user cannot yet prove is worth surfacing with a note about what proof
  to gather.

## Rejection is an output

Rejected candidates and their reasons belong in the report. Knowing what was
considered and dismissed is a large part of what makes the ranking trustworthy,
and it stops the same weak idea resurfacing every run.
