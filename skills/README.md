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

| Skill | What it does |
|-------|--------------|
| **edit-style** | Turn a raw talking-head take into a dynamically-edited vertical reel — full-face / full-graphic / split layouts, generated graphic cards, word-synced captions, ducked music. The "looks like an editor made it" style, from code. |
| **reels-engine** | Drive the whole automated pipeline conversationally — trending-topic proposals, script approval, clone render, QA-gated edit, schedule-only posting. |

More get added as the machine grows. Contributions welcome — see
`../CONTRIBUTING.md`.
