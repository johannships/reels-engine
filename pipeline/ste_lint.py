#!/usr/bin/env python3
"""Deterministic de-slop linter for spoken scripts.

Applies the SPOKEN-SAFE subset of Simplified Technical English (the aerospace
writing standard, ASD-STE100) plus an AI-slop blocklist:

  rule 2  sentence length limits (counted, not estimated)
  rule 4  active voice / imperative
  rule 9  substitution table (utilize -> use)
  rule 10 slop blocklist + em dashes

Deliberately NOT applied: one-word-one-meaning, keep-every-article, break
noun clusters, warnings-first. Those are correct for a flight manual and
wrong for a reel. Full STE strips personality by design; a script needs one.

Why a linter and not more prompt text: the model drifts past instructions.
It has paraphrased the CTA, spoken 49-star receipts, and written 40-word
sentences while being told not to. Counting words and grepping a list cannot
drift.

Usage:
    python3 ste_lint.py <file.txt|file.json>      # report violations
    python3 ste_lint.py --json <file>             # machine-readable
"""
import json, re, sys

# Rule 2 — spoken limits. A reel sentence past 20 words loses the listener.
MAX_SENTENCE_WORDS = 20
TARGET_MEAN_WORDS = 12          # advisory, reported not enforced

# Rule 9 — substitution table. Nobody says "utilize" out loud.
SUBSTITUTIONS = {
    "utilize": "use", "utilise": "use", "leverage": "use", "leveraging": "using",
    "commence": "start", "initiate": "start", "terminate": "stop",
    "accomplish": "do", "perform": "do", "execute": "run",
    "sufficient": "enough", "demonstrate": "show", "indicate": "show",
    "ensure": "make sure", "facilitate": "help", "obtain": "get",
    "require": "need", "attempt": "try", "modification": "change",
    "approximately": "about", "numerous": "many", "additional": "more",
    "prior to": "before", "subsequent to": "after", "in order to": "to",
    "additionally": "also", "furthermore": "also", "moreover": "also",
    "utilizing": "using", "possesses": "has", "purchase": "buy",
}

# Rule 10 — words that carry no information in a script.
SLOP = [
    "delve", "crucial", "comprehensive", "seamless", "seamlessly", "robust",
    "cutting-edge", "game-changer", "game changer", "landscape", "realm",
    "tapestry", "unlock", "unlocks", "elevate", "elevates", "foster",
    "streamline", "streamlines", "revolutionize", "revolutionary",
    "mind-blowing", "insane", "harness", "empower", "empowers",
    "it's important to note", "it is important to note",
    "it's worth mentioning", "in today's world", "at the end of the day",
    "let's dive in", "dive into", "in this video", "buckle up",
    "the bottom line", "needless to say",
]

# Rule 4 — passive voice. Reported as advisory: some passive is natural in
# speech, and an over-eager rewrite reads stilted. The repair pass decides.
PASSIVE = re.compile(
    r"\b(is|are|was|were|be|been|being)\s+(\w+ly\s+)?(\w+ed|written|built|made|"
    r"given|taken|shown|found|held|sold|kept|sent|done|seen|known|run)\b", re.I)

DASHES = re.compile(r"[—–]")          # em dash, en dash


def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return [p.strip() for p in parts if p.strip()]


def _words(s):
    return [w for w in re.split(r"\s+", s) if w.strip()]


def lint(text, label=""):
    """Return a list of violations. Each: (rule, severity, quote, fix)."""
    v = []
    low = " " + (text or "").lower() + " "

    for s in sentences(text):
        n = len(_words(s))
        if n > MAX_SENTENCE_WORDS:
            v.append(("rule2-length", "error", s,
                      f"{n} words, limit {MAX_SENTENCE_WORDS}. Split it."))

    for phrase, better in SUBSTITUTIONS.items():
        if re.search(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])", low):
            v.append(("rule9-substitute", "error", phrase, f'say "{better}"'))

    for word in SLOP:
        if re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", low):
            v.append(("rule10-slop", "error", word, "delete it, it carries no information"))

    if DASHES.search(text or ""):
        v.append(("rule10-dash", "error", "em/en dash",
                  "use a comma, a colon, or a full stop"))

    for m in PASSIVE.finditer(text or ""):
        v.append(("rule4-passive", "warn", m.group(0),
                  "name who does it, or make it a command"))

    if label:
        v = [(r, sev, f"[{label}] {q}", f) for r, sev, q, f in v]
    return v


def script_fields(out):
    """The spoken fields of a generated script, in delivery order.
    The CTA is excluded: it is overwritten verbatim from config downstream."""
    fields = [("hook", out.get("hook", ""))]
    for i, b in enumerate(out.get("beats") or [], 1):
        fields.append((f"beat{i}", b))
    for i, it in enumerate(out.get("items") or [], 1):
        fields.append((f"item{i}", (it or {}).get("text", "")))
    return [(k, t) for k, t in fields if t]


def lint_script(out):
    v = []
    for label, text in script_fields(out):
        v.extend(lint(text, label))
    return v


def stats(out):
    lens = [len(_words(s)) for _, t in script_fields(out) for s in sentences(t)]
    if not lens:
        return {}
    return {"sentences": len(lens), "mean_words": round(sum(lens) / len(lens), 1),
            "longest": max(lens)}


def report(violations):
    errs = [x for x in violations if x[1] == "error"]
    warns = [x for x in violations if x[1] == "warn"]
    lines = []
    for rule, sev, quote, fix in errs + warns:
        mark = "!!" if sev == "error" else " ~"
        lines.append(f"  {mark} {rule}: {quote[:80]!r} -> {fix}")
    return "\n".join(lines), len(errs), len(warns)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    if not args:
        raise SystemExit(__doc__)
    raw = open(args[0]).read()
    try:
        data = json.loads(raw)
        vs = lint_script(data) if isinstance(data, dict) else lint(raw)
        st = stats(data) if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        vs, st = lint(raw), {}
    if as_json:
        print(json.dumps({"violations": [list(x) for x in vs], "stats": st}, indent=1))
    else:
        body, e, w = report(vs)
        print(body or "  clean")
        print(f"  {e} errors, {w} warnings" + (f" | {st}" if st else ""))
    sys.exit(1 if any(x[1] == "error" for x in vs) else 0)
