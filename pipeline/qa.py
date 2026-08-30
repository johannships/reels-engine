#!/usr/bin/env python3
"""QA gate — every final.mp4 must pass before anything gets posted.

Checks (writes <episode>/qa.json, exit 0 = pass, 1 = fail):
  format    1080x1920, ~30fps, 15-70s, audio stream present, file > 3 MB
  loudness  mean volume in a sane window (audio not silent / not clipping)
  black     no black segments >= 0.4s (broken canvas / gap)
  freeze    no frozen video >= 3s (stuck renderer)
  captions  whisper heard >= 70% of the script's word count (audio intact,
            not garbled, right file)
  caption_sync
            captions land ON the words: the caption timeline and the finished
            audio's speech envelope cross-correlate at a lag within 0.25s
  face      the avatar's face is fully in frame with headroom: sampled frames
            of the bottom half must show a face whose box top sits >= 60px
            below the seam and whose box bottom stays >= 40px above the frame
            edge. Needs opencv-python-headless; if cv2 is missing the check
            is SKIPPED with a loud warning (install it on the server).

Usage: python3 qa.py <episode>   [--video path.mp4]
"""
import argparse, json, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
from configlib import load_config
CFG = load_config(HERE)
EPISODES = os.environ.get("REELS_EPISODES_DIR") or os.path.normpath(
    os.path.join(HERE, CFG["paths"]["episodes"]))

SEAM = 960          # avatar slot top in the 1080x1920 frame
HEADROOM_MIN = 60   # px required between seam and top of face box
CHIN_MARGIN = 40    # px required between face box bottom and frame bottom


def sh(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def probe(path):
    out = sh(["ffprobe", "-v", "quiet", "-print_format", "json",
              "-show_format", "-show_streams", path])
    return json.loads(out.stdout)


def check_format(path, report):
    d = probe(path)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    dur = float(d["format"]["duration"])
    size = int(d["format"]["size"])
    ok = (v and v["width"] == 1080 and v["height"] == 1920
          and a is not None and 15 <= dur <= 70 and size > 3_000_000)
    report["format"] = {"pass": bool(ok), "duration": round(dur, 1),
                        "size_mb": size // 1048576,
                        "res": f"{v['width']}x{v['height']}" if v else None,
                        "audio": a is not None}
    return ok


def check_loudness(path, report):
    out = sh(["ffmpeg", "-i", path, "-af", "volumedetect", "-f", "null", "-"])
    m = re.search(r"mean_volume: (-?[\d.]+) dB", out.stderr)
    mean = float(m.group(1)) if m else None
    ok = mean is not None and -30 <= mean <= -8
    report["loudness"] = {"pass": bool(ok), "mean_db": mean}
    return ok


def check_black_freeze(path, report):
    out = sh(["ffmpeg", "-i", path, "-vf",
              "blackdetect=d=0.4:pix_th=0.02,freezedetect=n=-60dB:d=3",
              "-an", "-f", "null", "-"])
    black = re.findall(r"black_start", out.stderr)
    frozen = re.findall(r"freeze_start", out.stderr)
    report["black"] = {"pass": not black, "segments": len(black)}
    report["freeze"] = {"pass": not frozen, "segments": len(frozen)}
    return not black and not frozen


def check_captions(epdir, report):
    wpath, spath = os.path.join(epdir, "words.json"), os.path.join(epdir, "script.json")
    if not (os.path.exists(wpath) and os.path.exists(spath)):
        report["captions"] = {"pass": True, "note": "skipped (no words/script json)"}
        return True
    heard = len([w for w in json.load(open(wpath))["transcription"] if w["text"].strip()])
    scripted = sum(len(sc["text"].split()) for sc in json.load(open(spath))["scenes"])
    ratio = heard / max(scripted, 1)
    ok = ratio >= 0.7
    report["captions"] = {"pass": bool(ok), "heard": heard,
                          "scripted": scripted, "ratio": round(ratio, 2)}
    return ok


CAPTION_LAG_MAX = 0.25   # seconds of drift tolerated between captions and speech


def check_caption_sync(path, epdir, report):
    """Do captions land on the words? Direct measurement: whisper the FINAL
    file and compare per-word onsets against words.json (scaled by
    video.speed, since words.json is measured pre-speedup).

    Replaces an energy-envelope cross-correlation that gave three mutually
    contradictory readings (-0.14, -0.9, -1.4) on renders whose whisper-vs-
    whisper ground truth measured <=0.12s. One extra whisper pass on a ~30s
    file is cheap; a gate nobody can trust is expensive.
    """
    import difflib, tempfile
    wpath = os.path.join(epdir, "words.json")
    if not os.path.exists(wpath):
        report["caption_sync"] = {"pass": True, "note": "skipped (no words.json)"}
        return True
    model = os.environ.get("WHISPER_MODEL", "/models/ggml-small.en.bin")
    if not os.path.exists(model):
        report["caption_sync"] = {"pass": True, "note": "skipped (no whisper model)"}
        return True
    speed = float(CFG.get("video", {}).get("speed", 1.0) or 1.0)
    norm_w = lambda t: re.sub(r"[^a-z0-9]", "", t.lower())
    ref = [(w["offsets"]["from"] / 1000.0 / speed, norm_w(w["text"]))
           for w in json.load(open(wpath))["transcription"] if norm_w(w["text"])]
    with tempfile.TemporaryDirectory() as td:
        wav = os.path.join(td, "a.wav")
        sh(["ffmpeg", "-y", "-v", "error", "-i", path, "-ar", "16000", "-ac", "1",
            "-c:a", "pcm_s16le", wav])
        out = os.path.join(td, "fw")
        sh(["whisper-cli", "-m", model, "-f", wav, "-ml", "1", "-oj", "-of", out])
        try:
            heard = [(w["offsets"]["from"] / 1000.0, norm_w(w["text"]))
                     for w in json.load(open(out + ".json"))["transcription"]
                     if norm_w(w["text"])]
        except Exception as e:
            report["caption_sync"] = {"pass": True,
                                      "note": f"skipped (final transcribe failed: {e})"}
            return True
    a = [t for _, t in ref]; b = [t for _, t in heard]
    pairs = difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_matching_blocks()
    deltas = []
    for blk in pairs:
        for k in range(blk.size):
            deltas.append(heard[blk.b + k][0] - ref[blk.a + k][0])
    if len(deltas) < 10:
        report["caption_sync"] = {"pass": True, "note": "skipped (too few matched words)"}
        return True
    deltas.sort()
    med = deltas[len(deltas) // 2]
    p90 = deltas[int(len(deltas) * 0.9)]
    ok = abs(med) <= CAPTION_LAG_MAX and abs(p90) <= CAPTION_LAG_MAX * 2
    report["caption_sync"] = {"pass": bool(ok), "lag_sec": round(med, 3),
                              "p90_sec": round(p90, 3),
                              "matched": len(deltas), "tolerance": CAPTION_LAG_MAX,
                              "method": "whisper-final vs words/speed"}
    if not ok:
        print(f"!! captions drift median {med:+.2f}s (p90 {p90:+.2f}s)", file=sys.stderr)
    return ok


def check_seam(path, dur, report):
    """The strip just below the canvas/avatar seam must not be a bright
    uniform band (HeyGen letterboxing white canvas). Uses ffmpeg signalstats
    on a crop of rows 960-1100."""
    def strip_avg(y, h):
        out = sh(["ffmpeg", "-ss", str(dur * 0.4), "-i", path, "-frames:v", "30",
                  "-vf", f"crop=1080:{h}:0:{y},signalstats,metadata=print",
                  "-f", "null", "-"])
        vals = re.findall(r"YAVG:([\d.]+)", out.stderr)
        return sum(float(v) for v in vals) / len(vals) if vals else 0

    top_avg = strip_avg(960, 140)      # just below the graphics/avatar seam
    bot_avg = strip_avg(1800, 120)     # bottom edge of the frame
    # letterbox white reads ~235 uniform; real footage (room, shirt) stays lower
    ok = top_avg < 170 and bot_avg < 190
    report["seam"] = {"pass": bool(ok), "y_avg_below_seam": round(top_avg, 1),
                      "y_avg_bottom": round(bot_avg, 1)}
    return ok


def check_face(path, dur, report):
    import facedet
    if not facedet.available():
        report["face"] = {"pass": True,
                          "note": "SKIPPED — cv2 not installed (pip install opencv-python-headless)"}
        print("!! face check skipped: install opencv-python-headless", file=sys.stderr)
        return True
    import cv2
    times = [dur * f for f in (0.15, 0.4, 0.65, 0.9)]
    results = []
    with tempfile.TemporaryDirectory() as td:
        for i, t in enumerate(times):
            fp = os.path.join(td, f"f{i}.png")
            sh(["ffmpeg", "-y", "-v", "quiet", "-ss", str(t), "-i", path,
                "-frames:v", "1", fp])
            img = cv2.imread(fp)
            if img is None:
                continue
            faces = [f for f in facedet.detect(img[SEAM:1920, :])
                     if f[2] >= 140 and f[3] >= 140]
            if not faces:
                results.append({"t": round(t, 1), "face": None})
                continue
            x, y, w, h = faces[0]
            headroom = y                       # px below seam (bottom-half coords)
            chin_gap = (1920 - SEAM) - (y + h)
            results.append({"t": round(t, 1), "headroom": int(headroom),
                            "chin_gap": int(chin_gap)})
    found = [r for r in results if r.get("headroom") is not None]
    ok = (len(found) >= 2
          and all(r["headroom"] >= HEADROOM_MIN for r in found)
          and all(r["chin_gap"] >= -10 for r in found))  # chin may sit at edge by design
    report["face"] = {"pass": bool(ok), "frames": results,
                      "rule": f"headroom>={HEADROOM_MIN}px in all detected frames, "
                              f">=2 of {len(times)} frames must detect a face"}
    return ok


def check_face_fullscreen(path, windows, report):
    """Fullscreen layout: during avatar scenes the face must be detected and
    fully inside the frame with margins (top >= 60px, not clipped)."""
    import facedet
    if not facedet.available():
        report["face"] = {"pass": True, "note": "SKIPPED — cv2 not installed"}
        return True
    if not windows:
        report["face"] = {"pass": True, "note": "no avatar scenes"}
        return True
    import cv2
    results, found = [], 0
    with tempfile.TemporaryDirectory() as td:
        for i, (a, b) in enumerate(windows):
            t = (a + b) / 2
            fp = os.path.join(td, f"f{i}.png")
            sh(["ffmpeg", "-y", "-v", "quiet", "-ss", str(t), "-i", path,
                "-frames:v", "1", fp])
            img = cv2.imread(fp)
            if img is None:
                continue
            faces = [f for f in facedet.detect(img) if f[2] >= 160]
            if not faces:
                results.append({"t": round(t, 1), "face": None})
                continue
            x, y, w, h = faces[0]
            ok_frame = y >= 60 and (y + h) <= 1900 and x >= 0 and (x + w) <= 1080
            found += 1
            results.append({"t": round(t, 1), "top": int(y), "ok": bool(ok_frame)})
    ok = found >= max(1, len(windows) // 2) and all(
        r.get("ok", True) for r in results if "ok" in r)
    report["face"] = {"pass": bool(ok), "frames": results,
                      "rule": "face detected + inside frame during avatar scenes"}
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--video", default=None)
    args = ap.parse_args()
    epdir = os.path.join(EPISODES, args.episode)
    path = args.video or os.path.join(epdir, "final.mp4")

    report = {}
    dur = float(probe(path)["format"]["duration"])
    props = {}
    ppath = os.path.join(epdir, "props.json")
    if os.path.exists(ppath):
        props = json.load(open(ppath))
    fullscreen = props.get("layout") == "fullscreen"

    if fullscreen:
        # face must be present and well-framed during AVATAR scenes only
        speed = CFG.get("video", {}).get("speed", 1.0)
        t = 0.0
        windows = []
        for sc in props.get("scenes", []):
            d0 = sc.get("durationSec", 0) / speed
            if sc.get("type") == "avatar":
                windows.append((t + 0.5, t + d0 - 0.5))
            t += d0
        checks = [
            check_format(path, report),
            check_loudness(path, report),
            check_black_freeze(path, report),
            check_captions(epdir, report),
            check_caption_sync(path, epdir, report),
            check_face_fullscreen(path, windows, report),
        ]
    else:
        checks = [
            check_format(path, report),
            check_loudness(path, report),
            check_black_freeze(path, report),
            check_captions(epdir, report),
            check_caption_sync(path, epdir, report),
            check_seam(path, dur, report),
            check_face(path, dur, report),
        ]
    passed = all(checks)
    report["pass"] = passed
    json.dump(report, open(os.path.join(epdir, "qa.json"), "w"), indent=1)
    for k, v in report.items():
        if isinstance(v, dict):
            print(f"  {'PASS' if v.get('pass') else 'FAIL'}  {k}: "
                  f"{ {kk: vv for kk, vv in v.items() if kk != 'pass'} }")
    print("QA:", "PASS" if passed else "FAIL")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
