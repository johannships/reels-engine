#!/usr/bin/env python3
"""Railway worker: one process, one volume, everything scheduled internally.

Runs:
  - serve.py handler in a thread (media URLs for Metricool)
  - topics.py    daily at TOPIC_HOUR (default 06) — topic-of-the-day deep dive
  - daily.py     daily at DAILY_HOUR (default 13) — 3-repo Repo Radar
  - watch.py     every WATCH_EVERY_HOURS (default 2) — breakout newsjacking
  - analyze.py   Sundays at 18
  (spotlight.py exists for manual/extra slots, not scheduled)

State (last-run stamps) persists in the episodes dir so redeploys don't
double-run. Times are in TIMEZONE (default Asia/Bangkok).

Start command: python3 pipeline/worker.py
"""
import datetime, json, os, subprocess, sys, threading, time
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from heygen import env  # noqa: E402

from configlib import load_config
CFG = load_config(HERE)
EPISODES = os.environ.get("REELS_EPISODES_DIR") or os.path.normpath(
    os.path.join(HERE, CFG["paths"]["episodes"]))
os.makedirs(EPISODES, exist_ok=True)
STATE = os.path.join(EPISODES, "worker-state.json")
TZ = ZoneInfo(env("TIMEZONE", "Asia/Bangkok"))


def run(script):
    print(f"[worker] running {script}", flush=True)
    try:
        subprocess.run([sys.executable, os.path.join(HERE, script)],
                       check=True, timeout=3600)
    except Exception as e:
        print(f"[worker] {script} failed: {e}", flush=True)


def serve_thread():
    if not env("REELS_SERVE_TOKEN"):
        print("[worker] REELS_SERVE_TOKEN unset — media server disabled", flush=True)
        return
    import serve  # noqa: F401  (its __main__ guard won't fire)
    import http.server
    port = int(env("REELS_SERVE_PORT", env("PORT", "8737")))
    httpd = http.server.ThreadingHTTPServer(("0.0.0.0", port), serve.Handler)
    print(f"[worker] media server on :{port}", flush=True)
    httpd.serve_forever()


def main():
    threading.Thread(target=serve_thread, daemon=True).start()
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    topic_h = int(env("TOPIC_HOUR", "6"))
    daily_h = int(env("DAILY_HOUR", "13"))
    watch_every = int(env("WATCH_EVERY_HOURS", "2"))

    while True:
        now = datetime.datetime.now(TZ)
        today = now.date().isoformat()

        if now.hour >= topic_h and state.get("topic") != today:
            state["topic"] = today
            json.dump(state, open(STATE, "w"))
            run("topics.py")
        if now.hour >= daily_h and state.get("daily") != today:
            state["daily"] = today
            json.dump(state, open(STATE, "w"))
            run("daily.py")
        last_watch = state.get("watch", 0)
        if time.time() - last_watch >= watch_every * 3600:
            state["watch"] = time.time()
            json.dump(state, open(STATE, "w"))
            run("watch.py")
        try:
            import approvals
            approvals.handle_commands()
        except Exception as e:
            print("[worker] approvals poll failed:", e, flush=True)
        if (now.weekday() == 6 and now.hour >= 18
                and state.get("analyze") != today):
            state["analyze"] = today
            json.dump(state, open(STATE, "w"))
            run("analyze.py")

        time.sleep(60)


if __name__ == "__main__":
    main()
