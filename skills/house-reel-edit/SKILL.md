---
name: house-reel-edit
description: Edit raw talking-head clips into a finished vertical reel in the house style that shipped on 28 Sep 2026 (six reels the owner approved). Two named formats, SPLIT-GRAPHIC (light graphic panel on top, face below, mono caption box on the seam, full-graphic beats, hard cuts) and PREMIUM TALKING-HEAD (warm grade, word-pop captions, dark glass panel on top, big type behind the matted head, split for UI demos). One command, driven by a JSON beat sheet the agent writes per reel. Voice + synthesised SFX only, -14 LUFS, captions on every word from a re-whisper of the final audio, hard QA gates (contact sheet, black frames, caption sync, loudness, OCR for private data, no-pill detector). Triggers on "edit this reel", "house style", "split graphic", "premium talking head", "edit like the 28 Sep reels".
author: jars
version: 1.0.0
tags: [editing, reels, captions, whisper, ffmpeg, sfx, qa, video]
---

# House reel edit

You turn one or more raw clips of the owner talking into a finished 1080x1920 reel that looks like
an editor made it. Every content decision lives in one JSON **beat sheet** you write per reel. The
library (`house/`) holds none: it draws, times, mixes and checks.

```
skills/house-reel-edit/
  bin/house-edit          one-command entry point (also ../../bin/house-edit)
  house/                  the library: prep, transcribe, face, captions, split, premium, sfx, audio, render, qa
  examples/               a beat sheet for each format
  tests/                  rule tests (validator + no-pill detector), run: python3 tests/test_rules.py
```

## Setup (once per machine)

- `ffmpeg` with `h264_videotoolbox` (macOS) or it falls back to libx264; `whisper-cli` (whisper.cpp) + a ggml model (small.en is enough).
- Python 3.10+: `pip install numpy pillow opencv-python-headless`. Optional: `rembg` for a true person matte (premium big type behind the head; without it a soft head-and-shoulders mask from the face box is used).
- Fonts are **not** in this repo: put `Inter-Var.ttf` and `JetBrainsMono-Variable.ttf` (+ optional `Playfair-Italic.ttf`) in a folder. All free on Google Fonts.
- Point the engine at them (env vars or `~/.config/house-edit/config.json`):
  `HOUSE_FONTS=~/path/to/fonts HOUSE_WHISPER_MODEL=~/path/to/ggml-small.en.bin`
- Private denylist for the OCR gate (client names, people, anything that must never be on screen):
  `~/.config/house-edit/denylist.txt`, one term per line. **Never commit it.**

## Run it

```
# 1. prep + transcript. Writes JOB/beats.skeleton.json (transcript with word times, sentence stubs, keyword guess) and stops.
bin/house-edit clip1.mov clip2.mov --format split --job ~/reels/<slug>

# 2. write JOB/beats.json (see "The beat sheet"), then LOOK at stills before any render:
bin/house-edit --format split --job ~/reels/<slug> --beats ~/reels/<slug>/beats.json --stills 0.3,4.9,12,20.5

# 3. the one render + QA gates + Telegram copy + POST.md:
bin/house-edit --format split --job ~/reels/<slug> --beats ~/reels/<slug>/beats.json
#    quick check of the first 10 s only:  add --limit 10
```

Exit codes: 2 = write the beat sheet, 3 = beat sheet broke a hard rule (the log says which), 4 = a QA gate failed.
Every stage is cached in the job folder and every write is atomic; if an agent dies, re-run the same command.
Progress is appended to `JOB/PROGRESS.log`.

---

## The pipeline

1. **Transcribe** each raw clip (whisper-cli, word timings). Caption TEXT comes from whisper corrected by the beat
   sheet's `caption_fixes`; only the TIMING comes from whisper.
2. **Pick takes.** Pass clips in script order. "retake" said as its own word drops the flubbed sentence up to the
   marker (the last take wins). Anything else: `manual drops` or leave the clip out.
3. **Tighten pauses** (measured on the 28 Sep reels; frame-aligned at 30 fps, 8 ms fades, never time-stretch the voice):
   | | split | premium |
   |---|---|---|
   | first/last-word gate | -50 dBFS | -50 dBFS |
   | internal pause gate | -42 dBFS | -42 dBFS |
   | pauses at least | 0.16 s | 0.25 s |
   | shrink them to | 0.10 s | 0.20 s |
   | head / tail | 0.06 / 0.08 s | 0.06 / 0.10 s |
   Never gate at -38 dBFS (it clips soft first consonants). Onset needs 60 ms sustained speech (ignores clicks).
4. **Pick the format** (next section).
5. **Graphics that land on spoken words.** Every element's `at` is a word anchor (`"deepline"`, `"email#2"`,
   `"ICP.end"`, `"pricing+0.2"`), resolved against a whisper pass over the FINAL audio. When the voice names a thing,
   that thing is on screen. Something new lands about every 1.3 s.
6. **Captions on every word**, from frame 1, timed the way the approved 28 Sep reels were: the FINAL mastered
   audio is re-whispered **one line at a time** (lines = sentences of the first transcript, long ones split near
   a comma; 0.15 s pad), the first transcript keeps the words and order, and each start snaps to the nearest energy
   onset within +/-0.15 s. A chunk that would show under 0.25 s is re-split with its neighbour. Do NOT cut the audio
   at arbitrary silences for whisper: on 29 Sep that collapsed stamps (four chunks inside 60 ms) and a
   same-method QA gate passed it.
7. **Voice + synthesised SFX only.** No music bed, ever. The SFX kit is synthesised from maths (`house/sfx.py`),
   so Content ID has nothing to match. Crisp voice chain (80 Hz high-pass, -2.5 dB at 260 Hz, +2.5 dB at 3.8 kHz,
   +1.5 dB at 9 kHz, 2.5:1 compression).
8. **Master to -14 LUFS integrated, -1.5 dBTP** (gain + true-peak limiter, iterated; loudnorm's linear mode silently
   falls back to dynamic, so it is not used).
9. **QA gates** (below). Then LOOK at the contact sheet yourself.
10. **Telegram-size copy**: one preset, 1280 px tall, ~6 Mbps, well under the 50 MB bot limit (`final_tg.mp4`).
11. **POST.md**: title, caption (plain lines, ready to paste), keyword, ManyChat DM, hashtags, checks. DRAFT until the
    owner approves. Nothing is posted or scheduled by this skill.

---

## Choose the format

| Pick **SPLIT-GRAPHIC** when | Pick **PREMIUM TALKING-HEAD** when |
|---|---|
| it is a tool / product / "how it works" reel | it is a founder, opinion, lesson or story reel |
| the lines name many things (a stack, steps, providers, a prompt) | the hook is a claim, a feeling or one number |
| you would need more than ~5 distinct visuals | 2-4 big moments carry it (a word, a number, a checklist) |
| recorded as several short clips, one line each | recorded as one continuous take |
| examples: Deepline cold outreach, the YouTube-skills remake | examples: EDIT (pipeline checklist), CHECK (QA gate), Volume, TALENT |

A premium reel can still show a product: use a `split` scene (face slides down, illustrative UI on top) for the demo
beat only. Never mix the two caption systems in one reel.

## SPLIT-GRAPHIC (measured spec)

- Canvas 1080x1920 @30. **SPLIT**: graphic panel y 0-680, flat #EEECEB with a 1 px #E4E2E0 grid at 90 px pitch; face
  panel y 680-1894, hard edge, no rounded corners, no glow seam, no head breakout. Face framed per clip:
  head-top ~10%, chin ~66% of the panel, centred.
- **FULL GRAPHIC** (3-4 times a reel, ~25% of runtime): the whole frame is the grid canvas, the voice continues.
  Use it for the list/system, the reveal and the setup beats. No face-only layout.
- Safe areas: panel y 220-660, x 60-1020 (the IG UI covers the top ~220 px). Full y 220-1620; must survive the 4:5
  feed crop (y 285-1635). Keep full-graphic content clear of the caption box band (y 630-720).
- **Cuts between layouts are hard.** No whips, dissolves or push-ins; the face is static. Inside a panel, elements
  animate in: pop (scale 0.9 to 1.0, ease-out-back 1.6, 0.30 s) or slide from the left (ease-out-cubic).
- **Captions**: JetBrains Mono 800, 52 px, ALL CAPS, +6 px tracking, white on #38343B at 95%, radius 10, padding
  28x18, 2-3 words on one line, no punctuation, no dashes, box centred on y 675 (straddles the seam), same y in full
  graphics, hard swap per chunk (no pop, no karaoke, no colour). Hidden for the first 0.35 s of a full-graphic shot.
  Function words are never stranded at the end of a chunk. Emphasis lives in the graphics, never the captions.
- Palette: canvas #EEECEB, terracotta #D26E51 accent, ink #1F1E1D, grey #6B6B6B, red #E5484D (strike/stamp),
  green #22A55B (done/positive), dark windows #1F1E1D. Cards white, radius 20, shadow 0 8 24 rgba(0,0,0,.10).
  Tiles: rounded square, terracotta, white line icon, grey 16 px label below.
- Face panel gets the house grade (warm, gentle S-curve, soft blacks). No grain on the flat canvas.
- **SFX**: few. Tick on the first frame, one sub-boom on the hook word (the only loud moment, ~12 dB under voice RMS,
  dead stop), pop on each cut to a full graphic, ticks on small landings, typing under the keyword. Everything else
  18-22 dB under the voice. At most 3 cues per 10 s. No whooshes on hard cuts.

Elements (`type`): `title`, `label` (spaced mono header, plain text), `tile`, `tiles` (row, optional arrows and
`check_at` ticks), `grid` (one icon becomes N; `highlight` + `highlight_at`), `card` (icon + title + sub),
`image` (a real screenshot you captured), `logo` (an official logo file on a white tile), `strike` (red diagonal
for "X is dead"), `arrow`, `line` (drawn progressively), `progress`, `stamp` (a rotated outline word on a card, max
once), `window` (dark app window, lines type in on their words, **labelled ILLUSTRATIVE** unless it is a real
capture), `checklist` (rows tick on spoken words, optional `counter`), `comment_cta` (COMMENT THIS WORD + a comment
field with the keyword typing in + a DM card). Icons: see `house/icons.py` (`ICONS`).

## PREMIUM TALKING-HEAD (measured spec)

- Full-frame face on a **virtual camera** from a smoothed face track: face box ~19% of frame height, eyes at ~y 800,
  zero-phase smoothing (no jitter). Jump cuts become punch-ins alternating 1.00 / 1.10-1.16, with a 0.27 s settle and a
  2.2% push-in per shot.
- **House grade** (R x1.03 +0.008, G x1.005, B x0.94, 22% smoothstep S-curve, saturation x1.04, lift 0.018, gain 0.975)
  + film grain 0.022, stronger in the midtones.
- **Captions**: Inter 900, 84 px, word-by-word pop (0.12 s ease-out-back, scale 0.8 to 1), max 3 words / 16 chars,
  centred at y 1640 (y 930 while split, between the UI and the face), never over the face, mic or hands. One accent word per phrase from
  `accents`: `"red"` (#FF5E5A) or `"serif"` (Playfair italic). Offwhite #EDF3FF for type.
- **Dark glass panel** at the top (`glass_panel`): x 60-1020 from y 206, 20 px backdrop blur, darkened, offwhite
  hairline, radius 44. Rows go active (red highlight + spinner) then done (red check) on spoken words; header in spaced
  mono with a red dot; optional counter. Name a tool with its **real logo** in a row (`logo`: a file path), never a pill.
- **Big type behind the head** (`behind_head`): 520 px Inter 900 word or spoken number between the background and the
  person (rembg matte, or the face-box mask fallback), 1.4 s, scale 1.18 to 1.0, glow + shadow, background dimmed 30%.
  Optional `strike_at` for a struck word.
- **Split for UI demos** (a scene with `"layout": "split"`): the face slides down 470 px over 0.30 s (smoothstep), the
  top shows a dark `window` (ILLUSTRATIVE label) over the blurred frame.
- `title` (big type in front, over a top dim), `end_card` (glass card: COMMENT THE WORD, the keyword in red at 150 px
  with a glow, one serif line, a chat icon). 1-2 `whip` transitions max, at chapter turns only.
- **SFX**: sub on the hook, whoosh when a panel slides in, click on each tick, one ching on a money/number payoff,
  sub + click on the end card. At most 5 cues per 10 s, ~12-20 dB under the voice.

---

## The beat sheet

`JOB/beats.json`, written by you from `beats.skeleton.json`. Full examples: `examples/beats.split.json`,
`examples/beats.premium.json`.

```json
{
  "format": "split",
  "keyword": "CLAUDE",                      // must be spoken; else keyword_flagged_to_owner: true after you flag it
  "caption_fixes": {"a email": "an email"}, // whisper -> what he actually said (names, brands, grammar)
  "accents": {"free": "red"},               // premium only
  "measured": [{"value": "51.2k", "source": "GitHub API stargazers_count", "date": "2026-10-02"}],
  "sfx": [{"at": "killed-0.03", "sfx": "hook_subboom", "under_db": 12, "why": "hook word"}],
  "scenes": [
    {"from": 0, "layout": "split", "elements": [
      {"type": "card", "title": "Outreach", "sub": "by hand", "icon": "list", "at": 0},
      {"type": "strike", "at": 0}]},
    {"from": "it brings", "layout": "full", "elements": [ ... ]}
  ],
  "post": {"title": "", "caption": "", "dm": "", "hashtags": [], "notes": []}
}
```

- A scene runs from its `from` anchor to the next scene. Elements default to `at` = scene start, `until` = scene end.
- Positions are pixels inside the region (panel 0-680 or full 0-1920); defaults centre the element in the safe area.
- The validator runs before anything renders and refuses: banned types or keys (pill, badge, chip, tag, sticker, rec,
  bubble, logo_pill, corner_tag, emoji); any number on screen that is not spoken and not in `measured` (step numbers
  need `"not_a_claim": true`); a keyword that is not spoken and not flagged; illustrative UI without its label.
- Look at the `WARN anchors not found` line: a missing anchor hides that element.

## Hard rules

- **No floating pills, bubbles, corner tags, REC chips or stickers.** (Johann, 28 Sep 2026: they read as AI slop.)
  There is no drawing path for them in this library, the validator rejects them, and the QA pill detector fails the
  render if one appears. Name a tool with its real product UI (a screenshot on a card, the actual app window) or its
  official logo inside a panel, or let the caption carry it. Fewer, bigger, anchored graphics; nothing floats over the face.
- **Official brand logo in the hook.** When the topic is a named product or brand (Claude, GitHub, OpenAI, Blender...),
  the first ~2 s show its official logo (`logo` element), fetched from the brand's press/brand page or its site's own
  SVG, never redrawn or AI-generated. A clean panel element near the caption, never a pill; colours and proportions
  untouched; nominative use only (no implied endorsement). Cache in a `brand-logos/` folder with the source URL per file.
- **Numbers only if spoken or measured** (same source, matched window, with the source and date in `measured`).
  Never quote a peak without its decay. A count-up must never show a wrong intermediate value for a claim: hard-in claims.
- **Label illustrative UI as illustrative** (`window` does it by default; only a real capture may drop it).
- **No client names or private data** on screen or in POST.md: no inbox, CRM, bank, call-recorder or member data, no
  candidate names or emails, no terminal paths with a home folder. Public datasets and the owner's own public work only.
  The OCR gate backs this up; it does not replace your judgement.
- **Original icons only.** Never copy another creator's frames, graphics, mascot, cards or audio, even when remaking a
  reference reel's style. Icons here are drawn from code; SFX are synthesised.
- **The keyword card only uses a keyword that is spoken**, or one you flagged to the owner (then it is end-card only
  and POST.md says the ManyChat trigger needs setting up). No `[LINK]` or `[...]` placeholder may ship.
- Real logos and screenshots are supplied per reel (a path in the beat sheet) and never committed to the repo.

## Machine load (the Mac went black on 28 Sep: six agents, 8-process frame farms each, load ~200)

- **One render queue for the whole machine**: `house/common.render_slot` holds a file lock in `~/.cache/house-edit/queue`.
  Max 1 concurrent render; a second slot opens only when load is under 4. A render waits while load is above 12.
- Everything runs under `nice -n 10`; ffmpeg gets `-threads 2`; numpy/OpenCV threads are pinned to 1.
- **Hardware encode** (`h264_videotoolbox`), hardware decode for proxies. Frames stream straight from the decoder
  through Python into the encoder: no per-frame PNGs, no multi-process frame farms, ever.
- Look-dev with `--stills` (single frames, cheap) and `--limit 10`; do the full render once, when the stills are right.
- Person matting (rembg) is the heaviest step: only for `behind_head` frames, and only when rembg is installed.

## QA gates (all must PASS; SKIPPED is not a pass)

`JOB/qa/qa.json`, run automatically after the render (or `--stage qa`):

1. **Contact sheet** `qa/contact.jpg`: every 0.25 s for the first 5 s, then every 1 s, with the IG top line (blue) and
   the 4:5 crop lines (pink). **You must open it and look at every frame** before saying done: layout, seam, caption
   position, face clear of graphics, nothing cut by the safe zones, nothing floating.
2. **Black frames**: no frame with mean luma under 20.
3. **Caption sync**: caption chunk starts vs an independent **large-v3-turbo single pass of the rendered file**
   (set `HOUSE_XCHECK_PYTHON` to a python with `mlx_whisper`): p95 <= 0.25 s, **0 flicker** (no chunk on screen
   under 0.2 s), >= 98% of words inside a caption. Captions are timed with small.en per line + energy snap, so turbo
   shares neither model nor method. If turbo is not installed, the gate falls back to a small.en per-line
   re-whisper of the rendered file and qa.json says `FALLBACK`; it never passes without a reference.
   Reported only: a small.en single pass (it drifts 0.12-0.19 s, up to ~0.5 s, inside dense ~40 s reels: measured
   29 Sep on the Deepline test, where turbo sat within 0.1 s of the captions on 11 of the 12 chunks small.en
   flagged) and post-pause energy onsets (a tightened split reel rarely has 3 to judge).
4. **Loudness**: -14 +/- 1 LUFS integrated, true peak <= -1.4 dBTP (target -1.5; 0.1 allowed for the AAC encode).
5. **OCR for private data** (macOS Vision, 2 fps): no emails, phone numbers, home-folder paths, key-like strings, or
   denylist terms. All text read is in `qa/ocr.txt`: skim it.
6. **No pills**: a detector for rounded-end shapes 28-150 px tall with text inside, outside the caption box. Any hit
   fails; crops are saved in `qa/pill_hits/` so you can see what it found. (It catches every pill in the 28 Sep renders:
   see `tests/test_rules.py`.)

Also check by eye: the finger matches the reveal when he points, the keyword on the end card matches what he said,
and every number on screen is one he said.

## Pitfalls learned on 28 Sep

- whisper word starts run early (they absorb the silence before them): starts are snapped to the end of measured
  silence. Anchors tolerate whisper gluing hyphenated words ("go-to-market", "end-to-end").
- A whisper hallucination on trailing silence ("Back in time") is not a word; the tail is gated by energy.
- Face crops are derived per clip, never reused (a reused crop cut a chin off).
- DJI selfie footage may be mirrored: check before placing anything he points at.
- Nothing hardcoded inside a panel: two old reels shipped a previous video's content. Panels only take beat-sheet data.
- The pill ban landed after the renders on 28 Sep, and agent QA passed six reels with pills. That is why the ban is now
  code (no drawing path + validator + detector), not judgement.
