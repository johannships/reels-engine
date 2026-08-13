#!/usr/bin/env python3
"""Daily "topic of the day" — the Goldie slot, generalized beyond GitHub.

Scans the AI news cycle across sources (Hacker News front page, Reddit AI
subs, GitHub trending), clusters candidates, picks ONE topic with the
strongest cross-source momentum, and runs the full chain: deep-dive script
that owns the search keyword -> HeyGen -> assemble (QA-gated) -> Metricool
schedule +24h.

Topic selection: the LLM picks from the top-scored candidates when LLM env
is set; otherwise falls back to the highest score. Dedupe: used-topics.json
(14-day window on keyword tokens).

Usage: python3 topics.py [--date YYYY-MM-DD] [--dry-run]  (dry-run: research only)
"""
import argparse, datetime, json, os, re, subprocess, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import research as R          # noqa: E402
from ledger import GENERIC    # noqa: E402
from watch import notify      # noqa: E402
from heygen import env        # noqa: E402
from scriptgen import call_llm  # noqa: E402

from configlib import load_config
CFG = load_config(HERE)
EPISODES = os.environ.get("REELS_EPISODES_DIR") or os.path.normpath(
    os.path.join(HERE, CFG["paths"]["episodes"]))
TCFG = CFG.get("topics", {})
USED_TOPICS = os.path.join(EPISODES, "used-topics.json")

VENDOR_WORDS = TCFG.get("extraKeywords", [
    "gemini", "openai", "gpt", "claude", "anthropic", "deepseek", "qwen",
    "llama", "mistral", "grok", "notebooklm", "copilot", "cursor", "codex",
    "midjourney", "runway", "elevenlabs", "heygen", "nvidia", "kimi", "glm",
])


def fetch_json(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
        "Accept": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def rss_candidates():
    """AI news feeds (TechCrunch/Verge/VentureBeat) — the Herk/Saraev topic
    pool: model releases, product launches, drama. No engagement metric, so
    they get a solid base score and live or die by cross-source boost +
    the LLM pick."""
    import email.utils, xml.etree.ElementTree as ET
    out = []
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=36)
    for feed in TCFG.get("feeds", []):
        try:
            req = urllib.request.Request(feed, headers={"User-Agent": "Mozilla/5.0"})
            root = ET.fromstring(urllib.request.urlopen(req, timeout=30).read())
            ATOM = "{http://www.w3.org/2005/Atom}"
            entries = list(root.iter("item")) + list(root.iter(f"{ATOM}entry"))
            for item in entries:
                title = (item.findtext("title") or item.findtext(f"{ATOM}title") or "").strip()
                link = (item.findtext("link") or "").strip()
                if not link:
                    ln = item.find(f"{ATOM}link")
                    link = ln.get("href", "") if ln is not None else ""
                pub = item.findtext("pubDate")
                atom_pub = item.findtext(f"{ATOM}published") or item.findtext(f"{ATOM}updated")
                try:
                    if pub and email.utils.parsedate_to_datetime(pub) < cutoff:
                        continue
                    if atom_pub and datetime.datetime.fromisoformat(
                            atom_pub.replace("Z", "+00:00")) < cutoff:
                        continue
                except Exception:
                    pass
                if title:
                    src = feed.split("/")[2].replace("www.", "").split(".")[0].title()
                    out.append({"title": title, "score": 220, "source": src,
                                "statLabel": f"breaking on {src}", "url": link,
                                "prefiltered": True})
        except Exception as e:
            print(f"rss {feed.split('/')[2]} failed:", str(e)[:60])
    return out


def hn_launch_candidates():
    """High-point AI stories from the last 24h (beyond the front page) —
    catches launches/releases the front page already rotated out."""
    out = []
    try:
        import time as _t
        since = int(_t.time()) - 86400
        nf = urllib.parse.quote(f"points>150,created_at_i>{since}", safe=",")
        d = fetch_json("https://hn.algolia.com/api/v1/search?query=AI&tags=story"
                       f"&numericFilters={nf}&hitsPerPage=20")
        for h in d.get("hits", []):
            out.append({"title": h["title"], "score": h.get("points") or 0,
                        "source": "Hacker News", "statLabel": "points on Hacker News",
                        "url": h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}"})
    except Exception as e:
        print("hn launch failed:", e)
    return out


def hn_candidates():
    out = []
    try:
        d = fetch_json("https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=30")
        for h in d.get("hits", []):
            out.append({"title": h["title"], "score": h.get("points") or 0,
                        "source": "Hacker News", "statLabel": "points on Hacker News",
                        "url": h.get("url") or f"https://news.ycombinator.com/item?id={h['objectID']}"})
    except Exception as e:
        print("hn failed:", e)
    return out


def reddit_candidates():
    out = []
    for sub in TCFG.get("subreddits", ["LocalLLaMA", "OpenAI", "ClaudeAI", "singularity"]):
        try:
            d = fetch_json(f"https://www.reddit.com/r/{sub}/top.json?t=day&limit=15")
            for c in d["data"]["children"]:
                p = c["data"]
                out.append({"title": p["title"], "score": p.get("score") or 0,
                            "source": f"r/{sub}", "statLabel": f"upvotes on r/{sub}",
                            "url": "https://reddit.com" + p.get("permalink", "")})
        except Exception as e:
            print(f"reddit {sub} failed:", e)
    return out


def github_candidates():
    # Complementary signal only: repos already covered (or destined for the
    # repo series) are excluded, and GitHub is down-weighted so news beats
    # repos in this slot — repo content has its own daily show.
    out = []
    try:
        used = R.load_used()
        for c in R.trending():
            if R.is_ai(c) and c["repo"] not in used:
                out.append({"title": f"{c['repo']}: {c['desc']}", "score": c["today"] // 4,
                            "source": "GitHub trending", "statLabel": "stars today on GitHub",
                            "url": f"https://github.com/{c['repo']}"})
    except Exception as e:
        print("github failed:", e)
    return out


def is_ai_topic(title):
    t = title.lower()
    kw = CFG["research"]["keywords"] + VENDOR_WORDS
    return any(re.search(r"\b" + re.escape(k) + r"\b", t) for k in kw)


def tokens(title):
    return {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9.\-]{2,}", title)
            if w.lower() in VENDOR_WORDS or w[0].isupper()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--menu", type=int, default=0,
                    help="print the top N candidate topics as a menu (no generation) and save menu.json")
    ap.add_argument("--from-menu", type=int, default=-1,
                    help="create the episode from menu.json entry N (1-based)")
    args = ap.parse_args()

    if args.from_menu > 0:
        menu = json.load(open(os.path.join(EPISODES, "menu.json")))
        pick = menu["candidates"][args.from_menu - 1]
        name = pick.get("topicName") or pick["title"][:40]
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:32]
        ep = f"{args.date}-topic-{slug}"
        epdir = os.path.join(EPISODES, ep)
        os.makedirs(epdir, exist_ok=True)
        json.dump({"date": args.date, "mode": "topic",
                   "picks": [{"name": name,
                              "keyword": pick.get("keyword", name.lower()),
                              "headline": pick["title"], "url": pick["url"],
                              "stats": ([{"value": pick["score"],
                                          "label": pick["statLabel"],
                                          "pill": f"hot on {pick['source']}"}]
                                        if not pick.get("prefiltered") else []),
                              "sources": []}]},
                  open(os.path.join(epdir, "research.json"), "w"), indent=1)
        used = json.load(open(USED_TOPICS)) if os.path.exists(USED_TOPICS) else {}
        for t in tokens(pick["title"]):
            used[t] = args.date
        json.dump(used, open(USED_TOPICS, "w"), indent=1)
        subprocess.run([sys.executable, os.path.join(HERE, "screenshot.py"),
                        pick["url"], os.path.join(epdir, "shot.jpg"),
                        os.path.join(epdir, "shot2.jpg")], check=False, timeout=150)
        subprocess.run([sys.executable, os.path.join(HERE, "scriptgen.py"), ep],
                       check=True)
        print(f"episode ready: {ep}")
        return

    used = json.load(open(USED_TOPICS)) if os.path.exists(USED_TOPICS) else {}
    cutoff = (datetime.date.fromisoformat(args.date)
              - datetime.timedelta(days=TCFG.get("noRepeatDays", 14))).isoformat()
    used_tokens = {t for t, day in used.items() if day >= cutoff} - GENERIC

    cands = [c for c in hn_candidates() + hn_launch_candidates() + rss_candidates()
             + reddit_candidates() + github_candidates()[:3]
             if (c.get("prefiltered") or is_ai_topic(c["title"]))
             and not (tokens(c["title"]) & used_tokens)]
    by_src = {}
    for c in cands:
        by_src[c["source"]] = by_src.get(c["source"], 0) + 1
    print("candidates by source:", by_src)
    if not cands:
        raise SystemExit("no fresh AI topics today")

    # cross-source boost: same vendor token appearing in multiple sources
    tok_sources = {}
    for c in cands:
        for t in tokens(c["title"]) & set(VENDOR_WORDS):
            tok_sources.setdefault(t, set()).add(c["source"])
    for c in cands:
        boost = max([len(tok_sources.get(t, ())) for t in tokens(c["title"])
                     & set(VENDOR_WORDS)] or [1])
        c["adj"] = c["score"] * boost
        # ecosystem niching (Nate Herk lesson): boost the keywords our
        # audience already engages with
        if any(k in c["title"].lower() for k in TCFG.get("priorityKeywords", [])):
            c["adj"] *= 1.5
    cands.sort(key=lambda c: -c["adj"])
    top = cands[:15]

    if args.menu:
        n = min(args.menu, len(top))
        json.dump({"date": args.date, "candidates": top[:n]},
                  open(os.path.join(EPISODES, "menu.json"), "w"), indent=1)
        for i, c in enumerate(top[:n], 1):
            metric = "" if c.get("prefiltered") else f"  [{c['score']} {c['statLabel']}]"
            print(f"{i}. {c['title'][:100]}  ({c['source']}){metric}")
        return

    pick = top[0]
    topic_name, keyword = None, None
    if env("LLM_API_KEY"):
        try:
            sel = call_llm(
                "Pick the ONE topic below that would STOP A FOUNDER'S SCROLL. "
                "Score each candidate on: (1) drama/stakes — deaths, leaks, "
                "price collapses, admissions, bans beat announcements; (2) a "
                "recognizable NAME in it (Google, OpenAI, Amazon, Claude...); "
                "(3) a money angle an operator can act on THIS WEEK; (4) "
                "specificity — a concrete event beats a trend piece. Corporate "
                "PR and funding rounds are boring unless the number is shocking. "
                "NEWS beats GitHub repos (repos have their own daily show) — "
                "only pick a repo if it is truly the biggest story today. "
                "Return ONLY JSON: "
                '{"index": <0-based index>, "topicName": "<display name, e.g. '
                'Gemini 3.5 Pro>", "keyword": "<the exact search phrase to own>"}'
                "\n\nCandidates:\n" + json.dumps(
                    [{"i": i, "title": c["title"], "score": c["score"],
                      "source": c["source"]} for i, c in enumerate(top)], indent=1))
            pick = top[int(sel["index"])]
            topic_name, keyword = sel["topicName"], sel["keyword"]
        except Exception as e:
            print("LLM topic pick failed, using top score:", e)
    if not topic_name:
        vendors = sorted(tokens(pick["title"]) & set(VENDOR_WORDS))
        if vendors:
            topic_name = " ".join(v.upper() if len(v) <= 4 else v.title()
                                  for v in vendors)[:40]
        else:
            topic_name = re.sub(r"^[a-z0-9_.\-]+/", "", pick["title"]).split(":")[0][:40]
        keyword = topic_name

    related = [c for c in cands if tokens(c["title"]) & tokens(pick["title"])][:4]
    # Only REAL engagement numbers may appear on screen / in scripts. RSS
    # feeds have no metric (their score is our internal ranking weight) —
    # never present it as a fact.
    def real_metric(c):
        return not c.get("prefiltered")
    stats = [{"value": c["score"], "label": c["statLabel"],
              "pill": f"hot on {c['source']}"}
             for c in ([pick] + [r for r in related if r is not pick])[:4]
             if real_metric(c)][:2]

    slug = re.sub(r"[^a-z0-9]+", "-", topic_name.lower()).strip("-")[:32]
    ep = f"{args.date}-topic-{slug}"
    epdir = os.path.join(EPISODES, ep)
    os.makedirs(epdir, exist_ok=True)
    json.dump({"date": args.date, "mode": "topic",
               "picks": [{"name": topic_name, "keyword": keyword,
                          "headline": pick["title"], "url": pick["url"],
                          "stats": stats,
                          "sources": [{"title": c["title"], "source": c["source"],
                                       "score": c["score"]} for c in related]}]},
              open(os.path.join(epdir, "research.json"), "w"), indent=1)
    print(f"topic of the day: {topic_name}  (keyword: {keyword})")
    print(f"  headline: {pick['title']}  [{pick['source']}, {pick['score']}]")

    for t in tokens(pick["title"]):
        used[t] = args.date
    json.dump(used, open(USED_TOPICS, "w"), indent=1)

    if args.dry_run:
        print(f"dry-run: research written to {epdir}")
        return

    def step(script, *a):
        subprocess.run([sys.executable, os.path.join(HERE, script), ep, *a], check=True)

    try:
        # best-effort screenshot of the source page (ShotPanel beat 2)
        shot_urls = [pick["url"]] + [s2["url"] for s2 in related
                                     if s2 is not pick and s2.get("url")][:2]
        for su in shot_urls:
            r = subprocess.run([sys.executable, os.path.join(HERE, "screenshot.py"),
                                su, os.path.join(epdir, "shot.jpg"),
                                os.path.join(epdir, "shot2.jpg")],
                               check=False, timeout=150)
            if r.returncode == 0:
                break
        step("scriptgen.py")
        if CFG.get("posting", {}).get("generation") == "propose":
            import approvals
            approvals.request_generation(ep)
            return
        if not env("HEYGEN_API_KEY"):
            notify("Topic of the day", f"Script ready for {ep} (record clip manually).")
            return
        step("heygen.py")
        step("prep.py")  # QA-gated
        if CFG.get("posting", {}).get("mode") == "approval":
            import approvals
            approvals.request(ep)
        elif env("METRICOOL_USER_TOKEN"):
            delay = CFG.get("posting", {}).get("dailyDelayHours", 24)
            step("metricool.py", "--in-hours", str(delay))
            notify("Topic of the day", f"{ep} passed QA, scheduled +{delay}h.")
        else:
            notify("Topic of the day", f"{ep} passed QA (no Metricool creds).")
    except subprocess.CalledProcessError as e:
        failed = os.path.basename(str(e.cmd[1])) if len(e.cmd) > 1 else e.cmd
        notify("Topic FAILED", f"{ep} stopped at {failed}. Nothing posted.")
        raise


if __name__ == "__main__":
    main()
