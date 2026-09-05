#!/usr/bin/env python3
"""Steal track: turn a competitor's OUTLIER video into an original proposal.

The owner's best video ever was an idea adapted from another creator's
viral reel: he kept the IDEA (aerospace writing standard kills AI slop),
wrote his own script, and gave away his own implementation. That is the
contract here, enforced in the prompt:

  STEAL THE IDEA. NEVER THE SCRIPT.

The output is an ORIGINAL script written for the owner's voice, audience,
and assets, plus a receipt card (what won, where, how hard) so the Telegram
approval is a 10-second decision. Default delivery is REAL FACE: if the
idea won for a human talking, the human should talk. The engine still does
research, script, captions, and the edit after he records.

Usage:
  python3 steal.py <competitor-video-or-reel-url>     # explicit steal
  python3 steal.py --top                              # best unproposed candidate
"""
import datetime, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from heygen import env  # noqa: E402
from configlib import load_config  # noqa: E402
from scriptgen import call_llm, cta_line  # noqa: E402
import competitors  # noqa: E402
import telegram  # noqa: E402

CFG = load_config(HERE)
EPISODES = os.environ.get("REELS_EPISODES_DIR") or os.path.normpath(
    os.path.join(HERE, CFG["paths"]["episodes"]))

# assets the adaptation can give away (his real, live repos)
ASSETS = CFG.get("assets", [
    {"name": "simplified-technical-english",
     "what": "Claude skill: kills AI slop with the ASD-STE100 flight-manual standard",
     "keyword": "GITHUB"},
    {"name": "llm-council",
     "what": "Claude skill: 5 sub-agents argue with your idea instead of agreeing",
     "keyword": "COUNCIL"},
    {"name": "content-research-team",
     "what": "3 Claude skills: signal-scout, content-strategist, brief-builder",
     "keyword": "CONTENT"},
    {"name": "reels-engine",
     "what": "the open-source automated reels pipeline itself (1.5M impressions)",
     "keyword": "SYSTEM"},
])

_I = CFG.get("identity", {})


def transcript_of(url):
    """Best-effort: download the video's audio and transcribe locally so the
    idea extraction sees what was actually said, not just the caption."""
    import tempfile
    model = os.environ.get("WHISPER_MODEL", "/models/ggml-small.en.bin")
    if not os.path.exists(model):
        return ""
    with tempfile.TemporaryDirectory() as td:
        mp4 = os.path.join(td, "v.mp4")
        try:
            subprocess.run(["yt-dlp", "-f", "best", "-o", mp4, url],
                           capture_output=True, text=True, timeout=300)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return ""
        if not os.path.exists(mp4):
            return ""
        wav = os.path.join(td, "a.wav")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp4, "-ar", "16000",
                        "-ac", "1", "-c:a", "pcm_s16le", wav], timeout=180)
        out = os.path.join(td, "t")
        subprocess.run(["whisper-cli", "-m", model, "-f", wav, "-np", "-nt",
                        "-of", out, "-otxt"], capture_output=True, timeout=600)
        try:
            return open(out + ".txt").read().strip()[:1600]
        except Exception:
            return ""


def propose(source):
    """source: dict with url + whatever receipt data we have."""
    meta = competitors.enrich_instagram(source["url"]) \
        if "instagram.com" in source["url"] else None
    tx = transcript_of(source["url"])

    receipt = {k: source.get(k) for k in
               ("title", "channel", "views", "outlier_ratio", "channel_median",
                "views_per_day", "age_days") if source.get(k) is not None}
    if meta:
        receipt.update({k: meta[k] for k in ("uploader", "likes", "comments")
                        if meta.get(k) is not None})
        source.setdefault("title", (meta.get("caption") or "")[:80])

    prompt = f"""A competitor's video OUTPERFORMED. Your job: extract the transferable
IDEA and design an ORIGINAL adaptation for this creator. You are adapting
the idea the way every top creator does. Hard rules:
- STEAL THE IDEA, NEVER THE SCRIPT. Do not reuse their sentences, their
  examples in the same order, or their exact framing. Write from zero.
- If their idea rests on an asset (a repo, a tool, a method), the adaptation
  must use one of THIS creator's own assets or a public resource he can
  legitimately point at, never their asset.

THE CREATOR you write for: {_I.get('name','the creator')}, {_I.get('positioning','')}.
Audience: {_I.get('audience','founders/operators')}. His proven register: direct,
receipts over adjectives, contrarian-insider, free-asset giveaways with a
one-word comment CTA. His best video (110K views) adapted someone else's
viral idea with an original script and his own asset. Sentence lengths vary;
max 20 words; no em dashes; numbers as digits.

HIS AVAILABLE GIVEAWAY ASSETS:
{json.dumps(ASSETS, indent=1)}

THE COMPETITOR VIDEO:
url: {source['url']}
receipt: {json.dumps(receipt, indent=1)}
caption: {(meta or {}).get('caption','(none)')}
transcript (what they actually said): {tx or '(unavailable)'}

Return ONLY JSON:
{{
 "idea": "<the transferable idea in one sentence, creator-independent>",
 "why_it_won": "<the mechanism: curiosity engine, formula, emotion. 1-2 sentences>",
 "fit": "<why it fits THIS creator's audience and funnel, or honest reasons it does not>",
 "fit_score": <1-10>,
 "delivery": "real-face" or "clone",
 "asset": "<which of his assets to give away, or 'none'>",
 "keyword": "<the comment keyword>",
 "hook_options": ["<3 original hooks, best first, 10-word rule>"],
 "script": "<the full ORIGINAL spoken script, 90-120 words, scene breaks as blank lines>",
 "title": "<YouTube/IG title, max 60 chars>",
 "truth_check": "<if the script narrates any specific event/anecdote that has
   not verifiably happened, name it here and say what the creator must DO
   before recording so it is true. Else 'clean'>"
}}"""

    out = call_llm(prompt)

    # de-slop the adaptation like every other script
    try:
        import ste_lint
        fields = {"hook": (out.get("hook_options") or [""])[0],
                  "beats": [b for b in re.split(r"\n\s*\n", out.get("script", "")) if b.strip()]}
        body, n_err, _ = ste_lint.report(ste_lint.lint_script(fields))
        if n_err:
            print(f"[steal] lint: {n_err} errors\n{body}", flush=True)
    except Exception:
        pass

    slug = re.sub(r"[^a-z0-9]+", "-", (out.get("title") or "steal").lower()).strip("-")[:32]
    ep = f"{datetime.date.today().isoformat()}-steal-{slug}"
    epdir = os.path.join(EPISODES, ep)
    os.makedirs(epdir, exist_ok=True)
    json.dump({"mode": "steal", "source": source, "receipt": receipt,
               "proposal": out}, open(os.path.join(epdir, "steal.json"), "w"), indent=1)
    with open(os.path.join(epdir, "script.md"), "w") as f:
        f.write(f"# STEAL: {out.get('title','')}\n\nsource: {source['url']}\n\n"
                + out.get("script", ""))

    ratio = receipt.get("outlier_ratio")
    stat = (f"{receipt.get('views'):,}v, {ratio}x their median" if ratio
            else f"{receipt.get('likes','?')} likes")
    delivery = out.get("delivery", "real-face")
    telegram.send_text(
        f"🎯 STEAL CANDIDATE — {ep}\n"
        f"WHAT WON: {receipt.get('title', source['url'])[:80]}\n"
        f"   [{receipt.get('channel', receipt.get('uploader','?'))}] {stat}\n"
        f"IDEA: {out.get('idea','')}\n"
        f"WHY IT WON: {out.get('why_it_won','')}\n"
        f"FIT: {out.get('fit_score','?')}/10 — {out.get('fit','')[:160]}\n"
        f"DELIVERY: {delivery.upper()}"
        + ("  (you record, engine edits)" if delivery == "real-face" else "")
        + f"\nASSET: {out.get('asset','none')}  CTA: comment {out.get('keyword','')}\n\n"
        + (f"⚠️ BEFORE RECORDING: {out['truth_check']}\n"
           if out.get('truth_check') and out.get('truth_check') != 'clean' else "")
        + f"HOOK: {(out.get('hook_options') or [''])[0]}\n\n"
        f"SCRIPT:\n{out.get('script','')[:900]}\n\n"
        f"source: {source['url']}")
    print(f"proposed {ep} (fit {out.get('fit_score')}/10, {delivery})")
    return ep


def main():
    if len(sys.argv) > 1 and sys.argv[1] != "--top":
        return propose({"url": sys.argv[1]})
    cands = competitors.scan()
    state_path = os.path.join(EPISODES, "steal-proposed.json")
    proposed = set()
    try:
        proposed = set(json.load(open(state_path)))
    except Exception:
        pass
    fresh = [c for c in cands if c["id"] not in proposed]
    if not fresh:
        print("no unproposed outliers today")
        return
    ep = propose(fresh[0])
    proposed.add(fresh[0]["id"])
    json.dump(sorted(proposed), open(state_path, "w"), indent=1)
    return ep


if __name__ == "__main__":
    main()
