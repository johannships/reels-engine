> **Author's context notes** — kept for transparency, not needed for setup. Start at CLAUDE.md.

# Reverse-engineering the winners (Goldie, Nate Herk, @johannships)

## Nate Herk (@nateherk, data pulled 2026-07-05 — 17k-160k views/short)

The lesson is **ecosystem niching**: Claude Code appears in nearly every
title. Top: "Google's New Tool Just Solved A Major Claude Code Problem"
(160k), "How I Build $10,000 Apple-Style Websites with Claude Code" (144k),
"How to Use Claude Code for 99% CHEAPER" (102k). Formula: one owned keyword
(Claude Code) × money number ($10k, 99% cheaper) × how-to/problem-solution ×
tool combos (X + Y). His IG mixes motion graphics with high-quality real
screenshots — now our ShotPanel.
**Applied:** topics.py boosts Claude-Code/agent-ecosystem topics
(config `topics.priorityKeywords`); the how-to combo angle is mandatory in
topic beat 2.

# Julian Goldie's shorts (data pulled 2026-07-05)

Sample: 60 most recent shorts from youtube.com/@JulianGoldieSEO/shorts with
view counts (via yt-dlp). Baseline views ~2-6K; outliers noted.

## What actually drives his views (ranked by outliers)

1. **Challenger vs incumbent** — "NEW GLM 5.2 DESTROYS Claude?" (32K, his #1),
   "Kimi K2.7: China's new AI DESTROYS Claude?" (8.6K), "Hermes MoA DESTROYS
   Fable 5?" (6.8K). Question-mark framing, David-vs-Goliath.
2. **FREE + open source** — "Ornith-1.0 is INSANE (FREE + Local + Open
   Source)!" (21K), "New Chinese AI Model Is INSANE! (FREE & Open Source)"
   (15K), "This NEW Chinese AI Agent…(FREE + Open Source)" (11K). The parens
   qualifier "(FREE + Open Source)" is practically a view multiplier.
3. **Big-name update news** — "NEW GPT 5.6 is INSANE!" (18K), "NEW Gemini 3.5
   Pro is INSANE!" (16K). Newsjacking model releases within hours.
4. **His own product woven in** — ~15% of shorts are his agent (Hermes):
   version updates, "run it FREE", integrations. Audience doesn't punish it;
   it converts. Cyndra should get the same rotation slot.

## Title formulas (frequency order)
- `NEW {thing} is INSANE!` / `{thing} Update is INSANE!` (default)
- `{challenger} DESTROYS/BEATS {incumbent}?` (best performer)
- `This NEW {category} is INSANE! (FREE + Open Source)`
- `{thing} Just Changed {category} Forever` / `Changes Everything`
- Drama variants: `LEAKS`, `BANNED`, `coming?`, `Just Broke the Internet`

## Cadence
Multiple shorts per day, 7 days/week. Volume + speed on news > polish.

## How we adopt it (encoded in config + scriptgen)
- **Structure yes, wording configurable.** Johann's brand voice bans hype
  words in the SCRIPT (still true). For TITLES, `posting.titleStyle` supports:
  - `goldie`: literal formulas (INSANE/DESTROYS caps energy)
  - `operator`: same structure, receipts wording ("GLM 5.2 just beat Claude
    on SWE-bench — and it's free")
  Let analyze.py + view data decide which wins; don't argue taste, A/B it.
- **Topic engine already matches**: his best performers (open-source models,
  agents, Chinese challengers) all surface on GitHub trending — which is our
  research source. The `spotlight` daily series exists precisely for the
  single-topic challenger/free angle.
- **Cyndra rotation**: 1-2 spotlight slots/week go to Cyndra features or
  Cyndra-adjacent workflows, same as Hermes in his feed.
- **Speed**: breakout watcher (2h) is our version of his newsjacking.

## SOP round 2 (2026-07-07): editing rules + the tutorial format

Absorbed into the skills: first frame = the thumbnail (hook text readable at
frame one); visuals must match the spoken words moment to moment; no music in
shorts (his measured result); 30-40s zone; benefit-driven Title Case titles
("How I Cut My Dev Costs by 95%") — never generic-AI fluff ("...Unveiled!");
specific varied hashtags, never #fyp-type.

FUTURE SERIES (his highest-watch-time format, not built yet): **tool
tutorial screencasts** — record a raw screen walkthrough of a workflow, AI
writes the structured script from the recording (Gemini/Claude maps each
step), avatar voice + screencast edited together, notes + JSON dropped in
Skool as the lead magnet. This is the natural long-form/Skool-content arm of
the engine and reuses the whole pipeline except the visual source.
