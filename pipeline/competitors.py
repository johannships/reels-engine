#!/usr/bin/env python3
"""Competitor track: find OUTLIER videos worth stealing the idea from.

The signal is never raw views. A big channel doing big numbers is Tuesday;
a video doing 3x ITS OWN CHANNEL'S baseline is a proven idea. The owner's
best video ever (110K, "the cure to AI slop is a 1980s flight manual") was
an idea adapted from another creator's outlier. This module industrialises
that: watch competitors, detect outliers, hand them to steal.py.

Sources:
  - YouTube: RSS feeds (public, reliable, gives real view counts). Both
    long-form and Shorts appear. Fully automated.
  - Instagram: per-reel enrichment via yt-dlp (public: caption, likes,
    comments; views are not exposed). Profile DISCOVERY needs an
    authenticated session harvested once on the owner's machine
    (`harvest-ig`, headed browser) and stored on the volume. That scraping
    runs against IG ToS; it is off unless the session file exists, paced
    like a human, and read-only.

Usage:
  python3 competitors.py scan            # scan all sources, print + save candidates
  python3 competitors.py scan --json     # machine readable
  python3 competitors.py enrich <url>    # metadata for one reel/video url
  python3 competitors.py harvest-ig      # (local Mac, headed) save IG session
State: <episodes>/competitors-state.json  (baselines, seen ids)
Out:   <episodes>/steal-candidates.json
"""
import datetime, html, json, os, re, subprocess, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from heygen import env  # noqa: E402  (.env loader)
from configlib import load_config  # noqa: E402

CFG = load_config(HERE)
EPISODES = os.environ.get("REELS_EPISODES_DIR") or os.path.normpath(
    os.path.join(HERE, CFG["paths"]["episodes"]))
STATE = os.path.join(EPISODES, "competitors-state.json")
OUT = os.path.join(EPISODES, "steal-candidates.json")

# who we watch; override/extend in config.local.json under "competitors"
DEFAULTS = {
    "youtube": {
        "Nate Herk": "UC2ojq-nuP8ceeHqiroeKhBA",
        "Nick Saraev": "UCbo-KbSjJDG6JWQ_MTZ_rNA",
        "AI Advantage": "UCHhYXsLBEVVnbvsq57n1MTQ",
        "TheAIGRID": "UCbY9xX3_jW5c2fjlZVBI4cg",
    },
    "instagram": ["benkimball.ai", "quant_kavin", "thad.codes"],
    # a video must beat its channel median by this factor to be a candidate
    "outlierRatio": 2.5,
    "minViews": 15000,
    "maxAgeDays": 21,
}
COMP = {**DEFAULTS, **CFG.get("competitors", {})}


def _load(path, default):
    try:
        return json.load(open(path))
    except Exception:
        return default


def fetch_youtube():
    """Outliers across all configured channels, scored vs each channel's own
    median. RSS carries the last ~15 uploads with live view counts."""
    now = datetime.datetime.now(datetime.timezone.utc)
    out = []
    for name, cid in COMP["youtube"].items():
        try:
            req = urllib.request.Request(
                f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}",
                headers={"User-Agent": "Mozilla/5.0"})
            x = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
        except Exception as e:
            print(f"  {name}: feed failed ({e})", file=sys.stderr)
            continue
        vids = []
        for e in re.findall(r"<entry>(.*?)</entry>", x, re.S):
            t = re.search(r"<title>(.*?)</title>", e, re.S)
            p = re.search(r"<published>(.*?)</published>", e)
            v = re.search(r'<media:statistics views="(\d+)"', e)
            i = re.search(r"<yt:videoId>(.*?)</yt:videoId>", e)
            if not (t and p and v and i):
                continue
            age = max(0.25, (now - datetime.datetime.fromisoformat(p.group(1))
                             ).total_seconds() / 86400)
            vids.append({"id": i.group(1), "title": html.unescape(t.group(1)),
                         "views": int(v.group(1)), "age_days": round(age, 1),
                         "channel": name,
                         "url": f"https://www.youtube.com/watch?v={i.group(1)}"})
        if len(vids) < 5:
            continue
        # baseline: median views of videos old enough to have settled.
        settled = sorted(v["views"] for v in vids if v["age_days"] >= 7)
        if len(settled) < 3:
            settled = sorted(v["views"] for v in vids)
        median = settled[len(settled) // 2] or 1
        for v in vids:
            v["channel_median"] = median
            v["outlier_ratio"] = round(v["views"] / median, 2)
            # young videos get velocity credit: compare views/day too
            v["views_per_day"] = int(v["views"] / v["age_days"])
        out.extend(vids)
    return out


def enrich_instagram(url):
    """Public per-reel metadata. No login, no views (IG hides them), but
    likes+comments are enough to judge an outlier when the caller knows the
    account's typical numbers."""
    try:
        r = subprocess.run(
            ["yt-dlp", "--skip-download", "--print",
             "%(uploader)s\t%(like_count)s\t%(comment_count)s\t%(description)s", url],
            capture_output=True, text=True, timeout=180)
    except Exception:
        return None
    line = (r.stdout or "").strip().splitlines()
    if not line:
        return None
    parts = line[-1].split("\t", 3)
    while len(parts) < 4:
        parts.append("")
    up, likes, comments, desc = parts

    def num(s):
        try:
            return int(s)
        except ValueError:
            return None
    return {"url": url, "uploader": up, "likes": num(likes),
            "comments": num(comments), "caption": desc[:600]}


IG_STATE_FILE = os.path.join(EPISODES, "ig-session.json")


def harvest_ig():
    """Run ON THE OWNER'S MAC (needs a display). Opens a real browser; the
    owner logs into Instagram; the session's storage state is saved. Copy the
    file to the server volume to enable authenticated discovery. AgentReach
    pattern: harvest once, run headless after."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch(headless=False,
                              executable_path=env("CHROME_BIN") or None)
        ctx = b.new_context()
        page = ctx.new_page()
        page.goto("https://www.instagram.com/accounts/login/")
        print("Log in in the browser window. Press Enter here when done.")
        input()
        ctx.storage_state(path=IG_STATE_FILE)
        b.close()
    print(f"session saved -> {IG_STATE_FILE}")


def scan():
    os.makedirs(EPISODES, exist_ok=True)
    state = _load(STATE, {"seen": {}})
    yt = fetch_youtube()
    cands = []
    for v in yt:
        if v["views"] < COMP["minViews"] or v["age_days"] > COMP["maxAgeDays"]:
            continue
        if v["outlier_ratio"] < COMP["outlierRatio"]:
            continue
        prev = state["seen"].get(v["id"], {})
        v["new"] = not prev
        cands.append(v)
        state["seen"][v["id"]] = {"ratio": v["outlier_ratio"],
                                  "at": datetime.date.today().isoformat()}
    cands.sort(key=lambda v: -v["outlier_ratio"])
    json.dump({"generated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "candidates": cands}, open(OUT, "w"), indent=1)
    json.dump(state, open(STATE, "w"), indent=1)
    return cands


if __name__ == "__main__":
    args = sys.argv[1:]
    cmd = args[0] if args else "scan"
    if cmd == "scan":
        cands = scan()
        if "--json" in args:
            print(json.dumps(cands, indent=1))
        else:
            for v in cands[:12]:
                mark = "NEW " if v.get("new") else "seen"
                print(f"  {mark} {v['outlier_ratio']:4.1f}x  {v['views']:>8,}v "
                      f"{v['age_days']:4.1f}d  [{v['channel']}] {v['title'][:60]}")
            print(f"{len(cands)} outliers -> {OUT}")
    elif cmd == "enrich" and len(args) > 1:
        print(json.dumps(enrich_instagram(args[1]), indent=1))
    elif cmd == "harvest-ig":
        harvest_ig()
    else:
        raise SystemExit(__doc__)
