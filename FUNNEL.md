# Funnels

## Funnel 1: New follower → lead magnet → email list → Skool

The moment someone follows, they're at peak interest — this flow converts
that into an owned email + a Skool pitch, automatically.

```
New IG follower
  → DM 1 (instant): welcome + offer, ask them to REPLY with a keyword
      (the reply opens Meta's 24h window + trains engagement)
  → they reply "TOOLKIT"
  → DM 2: Beehiiv landing link (magnet delivered BY EMAIL → they join the list)
      + a question ("what are you building?") to keep the window open
  → Day 2-3 follow-up: value nudge + Skool pitch (weekly calls, systems)
  → Beehiiv nurture continues by email forever (weekly repo drops)
```

### ManyChat build steps (~20 min)
1. Automation → New Automation → trigger **"User follows you"** (Instagram,
   Pro plan). If the follows-trigger isn't available on your account yet,
   fallback: run the same flow off a comment keyword on every reel
   ("comment TOOLKIT") — same messages, same result.
2. **DM 1** (send instantly on follow):
   > yo, thanks for the follow 🤝 I post the 3 hottest AI repos every day
   > plus how people are actually making money with them.
   >
   > I put the full toolkit in one doc: the 20 AI tools I use, my $0→$1M
   > stack, and the system that makes my videos for me.
   >
   > Want it? Reply **TOOLKIT** and I'll send it over.
3. **Keyword condition**: reply contains "toolkit" → **DM 2**:
   > here you go 👉 {beehiiv-landing-link}?utm_source=ig&utm_medium=dm&utm_campaign=follow
   >
   > grab it there — I'll also send you the 3 best repos of the week, every
   > week. no fluff.
   >
   > quick q so I know what to send you: what are you building right now?
4. **Smart Delay 2 days** → condition: has NOT clicked Skool before → **DM 3**:
   > quick one — how'd the toolkit land?
   >
   > if you want the deeper stuff — weekly calls, the full systems (including
   > the AI that makes every video on this page) — that's all inside AI
   > Operators: {skool-link}?utm_source=ig&utm_medium=dm&utm_campaign=follow
   >
   > either way the weekly repo drops keep coming 🫡
5. Public reply variants OFF for this flow (it's DM-native, no comment).

### The lead magnet (use what already exists — ship this week, don't build)
**"The AI Money Toolkit"**: the three LinkedIn listicle graphics (20 tools /
10 AI employees / one-person stack) + a 1-page "how I'd start" note, delivered
as a Beehiiv welcome email. Beehiiv landing page = the capture. Later, the
reels-engine breakdown becomes lead magnet #2 for the "SYSTEM" campaign below.

### Compliance / deliverability notes
- Meta's 24h window: every message must end with a question or button so a
  reply re-opens it. Never send day-2+ messages without a re-engagement hook.
- Volume: ManyChat contact limits — upgrade before a viral spike, not after.
- Don't include the Skool link in DM 1 (link-in-first-message to brand-new
  followers reads as spam to Meta's filters; the keyword-reply step fixes it).

### Tracking
- UTM every link (`utm_campaign=follow` vs `=system` vs per-reel keywords).
- Weekly: followers → TOOLKIT replies → email signups → Skool joins. Four
  numbers, one row per week, in the same sheet as reel metrics.

## Funnel 2: The "SYSTEM" reel → ManyChat → long-form → Skool

Goal: the meta reel ("I automated all my content") converts commenters into
AI Operators members. Target: 100+ Skool signups from one reel cycle.

## Flow

```
Reel CTA: comment "SYSTEM"
  → ManyChat keyword automation (IG + TikTok if enabled)
      DM 1 (instant): "Here's the full breakdown 👇" + YouTube long-form link
      DM 2 (10 min later): "The actual system (code, prompts, QA setup) lives
        in AI Operators — I drop every update there: <skool link>"
  → Long-form video (already recorded): description + pinned comment → Skool
  → Skool classroom module: "The Reels Engine" (the deliverable)
```

## ManyChat setup (one-time, ~15 min)

1. ManyChat → Automation → **Instagram Comment Trigger** → select the meta
   reel post → keyword contains: `system` (also add: `System`, `SYSTEM` —
   case variants are matched automatically, but add `systems` too).
2. Action 1: reply to the comment publicly (small engagement boost):
   "sent! check your DMs 📩" — randomized variants avoid spam detection.
3. Action 2: DM with the long-form YouTube link. IMPORTANT: IG requires the
   user to have DMs open; add a fallback comment reply "DM me the word
   system if the link doesn't arrive."
4. Action 3 (Smart Delay 10-15 min): follow-up DM with the Skool link.
5. Cap: ManyChat free tier handles 1k contacts; expect to hit it if the reel
   runs — upgrade before posting, not after.

## Skool packaging (the deliverable)

The code is open source (MIT) — the community layer is NOT the code, it's
the operating: your live configs, your funnel numbers, what the metrics
taught the style memo, weekly calls, and hands-on setup help. Recommended
classroom module **"The Reels Engine — run it like I do"**:
- Section 1: the long-form breakdown video (same as YouTube, so members
  feel at home)
- Section 2: your live config walkthrough — the parts that are gitignored
  for a reason (style-memo evolution, niche keywords, funnel words)
- Section 3: setup walkthrough (point at CLAUDE.md + deploy/RAILWAY.md,
  which are written to be followed by a member or their AI)
- Section 4: changelog post each time you push meaningful updates — recurring
  reason to stay subscribed.

The repo being free is the marketing; operating knowledge is the paywall.
"The code was never the moat."

## The meta reel itself

Episode prepared at `episodes/2026-07-06-meta-system/` — script.md is ready
to paste into HeyGen; graphics (21,000-view count-up, +200 followers pill,
COMMENT "SYSTEM" end card) are configured. Post natively (not via the
automation) so you can attach the ManyChat trigger to the exact post.

**Timing tip:** post it 2-3 days after the daily automation is visibly
running — the claim "AI posts every day" should be verifiable by anyone who
scrolls your feed. Receipts culture cuts both ways.
