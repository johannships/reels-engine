"""Shared helpers: niced subprocesses, wav io, atomic writes, the progress log, and the
machine-wide render queue (max 1-2 renders at once across every agent)."""
import contextlib
import fcntl
import json
import os
import re
import subprocess
import time
import wave

import numpy as np

from .config import CFG

# keep numeric libraries from spawning a thread per core (8 agents x 8 threads melted the Mac once)
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

W, H, FPS, SR = 1080, 1920, 30, 48000


def nice_prefix():
    return ["nice", "-n", str(CFG["nice"])]


def ff(*args, capture=False, check=True):
    """ffmpeg, niced, 2 threads, quiet."""
    cmd = nice_prefix() + ["ffmpeg", "-v", "error", "-nostdin", "-threads", str(CFG["ffmpeg_threads"]), "-y", *map(str, args)]
    return subprocess.run(cmd, check=check, capture_output=capture)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def video_encoder_args(bitrate=None, maxrate=None):
    enc = CFG["video_encoder"]
    if enc.endswith("videotoolbox"):
        return ["-c:v", enc, "-b:v", bitrate or CFG["video_bitrate"], "-maxrate", maxrate or CFG["video_maxrate"],
                "-profile:v", "high", "-pix_fmt", "yuv420p"]
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p"]


def read_wav(path):
    with wave.open(path) as w:
        sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
        x = np.frombuffer(w.readframes(w.getnframes()), {2: np.int16, 4: np.int32}[sw]).astype(np.float32)
    x /= 2 ** (8 * sw - 1)
    if ch > 1:
        x = x.reshape(-1, ch).mean(1)
    return x, sr


def write_wav(path, x, sr=SR):
    tmp = path + ".tmp.wav"
    with wave.open(tmp, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    os.replace(tmp, path)


def write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1)
    os.replace(tmp, path)


def read_json(path):
    with open(path) as f:
        return json.load(f)


def log(job, msg):
    """Append to <job>/PROGRESS.log so a dead agent can be resumed from where it stopped."""
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    with open(os.path.join(job, "PROGRESS.log"), "a") as f:
        f.write(line + "\n")


def loudness(path):
    """(integrated LUFS, true peak dBTP) via ffmpeg ebur128."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true:framelog=quiet",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    s = r[r.rindex("Summary"):]
    return float(re.search(r"I:\s+(-?[\d.]+)", s).group(1)), float(re.search(r"Peak:\s+(-?[\d.]+|-inf)", s).group(1))


# ------------------------------------------------------------------ render queue
@contextlib.contextmanager
def render_slot(label="render"):
    """Hold one of N machine-wide render slots (flock). Waits while the machine is busy.
    Slot 0 is always available; slot 1 is only taken when load is under idle_load."""
    qd = CFG["queue_dir"]
    os.makedirs(qd, exist_ok=True)
    maxn = max(1, min(2, int(CFG["max_concurrent_renders"])))
    fh = None
    waited = False
    while fh is None:
        load1 = os.getloadavg()[0]
        if load1 <= CFG["max_start_load"]:
            for i in range(maxn):
                if i > 0 and load1 > CFG["idle_load"]:
                    break
                f = open(os.path.join(qd, f"slot{i}.lock"), "w")
                try:
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    f.write(f"{os.getpid()} {label}\n"); f.flush()
                    fh = f
                    break
                except BlockingIOError:
                    f.close()
        if fh is None:
            if not waited:
                print(f"[queue] waiting for a render slot (load {load1:.1f}, max {maxn})", flush=True)
                waited = True
            time.sleep(5)
    try:
        yield
    finally:
        fcntl.flock(fh, fcntl.LOCK_UN)
        fh.close()
