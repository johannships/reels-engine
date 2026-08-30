#!/usr/bin/env python3
"""Generate the day's reel script from research.json.

Default provider is the Claude Code CLI in headless mode, authenticated by a
subscription OAuth token — no per-token API billing. Models are tried in order
(default: fable for the writing, opus as fallback).

Env (put in pipeline/.env or export):
  LLM_PROVIDER   "claude-cli" (default) | "http"
  --- claude-cli ---
  CLAUDE_CODE_OAUTH_TOKEN  from `claude setup-token` (required)
  LLM_MODELS     comma-separated fallback chain, default "fable,opus"
  CLAUDE_BIN     path to the claude binary, default "claude"
  LLM_TIMEOUT_SEC per-model timeout, default 180
  WARNING: never set ANTHROPIC_API_KEY here — it outranks the OAuth token and
  would switch this pipeline to paid per-token billing.
  --- http (legacy: z.ai / Anthropic API) ---
  LLM_BASE_URL   default https://api.z.ai/api/anthropic
  LLM_API_KEY    provider token
  LLM_MODEL      e.g. glm-4.7

Reads:  episodes/<ep>/research.json, style-memo.md, feedback.log, config.json
Writes: episodes/<ep>/script.json (scenes for the renderer)
        episodes/<ep>/script.md   (paste into HeyGen)

Usage: python3 scriptgen.py <episode-dir-name>
"""
import json, os, re, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
from configlib import load_config
CFG = load_config(HERE)
EPISODES = os.environ.get("REELS_EPISODES_DIR") or os.path.normpath(
    os.path.join(HERE, CFG["paths"]["episodes"]))
_I = CFG.get("identity", {})
IDENT = f"{_I.get('name', 'the creator')} ({_I.get('handle', '')}), {_I.get('positioning', 'a creator in the AI niche')}"


def env(name, default=None):
    # .env loader (no dependency): KEY=VALUE lines
    path = os.path.join(HERE, ".env")
    if os.path.exists(path) and name not in os.environ:
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    return os.environ.get(name, default)


def read_if(path):
    return open(path).read() if os.path.exists(path) else ""


def title_rules():
    """Two title schools, A/B-able via config posting.titleStyle.
    'goldie' = the formulas reverse-engineered from Julian Goldie's top shorts
    (see GOLDIE-NOTES.md); 'operator' = same structure, receipts wording."""
    style = CFG.get("posting", {}).get("titleStyle", "operator")
    if style == "goldie":
        return ('- "title": max 90 chars, MUST contain the main repo/tool name '
                '(people search it within hours). Use one of these proven formulas: '
                '"NEW {name} is INSANE!", "{challenger} DESTROYS {incumbent}?", '
                '"This NEW {category} is INSANE! (FREE + Open Source)", '
                '"{name} Just Changed {category} Forever". Prefer the DESTROYS '
                'challenger formula when the repo rivals a big incumbent; append '
                '"(FREE + Open Source)" whenever it is true.')
    return ('- "title": max 60 chars, Title Case (never ALL CAPS), MUST contain '
            'the main tool/topic name. Benefit-driven and SPECIFIC: "How to X", '
            '"Free Way to X", a number, or a claim that makes people ask HOW. '
            'Good: "How I Cut My Dev Costs by 95%", "Free AI Meeting Notes That '
            'Run Locally". BAD (generic AI fluff, instant scroll): "Master the '
            'Top AI Hack Unveiled!", anything with Unveiled/Ultimate/Master.')




HOOK_CRAFT = """HOOK DOCTRINE (scene 1 lives or dies on the FIRST THREE WORDS):
- The first 3 words must contain one of: you/your (the viewer's stake), a
  recognizable brand or product name, an imperative (Stop / Steal / Delete),
  or "I" plus a money number ("I cut my two thousand dollar...").
- The hook states what the VIEWER gains or loses, never what happened in the
  news. "Your AI bill is forty percent too high" beats "X just launched".
- BANNED in scene 1: "just dropped", "just launched", "just changed",
  "just went", "nobody's talking about", "blowing up right now", greetings,
  rhetorical questions, and ALL insider metrics (GitHub stars, Hacker News
  points, upvotes).
- Numbers in the hook: only a money or outcome number the viewer can feel.
  If the only available numbers are small or insider, use none at all.
- Internally draft 5 candidate hooks, judge each by its first three words,
  and output ONLY the winner as scene 1.
Proven hooks from this exact channel (match the energy, never copy):
"These 3 skills replace my 2,000 dollar a month content team." /
"The best engineers aren't on LinkedIn." / "Stop building AI agents." /
"These 3 AI tools get your business leads on autopilot."
"""

def cta_line(idx=0):
    """The spoken CTA, resolved against the channel funnel. ctaRotation entries
    may carry {keyword}/{magnet} placeholders so committed config stays neutral
    while the real keyword lives in config.local.json. A follow-CTA earns
    nothing; the comment keyword feeds ManyChat -> email -> community."""
    f = CFG.get("funnel", {})
    rot = CFG["script"]["ctaRotation"]
    line = rot[idx % len(rot)]
    # magnet is written copy (may carry parentheticals); the CTA is SPOKEN.
    # Prefer an explicit funnel.magnetSpoken, else strip parentheticals and
    # clamp to something a voice can land in one breath.
    spoken = f.get("magnetSpoken")
    if not spoken:
        spoken = re.sub(r"\s*\([^)]*\)", "", f.get("magnet", "the full breakdown"))
        spoken = " ".join(spoken.split()[:9]).rstrip(",.")
    return (line.replace("{keyword}", f.get("commentKeyword", "SYSTEM"))
                .replace("{magnet}", spoken))

def build_prompt(research):
    s = CFG["script"]
    picks = research["picks"]
    skill = read_if(os.path.join(HERE, "script-skill.md"))
    memo = read_if(os.path.join(HERE, "style-memo.md"))
    feedback = read_if(os.path.join(EPISODES, "feedback.log")) or read_if(os.path.join(HERE, "feedback.log"))
    if research.get("mode") == "topic":
        p = picks[0]
        return f"""You write vertical video scripts for {IDENT}. Direct, contrarian, numbers-led, zero hype in the spoken script.

Today's TOPIC OF THE DAY (own this search keyword): "{p['keyword']}"
Topic: {p['name']}
Headline: {p['headline']}
Cross-source data (REAL numbers only, do not alter): {json.dumps(p.get('stats', []))}
{'' if p.get('stats') else 'NO headline metric exists for this story. Do NOT invent, estimate, or imply any number that is not in the data above. Lead with the named fact instead.'}
Related coverage: {json.dumps(p.get('sources', []), indent=1)}\n{("THE PLAY (the topic picker chose this topic FOR this operator angle; Scene 3 must be built on it): " + p["play"]) if p.get("play") else ""}

{HOOK_CRAFT}
STRUCTURE (hard rules — this is the "money play" format, the channel's viral engine):
- Scene 1 HOOK: max {s['hookMaxWords']} words. Obey the HOOK DOCTRINE above. The TITLE owns the search keyword; the hook owns the viewer. Work the topic name in naturally by scene 2 at the latest.
- Scene 2: 28-36 words: what actually happened / what it is, with one real number as the receipt.
- Scene 3: 28-36 words: THE PLAY — the specific thing an operator builds, sells, or automates with this THIS WEEK. Tool-combo how-tos ("use {p['name']} with <tool they already have>") and honest dollar framing ("agencies charge X for this") are this channel's proven best formats. Never end on "this is interesting" — end on what to do.
- Scene 4 CTA: exactly: "{cta_line()}"
- Target 30-40 seconds at ~150 wpm. Banned: {", ".join(s['bannedPhrases'])}. No em dashes.
- Big numbers as words when spoken.
- SCENE OPENINGS: each scene opens mid-thought with a concrete subject, the way
  a person keeps talking ("Google's official repo has...", "The whole setup is
  two commands..."). NEVER a connective fragment used as a transition: "Now
  the setup", "So here's the thing", "Now the numbers", "So think about what
  this means", "Here's the kicker", "But here's where it gets interesting" —
  all banned. Technical constraint: the first two words of each scene must not
  start any other scene, and never open a scene with a digit (numbers as words).

THE CRAFT (this is the skill — it outranks your instincts):
{skill}

STYLE MEMO (obey): {memo or "(none)"}
FEEDBACK (obey): {feedback or "(none)"}

ALSO produce social metadata:
{title_rules()}
- The title MUST contain the search keyword "{p['keyword']}".
- "caption": 2 short lines + exactly 6 SPECIFIC hashtags (tool/topic names, never #fyp-style generics), varied per video.
- "desc": one line (max 12 words) describing the topic for the on-screen card.

ALSO produce the on-screen text (these appear as BIG animated type):
- "hookText": max 5 words, ALL CAPS, the scroll-stopper shown over the video in the first two seconds (e.g. "MTURK IS DEAD", "GOOGLE JUST BROKE PRICING"). Punchy claim, not a summary.
- "keyTexts": one entry per beat, each max 4 words ALL CAPS — the beat's most screenshot-worthy phrase (e.g. "3 GRAND PER CLIENT", "10X CHEAPER").

Return ONLY JSON: {{"hook": "...", "beats": ["...", "..."], "cta": "...", "desc": "...", "hookText": "...", "keyTexts": ["...", "..."], "social": {{"title": "...", "caption": "..."}}}}"""
    if research.get("mode") == "breakout":
        p = picks[0]
        return f"""You write vertical video scripts for {IDENT}. Direct, contrarian, numbers-led, zero hype.

A repo is BREAKING OUT on GitHub right now and this video needs to own the keyword within the hour. Repo (real data, do not alter numbers):

{json.dumps(p, indent=1)}

{HOOK_CRAFT}
STRUCTURE (hard rules):
- Scene 1 HOOK: max {s['hookMaxWords']} words. Obey the HOOK DOCTRINE above: the viewer's stake first, the repo's name by scene 2.
- Scene 2: the repo, 40-55 words. What it does concretely (speak the star velocity only if it clears ten thousand; otherwise skip metrics), one specific way an operator makes money with it this week.
- Scene 3 CTA: exactly: "{cta_line()}"
- Target 20-30 seconds total at ~150 wpm.
- Banned: {", ".join(s['bannedPhrases'])}. No em dashes.
- Write big numbers as words ("nineteen hundred").

THE CRAFT (this is the skill — it outranks your instincts):
{skill}

STYLE MEMO (obey): {memo or "(none)"}
FEEDBACK (obey): {feedback or "(none)"}

ALSO produce the social metadata for posting:
{title_rules()}
- "caption": 2 short lines in the same voice + exactly 6 SPECIFIC hashtags (tool names, topic terms). Never generic ones like #fyp #free #viral; vary them per video.

Return ONLY JSON: {{"hook": "...", "items": [{{"repo": "{p['repo']}", "text": "..."}}], "cta": "...", "social": {{"title": "...", "caption": "..."}}}}"""
    return f"""You write 30-second vertical video scripts for {IDENT}. Direct, contrarian, numbers-led, zero hype. Audience: founders and operators.

Write today's "Repo Radar" script covering exactly these {len(picks)} GitHub repos (real data, do not alter numbers):

{json.dumps(picks, indent=1)}

{HOOK_CRAFT}
STRUCTURE (hard rules):
- Scene 1 HOOK: max {s['hookMaxWords']} words. Obey the HOOK DOCTRINE above. No greeting.
- Scenes 2-{1 + len(picks)}: one per repo, {s['wordsPerItem']['min']}-{s['wordsPerItem']['max']} words each. MUST open with the words "First," / "Second," / "Third," respectively (caption alignment depends on it). Each: what it does in one concrete sentence, the star number as a spoken receipt, then the operator angle (who makes money with it and how).
- Final scene CTA: exactly this line: "{cta_line()}"
- Target total: {s['totalTargetSec'][0]}-{s['totalTargetSec'][1]} seconds at ~150 wpm. Shorter beats longer; people scroll.
- Banned words/phrases: {", ".join(s['bannedPhrases'])}. No em dashes.
- Write numbers as words where the voice clone might stumble ("nineteen hundred", "fourteen thousand").

THE CRAFT (this is the skill — it outranks your instincts):
{skill}

STYLE MEMO (learned from past performance — obey it):
{memo or "(none yet)"}

RECENT HUMAN FEEDBACK (obey it):
{feedback or "(none yet)"}

ALSO produce the social metadata for posting:
{title_rules()}
- "caption": 2 short lines in the same voice, names all repos, + exactly 6 SPECIFIC hashtags (tool names, topic terms). Never generic ones like #fyp #free #viral; vary them per video.

Return ONLY JSON, no markdown fences:
{{"hook": "...", "items": [{{"repo": "owner/name", "text": "First, ..."}}, ...], "cta": "...", "social": {{"title": "...", "caption": "..."}}}}"""


SYSTEM_PROMPT = (
    "You are a short-form video script writer. You return ONLY a single JSON "
    "object and nothing else: no preamble, no explanation, no markdown fences. "
    "You never use tools; you answer directly from the prompt you are given."
)


class LLMError(RuntimeError):
    """Raised when every model in the chain fails. Callers surface this to
    Telegram rather than dying silently (see watch.py / daily.py)."""


def _extract_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def _call_claude_cli(prompt):
    """Generate via the Claude Code CLI in headless print mode.

    Authenticated by CLAUDE_CODE_OAUTH_TOKEN (from `claude setup-token`), which
    bills against the Claude subscription rather than per-token API credits.

    NOTE: ANTHROPIC_API_KEY takes PRECEDENCE over the OAuth token in Claude
    Code's auth chain. If it is set we refuse to run, because that would
    silently switch this pipeline onto paid API billing.
    """
    import shutil, subprocess, tempfile

    if os.environ.get("ANTHROPIC_API_KEY"):
        raise LLMError(
            "ANTHROPIC_API_KEY is set. It outranks CLAUDE_CODE_OAUTH_TOKEN and "
            "would bill per-token API pricing instead of the subscription. "
            "Unset it (Railway: railway variables --unset ANTHROPIC_API_KEY).")

    binary = env("CLAUDE_BIN", "claude")
    if not shutil.which(binary):
        raise LLMError(f"'{binary}' not on PATH. Install Claude Code in the image "
                       "(curl -fsSL https://claude.ai/install.sh | bash).")
    # Auth is NOT pre-checked: a dev machine keeps credentials in the OS
    # keychain (no file to stat), while a container uses the OAuth token env
    # var. We run the command and translate an auth-shaped failure below.
    AUTH_HINT = ("run `claude setup-token` and set CLAUDE_CODE_OAUTH_TOKEN "
                 "in the environment")

    # Primary first, then fallbacks. Default: fable (creative writing) -> opus.
    chain = [m.strip() for m in env("LLM_MODELS", "fable,opus").split(",") if m.strip()]
    timeout = int(env("LLM_TIMEOUT_SEC", "180"))
    errors = []

    # Subprocess env: pass the OAuth token through explicitly. env() loads
    # pipeline/.env into os.environ, so this covers both .env and real env vars.
    child_env = dict(os.environ)
    tok = env("CLAUDE_CODE_OAUTH_TOKEN")
    if tok:
        child_env["CLAUDE_CODE_OAUTH_TOKEN"] = tok
    child_env.pop("ANTHROPIC_API_KEY", None)  # belt and braces: never bill API

    # Run from a scratch dir, NOT the repo. In the container cwd is /app, which
    # has a CLAUDE.md; letting the CLI load project context would waste tokens
    # on every generation and can leak repo instructions into the script.
    scratch = tempfile.mkdtemp(prefix="scriptgen-")

    for model in chain:
        # NB: do NOT add --bare. It skips the credential path that reads
        # CLAUDE_CODE_OAUTH_TOKEN, so headless auth fails with "Not logged in".
        # Verified against a clean environment 2026-08-28.
        cmd = [binary, "-p", prompt,
               "--model", model,
               "--system-prompt", SYSTEM_PROMPT,
               "--output-format", "json",
               "--no-session-persistence"]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  timeout=timeout, stdin=subprocess.DEVNULL,
                                  env=child_env, cwd=scratch)
        except subprocess.TimeoutExpired:
            errors.append(f"{model}: timed out after {timeout}s")
            continue

        if proc.returncode != 0:
            tail = (proc.stderr or proc.stdout or "").strip()[-300:]
            errors.append(f"{model}: exit {proc.returncode} — {tail}")
            continue

        try:
            envelope = json.loads(proc.stdout)
        except json.JSONDecodeError:
            errors.append(f"{model}: CLI did not return JSON — {proc.stdout[:200]}")
            continue

        if envelope.get("is_error"):
            errors.append(f"{model}: {str(envelope.get('result'))[:200]}")
            continue

        data = _extract_json(envelope.get("result") or "")
        if data is None:
            errors.append(f"{model}: no JSON object in result — "
                          f"{str(envelope.get('result'))[:200]}")
            continue

        if model != chain[0]:
            print(f"[scriptgen] primary model failed; produced with fallback "
                  f"'{model}'", flush=True)
        return data

    blob = " ".join(errors).lower()
    hint = ""
    if any(w in blob for w in ("auth", "login", "unauthor", "401", "credential", "token")):
        hint = f"\nLooks like an auth problem: {AUTH_HINT}."
    elif any(w in blob for w in ("rate limit", "429", "usage limit", "quota")):
        hint = ("\nLooks like a subscription usage limit. It resets on its own; "
                "the run will be retried on the next schedule.")
    raise LLMError("all models failed:\n  " + "\n  ".join(errors) + hint)


def _call_http(prompt):
    """Legacy path: any Anthropic-compatible HTTP endpoint (z.ai, Anthropic API)."""
    base = env("LLM_BASE_URL", "https://api.z.ai/api/anthropic").rstrip("/")
    key = env("LLM_API_KEY")
    model = env("LLM_MODEL")
    if not key or not model:
        raise LLMError("Set LLM_API_KEY and LLM_MODEL, or use LLM_PROVIDER=claude-cli")
    body = json.dumps({
        "model": model,
        "max_tokens": 1200,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        base + "/v1/messages", data=body,
        headers={"content-type": "application/json", "x-api-key": key,
                 "authorization": f"Bearer {key}", "anthropic-version": "2023-06-01"})
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
    except Exception as e:  # surface the status (e.g. 429 quota) to Telegram
        raise LLMError(f"{model} via {base}: {e}")
    text = "".join(b.get("text", "") for b in resp.get("content", []))
    data = _extract_json(text)
    if data is None:
        raise LLMError(f"LLM returned no JSON:\n{text[:500]}")
    return data


def call_llm(prompt):
    provider = env("LLM_PROVIDER", "claude-cli").strip().lower()
    if provider in ("claude-cli", "claude", "cli"):
        return _call_claude_cli(prompt)
    return _call_http(prompt)


def refine(research, draft):
    """Editor pass: critique the draft against the skill and return the
    improved version. Reliably lifts weaker models; falls back to the draft
    if the editor output doesn't parse."""
    skill = read_if(os.path.join(HERE, "script-skill.md"))
    prompt = f"""You are a ruthless short-form script editor. Below is THE CRAFT
(the standard) and a DRAFT script (JSON). Judge the draft against the craft,
then return the FINAL script as JSON with the exact same keys.

Non-negotiables:
- COHERENCE FIRST: read the draft aloud as one person speaking. Kill any
  sentence that sounds like a filled-in template or references something
  that doesn't exist in THIS video (e.g. "number one" in a video with no
  list). Rewrite in plain speech a founder would actually say to a friend.
- Hook: hard fact in sentence one + a reason to stay that FITS THE FORMAT
  (numbered loop ONLY for list videos; single-topic videos tease the payoff
  or let the fact carry). Exactly one bold claim, never two mashed.
- Every beat: a concrete fact, then the money/value line. Cite a number
  ONLY if it impresses an outsider on its own; never speak GitHub star
  counts under ten thousand, Hacker News points, or upvotes. A weak number
  is worse than none: translate it to the outcome instead. One
  screenshot-worthy line per beat.
- The loop's promised payoff must be the strongest moment in the script.
- Keep First/Second/Third openers in list videos and the CTA line VERBATIM.
  Other scenes may be rewritten freely, including their openings — but the
  first two words of each scene must stay distinct across scenes, must not
  be a digit, and must never be a bare connective fragment ("Now the setup",
  "So here's the thing"). Scenes open mid-thought with a concrete subject.
- Keep all real numbers unchanged. Shorten anything clunky when spoken.

If the draft is already excellent, return it with minimal polish. Rewrite
weak hooks entirely.

THE CRAFT:
{skill}

DRAFT:
{json.dumps(draft)}

Return ONLY the final JSON, no commentary."""
    try:
        out = call_llm(prompt)
        # sanity: same essential keys, non-empty
        if out.get("hook") and (out.get("items") or out.get("beats")):
            return out
    except Exception as e:
        print("refine pass failed, keeping draft:", e)
    return draft


def main():
    ep = sys.argv[1] if len(sys.argv) > 1 else None
    if not ep:
        raise SystemExit("usage: scriptgen.py <episode-dir-name>")
    epdir = os.path.join(EPISODES, ep)
    research = json.load(open(os.path.join(epdir, "research.json")))

    out = call_llm(build_prompt(research))
    out = refine(research, out)

    # Renderer scene list (durations get replaced by real Whisper timings in prep.py)
    scenes = [{"type": "intro", "durationSec": 4, "text": out["hook"]}]
    if research.get("mode") == "topic":
        p = research["picks"][0]
        # Format v3: fullscreen avatar hook with BIG kinetic text over the
        # footage (text hook in the first 2 seconds, always), then motion
        # every beat: screenshot pan / animated stat card / kinetic type.
        key_texts = out.get("keyTexts") or []
        scenes[0] = {"type": "avatar", "durationSec": scenes[0]["durationSec"],
                     "text": scenes[0]["text"],
                     "overlayText": (out.get("hookText") or p["name"])[:36]}
        stats = [st for st in (p.get("stats") or []) if st.get("value")]
        from urllib.parse import urlparse
        u = urlparse(p.get("url", ""))
        label = (u.netloc + u.path)[:44] or p["name"]
        shots = [f for f in ("shot.jpg", "shot2.jpg")
                 if os.path.exists(os.path.join(epdir, f))
                 and os.path.getsize(os.path.join(epdir, f)) > 20_000]
        for i, beat in enumerate(out["beats"]):
            key = (key_texts[i] if i < len(key_texts) else "")[:28]
            if i == 0:
                # beat 1 visual priority: real page > real stat card > kinetic type
                if shots:
                    scenes.append({"type": "shot", "durationSec": 12,
                                   "image": shots[0], "label": label, "text": beat})
                elif stats:
                    st = stats[0]
                    scenes.append({"type": "topic", "durationSec": 12,
                                   "name": p["name"],
                                   "desc": out.get("desc", p["headline"])[:90],
                                   "stat": st["value"], "statLabel": st["label"],
                                   "pill": st.get("pill", "trending today"),
                                   "text": beat})
                else:
                    scenes.append({"type": "kinetic", "durationSec": 12,
                                   "keyText": key or p["name"], "text": beat})
            else:
                # the play: back on camera WITH the money phrase punched in
                scenes.append({"type": "avatar", "durationSec": 12, "text": beat,
                               "overlayText": key})
    else:
        picks_by_repo = {p["repo"]: p for p in research["picks"]}
        for item in out["items"]:
            p = picks_by_repo.get(item["repo"]) or {}
            scenes.append({"type": "repo", "durationSec": 10, "repo": item["repo"],
                           "stars": p.get("stars", 0), "today": p.get("today", 0),
                           "desc": p.get("desc", ""), "text": item["text"]})
    scenes.append({"type": "cta", "durationSec": 4, "text": out["cta"],
                   "badge": _I.get("handle") or "@you"})

    social = out.get("social") or {}
    t = (social.get("title") or "").strip()
    bad = (not t or len(t) > 100 or t.count("?") > 1 or " No, " in t
           or t.upper().count("DESTROYS") + t.upper().count("INSANE") > 1)
    if bad:
        # deterministic fallback: the fact-first hook IS a good title
        social["title"] = scenes[0]["text"].rstrip(".")[:90]
        print(f"!! LLM title rejected ({t[:60]!r}) — using hook as title")
    fn = CFG.get("funnel", {})
    # repo-list videos get their own keyword/magnet (best-engagement series)
    is_repo_video = research.get("mode") not in ("topic", "breakout")
    kw = (fn.get("repoKeyword") if is_repo_video else None) or fn.get("commentKeyword")
    magnet = (fn.get("repoMagnet") if is_repo_video else None) or fn.get("magnet", "the free toolkit")
    if kw and social.get("caption"):
        cap_lines = social["caption"].rstrip().rsplit("\n", 1)
        cta_line = f"Comment {kw} and I'll DM you {magnet}."
        # insert the comment-CTA before the hashtag line
        if len(cap_lines) == 2 and cap_lines[1].startswith("#"):
            social["caption"] = f"{cap_lines[0]}\n{cta_line}\n{cap_lines[1]}"
        else:
            social["caption"] = f"{social['caption'].rstrip()}\n{cta_line}"
    social = social or {
        "title": scenes[0]["text"][:90],
        "caption": scenes[0]["text"] + "\n#ai #aiagents #github #buildinpublic #startup #tech",
    }
    layout = "fullscreen" if research.get("mode") == "topic" else "split"
    json.dump({"date": research["date"], "scenes": scenes, "social": social,
               "layout": layout},
              open(os.path.join(epdir, "script.json"), "w"), indent=1)

    md = [f"# Repo Radar — {research['date']}", "",
          "Paste each block as its own HeyGen scene (or all as one block).", ""]
    for i, sc in enumerate(scenes, 1):
        md += [f"**SCENE {i}**", sc["text"], ""]
    open(os.path.join(epdir, "script.md"), "w").write("\n".join(md))

    words = sum(len(sc["text"].split()) for sc in scenes)
    print(f"script.json + script.md written — {words} words (~{round(words / 2.5)}s)")


if __name__ == "__main__":
    main()
