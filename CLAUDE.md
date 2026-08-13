# CLAUDE.md — read this first

You (Claude Code, or any coding agent) are the setup wizard and operator
for the **Reels Engine**: an automated short-form video system. It
researches trending topics, writes scripts in the owner's voice via an LLM,
renders their HeyGen avatar clone, assembles branded vertical video
(Remotion graphics + karaoke captions), QA-checks every frame (including
that the face is never cut off), and schedules posts across platforms via
Metricool — with the owner approving every video from Telegram.

Built by Johann (@johannships), who runs this exact system daily. The
public repo is the engine; each owner's identity lives in a gitignored
`pipeline/config.local.json` layer, so cloning never inherits anyone else's
voice.

## Your job when someone says "set this up for me"

Run the stages IN ORDER. Do everything you can yourself; ask only for what
requires their accounts or their taste. After each stage, tell them what
just became true.

### Stage 0a — prove the renderer works (60 seconds, zero credentials)

Before asking a single question, give them a visible win and validate the
toolchain (only needs Node 20+):

```
mkdir -p episodes/demo-episode && cp examples/demo-episode/* episodes/demo-episode/
cd studio && npm install && npx remotion render RepoRadar \
  ../episodes/demo-episode/canvas.mp4 --props=../examples/demo-episode/props.preview.json
```

A 30-second vertical video renders: repo cards, karaoke captions, the
reserved avatar zone. Show it to them — "this is what your machine will
make" is the emotional hook that carries the rest of setup. If this fails,
fix Node before proceeding; nothing downstream will work.

### Stage 0 — the niche interview (5 minutes, do this FIRST)

Ask, conversationally, one at a time:
1. Name, handle, and what they make content about (their niche).
2. Who watches — founders? developers? fitness people? — and what outcome
   the audience wants.
3. Their site / community / newsletter links, if any.
4. What "trending" means in their niche: which subreddits, which RSS feeds,
   which keywords. (Defaults in config.json are for an AI/dev channel —
   replace them for other niches.)
5. One or two creators whose short-form style they admire.

Then WRITE the results:
- `pipeline/config.local.json` → `identity` block (name, handle,
  positioning, audience, site, community). The script generator builds its
  persona from this — it is the single highest-leverage file.
- `pipeline/config.local.json` → `research.keywords`, `topics.subreddits`,
  `topics.feeds`, `topics.extraKeywords` for their niche (overrides merge
  over config.json — see pipeline/configlib.py).
- `pipeline/style-memo.md` → seed 3-5 standing rules from their answers
  (named tools/specifics beat generic advice in every niche; keep the
  structural rules already there).
- CTA lines: `script.ctaRotation` in config.local.json, their links.

### Stage 1 — HeyGen clone from zero (the emotional peak — guide it well)

If they already have an avatar + voice, skip to verification below.

1. **Recording the training clip** (their phone or webcam, 2 minutes):
   - Good even lighting, clean background, camera at eye level, 1080p+.
   - Look at the lens, talk naturally the entire time (read anything aloud).
   - **Keep hands calm and below frame** — quick-clones inherit every
     gesture in the source; fidgety hands become permanent fidgety renders.
   - Small pauses with a closed mouth every few sentences (gives the model
     clean cut points).
2. In HeyGen: Avatars → Create Avatar → upload the clip, consent video as
   prompted. Voice: HeyGen will offer to clone from the same clip, or
   record/upload a cleaner 1-2 min voice sample.
3. API access: HeyGen settings → API — note that API credits are
   pay-as-you-go (~$1 per minute of rendered video) and separate from web
   subscriptions. They need the API key + a few dollars of credits.
4. **Verify with them** (never guess IDs):
   `GET https://api.heygen.com/v2/avatars` and `/v2/voices` with header
   `X-Api-Key` — list entries matching their name, confirm which avatar_id
   and voice_id to use, write them to `pipeline/.env`
   (`HEYGEN_AVATAR_ID`, `HEYGEN_VOICE_ID`, `HEYGEN_API_KEY`).
5. Multiple looks (optional, nice after the first successful video): more
   recordings → more avatars → put the ids in config.local.json
   `video.avatarLooks` [array]; the engine rotates per-episode
   deterministically, and an episode's script.json `"avatarId"` pins one.
6. **No-API mode**: without HEYGEN_API_KEY the daily run stops after the
   script and notifies them to record/export manually into
   `episodes/<ep>/avatar.mp4`; everything downstream stays automated.

### Stage 2 — the LLM key

Any Anthropic-compatible endpoint works (`LLM_BASE_URL`, `LLM_API_KEY`,
`LLM_MODEL` in pipeline/.env). Flat-rate coding plans (like z.ai GLM) avoid
per-token billing. Verify with a 1-token test call BEFORE proceeding —
a bad LLM key fails confusingly late otherwise.

### Stage 3 — Telegram approval bot (10 minutes)

1. @BotFather → /newbot → copy token → `TELEGRAM_BOT_TOKEN`.
2. They send their new bot any message.
3. `GET https://api.telegram.org/bot<token>/getUpdates` → read
   `chat.id` → `TELEGRAM_CHAT_ID`.
4. Send a test message and confirm they see it.
Approval commands they'll use: `list`, `post N [time]`, `skip N`,
`fb N <note>`, `go N`, `redo N <notes>` (see OPERATOR-HUMAN.md).
`notifications.telegram` defaults to true — leave it.

### Stage 4 — Metricool (the posting arm)

1. They need Metricool **Advanced** (API access) with their social
   accounts connected to ONE brand.
2. `GET https://app.metricool.com/api/admin/simpleProfiles` with header
   `X-Mc-Auth: <token>` → list their brands — **accounts often have
   several; confirm WHICH blogId with them**, never assume.
3. Write `METRICOOL_USER_TOKEN`, `METRICOOL_USER_ID`, `METRICOOL_BLOG_ID`,
   `METRICOOL_PROVIDERS` (their platforms, comma-separated), `TIMEZONE`.
4. Dry-run: `python3 metricool.py <ep> --in-hours 24 --dry-run`, then ONE
   real scheduled post they can see in the Metricool planner and delete.
   Their scheduler API is lightly documented — eyeball the first post per
   platform.

### Stage 5 — local proof run, then deploy

Local (macOS or Linux; deps: node 20+, ffmpeg, python3, whisper.cpp,
optionally opencv-python-headless). macOS: `brew install ffmpeg
whisper-cpp`. Linux: `deploy/setup.sh` (Debian/Ubuntu). The ggml-small.en
model auto-downloads to `pipeline/models/` on the first prep.py run
(~466MB; set WHISPER_MODEL in .env to reuse an existing copy):
```
cd studio && npm install
cd ../pipeline
python3 research.py          # picks trending repos for their keywords
python3 scriptgen.py <ep>    # script in THEIR voice (needs LLM key)
python3 heygen.py <ep>       # or manual avatar.mp4 in no-API mode
python3 prep.py <ep>         # whisper → remotion → ffmpeg → QA → telegram
```
The QA gate must pass (it self-corrects the face crop up to 3x). The video
lands in their Telegram. THAT moment — their clone presenting their
content — is the payoff; make sure they see it before deploying.

Deploy (their choice):
- **Railway** (managed, ~$5-10/mo + HeyGen credits): `deploy/RAILWAY.md`.
  One service from this Dockerfile, volume at `/data`, env vars pasted.
  **Copy config.local.json to /data/** — /app is rebuilt from git on every
  deploy and git never contains the local layer (configlib falls back to
  /data/config.local.json automatically).
- **VPS**: `deploy/DEPLOY.md` + `deploy/setup.sh` + crontab.
- **Mac mini**: `deploy/crontab.example`, runs locally forever.

Verify before calling it live: one full `topics.py` run end to end, video
in their Telegram, post visible in Metricool planner, they approve or veto.

### Stage 6 — first week of operating

- Everything waits in the approval queue; nothing posts itself
  (`posting.mode: "approval"` — do not change this for a new user).
- Their `fb N <note>` feedback accumulates → Sunday analyze.py →
  style-memo.md → better scripts. The system improves only if they give
  feedback the first week.
- Hand them OPERATOR-HUMAN.md: that is their entire job description.

## Architecture rules (violate these and it breaks)

- The avatar video is composited by **ffmpeg**, never played inside
  Remotion — headless Chrome crashes with misleading font-timeout errors.
- Fonts are CSS @font-face data URIs; do NOT "fix" them to the FontFace API
  (hangs on Remotion's page recycling).
- Caption alignment matches each scene's first two words against the Whisper
  transcript (list-video repo scenes still open "First/Second/Third"). Scene
  openings must be distinct across scenes and never start with a digit; see
  script-skill.md §3a — transition fragments like "Now the setup" are banned.
- Never bypass `qa.py` or lower its face-headroom threshold; never let
  anything post without `qa.json: pass=true`.
- Config is layered: config.json (committed, neutral) ← config.local.json
  (gitignored: ./ then $REELS_LOCAL_CONFIG then /data/). Personal identity,
  keywords, funnel words, avatarLooks belong ONLY in the local layer.
- Intro cards support `line1`/`line2`/`logo` (claude|github|microsoft|yc|deepseek|cloudflare
  glyphs); single-repo videos must never show a generic "3 repos" card.
- `shot` scenes take per-episode screenshots (`image`: filename in the
  episode dir, prep.py inlines as data URI); label pill renders top-left.

## Operating docs

- `PIPELINE.md` — daily runbook and how the two posting systems work
- `OPERATOR.md` — guardrails if an AI agent operates the system 24/7
- `OPERATOR-HUMAN.md` — the owner's 10-minute daily workflow
- `CLONING.md` — spinning up an instance for a teammate or client
- `GOLDIE-NOTES.md` — the content strategy research this system encodes
- `FUNNEL.md` — the comment-keyword → DM → email monetization playbook
