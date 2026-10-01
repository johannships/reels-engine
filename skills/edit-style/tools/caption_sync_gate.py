"""Per-chapter caption sync gate against a re-whisper of the FINAL render.

usage: python3 caption_sync_gate.py captions.json final_words.json chapters.json
  captions.json     the words as burned on screen: [{"w": "Claude", "t": 1.23}, ...]  (t = when it appears)
  final_words.json  word stamps from re-transcribing final.mp4: [{"w": "claude", "s": 1.20}, ...]
                    (mlx-whisper large-v3-turbo, word_timestamps=True; whisper.cpp small drifts 0.1-0.4 s)
  chapters.json     [[0, 7.3, "hook"], [7.3, 14.9, "story"], ...]

Gate per chapter: median <= 0.12 s and p95 <= 0.25 s. Exit 1 on any FAIL.
On a fail: retime that chapter's cues to the final words, re-render only those frames, run again.
"""
import difflib
import json
import sys

MEDIAN_MAX, P95_MAX = 0.12, 0.25


def norm(w):
    return "".join(c for c in w.lower() if c.isalnum())


def pct(v, q):
    v = sorted(v)
    k = (len(v) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


def main(cap_p, fin_p, chap_p):
    cap = json.load(open(cap_p))
    fin = json.load(open(fin_p))
    chapters = json.load(open(chap_p))
    sm = difflib.SequenceMatcher(a=[norm(c["w"]) for c in cap], b=[norm(f["w"]) for f in fin], autojunk=False)
    pairs = [(cap[b.a + k], fin[b.b + k]) for b in sm.get_matching_blocks() for k in range(b.size)]
    ok = True
    for c0, c1, name in chapters:
        d = [abs(c["t"] - f["s"]) for c, f in pairs if c0 <= f["s"] < c1]
        if not d:
            print(f"{name:<12} n= 0  no matched words  FAIL")
            ok = False
            continue
        med, p95 = pct(d, 0.5), pct(d, 0.95)
        res = "PASS" if med <= MEDIAN_MAX and p95 <= P95_MAX else "FAIL"
        ok &= res == "PASS"
        print(f"{name:<12} n={len(d):>2}  median {med:.3f}s  p95 {p95:.3f}s  {res}")
    print(f"matched {len(pairs)}/{len(cap)} caption words (unmatched words need a look)")
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    sys.exit(main(*sys.argv[1:]))
