<!--
strategy-memo.md
Produced by /content-strategist from signal-report.md. Consumed by /brief-builder.
The `## Selected concepts` section below is a contract. Keep the heading and the
field names exactly as written, or the next skill cannot read it.
Delete every comment block before sharing.
-->

# Strategy memo: <topic or brand>

## Run metadata

<!-- status: complete | provisional -->

- memo_id: `MEM-001`
- status: `complete`
- upstream: `signal-report.md` (`SIG-RUN-001`, run `YYYY-MM-DD`)
- audience: <who, and what they already believe>
- run date: `YYYY-MM-DD`

<!-- If the signal report was missing or partial, say so here and never fill the gap. -->

## Position

<!-- Two or three sentences. What this body of work argues, and who it is arguing
     against. If it could be said by any competitor, it is not a position. -->

<...>

## Signals used

| signal_id | why it earned a concept | confidence carried forward |
|---|---|---|
| `SIG-001` | <...> | high |

## Signals declined

<!-- Surface, do not silently drop. A signal that vanishes without a reason gets
     re-proposed next run and the user cannot tell whether you considered it. -->

| signal_id | reason declined |
|---|---|
| `SIG-004` | Real, but we own no proof and cannot get it this quarter. |

## Selected concepts

<!-- CONTRACT SECTION. Exact heading and exact field names.
     channel must be one of: youtube | linkedin | x | newsletter | short-form | blog
     cta is one CTA, or the literal string "no CTA".
     /brief-builder takes exactly ONE concept_id per run. -->

- concept_id: CON-001
  source_signals: [SIG-001, SIG-003]
  channel: linkedin
  promise: <one sentence: what the reader gets if they finish>
  cta: <one CTA, or the literal string "no CTA">

- concept_id: CON-002
  source_signals: [SIG-002]
  channel: youtube
  promise: <one sentence>
  cta: no CTA

## Concept detail

<!-- One block per concept above. This is what /brief-builder turns into beats.
     Give it the argument, not a topic list. -->

### `CON-001`: <working title>

- audience tension: <the belief they hold, and what complicates it>
- message architecture:
  1. <claim the piece establishes first>
  2. <claim it establishes next>
  3. <what it leaves the reader with>
- proof we already own: <analytics, transcript, screenshot, repo, customer note>
- proof we still need: <what, and who can get it>
- format hypothesis: <format and rough length; the brief confirms it>
- why now: <dated reason, or say plainly that it is evergreen>

## Sequencing

| order | concept_id | why in this position |
|---|---|---|
| 1 | `CON-001` | Proof is already in hand; nothing blocks production. |
| 2 | `CON-002` | Depends on the demo recording landing first. |

## Risks and constraints

<!-- Named risks only. "Might not perform" is not a risk, it is a mood.
     This suite does not promise reach, revenue, leads, or ranking. Do not put a
     performance forecast here. -->

- <risk>. Mitigation: <...>. Owner: <who>

## Open questions for the user

- <question that changes the strategy depending on the answer>
