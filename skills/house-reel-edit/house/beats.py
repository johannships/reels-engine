"""The beat sheet: one JSON file per reel, written by the agent. It holds every content decision
(layouts, graphics, SFX, caption fixes, keyword); the library holds none.

Time anchors (anywhere a time is expected):
    12.4               seconds on the final timeline
    "deepline"         start of the first spoken word "deepline" (case/punctuation ignored)
    "cold outreach"    start of the first occurrence of that phrase
    "email#2"          start of the 2nd occurrence
    "email#2.end"      end of it
    "pricing+0.2"      offset in seconds (also -0.1)
    "end" / "start"    end / start of the reel

validate() enforces the house rules before anything renders (see SKILL.md "Hard rules").
"""
import re

from .common import read_json

BANNED_TYPES = {"pill", "badge", "chip", "tag", "sticker", "rec", "rec_chip", "bubble", "tag_pill", "logo_pill",
                "corner_tag", "emoji"}
BANNED_KEYS = {"pill", "badge", "chip", "sticker", "corner_tag"}

_norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())


class Anchors:
    def __init__(self, words, dur):
        self.words = words; self.dur = dur
        # hyphenated words ("go-to-market", "end-to-end") become sub-tokens that point at the same word
        self.keys, self.owner = [], []
        for i, w in enumerate(words):
            for part in re.split(r"[-\u2013\u2014/]", w["w"]):
                if _norm(part):
                    self.keys.append(_norm(part)); self.owner.append(i)
        self.missing = []

    def find(self, phrase, nth=1):
        toks = [_norm(t) for t in re.split(r"[\s\-]+", phrase) if _norm(t)]
        hits = []
        for i in range(len(self.keys) - len(toks) + 1):
            if all(self.keys[i + k] == toks[k] for k in range(len(toks))):
                if not hits or self.owner[i] != self.owner[hits[-1]]:
                    hits.append(i)
        if len(hits) < nth:  # tolerate whisper spelling drift with a prefix match
            hits = [i for i in range(len(self.keys) - len(toks) + 1)
                    if all(self.keys[i + k].startswith(toks[k][:5]) for k in range(len(toks)))]
        if len(hits) < nth:
            return None
        i = hits[nth - 1]
        return self.owner[i], self.owner[i + len(toks) - 1]

    def t(self, a, default=None):
        if a is None:
            return default
        if isinstance(a, (int, float)):
            return float(a)
        s = str(a).strip()
        m = re.match(r"^(.*?)(?:#(\d+))?(\.end)?([+-]\d*\.?\d+)?$", s)
        phrase, nth, end, off = m.group(1).strip(), int(m.group(2) or 1), bool(m.group(3)), float(m.group(4) or 0)
        if phrase in ("end", ""):
            return self.dur + off
        if phrase == "start":
            return off
        try:
            return float(phrase) + off
        except ValueError:
            pass
        r = self.find(phrase, nth)
        if r is None:
            self.missing.append(s)
            return default
        i, j = r
        return (self.words[j]["t1"] if end else self.words[i]["t0"]) + off


def load(path):
    return read_json(path)


def _walk(obj, path=""):
    if isinstance(obj, dict):
        yield path, obj
        for k, v in obj.items():
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")


def _numbers(s):
    return re.findall(r"\d[\d,.]*", str(s))


def validate(bs, words, fmt):
    """-> (errors, warnings). Errors block the render."""
    errs, warns = [], []
    spoken = " ".join(w["w"] for w in words).lower()
    spoken_nums = {n.replace(",", "").rstrip(".") for n in _numbers(spoken)}
    NUMWORDS = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8",
                "nine": "9", "ten": "10", "eleven": "11", "twelve": "12", "twenty": "20", "thirty": "30", "forty": "40",
                "fifty": "50", "hundred": "100"}
    for wd, n in NUMWORDS.items():
        if re.search(rf"\b{wd}\b", spoken):
            spoken_nums.add(n)
    measured = {str(m.get("value")) for m in bs.get("measured", [])}  # [{"value": "35%", "source": "...", "date": "..."}]
    for p, node in _walk(bs):
        t = str(node.get("type", "")).lower()
        if t in BANNED_TYPES:
            errs.append(f"{p}: element type '{t}' is banned (no floating pills, bubbles, tags, REC chips or stickers)")
        for k in node:
            if k.lower() in BANNED_KEYS:
                errs.append(f"{p}: key '{k}' is banned (pill/badge/chip/sticker)")
        if t in ("window", "ui", "screen") and node.get("illustrative", True) and not node.get("label_illustrative", True):
            errs.append(f"{p}: illustrative UI must carry its ILLUSTRATIVE label")
        # numbers on screen must be spoken or measured
        for key in ("text", "title", "sub", "value", "label", "lines", "items", "word"):
            if key not in node:
                continue
            vals = node[key] if isinstance(node[key], list) else [node[key]]
            for v in vals:
                v = v.get("label", "") if isinstance(v, dict) else v
                for n in _numbers(v):
                    n2 = n.replace(",", "").rstrip(".")
                    if n2 not in spoken_nums and not any(n2 in m for m in measured) and not node.get("not_a_claim"):
                        errs.append(f"{p}.{key}: number '{n}' is on screen but not spoken and not in 'measured' "
                                    "(set not_a_claim:true only for step numbers like 1/2/3)")
    kw = bs.get("keyword")
    if kw:
        if _norm(kw) not in {_norm(w["w"]) for w in words} and not bs.get("keyword_flagged_to_owner"):
            errs.append(f"keyword '{kw}' is not spoken. Use the spoken keyword, or set keyword_flagged_to_owner:true "
                        "after flagging it to the owner")
    for name in bs.get("private_terms_check", []):
        warns.append(f"remember to confirm '{name}' is public before shipping")
    if fmt not in ("split", "premium"):
        errs.append(f"format must be split or premium, got {fmt}")
    return errs, warns
