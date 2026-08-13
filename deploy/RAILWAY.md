# Deploying to Railway

One service, one volume, everything scheduled inside `pipeline/worker.py`
(daily show, spotlight, 2-hourly breakout watcher, Sunday analyzer, and the
media server Metricool fetches videos from).

## Steps

1. Railway dashboard → New Project → **Deploy from GitHub repo** → `jsath/reels-engine`.
   It builds from the Dockerfile (~10 min first build: whisper.cpp + model).
2. Service → **Volumes** → add volume mounted at **`/data`** (5GB is plenty to start).
3. Service → **Settings → Networking** → Generate Domain (needed so Metricool
   can fetch the videos).
4. Service → **Variables** — set:

```
LLM_BASE_URL=https://api.z.ai/api/anthropic
LLM_API_KEY=<z.ai coding-plan token>
LLM_MODEL=glm-5.2
HEYGEN_API_KEY=<heygen PAYG key>
HEYGEN_AVATAR_ID=<avatar id>
HEYGEN_VOICE_ID=<voice id>
METRICOOL_USER_TOKEN=<token>
METRICOOL_USER_ID=<id>
METRICOOL_BLOG_ID=<brand id>
METRICOOL_PROVIDERS=tiktok,instagram,youtube,linkedin
REELS_SERVE_TOKEN=<long random string>
REELS_PUBLIC_BASE=https://<railway-domain>/<REELS_SERVE_TOKEN>
REELS_WEBHOOK_URL=<hermes/cyndra webhook for WhatsApp pings>
TIMEZONE=Asia/Bangkok
TOPIC_HOUR=6          # daily topic-of-the-day deep dive
DAILY_HOUR=13         # weekday 3-repo Repo Radar
WATCH_EVERY_HOURS=2   # breakout newsjacking
```

5. Deploy. Watch logs: you should see `media server on :<port>` and, on the
   next scheduled tick, the full chain running.

## Costs & sizing
- Plan with **2GB+ RAM** (Remotion render). A 35s reel renders in ~4-10 min
  on shared vCPU; ~3 renders/day is nothing.
- Railway ~$5-15/mo + HeyGen PAYG ~$1/reel-minute + z.ai flat + Metricool
  (existing).

## Operating it
GLM 5.2 is the operator — see `OPERATOR.md` in the repo root for the runbook,
tuning knobs, and guardrails. Blast-radius separation: this Railway project's
only credentials are the ones above; it can't touch anything else.
