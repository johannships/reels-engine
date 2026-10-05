---
name: edit-style
description: Turn a raw talking-head take into a dynamically-edited vertical reel — full-face / full-graphic / split layouts that switch per line, real UI and official-logo panels, captions on every word, voice + synthesised SFX (no music bed). The "looks like an editor made it" style, produced entirely from code, with hard QA gates (caption sync on the final render, A/V length, loudness, contact sheet, claims). Also covers how to WRITE the script so the voice doesn't read as AI. Point an agent at this, hand it a raw take or a topic, and it edits. Triggers on "edit this reel", "make it look edited", "add the dynamic layout / captions / graphics", "write a reel script".
author: jars
version: 1.2.1
tags: [editing, reels, remotion, whisper, ffmpeg, captions, video, script]
---

# Edit Style — dynamic vertical reels from a raw take

You turn one raw talking-head clip (an AI clone render OR a real recording)
into a finished 1080x1920 reel that looks hand-edited: the frame never sits
still, graphics are real UI, real logos or generated (not stock), and
captions land on the beat.

Nothing here is dragged on a timeline. Every decision is written as a shot
plan and rendered by code.

**Keep a working toolkit folder** — a `STYLE.md` (your measured spec), the
pipeline scripts, the Remotion panels, and past scripts with their verified
facts. Start there rather than rebuilding. One-command engine for the house
formats: the **house-reel-edit** skill (`skills/house-reel-edit`). Small gate
and capture scripts: [`tools/`](tools/) next to this file.

## The stack (all free/local except the clone)

- **Whisper** — word-level timestamps. This is what makes captions and cuts
  land on the audio. `whisper-cli` + `ggml-small.en.bin` for
  the transcript and SRT text; **mlx-whisper large-v3-turbo** for caption cue
  TIMING (small.en drifts 0.1–0.4s on the same audio, measured 2 Oct 2026).
- **Remotion** (React → video) — every graphic panel rendered to an exact
  duration. Runs standalone by symlinking this repo's `studio/node_modules`.
- **Playwright, headless only** — real screen footage (see Screens).
- **ffmpeg** — crops, composites the layouts, burns captions, mixes voice + SFX.
  NOTE: a stripped ffmpeg build may have — no `drawtext`, `subtitles`, `libass`.
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

# Part 2 — The voice

**Default is a raw take from the creator; the agent edits.** Clone only as a fallback.

## AI clone takes

- **Pair clone N with voice N.** Mismatched pairs sound wrong. Current
  production pairing is **11 + 11** (owner revert 31 Aug 2026; clone 13 rejected in production). Speed **1.5**, ear-approved 12 Sep 2026.
- **`SPEED` 1.45–1.5.** Slower reads as AI. 1.2 was rejected as "way too
  slow". 1.5 is HeyGen's ceiling.
- **One continuous render** for the whole script — chunked renders drift.
- **`elevenlabs_settings` does nothing on cloned voices** (HTTP 400, silently
  retried without). `emotion` is unavailable too. Speed and pitch are the
  only real levers.

## Raw takes

- **iPhone HDR (HLG / Dolby Vision) must be tone-mapped to SDR BT.709 first**,
  or it grades washed out. Check the fps survived: avconvert once turned a
  60 fps take into 18.75 fps.
- **Use Apple's tone map, never hand-rolled HLG maths** (3 Oct 2026). Reel1 on
  2 Oct used a numpy HLG curve (`gain 0.8`) and shipped overexposed and orange:
  face median luma 148-167 vs Apple's 116, ~10% of pixels clipped, and it was
  only caught after posting. Extract source frames with
  `tools/hdr_to_sdr_frames.sh raw.mov need.txt src 1350 2400 60` (AVAssetReader
  → BT.709, VFR-safe, all frames, drop-in for an ffmpeg `fps=60` extract).
  Then put one face frame next to `avconvert -p Preset1920x1080` of the raw and look.
- **Encode the final as tagged limited-range BT.709**, not the yuvj420p that
  JPEG frames give by default:
  `-vf "scale=in_range=pc:out_range=tv:in_color_matrix=bt601:out_color_matrix=bt709,format=yuv420p,setparams=range=tv:color_primaries=bt709:color_trc=bt709:colorspace=bt709" -color_range tv -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:v libx264 -profile:v high -preset slow -crf 17 -c:a aac -b:a 320k -ar 48000 -movflags +faststart`.
  `tools/final_gates.sh` now fails anything else (or < 8 Mbps).
- **Bitrate: never below 8 Mbps, aim for ~14.** CRF 17 usually lands there on
  busy frames; when the gate reports less (flat graphics compress hard), swap
  `-crf 17` for `-b:v 14M -maxrate 20M -bufsize 28M`. Platforms re-encode
  anyway; a thin upload just gives them less to work with.
- **DJI Pocket 3 "glamour" .mov is SDR but tagged FULL range** (5 Oct 2026).
  It needs no tone map, but decode it as full range and output limited-range
  BT.709, or faces render ~12 levels too dark with crushed blacks:
  `zscale=rangein=full:range=limited` where zscale exists, otherwise
  `-color_range pc` on the input plus
  `scale=in_range=pc:out_range=tv:in_color_matrix=bt709:out_color_matrix=bt709`
  (frame extracts: `scale=in_range=pc:out_range=pc` so the JPEGs keep the
  real levels). Check the tag first:
  `ffprobe -v error -select_streams v:0 -show_entries stream=color_range,color_transfer -of csv=p=0 raw.mov`
  (`pc,bt709` = this case; `arib-std-b67` = iPhone HLG, use the Apple tool).
- **Skin-luma gate for every raw take:** the final's face must sit within ~2
  levels of the source at the same moment.
  `tools/skin_luma_check.sh raw.mov <t_src> final.mp4 <t_final> <src_box> <final_box>`
  (boxes are `x:y:w:h` on a patch of skin; it decodes each file with its own
  range). A range mistake shows up as ~10+ levels.
- **Keep the last take** of any repeated line. Cut dead air and false starts.
  Never cut mid-word.
- **Cut private third-party detail** he says in passing (a friend's employer,
  a client, money). List the cut in QA so the owner can restore it.

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
- **GFX** — a full-screen graphic, no face: real UI, a stat, a card, a claim.
- **PIP / split** — graphic on top, face in a card at the bottom
  (`x0 y1087 1080x833 r48`). Show a logo or a screen while you keep talking.

Switching every 2–5s is what reads as "edited". Open on FULL or PIP, break to
GFX on each key beat, land the CTA on GFX then close on FULL.

## The hook: official brand logo (owner rule, 2 Oct 2026)

"The hook can use official brand logos. If the video is talking about Claude,
show the Claude logo, for pattern recognition."

- In the hook (first ~2s), when the topic is a named product or brand
  (Claude, GitHub, Metricool, OpenAI, Blender…), show that brand's
  **official** logo.
- Fetch it from the brand's official press / brand page or the official
  site's own SVG. Never redraw it or AI-generate it.
- Show it as a clean panel element near the caption (the split top panel or
  a card above the caption), never a pill or sticker.
- Don't alter its colours or proportions. Don't imply endorsement: it names
  the subject (nominative use), nothing more.
- Cache every logo in `brand-logos/<brand>.<svg|png>` with a
  `SOURCES.md` line per file: brand, source URL, date fetched. Reuse from
  the cache, and re-check the source if the brand rebrands.

## Pipeline order

0. **One folder per reel, everything inside it.** Each edit (and each
   parallel editor agent) keeps ALL its work files (frames, panels, audio,
   renders, logs) inside its own reel folder. Never use a shared `_work`
   dir: a parallel run wiped another reel's shared work folder on 5 Oct 2026.
   **Adapting a source reel?** Pull its keyframes (a contact sheet every
   ~0.5s) and use them as the layout and timing reference: which layout
   when, how long each beat holds, where the text sits. Rebuild it with your
   own real assets (your take, live screenshots, official logos). Never
   reuse its footage or graphics.
1. **Prep** the take (HDR → SDR, fps check) and **tighten** it (Part 2).
2. **Transcribe** the tightened audio with Whisper.
3. **Author the shot plan** — `(panel_kind, layout, anchor_phrase, content)`.
   `anchor_phrase` is a phrase from the script, matched against the transcript
   so the shot starts when those words are actually said. **Never hand-type
   timestamps.** Snap boundaries to script words so a cut never lands
   mid-name ("Matt" / "Pocock's").
4. **Capture screens and fetch logos** (below). Look at them before using them.
5. **Render panels** with Remotion, each to its exact shot duration.
6. **Composite** per shot with ffmpeg, concat, lay the continuous voice over.
   Run every render under **`nice -n 15`**: overload has dropped the
   creator's mic audio while they were recording. Look-dev on stills first, then do one
   full render.
7. **Burn captions** on every word (below).
8. **Mix voice + SFX and master** (Part 4).
9. **Run the QA gates** (Part 5). Do not ship if any fails.

## Captions — every word, from the first frame

Burned-in captions run continuously from the first word to the last. Punch
phrases and kinetic type are extra, never a replacement.

| | graphic shots | talking-head shots |
|---|---|---|
| face | Didot / Bodoni, italic, ALL CAPS | Arial Bold / Inter Tight |
| size | ~116px, shrink-to-fit | ~64px |
| position | y 0.46–0.62 (**0.38 on PIP**) | baseline 72% of height |
| grouping | 1–2 words | 1–2 words |

- **Caption TEXT comes from the script; only the TIMING comes from Whisper.**
  Using Whisper's text put "THE CARPOTHE" on screen instead of "THE KARPATHY".
- **Fix name spellings** in captions and the SRT: Claude (not Cloud/Claud),
  Metricool, GitHub, Fable, Opus, Sonnet, Haiku, and every product named in
  the reel. Keep a fix map and apply it to every Whisper pass.
- **Cue timing comes from a re-whisper of the FINAL audio** (turbo), not the
  raw. Raw-take times shifted by the edit failed the sync gate twice on 2 Oct.
- **Shrink long words to fit** or "OVERCOMPLICATING" clips to "OVERCOMPLICAT."
- **PIP captions need `capY≈0.38`** — at 0.50 a two-line cue runs under the
  avatar card and gets clipped. Captions never cover the mouth.
- Caption only the shots you replaced. Kept B-roll already has its own.

## Screens — clock-controlled headless capture

Screen-recording a monitor (or filming it with a phone) gives jitter, moiré
and a menu bar full of private things. Capture instead:

- **Playwright, headless only.** Never open a visible browser window.
- **Freeze the page clock**: an init script replaces `performance.now`,
  `Date.now` and `requestAnimationFrame`, then step it at 60 Hz and keep every
  2nd frame for 30 fps. Every frame is exact, however slow the machine is.
  Script: `tools/capture_clock.js`.
- Capture at the reel's size (e.g. 432x768 CSS at 2.5x = 1080x1920).
- Public pages logged out. Recapture live numbers (stars, trending) the day
  of render and note the capture time in QA.
- Highlight with outline boxes anchored to the real UI element, wiped in on
  the spoken word. Pan and push-in on the capture; no fake UI. A vendor's
  claim is shown as their own screenshot with "source: X README", never
  restated as your graphic.

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

# Part 4 — Audio: voice + SFX, no music bed

Raw-voice videos ship **voice + synthesised SFX only**. No music bed.

- **Crisp voice chain:** high-pass 70–80 Hz, light denoise (`afftdn` nr ~8).
- **SFX are synthesised, never licensed.** Content ID matches fingerprints of
  known recordings; generated audio has nothing to match. "Royalty-free"
  libraries are registered in Content ID and CC0 gets fraudulently claimed.
- Few SFX: a sub hit on the hook word, a soft tick or whoosh on graphic cuts,
  clicks on highlights. 12–20 dB under the voice peak. If you notice them
  over the words, they're too loud.
- **Master to −14 LUFS integrated, ≤ −1.5 dBTP** with gain + a true-peak
  limiter, iterated and measured on the final mp4. loudnorm two-pass failed
  on peaks on 2 Oct, and its linear mode silently falls back to dynamic.

---

# Part 5 — QA gates (all must pass)

`tools/final_gates.sh final.mp4` runs 3, 4 and the contact sheet;
`tools/caption_sync_gate.py` runs 2. Write results to `QA.md`.

1. **Framing** — head-top >3% and chin <94% of every crop, measured with a
   real face detector. Catches the chin-cutoff class of bug.
2. **Caption sync, per chapter, on the FINAL render.** Re-transcribe the
   finished mp4 (turbo), match caption words to it, and gate each chapter:
   **median ≤ 0.12s, p95 ≤ 0.25s**. Cross-check against the audio's
   rising-energy onsets. On a fail: retime that chapter's cues to the final
   words, re-render only the affected frames, re-whisper, re-gate. Loop until
   every chapter passes (reel4 needed two loops on 2 Oct).
3. **Audio length == video length** (within one frame), checked with ffprobe
   right after every render. Overload has silently dropped audio before.
4. **Loudness** — −14 ±1 LUFS, true peak ≤ −1.5 dBTP. No black frames.
5. **Contact sheet** — 12 evenly spaced frames in one image. **Open it and
   look at it** before saying done. Fail on: any pill, badge or sticker,
   captions over the face, a wrong or distorted logo, private data, graphics
   cut by the safe zones or the 4:5 feed crop. Every label and card must sit
   inside the 4:5 centre crop (1080x1350, y 285-1635), not just the captions.
6. **CLAIMS** — no number on screen without a source file you can name
   (path + date). Measured ranges beat spoken roundings ("67–86 sec", not
   "about a minute"). Anything he says on camera that the source doesn't support
   stays off screen and is listed under CLAIMS in `QA.md` for the owner to decide.
   **Verify every on-screen number live** (API or the live page, the day of
   render) and note the capture time; a number from memory or an old note is
   not a source. **A spoken line that is factually false gets cut** from the
   edit, not captioned, and is flagged under CLAIMS with what the source says.
7. **First word survives** — re-whisper the first 2s after any head trim.
8. **Colour** — `final_gates.sh` checks tags and bitrate (yuv420p, tv range,
   BT.709, >= 8 Mbps); `tools/skin_luma_check.sh` checks the face is within
   ~2 levels of the source (Part 2).

Deliverables: `final.mp4`, `contact.png`, `captions.srt` (re-whisper of the
final, spellings fixed), `QA.md`, and a `LOG.md` written as you go (agents
die after 10 min silent).

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
- **Logo sourcing:** official press / brand page or the site's own SVG first
  (see the hook rule). GitHub org avatars (`github.com/<org>.png?size=460`)
  are the org's own mark for repos. Favicon services
  (`google.com/s2/favicons?domain=X&sz=256`) are a low-res last resort,
  never for the hook. Wikimedia thumbs are UA-blocked from scripts. ALWAYS
  render a labeled contact sheet of every logo and look at it before
  compositing: it catches wrong brands and broken files in one glance.
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
  Captions at y 1612 graze the crop; y ~1560 is safe.
- **Forward panel props generically.** Copying a hardcoded list of prop names
  means a new panel kind silently gets `undefined` and Remotion dies with
  "outputRange must contain only numbers".
- **Never hardcode content inside a panel.** Twice a panel shipped showing a
  *previous video's* repos and checklist. Panels take data as props, always.
- **Sample frames proportionally**, not at fixed timestamps — a shorter take
  makes fixed offsets run past the end and the build crashes.
- **Nothing private on screen**: no finances, revenue, client names, brand or
  account ids, or internal files. Tables copied from internal files drop any row
  with a dollar figure or a client.

## Rules that keep the edit from looking like AI slop

- **No floating pills, bubbles or tags. Ever.** (owner, 28 Sep 2026: "remove
  the top bubble thing and never have those... looks like AI slop.") Banned:
  - glass or rounded "pill" badges floating over or above the head, e.g. "Opus 5.5" or "Claude Code"
  - a corner tag on every frame, e.g. "AI EDIT", "AI AGENTS" or "PART 1"
  - joke or "random graphic" stickers and chip clusters
  - a REC chip

  Instead, name a tool with its **real product UI or official logo** as a proper cutaway or split panel: a screenshot on a card, or the actual app window. Otherwise let the caption carry it. Graphics must look like a professional editor made them: fewer, bigger, purposeful, and anchored to a layout (split top panel, full-screen cutaway, lower third). Nothing should float over the face.

  QA gate: in the contact sheet, any small badge, pill or sticker = fail.
- **No code-generated motion-graphics sizzle.** Use founder footage and real
  product screens.
- Captions timed by Whisper on the final audio, never guessed. Wrong timing
  is the #1 tell.
- One accent colour. Serif-italic OR bold-sans captions, not both at once.
- Show, don't narrate: when the voice names a thing, that thing is on screen.
- Use **official logos** where a brand is named (hook rule above).

---

## Changelog

- **1.2.1 (5 Oct 2026)** — DJI Pocket 3 full-range decode + skin-luma gate
  (`tools/skin_luma_check.sh`); bitrate floor 8 Mbps, aim ~14; one folder per
  reel, no shared `_work` dir for parallel edits; labels and cards inside the
  4:5 crop; adapting a source reel = its keyframes as layout/timing reference
  with your own real assets; verify every on-screen number live; cut and flag
  factually false lines.
- **1.2.0 (2-3 Oct 2026)** — official brand logo in the hook; caption sync
  gated per chapter on the final render; Apple HDR tone map
  (`tools/hdr_to_sdr_frames.sh`) and the colour/encode gate in
  `tools/final_gates.sh`.
