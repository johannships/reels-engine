"""QA gates on the FINISHED file. Nothing ships until every gate is PASS and the agent has LOOKED
at the contact sheet. A SKIPPED gate is not a pass.

  contact   qa/contact.jpg: every 0.25 s for the first 5 s, then every 1 s (IG top line + 4:5 crop lines drawn)
  black     no frame with mean luma < 20
  sync      caption chunk starts vs a large-v3-turbo single pass of the RENDERED file (HOUSE_XCHECK_PYTHON):
            p95 <= 0.25 s; no chunk on screen < 0.2 s (flicker); >= 98% of words inside a caption.
            Without turbo: a small.en per-line re-whisper of the rendered file, labelled FALLBACK in qa.json.
            Reported only: small.en single pass (drifts 0.12-0.19 s on dense reels) and post-pause onsets.
  loudness  -14 +/- 1 LUFS integrated, true peak <= -1.4 dBTP (target -1.5; 0.1 for the AAC encode)
  ocr       macOS Vision OCR at 2 fps: no emails, phone numbers, local paths, key-like strings, or any term
            from the private denylist (client names etc., kept outside the repo)
  pill      no small floating pill / badge / tag / sticker: rounded-end shapes 28-150 px tall with text
            inside, outside the caption box. Hits are saved to qa/pill_hits/ to look at.
"""
import json
import os
import re
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageDraw

from . import transcribe
from .common import FPS, W, H, duration, loudness, read_json, write_json, log
from .config import CFG
from .face import swift_tool

_norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())


def _frames(path, times, w=W):
    """-> list of HxWx3 uint8 at the given times (one ffmpeg call, fps filter free)."""
    out = []
    with tempfile.TemporaryDirectory() as td:
        for i, t in enumerate(times):
            p = os.path.join(td, f"{i:04d}.png")
            subprocess.run(["nice", "-n", str(CFG["nice"]), "ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path,
                            "-frames:v", "1", "-vf", f"scale={w}:-2", p], check=True)
            out.append(np.asarray(Image.open(p).convert("RGB")))
    return out


def contact_sheet(path, dst, dur):
    ts = [round(x, 2) for x in np.arange(0, min(5, dur), 0.25)] + [float(x) for x in np.arange(5, dur, 1.0)]
    fr = _frames(path, ts, 216)
    cols = 10; rows = (len(fr) + cols - 1) // cols; th = fr[0].shape[0]
    sheet = Image.new("RGB", (cols * 216, rows * (th + 18)), "white"); d = ImageDraw.Draw(sheet)
    for i, (f, t) in enumerate(zip(fr, ts)):
        x, y = (i % cols) * 216, (i // cols) * (th + 18)
        sheet.paste(Image.fromarray(f), (x, y + 18)); d.text((x + 4, y + 3), f"{t:.2f}s", fill=(0, 0, 0))
        s = 216 / W
        for yy, c in ((220, (0, 160, 255)), (285, (255, 0, 160)), (1635, (255, 0, 160))):
            d.line([(x, y + 18 + yy * s), (x + 215, y + 18 + yy * s)], fill=c, width=1)
    sheet.save(dst, quality=88)
    return dst, ts


def black_frames(path):
    raw = subprocess.run(["nice", "-n", str(CFG["nice"]), "ffmpeg", "-v", "error", "-i", path, "-vf", "scale=54:96",
                          "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True).stdout
    g = np.frombuffer(raw, np.uint8).reshape(-1, 96 * 54)
    dark = np.where(g.mean(1) < 20)[0]
    return len(g), dark.tolist()


XCHECK = r"""
import json, sys, mlx_whisper
r = mlx_whisper.transcribe(sys.argv[1], path_or_hf_repo=sys.argv[2], word_timestamps=True)
print(json.dumps([{"w": w["word"].strip(), "t0": w["start"]} for s in r["segments"] for w in s.get("words", [])]))
"""


def _starts(captions, fmt):
    out = []
    for c in captions:
        first = c["text"].split()[0] if fmt == "split" else c["words"][0]["w"]
        t0 = c["t0"] if fmt == "split" else c["words"][0]["t0"]
        if t0 > 0.0:            # the frame-1 chunk is pinned to 0 on purpose
            out.append((t0, first))
    return out


def _stats(d):
    d = np.abs(np.array(d, dtype=float))
    if not len(d):
        return {"n": 0, "median": None, "p95": None}
    return {"n": int(len(d)), "median": round(float(np.median(d)), 3), "p95": round(float(np.percentile(d, 95)), 3),
            "over_0.25": int((d > 0.25).sum())}


def caption_sync(path, captions, fmt, qd):
    """Measured on the rendered file, by methods the captions were NOT timed with:
      energy  chunk starts vs measured post-pause speech onsets of the final audio (the gate; the eye judges these)
      xcheck  a different ASR model (mlx-whisper large-v3-turbo) if HOUSE_XCHECK_PYTHON points at a python with it
      single  whisper.cpp in one pass over the rendered file (reported)
    coverage: share of the single-pass words that fall inside a caption's span."""
    from .common import read_wav
    w16 = transcribe.to16k(path, os.path.join(qd, "final16k.wav"))
    x, sr = read_wav(w16)
    starts = _starts(captions, fmt)
    on = np.array(transcribe.pause_onsets(x, sr))
    ws = transcribe.words(w16)
    # each post-pause onset: which spoken word starts there (nearest single-pass word, text only), and is that word
    # the first word of a caption chunk? Only then is the onset a visible caption change we can judge.
    energy = []
    for o in on:
        if not ws:
            break
        wd = min(ws, key=lambda q: abs(q["t0"] - o))
        if abs(wd["t0"] - o) > 0.35:
            continue
        cand = [t for t, first in starts if _norm(first)[:4] == _norm(wd["w"])[:4] and abs(t - o) <= 0.4]
        if cand:
            energy.append(float(min(cand, key=lambda t: abs(t - o)) - o))
    write_json(os.path.join(qd, "final_words_single.json"), ws)

    def vs(ref):
        d = []
        for t, first in starts:
            key = _norm(first)[:4]
            c = [q["t0"] - t for q in ref if _norm(q["w"]).startswith(key) and abs(q["t0"] - t) < 1.0]
            if c:
                d.append(min(c, key=abs))
        return d
    res = {"energy": dict(_stats(energy), onsets=int(len(on))), "single_pass_whisper": _stats(vs(ws))}
    xpy = os.environ.get("HOUSE_XCHECK_PYTHON")
    if xpy and os.path.exists(os.path.expanduser(xpy)):
        r = subprocess.run(["nice", "-n", str(CFG["nice"]), os.path.expanduser(xpy), "-c", XCHECK, w16,
                            os.environ.get("HOUSE_XCHECK_MODEL", "mlx-community/whisper-large-v3-turbo")],
                           capture_output=True, text=True)
        try:
            xw = json.loads(r.stdout.strip().splitlines()[-1])
            write_json(os.path.join(qd, "final_words_xcheck.json"), xw)
            res["xcheck_model"] = _stats(vs(xw))
        except Exception:
            res["xcheck_model"] = {"error": r.stderr[-300:]}
    # flicker: a chunk on screen for less than 0.2 s cannot be read (collapsed whisper stamps did this on 29 Sep)
    short = [(round(c["t0"], 2), c["text"] if fmt == "split" else " ".join(w["w"] for w in c["words"]))
             for c in captions[:-1] if c["t1"] - c["t0"] < 0.2]
    res["flicker_chunks"] = short[:10]
    spans = [(c["t0"], c["t1"]) for c in captions]
    res["coverage"] = round(sum(1 for q in ws if any(a - 0.15 <= q["t0"] < b for a, b in spans)) / max(1, len(ws)), 3)
    # GATE reference: an independent large-v3-turbo single pass of the rendered file. Captions are timed with
    # small.en per-line + energy snap, so turbo shares neither the model nor the method. Without turbo, fall back
    # to a small.en per-line re-whisper of the rendered file (no snap) and say so. Never pass without a reference.
    xc = res.get("xcheck_model") or {}
    if xc.get("median") is not None:
        ref, res["reference"] = xc, "large-v3-turbo single pass of the rendered file"
    else:
        from .captions import retime_per_line
        why = xc.get("error", "HOUSE_XCHECK_PYTHON not set or mlx_whisper missing")
        pl = retime_per_line(w16, [dict(w) for w in ws], snap=0.0, log=lambda m: None)
        write_json(os.path.join(qd, "final_words_perline.json"), pl)
        ref = res["per_line_whisper"] = _stats(vs(pl))
        res["reference"] = f"FALLBACK: small.en per-line re-whisper of the rendered file (turbo unavailable: {why[:120]})"
    ok = bool(ref.get("median") is not None and ref["p95"] <= 0.25 and not short and res["coverage"] >= 0.98)
    # reported only: small.en single pass drifts 0.12-0.19 s (up to ~0.5 s) inside dense 40 s reels (29 Sep),
    # and the acoustic check rarely has >= 3 judgeable post-pause onsets in a tightened split reel
    return ok, res


PRIVATE_PATTERNS = [
    ("email", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    ("phone", r"(?:\+?\d[\s().-]?){9,}\d"),
    ("local path", r"(?:/Users/|/home/|C:\\\\Users)"),
    ("key-like", r"\b(?:sk-[A-Za-z0-9]{8,}|ghp_[A-Za-z0-9]{8,}|xox[bap]-[A-Za-z0-9-]{8,}|AKIA[0-9A-Z]{12,})"),
]


def ocr_gate(path, dur, qd):
    tool = swift_tool("ocr")
    if tool is None:
        return None, ["OCR needs macOS Vision; gate SKIPPED (not a pass)"]
    ts = list(np.arange(0.1, dur, 0.5))
    deny = []
    if os.path.exists(CFG["denylist"]):
        deny = [l.strip() for l in open(CFG["denylist"]) if l.strip() and not l.startswith("#")]
    hits, lines = [], []
    with tempfile.TemporaryDirectory() as td:
        paths = []
        for i, f in enumerate(_frames(path, ts)):
            p = os.path.join(td, f"t{ts[i]:06.2f}.jpg"); Image.fromarray(f).save(p, quality=92); paths.append(p)
        out = subprocess.run([tool, *paths], capture_output=True, text=True).stdout
    for line in out.splitlines():
        lines.append(line)
        txt = line.split("\t", 1)[-1]
        for name, rx in PRIVATE_PATTERNS:
            for m in re.findall(rx, txt):
                hits.append(f"{line.split(chr(9))[0]}: {name}: {m}")
        for term in deny:
            if term.lower() in txt.lower():
                hits.append(f"{line.split(chr(9))[0]}: denylist term")
    with open(os.path.join(qd, "ocr.txt"), "w") as f:
        f.write("\n".join(lines))
    return len(hits) == 0, hits


def pill_candidates(rgb, exclude=()):
    """Rounded-end ('pill') shapes with text inside: the floating-badge look the house style bans."""
    import cv2
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    e = cv2.dilate(cv2.Canny(g, 40, 120), np.ones((3, 3), np.uint8))
    cnts, _ = cv2.findContours(e, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    hits = []
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        if not (28 <= h <= 150 and 60 <= w <= 720 and w / h >= 1.8):
            continue
        if cv2.contourArea(c) < 0.6 * w * h:
            continue
        if any(x >= ex - 6 and y >= ey - 6 and x + w <= ex + ew + 6 and y + h <= ey + eh + 6 for ex, ey, ew, eh in exclude):
            continue
        m = np.zeros((h, w), np.uint8); cv2.drawContours(m, [c - [x, y]], -1, 1, -1)
        r = max(4, h // 2)
        corners = np.concatenate([m[:r, :r].ravel(), m[:r, -r:].ravel(), m[-r:, :r].ravel(), m[-r:, -r:].ravel()]).mean()
        mid = m[:, r:w - r].mean() if w > 2 * r else 0
        if not (corners < 0.88 and mid > 0.9):
            continue
        inner = cv2.erode(m, np.ones((7, 7), np.uint8))
        if inner.sum() < 50:
            continue
        sub = g[y:y + h, x:x + w]
        ed = (cv2.Canny(sub, 40, 120) > 0) & (inner > 0)
        if ed.sum() / inner.sum() < 0.03:          # an empty bar (progress bar) is not a badge
            continue
        vals = rgb[y:y + h, x:x + w][inner > 0].astype(np.int16)
        med = np.median(vals, 0)
        flat = (np.abs(vals - med).max(1) < 18).mean()
        if flat < 0.45:                              # textured = real-world object, not a flat/frosted badge
            continue
        hits.append((int(x), int(y), int(w), int(h)))
    return hits


def pill_gate(path, dur, qd, caption_boxes=None, start=0.0):
    ts = list(np.arange(0.1, dur, 0.5))
    frames = _frames(path, ts)
    hd = os.path.join(qd, "pill_hits"); os.makedirs(hd, exist_ok=True)
    for f in os.listdir(hd):
        os.remove(os.path.join(hd, f))
    hits = []
    for t, f in zip(ts, frames):
        ex = []
        if caption_boxes:
            i = int(round(t * FPS))
            if 0 <= i < len(caption_boxes) and caption_boxes[i]:
                ex.append(tuple(caption_boxes[i]))
        for (x, y, w, h) in pill_candidates(f, ex):
            hits.append({"t": round(float(t), 2), "box": [x, y, w, h]})
            Image.fromarray(f[max(0, y - 20):y + h + 20, max(0, x - 20):x + w + 20]).save(os.path.join(hd, f"t{t:06.2f}_{x}_{y}.jpg"))
    return len(hits) == 0, hits


def run(job, path, fmt):
    qd = os.path.join(job, "qa"); os.makedirs(qd, exist_ok=True)
    dur = duration(path)
    meta = read_json(os.path.join(job, "render_meta.json")) if os.path.exists(os.path.join(job, "render_meta.json")) else {}
    report = {"file": os.path.abspath(path), "duration": round(dur, 2), "gates": {}}
    sheet, _ = contact_sheet(path, os.path.join(qd, "contact.jpg"), dur)
    report["contact_sheet"] = sheet
    n, dark = black_frames(path)
    report["gates"]["black"] = {"pass": len(dark) == 0, "frames": n, "black": dark[:20]}
    caps = meta.get("captions") or read_json(os.path.join(job, "plan.json"))["captions"]
    start = meta.get("start", 0.0)
    if start:
        caps = [dict(c, t0=c["t0"] - start, t1=c["t1"] - start) for c in caps if c["t1"] > start]
        if fmt != "split":
            caps = [dict(c, words=[dict(w, t0=w["t0"] - start) for w in c["words"]]) for c in caps]
    caps = [c for c in caps if c["t0"] < dur - 0.3]
    ok, res = caption_sync(path, caps, fmt, qd)
    report["gates"]["caption_sync"] = {"pass": ok, **res}
    I, TP = loudness(path)
    report["gates"]["loudness"] = {"pass": abs(I + 14) <= 1.0 and TP <= -1.4, "lufs": I, "true_peak": TP}
    ok, hits = ocr_gate(path, dur, qd)
    report["gates"]["ocr_private"] = {"pass": ok, "hits": hits[:30]}
    ok, hits = pill_gate(path, dur, qd, meta.get("caption_boxes"))
    report["gates"]["no_pills"] = {"pass": ok, "hits": hits[:30], "crops": os.path.join(qd, "pill_hits")}
    report["all_pass"] = all(g["pass"] is True for g in report["gates"].values())
    report["LOOK"] = f"Open {sheet} and look at every frame before calling this done."
    write_json(os.path.join(qd, "qa.json"), report)
    for k, g in report["gates"].items():
        log(job, f"QA {k}: {'PASS' if g['pass'] else ('SKIPPED' if g['pass'] is None else 'FAIL')} "
                 f"{json.dumps({x: y for x, y in g.items() if x not in ('pass', 'worst', 'crops')})[:400]}")
    return report
