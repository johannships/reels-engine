#!/usr/bin/env python3
"""Metricool scheduling: push an episode's final.mp4 to all platforms.

Media must be reachable by URL, so the server exposes episodes through
serve.py (or your nginx) — set REELS_PUBLIC_BASE to that base URL.

Env (pipeline/.env):
  METRICOOL_USER_TOKEN   Settings > API in Metricool (advanced plans)
  METRICOOL_USER_ID      numeric user id
  METRICOOL_BLOG_ID      numeric brand/blog id
  METRICOOL_PROVIDERS    comma list, default: tiktok,instagram,youtube,linkedin
  REELS_PUBLIC_BASE      e.g. https://reels.yourdomain.com/<token>
  TIMEZONE               default Asia/Bangkok

NOTE: Metricool's scheduler API is lightly documented; the payload below
follows their app's v2 scheduler format. On first run, verify the post looks
right in the Metricool planner. Use --dry-run to print without posting.

Usage:
  python3 metricool.py <episode> --in-hours 24        # daily: schedule ahead
  python3 metricool.py <episode> --now                # breakout: post asap
  python3 metricool.py <episode> --in-hours 24 --dry-run
"""
import argparse, datetime, json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from heygen import env  # noqa: E402  (.env loader)

from configlib import load_config
CFG = load_config(HERE)
EPISODES = os.environ.get("REELS_EPISODES_DIR") or os.path.normpath(
    os.path.join(HERE, CFG["paths"]["episodes"]))
BASE = "https://app.metricool.com/api"


def api(method, path, body=None):
    url = f"{BASE}{path}{'&' if '?' in path else '?'}userId={env('METRICOOL_USER_ID')}&blogId={env('METRICOOL_BLOG_ID')}"
    req = urllib.request.Request(
        url, method=method,
        data=json.dumps(body).encode() if body else None,
        headers={"X-Mc-Auth": env("METRICOOL_USER_TOKEN"),
                 "content-type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


def build_post(ep, social, when_iso):
    providers = [{"network": n.strip()} for n in
                 env("METRICOOL_PROVIDERS", "tiktok,instagram,youtube,linkedin").split(",")]
    media_url = f"{env('REELS_PUBLIC_BASE','').rstrip('/')}/{ep}/final.mp4"
    return {
        "providers": providers,
        "publicationDate": {"dateTime": when_iso,
                            "timezone": env("TIMEZONE", "Asia/Bangkok")},
        "text": social["caption"],
        "media": [media_url],
        "autoPublish": True,
        "draft": False,
        "shortener": False,
        "instagramData": {"type": "REEL"},
        "youtubeData": {"title": social["title"][:95], "type": "SHORT",
                        "privacy": "PUBLIC", "madeForKids": False},
        "tiktokData": {"privacyOption": "PUBLIC_TO_EVERYONE",
                       "title": social["title"][:90]},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--in-hours", type=float)
    g.add_argument("--now", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    epdir = os.path.join(EPISODES, args.episode)
    script = json.load(open(os.path.join(epdir, "script.json")))
    social = script.get("social")
    if not social:
        raise SystemExit("script.json has no social block (re-run scriptgen.py)")
    if not os.path.exists(os.path.join(epdir, "final.mp4")):
        raise SystemExit("no final.mp4 yet (run prep.py)")
    for k in ("METRICOOL_USER_TOKEN", "METRICOOL_USER_ID", "METRICOOL_BLOG_ID",
              "REELS_PUBLIC_BASE"):
        if not env(k):
            raise SystemExit(f"{k} not set in pipeline/.env")

    # SCHEDULE-ONLY GUARANTEE: this tool can never publish immediately.
    # Minimum 1 hour out — the human veto gap is structural, not a habit.
    delay = max(1.0, 1.0 if args.now else args.in_hours)
    from zoneinfo import ZoneInfo
    when = (datetime.datetime.now(ZoneInfo(env("TIMEZONE", "Asia/Bangkok")))
            + datetime.timedelta(hours=delay))
    when_iso = when.strftime("%Y-%m-%dT%H:%M:%S")
    post = build_post(args.episode, social, when_iso)

    print(f"scheduling {args.episode} at {when_iso} "
          f"({', '.join(p['network'] for p in post['providers'])})")
    if args.dry_run:
        print(json.dumps(post, indent=1))
        return
    resp = api("POST", "/v2/scheduler/posts", post)
    print("metricool response:", json.dumps(resp)[:400])
    json.dump({"scheduledFor": when_iso, "response": resp},
              open(os.path.join(epdir, "posted.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
