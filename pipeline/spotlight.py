#!/usr/bin/env python3
"""Daily series #2: single-repo Spotlight (the Goldie slot).

Picks the hottest unused AI repo from trending and runs the full chain with a
challenger/free/open-source title angle, scheduled +24h like the daily show
but at a different time-of-day (cron decides when this runs).

Usage: python3 spotlight.py [--date YYYY-MM-DD]
"""
import argparse, datetime, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import research as R  # noqa: E402
from watch import notify  # noqa: E402
from heygen import env    # noqa: E402

from configlib import load_config
CFG = load_config(HERE)
EPISODES = os.environ.get("REELS_EPISODES_DIR") or os.path.normpath(
    os.path.join(HERE, CFG["paths"]["episodes"]))


def step(script, *args):
    subprocess.run([sys.executable, os.path.join(HERE, script), *args], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    args = ap.parse_args()

    used = R.load_used()
    cands = [c for c in R.trending() if R.is_ai(c) and c["repo"] not in used]
    cands.sort(key=lambda c: -c["today"])
    if not cands:
        print("no unused AI repo trending today; skipping spotlight")
        return
    pick = R.verify(cands[0]["repo"])
    if not pick:
        raise SystemExit(f"could not verify {cands[0]['repo']}")
    pick["today"] = cands[0]["today"]

    name = pick["repo"].split("/")[-1].lower()
    ep = f"{args.date}-spotlight-{name}"
    epdir = os.path.join(EPISODES, ep)
    os.makedirs(epdir, exist_ok=True)
    json.dump({"date": args.date, "mode": "breakout", "picks": [pick]},
              open(os.path.join(epdir, "research.json"), "w"), indent=1)
    used[pick["repo"]] = args.date
    json.dump(used, open(R.USED_PATH, "w"), indent=1)

    try:
        step("scriptgen.py", ep)
        if not env("HEYGEN_API_KEY"):
            notify("Spotlight", f"Script ready for {ep} (record clip manually).")
            return
        step("heygen.py", ep)
        step("prep.py", ep)  # includes the QA gate
        if CFG.get("posting", {}).get("mode") == "approval":
            import approvals
            approvals.request(ep)
        elif env("METRICOOL_USER_TOKEN"):
            delay = CFG.get("posting", {}).get("dailyDelayHours", 24)
            step("metricool.py", ep, "--in-hours", str(delay))
            notify("Spotlight", f"{ep} passed QA, scheduled +{delay}h.")
        else:
            notify("Spotlight", f"{ep} passed QA (no Metricool creds).")
    except subprocess.CalledProcessError as e:
        failed = os.path.basename(str(e.cmd[1])) if len(e.cmd) > 1 else e.cmd
        notify("Spotlight FAILED", f"{ep} stopped at {failed}. Nothing posted.")
        raise


if __name__ == "__main__":
    main()
