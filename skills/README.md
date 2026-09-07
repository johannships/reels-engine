# Skills

Drop-in [Claude Code skills](https://docs.claude.com/en/docs/claude-code/skills)
for the pieces of this machine. Each folder is one skill: a `SKILL.md` an agent
reads and follows. Grab the one you need — you don't have to run the whole
pipeline.

## How to use one

Point your agent at a skill and tell it to use it:

```
> use the edit-style skill in skills/edit-style to edit this take: raw.mov
```

Or install it into your own project so it's always available:

```
cp -r skills/edit-style ~/.claude/skills/
```

Then any agent in that project can invoke it by name.

## The skills

| Skill | Stage | What it does |
|-------|-------|--------------|
| **reel-ideation** | Ideation | Find PROVEN ideas: scan competitors for outliers vs their own channel median, steal the idea never the script, and pass every candidate through the ownership gate before anything gets made. |
| **signal-scout** | Ideation / research | Scan supplied sources (comments, transcripts, docs, communities) and return a ranked, evidence-backed list of audience signals with sources attached. Emits signal-report.md. |
| **content-strategist** | Ideation / selection | Score signals against your audience, offer, and proof. Picks the few worth making, says why it rejected the rest. Emits strategy-memo.md. |
| **brief-builder** | Pre-production | Turn one chosen angle into a record-ready brief: hook options, outline, the proof each section needs, and a claim ledger. |
| **reel-scriptwriting** | Creation | Write the spoken script: 10-word hooks, five curiosity engines, banned openers, anti-AI-slop register, verbatim one-word CTAs. |
| **edit-style** | Editing | Turn a raw talking-head take into a dynamically-edited vertical reel: layout switching, generated graphic cards, word-synced captions, blur-reveal gesture graphics, platform safe zones, QA gates. |
| **reels-engine** | Autopilot | Drive the whole automated pipeline conversationally: trending proposals, script approval, clone render, QA-gated edit, schedule-only posting with a human approval gate. |

The first six work completely standalone in Claude Code (or any agent that
reads markdown skills) — no VPS, no pipeline, no API keys. The last one
drives the full automated system in this repo.

**The workflow in order:** reel-ideation (or signal-scout ->
content-strategist for research-driven pieces) -> brief-builder ->
reel-scriptwriting -> you record -> edit-style.
