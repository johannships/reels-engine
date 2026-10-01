"""Stage 1: proxies -> per-clip transcript -> pick takes -> tighten pauses -> tight.mov + voice.

Measured thresholds (28 Sep 2026 reels):
  speech gate THR -50 dBFS for the first/last word (never -38: it clips soft consonants)
  pause gate PTHR -42 dBFS for internal pauses
  split format:   pauses >= 0.16 s shrink to 0.10 s  (the reference style never pauses > ~0.2 s)
  premium format: pauses >= 0.25 s shrink to 0.20 s  (a talking head needs a breath)
  head 0.06 s before the first word, tail 0.08 s after the last. 8 ms fades at every join.
  All cuts are frame-aligned at 30 fps so picture and voice stay locked. The voice is never time-stretched.
"""
import os
import re

import numpy as np

from . import transcribe
from .common import FPS, SR, ff, read_json, read_wav, write_json, log, video_encoder_args

PROXY_W, PROXY_H = 1296, 2304

TIGHTEN = {
    "split": dict(THR=-50.0, PTHR=-42.0, MIN_PAUSE=0.16, KEEP=0.10, HEAD=0.06, TAIL=0.08),
    "premium": dict(THR=-50.0, PTHR=-42.0, MIN_PAUSE=0.25, KEEP=0.20, HEAD=0.06, TAIL=0.10),
}


def proxy(src, dst):
    """30 fps 1296x2304 proxy with hardware decode + encode (cached)."""
    if os.path.exists(dst):
        return dst
    tmp = dst + ".tmp.mov"
    ff("-hwaccel", "videotoolbox", "-i", src, "-map", "0:v:0", "-map", "0:a:0",
       "-vf", f"fps={FPS},scale={PROXY_W}:{PROXY_H}:force_original_aspect_ratio=increase:flags=bicubic,crop={PROXY_W}:{PROXY_H}",
       *video_encoder_args("20M", "28M"), "-c:a", "pcm_s16le", "-ar", str(SR), "-ac", "1", tmp)
    os.replace(tmp, dst)
    return dst


def db_env(x, sr, hop_s=0.005, win_s=0.02):
    h = int(sr * win_s); hop = int(sr * hop_s)
    n = max(0, (len(x) - h) // hop)
    idx = np.arange(n)[:, None] * hop + np.arange(h)[None, :]
    return 20 * np.log10(np.sqrt((x[idx] ** 2).mean(1)) + 1e-9)


def retake_drops(words, gap=0.6):
    """'retake' said as its own word: drop from the start of the flubbed sentence to the end of the marker.
    Sentence start = the word after the last . ? ! or after a pause > gap s, before the marker."""
    drops = []
    for i, w in enumerate(words):
        if re.sub(r"[^a-z]", "", w["w"].lower()) != "retake":
            continue
        j = i - 1
        while j >= 0:
            if words[j]["w"].endswith((".", "?", "!")) or (j + 1 < len(words) and words[j + 1]["t0"] - words[j]["t1"] > gap and j + 1 < i):
                break
            j -= 1
        start = words[j + 1]["t0"] - 0.05 if j + 1 < i else w["t0"] - 0.05
        drops.append([max(0.0, start), w["t1"] + 0.05])
    return drops


def clip_edl(x, sr, p, drops=()):
    """Speech segments of one clip with long pauses shrunk. drops: [[t0, t1]] removed first."""
    db = db_env(x, sr)
    HOP = 0.005
    for a, b in drops:
        db[int(a / HOP): int(b / HOP) + 1] = -120
    sp = db > p["PTHR"]
    n = len(db)
    # onset: 60 ms sustained above PTHR (ignores clicks); offset: last frame above PTHR
    on_i = next((j for j in range(n - 12) if sp[j:j + 12].mean() > 0.7), 0)
    off_i = max((j for j in range(n) if sp[j]), default=n - 1)
    # extend onset back to where the -50 dB gate opens (soft first consonant)
    while on_i > 0 and db[on_i - 1] > p["THR"]:
        on_i -= 1
    runs, s = [], None
    for j in range(on_i, off_i + 1):
        if not sp[j] and s is None:
            s = j
        if sp[j] and s is not None:
            runs.append((s * HOP + 0.02, j * HOP)); s = None
    cur = max(0.0, on_i * HOP - p["HEAD"]); segs = []
    for a, b in runs:
        if b - a >= p["MIN_PAUSE"]:
            segs.append((cur, a + p["KEEP"] / 2)); cur = b - p["KEEP"] / 2
    segs.append((cur, min(len(x) / sr, off_i * HOP + 0.02 + p["TAIL"])))
    out = []
    for a, b in segs:
        a = np.floor(a * FPS) / FPS; b = a + round((b - a) * FPS) / FPS
        if b - a >= 2 / FPS:
            out.append((round(float(a), 4), round(float(b), 4)))
    return out


def run(job, clips, fmt, manual_drops=None):
    """Writes <job>/prep/{proxy_N.mov, clipN.wav, clipN_words.json}, tight.mov, voice_raw.wav, timeline.json."""
    pd = os.path.join(job, "prep"); os.makedirs(pd, exist_ok=True)
    p = TIGHTEN[fmt]
    segs, report = [], []
    for ci, src in enumerate(clips, 1):
        px = proxy(src, os.path.join(pd, f"proxy_{ci}.mov"))
        wav = os.path.join(pd, f"clip{ci}.wav")
        if not os.path.exists(wav):
            ff("-i", px, "-vn", "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", wav)
        wj = os.path.join(pd, f"clip{ci}_words.json")
        if not os.path.exists(wj):
            w16 = transcribe.to16k(wav, os.path.join(pd, f"clip{ci}_16k.wav"))
            write_json(wj, transcribe.words(w16))
        words = read_json(wj)
        drops = retake_drops(words) + [d[1:] for d in (manual_drops or []) if d[0] == ci]
        x, sr = read_wav(wav)
        e = clip_edl(x, sr, p, drops)
        report.append({"clip": ci, "src": os.path.basename(src), "dur": round(len(x) / sr, 2),
                       "kept": round(sum(b - a for a, b in e), 2), "segments": len(e), "retake_drops": drops,
                       "text": " ".join(w["w"] for w in words)})
        for a, b in e:
            segs.append({"clip": ci, "in": a, "out": b})
        log(job, f"clip {ci}: kept {report[-1]['kept']}s of {report[-1]['dur']}s in {len(e)} segments, drops {drops}")
    # timeline
    cum = 0
    for s in segs:
        nf = int(round((s["out"] - s["in"]) * FPS))
        s.update(f0=cum, nf=nf, t0=round(cum / FPS, 4)); cum += nf
    tl = {"format": fmt, "clips": [os.path.abspath(c) for c in clips], "segments": segs, "frames": cum,
          "dur": round(cum / FPS, 4), "tighten": p, "report": report}
    # picture + voice cut together, frame-exact
    tight = os.path.join(job, "tight.mov")
    tlp = os.path.join(job, "timeline.json")
    if not os.path.exists(tight) or not os.path.exists(tlp) or read_json(tlp).get("segments") != segs:
        ins, fc, cat = [], [], ""
        for ci in range(1, len(clips) + 1):
            ins += ["-i", os.path.join(pd, f"proxy_{ci}.mov")]
        for k, s in enumerate(segs):
            n = s["clip"] - 1; d = s["nf"] / FPS
            fc.append(f"[{n}:v]trim=start_frame={int(round(s['in'] * FPS))}:end_frame={int(round(s['in'] * FPS)) + s['nf']},setpts=PTS-STARTPTS[v{k}]")
            fc.append(f"[{n}:a]atrim=start={s['in']}:duration={d:.4f},asetpts=PTS-STARTPTS,"
                      f"afade=t=in:d=0.008,afade=t=out:st={max(0, d - 0.008):.4f}:d=0.008[a{k}]")
            cat += f"[v{k}][a{k}]"
        fc.append(f"{cat}concat=n={len(segs)}:v=1:a=1[v][a]")
        tmp = tight + ".tmp.mov"
        ff(*ins, "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]", *video_encoder_args("16M", "24M"),
           "-c:a", "pcm_s16le", "-ar", str(SR), "-ac", "1", tmp)
        os.replace(tmp, tight)
        ff("-i", tight, "-vn", "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", os.path.join(job, "voice_raw.wav"))
    write_json(os.path.join(job, "timeline.json"), tl)
    log(job, f"tight: {tl['dur']}s, {len(segs)} segments")
    return tl
