"""PREMIUM TALKING-HEAD format. Measured spec (28 Sep 2026 reels + the story-reel brand kit):

  Face full-frame on a face-tracked virtual camera: face box height ~19% of frame, eyes ~y 800,
  zero-phase smoothed track (no jitter), punch-ins alternate 1.00 / 1.10-1.16 on cuts, 2.2% push-in
  per shot with a 0.27 s settle. House grade (warm, 22% S-curve, soft blacks) + film grain 0.022.
  Captions: Inter 900 84 px, word-by-word pop (0.12 s ease-out-back, scale .8->1), max 3 words / 16 chars,
  centred at y 1640 (y 930 while split, between the UI and the face), one accent word per phrase (red #FF5E5A or serif italic).
  Graphics: a DARK GLASS PANEL at the top (x 60-1020 from y 206: 14-22 px backdrop blur, offwhite
  hairline), BIG TYPE BEHIND THE MATTED HEAD (person matte from rembg when installed, else a soft
  head-and-shoulders mask from the face box), SPLIT for UI demos (face slides down 470 px in 0.30 s,
  a dark illustrative window on top), end card on glass. 1-2 whips max, at chapter turns only.
  Palette: offwhite #EDF3FF type, red #FF5E5A accent, shadow (12,12,14).

No pill/badge/tag/REC/sticker drawing path exists here on purpose (Johann, 28 Sep 2026).
Tools are named with real logos (files supplied per reel) inside the glass panel, or by the caption.
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import icons
from .config import font_path

try:
    import cv2
    cv2.setNumThreads(1)
except ImportError:  # pragma: no cover
    cv2 = None

W, H, FPS = 1080, 1920, 30
OFF = (237, 243, 255); RED = (255, 94, 90); SHADOW = (12, 12, 14)
SPLIT_D = 470; TR = 0.30

_fc = {}


def INTER(sz, w=900):
    k = ("i", sz, w)
    if k not in _fc:
        f = ImageFont.truetype(font_path("inter"), sz)
        try:
            f.set_variation_by_axes([min(32, max(14, sz)), w])
        except Exception:
            pass
        _fc[k] = f
    return _fc[k]


def MONO(sz, w=800):
    k = ("m", sz, w)
    if k not in _fc:
        f = ImageFont.truetype(font_path("mono"), sz)
        try:
            f.set_variation_by_axes([w])
        except Exception:
            pass
        _fc[k] = f
    return _fc[k]


def SERIF(sz, w=800):
    k = ("s", sz, w)
    if k not in _fc:
        try:
            f = ImageFont.truetype(font_path("serif"), sz)
            f.set_variation_by_axes([w])
        except (SystemExit, Exception):
            f = INTER(sz, 900)   # serif accent is optional
        _fc[k] = f
    return _fc[k]


def eoc(x): x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3
def eio(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def eob(x, k=1.9): x = min(max(x, 0.0), 1.0); return 1 + (k + 1) * (x - 1) ** 3 + k * (x - 1) ** 2
def lin(t, a, b): return min(max((t - a) / max(1e-6, b - a), 0.0), 1.0)


# ------------------------------------------------------------------ look
def grade(x):
    x = x.copy()
    x[..., 0] = x[..., 0] * 1.03 + 0.008; x[..., 1] *= 1.005; x[..., 2] *= 0.94
    np.clip(x, 0, 1, out=x)
    x = x * 0.78 + 0.22 * (x * x * (3 - 2 * x))
    lum = x @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    x = lum[..., None] + (x - lum[..., None]) * 1.04
    return np.clip(0.018 + x * 0.975, 0, 1)


def grain(img, seed, amt=0.022):
    rng = np.random.default_rng(seed)
    n = rng.standard_normal((H // 2, W // 2)).astype(np.float32)
    n = cv2.resize(n, (W, H), interpolation=cv2.INTER_LINEAR)   # half-res noise: film-like and 4x cheaper
    n /= (n.std() + 1e-6)
    lum = img @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    w = 0.6 + 0.4 * lum * (1 - lum) * 4
    return np.clip(img + (n * amt * w)[..., None], 0, 1)


def over(dst, rgb, a):
    return dst * (1 - a[..., None]) + rgb * a[..., None]


def screen(dst, rgb):
    return 1 - (1 - dst) * (1 - np.clip(rgb, 0, 1))


def newlay():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def paste_layer(img, lay, opacity=1.0, glow=None, shadow=None):
    """Composite an RGBA PIL layer onto a float image, only inside the layer's bbox (cheap)."""
    arr = np.asarray(lay); al = arr[..., 3]
    ys = np.flatnonzero(al.max(1)); xs = np.flatnonzero(al.max(0))
    if len(ys) == 0 or opacity <= 0:
        return img
    pad = 4
    if shadow:
        pad = max(pad, int(3 * shadow[0] + abs(shadow[2])) + 2)
    if glow:
        pad = max(pad, int(3 * glow[0]) + 2)
    y0, y1 = max(0, ys[0] - pad), min(H, ys[-1] + 1 + pad); x0, x1 = max(0, xs[0] - pad), min(W, xs[-1] + 1 + pad)
    sub = arr[y0:y1, x0:x1].astype(np.float32) / 255.0
    a = sub[..., 3] * opacity
    reg = img[y0:y1, x0:x1]
    if shadow:
        r, k, dy = shadow
        reg = reg * (1 - (cv2.GaussianBlur(np.roll(a, int(dy), axis=0), (0, 0), r) * k)[..., None])
    if glow:
        r, k, c = glow
        reg = screen(reg, np.array(c, np.float32)[None, None] / 255.0 * (cv2.GaussianBlur(a, (0, 0), r) * k)[..., None])
    img = img.copy(); img[y0:y1, x0:x1] = over(reg, sub[..., :3], a)
    return img


def transform_layer(lay, scale=1.0, center=None, rot=0):
    center = center or (W / 2, H / 2)
    M = cv2.getRotationMatrix2D((float(center[0]), float(center[1])), rot, scale)
    arr = np.asarray(lay).astype(np.float32); pre = arr.copy(); pre[..., :3] *= pre[..., 3:4] / 255.0
    o = cv2.warpAffine(pre, M, (W, H), flags=cv2.INTER_LINEAR)
    o[..., :3] = o[..., :3] / np.maximum(o[..., 3:4] / 255.0, 1e-4)
    return Image.fromarray(np.clip(o, 0, 255).astype(np.uint8), "RGBA")


def glass(img, x0, y0, pw, ph, a, r=44, tint=0.02, blur=20, k=0.32, outline=100):
    """Dark frosted glass: blurred, darkened backdrop + an offwhite hairline. A PANEL, never a pill."""
    x0, y0, pw, ph = int(x0), int(y0), int(pw), int(ph)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + pw), min(H, y0 + ph)
    if xb <= xa or yb <= ya or a <= 0:
        return img
    pm = Image.new("L", (pw, ph), 0); ImageDraw.Draw(pm).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=r, fill=255)
    pm = np.asarray(pm).astype(np.float32)[ya - y0:yb - y0, xa - x0:xb - x0] / 255 * a
    sub = img[ya:yb, xa:xb]
    g = cv2.GaussianBlur(sub, (0, 0), blur) * k + np.array([tint, tint, tint * 1.2], np.float32)
    img = img.copy(); img[ya:yb, xa:xb] = over(sub, g, pm)
    bl = newlay()
    ImageDraw.Draw(bl).rounded_rectangle([x0, y0, x0 + pw - 1, y0 + ph - 1], radius=r, outline=OFF + (outline,), width=2)
    return paste_layer(img, bl, opacity=a)


def top_dim(img, amt, reach=0.36):
    if amt <= 0:
        return img
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    return img * (1 - amt * np.clip(1 - (yy - 0.04) / reach, 0, 1) ** 1.5)


def whip(img, p, direction):
    sh = -W * 0.55 * p ** 2 if direction == "out" else W * 0.55 * (1 - p) ** 2
    vel = 2 * p if direction == "out" else 2 * (1 - p)
    o = cv2.warpAffine(img, np.float32([[1, 0, sh], [0, 1, 0]]), (W, H), borderMode=cv2.BORDER_REFLECT)
    L = int(8 + 150 * vel)
    o = cv2.filter2D(o, -1, np.ones((1, L), np.float32) / L, borderType=cv2.BORDER_REFLECT)
    return np.clip(o * (1 + 0.10 * vel), 0, 1)


# ------------------------------------------------------------------ person matte for big type behind the head
_rembg = None


def person_matte(img_u8, face_box_px):
    """Soft person matte 0..1 (H, W). rembg (isnet) when installed; otherwise a head-and-shoulders
    mask built from the face box (good enough for big type that sits above and beside the head)."""
    global _rembg
    if _rembg is None:
        try:
            from rembg import new_session, remove
            _rembg = (new_session("isnet-general-use"), remove)
        except Exception:
            _rembg = False
    if _rembg:
        s, remove = _rembg
        m = remove(Image.fromarray(img_u8), session=s, only_mask=True)
        return np.asarray(m).astype(np.float32) / 255
    cx, cy, fw, fh = face_box_px
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    top = cy - 0.85 * fh; chin = cy + 0.55 * fh
    d.ellipse([cx - 0.66 * fw, top, cx + 0.66 * fw, chin + 0.05 * fh], fill=255)
    d.rectangle([cx - 0.36 * fw, chin - 0.2 * fh, cx + 0.36 * fw, chin + 0.6 * fh], fill=255)
    d.polygon([(cx - 0.4 * fw, chin + 0.35 * fh), (cx + 0.4 * fw, chin + 0.35 * fh), (cx + 1.9 * fw, chin + 1.3 * fh),
               (cx + 2.2 * fw, H), (cx - 2.2 * fw, H), (cx - 1.9 * fw, chin + 1.3 * fh)], fill=255)
    return cv2.GaussianBlur(np.asarray(m).astype(np.float32) / 255, (0, 0), 6)


# ------------------------------------------------------------------ elements
def _rows_panel(img, el, t):
    """Dark glass panel at the top with rows that go active -> done on spoken words.
    el: title, items [{label, sub?, at, done, logo?}], counter {label, values:[{v, at}]}, x0, y0, w."""
    at = el["at"]; until = el.get("until", 1e9)
    amt = eio(lin(t, at, at + TR)) * (1 - eio(lin(t, until - TR, until)))
    if amt <= 0.001:
        return img
    items = el["items"]; RH = el.get("row_h", 122); HEAD = 92
    x0, y0, cw = el.get("x0", 60), el.get("y0", 206) + 70 * (1 - eoc(amt)), el.get("w", 960)
    ch = HEAD + RH * len(items) + 26
    img = glass(img, x0, y0, cw, ch, eoc(amt))
    lay = newlay(); d = ImageDraw.Draw(lay)
    hx, hy = x0 + 44, y0 + 50
    d.ellipse([hx, hy - 7, hx + 14, hy + 7], fill=RED + (255,)); xx = hx + 30
    for c in el.get("title", "").upper():
        d.text((xx, hy), c, font=MONO(28, 700), fill=OFF + (220,), anchor="lm"); xx += MONO(28, 700).getlength(c) + 5
    if el.get("counter"):
        vals = [v for v in el["counter"]["values"] if t >= v["at"]]
        if vals:
            d.text((x0 + cw - 44, hy), f"{el['counter'].get('label', '')} {vals[-1]['v']}".strip(), font=MONO(28, 700),
                   fill=OFF + (200,), anchor="rm")
    d.line([(x0 + 30, y0 + HEAD), (x0 + cw - 30, y0 + HEAD)], fill=OFF + (40,), width=2)
    y = y0 + HEAD
    for i, r in enumerate(items):
        act_t, done_t = r.get("at", at), r.get("done", 1e9)
        is_done = t >= done_t; is_act = act_t <= t < done_t
        cyr = y + RH / 2 + 4
        if is_act:
            hl = eoc(lin(t, act_t, act_t + 0.25))
            d.rounded_rectangle([x0 + 18, y + 10, x0 + cw - 18, y + RH - 6], radius=26, fill=RED + (int(26 * hl),),
                                outline=RED + (int(120 * hl),), width=2)
        dim = 255 if (is_act or is_done) else 120
        d.text((x0 + 50, cyr), f"{i + 1:02d}", font=MONO(34, 700), fill=(RED if (is_act or is_done) else OFF) + (dim,), anchor="lm")
        tx = x0 + 130
        if r.get("logo"):
            lg = Image.open(r["logo"]).convert("RGBA"); lg.thumbnail((56, 56), Image.LANCZOS)
            if not (is_act or is_done):
                lg.putalpha(lg.split()[3].point(lambda v: int(v * 0.45)))
            lay.alpha_composite(lg, (int(tx), int(cyr - 22 - lg.height / 2))); tx += lg.width + 16
        d.text((tx, cyr - (22 if r.get("sub") else 0)), r["label"], font=INTER(54, 900), fill=OFF + (dim,), anchor="lm")
        if r.get("sub"):
            d.text((x0 + 131, cyr + 28), r["sub"], font=INTER(32, 500), fill=OFF + (int(dim * 0.62),), anchor="lm")
        sx, sy, sr = x0 + cw - 78, cyr, 30
        if is_done:
            k = eob(lin(t, done_t, done_t + 0.22), 2.0); rr = sr * (0.6 + 0.4 * k)
            d.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], fill=RED + (255,))
            if t > done_t + 0.05:
                d.line([(sx - 13, sy + 1), (sx - 4, sy + 11), (sx + 14, sy - 11)], fill=(255, 255, 255, 255), width=7, joint="curve")
        elif is_act:
            ang = (t * 360 * 1.4) % 360
            d.arc([sx - sr + 4, sy - sr + 4, sx + sr - 4, sy + sr - 4], 0, 360, fill=OFF + (50,), width=6)
            d.arc([sx - sr + 4, sy - sr + 4, sx + sr - 4, sy + sr - 4], ang, ang + 100, fill=RED + (255,), width=6)
        else:
            d.ellipse([sx - sr + 4, sy - sr + 4, sx + sr - 4, sy + sr - 4], outline=OFF + (70,), width=4)
        if i < len(items) - 1:
            d.line([(x0 + 40, y + RH), (x0 + cw - 40, y + RH)], fill=OFF + (26,), width=2)
        y += RH
    return paste_layer(img, lay, opacity=eoc(amt), shadow=(14, 0.35, 6))


def _big_type_layer(el, t):
    at, until = el["at"], el.get("until", el["at"] + 1.4)
    a = lin(t, at, at + 0.30)
    if a <= 0 or t >= until:
        return None, 0
    op = eoc(a) * (1 - eio(lin(t, until - 0.25, until)))
    lay = newlay(); d = ImageDraw.Draw(lay)
    size = el.get("size", 520)
    f = INTER(size, 900)
    while f.getlength(el["text"]) > W * 0.96 and size > 120:
        size -= 20; f = INTER(size, 900)
    c = RED if el.get("color") == "red" else OFF
    d.text((540, el.get("y", 470)), el["text"], font=f, fill=c + (255,), anchor="mm")
    if el.get("strike_at") is not None and t >= el["strike_at"]:
        p = eoc(lin(t, el["strike_at"], el["strike_at"] + 0.25)); w_ = f.getlength(el["text"])
        x0 = 540 - w_ / 2; d.line([(x0, el.get("y", 470) + 20), (x0 + w_ * p, el.get("y", 470) - 60 * p + 20)], fill=RED + (255,), width=28)
    sc = 1.18 - 0.18 * eoc(a)
    return transform_layer(lay, scale=sc, center=(540, el.get("y", 470))), op


def _end_card(img, el, t):
    t0 = el["at"]; a = eoc(lin(t, t0, t0 + 0.5))
    if a <= 0:
        return img
    img = top_dim(img, 0.40 * a)
    cw, chh = 900, 360; x0, y0 = (W - cw) // 2, int(206 + 80 * (1 - a))
    img = glass(img, x0, y0, cw, chh, a)
    lay = newlay(); d = ImageDraw.Draw(lay)
    x, y = x0 + 56, y0 + 64
    d.ellipse([x, y - 7, x + 14, y + 7], fill=RED + (255,)); xx = x + 30
    for ch in el.get("label", "COMMENT THE WORD"):
        d.text((xx, y), ch, font=MONO(32, 800), fill=OFF + (255,), anchor="lm"); xx += MONO(32, 800).getlength(ch) + 6
    kk = lin(t, t0 + 0.25, t0 + 0.55)
    kl = newlay(); fk = INTER(150, 900); kw = el["keyword"].upper()
    ImageDraw.Draw(kl).text((x0 + 56, y0 + 180), kw, font=fk, fill=RED + (255,), anchor="lm")
    if kk > 0:
        kl = transform_layer(kl, scale=1.3 - 0.3 * eob(kk, 2.2), center=(x0 + 56 + fk.getlength(kw) / 2, y0 + 180))
    if el.get("line"):
        fsz = 58
        while SERIF(fsz, 800).getlength(el["line"]) > cw - 112 and fsz > 30:
            fsz -= 2
        d.text((x0 + 56, y0 + 295), el["line"], font=SERIF(fsz, 800), fill=OFF + (255,), anchor="lm")
    bx, by = x0 + cw - 150, y0 + 180
    icons.glyph(d, "chat", bx - 70, by - 70, 140, OFF + (230,), 7)
    img = paste_layer(img, lay, opacity=a, shadow=(14, 0.4, 6))
    if kk > 0:
        img = paste_layer(img, kl, opacity=a * min(1, kk * 4), glow=(22, 0.45, RED), shadow=(14, 0.45, 8))
    return img


def _title(img, el, t):
    at, until = el["at"], el.get("until", 1e9)
    a = eoc(lin(t, at, at + 0.3)) * (1 - eio(lin(t, until - 0.25, until)))
    if a <= 0:
        return img
    lay = newlay(); f = INTER(el.get("size", 110), 900)
    ImageDraw.Draw(lay).text((540, el.get("y", 420)), el["text"], font=f, fill=(RED if el.get("color") == "red" else OFF) + (255,), anchor="mm")
    lay = transform_layer(lay, scale=0.85 + 0.15 * eob(lin(t, at, at + 0.3)), center=(540, el.get("y", 420)))
    img = top_dim(img, 0.3 * a)
    return paste_layer(img, lay, opacity=a, glow=(18, 0.35, OFF), shadow=(14, 0.45, 8))


# ------------------------------------------------------------------ captions
def caption_layer(groups, accents, t, cy):
    g = next((gg for gg in groups if gg["t0"] <= t < gg["t1"]), None)
    if not g:
        return None, None
    fs = 84; items = []
    for w in g["words"]:
        kind = accents.get(w["w"].lower().strip(".,!?"), "")
        f = SERIF(fs + 10, 800) if kind == "serif" else INTER(fs, 900)
        c = RED if kind == "red" else (255, 255, 255)
        bb = f.getbbox(w["w"]); items.append((w, f, c, bb[2] - bb[0]))
    gap = 22; lines, cur, cw = [], [], 0
    for it in items:
        add = it[3] + (gap if cur else 0)
        if cur and cw + add > 760:
            lines.append(cur); cur, cw = [], 0; add = it[3]
        cur.append(it); cw += add
    if cur:
        lines.append(cur)
    lay = newlay(); box = None
    for li, line in enumerate(lines):
        total = sum(it[3] for it in line) + gap * (len(line) - 1)
        x = 540 - total / 2; y = cy + li * 96
        box = (int(540 - total / 2), int(cy - 50), int(total), int(96 * len(lines)))
        for w, f, c, wd in line:
            age = max(t - w["t0"] + 0.03, 0.13 if g["t0"] == 0 and w is g["words"][0] else -1)
            op = min(max((age + 0.02) / 0.06, 0), 1)
            if op > 0:
                wl = newlay()
                ImageDraw.Draw(wl).text((x - f.getbbox(w["w"])[0], y), w["w"], font=f, fill=c + (int(255 * op),), anchor="lm")
                if age < 0.12:
                    wl = transform_layer(wl, scale=0.8 + 0.2 * eob(age / 0.12, 1.6), center=(x + wd / 2, y))
                lay.alpha_composite(wl)
            x += wd + gap
    return lay, box


# ------------------------------------------------------------------ camera
class Camera:
    """Virtual camera over the proxy frame from the smoothed face track."""

    def __init__(self, track_ts, track_boxes, cuts, dur, src_w, src_h, punch=(1.0, 1.12, 1.0, 1.16, 1.04, 1.13)):
        self.ts = np.array(track_ts); self.b = np.array(track_boxes)
        self.cuts = sorted(set([0.0] + [round(c, 3) for c in cuts])); self.dur = dur
        self.sw, self.sh = src_w, src_h; self.punch = punch

    def box(self, t):
        return [float(np.interp(t, self.ts, self.b[:, k])) for k in range(4)]

    def shot(self, t):
        a = 0.0; i = 0
        for k, c in enumerate(self.cuts):
            if c <= t + 1e-6:
                a = c; i = k
        nxt = [c for c in self.cuts if c > a + 1e-6]
        return i, a, (nxt[0] if nxt else self.dur)

    def matrix(self, t):
        cx, cy, fw, fh = self.box(t)
        base = float(np.clip(0.19 / max(fh, 1e-3), 1.0, 1.6))   # face box ~19% of frame height
        i, a, b = self.shot(t)
        p = self.punch[i % len(self.punch)]
        settle = 1 + 0.022 * (1 - eoc(lin(t, a, a + 0.27))) if a > 0 else 1.0
        z = base * p * settle * (1 + 0.022 * eio(lin(t, a, b)))
        s = self.sw / W / z                         # source px per output px
        fx, fy = cx * self.sw, cy * self.sh
        ox = float(np.clip(fx, 540 * s, self.sw - 540 * s)); oy = float(np.clip(fy + (960 - 800) * s, 960 * s, self.sh - 960 * s))
        M = np.float32([[1 / s, 0, 540 - ox / s], [0, 1 / s, 960 - oy / s]])
        face_px = ((fx - ox) / s + 540, (fy - oy) / s + 960, fw * self.sw / s, fh * self.sh / s)
        return M, face_px


# ------------------------------------------------------------------ renderer
class PremiumRenderer:
    """scenes: [{'t0','t1','layout':'face'|'split','transition'?,'elements':[...]}]; groups: premium caption groups."""

    def __init__(self, scenes, groups, accents, camera):
        if cv2 is None:
            raise SystemExit("premium format needs opencv-python-headless")
        self.scenes = scenes; self.groups = groups; self.accents = {k.lower(): v for k, v in (accents or {}).items()}
        self.cam = camera; self.caption_boxes = []
        self.whips = [s["t0"] for s in scenes if s.get("transition") == "whip"][:2]
        self.splits = [(s["t0"], s["t1"]) for s in scenes if s["layout"] == "split"]

    def split_amount(self, t):
        v = 0.0
        for a, b in self.splits:
            v = max(v, eio(lin(t, a, a + TR)) * (1 - eio(lin(t, b - TR, b))))
        return v

    def elements(self, t):
        for s in self.scenes:
            for el in s["elements"]:
                if el["at"] - 0.5 <= t < el.get("until", s["t1"]) + 0.5:
                    yield s, el

    def frame(self, t, src_u8):
        M, face_px = self.cam.matrix(t)
        src = src_u8.astype(np.float32) / 255.0
        img = cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_AREA if M[0, 0] < 1 else cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        img = grade(img)
        els = list(self.elements(t))
        # big type behind the head
        for s, el in els:
            if el["type"] == "behind_head":
                lay, op = _big_type_layer(el, t)
                if lay is not None:
                    m = person_matte((img * 255).astype(np.uint8), face_px)
                    img = img * (1 - 0.30 * op * (1 - m)[..., None])
                    base = img.copy()
                    img = paste_layer(img, lay, opacity=op * 0.97, glow=(26, 0.5, OFF), shadow=(30, 0.45, 18))
                    img = over(img, base, m)
        amt = self.split_amount(t)
        if amt > 0:
            D = SPLIT_D * eio(amt)
            face = cv2.warpAffine(img, np.float32([[1, 0, 0], [0, 1, D]]), (W, H), borderMode=cv2.BORDER_REFLECT)
            bg = cv2.resize(cv2.GaussianBlur(cv2.resize(img, (W // 4, H // 4)), (0, 0), 6), (W, H)) * (1 - 0.55 * amt)
            yy = np.arange(H, dtype=np.float32)[:, None, None]
            Y = -300 + (900 + 300) * eio(amt)
            mk = np.clip((yy - Y) / 180, 0, 1)
            img = bg * (1 - mk) + face * mk
        for s, el in els:
            typ = el["type"]
            if typ == "glass_panel":
                img = _rows_panel(img, el, t)
            elif typ == "title":
                img = _title(img, el, t)
            elif typ == "end_card":
                img = _end_card(img, el, t)
            elif typ == "window" and amt > 0:
                from . import split as sp
                lay = Image.new("RGBA", (W, 900), (0, 0, 0, 0))
                el2 = dict(el); el2.setdefault("y", 470); el2.setdefault("h", 600)
                sp.draw_element(lay, el2, t, 900)
                full = newlay(); full.alpha_composite(lay, (0, 0))
                img = paste_layer(img, full, opacity=eoc(amt), shadow=(14, 0.35, 6))
            elif typ in ("behind_head",):
                pass
            elif typ not in ("window",):
                raise ValueError(f"unknown premium element '{typ}'")
        for wt in self.whips:
            if wt - 0.18 <= t < wt:
                img = whip(img, lin(t, wt - 0.18, wt), "out")
            elif wt <= t < wt + 0.18:
                img = whip(img, lin(t, wt, wt + 0.18), "in")
        cy = 1640 + (930 - 1640) * eio(amt)   # while split: between the UI and the face, never on the chin
        cap, box = caption_layer(self.groups, self.accents, t, cy)
        if cap is not None:
            img = paste_layer(img, cap, shadow=(12, 0.55, 6))
        self.caption_boxes.append(box)
        img = grain(img, seed=int(t * FPS) * 7 + 3)
        return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
