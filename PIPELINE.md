# Reels Engine — Pipeline Runbook

Everything lives in `Desktop/Reels Engine/`:

```
pipeline/     the automation (config, scripts, style memo, .env)
studio/       Remotion template (renders the graphics + captions)
episodes/     one folder per reel: research.json → script → avatar.mp4 → final.mp4
```

## One-time setup
1. `cp pipeline/.env.example pipeline/.env` and fill in your z.ai token + model.
2. Optional: set `REELS_WEBHOOK_URL` to a Cyndra Agent hook for WhatsApp breakout alerts.

## Daily flow (the 3 minutes that are yours)

```bash
cd "~/Desktop/Reels Engine/pipeline"
python3 research.py            # picks today's 3 repos, creates episodes/<date>-repo-radar/
python3 scriptgen.py <ep-dir>  # writes script.json + script.md (GLM via your z.ai sub)
# → paste script.md into HeyGen, export 1080p, save as episodes/<ep-dir>/avatar.mp4
python3 prep.py <ep-dir>       # whisper → align → remotion → ffmpeg → final.mp4
# → watch final.mp4 (approval gate), then post via Metricool
```

`prep.py` is the whole post-production chain from the V1 build: word-level
captions from what you actually said, scene panels switched on your anchor
words (First/Second/Third), 1.08x pacing, loudness-normalized audio.

## Breakout mode (the every-2-hours "own the keyword" cron)

`watch.py` checks GitHub trending, remembers star velocity between runs, and
when an uncovered AI repo crosses the threshold (config: `breakout`) it
creates a single-repo episode, pre-writes the script, and pings you
(macOS notification + webhook). You record one HeyGen clip and run `prep.py` —
video is live while the repo is still on page 1 of trending.

Schedule both (launchd, survives reboots — or use `cron`):

```bash
# every 2 hours: trend watcher
crontab -e
0 */2 * * *  cd "$HOME/Desktop/Reels Engine/pipeline" && /usr/bin/python3 watch.py >> watch.log 2>&1
# daily 6am: research for the regular episode
0 6 * * 1-5  cd "$HOME/Desktop/Reels Engine/pipeline" && /usr/bin/python3 research.py >> research.log 2>&1
```

Note: cron only fires while the Mac is awake. If reels become a real channel,
move watch.py to Railway later — it has no Mac dependency (notifications go
through the webhook; scriptgen runs anywhere).

## Feedback loop (how each reel gets better)

Two inputs, one output:

1. **Your notes — `pipeline/feedback.log`.** One line per observation, e.g.
   `2026-07-05: repo explanations too long, people scroll — target 25 words.`
   Highest priority; scriptgen quotes this file into every prompt.
2. **Metrics — `pipeline/metrics.csv`.** Weekly: export post analytics from
   Metricool (views, likes, shares, watch %) into this file. For drop-off
   curves, check YouTube Studio's retention graph per Short and write what
   you see into feedback.log ("drop at second repo" etc.) — Metricool doesn't
   expose second-by-second retention, YouTube does natively.

Then run:

```bash
python3 analyze.py   # LLM turns metrics + notes into concrete rules in style-memo.md
```

`style-memo.md` is the memory of the system: scriptgen reads it before every
script, so rules like "hooks with star counts outperform" compound daily.
analyze.py only ever edits the memo — it can't break the pipeline; review its
proposals like a PR.

## Fully-automated mode (all keys set in .env)

Two posting systems, per the spec:

1. **Daily show** — `daily.py` (cron 06:00): research → GLM script (+ social
   title/caption/hashtags) → HeyGen API render → assemble → **Metricool
   schedule at +24h across all platforms**. The 24h delay IS the approval
   gate: you get a webhook ping, and anything you don't like you delete from
   the Metricool planner before it fires.
2. **Breakout** — `watch.py` (cron every 2h): only fires on a BIG trend
   (config `breakout`: ≥1,200 stars today, or +500 since the last check) →
   script with a searchable keyword title → render → **posts immediately**
   (`breakout.autopost: true`; set false to require a manual `metricool.py
   <ep> --now`). Max 2/day.

Combined output: 1 scheduled daily reel + 0-2 breakout reels = the 2-3/day
target. `serve.py` (or nginx) exposes finals so Metricool can fetch them —
set `REELS_PUBLIC_BASE` + `REELS_SERVE_TOKEN`.

First Metricool run: use `python3 metricool.py <ep> --in-hours 24 --dry-run`,
then a real run, and verify the post in the planner — their scheduler API is
lightly documented, so eyeball the first one per platform.

## Roadmap (in order, each unlocks the next)
- [ ] 7 days of daily episodes (proves quality + gathers metrics)
- [ ] First analyze.py run with real Metricool export
- [ ] Wire alerts into Cyndra/hermes WhatsApp (veto + "post it" from phone)
- [ ] Series B (AI news) — same pipeline, different research.py source
