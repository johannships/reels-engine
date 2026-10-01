"""Synthesised SFX kit. numpy only. Nothing is sampled from any recording, so Content ID has
nothing to match. Fixed seed: the same code always gives the same sounds.

    python3 -m house.sfx <outdir>     # write the kit as 48 kHz wavs to listen to

Kit (default level = dB under the voice's speech RMS):
  hook_subboom  808-style sub drop 112->42 Hz, 900 Hz tail, 4-7 kHz glitter, dead stop   (10 dB under; once per reel)
  pop_cut       round 520->300 Hz bloop, ~80 ms: the cut to a full graphic                (18)
  pop_soft      smaller, higher bloop: an element pulled out / a card swap                (18)
  tick_hi       2 kHz blip: first element on screen, a button state change                (18)
  tick_lo       1 kHz blip: a grid or URL landing                                         (18)
  stamp         thud + slap for a stamp, at most once                                     (20)
  typing        7 soft key clicks over 0.69 s: a keyword typing in                        (20)
  tuck          quiet airy swell into a beat (stands in for a music drop-out)             (22)
  sub           short sub hit for a premium hook or big-type reveal                       (12)
  whoosh        band-passed noise swell: a panel sliding in (premium only, never on hard cuts)  (20)
  ching         bright double strike: a money / number payoff (premium, max once)         (18)
  click         UI click: a checkbox ticking                                              (20)
"""
import os
import sys

import numpy as np

SR = 48000


def _t(L):
    return np.arange(int(L * SR)) / SR


def _bandpass(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    w = np.ones_like(f)
    if lo:
        w *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1)) ** 4)
    if hi:
        w *= 1 / np.sqrt(1 + (f / hi) ** 4)
    return np.fft.irfft(X * w, len(x))


def _env(L, a, d):
    t = _t(L); return np.minimum(t / a, 1) * np.exp(-t / d)


def _fade(x, ms=6):
    n = int(SR * ms / 1000); x = x.copy(); x[-n:] *= np.linspace(1, 0, n); return x


def hook_subboom(L=0.75, rng=None):
    rng = rng or np.random.default_rng(7)
    t = _t(L)
    f = 42 + 70 * np.exp(-t / 0.06)
    body = np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f) / SR)) * _env(L, 0.003, 0.45)
    tone = 0.18 * np.sin(2 * np.pi * 900 * t) * _env(L, 0.02, 0.35)
    glit = sum(a * np.sin(2 * np.pi * fr * t + rng.uniform(0, 6)) for fr, a in [(4200, .05), (5600, .04), (7300, .03)])
    glit = glit * _env(L, 0.25, 0.3) * (t > 0.3)
    click = _bandpass(rng.standard_normal(len(t)), 1500, 9000) * _env(L, 0.0005, 0.012) * 0.35
    x = body + tone + glit + click
    k = t > L - 0.02
    x[k] *= np.linspace(1, 0, k.sum())
    return x


def pop(L=0.12, f0=520, f1=300, rng=None):
    rng = rng or np.random.default_rng(7)
    t = _t(L); f = f1 + (f0 - f1) * np.exp(-t / 0.025)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(L, 0.002, 0.035)
    return x + 0.15 * _bandpass(rng.standard_normal(len(t)), 800, 4000) * _env(L, 0.0005, 0.006)


def tick(freq=2000, L=0.06):
    t = _t(L)
    return np.sin(2 * np.pi * freq * t) * _env(L, 0.001, 0.012) + 0.2 * np.sin(4 * np.pi * freq * t) * _env(L, 0.001, 0.006)


def stamp(L=0.22, rng=None):
    rng = rng or np.random.default_rng(7)
    t = _t(L); f = 90 + 80 * np.exp(-t / 0.02)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(L, 0.001, 0.05)
    return x + 0.5 * _bandpass(rng.standard_normal(len(t)), 600, 5000) * _env(L, 0.0005, 0.02)


def typing(n=7, gap=0.085, rng=None):
    rng = rng or np.random.default_rng(7)
    L = n * gap + 0.1; x = np.zeros(int(L * SR))
    for i in range(n):
        k = _bandpass(rng.standard_normal(int(0.03 * SR)), 1800, 7000) * _env(0.03, 0.0003, 0.004)
        k += 0.4 * np.sin(2 * np.pi * rng.uniform(180, 260) * _t(0.03)) * _env(0.03, 0.0005, 0.008)
        s = int((i * gap + rng.uniform(-0.015, 0.015) + 0.01) * SR); x[s:s + len(k)] += k * rng.uniform(0.6, 1)
    return x


def tuck(L=0.28, rng=None):
    rng = rng or np.random.default_rng(7)
    t = _t(L)
    return _bandpass(rng.standard_normal(len(t)), 1200, 6000) * (t / L) ** 2.5 * 0.8


def sub(L=0.9, rng=None):
    rng = rng or np.random.default_rng(3)
    t = _t(L); f = 38 + 30 * np.exp(-t / 0.08)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(L, 0.004, 0.28)
    return x + 0.3 * _bandpass(rng.standard_normal(len(t)), 0, 900) * _env(L, 0.001, 0.02)


def whoosh(L=0.42, lo=300, hi=3500, rng=None):
    rng = rng or np.random.default_rng(3)
    t = _t(L)
    return _bandpass(rng.standard_normal(len(t)), lo, hi) * np.sin(np.pi * t / L) ** 2 * 0.6


def ching(rng=None):
    rng = rng or np.random.default_rng(3)
    L = 1.2; t = _t(L); x = np.zeros(len(t))
    for f, a, d in [(2093, 1, .35), (3136, .6, .25), (4186, .45, .2), (5274, .3, .12), (6272, .2, .09)]:
        x += a * np.sin(2 * np.pi * f * t) * np.exp(-t / d)
    x *= np.minimum(t / 0.002, 1)
    x2 = np.zeros(len(t)); o = int(0.07 * SR); x2[o:] = x[:len(t) - o] * 0.8
    tr = _bandpass(rng.standard_normal(len(t)), 6000, 0) * _env(L, 0.001, 0.015) * 0.6
    return (x * 0.5 + x2 + tr) / 2.5


def click(rng=None):
    rng = rng or np.random.default_rng(3)
    L = 0.05; t = _t(L)
    x = _bandpass(rng.standard_normal(len(t)), 1500, 7000) * np.exp(-t / 0.006)
    return x + 0.5 * np.sin(2 * np.pi * 2400 * t) * np.exp(-t / 0.01)


KIT = {
    "hook_subboom": (hook_subboom, 10), "pop_cut": (pop, 18), "pop_soft": (lambda: pop(0.09, 700, 420), 18),
    "tick_hi": (lambda: tick(2000), 18), "tick_lo": (lambda: tick(1000), 18), "stamp": (stamp, 20),
    "typing": (typing, 20), "tuck": (tuck, 22), "sub": (sub, 12), "whoosh": (whoosh, 20), "ching": (ching, 18),
    "click": (click, 20),
}

# cues per 10 s, measured on the reference edits: the split format is sparse on purpose
MAX_PER_10S = {"split": 3, "premium": 5}


def get(name):
    if name not in KIT:
        raise ValueError(f"unknown sfx '{name}'. Kit: {sorted(KIT)}")
    fn, default_under = KIT[name]
    return _fade(fn()), default_under


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out, exist_ok=True)
    from .common import write_wav
    for k in KIT:
        x, _ = get(k)
        write_wav(os.path.join(out, f"sfx_{k}.wav"), x / (np.abs(x).max() + 1e-9) * 0.5)
        print("wrote", k)
