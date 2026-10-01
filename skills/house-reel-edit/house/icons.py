"""Original line icons, drawn from code (never another creator's assets or mascot).
glyph(d, name, x, y, g, col, lw) draws into the g x g box at (x, y) on an ImageDraw."""
import math

ICONS = ["agent", "mail", "db", "gauge", "key", "api", "bolt", "search", "signal", "doc", "list", "plug", "check",
         "dm", "cursor", "pencil", "image", "play", "chat", "calendar", "trend", "dots", "spark", "link", "folder",
         "book", "heart", "mic", "camera", "clock", "user", "users", "lock", "gear", "code", "terminal", "x", "cross",
         "star", "shield", "flag"]


def glyph(d, name, x, y, g, col=(255, 255, 255), lw=None, mono_font=None):
    lw = lw or max(2, int(g * 0.075))
    c = lambda a, b: (x + a * g, y + b * g)
    if name == "agent":
        d.rounded_rectangle([c(.18, .30), c(.82, .82)], radius=g * .14, outline=col, width=lw)
        d.ellipse([c(.34, .48), c(.44, .58)], fill=col); d.ellipse([c(.56, .48), c(.66, .58)], fill=col)
        d.line([c(.40, .70), c(.60, .70)], fill=col, width=lw)
        d.line([c(.5, .30), c(.5, .16)], fill=col, width=lw); d.ellipse([c(.45, .09), c(.55, .19)], fill=col)
    elif name == "mail":
        d.rounded_rectangle([c(.12, .26), c(.88, .74)], radius=g * .06, outline=col, width=lw)
        d.line([c(.14, .30), c(.5, .54), c(.86, .30)], fill=col, width=lw, joint="curve")
    elif name == "db":
        for yy in (.22, .44, .66):
            d.ellipse([c(.2, yy), c(.8, yy + .16)], outline=col, width=lw)
        d.line([c(.2, .30), c(.2, .74)], fill=col, width=lw); d.line([c(.8, .30), c(.8, .74)], fill=col, width=lw)
    elif name == "gauge":
        d.arc([c(.14, .22), c(.86, .94)], 180, 360, fill=col, width=lw)
        d.line([c(.5, .58), c(.70, .36)], fill=col, width=lw); d.ellipse([c(.45, .53), c(.55, .63)], fill=col)
        d.line([c(.14, .66), c(.86, .66)], fill=col, width=lw)
    elif name == "key":
        d.ellipse([c(.12, .34), c(.44, .66)], outline=col, width=lw)
        d.line([c(.44, .5), c(.88, .5)], fill=col, width=lw)
        d.line([c(.72, .5), c(.72, .66)], fill=col, width=lw); d.line([c(.84, .5), c(.84, .62)], fill=col, width=lw)
    elif name == "api":
        d.line([c(.36, .2), c(.26, .2), c(.26, .45), c(.16, .5), c(.26, .55), c(.26, .8), c(.36, .8)], fill=col, width=lw, joint="curve")
        d.line([c(.64, .2), c(.74, .2), c(.74, .45), c(.84, .5), c(.74, .55), c(.74, .8), c(.64, .8)], fill=col, width=lw, joint="curve")
    elif name == "bolt":
        d.polygon([c(.56, .08), c(.22, .56), c(.48, .56), c(.40, .92), c(.78, .40), c(.52, .40)], fill=col)
    elif name == "search":
        d.ellipse([c(.16, .16), c(.62, .62)], outline=col, width=lw); d.line([c(.58, .58), c(.84, .84)], fill=col, width=int(lw * 1.4))
    elif name == "signal":
        for i, hh in enumerate((.25, .45, .65)):
            d.rounded_rectangle([c(.18 + i * .24, .82 - hh), c(.34 + i * .24, .82)], radius=g * .03, fill=col)
    elif name == "doc":
        d.rounded_rectangle([c(.22, .10), c(.78, .90)], radius=g * .06, outline=col, width=lw)
        for yy in (.32, .48, .64):
            d.line([c(.34, yy), c(.66, yy)], fill=col, width=lw)
    elif name == "list":
        for yy in (.28, .5, .72):
            d.rectangle([c(.14, yy - .05), c(.24, yy + .05)], fill=col); d.line([c(.32, yy), c(.86, yy)], fill=col, width=lw)
    elif name == "plug":
        d.line([c(.38, .12), c(.38, .32)], fill=col, width=lw); d.line([c(.62, .12), c(.62, .32)], fill=col, width=lw)
        d.rounded_rectangle([c(.24, .32), c(.76, .60)], radius=g * .08, outline=col, width=lw)
        d.line([c(.5, .60), c(.5, .88)], fill=col, width=lw)
    elif name == "check":
        d.line([c(.2, .52), c(.42, .74), c(.82, .28)], fill=col, width=int(lw * 1.5), joint="curve")
    elif name == "dm":
        d.polygon([c(.12, .48), c(.88, .14), c(.62, .86), c(.48, .56)], outline=col, width=lw)
        d.line([c(.48, .56), c(.88, .14)], fill=col, width=lw)
    elif name == "cursor":
        d.polygon([c(.28, .12), c(.28, .80), c(.44, .64), c(.56, .90), c(.66, .85), c(.54, .60), c(.76, .60)], fill=col)
    elif name == "pencil":
        d.line([c(.2, .8), c(.72, .28)], fill=col, width=lw * 2)
        d.polygon([c(.14, .86), c(.3, .8), c(.2, .7)], fill=col)
    elif name == "image":
        d.rounded_rectangle([c(.16, .22), c(.84, .78)], radius=g * .05, outline=col, width=lw)
        d.polygon([c(.22, .72), c(.42, .48), c(.58, .72)], fill=col); d.ellipse([c(.62, .32), c(.74, .44)], fill=col)
    elif name == "play":
        d.rounded_rectangle([c(.14, .22), c(.86, .78)], radius=g * .12, outline=col, width=lw)
        d.polygon([c(.42, .36), c(.42, .64), c(.64, .5)], fill=col)
    elif name == "chat":
        d.rounded_rectangle([c(.14, .18), c(.86, .66)], radius=g * .1, outline=col, width=lw)
        d.polygon([c(.28, .64), c(.28, .84), c(.46, .64)], fill=col)
    elif name == "calendar":
        d.rounded_rectangle([c(.16, .22), c(.84, .84)], radius=g * .06, outline=col, width=lw)
        d.line([c(.16, .40), c(.84, .40)], fill=col, width=lw)
        for xx in (.32, .68):
            d.line([c(xx, .12), c(xx, .28)], fill=col, width=lw)
    elif name == "trend":
        d.line([c(.14, .78), c(.4, .5), c(.56, .62), c(.84, .26)], fill=col, width=lw, joint="curve")
        d.polygon([c(.88, .2), c(.66, .24), c(.84, .42)], fill=col)
    elif name == "dots":
        for i in range(3):
            d.ellipse([c(.24 + .2 * i, .44), c(.36 + .2 * i, .56)], fill=col)
    elif name == "spark":
        cx, cy = x + g / 2, y + g / 2
        for k in range(8):
            a = k * math.pi / 4; r1 = g * .1; r2 = g * (.38 if k % 2 == 0 else .28)
            d.line([(cx + r1 * math.cos(a), cy + r1 * math.sin(a)), (cx + r2 * math.cos(a), cy + r2 * math.sin(a))], fill=col, width=lw)
    elif name == "link":
        d.rounded_rectangle([c(.12, .36), c(.58, .64)], radius=g * .14, outline=col, width=lw)
        d.rounded_rectangle([c(.42, .36), c(.88, .64)], radius=g * .14, outline=col, width=lw)
    elif name == "folder":
        d.polygon([c(.14, .26), c(.42, .26), c(.5, .36), c(.86, .36), c(.86, .8), c(.14, .8)], outline=col, width=lw)
    elif name == "book":
        d.rounded_rectangle([c(.2, .14), c(.8, .86)], radius=g * .04, outline=col, width=lw)
        d.line([c(.36, .14), c(.36, .86)], fill=col, width=lw)
    elif name == "heart":
        r = .17
        d.ellipse([c(.5 - 2 * r, .3), c(.5, .3 + 2 * r)], fill=col); d.ellipse([c(.5, .3), c(.5 + 2 * r, .3 + 2 * r)], fill=col)
        d.polygon([c(.5 - 2 * r + .01, .3 + r * 1.3), c(.5 + 2 * r - .01, .3 + r * 1.3), c(.5, .84)], fill=col)
    elif name == "mic":
        d.rounded_rectangle([c(.38, .12), c(.62, .58)], radius=g * .12, fill=col)
        d.arc([c(.26, .3), c(.74, .7)], 0, 180, fill=col, width=lw); d.line([c(.5, .7), c(.5, .86)], fill=col, width=lw)
    elif name == "camera":
        d.rounded_rectangle([c(.12, .3), c(.66, .72)], radius=g * .06, outline=col, width=lw)
        d.polygon([c(.66, .46), c(.88, .32), c(.88, .7), c(.66, .56)], fill=col)
    elif name == "clock":
        d.ellipse([c(.14, .14), c(.86, .86)], outline=col, width=lw)
        d.line([c(.5, .5), c(.5, .28)], fill=col, width=lw); d.line([c(.5, .5), c(.66, .58)], fill=col, width=lw)
    elif name == "user":
        d.ellipse([c(.36, .14), c(.64, .42)], outline=col, width=lw)
        d.arc([c(.18, .5), c(.82, 1.1)], 180, 360, fill=col, width=lw)
    elif name == "users":
        for ox in (-.14, .14):
            d.ellipse([c(.38 + ox, .18), c(.62 + ox, .42)], outline=col, width=lw)
            d.arc([c(.22 + ox, .52), c(.78 + ox, 1.06)], 180, 360, fill=col, width=lw)
    elif name == "lock":
        d.rounded_rectangle([c(.22, .44), c(.78, .86)], radius=g * .06, outline=col, width=lw)
        d.arc([c(.32, .14), c(.68, .6)], 180, 360, fill=col, width=lw)
        d.line([c(.32, .37), c(.32, .44)], fill=col, width=lw); d.line([c(.68, .37), c(.68, .44)], fill=col, width=lw)
    elif name == "gear":
        cx, cy = x + g / 2, y + g / 2
        for k in range(8):
            a = k * math.pi / 4
            d.line([(cx + g * .22 * math.cos(a), cy + g * .22 * math.sin(a)), (cx + g * .38 * math.cos(a), cy + g * .38 * math.sin(a))], fill=col, width=lw * 2)
        d.ellipse([c(.24, .24), c(.76, .76)], outline=col, width=lw)
    elif name in ("code", "terminal"):
        d.rounded_rectangle([c(.12, .2), c(.88, .8)], radius=g * .06, outline=col, width=lw)
        d.line([c(.24, .38), c(.36, .5), c(.24, .62)], fill=col, width=lw, joint="curve")
        d.line([c(.44, .62), c(.62, .62)], fill=col, width=lw)
    elif name in ("x", "cross"):
        d.line([c(.24, .24), c(.76, .76)], fill=col, width=int(lw * 1.4)); d.line([c(.76, .24), c(.24, .76)], fill=col, width=int(lw * 1.4))
    elif name == "star":
        pts = []
        for k in range(10):
            r = .38 if k % 2 == 0 else .16; a = -math.pi / 2 + k * math.pi / 5
            pts.append(c(.5 + r * math.cos(a), .52 + r * math.sin(a)))
        d.polygon(pts, fill=col)
    elif name == "shield":
        d.polygon([c(.5, .12), c(.82, .24), c(.78, .6), c(.5, .88), c(.22, .6), c(.18, .24)], outline=col, width=lw)
    elif name == "flag":
        d.line([c(.24, .12), c(.24, .88)], fill=col, width=lw)
        d.polygon([c(.24, .16), c(.8, .26), c(.24, .5)], fill=col)
    else:
        raise ValueError(f"unknown icon '{name}'. Icons: {ICONS}")
