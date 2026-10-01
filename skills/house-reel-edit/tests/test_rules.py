"""Rule tests: the validator refuses banned elements and unspoken numbers, and the no-pill detector
fires on a floating pill but not on the house caption box, a progress bar or a card.
Run: python3 tests/test_rules.py   (needs numpy, pillow, opencv-python-headless; no fonts, no video)"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from house import beats, qa  # noqa: E402

WORDS = [{"w": w, "t0": i * 0.3, "t1": i * 0.3 + 0.25} for i, w in enumerate(
    "most people skip this comment check and seven replied".split())]


def test_validator():
    bad = {"scenes": [{"elements": [{"type": "pill", "text": "FREE"}]}], "keyword": "CHECK"}
    errs, _ = beats.validate(bad, WORDS, "split")
    assert any("banned" in e for e in errs), errs
    nums = {"scenes": [{"elements": [{"type": "title", "text": "40% faster"}]}], "keyword": "CHECK"}
    errs, _ = beats.validate(nums, WORDS, "split")
    assert any("'40%'" in e or "number '40" in e for e in errs), errs
    spoken = {"scenes": [{"elements": [{"type": "title", "text": "7 replied"}]}], "keyword": "CHECK"}
    errs, _ = beats.validate(spoken, WORDS, "split")
    assert not errs, errs
    kw = {"scenes": [], "keyword": "SHIP"}
    errs, _ = beats.validate(kw, WORDS, "split")
    assert any("not spoken" in e for e in errs), errs
    errs, _ = beats.validate(dict(kw, keyword_flagged_to_owner=True), WORDS, "split")
    assert not errs, errs


def _canvas():
    im = Image.new("RGB", (1080, 1920), (238, 236, 235))
    return im, ImageDraw.Draw(im)


def _text(d, x, y, n=8):
    for k in range(n):  # fake glyph strokes
        d.rectangle([x + k * 22, y, x + k * 22 + 12, y + 26], fill=(255, 255, 255))


def test_pill_detector():
    im, d = _canvas()
    d.rounded_rectangle([300, 400, 700, 466], radius=33, fill=(31, 30, 29)); _text(d, 340, 420, 14)
    assert qa.pill_candidates(np.asarray(im)), "a floating pill must be detected"
    im, d = _canvas()
    d.rounded_rectangle([260, 632, 820, 717], radius=10, fill=(56, 52, 59)); _text(d, 290, 660, 20)   # caption box
    d.rounded_rectangle([140, 960, 940, 1010], radius=25, fill=(210, 110, 81))                     # progress bar
    d.rounded_rectangle([110, 200, 970, 400], radius=20, fill=(255, 255, 255)); _text(d, 200, 280, 20)  # card
    assert not qa.pill_candidates(np.asarray(im)), qa.pill_candidates(np.asarray(im))


if __name__ == "__main__":
    test_validator(); test_pill_detector(); print("ok")
