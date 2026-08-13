#!/usr/bin/env python3
"""HeyGen API avatar rendering (pay-as-you-go credits, ~$1/min of video).

Takes an episode's script.json, generates the avatar video via the HeyGen API
(one scene per script scene, so panel cuts line up with delivery), polls until
done, downloads it as <episode>/avatar.mp4 — ready for prep.py.

Env (pipeline/.env):
  HEYGEN_API_KEY     required for this module
  HEYGEN_AVATAR_ID   your avatar id (HeyGen > Avatars > ... > copy ID)
  HEYGEN_VOICE_ID    your ElevenLabs-linked voice id in HeyGen

Usage: python3 heygen.py <episode-dir-name>
"""
import json, os, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
from configlib import load_config
CFG = load_config(HERE)
EPISODES = os.environ.get("REELS_EPISODES_DIR") or os.path.normpath(
    os.path.join(HERE, CFG["paths"]["episodes"]))
API = "https://api.heygen.com"


def env(name, default=None):
    path = os.path.join(HERE, ".env")
    if os.path.exists(path) and name not in os.environ:
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    return os.environ.get(name, default)


def call(method, path, body=None):
    req = urllib.request.Request(
        API + path,
        data=json.dumps(body).encode() if body else None,
        method=method,
        headers={"X-Api-Key": env("HEYGEN_API_KEY"),
                 "content-type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def pick_avatar(ep, script):
    """Rotate between the owner's avatar looks so back-to-back videos don't
    all show the identical clone. script.json "avatarId" pins a look for one
    episode; config video.avatarLooks rotates deterministically by episode
    name (stable across re-runs of the same episode); env is the fallback."""
    if script.get("avatarId"):
        return script["avatarId"]
    looks = CFG.get("video", {}).get("avatarLooks") or []
    if looks:
        import hashlib
        i = int(hashlib.md5(ep.encode()).hexdigest(), 16) % len(looks)
        return looks[i]
    return env("HEYGEN_AVATAR_ID")


def main():
    ep = sys.argv[1]
    epdir = os.path.join(EPISODES, ep)
    script = json.load(open(os.path.join(epdir, "script.json")))
    avatar_id = pick_avatar(ep, script)
    voice_id = env("HEYGEN_VOICE_ID")
    if not (env("HEYGEN_API_KEY") and avatar_id and voice_id):
        raise SystemExit("Set HEYGEN_API_KEY, HEYGEN_AVATAR_ID, HEYGEN_VOICE_ID in pipeline/.env")
    print(f"avatar look: {avatar_id}")

    # ONE continuous generation for the whole script: voice clones drift in
    # accent/prosody between separate TTS generations (the owner heard an
    # Australian lilt appear on the final scene). Only chunk when a script
    # exceeds HeyGen's per-scene text limit.
    full_text = " ".join(sc["text"].strip() for sc in script["scenes"])
    chunks = [full_text]
    if len(full_text) > 1800:
        chunks, cur = [], ""
        for sc in script["scenes"]:
            if len(cur) + len(sc["text"]) > 1700 and cur:
                chunks.append(cur.strip())
                cur = ""
            cur += " " + sc["text"].strip()
        chunks.append(cur.strip())
    # Voice tuning from config (engine pin + stability — fixes the drift and
    # "sounds off" variance of engine-default renders). If HeyGen rejects the
    # extra settings we retry without them, so renders can never hard-fail
    # on a tuning knob.
    voice_cfg = CFG.get("video", {}).get("voice", {})

    def build_inputs(with_tuning):
        voice = {"type": "text", "voice_id": voice_id}
        if with_tuning:
            voice.update(voice_cfg)
        return [{
            "character": {"type": "avatar", "avatar_id": avatar_id,
                          "avatar_style": "normal"},
            "voice": {**voice, "input_text": chunk},
            # dark canvas: the API letterboxes non-9:16 avatar looks, and a
            # white default canvas creates an ugly seam against the template
            "background": {"type": "color", "value": "#0A0A0D"},
        } for chunk in chunks]

    inputs = build_inputs(bool(voice_cfg))

    def generate(ins):
        return call("POST", "/v2/video/generate", {
            "video_inputs": ins,
            "dimension": {"width": 1080, "height": 1920},
        })

    try:
        resp = generate(inputs)
    except Exception as e:
        print(f"voice tuning rejected ({str(e)[:120]}) — retrying without it")
        resp = generate(build_inputs(False))
    vid = (resp.get("data") or {}).get("video_id")
    if not vid:
        print(f"HeyGen error with tuning: {resp} — retrying without tuning")
        resp = generate(build_inputs(False))
        vid = (resp.get("data") or {}).get("video_id")
    if not vid:
        raise SystemExit(f"HeyGen error: {resp}")
    print(f"heygen video_id {vid} — polling (typically 2-6 min)")

    deadline = time.time() + 30 * 60
    url = None
    while time.time() < deadline:
        st = call("GET", f"/v1/video_status.get?video_id={vid}")
        data = st.get("data") or {}
        status = data.get("status")
        if status == "completed":
            url = data["video_url"]
            break
        if status == "failed":
            raise SystemExit(f"HeyGen render failed: {data.get('error')}")
        time.sleep(15)
    if not url:
        raise SystemExit("HeyGen render timed out after 30 min")

    out = os.path.join(epdir, "avatar.mp4")
    urllib.request.urlretrieve(url, out)
    print(f"downloaded -> {out} ({os.path.getsize(out)//1048576} MB)")


if __name__ == "__main__":
    main()
