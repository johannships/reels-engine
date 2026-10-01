"""Word-level timings from whisper.cpp (whisper-cli). Caption TEXT is corrected later from the
beat sheet; only the TIMING comes from whisper."""
import os
import re
import subprocess
import tempfile

from .common import ff, read_json, nice_prefix
from .config import CFG


def to16k(src, dst):
    ff("-i", src, "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", dst)
    return dst


def words(wav16, prompt=None):
    """-> [{'w': str, 't0': s, 't1': s}] ; wav16 must be 16 kHz mono."""
    if not os.path.exists(CFG["whisper_model"]):
        raise SystemExit(f"whisper model missing: {CFG['whisper_model']} (set HOUSE_WHISPER_MODEL)")
    with tempfile.TemporaryDirectory() as td:
        pre = os.path.join(td, "w")
        cmd = nice_prefix() + [CFG["whisper_bin"], "-m", CFG["whisper_model"], "-f", wav16, "-ml", "1", "-oj",
                               "-of", pre, "-np", "-t", "2"]
        if prompt:
            cmd += ["--prompt", prompt]
        subprocess.run(cmd, check=True, capture_output=True)
        j = read_json(pre + ".json")
    out = []; pending = ""
    for seg in j.get("transcription", []):
        txt = seg["text"]
        a, b = seg["offsets"]["from"] / 1000, seg["offsets"]["to"] / 1000
        if txt.strip().startswith("[") and txt.strip().endswith("]"):
            continue
        if not re.search(r"[A-Za-z0-9]", txt):
            if txt.startswith(" ") and re.search(r"[\"'(]", txt):
                pending += txt.strip()        # an opening quote belongs to the NEXT word
            elif out and txt.strip():
                out[-1]["w"] += txt.strip()   # punctuation / hyphen belongs to the previous word
            continue
        glue = out and not pending and (not txt.startswith(" ") or txt.startswith("'") or out[-1]["w"].endswith("-"))
        if glue:
            out[-1]["w"] += txt.strip(); out[-1]["t1"] = b
        else:
            out.append({"w": pending + txt.strip(), "t0": round(a, 3), "t1": round(b, 3)}); pending = ""
    return out


def pause_onsets(x, sr, quiet_db=-38.0, loud_db=-30.0, min_quiet=0.05):
    """Speech onsets that follow a measured pause (>= min_quiet s under quiet_db, then a rise over loud_db).
    These are the moments whose timing the eye checks hardest: a caption must not lead or lag them."""
    import numpy as np
    hop = int(sr * 0.005); n = len(x) // hop
    db = 20 * np.log10(np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
    out, quiet = [], 0
    for k in range(n):
        if db[k] < quiet_db:
            quiet += 1
        else:
            if db[k] > loud_db:
                if quiet * 0.005 >= min_quiet:
                    out.append(round(k * 0.005, 3))
                quiet = 0
    return out


def snap_onsets(ws, x, sr, max_shift=0.3, quiet_db=-30.0):
    """whisper word starts run early at a pause: they absorb the silence before the word (measured 29 Sep:
    ~0.2 s early after most pauses). A word cannot start in silence, so when the audio from a word's stamp up
    to the next post-pause onset (<= max_shift later) stays under quiet_db, the start moves to that onset."""
    import numpy as np
    on = np.array(pause_onsets(x, sr))
    if not len(on):
        return ws
    hop = int(sr * 0.005); n = len(x) // hop
    db = 20 * np.log10(np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)
    for w in ws:
        nxt = on[(on > w["t0"]) & (on <= w["t0"] + max_shift)]
        if len(nxt):
            a, b = int(w["t0"] / 0.005), int(nxt[0] / 0.005) - 1
            if b > a and db[a:b].max() < quiet_db:
                w["t0"] = round(float(nxt[0]), 3)
    return ws
