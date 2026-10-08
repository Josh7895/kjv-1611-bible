"""Draw the story pictures in art/scenes/ as small, self-hosted SVG files.

Each scene is an original drawing in a sepia engraving style, made from a
few shared shapes (hills, robed figures, waters, buildings). They ship with
the app, so every chapter has a picture even offline and no outside image
host is needed. Re-run after changing a scene:  python tools/make_scenes.py
"""
import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "art" / "scenes"
W, H = 600, 360

PAPER = "#f2e6c9"
WASH = "#e2cfa4"
MID = "#b39467"
INK = "#3a2814"
GOLD = "#b8862b"


def f(n):
    return ("%.1f" % n).rstrip("0").rstrip(".")


def pts(*xy):
    return " ".join(f(v) for v in xy)


# ---------------------------------------------------------------- shapes

def sky(top=WASH, bottom=PAPER):
    return ('<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/>'
            '</linearGradient>'
            '<pattern id="hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(35)">'
            '<line x1="0" y1="0" x2="0" y2="5" stroke="%s" stroke-width="1" opacity=".35"/></pattern>'
            '<radialGradient id="glow"><stop offset="0" stop-color="#fff8e2"/>'
            '<stop offset=".5" stop-color="#f7e7bd" stop-opacity=".8"/>'
            '<stop offset="1" stop-color="#f7e7bd" stop-opacity="0"/></radialGradient>'
            '</defs><rect width="%d" height="%d" fill="url(#sky)"/>') % (top, bottom, INK, W, H)


def glow(x, y, r):
    return '<circle cx="%s" cy="%s" r="%s" fill="url(#glow)"/>' % (f(x), f(y), f(r))


def rays(x, y, n=18, r0=30, r1=420, width=1.2, opacity=.35, start=0, end=360):
    out = []
    for i in range(n):
        a = math.radians(start + (end - start) * (i + .5) / n)
        out.append('<line x1="%s" y1="%s" x2="%s" y2="%s"/>' % (
            f(x + r0 * math.cos(a)), f(y + r0 * math.sin(a)),
            f(x + r1 * math.cos(a)), f(y + r1 * math.sin(a))))
    return '<g stroke="%s" stroke-width="%s" opacity="%s">%s</g>' % (GOLD, width, opacity, "".join(out))


def sun(x, y, r=26):
    return glow(x, y, r * 4) + '<circle cx="%s" cy="%s" r="%s" fill="#fbf1d2" stroke="%s" stroke-width="1.5"/>' % (
        f(x), f(y), f(r), GOLD) + rays(x, y, 24, r + 6, r + 40, 1.4, .6)


def moon(x, y, r=16):
    return ('<circle cx="%s" cy="%s" r="%s" fill="#fbf1d2" stroke="%s" stroke-width="1.2"/>'
            '<circle cx="%s" cy="%s" r="%s" fill="%s"/>') % (f(x), f(y), f(r), GOLD, f(x + r * .45), f(y - r * .2), f(r * .9), WASH)


def star(x, y, r=4, color=GOLD):
    p = []
    for i in range(8):
        a = math.radians(i * 45 - 90)
        rr = r if i % 2 == 0 else r * .3
        p += [x + rr * math.cos(a), y + rr * math.sin(a)]
    return '<polygon points="%s" fill="%s"/>' % (pts(*p), color)


def stars(n, seed, ymax=150):
    rnd = random.Random(seed)
    return "".join(star(rnd.uniform(20, W - 20), rnd.uniform(15, ymax), rnd.uniform(1.5, 3.5)) for _ in range(n))


def hills(y, amp, seed, fill=MID, hatch=True, bumps=4):
    rnd = random.Random(seed)
    n = bumps * 2
    xs = [i * W / n for i in range(n + 1)]
    ys = [y - (amp * rnd.uniform(.4, 1) if i % 2 else amp * rnd.uniform(0, .3)) for i in range(n + 1)]
    d = "M0 %s" % f(ys[0])
    for i in range(1, n + 1):
        mx = (xs[i - 1] + xs[i]) / 2
        d += " Q%s %s %s %s" % (f(mx), f(ys[i - 1]), f(xs[i]), f(ys[i]))
    d += " L%d %d L0 %d Z" % (W, H, H)
    s = '<path d="%s" fill="%s" stroke="%s" stroke-width="1.2"/>' % (d, fill, INK)
    if hatch:
        s += '<path d="%s" fill="url(#hatch)"/>' % d
    return s


def ground(y, fill=WASH):
    return '<rect x="0" y="%s" width="%d" height="%s" fill="%s"/><line x1="0" y1="%s" x2="%d" y2="%s" stroke="%s" stroke-width="1"/>' % (
        f(y), W, f(H - y), fill, f(y), W, f(y), INK)


def waters(y, rows=6, color=INK, amp=4, seed=1, x0=0, x1=W, fill="#d6c49c"):
    rnd = random.Random(seed)
    s = '<rect x="%s" y="%s" width="%s" height="%s" fill="%s"/>' % (f(x0), f(y), f(x1 - x0), f(H - y), fill)
    for r in range(rows):
        yy = y + 6 + r * (H - y) / rows
        d = "M%s %s" % (f(x0), f(yy))
        x = x0
        step = 18 + r * 4
        while x < x1:
            d += " q%s %s %s 0" % (f(step / 2), f(-amp - rnd.uniform(0, 2)), f(step))
            x += step
        s += '<path d="%s" fill="none" stroke="%s" stroke-width="1" opacity=".55"/>' % (d, color)
    return s


def figure(x, y, h=60, pose="stand", face=1, staff=False, robe=MID, halo=False, crown=False):
    """A robed figure standing on (x, y), h tall."""
    k = h / 60.0
    head_y = y - 52 * k
    out = []
    if halo:
        out.append('<circle cx="%s" cy="%s" r="%s" fill="#f8e9b8" stroke="%s" stroke-width="1"/>' % (
            f(x), f(head_y), f(10 * k), GOLD))
    if pose == "kneel":
        robe_d = "M%s %s Q%s %s %s %s L%s %s Q%s %s %s %s Z" % (
            f(x - 6 * k), f(y - 40 * k), f(x - 12 * k), f(y - 16 * k), f(x - 14 * k), f(y),
            f(x + 16 * k * face), f(y), f(x + 4 * k), f(y - 18 * k), f(x + 6 * k), f(y - 40 * k))
        head_y = y - 45 * k
    else:
        robe_d = "M%s %s Q%s %s %s %s L%s %s Q%s %s %s %s Z" % (
            f(x - 6 * k), f(y - 44 * k), f(x - 10 * k), f(y - 20 * k), f(x - 12 * k), f(y),
            f(x + 12 * k), f(y), f(x + 10 * k), f(y - 20 * k), f(x + 6 * k), f(y - 44 * k))
    out.append('<path d="%s" fill="%s" stroke="%s" stroke-width="1.2"/>' % (robe_d, robe, INK))
    out.append('<path d="M%s %s L%s %s" stroke="%s" stroke-width=".8" opacity=".6"/>' % (
        f(x + 2 * k * face), f(y - 38 * k), f(x + 3 * k * face), f(y - 2 * k), INK))
    sh = y - (40 if pose == "kneel" else 42) * k
    if pose == "arms_up":
        out.append('<path d="M%s %s L%s %s M%s %s L%s %s" stroke="%s" stroke-width="%s" stroke-linecap="round"/>' % (
            f(x - 5 * k), f(sh), f(x - 14 * k), f(sh - 22 * k), f(x + 5 * k), f(sh), f(x + 14 * k), f(sh - 22 * k),
            INK, f(3.2 * k)))
    elif pose in ("pray", "kneel"):
        out.append('<path d="M%s %s L%s %s L%s %s" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round"/>' % (
            f(x), f(sh + 2 * k), f(x + 9 * k * face), f(sh + 10 * k), f(x + 10 * k * face), f(sh - 2 * k), INK, f(3 * k)))
    elif pose == "reach":
        out.append('<path d="M%s %s L%s %s" stroke="%s" stroke-width="%s" stroke-linecap="round"/>' % (
            f(x + 4 * k * face), f(sh), f(x + 22 * k * face), f(sh - 6 * k), INK, f(3 * k)))
    if staff:
        sx = x + 13 * k * face
        out.append('<path d="M%s %s L%s %s q%s %s %s %s" fill="none" stroke="%s" stroke-width="%s" stroke-linecap="round"/>' % (
            f(sx), f(y), f(sx), f(y - 62 * k), f(-5 * k * face), f(-6 * k), f(-8 * k * face), f(0), INK, f(2.2 * k)))
        out.append('<path d="M%s %s L%s %s" stroke="%s" stroke-width="%s" stroke-linecap="round"/>' % (
            f(x + 4 * k * face), f(sh + 4 * k), f(sx), f(sh + 6 * k), INK, f(3 * k)))
    out.append('<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="%s" stroke-width="1.1"/>' % (
        f(x), f(head_y), f(6.5 * k), WASH, INK))
    out.append('<path d="M%s %s Q%s %s %s %s L%s %s Q%s %s %s %s Z" fill="%s" stroke="%s" stroke-width="1"/>' % (
        f(x - 7.5 * k), f(head_y + 6 * k), f(x - 8 * k), f(head_y - 9 * k), f(x), f(head_y - 8 * k),
        f(x), f(head_y - 8 * k), f(x + 8 * k), f(head_y - 9 * k), f(x + 7.5 * k), f(head_y + 6 * k), robe, INK))
    if crown:
        cy = head_y - 8 * k
        out.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width=".8"/>' % (pts(
            x - 6 * k, cy, x - 6 * k, cy - 7 * k, x - 3 * k, cy - 3 * k, x, cy - 8 * k,
            x + 3 * k, cy - 3 * k, x + 6 * k, cy - 7 * k, x + 6 * k, cy), GOLD, INK))
    return "<g>%s</g>" % "".join(out)


def crowd(x0, x1, y, n, h=34, seed=3, poses=("stand",)):
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        x = x0 + (x1 - x0) * (i + rnd.uniform(.1, .9)) / n
        out.append(figure(x, y + rnd.uniform(-4, 4), h * rnd.uniform(.85, 1.1), rnd.choice(poses),
                          face=rnd.choice((-1, 1)), robe=rnd.choice((MID, WASH, "#a3845a"))))
    return "".join(out)


def tree(x, y, h=80, kind="round"):
    k = h / 80.0
    trunk = '<path d="M%s %s L%s %s L%s %s L%s %s Z" fill="%s" stroke="%s"/>' % (
        f(x - 4 * k), f(y), f(x - 2 * k), f(y - 40 * k), f(x + 2 * k), f(y - 40 * k), f(x + 4 * k), f(y), MID, INK)
    if kind == "palm":
        out = ['<path d="M%s %s Q%s %s %s %s" fill="none" stroke="%s" stroke-width="%s"/>' % (
            f(x), f(y), f(x + 8 * k), f(y - 40 * k), f(x + 4 * k), f(y - 80 * k), INK, f(4 * k))]
        for a in (-160, -130, -100, -70, -40, -15):
            r = math.radians(a)
            ex, ey = x + 4 * k + 36 * k * math.cos(r), y - 80 * k + 36 * k * math.sin(r) + 14 * k
            out.append('<path d="M%s %s Q%s %s %s %s" fill="none" stroke="%s" stroke-width="%s"/>' % (
                f(x + 4 * k), f(y - 80 * k), f((x + 4 * k + ex) / 2), f(y - 92 * k), f(ex), f(ey), INK, f(2.4 * k)))
        return "".join(out)
    crown_ = '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s" stroke="%s" stroke-width="1.2"/>' % (
        f(x), f(y - 56 * k), f(26 * k), f(24 * k), MID, INK)
    crown_ += '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="url(#hatch)"/>' % (f(x), f(y - 56 * k), f(26 * k), f(24 * k))
    return trunk + crown_


def sheep(x, y, s=1.0):
    return ('<g><ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="#f8f0dc" stroke="%s"/>'
            '<ellipse cx="%s" cy="%s" rx="%s" ry="%s" fill="%s"/>'
            '<path d="M%s %s v%s M%s %s v%s" stroke="%s" stroke-width="%s"/></g>') % (
        f(x), f(y - 8 * s), f(12 * s), f(7 * s), INK, f(x + 12 * s), f(y - 10 * s), f(4 * s), f(3.5 * s), INK,
        f(x - 6 * s), f(y - 3 * s), f(5 * s), f(x + 6 * s), f(y - 3 * s), f(5 * s), INK, f(1.6 * s))


def tent(x, y, w=70, h=44):
    return ('<path d="M%s %s L%s %s L%s %s Z" fill="%s" stroke="%s" stroke-width="1.2"/>'
            '<path d="M%s %s L%s %s L%s %s Z" fill="%s" stroke="%s"/>') % (
        f(x - w / 2), f(y), f(x), f(y - h), f(x + w / 2), f(y), WASH, INK,
        f(x - 6), f(y), f(x), f(y - h * .45), f(x + 6), f(y), INK, INK)


def wall(x, y, w, h, crenel=True, fill=WASH):
    s = '<rect x="%s" y="%s" width="%s" height="%s" fill="%s" stroke="%s" stroke-width="1.2"/>' % (
        f(x), f(y - h), f(w), f(h), fill, INK)
    rows = int(h // 10)
    for r in range(1, rows):
        yy = y - r * 10
        s += '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width=".6" opacity=".5"/>' % (f(x), f(yy), f(x + w), f(yy), INK)
        off = 0 if r % 2 else 9
        xx = x + off
        while xx < x + w:
            s += '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width=".6" opacity=".5"/>' % (f(xx), f(yy), f(xx), f(yy + 10), INK)
            xx += 18
    if crenel:
        xx = x
        while xx < x + w - 6:
            s += '<rect x="%s" y="%s" width="8" height="8" fill="%s" stroke="%s"/>' % (f(xx), f(y - h - 8), fill, INK)
            xx += 14
    return s


def temple(x, y, w=200, h=110):
    s = '<polygon points="%s" fill="%s" stroke="%s" stroke-width="1.2"/>' % (pts(
        x - w / 2 - 8, y - h, x, y - h - 38, x + w / 2 + 8, y - h), WASH, INK)
    s += '<rect x="%s" y="%s" width="%s" height="12" fill="%s" stroke="%s"/>' % (f(x - w / 2 - 8), f(y - h), f(w + 16), MID, INK)
    cols = 6
    for i in range(cols):
        cx = x - w / 2 + 10 + i * (w - 20) / (cols - 1)
        s += '<rect x="%s" y="%s" width="12" height="%s" fill="#efe1bf" stroke="%s"/>' % (f(cx - 6), f(y - h + 12), f(h - 22), INK)
        s += '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width=".6" opacity=".5"/>' % (f(cx), f(y - h + 14), f(cx), f(y - 12), INK)
    s += '<rect x="%s" y="%s" width="%s" height="10" fill="%s" stroke="%s"/>' % (f(x - w / 2 - 14), f(y - 10), f(w + 28), MID, INK)
    return s


def boat(x, y, w=150, sail=True, tilt=0):
    s = '<path d="M%s %s Q%s %s %s %s L%s %s Q%s %s %s %s Z" fill="%s" stroke="%s" stroke-width="1.4"/>' % (
        f(x - w / 2), f(y - 18), f(x - w / 2 + 10), f(y + 6), f(x - w / 3), f(y + 6),
        f(x + w / 3), f(y + 6), f(x + w / 2 - 10), f(y + 6), f(x + w / 2), f(y - 18), MID, INK)
    s += '<path d="M%s %s L%s %s" stroke="%s" stroke-width=".8" opacity=".6"/>' % (f(x - w / 2 + 6), f(y - 8), f(x + w / 2 - 6), f(y - 8), INK)
    if sail:
        s += '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="2.4"/>' % (f(x), f(y - 18), f(x), f(y - 110), INK)
        s += '<path d="M%s %s Q%s %s %s %s L%s %s Z" fill="#f6ecd2" stroke="%s" stroke-width="1.2"/>' % (
            f(x + 2), f(y - 104), f(x + 48), f(y - 80), f(x + 40), f(y - 30), f(x + 2), f(y - 30), INK)
    if tilt:
        s = '<g transform="rotate(%s %s %s)">%s</g>' % (f(tilt), f(x), f(y), s)
    return s


def scroll(x, y, w=240, h=150, lines=7, quill=True):
    s = '<rect x="%s" y="%s" width="%s" height="%s" fill="#f7edd3" stroke="%s" stroke-width="1.4"/>' % (
        f(x - w / 2), f(y - h / 2), f(w), f(h), INK)
    for side in (-1, 1):
        cx = x + side * w / 2
        s += '<rect x="%s" y="%s" width="16" height="%s" rx="8" fill="%s" stroke="%s" stroke-width="1.2"/>' % (
            f(cx - 8), f(y - h / 2 - 10), f(h + 20), MID, INK)
    for i in range(lines):
        yy = y - h / 2 + 22 + i * (h - 40) / (lines - 1)
        ln = w - 60 - (40 if i == lines - 1 else (i * 7) % 20)
        s += '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1.6" opacity=".55" stroke-dasharray="%s"/>' % (
            f(x - w / 2 + 28), f(yy), f(x - w / 2 + 28 + ln), f(yy), INK, "14 4 22 4 9 4")
    if quill:
        s += '<path d="M%s %s Q%s %s %s %s Q%s %s %s %s Z" fill="#fbf4e0" stroke="%s" stroke-width="1.1"/>' % (
            f(x + w / 2 - 30), f(y + h / 2 + 4), f(x + w / 2 + 10), f(y - 10), f(x + w / 2 + 40), f(y - h / 2 - 20),
            f(x + w / 2 + 6), f(y - 4), f(x + w / 2 - 30), f(y + h / 2 + 4), INK)
    return s


def frame(inner):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">'
            '%s<rect x="5" y="5" width="%d" height="%d" fill="none" stroke="%s" stroke-width="2"/>'
            '<rect x="11" y="11" width="%d" height="%d" fill="none" stroke="%s" stroke-width=".8"/></svg>') % (
        W, H, W, H, inner, W - 10, H - 10, INK, W - 22, H - 22, INK)


# ---------------------------------------------------------------- scenes

def flames(x, y, n=5, h=24, spread=40):
    out = []
    for i in range(n):
        xx = x - spread / 2 + spread * i / max(1, n - 1)
        hh = h * (0.7 + 0.3 * ((i * 37) % 5) / 4)
        out.append('<path d="M%s %s Q%s %s %s %s Q%s %s %s %s Z" fill="#e9a94a" stroke="%s" stroke-width="1"/>' % (
            f(xx - 6), f(y), f(xx - 8), f(y - hh * .6), f(xx), f(y - hh), f(xx + 8), f(y - hh * .6), f(xx + 6), f(y), INK))
    return "".join(out)


def lion(x, y, s=1.0, face=1):
    m = '<g transform="translate(%s %s) scale(%s %s)">' % (f(x), f(y), f(s * face), f(s))
    m += '<path d="M-34 0 Q-38 -22 -20 -28 L18 -28 Q30 -26 30 -10 L30 0 L22 0 L22 -10 L-18 -10 L-22 0 Z" fill="#c9a66e" stroke="%s" stroke-width="1.2"/>' % INK
    m += '<path d="M-34 -18 Q-50 -26 -46 -6" fill="none" stroke="%s" stroke-width="2"/>' % INK
    m += '<circle cx="30" cy="-30" r="15" fill="%s" stroke="%s" stroke-width="1.2"/><circle cx="30" cy="-30" r="15" fill="url(#hatch)"/>' % (MID, INK)
    m += '<circle cx="34" cy="-30" r="8" fill="#d9b77e" stroke="%s"/><circle cx="37" cy="-32" r="1.2" fill="%s"/>' % (INK, INK)
    return m + "</g>"


def camel(x, y, s=1.0, face=1):
    m = '<g transform="translate(%s %s) scale(%s %s)">' % (f(x), f(y), f(s * face), f(s))
    m += ('<path d="M-30 -30 Q-28 -52 -12 -48 Q-4 -62 6 -46 Q18 -44 22 -36 L32 -58 L40 -56 L34 -30 Q30 -24 22 -26 '
          'L20 0 L15 0 L14 -24 L-18 -24 L-20 0 L-25 0 L-24 -26 Q-30 -26 -30 -30 Z" fill="#c9a66e" stroke="%s" stroke-width="1.2"/>') % INK
    return m + "</g>"


def SCENES():
    s = {}

    s["creation"] = sky("#d8c290", PAPER) + glow(300, 120, 260) + rays(300, 120, 40, 40, 460, 1.3, .45) + \
        '<circle cx="300" cy="120" r="34" fill="#fffaf0" stroke="%s"/>' % GOLD + waters(260, 5, seed=2)

    s["garden"] = sky() + sun(470, 70, 18) + hills(250, 40, 4, "#c6ad7c") + ground(285, "#d6c191") + \
        tree(110, 290, 120) + tree(470, 292, 100) + tree(300, 285, 150) + \
        '<circle cx="292" cy="160" r="5" fill="#b0452c" stroke="%s"/><circle cx="315" cy="175" r="5" fill="#b0452c" stroke="%s"/>' % (INK, INK) + \
        figure(220, 320, 56, "reach", 1, robe=WASH) + figure(380, 322, 54, "stand", -1, robe=WASH) + \
        '<path d="M0 340 Q150 320 300 335 T600 330 L600 360 L0 360 Z" fill="#cdbb92" stroke="%s"/>' % INK

    s["ark"] = sky("#cdb98e", PAPER) + \
        "".join('<path d="M%d 300 A240 200 0 0 1 %d 300" fill="none" stroke="%s" stroke-width="5" opacity=".45"/>' % (60 + i * 7, 540 - i * 7, c)
                for i, c in enumerate(("#b0452c", "#d8892c", "#d9c04a", "#6b8a4a", "#4a6a8a", "#6a4a8a"))) + \
        waters(250, 6, seed=3) + \
        '<path d="M150 250 L450 250 L420 290 L180 290 Z" fill="%s" stroke="%s" stroke-width="1.5"/>' % (MID, INK) + \
        '<path d="M150 250 L450 250 L420 290 L180 290 Z" fill="url(#hatch)"/>' + \
        '<rect x="210" y="205" width="180" height="45" fill="%s" stroke="%s" stroke-width="1.3"/>' % (WASH, INK) + \
        '<polygon points="200,205 300,180 400,205" fill="%s" stroke="%s" stroke-width="1.3"/>' % (MID, INK) + \
        '<rect x="285" y="218" width="30" height="20" fill="%s"/>' % INK + \
        '<path d="M470 120 q6 -6 12 0 q6 -6 12 0" fill="none" stroke="%s" stroke-width="2"/>' % INK

    s["tower"] = sky() + sun(500, 60, 16) + ground(300) + \
        "".join('<rect x="%d" y="%d" width="%d" height="38" fill="%s" stroke="%s" stroke-width="1.2"/>' % (
            300 - (170 - i * 30), 300 - (i + 1) * 38, 2 * (170 - i * 30), WASH if i % 2 else "#d4bd8e", INK) for i in range(6)) + \
        '<path d="M300 72 L300 44" stroke="%s" stroke-width="3"/>' % INK + \
        crowd(40, 140, 320, 4, 30, 5) + crowd(460, 570, 322, 4, 30, 6)

    s["tents"] = sky("#5b4a33", "#a8916a") + stars(60, 7) + moon(480, 60) + \
        hills(260, 25, 8, "#8a6f4b") + ground(290, "#c3aa7a") + tent(150, 300, 110, 70) + tent(260, 296, 80, 50) + \
        figure(400, 320, 62, "arms_up", -1, staff=False) + camel(530, 320, .9, -1)

    s["well"] = sky() + sun(90, 70, 16) + hills(240, 30, 9, "#c6ad7c") + ground(280) + \
        tree(520, 285, 110, "palm") + \
        '<ellipse cx="300" cy="300" rx="50" ry="12" fill="%s" stroke="%s"/>' % (MID, INK) + \
        '<path d="M250 300 L250 270 L350 270 L350 300" fill="%s" stroke="%s"/>' % (WASH, INK) + \
        '<path d="M262 270 L262 230 L338 230 L338 270 M262 236 L338 236" fill="none" stroke="%s" stroke-width="2.5"/>' % INK + \
        figure(220, 320, 60, "reach", 1, robe=WASH) + figure(380, 322, 58, "stand", -1, staff=True) + camel(470, 330, .9, -1)

    s["ladder"] = sky("#4f4030", "#9d8661") + stars(50, 11) + glow(380, 30, 160) + \
        '<path d="M300 300 L360 20 M330 304 L392 20" stroke="%s" stroke-width="2.4"/>' % GOLD + \
        "".join('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1.6"/>' % (
            f(300 + 60 * t), f(300 - 280 * t), f(330 + 62 * t), f(304 - 284 * t), GOLD) for t in [i / 14 for i in range(1, 14)]) + \
        figure(330, 180, 30, "stand", 1, robe="#f4e8c8", halo=True) + figure(360, 90, 26, "stand", -1, robe="#f4e8c8", halo=True) + \
        hills(290, 20, 12, "#7d6545") + \
        '<path d="M180 320 Q230 300 290 316 L290 328 L180 328 Z" fill="%s" stroke="%s"/>' % (WASH, INK) + \
        '<rect x="160" y="316" width="30" height="14" fill="%s" stroke="%s"/>' % (MID, INK)

    s["egypt"] = sky() + sun(460, 60, 20) + ground(270, "#dcc89c") + \
        '<polygon points="80,270 190,120 300,270" fill="#d9c08b" stroke="%s" stroke-width="1.3"/><polygon points="190,120 300,270 220,270" fill="url(#hatch)"/>' % INK + \
        '<polygon points="270,270 350,165 430,270" fill="#d9c08b" stroke="%s" stroke-width="1.3"/><polygon points="350,165 430,270 370,270" fill="url(#hatch)"/>' % INK + \
        waters(300, 3, seed=4) + tree(520, 300, 110, "palm") + tree(40, 300, 90, "palm")

    s["bush"] = sky() + hills(220, 50, 13, "#b69a6a") + ground(280) + glow(380, 220, 140) + \
        '<path d="M340 280 Q350 240 380 230 Q410 240 420 280 Z" fill="#7d6545" stroke="%s"/>' % INK + \
        flames(380, 250, 7, 50, 60) + figure(210, 320, 62, "kneel", 1, staff=False) + \
        '<path d="M150 322 L170 318" stroke="%s" stroke-width="3"/>' % INK

    s["redsea"] = sky("#bca97f", PAPER) + glow(300, 40, 200) + \
        '<path d="M0 120 Q120 110 230 140 L250 360 L0 360 Z" fill="#c4b38c" stroke="%s" stroke-width="1.3"/>' % INK + \
        '<path d="M600 120 Q480 110 370 140 L350 360 L600 360 Z" fill="#c4b38c" stroke="%s" stroke-width="1.3"/>' % INK + \
        "".join('<path d="M%d %d q30 -10 60 0 t60 0 t60 0" fill="none" stroke="%s" opacity=".5" transform="translate(%d 0)"/>' % (
            0, 150 + i * 30, INK, 0) for i in range(7)) + \
        "".join('<path d="M%d %d q30 -10 60 0 t60 0 t60 0" fill="none" stroke="%s" opacity=".5"/>' % (
            390, 150 + i * 30, INK) for i in range(7)) + \
        '<path d="M250 360 L270 150 L330 150 L350 360 Z" fill="#e3d2a8"/>' + \
        crowd(260, 340, 340, 5, 30, 14) + figure(300, 250, 44, "arms_up", 1, staff=True)

    s["sinai"] = sky("#6a5a42", "#b29c74") + \
        '<path d="M60 360 L250 110 Q300 70 350 110 L560 360 Z" fill="#8a7050" stroke="%s" stroke-width="1.4"/><path d="M300 90 L560 360 L380 360 Z" fill="url(#hatch)"/>' % INK + \
        '<ellipse cx="300" cy="80" rx="140" ry="36" fill="#d9caa6" stroke="%s" opacity=".9"/>' % INK + \
        '<path d="M250 60 L232 96 L248 96 L228 136" fill="none" stroke="%s" stroke-width="3"/>' % GOLD + \
        '<path d="M360 54 L374 90 L360 90 L380 126" fill="none" stroke="%s" stroke-width="3"/>' % GOLD + \
        '<g transform="translate(300 175)"><path d="M-30 0 L-30 -34 Q-30 -46 -16 -46 Q-2 -46 -2 -34 L-2 0 Z M2 0 L2 -34 Q2 -46 16 -46 Q30 -46 30 -34 L30 0 Z" fill="#efe3c3" stroke="%s" stroke-width="1.3"/></g>' % INK + \
        crowd(60, 540, 350, 12, 26, 15, ("stand", "arms_up"))

    s["tabernacle"] = sky() + glow(300, 80, 120) + \
        '<path d="M300 0 Q280 40 300 70 Q320 100 300 130" fill="none" stroke="#efe6cf" stroke-width="30" opacity=".85"/>' + \
        ground(270) + '<rect x="70" y="230" width="460" height="40" fill="#efe3c3" stroke="%s"/>' % INK + \
        "".join('<line x1="%d" y1="230" x2="%d" y2="270" stroke="%s" stroke-width="1.5"/>' % (x, x, INK) for x in range(80, 530, 20)) + \
        '<rect x="260" y="160" width="160" height="80" fill="%s" stroke="%s" stroke-width="1.3"/><rect x="260" y="160" width="160" height="80" fill="url(#hatch)"/>' % (MID, INK) + \
        '<path d="M250 165 L340 140 L430 165 Z" fill="%s" stroke="%s"/>' % (WASH, INK) + \
        '<rect x="160" y="210" width="40" height="28" fill="%s" stroke="%s"/>' % (MID, INK) + flames(180, 210, 3, 16, 20) + \
        crowd(60, 540, 330, 9, 32, 16, ("stand", "pray"))

    s["wilderness"] = sky("#5a4935", "#a38b64") + stars(40, 17, 100) + \
        '<path d="M330 0 Q310 120 330 230" stroke="#e9a94a" stroke-width="26" opacity=".75" fill="none"/>' + flames(330, 240, 5, 40, 40) + \
        hills(280, 20, 18, "#8a6f4b") + ground(300, "#c3aa7a") + \
        "".join(tent(x, 320 + (i % 2) * 8, 60, 34) for i, x in enumerate(range(60, 560, 70)))

    s["jericho"] = sky() + sun(80, 60, 16) + ground(280) + \
        wall(120, 270, 360, 110) + '<rect x="270" y="200" width="60" height="70" fill="%s"/>' % INK + \
        '<path d="M200 160 L220 120 L240 160 M380 150 L360 110 L340 150" fill="none" stroke="%s" stroke-width="3"/>' % INK + \
        '<path d="M140 170 l20 10 l-10 18 M420 165 l-18 12 l12 16" fill="none" stroke="%s" stroke-width="2"/>' % INK + \
        crowd(30, 570, 340, 12, 30, 19) + \
        "".join('<path d="M%d 300 q20 -12 26 -26 l6 4 q-6 18 -26 28 Z" fill="%s" stroke="%s"/>' % (x, GOLD, INK) for x in (90, 190, 400, 500))

    s["battle"] = sky("#bfa77a", PAPER) + hills(230, 40, 20, "#b69a6a") + ground(280) + \
        "".join('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2"/>' % (x, 320, x + 20, 180, INK) for x in range(40, 260, 26)) + \
        "".join('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2"/>' % (x, 320, x - 20, 180, INK) for x in range(360, 580, 26)) + \
        crowd(30, 250, 330, 7, 40, 21) + crowd(350, 570, 330, 7, 40, 22) + \
        "".join('<ellipse cx="%d" cy="300" rx="10" ry="14" fill="%s" stroke="%s"/>' % (x, GOLD, INK) for x in (70, 140, 210, 400, 470, 540)) + \
        '<path d="M140 180 L140 120 L180 132 L140 144" fill="%s" stroke="%s" stroke-width="1.5"/>' % ("#b0452c", INK) + \
        '<path d="M460 180 L460 120 L420 132 L460 144" fill="%s" stroke="%s" stroke-width="1.5"/>' % (MID, INK)

    s["shepherd"] = sky() + sun(500, 70, 18) + hills(230, 50, 23, "#c6ad7c") + hills(280, 30, 24, "#d6c191") + \
        figure(170, 320, 70, "stand", 1, staff=True) + \
        "".join(sheep(x, y, sc) for x, y, sc in ((250, 320, 1.2), (300, 330, 1.1), (350, 318, 1.2), (400, 334, 1.0),
                                                   (450, 322, 1.1), (330, 300, .9), (420, 298, .8), (480, 300, .8)))

    s["harvest"] = sky() + sun(470, 70, 20) + hills(230, 30, 25, "#c6ad7c") + ground(260, "#e0c98e") + \
        "".join('<path d="M%d %d l-8 -50 M%d %d l0 -54 M%d %d l8 -50" stroke="%s" stroke-width="1.4"/>' % (
            x, y, x, y, x, y, "#8a6a33") for x in range(30, 590, 22) for y in (290,)) + \
        "".join('<g><path d="M%d 330 L%d 270 L%d 270 L%d 330 Z" fill="#e3c47e" stroke="%s"/><line x1="%d" y1="300" x2="%d" y2="300" stroke="%s" stroke-width="2"/></g>' % (
            x - 14, x - 6, x + 6, x + 14, INK, x - 10, x + 10, INK) for x in (90, 480, 540)) + \
        figure(230, 335, 62, "reach", 1, robe=WASH) + figure(360, 335, 66, "stand", -1, staff=True)

    s["king"] = sky("#d4bd8e", PAPER) + \
        '<rect x="40" y="40" width="520" height="290" fill="#e8d8b0" stroke="%s"/>' % INK + \
        "".join('<rect x="%d" y="60" width="26" height="270" fill="#efe1bf" stroke="%s"/>' % (x, INK) for x in (70, 504)) + \
        '<path d="M120 60 Q300 0 480 60" fill="none" stroke="%s" stroke-width="2"/>' % INK + \
        '<rect x="230" y="230" width="140" height="30" fill="%s" stroke="%s"/>' % (MID, INK) + \
        '<path d="M240 230 L240 120 Q300 90 360 120 L360 230 Z" fill="#b0452c" stroke="%s" stroke-width="1.3"/>' % INK + \
        figure(300, 250, 92, "stand", 1, robe=GOLD, crown=True) + \
        "".join('<rect x="%d" y="%d" width="150" height="14" fill="%s" stroke="%s"/>' % (225 - i * 20, 260 + i * 14, WASH, INK, ) for i in range(0)) + \
        '<rect x="200" y="260" width="200" height="14" fill="%s" stroke="%s"/><rect x="180" y="274" width="240" height="14" fill="%s" stroke="%s"/>' % (WASH, INK, WASH, INK) + \
        figure(120, 330, 50, "kneel", 1) + figure(480, 330, 50, "kneel", -1) + \
        '<rect x="20" y="330" width="560" height="22" fill="%s" stroke="%s"/>' % (WASH, INK)

    s["temple"] = sky() + sun(500, 60, 16) + ground(290) + glow(300, 160, 180) + temple(300, 290, 260, 140) + \
        '<path d="M300 112 l0 -14 m-7 7 l14 0" stroke="%s" stroke-width="2"/>' % GOLD + crowd(40, 140, 332, 3, 34, 26, ("pray",)) + \
        crowd(460, 570, 332, 3, 34, 27, ("pray", "stand"))

    s["prophet"] = sky("#cbb487", PAPER) + glow(420, 70, 200) + rays(420, 70, 22, 30, 300, 1.2, .4, 90, 200) + \
        hills(260, 70, 28, "#b69a6a") + figure(260, 225, 78, "arms_up", 1) + \
        '<path d="M150 360 Q300 320 450 360 Z" fill="%s" stroke="%s"/>' % (MID, INK) + crowd(60, 220, 345, 4, 30, 29) + crowd(380, 560, 348, 4, 30, 30)

    s["chariot"] = sky("#c6ad7c", PAPER) + glow(380, 110, 200) + hills(300, 30, 31, "#b69a6a") + \
        '<path d="M80 320 Q300 260 560 40" fill="none" stroke="#e9a94a" stroke-width="20" opacity=".6"/>' + \
        '<g transform="translate(380 120) rotate(-28)"><path d="M-50 0 L40 0 L50 -30 L-40 -30 Z" fill="#e9a94a" stroke="%s" stroke-width="1.4"/>' % INK + \
        '<circle cx="-30" cy="6" r="18" fill="none" stroke="%s" stroke-width="3"/><circle cx="26" cy="6" r="18" fill="none" stroke="%s" stroke-width="3"/>' % (INK, INK) + \
        flames(0, -28, 5, 34, 80) + '<path d="M60 -10 Q90 -40 120 -30 Q110 -12 130 4 Q100 6 80 -4 Z" fill="#e9a94a" stroke="%s"/></g>' % INK + \
        figure(200, 330, 58, "arms_up", 1)

    s["exile"] = sky("#bfa77a", PAPER) + \
        wall(60, 250, 120, 70, crenel=False) + '<path d="M60 180 l20 -10 l14 14 l20 -18 l10 12 l20 -8 l16 10 l0 20 L60 200 Z" fill="%s"/>' % PAPER + \
        '<path d="M380 250 l40 -60 l40 30 l30 -50 l30 80 Z" fill="%s" stroke="%s"/>' % (MID, INK) + \
        waters(260, 4, seed=32) + tree(500, 270, 110) + tree(100, 272, 90) + \
        '<path d="M470 230 l-10 26 l18 0 Z" fill="none" stroke="%s" stroke-width="1.5"/>' % INK + \
        crowd(200, 420, 340, 5, 40, 33, ("kneel", "stand", "pray"))

    s["rebuild"] = sky() + sun(500, 60, 16) + ground(280) + wall(40, 280, 340, 90) + \
        '<path d="M380 280 L380 230 L410 230 L410 250 L440 250 L440 280" fill="%s" stroke="%s"/>' % (WASH, INK) + \
        "".join('<rect x="%d" y="%d" width="22" height="12" fill="%s" stroke="%s"/>' % (x, y, WASH, INK) for x, y in ((460, 300), (488, 300), (474, 288), (520, 310))) + \
        figure(200, 180, 36, "reach", 1) + figure(300, 182, 36, "stand", -1, staff=True) + figure(420, 330, 50, "reach", -1) + figure(560, 336, 48, "stand", -1)

    s["queen"] = sky("#d4bd8e", PAPER) + \
        '<rect x="40" y="40" width="520" height="290" fill="#e8d8b0" stroke="%s"/>' % INK + \
        "".join('<rect x="%d" y="60" width="22" height="270" fill="#efe1bf" stroke="%s"/>' % (x, INK) for x in (70, 160, 418, 508)) + \
        '<rect x="300" y="200" width="160" height="40" fill="%s" stroke="%s"/>' % (MID, INK) + \
        figure(400, 240, 76, "reach", -1, robe=GOLD, crown=True) + figure(250, 330, 74, "stand", 1, robe="#b0452c", crown=True) + \
        '<line x1="372" y1="186" x2="300" y2="230" stroke="%s" stroke-width="2.5"/>' % GOLD + \
        '<rect x="20" y="330" width="560" height="22" fill="%s" stroke="%s"/>' % (WASH, INK)

    s["furnace"] = sky("#a2885e", "#d8c49a") + \
        '<path d="M140 340 L140 120 Q300 60 460 120 L460 340 Z" fill="#7d6545" stroke="%s" stroke-width="1.5"/>' % INK + \
        '<path d="M190 340 L190 170 Q300 120 410 170 L410 340 Z" fill="#e9a94a" stroke="%s"/>' % INK + glow(300, 260, 140) + \
        flames(300, 340, 9, 70, 200) + figure(250, 320, 50, "stand", 1, robe=WASH) + figure(290, 318, 52, "stand", 1, robe=WASH) + \
        figure(330, 320, 50, "stand", -1, robe=WASH) + figure(370, 316, 54, "stand", -1, robe="#f8edd0", halo=True)

    s["lions"] = sky("#6a5a42", "#a8916a") + glow(300, 60, 120) + \
        '<path d="M0 0 L0 360 L600 360 L600 0 L520 0 Q520 80 300 90 Q80 80 80 0 Z" fill="#8a7050" stroke="%s"/>' % INK + \
        '<path d="M0 0 L0 360 L600 360 L600 0 L520 0 Q520 80 300 90 Q80 80 80 0 Z" fill="url(#hatch)"/>' + \
        ground(310, "#a3895f") + figure(300, 300, 74, "pray", 1, robe=WASH) + \
        lion(140, 320, 1.2, 1) + lion(470, 322, 1.2, -1) + lion(200, 270, .8, 1) + lion(420, 272, .8, -1)

    s["fish"] = sky("#b8a47a", PAPER) + waters(150, 8, seed=34, fill="#cbb98e") + \
        '<path d="M120 250 Q250 160 420 230 Q470 200 520 170 Q500 240 520 310 Q470 280 420 260 Q260 340 120 250 Z" fill="%s" stroke="%s" stroke-width="1.5"/>' % (MID, INK) + \
        '<path d="M120 250 Q250 160 420 230 Q260 340 120 250 Z" fill="url(#hatch)"/>' + \
        '<circle cx="170" cy="236" r="5" fill="%s"/><path d="M120 250 Q150 262 180 256" fill="none" stroke="%s" stroke-width="2"/>' % (INK, INK) + \
        boat(470, 140, 120, True, -8) + figure(110, 238, 34, "arms_up", -1, robe=WASH)

    s["vineyard"] = sky() + sun(470, 70, 18) + hills(230, 30, 35, "#c6ad7c") + ground(250, "#d6c191") + \
        "".join('<g><line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2"/>%s</g>' % (
            x, 330, x, 260, INK, "".join('<circle cx="%d" cy="%d" r="4" fill="#6a3a5a" stroke="%s" stroke-width=".6"/>' % (x + dx, 280 + dy, INK)
                                         for dx, dy in ((-6, 0), (0, 6), (6, 0), (-3, 12), (3, 12)))) for x in range(40, 600, 46)) + \
        '<path d="M20 262 L580 262" stroke="#6b8a4a" stroke-width="5" opacity=".7"/>' + \
        figure(250, 340, 60, "reach", 1, robe=WASH) + figure(350, 340, 64, "stand", -1)

    s["harp"] = sky() + glow(300, 120, 200) + rays(300, 120, 20, 40, 300, 1, .3) + ground(300) + \
        '<path d="M250 300 L250 110 Q300 70 360 120 Q330 200 360 300 Z" fill="none" stroke="%s" stroke-width="6"/>' % GOLD + \
        "".join('<line x1="%d" y1="%d" x2="%d" y2="300" stroke="%s" stroke-width="1"/>' % (260 + i * 10, 108 - i * 3 if i < 4 else 98 + (i - 4) * 6, 260 + i * 10, INK) for i in range(10)) + \
        figure(190, 330, 66, "reach", 1) + sheep(430, 330, 1.2) + sheep(490, 320, 1)

    s["lamp"] = sky("#5b4a33", "#a8916a") + glow(300, 170, 180) + \
        '<rect x="0" y="250" width="600" height="110" fill="%s" stroke="%s"/>' % (MID, INK) + \
        '<path d="M240 240 Q300 280 360 240 L340 220 Q300 230 260 220 Z" fill="%s" stroke="%s" stroke-width="1.4"/>' % (GOLD, INK) + \
        '<path d="M360 240 Q390 236 396 222" fill="none" stroke="%s" stroke-width="2"/>' % INK + flames(396, 222, 1, 30, 0) + \
        scroll(160, 300, 180, 70, 3, False) + scroll(450, 300, 160, 70, 3, False)

    s["whirlwind"] = sky("#9d8661", "#d8c49a") + \
        "".join('<ellipse cx="%d" cy="%d" rx="%d" ry="%d" fill="none" stroke="%s" stroke-width="2" opacity=".55"/>' % (
            400 + i * 4, 60 + i * 24, 140 - i * 14, 18, INK) for i in range(9)) + \
        hills(290, 20, 36, "#8a6f4b") + ground(310, "#c3aa7a") + figure(200, 340, 66, "kneel", 1, robe=WASH) + \
        crowd(60, 140, 340, 3, 40, 37)

    s["nativity"] = sky("#4f4030", "#9d8661") + stars(40, 38) + star(300, 50, 18, "#fbf1d2") + rays(300, 50, 6, 20, 120, 2, .7, 60, 120) + \
        hills(270, 20, 39, "#7d6545") + \
        '<path d="M170 320 L170 200 L300 140 L430 200 L430 320 Z" fill="%s" stroke="%s" stroke-width="1.4"/>' % ("#8a7050", INK) + \
        '<path d="M200 320 L200 210 L400 210 L400 320 Z" fill="#e9cf8e"/>' + glow(300, 280, 100) + \
        '<path d="M270 300 L330 300 L320 316 L280 316 Z" fill="%s" stroke="%s"/><ellipse cx="300" cy="298" rx="16" ry="7" fill="#fbf4e0" stroke="%s"/>' % (MID, INK, INK) + \
        figure(240, 320, 58, "kneel", 1, robe="#6a7a9a") + figure(365, 322, 64, "stand", -1, staff=True) + \
        sheep(470, 334, 1) + sheep(110, 334, 1)

    s["storm"] = sky("#6a5a42", "#a8916a") + \
        '<path d="M380 30 L360 80 L378 80 L350 140" fill="none" stroke="#fbf1d2" stroke-width="3"/>' + \
        waters(220, 7, amp=9, seed=40, fill="#9c8762") + boat(280, 250, 220, True, 10) + \
        crowd(200, 340, 236, 5, 26, 41, ("arms_up", "stand")) + figure(470, 220, 56, "reach", -1, robe=WASH, halo=True)

    s["mount"] = sky() + sun(480, 70, 18) + hills(200, 60, 42, "#c6ad7c", bumps=2) + \
        figure(300, 170, 50, "reach", 1, robe=WASH, halo=True) + \
        crowd(30, 570, 260, 14, 30, 43) + crowd(20, 580, 320, 16, 34, 44) + \
        '<path d="M0 340 L600 340 L600 360 L0 360 Z" fill="%s"/>' % MID

    s["healing"] = sky() + sun(80, 60, 16) + ground(270) + wall(380, 270, 200, 90) + \
        tree(60, 280, 100, "palm") + \
        '<path d="M0 360 Q300 270 600 300 L600 360 Z" fill="%s" stroke="%s"/>' % ("#d6c191", INK) + \
        figure(260, 330, 72, "reach", 1, robe=WASH, halo=True) + figure(340, 334, 48, "kneel", -1) + \
        crowd(390, 560, 332, 4, 50, 45) + figure(170, 334, 58, "stand", 1)

    s["supper"] = sky("#6a5a42", "#a8916a") + glow(300, 160, 220) + \
        '<rect x="30" y="40" width="540" height="200" fill="#c9b386" stroke="%s"/>' % INK + \
        '<rect x="250" y="70" width="100" height="120" fill="#e9dcb8" stroke="%s"/>' % INK + \
        crowd(70, 250, 250, 6, 60, 46) + crowd(350, 530, 250, 6, 60, 47) + figure(300, 250, 66, "reach", 1, robe=WASH, halo=True) + \
        '<rect x="40" y="246" width="520" height="22" fill="%s" stroke="%s" stroke-width="1.3"/><rect x="60" y="268" width="480" height="60" fill="%s" stroke="%s"/>' % (MID, INK, WASH, INK) + \
        '<path d="M290 246 L310 246 L306 230 L294 230 Z M300 230 L300 222" fill="%s" stroke="%s"/>' % (GOLD, INK) + \
        '<ellipse cx="200" cy="244" rx="16" ry="5" fill="#e3c47e" stroke="%s"/><ellipse cx="420" cy="244" rx="16" ry="5" fill="#e3c47e" stroke="%s"/>' % (INK, INK)

    s["cross"] = sky("#6a5a42", "#bfa77a") + glow(300, 120, 200) + hills(280, 90, 48, "#8a7050", bumps=1) + \
        "".join('<path d="M%d %d L%d %d M%d %d L%d %d" stroke="%s" stroke-width="%d" stroke-linecap="square"/>' % (
            x, y, x, y - h, x - w, y - h + 26, x + w, y - h + 26, INK, sw) for x, y, h, w, sw in ((300, 220, 150, 40, 9), (170, 250, 110, 28, 6), (430, 250, 110, 28, 6))) + \
        crowd(60, 250, 340, 5, 40, 49, ("stand", "pray")) + crowd(350, 560, 340, 5, 40, 50, ("stand", "kneel"))

    s["tomb"] = sky("#cbb487", PAPER) + sun(470, 220, 26) + hills(260, 60, 51, "#b69a6a", bumps=2) + ground(300) + \
        '<path d="M120 300 Q120 150 240 150 Q360 150 360 300 Z" fill="#9c845a" stroke="%s" stroke-width="1.4"/>' % INK + \
        '<path d="M190 300 Q190 220 240 220 Q290 220 290 300 Z" fill="%s"/>' % INK + \
        '<circle cx="330" cy="268" r="44" fill="#c4ae80" stroke="%s" stroke-width="1.4"/><circle cx="330" cy="268" r="44" fill="url(#hatch)"/>' % INK + \
        figure(220, 300, 54, "stand", 1, robe="#fbf4e0", halo=True) + figure(450, 334, 50, "reach", -1, robe=WASH) + figure(500, 336, 48, "pray", -1)

    s["pentecost"] = sky("#d4bd8e", PAPER) + glow(300, 40, 240) + rays(300, 0, 18, 10, 360, 1.2, .35, 30, 150) + \
        '<rect x="40" y="110" width="520" height="220" fill="#e8d8b0" stroke="%s"/>' % INK + \
        crowd(60, 540, 320, 12, 66, 52, ("stand", "arms_up", "pray")) + \
        "".join(flames(60 + (540 - 60) * (i + .5) / 12, 238, 1, 18, 0) for i in range(12)) + \
        '<path d="M290 80 q10 -14 20 0 q-10 6 -20 0 Z M300 80 l-16 -10 M300 80 l16 -10" fill="#fbf4e0" stroke="%s" stroke-width="1.5"/>' % INK

    s["voyage"] = sky() + sun(110, 80, 18) + waters(220, 7, seed=53) + \
        '<path d="M470 220 L520 150 L580 220 Z" fill="%s" stroke="%s"/>' % (MID, INK) + boat(300, 236, 240, True) + \
        crowd(220, 360, 216, 4, 26, 54) + \
        '<path d="M140 150 q10 -8 20 0 q10 -8 20 0" fill="none" stroke="%s" stroke-width="1.6"/>' % INK

    s["letter"] = sky() + glow(300, 170, 200) + \
        '<rect x="0" y="270" width="600" height="90" fill="%s" stroke="%s"/>' % (MID, INK) + \
        scroll(300, 170, 300, 170, 7, True) + \
        '<circle cx="390" cy="236" r="16" fill="#b0452c" stroke="%s" stroke-width="1.3"/><path d="M382 236 l8 -8 l8 8 l-8 8 Z" fill="none" stroke="#f2e6c9"/>' % INK + \
        '<path d="M140 290 Q150 270 170 272 L176 300 Z" fill="%s" stroke="%s"/>' % (INK, INK)

    s["throne"] = sky("#e2cfa4", PAPER) + glow(300, 150, 300) + rays(300, 150, 36, 70, 420, 1.2, .4) + \
        "".join('<path d="M%d 330 A230 200 0 0 1 %d 330" fill="none" stroke="%s" stroke-width="4" opacity=".4"/>' % (70 + i * 6, 530 - i * 6, c)
                for i, c in enumerate(("#4a8a6a", "#6b8a4a", "#d9c04a"))) + \
        '<rect x="250" y="160" width="100" height="120" rx="8" fill="%s" stroke="%s" stroke-width="1.4"/>' % (GOLD, INK) + \
        glow(300, 160, 70) + \
        "".join(figure(x, 332, 40, "kneel", 1 if x < 300 else -1, robe="#f4e8c8", crown=True) for x in (70, 120, 170, 430, 480, 530)) + \
        '<rect x="200" y="280" width="200" height="16" fill="%s" stroke="%s"/>' % (WASH, INK)

    s["newjerusalem"] = sky("#e2cfa4", PAPER) + glow(300, 150, 300) + rays(300, 150, 30, 60, 420, 1.2, .35) + \
        '<path d="M60 360 Q300 300 540 360 Z" fill="#d6c191" stroke="%s"/>' % INK + \
        wall(120, 300, 360, 120, fill="#efe3bd") + \
        "".join('<path d="M%d 300 L%d 250 Q%d 230 %d 250 L%d 300 Z" fill="#fff3cf" stroke="%s"/>' % (x - 16, x - 16, x, x + 16, x + 16, INK) for x in (180, 300, 420)) + \
        "".join('<rect x="%d" y="%d" width="28" height="%d" fill="#efe3bd" stroke="%s"/>' % (x, 300 - h, h, INK) for x, h in ((106, 160), (466, 160), (286, 190))) + \
        waters(330, 2, seed=55, x0=260, x1=340, fill="#cfe0d8")

    s["seals"] = sky("#5b4a33", "#a8916a") + stars(40, 56) + glow(300, 170, 220) + \
        '<g transform="translate(300 180)"><rect x="-90" y="-60" width="180" height="120" fill="#f7edd3" stroke="%s" stroke-width="1.4"/>' % INK + \
        "".join('<circle cx="%d" cy="62" r="9" fill="#b0452c" stroke="%s"/>' % (-72 + i * 24, INK) for i in range(7)) + \
        "".join('<line x1="-70" y1="%d" x2="70" y2="%d" stroke="%s" opacity=".5" stroke-width="1.4"/>' % (y, y, INK) for y in (-38, -20, -2, 16, 34)) + "</g>" + \
        "".join(figure(x, 350, 46, "arms_up", 1 if x < 300 else -1, robe="#f4e8c8", halo=True) for x in (60, 130, 470, 540))

    s["genealogy"] = sky() + glow(300, 160, 200) + \
        tree(300, 340, 300) + \
        "".join('<circle cx="%d" cy="%d" r="11" fill="#f7edd3" stroke="%s" stroke-width="1.2"/>' % (x, y, INK)
                for x, y in ((300, 60), (240, 90), (360, 90), (200, 130), (300, 120), (400, 130), (230, 170), (370, 170))) + \
        scroll(110, 300, 140, 60, 3, False) + scroll(490, 300, 140, 60, 3, False)

    s["altar"] = sky() + glow(300, 120, 200) + rays(300, 0, 14, 10, 260, 1.2, .35, 40, 140) + ground(280) + \
        '<rect x="240" y="220" width="120" height="70" fill="%s" stroke="%s" stroke-width="1.4"/>' % (WASH, INK) + \
        "".join('<line x1="240" y1="%d" x2="360" y2="%d" stroke="%s" opacity=".5"/>' % (y, y, INK) for y in (240, 260)) + \
        flames(300, 222, 5, 40, 70) + '<path d="M290 180 Q280 120 300 60" fill="none" stroke="%s" stroke-width="10" opacity=".25"/>' % INK + \
        figure(170, 320, 64, "arms_up", 1) + figure(440, 322, 56, "pray", -1) + sheep(520, 330, 1)

    s["valley"] = sky("#bfa77a", PAPER) + glow(300, 60, 180) + hills(220, 60, 57, "#9c845a") + ground(260, "#cdb88c") + \
        "".join('<path d="M%d %d l18 -4 M%d %d l-6 12" stroke="#fbf4e0" stroke-width="3" stroke-linecap="round"/>' % (x, y, x + 6, y - 2) for x, y in
                ((80, 300), (140, 320), (220, 296), (380, 310), (460, 300), (520, 330), (300, 340), (180, 344))) + \
        crowd(330, 560, 300, 6, 36, 58, ("stand", "arms_up")) + figure(200, 260, 60, "arms_up", 1)

    s["cloud"] = sky("#d8c49a", PAPER) + glow(300, 90, 240) + \
        '<ellipse cx="300" cy="90" rx="120" ry="34" fill="#fbf4e0" stroke="%s"/>' % INK + \
        figure(300, 120, 50, "arms_up", 1, robe="#fbf4e0", halo=True) + hills(300, 40, 59, "#b69a6a", bumps=2) + \
        crowd(60, 540, 340, 11, 36, 60, ("arms_up", "stand", "pray"))
    s["scroll"] = sky() + glow(300, 120, 220) + ground(290) + \
        '<rect x="230" y="210" width="140" height="80" fill="%s" stroke="%s" stroke-width="1.3"/>' % (MID, INK) + \
        scroll(300, 150, 220, 110, 5, False) + figure(300, 214, 40, "reach", 1, robe=WASH) + \
        crowd(30, 220, 336, 6, 40, 63, ("stand", "pray")) + crowd(380, 570, 336, 6, 40, 64, ("stand", "pray"))
    s["tree"] = sky() + sun(480, 70, 18) + hills(250, 30, 61, "#c6ad7c") + ground(290, "#d6c191") + \
        waters(310, 3, seed=62, x0=0, x1=260) + tree(330, 300, 200) + figure(450, 322, 56, "stand", -1, staff=True) + \
        sheep(520, 330, 1)
    return s


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.svg"):
        old.unlink()
    scenes = SCENES()
    for name, body in sorted(scenes.items()):
        (OUT / (name + ".svg")).write_text(frame(body), encoding="utf-8")
    print("wrote %d scenes to %s" % (len(scenes), OUT))


if __name__ == "__main__":
    main()
