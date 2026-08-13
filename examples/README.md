# Examples

`demo-episode/` is a real episode (a video that ran on @johannships) with
its research.json and script.json committed, so you can see the exact data
shapes the pipeline produces and previews the graphics **without any
credentials**:

## Preview the graphics template (no API keys needed)

```
cd studio && npm install && npm run dev
```

Remotion Studio opens with sample data — scrub through the intro card,
repo card, kinetic panel, and CTA scenes. Colors/fonts live in
`studio/src/theme.ts`.

## Render this episode's graphics canvas (no API keys needed)

```
mkdir -p episodes/demo-episode
cp examples/demo-episode/* episodes/demo-episode/
cd studio && npx remotion render RepoRadar ../episodes/demo-episode/canvas.mp4 \
  --props=../examples/demo-episode/props.preview.json
```

The full pipeline (voice, captions, QA) needs the credentials from
CLAUDE.md stages 1-4 — this demo is just the visual layer.

## Data shapes

- `research.json` — what research.py/topics.py/watch.py emit
- `script.json` — what scriptgen.py emits and heygen.py/prep.py consume.
  Scene types: `intro` (line1/line2/logo), `repo`, `topic`, `shot`
  (screenshot + label), `kinetic` (full-frame text), `avatar`, `isen`,
  `cta`. `"avatarId"` at the top level pins a specific HeyGen look for
  this episode; otherwise `video.avatarLooks` rotates.
