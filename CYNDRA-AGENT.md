> **Author's context notes** — kept for transparency, not needed for setup. Start at CLAUDE.md.

# Deploying the Social Media Agent on Cyndra SaaS (dogfood → product)

The Reels Engine exposes an HTTP API, so a Cyndra-deployed agent can run the
entire stage-gated workflow with plain HTTP tools — no SSH, no keys beyond
one URL token. This is both Johann's daily driver and the template for a
sellable Cyndra vertical: "Hire an AI Social Media Manager."

## The tools (register these as custom HTTP tools on the Cyndra agent)

Base: `https://<railway-domain>/<REELS_SERVE_TOKEN>` (treat the token as the
API key; HTTPS only).

| Tool name | Method + path | Purpose |
|---|---|---|
| get_video_ideas | GET /api/menu | 5 trending ideas w/ real metrics |
| create_episode | POST /api/episodes {"menuIndex": N} | pick an idea → drafts the script |
| get_episode | GET /api/episodes/{ep} | script, QA report, render status, video URL |
| rewrite_script | POST /api/episodes/{ep}/redo {"note": "..."} | note becomes a permanent style rule + rewrite |
| render_video | POST /api/episodes/{ep}/render | ~$0.50, ~10 min, QA-gated (poll get_episode) |
| schedule_post | POST /api/episodes/{ep}/schedule {"inHours": N} | Metricool, all platforms, HARD 1-hour minimum |
| get_pending | GET /api/pending | anything the cron sensors drafted |

Hard guarantees live in the engine, not the agent: QA gates every render,
scheduling is the only publish path with a 1h+ veto gap, subjects never
repeat (ledger), spend requires an explicit render call.

## The agent prompt (paste as the Cyndra agent's instructions)

> You are the social media manager for {owner}. Your channel produces short
> AI-niche videos through the Reels Engine tools — you NEVER write or edit
> content by hand; you drive the tools and hold the conversation.
>
> Daily at {morning time}: call get_video_ideas and present the 5 ideas with
> your one-line recommendation. Wait for a pick. Then create_episode, show
> the full script, and iterate with rewrite_script until they approve —
> their notes are gold, log them faithfully. Only on an explicit "go" call
> render_video (it costs money). When the video is ready, share the videoUrl
> and wait again. Only on an explicit "post/schedule" call schedule_post.
> Confirm what was scheduled and when.
>
> If they are silent, do nothing. Unreviewed content never ships. If a step
> fails, read the log, explain it plainly, and ask before retrying anything
> that costs money.

## Deployment steps
1. Cyndra dashboard → new agent ("Riley — Social Media Manager") → paste the
   prompt → register the 7 HTTP tools above (URL + method + JSON body).
2. Connect the chat surface (Slack channel / Teams / WhatsApp) — wherever
   the eventual human operator lives all day.
3. Schedule the agent's morning trigger (Cyndra cron) → "run your daily
   idea menu."
4. Test with the 5-message flow: ideas → pick → redo → go → schedule.

## Why this is the product
One config swap (identity block + Metricool brand + avatar/voice) and this
exact agent runs for any Cyndra customer with their own engine instance
(CLONING.md). The pitch writes itself: the agent that pitched, produced, and
scheduled the video you just watched *is* the product.
