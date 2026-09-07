---
name: reel-ideation
description: Find short-form video ideas that are proven before you record them. Two tracks: outlier-steal (scan competitors, detect videos beating their own channel's median, extract the transferable idea, never the script) and the ownership gate (only propose videos containing something no other channel has). Use when asked for video ideas, content ideas, "what should I make today", or to evaluate whether an idea is worth recording. Works standalone in Claude Code or Codex; the reels-engine pipeline automates the same doctrine via pipeline/competitors.py and pipeline/steal.py.
argument-hint: [niche / competitor channels / your assets and receipts]
---

# Reel Ideation — proven ideas only

An idea is not good because it sounds good. An idea is good because the
audience already chose it somewhere, or because it contains something only
this creator can ship. Everything below enforces one of those two.

## Track 1 — the outlier steal

The signal is never raw views. A big channel doing big numbers is Tuesday;
a video doing 2.5x ITS OWN CHANNEL'S baseline is a proven idea.

1. **Collect** each competitor's recent uploads with view counts.
   YouTube RSS is free and reliable:
   `https://www.youtube.com/feeds/videos.xml?channel_id=<ID>`
   (carries ~15 recent videos with live view counts).
2. **Baseline** = median views of that channel's videos old enough to have
   settled (>= 7 days).
3. **Outlier** = views / median >= 2.5, with a minimum absolute floor
   (~15,000) and a freshness cap (<= 21 days). Young videos get velocity
   credit: also compute views per day.
4. **Extract the idea, never the script.** Transcribe or watch the outlier.
   Write down the transferable idea in one creator-independent sentence and
   the mechanism that made it win (curiosity engine, formula, emotion).
5. **Adapt with the creator's own assets.** If the source's idea rests on an
   asset (a repo, a tool, a method), the adaptation must use one of THIS
   creator's assets or a public resource they can legitimately point at.
   Never reuse their sentences, their examples in the same order, or their
   framing. Write from zero.
6. **Truth-check before recording.** If the adapted script narrates any
   event that has not verifiably happened, name what the creator must DO
   first so it becomes true, or soften the claim.

Default delivery is REAL FACE: if the idea won for a human talking, a human
should talk.

## Track 2 — the ownership gate

Ask of every candidate: **what does this video contain that no other
channel gets from the same feed?** Acceptable answers:

1. An asset WE ship (skill, repo, checklist, prompt) the viewer takes home.
2. A test WE actually ran, with our own recording of the result.
3. Insider translation only this creator can make from work they really do.
4. Same-day tier-1 launch coverage WITH a runnable demo.

If the answer is "nothing, it is coverage" — REJECT. A quiet day with no
video beats a competent video 50 other channels can also make.

## The formula behind the biggest winners

[modern pain everyone feels] x [obscure system from an unrelated industry]
x [free asset they can grab] x [one-word comment CTA]

The idea class that wins is "here is a crazy specific thing that exists and
you can have it" — never takes, never news reactions without a demo, never
advice. A jaw-dropping checkable fact plus something huge the viewer can
grab free, with a whiff of transgression.

## Anti-patterns (all previously proposed, all rejected)

- Vendor speed/cost news with no operator action.
- "Company launched product" reframed as a how-to without a real test.
- Any idea whose only receipt is someone else's benchmark.
- Duplicating a video the creator already made (check their history first).
