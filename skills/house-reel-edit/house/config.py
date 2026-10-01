"""Settings for house-edit. Nothing personal is hardcoded: every path comes from
an environment variable or ~/.config/house-edit/config.json, with ~-relative defaults.

    HOUSE_FONTS          folder with Inter-Var.ttf, JetBrainsMono-Variable.ttf (+ optional Playfair-Italic.ttf)
    HOUSE_WHISPER_MODEL  whisper.cpp ggml model (small.en is enough for word timings)
    HOUSE_WHISPER_BIN    whisper-cli binary (default: first on PATH)
    HOUSE_QUEUE_DIR      render-queue lock folder (shared by every agent on the machine)
    HOUSE_DENYLIST       text file, one private term per line (client names, people) for the OCR gate.
                         Keep it OUTSIDE the repo.
"""
import json
import os

_DEFAULTS = {
    "fonts": "~/.config/house-edit/fonts",
    "whisper_model": "~/.config/house-edit/models/ggml-small.en.bin",
    "whisper_bin": "whisper-cli",
    "queue_dir": "~/.cache/house-edit/queue",
    "denylist": "~/.config/house-edit/denylist.txt",
    # machine-load rules (see SKILL.md "Machine load")
    "max_concurrent_renders": 1,     # 2 only when the machine is idle (load < idle_load)
    "idle_load": 4.0,
    "max_start_load": 12.0,          # a render waits in the queue while load is above this
    "nice": 10,
    "ffmpeg_threads": 2,
    "video_encoder": "h264_videotoolbox",   # hardware encode; falls back to libx264 -preset veryfast
    "video_bitrate": "14M",
    "video_maxrate": "20M",
    "telegram_bitrate": "6M",         # preview copy stays under Telegram's 50 MB limit
    "telegram_height": 1280,
}

_ENV = {
    "fonts": "HOUSE_FONTS",
    "whisper_model": "HOUSE_WHISPER_MODEL",
    "whisper_bin": "HOUSE_WHISPER_BIN",
    "queue_dir": "HOUSE_QUEUE_DIR",
    "denylist": "HOUSE_DENYLIST",
}


def load():
    cfg = dict(_DEFAULTS)
    p = os.path.expanduser(os.environ.get("HOUSE_CONFIG", "~/.config/house-edit/config.json"))
    if os.path.exists(p):
        with open(p) as f:
            cfg.update(json.load(f))
    for k, env in _ENV.items():
        if os.environ.get(env):
            cfg[k] = os.environ[env]
    for k in ("fonts", "whisper_model", "queue_dir", "denylist"):
        cfg[k] = os.path.expanduser(cfg[k])
    return cfg


CFG = load()


def font_path(name):
    """name: 'inter' | 'mono' | 'serif'"""
    files = {"inter": "Inter-Var.ttf", "mono": "JetBrainsMono-Variable.ttf", "serif": "Playfair-Italic.ttf"}
    p = os.path.join(CFG["fonts"], files[name])
    if not os.path.exists(p):
        raise SystemExit(f"font missing: {p}\nSet HOUSE_FONTS to a folder with {files[name]} "
                         "(Inter and JetBrains Mono are free from Google Fonts; fonts are not shipped in this repo).")
    return p
