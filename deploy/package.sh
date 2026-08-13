#!/usr/bin/env bash
# Build shareable zips (no secrets — .env/episodes are untracked by design).
#   reels-engine-full.zip    the whole system (Skool deliverable)
#   reels-engine-skills.zip  just the agent skills + docs (for agent users)
set -euo pipefail
cd "$(dirname "$0")/.."
git archive --format=zip HEAD -o reels-engine-full.zip
zip -qj reels-engine-skills.zip \
  HERMES.md CLAUDE.md OPERATOR.md OPERATOR-HUMAN.md CLONING.md \
  PIPELINE.md FUNNEL.md GOLDIE-NOTES.md pipeline/script-skill.md \
  pipeline/style-memo.md
echo "built: reels-engine-full.zip ($(du -h reels-engine-full.zip | cut -f1))"
echo "built: reels-engine-skills.zip ($(du -h reels-engine-skills.zip | cut -f1))"
