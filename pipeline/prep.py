#!/usr/bin/env python3
"""Assemble the final reel from a HeyGen avatar clip + script.json.

Automates the whole post-production chain:
  1. ffmpeg: extract 16k mono wav from the avatar clip
  2. whisper-cli: word-level timestamps
  3. align scenes to the transcript (First/Second/Third/I anchors,
     proportional fallback)
  4. remotion: render the graphics canvas (opaque H.264, avatar zone unused)
  5. ffmpeg: vstack canvas top half over cropped avatar, speed-up, loudnorm
Output: <episode>/final.mp4

Usage: python3 prep.py <episode-dir-name> [--avatar path.mp4]
       (default avatar: <episode>/avatar.mp4)
"""
import argparse, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
from configlib import load_config
CFG = load_config(HERE)
EPISODES = os.environ.get("REELS_EPISODES_DIR") or os.path.normpath(
    os.path.join(HERE, CFG["paths"]["episodes"]))
STUDIO = os.path.normpath(os.path.join(HERE, CFG["paths"]["studio"]))
WHISPER_MODEL = os.path.expanduser(
    os.environ.get("WHISPER_MODEL",
                   os.path.join(HERE, "models", "ggml-small.en.bin")))
WHISPER_MODEL_URL = ("https://huggingface.co/ggerganov/whisper.cpp/"
                     "resolve/main/ggml-small.en.bin")


def ensure_whisper_model():
    """Auto-download the whisper model on first run (same pattern as
    facedet.py's YuNet download). ~466MB, one time."""
    if os.path.exists(WHISPER_MODEL):
        return
    os.makedirs(os.path.dirname(WHISPER_MODEL), exist_ok=True)
    print(f"whisper model not found — downloading to {WHISPER_MODEL} (~466MB, one time)")
    import urllib.request
    tmp = WHISPER_MODEL + ".part"
    urllib.request.urlretrieve(WHISPER_MODEL_URL, tmp)
    os.rename(tmp, WHISPER_MODEL)
# Optional: point Remotion at a specific browser binary (Linux servers where
# the auto-downloaded headless shell is flaky): export REELS_BROWSER=/usr/bin/chromium
REELS_BROWSER = os.environ.get("REELS_BROWSER")


def run(cmd, **kw):
    print("$", " ".join(str(c) for c in cmd))
    subprocess.run([str(c) for c in cmd], check=True, **kw)


def probe(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", path])
    d = json.loads(out)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    return {"w": v["width"], "h": v["height"],
            "duration": float(d["format"]["duration"])}


def norm(w):
    return re.sub(r"[^a-z0-9]", "", w.lower())


def _edit_distance(a, b):
    if abs(len(a) - len(b)) > 2:
        return 3
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def fix_misheard(words, epdir):
    """Correct Whisper mishearings against the script's own vocabulary.

    The script is ground truth: a transcribed word that isn't in the script
    but is within edit distance 1 (or 2 for 6+ letter words) of a script word
    is replaced by that script word, keeping the script's casing (so the CTA
    keyword always renders exactly — 'repose' can never ship again). Timing
    is untouched.
    """
    spath = os.path.join(epdir, "script.json")
    if not os.path.exists(spath):
        return words
    scenes = json.load(open(spath)).get("scenes", [])
    vocab = {}
    for sc in scenes:
        for w in (sc.get("text") or "").split():
            k = norm(w)
            if k:
                cand = w.strip(".,!?;:\"'")
                cur = vocab.get(k)
                # ALL-CAPS script words (CTA keywords) beat other casings, so
                # a lowercase use earlier in the script can't demote "TOOLS"
                # to "tools" in the caption that matters.
                if cur is None or (cand.isupper() and len(cand) > 1 and not cur.isupper()):
                    vocab[k] = cand
    for entry in words:
        raw = entry["word"]
        m = re.match(r"^(\W*)([\w'-]+)(\W*)$", raw)
        if not m:
            continue
        pre, core, post = m.groups()
        k = norm(core)
        if not k:
            continue
        if k in vocab:
            # same word, wrong surface form: fix hyphenation ("Deep-Seek" ->
            # "DeepSeek") and enforce ALL-CAPS script words ("Repos" -> "REPOS"),
            # but leave pure sentence-case differences alone.
            script_w = vocab[k]
            if core.lower() != script_w.lower() or (script_w.isupper() and len(script_w) > 1 and core != script_w):
                entry["word"] = pre + script_w + post
            continue
        limit = 2 if len(k) >= 6 else 1
        best = min(vocab, key=lambda v: _edit_distance(k, v))
        if _edit_distance(k, best) <= limit:
            entry["word"] = pre + vocab[best] + post
    return words


def transcribe(epdir, avatar):
    ensure_whisper_model()
    wav = os.path.join(epdir, "audio.wav")
    run(["ffmpeg", "-y", "-v", "quiet", "-i", avatar, "-ar", "16000", "-ac", "1", wav])
    run(["whisper-cli", "-m", WHISPER_MODEL, "-f", wav, "-ml", "1", "-sow",
         "-oj", "-of", os.path.join(epdir, "words")],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(wav)
    d = json.load(open(os.path.join(epdir, "words.json")))
    words = [{"word": s["text"].strip(), "startMs": s["offsets"]["from"],
              "endMs": s["offsets"]["to"]} for s in d["transcription"] if s["text"].strip()]
    return fix_misheard(words, epdir)


def analyze_avatar(avatar_path, meta):
    """Letterbox-proof analysis of the HeyGen render.

    Returns (content_box, face_box_or_None) in SOURCE pixels.
    content_box excludes uniform letterbox bands (white canvas, black bars,
    or the dark #0A0A0D canvas) on all four edges, so the composite can zoom
    into the real video and NO canvas pixel can ever reach the frame.
    """
    import facedet
    if not facedet.available():
        print("!! cv2 not installed — cannot letterbox-detect; using full frame")
        return (0, 0, meta["w"], meta["h"]), None
    import cv2, numpy as np, tempfile
    frames = []
    with tempfile.TemporaryDirectory() as td:
        for i, frac in enumerate((0.2, 0.5, 0.8)):
            fp = os.path.join(td, f"f{i}.png")
            subprocess.run(["ffmpeg", "-y", "-v", "quiet", "-ss",
                            str(meta["duration"] * frac), "-i", avatar_path,
                            "-frames:v", "1", fp], check=False)
            img = cv2.imread(fp)
            if img is not None:
                frames.append(img)
    if not frames:
        return (0, 0, meta["w"], meta["h"]), None

    def uniform_mask(gray, axis):
        std = gray.std(axis=axis)
        mean = gray.mean(axis=axis)
        return (std < 12) & ((mean > 165) | (mean < 26))

    h, w = frames[0].shape[:2]
    top, bottom, left, right = 0, h, 0, w
    rows = np.ones(h, bool)
    cols = np.ones(w, bool)
    for f in frames:
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype("float32")
        rows &= uniform_mask(g, axis=1)
        cols &= uniform_mask(g, axis=0)
    while top < h // 2 and rows[top]:
        top += 1
    while bottom > h // 2 and rows[bottom - 1]:
        bottom -= 1
    while left < w // 2 and cols[left]:
        left += 1
    while right > w // 2 and cols[right - 1]:
        right -= 1
    # small safety inset so anti-aliased canvas edges never bleed in
    inset = 6
    top, bottom = top + inset, bottom - inset
    left, right = left + inset, right - inset
    content = (left, top, max(right - left, 32), max(bottom - top, 32))

    tops, bottoms = [], []
    for f in frames:
        faces = [b for b in facedet.detect(f) if b[2] >= meta["w"] // 10]
        if faces:
            x, y, fw, fh = faces[0]
            tops.append(y)
            bottoms.append(y + fh)
    face = (min(tops), max(bottoms)) if len(tops) >= 2 else None
    print(f"content box: x={content[0]} y={content[1]} w={content[2]} h={content[3]} "
          f"(source {w}x{h}) | face rows: {face}")
    return content, face


ANCHORS = ["first", "second", "third", "fourth", "fifth"]


def align(scenes, words, total_ms):
    """Scene boundaries from anchor words; proportional fallback.

    Among candidate occurrences of an anchor word, pick the one closest to
    the scene's expected position (proportional to script word counts) —
    first-match grabs strays, e.g. a CTA anchored on the "I" in "the one I
    teased" a scene early."""
    counts = [len(sc["text"].split()) for sc in scenes]
    total_words = sum(counts) or 1
    expected, acc = [], 0
    for c in counts:
        expected.append(round(acc / total_words * len(words)))
        acc += c
    bounds = [0]
    cursor = 0
    ok = True
    n_repo = 0
    for k, sc in enumerate(scenes[1:], start=1):
        if sc["type"] == "repo":
            anchor = ANCHORS[n_repo]
            n_repo += 1
            cands = [i for i in range(cursor + 1, len(words))
                     if norm(words[i]["word"]) == anchor]
        else:
            # Match the scene's own opening words — bigram first (robust for
            # natural openers), single word as fallback. Scripts no longer
            # need "So"/"Now" scene anchors; any distinctive opening works.
            toks = [norm(w) for w in sc["text"].split() if norm(w)]
            w1 = toks[0] if toks else ""
            w2 = toks[1] if len(toks) > 1 else None
            cands = [i for i in range(cursor + 1, len(words) - 1)
                     if norm(words[i]["word"]) == w1
                     and (w2 is None or norm(words[i + 1]["word"]) == w2)]
            if not cands:
                cands = [i for i in range(cursor + 1, len(words))
                         if norm(words[i]["word"]) == w1]
        if not cands:
            ok = False
            break
        idx = min(cands, key=lambda i: abs(i - expected[k]))
        bounds.append(idx)
        cursor = idx
    if ok:
        bounds.append(len(words))
    else:
        print("!! anchor alignment failed, falling back to proportional split")
        counts = [len(sc["text"].split()) for sc in scenes]
        total_words = sum(counts)
        bounds, acc = [0], 0
        for c in counts[:-1]:
            acc += c
            bounds.append(round(acc / total_words * len(words)))
        bounds.append(len(words))

    for i, sc in enumerate(scenes):
        a, b = bounds[i], bounds[i + 1]
        start = words[a]["startMs"]
        end = words[b]["startMs"] if b < len(words) else total_ms
        sc["durationSec"] = round((end - start) / 1000, 3)
    return scenes, words


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--avatar", default=None)
    args = ap.parse_args()
    epdir = os.path.join(EPISODES, args.episode)
    avatar = args.avatar or os.path.join(epdir, "avatar.mp4")
    if not os.path.exists(avatar):
        raise SystemExit(f"no avatar clip at {avatar} — drop the HeyGen export there")

    script = json.load(open(os.path.join(epdir, "script.json")))
    meta = probe(avatar)
    print(f"avatar: {meta['w']}x{meta['h']}, {meta['duration']:.1f}s")

    # keyframe-friendly re-encode (fast decode + clean seeking)
    avatar_kf = os.path.join(epdir, "avatar-kf.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-i", avatar, "-c:v", "libx264",
         "-preset", "fast", "-crf", "18", "-g", "30", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", avatar_kf])

    words = transcribe(epdir, avatar_kf)
    total_ms = int(meta["duration"] * 1000)
    scenes, words = align(script["scenes"], words, total_ms)

    # Inline screenshot assets as data URIs (Remotion can't read episode dirs)
    import base64
    for sc in scenes:
        if sc.get("type") == "shot" and not sc["image"].startswith("data:"):
            img_path = os.path.join(epdir, sc["image"])
            if not os.path.exists(img_path):
                raise SystemExit(f"shot scene references missing {img_path}")
            b64 = base64.b64encode(open(img_path, "rb").read()).decode()
            sc["image"] = f"data:image/jpeg;base64,{b64}"

    layout = script.get("layout", "split")
    # RepoDrop is the default look; set "style": "RepoRadar" in the script to
    # render an older episode with the previous composition.
    STYLE = script.get("style", "RepoDrop")
    props = {
        "date": script["date"], "scenes": scenes, "layout": layout,
        "avatarTransparent": True, "captions": words,
    }
    props_path = os.path.join(epdir, "props.json")
    json.dump(props, open(props_path, "w"), indent=1)

    # fullscreen: graphics+captions render as a TRANSPARENT overlay (ProRes
    # 4444) — the full-frame avatar shows through wherever nothing is drawn.
    if layout in ("fullscreen", "pip"):
        canvas = os.path.join(epdir, "canvas.mov")
        render_cmd = ["npx", "remotion", "render", STYLE, canvas,
                      f"--props={props_path}", "--codec=prores",
                      "--prores-profile=4444", "--image-format=png",
                      "--pixel-format=yuva444p10le"]
    else:
        canvas = os.path.join(epdir, "canvas.mp4")
        render_cmd = ["npx", "remotion", "render", STYLE, canvas,
                      f"--props={props_path}"]
    if REELS_BROWSER:
        render_cmd.append(f"--browser-executable={REELS_BROWSER}")
    run(render_cmd, cwd=STUDIO)

    # composite: canvas top 960 over the avatar CONTENT region (letterbox
    # excluded by construction), zoomed to cover, face-positioned.
    v = CFG["video"]
    (cx, cy, cw, ch), face = analyze_avatar(avatar_kf, meta)
    sc = max(1080 / cw, 960 / ch)
    rw2, rh2 = round(cw * sc), round(ch * sc)
    if face:
        ft = (face[0] - cy) * sc          # face top in zoomed content coords
        fb = (face[1] - cy) * sc
        off_y = ft - 150
        off_y = max(off_y, fb + 40 - 960)  # chin stays inside
    else:
        off_y = v["avatarFocusY"] * rh2 - 480
    off_y = min(max(round(off_y), 0), max(rh2 - 960, 0))
    off_x = max((rw2 - 1080) // 2, 0)
    speed = v["speed"]
    final = os.path.join(epdir, "final.mp4")

    # fullscreen: avatar covers the whole 1080x1920 frame (content region
    # zoomed), face composed toward the upper third; graphics overlay on top.
    if layout in ("fullscreen", "pip"):
        scf = max(1080 / cw, 1920 / ch)
        rwf, rhf = round(cw * scf), round(ch * scf)
        if face:
            ftf = (face[0] - cy) * scf
            offf = min(max(round(ftf - 320), 0), max(rhf - 1920, 0))
        else:
            offf = max((rhf - 1920) // 3, 0)
        offxf = max((rwf - 1080) // 2, 0)

        def composite(off):
            run(["ffmpeg", "-y", "-v", "warning", "-i", avatar_kf, "-i", canvas,
                 "-filter_complex",
                 f"[0:v]crop={cw}:{ch}:{cx}:{cy},scale={rwf}:{rhf},"
                 f"crop=1080:1920:{offxf}:{offf},fps={v['fps']}[base];"
                 f"[base][1:v]overlay=0:0:format=auto,setpts=PTS/{speed}[v];"
                 f"[0:a]atempo={speed},loudnorm=I={v['loudnormI']}:TP=-1.5:LRA=11[a]",
                 "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "17",
                 "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac",
                 "-b:a", "192k", "-movflags", "+faststart", final])
    else:
        def composite(off):
            run(["ffmpeg", "-y", "-v", "warning", "-i", canvas, "-i", avatar_kf,
                 "-filter_complex",
                 f"[1:v]crop={cw}:{ch}:{cx}:{cy},scale={rw2}:{rh2},"
                 f"crop=1080:960:{off_x}:{off},fps={v['fps']}[bot];"
                 f"[0:v]crop=1080:960:0:0[top];[top][bot]vstack=inputs=2,setpts=PTS/{speed}[v];"
                 f"[1:a]atempo={speed},loudnorm=I={v['loudnormI']}:TP=-1.5:LRA=11[a]",
                 "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "17",
                 "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                 "-movflags", "+faststart", final])

    HEADROOM_TARGET = 110  # aim above qa.py's 60px minimum, with margin
    for attempt in range(3):
        composite(off_y)
        qa = subprocess.run([sys.executable, os.path.join(HERE, "qa.py"),
                             args.episode], cwd=HERE)
        report = json.load(open(os.path.join(epdir, "qa.json")))
        if report["pass"]:
            break
        face = report.get("face", {})
        frames = [f for f in face.get("frames", []) if f.get("headroom") is not None]
        only_face_failed = all(v.get("pass", True) for k, v in report.items()
                               if isinstance(v, dict) and k != "face")
        if not (only_face_failed and frames and attempt < 2):
            raise SystemExit(f"QA failed (see {epdir}/qa.json)")
        min_hr = min(f["headroom"] for f in frames)
        adjust = HEADROOM_TARGET - min_hr
        new_off = min(max(off_y - adjust, 0), max(rh2 - 960, 0))
        if new_off == off_y:
            raise SystemExit(f"QA face check failed and crop can't move further "
                             f"(see {epdir}/qa.json) — check the HeyGen framing")
        print(f"QA face check: min headroom {min_hr}px -> shifting crop "
              f"{off_y} -> {new_off} and re-compositing")
        off_y = new_off

    out = probe(final)
    print(f"DONE -> {final}  ({out['duration']:.1f}s, QA pass, crop offset {off_y})")

    # deliver the QA-passed final to Telegram (approval surface on the phone):
    # inline video for instant watching + document for the pristine postable file
    try:
        import telegram
        title = script.get("social", {}).get("title", args.episode)
        telegram.send_video(final, f"✅ QA passed — {args.episode}\n{title}")
        if telegram.send_document(final, "📦 Original quality — post this file"):
            print("sent to Telegram (video + document)")
    except Exception as e:
        print("telegram delivery failed:", e)

    # keep the volume lean: render intermediates are huge (ProRes canvas is
    # ~300MB/video) and only final.mp4 + metadata matter after QA passes
    for junk in ("canvas.mov", "avatar-kf.mp4", "audio.wav", "audio16.wav"):
        p = os.path.join(epdir, junk)
        if os.path.exists(p):
            os.remove(p)


if __name__ == "__main__":
    main()
