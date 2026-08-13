#!/usr/bin/env python3
"""Daily orchestrator — the whole episode in one run.

research -> scriptgen -> heygen (if API key set) -> prep -> notify.
Without a HeyGen key it stops after the script and pings you to record the
clip manually (semi-auto mode); run `prep.py <ep>` after dropping avatar.mp4.

Usage: python3 daily.py [--date YYYY-MM-DD]
"""
import argparse, datetime, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from watch import notify  # noqa: E402
from heygen import env    # noqa: E402  (.env loader)

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
    ep = f"{args.date}-{CFG['series']}"
    epdir = os.path.join(EPISODES, ep)

    if not os.path.exists(os.path.join(epdir, "research.json")):
        step("research.py", "--date", args.date)
    if not os.path.exists(os.path.join(epdir, "script.json")):
        step("scriptgen.py", ep)
    if (CFG.get("posting", {}).get("generation") == "propose"
            and not os.path.exists(os.path.join(epdir, "qa.json"))):
        import approvals
        approvals.request_generation(ep)
        return

    if not env("HEYGEN_API_KEY"):
        notify("Repo Radar", f"Script ready for {ep}. Record the HeyGen clip, "
               f"save as avatar.mp4 in the episode folder, then run prep.py {ep}.")
        print(f"semi-auto mode: script at {epdir}/script.md")
        return

    try:
        if not os.path.exists(os.path.join(epdir, "avatar.mp4")):
            step("heygen.py", ep)
        if not os.path.exists(os.path.join(epdir, "qa.json")):
            step("prep.py", ep)  # includes the QA gate

        if CFG.get("posting", {}).get("mode") == "approval":
            import approvals
            approvals.request(ep)
        elif env("METRICOOL_USER_TOKEN"):
            delay = CFG.get("posting", {}).get("dailyDelayHours", 24)
            step("metricool.py", ep, "--in-hours", str(delay))
            notify("Repo Radar", f"{ep} rendered, passed QA, scheduled +{delay}h.")
        else:
            notify("Repo Radar", f"{ep} passed QA — post manually.")
    except subprocess.CalledProcessError as e:
        failed = os.path.basename(str(e.cmd[1])) if len(e.cmd) > 1 else e.cmd
        notify("Repo Radar FAILED", f"{ep} stopped at {failed}. Nothing was "
               f"posted. See qa.json / logs.")
        raise
    print(f"done: {epdir}/final.mp4")


if __name__ == "__main__":
    main()
