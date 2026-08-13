# Deploying to the Hetzner box (next to the hermes agent)

## Why this server
Fixed cost you already pay, persistent disk for episodes/state, and the agent
lives here — so it can pull this repo, edit `pipeline/style-memo.md`,
`config.json`, or any script, and commit back. GitHub is the source of truth;
the server runs whatever `main` says.

## First deploy

```bash
ssh <hetzner>
git clone https://github.com/jsath/reels-engine.git ~/reels-engine
cd ~/reels-engine && bash deploy/setup.sh          # ffmpeg, node, whisper.cpp, chromium
nano pipeline/.env                                  # LLM_*, HEYGEN_*, REELS_WEBHOOK_URL
cd pipeline && python3 daily.py                     # full test run
crontab ../deploy/crontab.example                   # after editing REPO path
```

`REELS_WEBHOOK_URL` should point at the hermes agent's inbound hook so
breakout alerts and "final ready" pings land in WhatsApp. To approve from the
phone, have the agent reply-handle those messages (e.g. "post it" -> agent
runs the Metricool step or moves the file to a posting queue).

## Update flow (how edits happen)

- **You or GLM edit on GitHub** (or locally, push) -> server: `git pull`.
  Add a cron line or a webhook-triggered `git pull` if you want auto-deploy.
- **The agent optimizes in place**: it can run `analyze.py`, edit the style
  memo / thresholds, then `git commit && git push` so changes survive and are
  reviewable. Suggested guardrail: the agent only touches `style-memo.md`,
  `feedback.log`, and `config.json` — code changes go through you/GLM.

## Notes
- The Mac remains a fully working dev environment (same commands); server and
  Mac share nothing but the repo. Episodes/state stay local to each machine.
- Remotion renders ~45s at roughly 2-6x realtime on a shared vCPU — fine for
  a dozen reels/day. If the auto-downloaded Chrome headless shell misbehaves,
  `REELS_BROWSER` in .env already points at system chromium (setup.sh set it).
- HeyGen renders happen in HeyGen's cloud (PAYG ~$1/min); the server only
  downloads the result. Without `HEYGEN_API_KEY`, daily.py stops after the
  script and pings you to record manually.
