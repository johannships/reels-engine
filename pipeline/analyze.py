#!/usr/bin/env python3
"""Weekly feedback loop: turn performance data + your notes into concrete
script-generation rules (style-memo.md), so every new reel is tuned by the
last ones.

Data sources (best-effort, use what's configured):
  1. metrics.csv       — export from Metricool (Reports > export) into
                         pipeline/metrics.csv. Columns are auto-detected by
                         header keywords (views, likes, comments, shares,
                         watch/retention, date, title/text).
  2. YouTube retention — if yt-dlp/API creds are wired later, per-second
                         drop-off; until then, note drop-off manually in
                         feedback.log (e.g. "ep 07-04: big drop at repo 2").
  3. feedback.log      — your own one-liners. Highest priority.

Output: rewrites the "## Data-driven adjustments" section of style-memo.md
via the LLM, and prints the proposal. Nothing else changes automatically —
the memo only steers future scripts, so a bad suggestion can't wreck the
pipeline. Review the diff after each run.

Usage: python3 analyze.py
"""
import csv, json, os, re, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
from configlib import load_config
CFG = load_config(HERE)
EPISODES = os.environ.get("REELS_EPISODES_DIR") or os.path.normpath(
    os.path.join(HERE, CFG["paths"]["episodes"]))
MEMO = os.path.join(HERE, "style-memo.md")


def env(name, default=None):
    path = os.path.join(HERE, ".env")
    if os.path.exists(path) and name not in os.environ:
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    return os.environ.get(name, default)


def load_metrics():
    path = os.path.join(HERE, "metrics.csv")
    if not os.path.exists(path):
        return []
    rows = list(csv.DictReader(open(path)))
    return rows


def load_episode_meta():
    out = []
    if not os.path.isdir(EPISODES):
        return out
    for ep in sorted(os.listdir(EPISODES)):
        p = os.path.join(EPISODES, ep, "script.json")
        if os.path.exists(p):
            s = json.load(open(p))
            words = sum(len(sc["text"].split()) for sc in s["scenes"])
            out.append({"episode": ep, "date": s.get("date"),
                        "hook": s["scenes"][0]["text"],
                        "items": len([x for x in s["scenes"] if x["type"] == "repo"]),
                        "totalWords": words})
    return out


def call_llm(prompt):
    """Delegates to the shared subscription-authenticated provider in
    scriptgen (the private z.ai HTTP client here kept 429ing after that
    subscription lapsed, which crashed every Sunday analyze run)."""
    from scriptgen import call_llm_text
    return call_llm_text(prompt)


def main():
    metrics = load_metrics()
    episodes = load_episode_meta()
    feedback = ""
    fl = os.path.join(EPISODES, "feedback.log")
    if not os.path.exists(fl):
        fl = os.path.join(HERE, "feedback.log")
    if os.path.exists(fl):
        feedback = open(fl).read()

    if not metrics and not feedback:
        raise SystemExit("Nothing to analyze yet: export metrics.csv from "
                         "Metricool and/or add lines to feedback.log")

    memo = open(MEMO).read() if os.path.exists(MEMO) else "# Style memo\n"
    prompt = f"""You are the growth analyst for a daily short-form series ("Repo Radar", vertical reels: hook, 3 GitHub repos, CTA). Based on the data below, produce an UPDATED "Data-driven adjustments" list: max 6 bullet rules the scriptwriter must follow next week. Be specific and mechanical (word counts, hook patterns, ordering), never vague ("be more engaging" is banned). Keep rules that still look right, drop ones the data contradicts.

CURRENT MEMO:
{memo}

EPISODE METADATA (what we made):
{json.dumps(episodes[-14:], indent=1)}

PLATFORM METRICS (Metricool export rows):
{json.dumps(metrics[-40:], indent=1) if metrics else "(none yet)"}

HUMAN FEEDBACK LOG (highest priority, obey verbatim):
{feedback or "(none)"}

Return ONLY the markdown bullet list, no preamble."""

    proposal = call_llm(prompt).strip()
    marker = "## Data-driven adjustments"
    if marker in memo:
        memo = re.sub(rf"{marker}.*?(?=\n## |\Z)", f"{marker}\n\n{proposal}\n\n",
                      memo, flags=re.S)
    else:
        memo += f"\n{marker}\n\n{proposal}\n"
    open(MEMO, "w").write(memo)
    print("style-memo.md updated:\n")
    print(proposal)


if __name__ == "__main__":
    main()
