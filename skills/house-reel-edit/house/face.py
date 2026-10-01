"""Face measurement and framing.

Detector: macOS Vision (compiled once from swift/face.swift), with an OpenCV Haar fallback off macOS.
Framing: derive the crop PER CLIP from measured head-top and chin, never reuse one crop across clips
(a crop measured on one take cut the next take's chin off).

    H = (chin - head) / (chin_pct - head_pct)     y0 = head - head_pct * H
"""
import os
import platform
import shutil
import subprocess
import tempfile

import numpy as np

from .common import ff
from .config import CFG

_HERE = os.path.dirname(os.path.abspath(__file__))


def swift_tool(name):
    """Compile swift/<name>.swift once into the cache; returns the binary path or None off macOS."""
    if platform.system() != "Darwin" or not shutil.which("swiftc"):
        return None
    out = os.path.join(os.path.dirname(CFG["queue_dir"]), "bin", name)
    src = os.path.join(_HERE, "swift", name + ".swift")
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(src):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        subprocess.run(["nice", "-n", str(CFG["nice"]), "swiftc", "-O", src, "-o", out], check=True, capture_output=True)
    return out


def _haar(paths):
    import cv2
    cc = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
    res = []
    for p in paths:
        g = cv2.imread(p, 0)
        f = cc.detectMultiScale(g, 1.1, 5, minSize=(g.shape[1] // 10, g.shape[1] // 10))
        if len(f) == 0:
            res.append(None); continue
        x, y, w, h = max(f, key=lambda r: r[2])
        H_, W_ = g.shape
        res.append([(x + w / 2) / W_, (y + h / 2) / H_, w / W_, h / H_])
    return res


def detect(paths):
    """-> list of [cx, cy, w, h] (normalised, top-left origin) or None, one per image."""
    tool = swift_tool("face")
    if tool is None:
        return _haar(paths)
    out = subprocess.run([tool, *paths], capture_output=True, text=True, check=True).stdout.split("\n")
    import json
    return [json.loads(l) if l.strip() and l.strip() != "null" else None for l in out[: len(paths)]]


def sample_faces(video, times, width=432):
    """Detect faces at the given times of a video (small frames, cheap)."""
    with tempfile.TemporaryDirectory() as td:
        paths = []
        for i, t in enumerate(times):
            p = os.path.join(td, f"f{i:04d}.jpg")
            ff("-ss", f"{t:.3f}", "-i", video, "-frames:v", "1", "-vf", f"scale={width}:-2", "-q:v", "3", p)
            paths.append(p)
        return detect(paths)


def head_chin(box):
    """Vision's face box runs roughly brow-to-chin, so the top of the head sits about 0.35 box-heights
    above the box top: head_top = cy - 0.85h, chin = cy + 0.5h. Check it on the contact sheet."""
    cx, cy, w, h = box
    return cx, cy - 0.85 * h, cy + 0.5 * h


def solve_crop(box, src_w, src_h, out_w, out_h, head_pct, chin_pct):
    """Crop (x0, y0, cw, ch) in source pixels that puts head-top at head_pct and chin at chin_pct."""
    cx, head, chin = head_chin(box)
    head *= src_h; chin *= src_h; cx *= src_w
    ch = (chin - head) / (chin_pct - head_pct)
    ch = min(ch, src_h)
    cw = ch * out_w / out_h
    if cw > src_w:
        cw = src_w; ch = cw * out_h / out_w
    y0 = head - head_pct * ch
    x0 = cx - cw / 2
    x0 = float(np.clip(x0, 0, src_w - cw)); y0 = float(np.clip(y0, 0, src_h - ch))
    even = lambda v: int(round(v / 2) * 2)
    return even(x0), even(y0), even(cw), even(ch)


def median_box(boxes):
    b = [x for x in boxes if x]
    if not b:
        return None
    return list(np.median(np.array(b), axis=0))


def track(video, dur, fps_sample=5):
    """Per-sample face boxes over a whole video, interpolated over misses and smoothed
    (zero-phase, sigma ~3 samples) so the virtual camera never jitters."""
    ts = np.arange(0, dur, 1 / fps_sample)
    boxes = sample_faces(video, ts)
    arr = np.array([b if b else [np.nan] * 4 for b in boxes], dtype=np.float64)
    for k in range(4):
        col = arr[:, k]; ok = ~np.isnan(col)
        if ok.sum() == 0:
            arr[:, k] = [0.5, 0.35, 0.3, 0.3][k]
        else:
            arr[:, k] = np.interp(ts, ts[ok], col[ok])
    # zero-phase gaussian smoothing
    sig = 3.0; r = int(3 * sig); kern = np.exp(-0.5 * (np.arange(-r, r + 1) / sig) ** 2); kern /= kern.sum()
    pad = np.pad(arr, ((r, r), (0, 0)), mode="edge")
    sm = np.stack([np.convolve(pad[:, k], kern, mode="valid") for k in range(4)], 1)
    return ts.tolist(), sm.tolist(), sum(b is None for b in boxes)
