"""Voice + synthesised SFX only (never a music bed), mastered to -14 LUFS integrated / -1.5 dBTP.

1. voice chain: rumble cut, de-mud, presence + air, gentle compression (crisp, no bed to hide in)
2. SFX from the beat sheet, each set N dB under the voice's speech RMS (the split format keeps them
   18-22 dB under; only the hook sub-boom is loud)
3. master: gain + true-peak limiter, iterated until integrated loudness is within 0.1 LU of -14
"""
import os

import numpy as np

from . import sfx as sfxkit
from .common import SR, ff, loudness, read_wav, write_wav, write_json, log

VOICE_CHAIN = ("highpass=f=80,equalizer=f=260:t=q:w=1.2:g=-2.5,equalizer=f=3800:t=q:w=1.0:g=2.5,"
               "equalizer=f=9000:t=q:w=0.8:g=1.5,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=2")
TARGET_I, TARGET_TP = -14.0, -1.5


def gain_to(src, dst, target=TARGET_I, limit_db=TARGET_TP, iters=6):
    """Loudness by linear gain + limiter (ffmpeg loudnorm's linear mode silently falls back to dynamic
    when the peak budget is short, so we iterate instead). Returns (I, TP)."""
    I, _ = loudness(src)
    g = target - I
    lim = 10 ** ((limit_db - 0.3) / 20)   # limiter ceiling a hair under the true-peak target (inter-sample overs)
    for _ in range(iters):
        ff("-i", src, "-af", f"volume={g:.2f}dB,alimiter=limit={lim:.4f}:attack=3:release=60:level=false",
           "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", dst)
        I2, TP2 = loudness(dst)
        if abs(I2 - target) < 0.1 and TP2 <= limit_db + 0.05:
            return I2, TP2
        g += target - I2
        if TP2 > limit_db + 0.05:
            lim *= 10 ** ((limit_db - TP2) / 20)
    return I2, TP2


def voice(job):
    raw = os.path.join(job, "voice_raw.wav"); chain = os.path.join(job, "voice_chain.wav")
    out = os.path.join(job, "voice.wav")
    ff("-i", raw, "-af", VOICE_CHAIN, "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", chain)
    I, TP = gain_to(chain, out)
    log(job, f"voice: {I:.1f} LUFS {TP:.1f} dBTP")
    return out


def speech_rms(x, sr):
    h = int(sr * 0.02); fr = x[: len(x) // h * h].reshape(-1, h)
    r = np.sqrt((fr ** 2).mean(1))
    return float(np.sqrt((r[r > 0.01] ** 2).mean())) if (r > 0.01).any() else 0.05


def mix(job, cues, fmt):
    """cues: [{'t': seconds, 'sfx': name, 'under_db': optional, 'why': str}] (already resolved)."""
    v, sr = read_wav(os.path.join(job, "voice.wav"))
    vr = speech_rms(v, sr)
    bus = np.zeros(len(v) + sr, np.float32); used = []
    for c in sorted(cues, key=lambda c: c["t"]):
        x, under = sfxkit.get(c["sfx"])
        under = c.get("under_db", under)
        act = x[np.abs(x) > np.abs(x).max() * 0.05]
        g = vr * 10 ** (-under / 20) / (np.sqrt((act ** 2).mean()) + 1e-9)
        i = max(0, int(round(c["t"] * sr))); L = min(len(x), len(bus) - i)
        bus[i:i + L] += x[:L] * g
        used.append({"t": round(c["t"], 3), "sfx": c["sfx"], "db_under_voice_rms": under, "why": c.get("why", "")})
    bus = bus[: len(v)]
    # density check (measured on the reference edits)
    ts = [u["t"] for u in used]
    worst = max((sum(1 for t in ts if a <= t < a + 10) for a in ts), default=0)
    if worst > sfxkit.MAX_PER_10S[fmt]:
        log(job, f"WARN sfx density {worst} per 10 s > {sfxkit.MAX_PER_10S[fmt]} for {fmt}")
    write_wav(os.path.join(job, "sfx_bus.wav"), bus, sr)
    write_json(os.path.join(job, "sfx_cues_used.json"), used)
    write_wav(os.path.join(job, "premix.wav"), (v + bus) * 0.7, sr)
    I, TP = gain_to(os.path.join(job, "premix.wav"), os.path.join(job, "master.wav"))
    log(job, f"master: {I:.1f} LUFS {TP:.1f} dBTP, {len(used)} sfx cues, no music bed")
    return I, TP
