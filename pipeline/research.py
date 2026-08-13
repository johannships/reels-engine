#!/usr/bin/env python3
"""Repo Radar research: pick today's 3 hottest AI repos from GitHub trending.

- Scrapes github.com/trending (daily), filters to AI-ish repos by keyword.
- Verifies name/stars/description via the GitHub API.
- Dedupes against episodes/used-repos.json (no repeats within noRepeatDays).
- Writes episodes/<date>-<series>/research.json

Usage: python3 research.py [--date YYYY-MM-DD]
"""
import argparse, datetime, html, json, os, re, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
from configlib import load_config
CFG = load_config(HERE)
EPISODES = os.environ.get("REELS_EPISODES_DIR") or os.path.normpath(
    os.path.join(HERE, CFG["paths"]["episodes"]))
USED_PATH = os.path.join(EPISODES, "used-repos.json")


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (reels-engine research)",
        "Accept": "application/vnd.github+json" if "api.github" in url else "text/html",
    })
    return urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")


def trending():
    h = fetch("https://github.com/trending?since=daily")
    out = []
    for art in re.findall(r'<article class="Box-row">(.*?)</article>', h, re.S):
        m = re.search(r'href="/(?:login\?return_to=%2F)?([^"%]+%2F[^"]+|[^"]+/[^"]+)"', art)
        if not m:
            continue
        repo = urllib.parse.unquote(m.group(1)).strip("/")
        if repo.startswith(("sponsors/", "login", "features/")) or repo.count("/") != 1:
            # sponsor rows hide the repo link; recover it from the h2 anchor
            m2 = re.search(r'<h2[^>]*>.*?href="/([^"]+)"', art, re.S)
            repo = m2.group(1).strip("/") if m2 else None
        if not repo or repo.count("/") != 1:
            continue
        d = re.search(r'<p class="col-9[^"]*">\s*(.*?)\s*</p>', art, re.S)
        desc = html.unescape(re.sub(r"<[^>]+>", "", d.group(1))).strip() if d else ""
        t = re.search(r"([\d,]+) stars today", art)
        today = int(t.group(1).replace(",", "")) if t else 0
        out.append({"repo": repo, "desc": desc, "today": today})
    return out


def is_ai(item):
    text = (item["repo"] + " " + item["desc"]).lower()
    return any(re.search(r"\b" + re.escape(k) + r"\b", text) for k in CFG["research"]["keywords"])


def verify(repo):
    try:
        d = json.loads(fetch(f"https://api.github.com/repos/{repo}"))
        return {"repo": d["full_name"], "stars": d["stargazers_count"],
                "desc": (d.get("description") or "").strip(), "url": d["html_url"]}
    except Exception:
        return None


def load_used():
    if os.path.exists(USED_PATH):
        return json.load(open(USED_PATH))
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    args = ap.parse_args()

    used = load_used()
    cutoff = (datetime.date.fromisoformat(args.date)
              - datetime.timedelta(days=CFG["research"]["noRepeatDays"])).isoformat()
    recent = {r for r, day in used.items() if day >= cutoff}

    cands = [c for c in trending() if is_ai(c)
             and c["today"] >= CFG["research"]["minStarsToday"]
             and c["repo"] not in recent]
    cands.sort(key=lambda c: -c["today"])

    picks = []
    for c in cands:
        v = verify(c["repo"])
        if not v:
            continue
        v["today"] = c["today"]
        v["desc"] = v["desc"] or c["desc"]
        picks.append(v)
        if len(picks) == CFG["itemsPerReel"]:
            break

    if len(picks) < CFG["itemsPerReel"]:
        raise SystemExit(f"Only {len(picks)} eligible repos today; lower minStarsToday or add keywords.")

    epdir = os.path.join(EPISODES, f"{args.date}-{CFG['series']}")
    os.makedirs(epdir, exist_ok=True)
    out = {"date": args.date, "picks": picks}
    json.dump(out, open(os.path.join(epdir, "research.json"), "w"), indent=1)

    for p in picks:
        used[p["repo"]] = args.date
    os.makedirs(EPISODES, exist_ok=True)
    json.dump(used, open(USED_PATH, "w"), indent=1)

    print(f"episode dir: {epdir}")
    for p in picks:
        print(f"  {p['repo']}  ★{p['stars']:,}  +{p['today']:,} today — {p['desc'][:70]}")


if __name__ == "__main__":
    main()
