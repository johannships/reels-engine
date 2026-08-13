# Cloning the engine for another creator (a teammate, a client, anyone)

Each creator gets their OWN instance: own Railway service, own volume, own
identity, own avatar/voice, own Metricool brand. Nothing is shared at
runtime, so one person's content can never leak into another's. Budget
~45 minutes per clone, mostly waiting on builds.

## What the new creator must bring

| Thing | Where they get it |
|---|---|
| HeyGen avatar + voice clone | Their HeyGen account (2-min training video + voice sample) — or a look/voice added under the maintainer's account |
| HeyGen API key + PAYG credits | HeyGen API settings (~$1/min of video) |
| LLM key | Their z.ai coding plan, or any Anthropic-compatible endpoint |
| Metricool brand with socials connected | Their Metricool account (Advanced plan for the API) — or a new brand on the maintainer's account: same METRICOOL_USER_TOKEN + METRICOOL_USER_ID, just set the new brand's METRICOOL_BLOG_ID |
| Telegram bot | @BotFather, 2 minutes; they message it once to get their chat id |

## Steps (the maintainer or their Claude Code does this)

1. **Fork/copy the repo** (or new branch per creator if Johann hosts them):
   `gh repo create <name>-reels-engine --private --template` style, or just
   clone + push to a fresh private repo they own.
2. **Personalize** `pipeline/config.json` → `identity` block (name, handle,
   positioning, audience, site, community). This changes every script's
   voice. Then `pipeline/style-memo.md` → their standing rules (keep the
   structural ones, replace the channel-specific ones — ideally mine THEIR
   past posts for what works, like we did for Johann).
3. Optional brand skin: `studio/src/theme.ts` (colors) + CtaPanel badge
   default (their handle) — 10 minutes, or keep the violet look.
4. **Railway**: new project → deploy from their repo → volume at `/data` →
   generate domain → paste env vars (list in `deploy/RAILWAY.md`; use THEIR
   avatar/voice/LLM/Telegram values and their `METRICOOL_BLOG_ID`).
5. **Verify like we did for Johann** (CLAUDE.md walks any Claude Code
   through it): one `topics.py` run watched in logs → video lands in their
   Telegram → post appears in their Metricool planner → they veto or let it
   fly.
6. **Seed their ledger**: dashboard → Covered Content → add everything
   they've already posted about recently.
7. Hand them `OPERATOR-HUMAN.md`. That's their entire job description.

## The 15-minute version once you've done it once

Fork → edit identity block → `railway init && railway up` → volume + vars →
one verification run. Steps 2-3 are the only creative work; everything else
is copy-paste. A Claude Code session pointed at the repo does all of it —
that's what CLAUDE.md is for.

## Multi-creator ops note

If Johann's team operates all instances: each creator gets their own
Telegram bot but alerts can share one group chat; dashboards are separate
URLs (separate tokens/passwords). Keep repos separate per creator once they
customize — a shared "engine core" upstream repo + per-creator forks with
`git pull upstream` is the clean pattern when the fleet grows past ~3.
