# Voice: making a clone stop sounding like a clone

Three findings from tuning a HeyGen clone against a reference reel. All of them are
measurements, not preferences.

## 1. Don't `atempo` the voice — cut the silence instead

`video.speed` applies `atempo` + `setpts` to the finished video. That compresses the
*speech*: pauses shrink along with the words and the delivery starts to sound clipped.

Do it in two steps instead:

1. Render the voice at the pace you want with HeyGen's `voice.speed` (0.5–1.5).
2. Remove the gaps with `pipeline/silence.py`.

Silence removal has no effect on how the words themselves sound, so you can be
aggressive with it and stay natural.

## 2. The threshold is the whole ballgame

A pause detector at **−38 dB** classifies low-energy consonants, word tails and breath
as silence and cuts them out. That is what makes a clone sound choppy and synthetic —
it is removing speech, not gaps. On a measured take, 25% of frames sat below −41 dB,
and the detector found 35 "gaps" at −38 dB versus 22 real ones at −52 dB.

Use **−50 dB**, only touch gaps ≥0.22s, and leave ~0.13s of each one.

The cuts are invisible: the avatar is essentially motionless during a pause
(frame-to-frame delta 0.02/255), so video and audio can be cut together.

## 3. Pace, and what "natural" actually means

The reference reel runs at **3.90 words/sec** with exactly **one 0.10s pause in 39.5s** —
it is hard-edited so every breath is gone. A raw HeyGen take has ~26 pauses.

Rendering at `voice.speed: 1.45` plus silence removal lands at 4.01 w/s and reads as
natural. Rendering slower (1.2) and trimming gently reads as *slow*, which is the thing
viewers actually clock as AI.

Two smaller levers:

- **Punctuation is a bigger lever than trimming.** Fewer commas in the script means
  fewer pauses generated in the first place.
- **Write numbers as digits.** Whisper emits "700,000" as three tokens, so a script
  saying "seven hundred thousand" fails to align and captions drop words. Digits also
  read faster on screen.

## Note on voice tuning

`video.voice.elevenlabs_settings` only applies to voices on the ElevenLabs or Fish
engines. HeyGen-cloned voices reject it with HTTP 400 — `heygen.py` already retries
without it, so renders still succeed, but be aware the tuning is silently dropped and
`voice.speed` is doing all the work. Cloned voices also report
`emotion_support: false`, so the `emotion` parameter is unavailable for them.

## QA

`qa.py` gained `caption_sync`. The existing `captions` check compares word *counts*,
which passes even when every caption is half a second late. `caption_sync` correlates
word onsets against the finished audio's rising-energy envelope and fails if the lag
exceeds 0.25s. On an aligned build it measures 0.02s.
