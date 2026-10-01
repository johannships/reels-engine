"""SPLIT-GRAPHIC format (light panel top / face bottom). Measured spec (28 Sep 2026 reels):

  canvas 1080x1920 @30. SPLIT: graphic panel y 0-680 (#EEECEB + 1 px grid #E4E2E0 at 90 px pitch),
  face panel y 680-1894 (hard edge, no rounded corners, no glow seam), face head-top ~10% / chin ~66% of panel.
  FULL GRAPHIC: whole frame is the grid canvas, voice continues. No face-only layout.
  Panel safe area y 220-660, x 60-1020 (IG UI covers the top ~220 px). Full safe area y 220-1620.
  Cuts between layouts are HARD. Elements inside animate in: pop (scale .9->1 ease-out-back 1.6, 0.30 s)
  or slide from the left (ease-out-cubic). Something new lands in the panel about every 1.3 s.
  Captions: JetBrains Mono 800, 52 px, ALL CAPS, +6 px tracking, white on #38343B @95%, radius 10,
  28x18 px padding, box centred on y 675 (straddles the seam), hard swap, hidden for the first
  0.35 s of a full-graphic shot. Face panel gets the house grade only (no grain). Face is static (no push-ins).
  Palette: terracotta #D26E51 accent, ink #1F1E1D, grey #6B6B6B, red #E5484D (strike/stamp), green #22A55B.

No pill/badge/tag drawing path exists here on purpose (Johann, 28 Sep 2026: floating pills read as AI slop).
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from . import icons
from .config import font_path

W, H, FPS = 1080, 1920, 30
PANEL_H, FACE_Y, FACE_H = 680, 680, 1214     # videotoolbox needs even sizes
CAP_Y = 675
BG, GRIDC = (238, 236, 235), (228, 226, 224)
COL = {"terra": (210, 110, 81), "ink": (31, 30, 29), "grey": (107, 107, 107), "white": (255, 255, 255),
       "red": (229, 72, 77), "green": (34, 165, 91), "capbox": (56, 52, 59), "light": (222, 219, 216),
       "line": (205, 200, 196), "dark": (31, 30, 29)}
S = 2  # supersample for sprites


def col(c):
    if isinstance(c, (list, tuple)):
        return tuple(c)
    if isinstance(c, str) and c.startswith("#"):
        return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
    return COL.get(c or "ink", COL["ink"])


_fc = {}


def F(kind, size, wt):
    k = (kind, size, wt)
    if k not in _fc:
        f = ImageFont.truetype(font_path("inter" if kind == "inter" else "mono"), size)
        try:
            f.set_variation_by_axes([min(32, max(14, size // S)), wt] if kind == "inter" else [wt])
        except Exception:
            pass
        _fc[k] = f
    return _fc[k]


def grid(h):
    im = Image.new("RGB", (W, h), BG); d = ImageDraw.Draw(im)
    for x in range(0, W, 90):
        d.line([(x, 0), (x, h)], fill=GRIDC, width=1)
    for y in range(0, h, 90):
        d.line([(0, y), (W, y)], fill=GRIDC, width=1)
    return im


PANEL_BG = None
FULL_BG = None


def _bgs():
    global PANEL_BG, FULL_BG
    if PANEL_BG is None:
        PANEL_BG = grid(PANEL_H).convert("RGBA"); FULL_BG = grid(H).convert("RGBA")


# ------------------------------------------------------------------ sprites
_sp = {}


def _finish(im):
    return im.resize((im.width // S, im.height // S), Image.LANCZOS)


def _shadowed(im, pad=18, op=0.10):
    a = im.split()[3]
    sh = Image.new("RGBA", (im.width + pad * 2 * S, im.height + pad * 2 * S), (0, 0, 0, 0))
    m = Image.new("L", sh.size, 0); m.paste(a, (pad * S, pad * S + 8 * S))
    m = m.filter(ImageFilter.GaussianBlur(12 * S)).point(lambda v: int(v * op))
    sh.putalpha(m); sh.alpha_composite(im, (pad * S, pad * S))
    return sh


def _mdraw():
    return ImageDraw.Draw(Image.new("L", (1, 1)))


def tile(icon, label=None, sub=None, color="terra", size=150, dotted=False, highlight=False):
    k = ("tile", icon, label, sub, str(color), size, dotted, highlight)
    if k in _sp:
        return _sp[k]
    s = size * S
    lf = F("inter", 32 * S, 650); sf = F("mono", 24 * S, 800)
    tw = max([s] + [_mdraw().textlength(t, font=f) for t, f in ((label, lf), (sub, sf)) if t])
    wd = int(tw) + 8 * S + (24 * S if highlight else 0)
    hh = s + (54 * S if label else 0) + (36 * S if sub else 0) + (24 * S if highlight else 0)
    im = Image.new("RGBA", (wd, hh), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x0 = (wd - s) // 2; y0 = 12 * S if highlight else 0
    if highlight:
        d.rounded_rectangle([x0 - 12 * S, 0, x0 + s + 12 * S, s + 24 * S], radius=36 * S, outline=COL["ink"], width=5 * S)
    if dotted:
        d.rounded_rectangle([x0, y0, x0 + s, y0 + s], radius=28 * S, outline=(180, 176, 172), width=4 * S)
        for i in range(3):
            cx = x0 + s * (.28 + i * .22)
            d.ellipse([cx - 7 * S, y0 + s / 2 - 7 * S, cx + 7 * S, y0 + s / 2 + 7 * S], fill=(160, 156, 152))
    else:
        d.rounded_rectangle([x0, y0, x0 + s, y0 + s], radius=28 * S, fill=col(color))
        icons.glyph(d, icon, x0 + s * .18, y0 + s * .18, s * .64)
    y = y0 + s + 10 * S + (12 * S if highlight else 0)
    if label:
        d.text(((wd - d.textlength(label, font=lf)) / 2, y), label, font=lf, fill=COL["grey"]); y += 44 * S
    if sub:
        d.text(((wd - d.textlength(sub, font=sf)) / 2, y), sub, font=sf, fill=COL["ink"])
    out = _finish(_shadowed(im) if not dotted else im); _sp[k] = out
    return out


def text_sprite(text, size, kind="inter", wt=850, color="ink", track=0):
    k = ("txt", text, size, kind, wt, str(color), track)
    if k in _sp:
        return _sp[k]
    f = F(kind, size * S, wt); d0 = _mdraw()
    bb = f.getbbox(text or " ")
    tw = sum(d0.textlength(ch, font=f) + track * S for ch in text) if track else d0.textlength(text, font=f)
    im = Image.new("RGBA", (int(tw) + 6 * S, bb[3] + 8 * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if track:
        x = 0
        for ch in text:
            d.text((x, 0), ch, font=f, fill=col(color)); x += d.textlength(ch, font=f) + track * S
    else:
        d.text((0, 0), text, font=f, fill=col(color))
    out = _finish(im); _sp[k] = out
    return out


def label_sprite(text, size=32, color="grey"):
    """Small spaced-mono header line ("THE TOOL", "COMMENT THIS WORD"). Plain text, never boxed."""
    return text_sprite(text.upper(), size, "mono", 700, color, track=3)


def card_sprite(key, w, h, draw_fn, fill="white", radius=20):
    k = ("card", key)
    if k in _sp:
        return _sp[k]
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=radius * S, fill=col(fill))
    draw_fn(im, d)
    out = _finish(_shadowed(im)); _sp[k] = out
    return out


def image_sprite(path, w, radius=20):
    k = ("img", path, w)
    if k in _sp:
        return _sp[k]
    im = Image.open(path).convert("RGBA")
    h = int(im.height * w / im.width)
    im = im.resize((w * S, h * S), Image.LANCZOS)
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=radius * S, fill=255)
    a = np.minimum(np.asarray(im.split()[3]), np.asarray(m)); im.putalpha(Image.fromarray(a))
    out = _finish(_shadowed(im)); _sp[k] = out
    return out


def logo_sprite(path, size=150, label=None):
    """A real logo (official file supplied per reel, never shipped in the repo) on a white tile."""
    k = ("logo", path, size, label)
    if k in _sp:
        return _sp[k]
    s = size * S
    lg = Image.open(path).convert("RGBA"); lg.thumbnail((int(s * .66), int(s * .66)), Image.LANCZOS)
    lf = F("inter", 32 * S, 650)
    wd = int(max(s, _mdraw().textlength(label, font=lf) if label else 0)) + 8 * S
    im = Image.new("RGBA", (wd, s + (54 * S if label else 0)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x0 = (wd - s) // 2
    d.rounded_rectangle([x0, 0, x0 + s, s], radius=28 * S, fill=COL["white"])
    im.alpha_composite(lg, (x0 + (s - lg.width) // 2, (s - lg.height) // 2))
    if label:
        d.text(((wd - d.textlength(label, font=lf)) / 2, s + 10 * S), label, font=lf, fill=COL["grey"])
    out = _finish(_shadowed(im)); _sp[k] = out
    return out


# ------------------------------------------------------------------ animation
def ease_back(x, s=1.6):
    x = min(max(x, 0), 1) - 1
    return 1 + x * x * ((s + 1) * x + s)


def ease_cubic(x):
    x = min(max(x, 0), 1); return 1 - (1 - x) ** 3


def place(cv, spr, cx, cy, t0, t, anim="pop", dur=0.30):
    if spr is None or t < t0:
        return
    p = (t - t0) / dur; im = spr; a = 1.0; dx = 0
    if anim == "pop" and p < 1:
        sc = 0.9 + 0.1 * ease_back(p)
        im = spr.resize((max(1, int(spr.width * sc)), max(1, int(spr.height * sc))), Image.BILINEAR)
        a = min(1, p * 3.3)
    elif anim == "slide" and p < 1:
        dx = -(1 - ease_cubic(p)) * 140; a = min(1, p * 3)
    if a < 1:
        im = im.copy(); im.putalpha(im.split()[3].point(lambda v: int(v * a)))
    cv.alpha_composite(im, (int(round(cx - im.width / 2 + dx)), int(round(cy - im.height / 2))))


def line_draw(d, pts, t0, t, dur, color, width):
    if t < t0:
        return
    p = ease_cubic((t - t0) / dur) if dur > 0 else 1
    seg = list(zip(pts[:-1], pts[1:])); L = [math.dist(a, b) for a, b in seg]; run = p * sum(L)
    for (a, b), l in zip(seg, L):
        if run <= 0:
            break
        if l == 0:
            continue
        f = min(1, run / l)
        d.line([tuple(a), (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)], fill=color, width=width)
        run -= l


def arrow(d, a, b, color, width=8, head=20):
    d.line([tuple(a), tuple(b)], fill=color, width=width)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for s_ in (2.6, -2.6):
        d.line([tuple(b), (b[0] + head * math.cos(ang + s_), b[1] + head * math.sin(ang + s_))], fill=color, width=width)


# ------------------------------------------------------------------ elements
def _typed(txt, t, a, b):
    if t < a:
        return ""
    return txt if t >= b else txt[: int(len(txt) * (t - a) / max(1e-3, b - a))]


def draw_element(cv, el, t, region_h):
    """el has resolved times (at, until, ...). Positions are in region pixels (panel: 0-680, full: 0-1920)."""
    typ = el["type"]; at = el["at"]; anim = el.get("anim", "pop")
    if t < at or t >= el.get("until", 1e9):
        return
    cx = el.get("x", 540); cy = el.get("y", 440 if region_h == PANEL_H else 900)
    d = ImageDraw.Draw(cv)
    if typ == "title":
        place(cv, text_sprite(el["text"], el.get("size", 72), "inter", el.get("weight", 850), el.get("color", "ink")), cx, cy, at, t, anim)
    elif typ == "label":
        place(cv, label_sprite(el["text"], el.get("size", 32), el.get("color", "grey")), cx, cy, at, t, el.get("anim", "slide"))
    elif typ == "tile":
        place(cv, tile(el["icon"], el.get("label"), el.get("sub"), el.get("color", "terra"), el.get("size", 150),
                       el.get("dotted", False), el.get("highlight", False)), cx, cy, at, t, anim)
    elif typ == "tiles":
        items = el["items"]; n = len(items); size = el.get("size", 170)
        xs = el.get("xs") or [int(W / 2 + (i - (n - 1) / 2) * el.get("gap", 330)) for i in range(n)]
        for i, it in enumerate(items):
            ti = it.get("at", at + i * el.get("stagger", 0.12))
            if el.get("arrows") and i < n - 1 and t >= ti + 0.2:
                arrow(d, (xs[i] + size * .62, cy - 10), (xs[i + 1] - size * .62, cy - 10), (180, 176, 172), 8, 18)
            place(cv, tile(it.get("icon", "dots"), it.get("label"), it.get("sub"), it.get("color", "terra"), size,
                           it.get("dotted", False), it.get("highlight", False)), xs[i], cy, ti, t, anim)
            if it.get("check_at") is not None:
                place(cv, tile("check", color="green", size=72), xs[i] + size * .45, cy - size * .6, it["check_at"], t)
    elif typ == "grid":
        n = el["n"]; cols = el.get("cols", min(n, 4)); size = el.get("size", 120)
        rows = math.ceil(n / cols); gx, gy = el.get("gap_x", 230), el.get("gap_y", 230)
        labels = el.get("labels", [None] * n); hi = el.get("highlight"); hi_at = el.get("highlight_at", 1e9)
        for i in range(n):
            r, c = divmod(i, cols)
            x = cx + (c - (cols - 1) / 2) * gx; y = cy + (r - (rows - 1) / 2) * gy
            is_hi = hi is not None and i == hi and t >= hi_at
            spr = tile(el.get("icon", "agent"), labels[i] if i < len(labels) else None, color=el.get("color", "terra"),
                       size=size, highlight=is_hi)
            if hi is not None and t >= hi_at and not is_hi:
                spr = spr.copy(); spr.putalpha(spr.split()[3].point(lambda v: int(v * 0.3)))
            place(cv, spr, x, y, at + i * el.get("stagger", 0.05), t, anim)
    elif typ == "card":
        w_, h_ = el.get("w", 860), el.get("h", 200)
        key = ("card", el.get("title"), el.get("sub"), el.get("icon"), w_, h_, str(el.get("fill")), el.get("title_size"), el.get("sub_size"))

        def fn(im, dd, el=el, w_=w_, h_=h_):
            x = 44 * S
            if el.get("icon"):
                ib = min(120, h_ - 80); iy = (h_ - ib) / 2
                dd.rounded_rectangle([44 * S, iy * S, (44 + ib) * S, (iy + ib) * S], radius=int(ib * 0.22) * S,
                                     fill=col(el.get("icon_color", "terra")))
                icons.glyph(dd, el["icon"], (44 + ib * .17) * S, (iy + ib * .17) * S, ib * .66 * S); x = (44 + ib + 34) * S
            tsz = el.get("title_size", 64); ssz = el.get("sub_size", 26)
            ft = F("inter", tsz * S, 850); fs = F("mono", ssz * S, 700)
            tb = ft.getbbox(el.get("title", "") or " "); th = tb[3] - tb[1]
            sh = (fs.getbbox("HG")[3] - fs.getbbox("HG")[1] + ssz * 0.6 * S) if el.get("sub") else 0
            y = (h_ * S - th - sh) / 2 - tb[1]
            dd.text((x, y), el.get("title", ""), font=ft, fill=col(el.get("color", "ink")))
            if el.get("sub"):
                dd.text((x + 3 * S, y + tb[3] + ssz * 0.6 * S), el["sub"].upper(), font=fs, fill=COL["grey"])
        place(cv, card_sprite(key, w_, h_, fn, el.get("fill", "white")), cx, cy, at, t, anim)
    elif typ == "image":
        place(cv, image_sprite(el["path"], el.get("w", 900)), cx, cy, at, t, anim)
    elif typ == "logo":
        place(cv, logo_sprite(el["path"], el.get("size", 150), el.get("label")), cx, cy, at, t, anim)
    elif typ == "strike":
        a, b = el.get("from", [210, 590]), el.get("to", [870, 290])
        line_draw(d, [a, b], at, t, el.get("dur", 0.0), col(el.get("color", "red")), el.get("width", 16))
    elif typ == "arrow":
        a, b = el["from"], el["to"]
        if t >= at + el.get("dur", 0.3) * 0.8:
            arrow(d, a, b, col(el.get("color", "terra")), el.get("width", 10), 22)
        else:
            line_draw(d, [a, b], at, t, el.get("dur", 0.3), col(el.get("color", "terra")), el.get("width", 10))
    elif typ == "line":
        line_draw(d, el["points"], at, t, el.get("dur", 0.4), col(el.get("color", "terra")), el.get("width", 8))
    elif typ == "progress":
        x0, w_ = el.get("x0", 140), el.get("w", 800); p = ease_cubic((t - at) / el.get("dur", 0.6))
        d.rounded_rectangle([x0, cy - 25, x0 + w_, cy + 25], radius=25, fill=COL["light"])
        d.rounded_rectangle([x0, cy - 25, x0 + max(50, int(w_ * p)), cy + 25], radius=25, fill=col(el.get("color", "terra")))
    elif typ == "stamp":
        # a rotated outline word ON a card (never floating over the face); at most one per reel
        spr = text_sprite(el["text"].upper(), el.get("size", 64), "mono", 800, el.get("color", "red"), track=4)
        box = Image.new("RGBA", (spr.width + 40, spr.height + 30), (0, 0, 0, 0))
        ImageDraw.Draw(box).rounded_rectangle([2, 2, box.width - 3, box.height - 3], radius=8, outline=col(el.get("color", "red")), width=6)
        box.alpha_composite(spr, (20, 12))
        place(cv, box.rotate(el.get("rot", 8), expand=True, resample=Image.BICUBIC), cx, cy, at, t, "pop", 0.2)
    elif typ == "window":
        _window(cv, el, t, cx, cy)
    elif typ == "checklist":
        _checklist(cv, el, t, cx, cy)
    elif typ == "comment_cta":
        _comment(cv, el, t, cy)
    else:
        raise ValueError(f"unknown split element '{typ}'")


def _window(cv, el, t, cx, cy):
    """Dark app window with typed lines. Illustrative unless it is a real capture -> labelled."""
    w_, h_ = el.get("w", 960), el.get("h", 400); at = el["at"]
    key = ("win", el.get("title", ""), w_, h_, el.get("illustrative", True))

    def fn(im, dd):
        dd.rectangle([0, 60 * S, w_ * S, 62 * S], fill=(60, 57, 55))
        for i, c in enumerate(((236, 106, 94), (244, 190, 80), (98, 197, 84))):
            dd.ellipse([(28 + i * 32) * S, 22 * S, (46 + i * 32) * S, 40 * S], fill=c)
        dd.text((150 * S, 16 * S), el.get("title", ""), font=F("mono", 28 * S, 700), fill=(170, 165, 160))
        if el.get("illustrative", True):
            lab = "ILLUSTRATIVE"; f = F("mono", 22 * S, 800)
            dd.text(((w_ - 30) * S - dd.textlength(lab, font=f), 20 * S), lab, font=f, fill=(150, 145, 140))
    place(cv, card_sprite(key, w_, h_, fn, "dark"), cx, cy, at, t, el.get("anim", "pop"))
    if t < at + 0.25:
        return
    d = ImageDraw.Draw(cv); x0 = cx - w_ / 2; y0 = cy - h_ / 2
    f = F("mono", el.get("font_size", 36), 650); fn_ = F("mono", 28, 800)
    lines = el.get("lines", []); ph = el.get("placeholder")
    if ph and (not lines or t < lines[0]["at"]):
        s = _typed(ph, t, at + 0.25, at + 0.25 + len(ph) * 0.045)
        d.text((x0 + 100, y0 + 112), s, font=f, fill=(120, 116, 112))
    for i, ln in enumerate(lines):
        if t < ln["at"]:
            break
        a, b = ln["at"], ln.get("until", ln["at"] + len(ln["text"]) * 0.05)
        y = y0 + 112 + i * 92
        if el.get("numbered", True):
            d.rounded_rectangle([x0 + 30, y - 4, x0 + 78, y + 44], radius=10, fill=COL["terra"] if t < b else COL["green"])
            d.text((x0 + 45, y + 3), str(i + 1), font=fn_, fill=COL["white"])
        s = _typed(ln["text"], t, a, b)
        d.text((x0 + 100, y), s, font=f, fill=(236, 233, 229))
        if t < b and int(t * 4) % 2 == 0:
            cxp = x0 + 100 + d.textlength(s, font=f) + 4
            d.rectangle([cxp, y + 2, cxp + 16, y + 42], fill=COL["terra"])


def _checklist(cv, el, t, cx, cy):
    """Light card: rows tick green on their spoken words. Optional counter line on the header ("ROUND 3")."""
    items = el["items"]; w_ = el.get("w", 900); rh = el.get("row_h", 84); at = el["at"]
    h_ = 90 + rh * len(items) + 20
    x0 = cx - w_ / 2; y0 = cy - h_ / 2
    key = ("chk", el.get("title", ""), w_, h_)
    place(cv, card_sprite(key, w_, h_, lambda im, dd: dd.text((40 * S, 30 * S), el.get("title", "").upper(),
          font=F("mono", 28 * S, 800), fill=COL["grey"])), cx, cy, at, t, el.get("anim", "pop"))
    if t < at + 0.2:
        return
    d = ImageDraw.Draw(cv)
    if el.get("counter"):
        vals = [v for v in el["counter"]["values"] if t >= v["at"]]
        if vals:
            s = f"{el['counter'].get('label', '')} {vals[-1]['v']}".strip()
            f = F("mono", 30, 800); d.text((x0 + w_ - 40 - d.textlength(s, font=f), y0 + 34), s, font=f, fill=COL["terra"])
    for i, it in enumerate(items):
        y = y0 + 90 + i * rh; act = t >= it.get("at", at); done = t >= it.get("done", 1e9)
        c = COL["ink"] if act else (190, 186, 182)
        bx = x0 + 40
        if done:
            d.rounded_rectangle([bx, y + 10, bx + 52, y + 62], radius=12, fill=COL["green"])
            icons.glyph(d, "check", bx + 6, y + 16, 40, COL["white"], 6)
        else:
            d.rounded_rectangle([bx, y + 10, bx + 52, y + 62], radius=12, outline=(200, 196, 192), width=4)
        d.text((bx + 80, y + 12), it["label"], font=F("inter", 44, 750), fill=c)


def _comment(cv, el, t, cy):
    """CTA: spaced-mono 'COMMENT THIS WORD', a comment field with the keyword typing in, then a DM card."""
    at = el["at"]; kw = el["keyword"].upper(); d = ImageDraw.Draw(cv)
    place(cv, label_sprite(el.get("label", "COMMENT THIS WORD"), 32, "terra"), 540, cy - 178, at, t, "slide")

    def box(im, dd):
        dd.rounded_rectangle([0, 0, 760 * S - 1, 110 * S - 1], radius=20 * S, outline=(200, 196, 192), width=3 * S)
        dd.text((600 * S, 32 * S), "Post", font=F("inter", 38 * S, 750), fill=COL["terra"])
    place(cv, card_sprite(("cbox",), 760, 110, box, radius=20), 540, cy - 90, at, t)
    ta = el.get("type_at", at + 0.4)
    n = 0 if t < ta else min(len(kw), int((t - ta) / 0.07) + 1)
    f = F("mono", 58, 800)
    if n:
        d.text((200, cy - 122), kw[:n], font=f, fill=COL["ink"])
    if t < ta + len(kw) * 0.07 + 0.3 and int(t * 4) % 2 == 0:
        x = 200 + d.textlength(kw[:n], font=f) + 6; d.rectangle([x, cy - 116, x + 6, cy - 56], fill=COL["terra"])
    if el.get("dm_text") and t >= el.get("dm_at", 1e9):
        def dm(im, dd):
            dd.rounded_rectangle([24 * S, 22 * S, 104 * S, 102 * S], radius=24 * S, fill=COL["terra"])
            icons.glyph(dd, "dm", 40 * S, 38 * S, 48 * S)
            dd.text((128 * S, 34 * S), el["dm_text"], font=F("inter", 40 * S, 750), fill=COL["ink"])
        place(cv, card_sprite(("dm", el["dm_text"]), 760, 124, dm), 540, cy + 90, el["dm_at"], t, "slide")


# ------------------------------------------------------------------ captions (mono box on the seam)
def cap_sprite(text):
    k = ("cap", text)
    if k in _sp:
        return _sp[k]
    f = F("mono", 52 * S, 800); tr = 6 * S; d0 = _mdraw()
    tw = sum(d0.textlength(ch, font=f) for ch in text) + tr * (len(text) - 1)
    bb = f.getbbox("HQ")
    w_, h_ = int(tw + 56 * S), 85 * S
    im = Image.new("RGBA", (w_, h_), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w_ - 1, h_ - 1], radius=10 * S, fill=COL["capbox"] + (242,))
    x = 28 * S; y = (h_ - (bb[3] - bb[1])) / 2 - bb[1]
    for ch in text:
        d.text((x, y), ch, font=f, fill=COL["white"]); x += d0.textlength(ch, font=f) + tr
    out = _finish(im); _sp[k] = out
    return out


# ------------------------------------------------------------------ grade (house grade, face only)
def grade_u8(u8):
    x = u8.astype(np.float32) / 255.0
    x[..., 0] = x[..., 0] * 1.03 + 0.008; x[..., 1] *= 1.005; x[..., 2] *= 0.94
    np.clip(x, 0, 1, out=x)
    x = x * 0.78 + 0.22 * (x * x * (3 - 2 * x))
    lum = x @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    x = lum[..., None] + (x - lum[..., None]) * 1.04
    x = 0.018 + x * 0.975
    return (np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8)


# ------------------------------------------------------------------ frame
class SplitRenderer:
    """scenes: [{'t0','t1','layout':'split'|'full','elements':[...]}] (times resolved);
    cues: caption chunks; crops: per-output-frame (x0,y0,cw,ch) on the proxy frame."""
    needs_matte = False

    def __init__(self, scenes, cues):
        _bgs()
        self.scenes = scenes; self.cues = cues
        self.caption_boxes = []

    def scene(self, t):
        for s in self.scenes:
            if s["t0"] <= t < s["t1"]:
                return s
        return self.scenes[-1]

    def frame(self, t, face_u8):
        s = self.scene(t)
        if s["layout"] == "full":
            cv = FULL_BG.copy()
            for el in s["elements"]:
                draw_element(cv, el, t, H)
        else:
            cv = Image.new("RGBA", (W, H), BG + (255,))
            panel = PANEL_BG.copy()
            for el in s["elements"]:
                draw_element(panel, el, t, PANEL_H)
            cv.alpha_composite(panel, (0, 0))
            cv.paste(Image.fromarray(grade_u8(face_u8)), (0, FACE_Y))
        box = None
        for c in self.cues:
            if c["t0"] <= t < c["t1"]:
                if s["layout"] == "full" and 0 <= t - s["t0"] < 0.35 and s["t0"] > 0:
                    break  # let the graphic land
                sp = cap_sprite(c["text"]); x, y = (W - sp.width) // 2, CAP_Y - sp.height // 2
                cv.alpha_composite(sp, (x, y)); box = (x, y, sp.width, sp.height)
                break
        self.caption_boxes.append(box)
        return np.asarray(cv.convert("RGB"))
