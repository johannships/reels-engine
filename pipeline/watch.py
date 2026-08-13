#!/usr/bin/env python3
"""Trend watcher — run every 2 hours. Detects a breakout AI repo and preps a
single-repo "own the keyword" episode before everyone else covers it.

Breakout = AI repo on GitHub trending that we haven't covered, with either
  - stars-today >= breakout.minStarsToday, or
  - stars-today grew by >= breakout.minDelta since the last check.

On detection:
  1. creates episodes/<date>-breakout-<name>/research.json (mode=breakout)
  2. runs scriptgen.py (if LLM env is configured) so the script is waiting
  3. notifies you (macOS notification + optional webhook e.g. Cyndra Agent)
You then: record the HeyGen clip, drop it in the episode dir as avatar.mp4,
run prep.py, approve, post. Speed is the whole point.

Usage: python3 watch.py            (one check; schedule via launchd/cron)
"""
import datetime, json, os, subprocess, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import research as R  # reuse trending/is_ai/verify/load_used  # noqa: E402
from heygen import env as _env  # .env loader  # noqa: E402

from configlib import load_config
CFG = load_config(HERE)
EPISODES = os.environ.get("REELS_EPISODES_DIR") or os.path.normpath(
    os.path.join(HERE, CFG["paths"]["episodes"]))
STATE_PATH = os.path.join(EPISODES, "trend-state.json")
BK = CFG.get("breakout", {"minStarsToday": 800, "minDelta": 300, "maxPerDay": 2})


def notify(title, body):
    try:
        subprocess.run(["osascript", "-e",
                        f'display notification "{body}" with title "{title}" sound name "Glass"'],
                       check=False)
    except Exception:
        pass
    try:
        import telegram
        telegram.send_text(f"{title}\n{body}")
    except Exception as e:
        print("telegram notify failed:", e)
    hook = os.environ.get("REELS_WEBHOOK_URL")
    if hook:
        try:
            req = urllib.request.Request(hook, data=json.dumps(
                {"text": f"{title}: {body}"}).encode(),
                headers={"content-type": "application/json"})
            urllib.request.urlopen(req, timeout=15)
        except Exception as e:
            print("webhook failed:", e)


def main():
    today = datetime.date.today().isoformat()
    now = datetime.datetime.now().isoformat(timespec="minutes")
    state = json.load(open(STATE_PATH)) if os.path.exists(STATE_PATH) else {}
    used = R.load_used()

    alerted_today = [k for k, v in state.items()
                     if v.get("alertedOn", "") == today]

    breakouts = []
    for c in R.trending():
        if not R.is_ai(c) or c["repo"] in used:
            continue
        prev = state.get(c["repo"], {})
        delta = c["today"] - prev.get("lastToday", 0) if prev else 0
        hot = (c["today"] >= BK["minStarsToday"] or
               (prev and delta >= BK["minDelta"]))
        state[c["repo"]] = {"lastToday": c["today"], "lastSeen": now,
                            "alertedOn": prev.get("alertedOn", "")}
        if hot and prev.get("alertedOn", "") != today:
            breakouts.append((c, delta))

    breakouts.sort(key=lambda x: -x[0]["today"])
    room = max(0, BK["maxPerDay"] - len(alerted_today))
    for c, delta in breakouts[:room]:
        v = R.verify(c["repo"])
        if not v:
            continue
        v["today"] = c["today"]
        name = c["repo"].split("/")[-1].lower()
        ep = f"{today}-breakout-{name}"
        epdir = os.path.join(EPISODES, ep)
        os.makedirs(epdir, exist_ok=True)
        json.dump({"date": today, "mode": "breakout", "picks": [v]},
                  open(os.path.join(epdir, "research.json"), "w"), indent=1)
        state[c["repo"]]["alertedOn"] = today

        # Full-auto chain when the keys exist: script -> HeyGen -> assemble ->
        # post immediately (speed is the whole point of breakout mode).
        def step(script, *a):
            subprocess.run([sys.executable, os.path.join(HERE, script), ep, *a],
                           check=True)

        status = "detected"
        try:
            step("scriptgen.py")
            status = "script ready"
            if CFG.get("posting", {}).get("generation") == "propose":
                import approvals
                approvals.request_generation(ep)
                status = "script proposed — awaiting 'go' in Telegram"
            elif os.environ.get("HEYGEN_API_KEY") or _env("HEYGEN_API_KEY"):
                step("heygen.py")
                step("prep.py")
                status = "rendered"
                if CFG.get("posting", {}).get("mode") == "approval":
                    import approvals
                    approvals.request(ep)
                    status = "rendered — AWAITING YOUR APPROVAL in Telegram"
                elif (CFG.get("breakout", {}).get("autopost") and
                        _env("METRICOOL_USER_TOKEN")):
                    step("metricool.py", "--now")
                    status = "POSTED to all platforms"
        except subprocess.CalledProcessError as e:
            status = f"stopped at: {e.cmd[1] if len(e.cmd) > 1 else e.cmd}"

        msg = (f"{c['repo']} is breaking out: +{c['today']:,} stars today"
               f" (Δ{delta:+,} since last check). Episode {ep}: {status}.")
        print("BREAKOUT:", msg)
        notify("Repo Radar breakout", msg)

    json.dump(state, open(STATE_PATH, "w"), indent=1)
    if not breakouts:
        print(f"{now} no breakout (tracked {len(state)} repos)")


if __name__ == "__main__":
    main()
