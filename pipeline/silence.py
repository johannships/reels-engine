#!/usr/bin/env python3
"""Trim dead air out of a HeyGen take without touching the speech.

Why this exists
---------------
The pipeline currently shortens a video with `atempo`/`setpts` (video.speed).
That time-compresses the *speech itself*, which is audible: pauses shrink along
with the words and the delivery starts to sound clipped and synthetic.

Cutting silence does the same job with no effect on the words. Render the voice
at the pace you want with HeyGen's `voice.speed`, then remove the gaps here.

The one thing to get right is the threshold. At -38dB a low-energy consonant,
word tail or breath reads as "silence" and gets excised — that is what makes a
clone sound choppy. On a measured take, 25% of frames sat below -41dB. Use -50dB
so only genuine silence qualifies.

    python3 silence.py in.mp4 out.mp4 [threshold_db]

Video and audio are cut together with the concat filter, so lipsync is preserved
exactly. The avatar is essentially motionless during a pause (measured
frame-to-frame delta 0.02/255), so the cuts are invisible.
"""
import os, subprocess, sys

import numpy as np

MIN_PAUSE = float(os.environ.get("MIN_PAUSE", 0.22))  # only touch gaps this long
KEEP      = float(os.environ.get("KEEP", 0.13))       # what a trimmed gap becomes
MIN_GAIN  = 0.06                                      # skip cuts smaller than this
HEAD, TAIL = 0.03, 0.12


def trim(src, out, thresh_db=-50.0):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
        capture_output=True).stdout
    a = np.frombuffer(raw, dtype=np.int16).astype(float) / 32768
    hop = 320                                  # 20 ms
    n = len(a) // hop
    db = np.array([20 * np.log10(np.sqrt((a[i*hop:(i+1)*hop] ** 2).mean()) + 1e-12)
                   for i in range(n)])
    quiet = db < thresh_db

    runs, s = [], None
    for i, v in enumerate(quiet):
        if v and s is None:
            s = i
        if not v and s is not None:
            runs.append((s * 0.02, i * 0.02)); s = None
    if s is not None:
        runs.append((s * 0.02, n * 0.02))

    total = n * 0.02
    cuts = []
    for a_, b_ in runs:
        d = b_ - a_
        if a_ <= 0.02:
            if d > HEAD:
                cuts.append((0.0, b_ - HEAD))
        elif b_ >= total - 0.02:
            if d > TAIL:
                cuts.append((a_ + TAIL, total))
        elif d >= MIN_PAUSE and d - KEEP >= MIN_GAIN:
            excess = d - KEEP
            mid = (a_ + b_) / 2
            cuts.append((mid - excess / 2, mid + excess / 2))

    keeps, prev = [], 0.0
    for c0, c1 in cuts:
        if c0 > prev + 0.02:
            keeps.append((prev, c0))
        prev = c1
    if prev < total - 0.02:
        keeps.append((prev, total))
    if not cuts:
        print(f"silence: nothing to trim in {src}")
        return src

    removed = sum(c1 - c0 for c0, c1 in cuts)
    print(f"silence: {total:.2f}s @ {thresh_db}dB — trimmed {len(cuts)} gaps "
          f"(-{removed:.2f}s) -> {total - removed:.2f}s")

    parts, labels = [], []
    for i, (k0, k1) in enumerate(keeps):
        parts.append(f"[0:v]trim=start={k0:.3f}:end={k1:.3f},setpts=PTS-STARTPTS[v{i}]")
        parts.append(f"[0:a]atrim=start={k0:.3f}:end={k1:.3f},asetpts=PTS-STARTPTS[a{i}]")
        labels.append(f"[v{i}][a{i}]")
    fc = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(keeps)}:v=1:a=1[v][a]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fc,
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "17", "-pix_fmt", "yuv420p", "-r", "30",
                    "-c:a", "aac", "-b:a", "192k", out], check=True)
    return out


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    trim(sys.argv[1], sys.argv[2],
         float(sys.argv[3]) if len(sys.argv) > 3 else -50.0)
