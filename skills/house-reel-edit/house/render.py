"""Stage 3: compose every frame in one process and stream it straight into the hardware encoder.
No per-frame PNGs (they were written non-atomically and silently skipped on resume), no frame farms.
Runs inside the machine-wide render queue."""
import os
import subprocess

import numpy as np

from . import beats as B
from . import captions as C
from . import face as FACE
from .common import (FPS, W, H, duration, log, nice_prefix, read_json, render_slot, video_encoder_args, write_json)
from .config import CFG
from .prep import PROXY_W, PROXY_H

TIME_KEYS = {"at", "until", "done", "check_at", "highlight_at", "type_at", "dm_at", "strike_at"}


def _resolve(node, A, default_at):
    if isinstance(node, list):
        return [_resolve(x, A, default_at) for x in node]
    if not isinstance(node, dict):
        return node
    out = {}
    for k, v in node.items():
        if k in TIME_KEYS:
            out[k] = A.t(v, default_at)
        else:
            out[k] = _resolve(v, A, default_at)
    if "type" in out and "at" not in out:
        out["at"] = default_at
    return out


def resolve_scenes(bs, A, dur, fmt):
    raw = bs.get("scenes", [])
    if not raw:
        raw = [{"from": 0, "layout": "split" if fmt == "split" else "face", "elements": []}]
    sc = []
    for s in raw:
        t0 = A.t(s.get("from", 0), 0.0)
        sc.append({"t0": t0, "layout": s.get("layout", "split" if fmt == "split" else "face"),
                   "transition": s.get("transition"), "raw": s})
    sc.sort(key=lambda s: s["t0"])
    sc[0]["t0"] = 0.0
    for i, s in enumerate(sc):
        s["t1"] = sc[i + 1]["t0"] if i + 1 < len(sc) else dur + 1
        s["elements"] = [_resolve(e, A, s["t0"]) for e in s["raw"].get("elements", [])]
        for e in s["elements"]:
            e.setdefault("until", e["at"] + 1.4 if e.get("type") == "behind_head" else s["t1"])
        del s["raw"]
    return sc


def plan(job, bs, fmt):
    """Resolve the beat sheet against the final words. Returns (scenes, captions, words, anchors)."""
    tl = read_json(os.path.join(job, "timeline.json"))
    words = C.apply_fixes(read_json(os.path.join(job, "words_final.json")), bs.get("caption_fixes"))
    A = B.Anchors(words, tl["dur"])
    scenes = resolve_scenes(bs, A, tl["dur"], fmt)
    caps = C.split_chunks(words, tl["dur"]) if fmt == "split" else C.premium_groups(words, tl["dur"])
    return tl, scenes, caps, words, A


def split_crops(job, tl, bs):
    """Per-clip static crop for the face panel (1080x1214), head-top 10% / chin 66%, measured per clip."""
    cp = os.path.join(job, "crops.json")
    if os.path.exists(cp):
        return {int(k): v for k, v in read_json(cp).items()}
    fr = bs.get("framing", {})
    crops = {}
    tight = os.path.join(job, "tight.mov")
    for ci in sorted({s["clip"] for s in tl["segments"]}):
        segs = [s for s in tl["segments"] if s["clip"] == ci]
        a = segs[0]["t0"]; b = segs[-1]["t0"] + segs[-1]["nf"] / FPS
        box = FACE.median_box(FACE.sample_faces(tight, [a + (b - a) * q for q in (0.2, 0.5, 0.8)]))
        if box is None:
            box = [0.5, 0.36, 0.28, 0.16]
            log(job, f"WARN no face found in clip {ci}; using a centred default crop. Check the contact sheet.")
        crops[ci] = FACE.solve_crop(box, PROXY_W, PROXY_H, 1080, 1214, fr.get("head_pct", 0.10), fr.get("chin_pct", 0.66))
    for k, v in (bs.get("crops") or {}).items():
        crops[int(k)] = v
    write_json(cp, {str(k): v for k, v in crops.items()})
    return crops


def premium_camera(job, tl, bs, scenes):
    from .premium import Camera
    tp = os.path.join(job, "track.json")
    if not os.path.exists(tp):
        ts, boxes, miss = FACE.track(os.path.join(job, "tight.mov"), tl["dur"])
        write_json(tp, {"ts": ts, "boxes": boxes, "misses": miss})
    tr = read_json(tp)
    cuts = [s["t0"] for k, s in enumerate(tl["segments"]) if k > 0]
    cuts += [s["t0"] for s in scenes if s["t0"] > 0]
    return Camera(tr["ts"], tr["boxes"], cuts, tl["dur"], PROXY_W, PROXY_H)


def build_renderer(job, bs, fmt):
    tl, scenes, caps, words, A = plan(job, bs, fmt)
    if fmt == "split":
        from .split import SplitRenderer
        r = SplitRenderer(scenes, caps)
        crops = split_crops(job, tl, bs)
        clip_of = np.zeros(tl["frames"] + 1, np.int32)
        for s in tl["segments"]:
            clip_of[s["f0"]: s["f0"] + s["nf"]] = s["clip"]
        clip_of[-1] = clip_of[-2]

        def face_of(i, src):
            import cv2
            x0, y0, cw, ch = crops[int(clip_of[min(i, len(clip_of) - 1)])]
            return cv2.resize(np.ascontiguousarray(src[y0:y0 + ch, x0:x0 + cw]), (1080, 1214), interpolation=cv2.INTER_AREA)
        fn = lambda i, t, src: r.frame(t, face_of(i, src))
    else:
        from .premium import PremiumRenderer
        r = PremiumRenderer(scenes, caps, bs.get("accents"), premium_camera(job, tl, bs, scenes))
        fn = lambda i, t, src: r.frame(t, src)
    write_json(os.path.join(job, "plan.json"), {"scenes": scenes, "captions": caps, "missing_anchors": A.missing})
    if A.missing:
        log(job, f"WARN anchors not found (element hidden): {A.missing}")
    return tl, r, fn, caps


def _decoder(src, start=0.0):
    return subprocess.Popen(nice_prefix() + ["ffmpeg", "-v", "error", "-nostdin", "-threads", str(CFG["ffmpeg_threads"]),
                                             "-ss", f"{start:.3f}", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                            stdout=subprocess.PIPE)


def stills(job, bs, fmt, times, outdir=None):
    """Look-dev stills (cheap): compose single frames to JPGs so the agent can LOOK before a render."""
    from PIL import Image
    tl, r, fn, caps = build_renderer(job, bs, fmt)
    outdir = outdir or os.path.join(job, "look"); os.makedirs(outdir, exist_ok=True)
    paths = []
    for t in times:
        raw = subprocess.run(nice_prefix() + ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", os.path.join(job, "tight.mov"),
                                              "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        src = np.frombuffer(raw, np.uint8).reshape(PROXY_H, PROXY_W, 3)
        p = os.path.join(outdir, f"still_{t:06.2f}.jpg")
        Image.fromarray(fn(int(round(t * FPS)), t, src)).save(p, quality=88); paths.append(p)
    return paths


def render(job, bs, fmt, out, start=0.0, limit=None):
    tl, r, fn, caps = build_renderer(job, bs, fmt)
    dur = tl["dur"] if limit is None else min(tl["dur"] - start, limit)
    N = int(round(dur * FPS)); f0 = int(round(start * FPS))
    master = os.path.join(job, "master.wav")
    tmp = out + ".tmp.mp4"
    with render_slot(os.path.basename(job)):
        log(job, f"render {fmt}: {N} frames from {start:.2f}s -> {out} (load {os.getloadavg()[0]:.1f})")
        dec = _decoder(os.path.join(job, "tight.mov"), start)
        enc = subprocess.Popen(nice_prefix() + ["ffmpeg", "-v", "error", "-nostdin", "-threads", str(CFG["ffmpeg_threads"]), "-y",
                                                "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                                                "-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", master,
                                                "-map", "0:v", "-map", "1:a", *video_encoder_args(),
                                                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest",
                                                "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
        fsz = PROXY_W * PROXY_H * 3; last = None
        for i in range(N):
            raw = dec.stdout.read(fsz)
            if len(raw) == fsz:
                last = np.frombuffer(raw, np.uint8).reshape(PROXY_H, PROXY_W, 3)
            t = (f0 + i) / FPS
            enc.stdin.write(np.ascontiguousarray(fn(f0 + i, t, last)).tobytes())
            if i % 150 == 0:
                log(job, f"frame {i}/{N}")
        enc.stdin.close(); rc = enc.wait(); dec.kill()
        if rc != 0:
            raise SystemExit(f"encoder failed ({rc})")
    os.replace(tmp, out)
    write_json(os.path.join(job, "render_meta.json"), {"out": out, "start": start, "dur": dur, "format": fmt,
                                                        "caption_boxes": r.caption_boxes, "captions": caps})
    log(job, f"rendered {out} ({duration(out):.2f}s)")
    return out


def telegram_copy(src, dst):
    """One saved preset: 720 wide, ~6 Mbps, stays under Telegram's 50 MB bot limit."""
    from .common import ff
    ff("-i", src, "-vf", f"scale=-2:{CFG['telegram_height']}", *video_encoder_args(CFG["telegram_bitrate"], "8M"),
       "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", dst)
    return dst
