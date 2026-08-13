"""Layered config: config.json (committed, neutral defaults) deep-merged
with config.local.json (gitignored, personal). Identity, avatar looks,
funnel keywords, and anything channel-specific belongs in the local file so
the public repo stays neutral. Lists and scalars replace; dicts merge."""
import json, os


def _merge(base, over):
    out = dict(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(here):
    """Local overrides are searched in order; the LAST existing file wins so
    a volume-backed config survives redeploys (containers rebuild /app from
    git, which never contains config.local.json)."""
    cfg = json.load(open(os.path.join(here, "config.json")))
    candidates = [
        os.path.join(here, "config.local.json"),
        os.environ.get("REELS_LOCAL_CONFIG") or "",
        "/data/config.local.json",
    ]
    for local in candidates:
        if local and os.path.exists(local):
            cfg = _merge(cfg, json.load(open(local)))
    return cfg
