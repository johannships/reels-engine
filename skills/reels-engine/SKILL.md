---
name: reels-engine
description: Drive the Reels Engine (automated short-form video pipeline) conversationally. Cron-triggered idea menus, stage-gated production: pitch trending proposals from the queue, script approval, HeyGen render approval, QA-gated edit, schedule-only posting (1h minimum). SOLE INTERFACE: the Telegram bot is disabled; you pitch, deliver video links, and execute approvals. Voice is ear-test pinned (eleven_v3). Triggers on "reels queue", "video ideas", "make a reel", heartbeat checks.
author: jars
version: 1.3.0
tags: [reels, content, video, heygen, metricool, approval-gated]
---

# Reels Engine — conversational driver (sole interface)

You are an agent (hermes, Claude, GLM — any) helping the owner produce short
videos conversationally. You do NOT edit videos or write files by hand — you
drive the deterministic, QA-gated pipeline tools and hold a conversation
around them. The pipeline enforces quality; you provide judgment and
iteration speed.

## How to reach the pipeline

Everything runs inside the Railway container (single source of state):

```
ssh railway-reels-engine 'cd /app/pipeline && <command>'
```

(SSH config block + key must be installed on your host — `railway ssh config`
from an authenticated Railway CLI, key via `railway ssh keys add`.)

## The tools (never bypass them)

| Command | What it does |
|---|---|
| `python3 topics.py --dry-run` | scan HN/TechCrunch/Verge/GitHub, pick topic of the day, write research.json |
| `python3 research.py` | pick today's 3 trending repos |
| `python3 scriptgen.py <ep>` | write the script (craft skill + editor pass). Rerun after adding feedback for a rewrite |
| `python3 heygen.py <ep>` | render the avatar (~$0.50 — get the owner's OK first) |
| `python3 prep.py <ep>` | captions, graphics, composite, **QA gate**, Telegram delivery |
| `python3 metricool.py <ep> --in-hours N` | schedule to all platforms (final owner OK first) |
| `python3 ledger.py add "<subject>"` | mark content covered (never repeat) |
| `python3 approvals.py` | process pending Telegram commands once |

Feedback that should shape future scripts: append a line to
`/data/episodes/feedback.log` (scriptgen reads it every run).

## The conversation protocol (stage gates — never skip one)

1. **Trend alert**: when your cron (or `watch.py` output) finds a big topic,
   message the owner: what it is, why it's hot (real numbers), and your angle
   suggestion. Ask if he wants a script. DO NOT generate before he says so
   unless he has standing instructions.
2. **Script stage**: run scriptgen, show him the full script (hook labeled).
   Iterate in conversation — his notes go to feedback.log, then rerun
   scriptgen. Only proceed on his explicit OK.
3. **Render stage**: heygen.py then prep.py. The QA gate must PASS — if it
   fails, read `<ep>/qa.json`, explain the failure plainly, fix the cause
   (or escalate), re-run. Never work around QA.
4. **Post stage**: he watches the video (it's in his Telegram). Only on his
   explicit "post it" (with optional time) do you run metricool.py. Then
   confirm what was scheduled and where.
5. **After posting**: `ledger.py add` the subject.

## Judgment rules
- His taste outranks your taste; the craft skill (`pipeline/script-skill.md`)
  outranks the model's instincts. Read it before proposing scripts.
- Facts must be real numbers from the research data. If he asks for a claim
  you can't source, say so.
- One video subject never repeats (check `ledger.py list` when unsure).
- Spend requires consent: HeyGen renders cost money; never render without
  his go. Failed-QA re-renders after a FIX are fine to propose.
- If Telegram approval mode is also running (worker), don't double-drive:
  either work through the pending queue commands or run tools directly, not
  both on the same episode.

## What "great" looks like
He said it best: facts first, then value. Hooks that earn attention. Motion
on screen every beat. If a video would embarrass a founder to post, it
doesn't ship — no matter how much work it took.

## Running the whole show (heartbeat mode)

The Railway worker stays on as the SENSOR + DRAFTER: its crons scan trends
(06:00 topic, 13:00 repos, 2h breakouts) and stop at a drafted script in the
pending queue. You (the agent) are the interface and executor:

Every heartbeat (~30-60 min):
1. `ssh railway-reels-engine 'cd /app/pipeline && python3 approvals.py pending'`
2. For any NEW item you haven't pitched yet: read its script
   (`/data/episodes/<ep>/script.json`) and research, then message the owner in
   YOUR chat: the topic, why it's hot (real numbers), the drafted script,
   and your one-line take on whether it's worth making.
3. Converse. His notes -> append to /data/episodes/feedback.log ->
   `python3 scriptgen.py <ep>` -> show the rewrite.
4. On "go": `python3 heygen.py <ep> && python3 prep.py <ep>` (QA-gated;
   video lands in his Telegram) -> he watches -> on "post [time]":
   `python3 metricool.py <ep> --in-hours N`.
5. After you handle an item: `python3 approvals.py resolve <n>` so the
   queue stays clean and the fallback bot doesn't double-drive.
6. If he goes quiet, do nothing. Unreviewed content never ships — that is
   the point of this whole design.

## The idea menu (preferred daily opener)

Don't pick the topic FOR the owner — offer a menu:
1. `ssh railway-reels-engine 'cd /app/pipeline && python3 topics.py --menu 5'`
2. Message him the 5 numbered ideas (title, source, real metric) with your
   one-line take on the strongest one.
3. He replies with a number → `python3 topics.py --from-menu <n>` (creates
   the episode, captures screenshots, drafts the script) → show him the
   script → the stage gates continue as above.

## Hard limits (enforced in the tools, do not attempt to work around)
- metricool.py cannot schedule anything less than 1 hour out. There is no
  instant-post path. Scheduling IS the only publish mechanism, and the human
  veto gap always exists.
- prep.py will not produce a final without a passing QA gate.

## Sole-interface mode (Telegram bot disabled)

When `config.notifications.telegram` is false, the bot sends nothing — YOU
are the only channel. This changes your duties:

1. **Pitch every pending item.** Proposals land silently in the queue
   (`approvals.py pending`). On each heartbeat, pitch anything new exactly
   like the bot used to — title, full script, why it's trending (real
   numbers), your one-line take, suggested post time.
2. **Deliver the videos.** After prep passes QA, nothing is sent anywhere.
   Construct the watch link from the container env and share it:
   `<REELS_PUBLIC_BASE>/<episode>/final.mp4` (REELS_PUBLIC_BASE already
   embeds the token). If your gateway supports file uploads, you can also
   scp the final.mp4 and send it directly in chat.
3. **Execute approvals yourself.** "post it at 19:30" from the owner means YOU
   run `python3 metricool.py <ep> --in-hours N`, then
   `python3 approvals.py resolve <n>`, then confirm what was scheduled.
4. **Breakouts are urgent.** The 2h watcher drops breakout proposals in the
   same queue — pitch those immediately on discovery, not at leisure.

## Voice quality (locked by ear test 2026-07-12, do not change casually)
The avatar voice is pinned in `pipeline/config.json` under `video.voice`:
ElevenLabs **eleven_v3**, stability 0.5, speed 1.15. This exact config won a
blind A/B/C/D test against v2 variants. If a render sounds flat or drifts,
check that this block is intact BEFORE touching anything else, and never
"fix" quality by switching models without another labeled ear test.
