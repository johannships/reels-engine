---
name: edit-style
description: Turn a raw talking-head take into a dynamically-edited vertical reel — full-face / full-graphic / split layouts that switch per line, generated graphic cards, word-synced captions, and a ducked music bed. The "looks like an editor made it" style, produced entirely from code. Point an agent at this, hand it a raw take, and it edits. Triggers on "edit this reel", "make it look edited", "add the dynamic layout / captions / graphics".
author: jars
version: 1.0.0
tags: [editing, reels, remotion, whisper, ffmpeg, captions, video]
---

# Edit Style — dynamic vertical reels from a raw take

You turn one raw talking-head clip (an AI clone render OR a real recording)
into a finished 1080x1920 reel that looks hand-edited: the frame never sits
still, graphics are generated (not stock), and captions land on the beat.

Nothing here is dragged on a timeline. Every decision is written as a shot
plan and rendered by code.

## The stack (all free/local except the clone)

- **Whisper** (whisper.cpp / `whisper-cli`) — word-level timestamps. This is
  what makes captions and cuts land exactly on the audio.
- **Remotion** (React → video) — every graphic panel (cards, counters,
  kinetic text) rendered to an exact duration.
- **ffmpeg** — crops, composites the layouts, burns captions, mixes the bed.
- **HeyGen** — only if the take is an AI clone; a real recording skips this.
- **Claude Code** — orchestrates all of the above.

## The three layouts (the whole look comes from mixing these)

- **FULL** — the face fills the frame. Used for hooks and personal beats.
- **GFX** — a full-screen generated graphic, no face. Used for a stat, a
  card, a statement.
- **PIP (split)** — a graphic on top, the face in a rounded card on the
  bottom. Used to show a logo/brand while you keep talking.

Switching between these, roughly every 2–5 seconds, is what reads as
"edited". A static talking head with a banner does not.

## The pipeline, in order

1. **Tighten** the take: strip dead air / long pauses so it's punchy.
2. **Transcribe** the tightened audio with Whisper → per-word `{word,start,end}`.
3. **Author the shot plan**: an ordered list. Each shot is
   `(panel_kind, layout, anchor_phrase, content)` where:
   - `layout` is FULL / GFX / PIP.
   - `anchor_phrase` is a short phrase from the script; it's matched against
     the transcript so the shot starts at the real moment those words are
     said. (Never hand-type timestamps — resolve them from the transcript.)
   - `content` (for graphic shots) is the card data: title + checklist items,
     a struck-out number, a brand logo, etc.
4. **Render the panels** with Remotion, each to its exact shot duration.
   Panels are small React components (a checklist card, a counter, a
   struck-out cost, a brand/logo screen). Keep them on-brand: one accent
   colour, generous whitespace, no third-party clutter.
5. **Composite** with ffmpeg per shot:
   - FULL → crop the take to fill 1080x1920 (frame the face: head ~13%, chin
     ~85%).
   - GFX → the rendered panel, full frame.
   - PIP → panel as background, the face cropped into a rounded card overlaid
     on the bottom.
   Concatenate the shots; lay the continuous voice track over the whole thing.
6. **Captions**: from the Whisper word timings, burn bold 1–2 word captions
   across every shot, centred in the lower third. Word-for-word, on the beat.
7. **QA**: verify the face is never cut off and every caption is within its
   shot's time window. Do not ship if either fails.
8. **Music (optional)**: generate or drop in a bed, then **sidechain-duck it
   under the voice** and keep it quiet (mean ~ -30 dB). The voice always wins.

## Rules that keep it from looking like AI slop

- Captions are timed by Whisper, never guessed. Wrong timing is the #1 tell.
- Never reuse a face crop across different takes — derive it per take from a
  face detector, or the chin gets cut off.
- One accent colour. Serif-italic OR bold-sans captions, not both at once.
- The music sits *under* the voice. If you can hear the bed over the words,
  it's too loud.
- Show, don't narrate: when the voice says "it built these graphics", the
  graphics should be on screen.

## How to use this skill

Give the agent a raw vertical (or letterboxed) talking-head clip and this
skill. It will: tighten → transcribe → author a shot plan matched to what was
actually said → render the panels → composite the layouts → burn captions →
QA → (optionally) add the ducked bed, and hand back a finished reel.

If you want the exact same look as the reference reels, keep the layout
rhythm (open on a FULL or PIP hook, break to a GFX for each key beat, land on
a GFX call-to-action) and the caption style (bold, 1–2 words, lower third).
