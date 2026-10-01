"""Captions on EVERY word, from the first frame, timed from a whisper pass over the FINAL audio.
Text comes from whisper corrected by the beat sheet's caption_fixes; timing only from whisper.

Two systems, never mixed:
  split   -> mono ALL CAPS, 2-3 words, one line, charcoal box on the seam, hard swap (no pop, no colour)
  premium -> Inter 900 word-by-word pop (0.12 s ease-out-back), up to 3 words / 16 chars, one accent
             word per phrase (red, or serif italic) from the beat sheet
"""
import re

FUNCTION_WORDS = {"A", "AN", "THE", "TO", "SO", "AND", "FROM", "THAT", "OF", "FOR", "IN", "ON", "WITH", "OR", "BUT", "IS"}


def apply_fixes(words, fixes):
    """fixes: {"Claud": "Claude", "a email": "an email", "go-to-market": "go to market"}. Multi-word keys
    match consecutive words (punctuation ignored). Returns a new list; timings are kept."""
    norm = lambda s: re.sub(r"[^a-z0-9']", "", s.lower())
    out = [dict(w) for w in words]
    for k, v in (fixes or {}).items():
        ks = k.split()
        i = 0
        while i <= len(out) - len(ks):
            if all(norm(out[i + j]["w"]) == norm(ks[j]) for j in range(len(ks))):
                tail = re.sub(r"^.*?([.,?!:;\"]*)$", r"\1", out[i + len(ks) - 1]["w"])
                vs = v.split()
                if len(vs) == len(ks):
                    for j in range(len(ks)):
                        out[i + j]["w"] = vs[j] + (tail if j == len(ks) - 1 else "")
                else:  # different word count: spread the span evenly
                    t0, t1 = out[i]["t0"], out[i + len(ks) - 1]["t1"]
                    step = (t1 - t0) / len(vs)
                    new = [{"w": vs[j] + (tail if j == len(vs) - 1 else ""), "t0": round(t0 + j * step, 3),
                            "t1": round(t0 + (j + 1) * step, 3)} for j in range(len(vs))]
                    out[i:i + len(ks)] = new
                i += len(vs)
            else:
                i += 1
    return out


def _clean_split(w):
    core = w.strip('",.?!:;').upper()
    return core.replace("-", " ").replace("—", " ").replace("–", " ")


def split_chunks(words, dur, max_words=3, max_chars=18, gap=0.25):
    """2-3 word mono chunks, continuous (each holds until the next starts), never mid-name."""
    toks = [[w["t0"], w["t1"], _clean_split(w["w"]), w["w"].rstrip('"').endswith((",", ".", "?", "!"))] for w in words]
    toks = [t for t in toks if t[2].strip()]
    groups, cur = [], []
    for k, tk in enumerate(toks):
        cur.append(tk)
        nw = sum(len(x[2].split()) for x in cur)
        nxt = toks[k + 1] if k + 1 < len(toks) else None
        g = (nxt[0] - tk[1]) if nxt else 9
        if nw >= max_words or tk[3] or g > gap or (nw >= 2 and nxt and len(" ".join(x[2] for x in cur + [nxt])) > max_chars):
            groups.append(cur); cur = []
    if cur:
        groups.append(cur)
    # never strand a function word at the end of a chunk
    for k in range(len(groups) - 1):
        g, h = groups[k], groups[k + 1]
        while len(g) > 1 and g[-1][2] in FUNCTION_WORDS and not g[-1][3] and len(" ".join(x[2] for x in [g[-1]] + h)) <= max_chars + 2:
            h.insert(0, g.pop())
    # a chunk that would be on screen < 0.25 s cannot be read: re-split it with the next chunk so both last
    # >= 0.25 s and fit one line; if no split works, merge them when the result still fits
    groups = [g for g in groups if g]
    txt = lambda g: " ".join(x[2] for x in g)
    k = 0
    while k < len(groups) - 1:
        g, h = groups[k], groups[k + 1]
        if h[0][0] - g[0][0] >= 0.25:
            k += 1; continue
        pool = g + h
        end = groups[k + 2][0][0] if k + 2 < len(groups) else pool[-1][1] + 0.5
        best = None
        for i in range(1, len(pool)):
            a, b = pool[:i], pool[i:]
            d = min(b[0][0] - a[0][0], end - b[0][0])
            if len(txt(a)) <= max_chars + 4 and len(txt(b)) <= max_chars + 4 and d >= 0.25 and (best is None or d > best[0]):
                best = (d, i)
        if best:
            groups[k:k + 2] = [pool[:best[1]], pool[best[1]:]]
        elif len(txt(pool)) <= max_chars + 6:
            groups[k:k + 2] = [pool]
        k += 1
    cues = [{"t0": g[0][0], "t1": g[-1][1], "text": " ".join(x[2] for x in g), "n": len(g)} for g in groups if g]
    for i in range(len(cues) - 1):
        cues[i]["t1"] = cues[i + 1]["t0"]
    if cues:
        cues[0]["t0"] = 0.0          # caption on frame 1
        cues[-1]["t1"] = min(dur, cues[-1]["t1"] + 0.5)
    return cues


def premium_groups(words, dur, max_words=3, max_chars=16, gap=0.7, lead=0.03):
    """Word-pop groups: [{'t0','t1','words':[{'w','t0','t1'}]}]."""
    disp = lambda w: w.strip('",').rstrip(".")
    groups, cur = [], []
    for i, w in enumerate(words):
        if cur:
            prev = cur[-1]
            ln = sum(len(disp(x["w"])) for x in cur) + len(disp(w["w"]))
            if len(cur) >= max_words or prev["w"][-1] in ".,?!" or ln > max_chars or w["t0"] - prev["t0"] > gap:
                groups.append(cur); cur = []
        cur.append({"w": disp(w["w"]), "t0": w["t0"], "t1": w["t1"]})
    if cur:
        groups.append(cur)
    out = []
    for k, g in enumerate(groups):
        a = 0.0 if k == 0 else max(0.0, g[0]["t0"] - lead)
        b = groups[k + 1][0]["t0"] - lead if k + 1 < len(groups) else min(dur, g[-1]["t1"] + 0.6)
        out.append({"t0": a, "t1": b, "words": g})
    return out


# ------------------------------------------------------------------ per-line re-timing (the 28 Sep method)
def lines_from_words(words, max_len=6.0):
    """Line spans from the first transcript: split at sentence ends, and split a line longer than max_len at its
    widest word gap. Each boundary sits halfway between one word's end and the next word's start."""
    groups, cur = [], []
    for w in words:
        cur.append(w)
        if w["w"].rstrip('"').endswith((".", "?", "!")):
            groups.append(cur); cur = []
    if cur:
        groups.append(cur)
    out = []
    stack = groups[:]
    while stack:
        g = stack.pop(0)
        if g[-1]["t0"] - g[0]["t0"] > max_len and len(g) > 5:
            # split near the middle, preferring a comma, never leaving a piece under 1.5 s
            mid = (g[0]["t0"] + g[-1]["t0"]) / 2
            ks = [i for i in range(2, len(g) - 2) if g[i]["t0"] - g[0]["t0"] >= 1.5 and g[-1]["t0"] - g[i]["t0"] >= 1.5]
            if ks:
                k = min(ks, key=lambda i: abs(g[i]["t0"] - mid) - (0.8 if g[i - 1]["w"].endswith(",") else 0))
                stack = [g[:k], g[k:]] + stack
                continue
        out.append(g)
    return out


def energy_onsets(x, sr, rise_db=9.0, floor_db=-30.0, min_gap=0.08):
    """Syllable-level onsets: a rise of >= rise_db within 40 ms ending above floor_db (5 ms RMS frames)."""
    import numpy as np
    h = int(sr * 0.005); n = len(x) // h
    db = 20 * np.log10(np.sqrt((x[: n * h].reshape(n, h) ** 2).mean(1)) + 1e-9)
    on = []
    for i in range(8, n):
        if db[i] > floor_db and db[i] - db[i - 8:i].min() >= rise_db and (not on or i * 0.005 - on[-1] > min_gap):
            on.append(i * 0.005)
    return np.array(on)


def retime_per_line(wav16, first_words, pad=0.15, snap=0.15, log=print):
    """Re-whisper the FINAL audio one line at a time (whisper does not drift inside a 2-6 s line), keep the first
    transcript's words and order, take each word's start from its line pass, then snap it to the nearest energy
    onset within +/- snap s. A line whose pass does not line up word-for-word keeps the text-matched stamps it can
    and its first-pass times for the rest (logged)."""
    import os
    import re
    import tempfile
    import numpy as np
    from . import transcribe
    from .common import ff, read_wav
    x, sr = read_wav(wav16)
    dur = len(x) / sr
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
    lines = lines_from_words(first_words)
    bounds = []
    for k, g in enumerate(lines):
        a = 0.0 if k == 0 else (lines[k - 1][-1]["t1"] + g[0]["t0"]) / 2
        b = dur if k == len(lines) - 1 else (g[-1]["t1"] + lines[k + 1][0]["t0"]) / 2
        bounds.append((max(0.0, min(a, g[0]["t0"] - 0.02)), b))
    on = energy_onsets(x, sr)
    out = []
    with tempfile.TemporaryDirectory() as td:
        for k, (g, (a, b)) in enumerate(zip(lines, bounds)):
            pa, pb = max(0.0, a - pad), min(dur, b + pad)
            p = os.path.join(td, f"l{k}.wav")
            ff("-ss", f"{pa:.3f}", "-t", f"{pb - pa:.3f}", "-i", wav16, "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", p)
            lw = [dict(w, t0=round(w["t0"] + pa, 3), t1=round(w["t1"] + pa, 3)) for w in transcribe.words(p)]
            lw = [w for w in lw if a - 0.1 <= w["t0"] < b + 0.05]
            if [norm(w["w"]) for w in lw] == [norm(w["w"]) for w in g]:
                times = [w["t0"] for w in lw]
            else:
                times = []
                for w in g:
                    c = [q["t0"] for q in lw if norm(q["w"])[:4] == norm(w["w"])[:4] and abs(q["t0"] - w["t0"]) < 0.8]
                    times.append(min(c, key=lambda t: abs(t - w["t0"])) if c else w["t0"])
                log(f"line {k + 1}: per-line words differ from the first transcript; text-matched where possible")
            for w, t in zip(g, times):
                out.append(dict(w, t0=float(t)))
    for w in out:
        if len(on):
            o = on[np.argmin(np.abs(on - w["t0"]))]
            if abs(o - w["t0"]) <= snap:
                w["t0"] = round(float(o), 3)
    for p_, q in zip(out, out[1:]):       # order is the transcript's; never let a start pass the next one
        if q["t0"] <= p_["t0"]:
            q["t0"] = round(p_["t0"] + 0.05, 3)
    return out
