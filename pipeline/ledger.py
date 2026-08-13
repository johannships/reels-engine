#!/usr/bin/env python3
"""Content ledger — the single source of truth for "have we covered this?".

Wraps the two dedupe stores every picker already consults:
  used-repos.json   exact repo keys  ("owner/name" or bare name)
  used-topics.json  topic tokens     (vendor words, capitalized terms)

Manual entries (things the owner posted manually) go through add(); the dashboard
and CLI both use this module.

CLI:
  python3 ledger.py list
  python3 ledger.py add meetily                # marks repo-ish key + token
  python3 ledger.py add "gemini 3.5 leak" --type topic
  python3 ledger.py remove meetily
"""
import argparse, datetime, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
from configlib import load_config
CFG = load_config(HERE)
EPISODES = os.environ.get("REELS_EPISODES_DIR") or os.path.normpath(
    os.path.join(HERE, CFG["paths"]["episodes"]))
# Tokens too generic to ever block — they are the niche itself, not a subject.
GENERIC = {"claude", "code", "ai", "openai", "google", "gemini", "gpt", "grok",
           "new", "free", "open", "source", "opensource", "model", "agent",
           "agents", "api", "app", "tool", "tools", "with", "for", "the"}

REPOS = os.path.join(EPISODES, "used-repos.json")
TOPICS = os.path.join(EPISODES, "used-topics.json")


def _load(path):
    try:
        return json.load(open(path))
    except Exception:
        return {}


def _save(path, data):
    os.makedirs(EPISODES, exist_ok=True)
    json.dump(data, open(path, "w"), indent=1)


def entries():
    """[{key, kind, date}] sorted newest first."""
    out = [{"key": k, "kind": "repo", "date": v} for k, v in _load(REPOS).items()]
    out += [{"key": k, "kind": "topic", "date": v} for k, v in _load(TOPICS).items()]
    return sorted(out, key=lambda e: e["date"], reverse=True)


def add(key, kind="both", date=None):
    """Mark content as covered. kind: repo | topic | both.
    For repos, also registers the bare name as a topic token so the topic
    engine can never pick the same subject (the Meetily lesson)."""
    date = date or datetime.date.today().isoformat()
    key = key.strip()
    if kind in ("repo", "both"):
        repos = _load(REPOS)
        repos[key] = date
        _save(REPOS, repos)
    if kind in ("topic", "both"):
        topics = _load(TOPICS)
        for tok in re.findall(r"[a-z0-9][a-z0-9.\-]{2,}", key.lower()):
            if tok not in GENERIC:
                topics[tok] = date
        _save(TOPICS, topics)
    return date


def remove(key):
    key_l = key.strip().lower()
    n = 0
    for path in (REPOS, TOPICS):
        d = _load(path)
        keep = {k: v for k, v in d.items()
                if k.lower() != key_l and key_l not in k.lower()}
        n += len(d) - len(keep)
        _save(path, keep)
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["list", "add", "remove"])
    ap.add_argument("key", nargs="?")
    ap.add_argument("--type", default="both", choices=["repo", "topic", "both"])
    ap.add_argument("--date", default=None)
    args = ap.parse_args()
    if args.action == "list":
        for e in entries():
            print(f"{e['date']}  {e['kind']:5s}  {e['key']}")
    elif args.action == "add":
        if not args.key:
            sys.exit("add needs a key")
        print("covered since", add(args.key, args.type, args.date))
    else:
        print(f"removed {remove(args.key)} entries")


if __name__ == "__main__":
    main()
