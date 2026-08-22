# RepoDrop — the default style

RepoDrop is the composition the engine renders by default. It replaces the
split-screen RepoRadar look with full-bleed alternation: graphic scenes paint the
whole frame, talking-head scenes are left transparent so the avatar shows through,
and a picture-in-picture card puts the presenter under the graphic.

RepoRadar is still registered. Set `"style": "RepoRadar"` in an episode script to
render with it.

## Why these numbers

Every value below was measured off a reference reel rather than picked by eye.

### Shot grammar
12–15 shots, mean ~3s, nothing longer than ~4s on a talking head. Open on a PIP
(face and product together), close on a full-frame talking head for the CTA. Two
consecutive scenes never share a ground colour unless they're one animated block.

### Two caption systems — never mix them
| | graphic scenes | talking-head scenes |
|---|---|---|
| face | Didot / Bodoni, italic, ALL CAPS | Inter Tight / Arial Bold, sentence case |
| size | ~116px (cap-height 87–99px) | ~64px |
| position | y 0.46–0.62 of frame | baseline at 72% of frame height |
| grouping | 1–2 words per cue | 1–2 words per cue |

Long words are shrunk to fit `RD_CAP.maxWidth`. Without that, "OVERCOMPLICATING"
renders as "OVERCOMPLICAT." and runs off the frame.

### PIP card
```
x = 0    y = 1087    w = 1080    h = 833    corner radius 48 (top corners only)
```
The card is knocked out of the graphics layer with an SVG mask, so the avatar
composites *through* it. Render `pip` and `fullscreen` layouts as ProRes 4444.

### Palette
| role | value |
|---|---|
| dark ground | `#0F0F0F` |
| dark panel | `#121216` |
| white ground | `#FDFDFD` |
| danger (breach / failure beats) | `#E5484D` |
| success (payoff beats) | `#3DD68C` |
| accent | `#2BD9C4` |

## Scene mapping

RepoDrop consumes the **same episode JSON** as RepoRadar, so existing episodes
render in the new look with no edits:

| scene type | renders as |
|---|---|
| `intro` | terminal glyph with expanding rings + headline |
| `repo` | repo row, bar grows, star count counts up, "+N stars today" pill |
| `topic` | large stat counter with label and pill |
| `kinetic` | titled card |
| `isen` | titled card with ticking checklist items |
| `shot` | screenshot in browser chrome |
| `cta` | glyph + badge row |
| `avatar` | nothing — the footage shows through |

Captions come from `captions` (Whisper word timings) when present, and fall back to
timings derived evenly from the scene's `text` otherwise.

## Voice, if you are building the audio side

Two findings that matter more than anything in the studio:

1. **Never time-stretch the voice to fit the picture — re-time the picture.** Audio
   stretching is audible at ±10%; video stretching is invisible at ±25%.
2. **Only ever cut true silence.** A pause detector at −38 dB classifies low-energy
   consonants and word tails as silence and excises them, which is what makes a
   clone sound choppy and robotic. Use −50 dB, only touch gaps ≥0.22s, and leave
   ~0.13s of each one.

## Outstanding

`pip` layout renders correctly in the studio, and `prep.py` routes it through the
transparent ProRes path — but the ffmpeg composite step in `prep.py` still places
the avatar using the split-layout geometry (top 960 / bottom 960). To finish it,
composite the avatar into the card rect above instead. The existing QA gate
(`HEADROOM_MIN` / `CHIN_MARGIN` in `pipeline/qa.py`) already covers the failure this
guards against: a crop that cuts the chin off.
