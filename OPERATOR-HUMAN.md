# Running the Reels Engine — human operator guide

You're operating an automated content machine. It researches, writes, films
(AI avatar), edits, QA-checks, and schedules 2-3 short videos every day.
Your job is NOT to make content. Your job is taste and veto: catch the ~5%
the machine gets wrong before the world sees it.

Time cost: ~10 minutes/day + 20 minutes on Sunday.

## Your three surfaces

1. **Telegram (the feed).** Every finished video arrives here the moment it
   passes QA, with its title. Alerts arrive here too (breakouts, failures).
   This is your primary review surface — watch every video, on your phone,
   with sound.
2. **The dashboard (the control room).** `https://<domain>/<token>/dash`
   (password-protected). Shows: every episode's stage and QA numbers, the
   live Metricool schedule for the next 14 days, and the Covered Content
   ledger. This page answers "what's happening?" — bookmark it.
3. **Metricool planner (the veto).** Daily videos are scheduled 24h ahead —
   that delay IS the approval process. Approve = do nothing. Veto = delete
   the post in Metricool before it fires. You can also drag posts to better
   times.

## The daily loop (morning + midday, ~5 min each)

1. Video arrives in Telegram (topic reel ~06:05, repo reel ~13:05).
2. Watch it fully. Checklist:
   - Hook: does the first sentence make YOU want to keep watching?
   - Voice: sounds like you, no accent drift, natural pacing?
   - Visuals: no white/blank zones anywhere, captions synced, face never
     cropped, screenshots readable?
   - Facts: star counts / claims sane? (Numbers come from live APIs, but
     eyeball them.)
   - Title + caption (shown in dashboard/Metricool): coherent, no word
     salad, keyword present?
3. Good → do nothing. It posts itself in ~24h.
4. Bad → delete it in the Metricool planner, then write ONE line about why
   in the feedback log (see below). If it's a rendering defect (visual
   glitch), also tell the maintainer — that's a bug, not taste.
5. Breakout videos (big trend alerts) post IMMEDIATELY — you review them
   after the fact. If one misfired, delete the live posts from the
   platforms and note it.

## When you post something manually

Dashboard → Covered Content → type the subject ("meetily", "owner/repo",
"gemini leak") → **Mark covered**. Five seconds. This guarantees the
machine never repeats it. Do this EVERY time — it's the only thing the
machine can't know by itself.

## Sunday ritual (20 min) — this is how the machine gets smarter

1. Open the platform analytics (or Metricool) and find the week's best and
   worst 2-3 videos.
2. Append one line each to the feedback log — on the server:
   `/data/episodes/feedback.log` (the maintainer can give you a one-line
   command or do it for you). Format:
   `2026-07-12: hooks with dollar amounts held viewers; the Tuesday topic
   flopped, too corporate. More leaks/drama, fewer press releases.`
3. The Sunday analyzer reads this + the metrics and rewrites the style
   memo that every future script obeys. Your one line literally changes
   what the machine writes tomorrow.

## Red lines (never do these)

- Never disable or "loosen" QA to push a video through.
- Never edit `pipeline/` code — report bugs instead.
- Never let a factual error slide because the video looks good.
- Never post manually from the brand accounts without marking the subject
  covered.

## Escalate to the maintainer when

- The same QA failure happens twice in a row (systemic bug).
- Telegram goes quiet for a whole scheduled slot (worker may be down —
  check the dashboard; if it's not refreshing, say something).
- A platform flags/removes a post (policy issue — stop the schedule first,
  ask questions after).
- HeyGen/LLM/Metricool credit or auth errors appear in alerts.
