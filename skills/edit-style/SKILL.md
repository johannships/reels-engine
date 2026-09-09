---
name: edit-style
description: Turn a raw talking-head take into a dynamically-edited vertical reel — full-face / full-graphic / split layouts that switch per line, generated graphic cards, word-synced captions, and a ducked music bed. The "looks like an editor made it" style, produced entirely from code. Also covers how to WRITE the script so the voice doesn't read as AI. Point an agent at this, hand it a raw take or a topic, and it edits. Triggers on "edit this reel", "make it look edited", "add the dynamic layout / captions / graphics", "write a reel script".
author: jars
version: 1.1.0
tags: [editing, reels, remotion, whisper, ffmpeg, captions, video, script]
---

# Edit Style — dynamic vertical reels from a raw take

You turn one raw talking-head clip (an AI clone render OR a real recording)
into a finished 1080x1920 reel that looks hand-edited: the frame never sits
still, graphics are generated (not stock), and captions land on the beat.

Nothing here is dragged on a timeline. Every decision is written as a shot
plan and rendered by code.

**Working toolkit: `~/reel-style/`** — `STYLE.md` (measured spec), `tools/`
(the whole pipeline), `tools/panels-src/` (the Remotion panels), `scripts/`
(past scripts with their verified facts). Start there rather than rebuilding.

## The stack (all free/local except the clone)

- **Whisper** (`whisper-cli`, model `~/yt-thumb/models/ggml-small.en.bin`) —
  word-level timestamps. This is what makes captions and cuts land on the audio.
- **Remotion** (React → video) — every graphic panel rendered to an exact
  duration. Runs standalone by symlinking `~/Desktop/Reels Engine/studio/node_modules`.
- **ffmpeg** — crops, composites the layouts, burns captions, mixes the bed.
  NOTE: this Mac's ffmpeg is stripped — no `drawtext`, `subtitles`, `libass`.
  Text is rendered to transparent PNGs with Pillow and composited with `overlay`.
- **HeyGen** — only if the take is an AI clone.
- **Claude Code** — orchestrates all of the above.

---

# Part 1 — Writing the script

The edit can be perfect and the video still reads as AI if the words are
wrong. This is the part that gets rejected most often.

## Beat structure

Roughly 140–155 words, landing 32–40s at 3.8–4.0 words/sec.

| beat | words | job |
|---|---|---|
| Hook | 7–18 | see below — the first three words carry it |
| Setup + name + proof | ~40 | name the thing, one hard number |
| Mechanism A | ~25 | why it works / what it really is |
| Mechanism B | ~20 | what it literally does, in verbs |
| Payoff | ~35 | what the viewer gets |
| Price | ~5–10 | "it's free" / licence |
| CTA | ~8 | the comment gate |

## The hook

**The first three words decide it.** Openers that work, in order:

1. Second person — "Your AI agents…" — the subject is something they own.
2. The product's own name when it sounds impossible — "Free Claude Code…".
3. A recognisable brand — "Cash App's parent…".

Weak first-three-words: anything that starts with a concept, a preamble, or
the word "There". Never open with a rhetorical question.

## Register — how to not sound like AI

Two scripts were rejected outright for this. The tells were **not** formality.
They were *performed style*:

- **Never the "Not X. Y." antithesis.** "Not as a bot. As an actual member."
  This is a copywriting tic and it is the single most recognisable AI tell.
- **No performed asides.** "and yeah, that Block. Square, Cash App." Trying
  to sound offhand reads as more AI, not less.
- **No technical-writer register.** "the difference isn't cosmetic",
  "by a factor of forty", "is a signed event in one log".
- **No tacked-on trailing clauses.** "…, in the same place your team talks."
- **Raw numbers, never ratios.** "Their next biggest repo has 700" beats
  "by a factor of forty". Humans quote the number and let you do the maths.
- **Concrete comparisons over jargon.** "you give it access the way you'd
  give a new hire access" beats "scoped by identity, not permission flags".
- **No em-dashes or en-dashes in any script or caption.** Standing rule,
  verbatim: "Remove any em dashes or hyphens, people know it's AI." Use a
  period, a comma, or rewrite the line. This is the same tell as everything
  above and it is the one most likely to slip through.

What actually works: plain declaratives, contractions, the occasional
fragment for emphasis, and **one** first-person judgement ("that matters
because…"). Say the thing and stop. Real speech isn't stylised, it's direct.

## Two accuracy rules that bite

- **Write numbers as digits** — `2,000`, `700,000`, `47,000`. Whisper emits
  "700,000" as three tokens, so a script saying "seven hundred thousand"
  fails to align and captions silently drop words. Digits also read faster
  on screen.
- **Never claim a repo "launched today"** unless you checked `created_at`.
  Trending ≠ new, and the creation date is two clicks away. Attribute
  unverifiable vendor claims ("the repo puts it at…") rather than asserting.

---

# Part 2 — The voice (AI clone takes)

- **Pair clone N with voice N.** Mismatched pairs sound wrong. Current
  production pairing is **13 + 13**, ear-confirmed.
- **`SPEED` 1.45–1.5.** Slower reads as AI. 1.2 was rejected as "way too
  slow". 1.5 is HeyGen's ceiling.
- **One continuous render** for the whole script — chunked renders drift.
- **`elevenlabs_settings` does nothing on cloned voices** (HTTP 400, silently
  retried without). `emotion` is unavailable too. Speed and pitch are the
  only real levers.

## Silence trimming — the setting that matters most

Reels are hard-edited to almost zero pauses (a reference reel had **one
0.10s pause in 39.5s**). A raw take has ~26. Trim them — but:

**Use a −50 dB threshold. Never −38 dB.** On this voice 25% of frames sit
below −41 dB, so −38 dB classifies consonants, word tails and breath as
silence and *cuts speech*. That is exactly what "choppy / AI slop" sounds
like. Settings: `MIN_PAUSE` 0.16–0.22, `KEEP` 0.10–0.13.

**Never time-stretch the voice to fit the picture — re-time the picture.**
Audio stretching is audible at ±10%; video stretching is invisible at ±25%.
Cutting silence is inaudible at any amount, because the avatar is motionless
during a pause (measured frame delta 0.02/255).

---

# Part 3 — The edit

## The three layouts

- **FULL** — the face fills the frame. Hooks and personal beats.
- **GFX** — a full-screen generated graphic, no face. A stat, a card, a claim.
- **PIP** — graphic on top, face in a rounded card at the bottom
  (`x0 y1087 1080x833 r48`). Show a logo while you keep talking.

Switching every 2–5s is what reads as "edited". Open on FULL or PIP, break to
GFX on each key beat, land the CTA on GFX then close on FULL.

## Pipeline order

1. **Tighten** the take (Part 2 settings).
2. **Transcribe** the tightened audio with Whisper.
3. **Author the shot plan** — `(panel_kind, layout, anchor_phrase, content)`.
   `anchor_phrase` is a phrase from the script, matched against the transcript
   so the shot starts when those words are actually said. **Never hand-type
   timestamps.** Snap boundaries to script words so a cut never lands
   mid-name ("Matt" / "Pocock's").
4. **Render panels** with Remotion, each to its exact shot duration.
5. **Composite** per shot with ffmpeg, concat, lay the continuous voice over.
6. **Burn captions** (see below).
7. **Run both QA gates.** Do not ship if either fails.
8. **Add the bed** (Part 4).

## Captions — two systems, never mixed

| | graphic shots | talking-head shots |
|---|---|---|
| face | Didot / Bodoni, italic, ALL CAPS | Arial Bold / Inter Tight |
| size | ~116px, shrink-to-fit | ~64px |
| position | y 0.46–0.62 (**0.38 on PIP**) | baseline 72% of height |
| grouping | 1–2 words | 1–2 words |

- **Caption TEXT comes from the script; only the TIMING comes from Whisper.**
  Using Whisper's text put "THE CARPOTHE" on screen instead of "THE KARPATHY".
- **Shrink long words to fit** or "OVERCOMPLICATING" clips to "OVERCOMPLICAT."
- **PIP captions need `capY≈0.38`** — at 0.50 a two-line cue runs under the
  avatar card and gets clipped.
- Caption only the shots you replaced. Kept B-roll already has its own.

## Framing

Derive crops **per take** — never reuse them. A crop measured on clone 11 cut
clone 13's chin off. Solve for targets:

```
H = (chin - head) / (chin_pct - head_pct)     y0 = head - head_pct * H
W = H * (out_w / out_h)                       x0 = centre_x - W/2
```
FULL targets head 13% / chin 85%; PIP 9% / 85%.

Measure the face with **YuNet** (`pipeline/facedet.py`, needs
`opencv-python-headless`). Skin-tone thresholds fail silently against a warm
wall. YuNet's box is brow-to-chin, so top-of-head ≈ `y - 0.55h`.

---

# Part 4 — Music bed

**Synthesise it. Never licence it.** Content ID matches fingerprints of known
recordings; audio generated fresh has nothing to match, on any platform.
"Royalty-free" libraries are registered in Content ID — a licence buys a
whitelist, not immunity. CC0 gets fraudulently claimed. Generated audio is
the only option with no legitimate claim available.

**The bed must live in 400 Hz – 6 kHz.** A low ambient drone measured 99.2%
of its energy below 200 Hz — phone speakers roll that off entirely, so it was
*inaudible*, not quiet. Verify the band split with an FFT before judging
level. A plucked arpeggio over a 4-chord loop puts 91% in the audible band.

- Voice sits **~14 dB above** the bed (`BED_DB=-36 TICK_DB=-38`).
- Add a soft tick on every shot cut — this marks the edit rhythm and is
  probably a bigger retention lever than the music itself.
- Duck under a voice envelope follower.
- **Mix the bed in BEFORE loudnorm** so the whole thing normalises to −14 LUFS
  as one.

---

# Part 5 — QA gates (both must pass)

1. **Framing** — head-top >3% and chin <94% of every crop, measured with a
   real face detector. Catches the chin-cutoff class of bug.
2. **Caption sync** — re-transcribe the **finished** video and correlate word
   onsets against the audio's rising-energy envelope. Fail past 0.25s.
   Align on onsets, not word spans; spans bias the result by ~0.2s.
   A good build measures 0.00–0.09s median.


## Gesture-anchored graphics (verdict-card / pointing reels)

Learned on the bad/good/great tools reel (Sep 2026), which shipped mirrored
once. When on-screen graphics are things the speaker POINTS at:

- **Map the pointing direction before placing anything.** Extract a frame at
  every reveal word and look at where the finger actually is. A right-handed
  speaker pointing overhead sweeps RIGHT -> MIDDLE -> LEFT from the viewer's
  side, the mirror of reading order. Never assume left-to-right.
- **QA gate: finger matches reveal.** After rendering, re-extract a frame at
  each reveal moment and verify the revealed element is on the side being
  pointed at. Head-clearance and timing checks do not catch this class.
- **Every curiosity element starts hidden.** In blur-reveal formats ALL
  tiles start blurred, each unblurs only at its spoken word (word start
  minus ~0.12s). A tile that starts sharp kills the hold.
- **Face-detector outliers can be hands.** A hand raised in front of the
  face reads as head_top jumping to 20% for one frame. Before shrinking a
  layout over one outlier measurement, eyeball that frame: hand or head?
- **Logo sourcing that works:** google s2 favicon service
  (`google.com/s2/favicons?domain=X&sz=256`) covers most brands with
  transparency; GitHub org avatars (`github.com/<org>.png?size=460`) as the
  high-res fallback; wikimedia thumbs are UA-blocked from scripts. White
  tiles make opaque-white-background logos a non-issue. ALWAYS render a
  labeled contact sheet of every logo and look at it before compositing --
  this catches wrong brands and broken files in one glance.
- **Trim leading dead air by RMS, not by Whisper.** Whisper stamps the first
  word at 0.00 even when the voice starts at 0.50; measure a 20ms RMS
  envelope, cut to onset minus ~0.1s, then re-transcribe the trimmed file's
  first 2s to prove the first word survived.


## Editorial / "Vox-style" edits (learned Sep 9 2026, one cut rejected first)

Text panels on a flat color are NOT editorial style; they are slides, and the
owner reads them as AI slop. Real Vox / Johnny Harris short-form is:
- real imagery cutaways (screenshots, B-roll, the creator's own prior work) with
  slow push-ins; text sits ON imagery, never alone on a card
- "receipt" cards: source masthead + headline / repo + live star count, dropped
  over the imagery as proof
- ONE bold sans, white captions, key words in a solid yellow highlighter box;
  a yellow name lower-third in the first 3s; big stat type over darkened footage
- punch-ins on the talking head on hard beats; calm 8-12 frame ease-outs;
  numbers count up, highlighter boxes wipe in
- when the speaker points and names a graphic, a graphic MUST be there, anchored
  to the measured hand position (detect the hand; do not guess)
- build in Remotion (studio/), not Pillow overlays, so everything actually moves
- numbers: one source of truth, verified via API the day of render; QA every
  frame of a count-up's life, not one sample (a mid-ramp frame reads as a wrong
  number)

## Recurring pitfalls

- **Footage↔audio alignment is a QA gate, not an assumption.** A Remotion
  `<OffthreadVideo>` inside a `<Sequence from={X}>` restarts at frame 0 unless it
  has `startFrom={X}` — every shot after the first then shows footage from the
  wrong time while the audio is right (lips and hands stop matching). Ship-blocking,
  and invisible to face/safe-zone/caption gates. Gate: match face-box (or hand)
  trajectories of the finished file against the raw take at 0.1s across the whole
  timeline; offset must be 0.0 in every shot.
- **Never cut to moving footage of the speaker from another take.** Their lips
  move on different words and it reads as a glitch. Cutaways of prior work are
  freeze-frames with a push-in, cropped toward the graphics.
- **Count-ups must never display a wrong intermediate value** where the number
  is a claim (a frame reading "54% automated"). Hard-in claims; animate only
  decoration.
- **Platform safe zones (shipped cropped once).** Instagram crops reels to
  4:5 in the feed and lays UI over the edges of the full 9:16 view. Keep ALL
  critical graphics (cards, labels, text) inside: top >= 220px, bottom
  <= 1620px, sides >= 60px on a 1080x1920 frame. A card row that starts at
  y=60 gets its labels cut off on phones. QA gate: check the 4:5 center crop
  (1080x1350, y 285-1635) still shows every graphic that carries meaning.
- **Forward panel props generically.** Copying a hardcoded list of prop names
  means a new panel kind silently gets `undefined` and Remotion dies with
  "outputRange must contain only numbers".
- **Never hardcode content inside a panel.** Twice a panel shipped showing a
  *previous video's* repos and checklist. Panels take data as props, always.
- **Sample frames proportionally**, not at fixed timestamps — a shorter take
  makes fixed offsets run past the end and the build crashes.

## Rules that keep the edit from looking like AI slop

- Captions timed by Whisper, never guessed. Wrong timing is the #1 tell.
- One accent colour. Serif-italic OR bold-sans captions, not both at once.
- The music sits *under* the voice. If you hear the bed over the words, it's
  too loud.
- Show, don't narrate: when the voice names a thing, that thing is on screen.
- Use **official logos** where a brand is named — org avatars from the
  GitHub API are the real marks.
