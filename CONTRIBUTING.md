# Contributing

This repo is the live engine I run my own channel on every day — not a
community project with maintainers. That shapes how contributions work:

- **Only I can push.** Forks are the intended way to make it yours: fork,
  put your identity in `pipeline/config.local.json`, and run your own
  instance. You never need a PR merged to use this fully.
- **PRs are welcome but merged conservatively.** A change lands only if it
  helps every instance (bug fixes, portability, docs) and I've run it on my
  own machine for a few days first. Niche-specific features belong in your
  fork's local layer, not here.
- **Issues**: bug reports with logs are gold. "It doesn't work" without the
  failing command's output will be closed with love.
- **Never include secrets or personal config in a PR** — CI blocks
  `.env`, `config.local.json`, and anything matching common key patterns,
  and I will not review around a red X.

The fastest way to get help: open Claude Code in the repo and ask it —
CLAUDE.md and the operating docs are written for exactly that.
