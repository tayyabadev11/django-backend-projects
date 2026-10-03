#!/usr/bin/env python3
"""Draws the 23 dish illustrations (hand-drawn style SVG) into restaurant/static/images/.

Run from the project root:  python tools/make_images.py
The files are already included, so you only need this to redraw them.
"""
import math
import pathlib
import random
import zlib

INK = "#3b1d1d"
OUT = pathlib.Path(__file__).resolve().parent.parent / "restaurant" / "static" / "images"


# ------------------------------------------------------------ primitives
def circ(x, y, r, fill, sw=None):
    s = f' stroke-width="{sw}"' if sw else ""
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}"{s}/>'


def ell(x, y, rx, ry, fill, rot=0, sw=None):
    s = f' stroke-width="{sw}"' if sw else ""
    return (f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{fill}"{s} '
            f'transform="rotate({rot:.1f} {x:.1f} {y:.1f})"/>')


def rect(x, y, w, h, fill, rx=6, rot=0, sw=None):
    s = f' stroke-width="{sw}"' if sw else ""
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}"{s} '
            f'transform="rotate({rot:.1f} {x + w / 2:.1f} {y + h / 2:.1f})"/>')


def path(d, fill="none", stroke=None, sw=None):
    st = f' stroke="{stroke}"' if stroke else ""
    w = f' stroke-width="{sw}"' if sw else ""
    return f'<path d="{d}" fill="{fill}"{st}{w}/>'


def line(x1, y1, x2, y2, color=INK, sw=2.5):
    return f'<path d="M{x1:.1f} {y1:.1f} L{x2:.1f} {y2:.1f}" fill="none" stroke="{color}" stroke-width="{sw}"/>'


def dot(x, y, r, fill):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" stroke="none"/>'


def leaf(x, y, rot=0, size=14, fill="#5a9a43"):
    return (ell(x, y, size, size * 0.5, fill, rot, 2)
            + f'<path d="M{x - size * .8:.1f} {y:.1f} L{x + size * .8:.1f} {y:.1f}" stroke="{INK}" stroke-width="1" '
              f'transform="rotate({rot:.1f} {x:.1f} {y:.1f})"/>')


def pts(rng, n, cx, cy, radius, inner=0.0):
    out = []
    for _ in range(n):
        a = rng.uniform(0, 6.2832)
        d = radius * math.sqrt(rng.uniform(inner ** 2, 1))
        out.append((cx + d * math.cos(a), cy + d * math.sin(a)))
    return out


def plate(cx=200, cy=150, r=118):
    return (f'<ellipse cx="{cx + 6}" cy="{cy + 8}" rx="{r}" ry="{r - 4}" fill="{INK}" fill-opacity="0.18" stroke="none"/>'
            + circ(cx, cy, r, "#fffaf0") + circ(cx, cy, r * 0.78, "#f4ebdc", 1.6))


def plate_side(cx=200, cy=212, rx=130, ry=36):
    return (ell(cx + 5, cy + 7, rx, ry, INK + "30", sw=0).replace('stroke-width="0"', 'stroke="none"')
            + ell(cx, cy, rx, ry, "#fffaf0") + ell(cx, cy - 2, rx * 0.72, ry * 0.62, "#f4ebdc", 0, 1.5))


def wrap(body, bg="#f2e3cf"):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300" width="400" height="300">
<defs><filter id="rough" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="2" seed="4" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="3.2"/></filter></defs>
<rect width="400" height="300" fill="{bg}"/>
<rect x="9" y="9" width="382" height="282" rx="10" fill="none" stroke="#8b1e2d" stroke-opacity=".35" stroke-width="2" stroke-dasharray="7 6"/>
<g filter="url(#rough)" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round">
{body}
</g>
</svg>
'''


# ----------------------------------------------------------- shared bits
def potatoes(rng, cx, cy, n=5):
    return "".join(ell(x, y, 13, 8, "#e6b552", rng.uniform(0, 180), 2) for x, y in pts(rng, n, cx, cy, 20))


def lemon_wedge(x, y, rot=0):
    return (f'<g transform="rotate({rot} {x} {y})">'
            + path(f"M{x - 20} {y} A20 20 0 0 0 {x + 20} {y} Z", "#f6dc5a")
            + line(x, y, x, y + 18, INK, 1.3) + line(x, y, x - 12, y + 14, INK, 1.3) + line(x, y, x + 12, y + 14, INK, 1.3)
            + '</g>')


def greens(rng, cx, cy, n=6):
    return "".join(leaf(x, y, rng.uniform(0, 180), 11, "#4f8a3c") for x, y in pts(rng, n, cx, cy, 20))


def grill_marks(x, y, n=4, spread=18, color="#3d1b0e"):
    return "".join(line(x + i * spread - 6, y - 20, x + i * spread + 10, y + 22, color, 3.5) for i in range(n))


# ---------------------------------------------------------------- dishes
def pizza(rng, kind):
    b = [circ(200, 150, 124, "#b98353"), circ(200, 150, 104, "#e3a95e")]
    sauce = "#7a3b1d" if kind == "bbq" else "#c8402f"
    b += [circ(200, 150, 90, sauce), circ(200, 150, 83, "#f7d98a")]
    for x, y in pts(rng, 9, 200, 150, 66):
        b.append(ell(x, y, 16, 11, "#fbe9b0", rng.uniform(0, 180), 0))
    if kind == "margherita":
        for x, y in pts(rng, 6, 200, 150, 62, .25):
            b.append(circ(x, y, 14, "#fffdf4", 2))
        for x, y in pts(rng, 8, 200, 150, 68):
            b.append(leaf(x, y, rng.uniform(0, 180), 12))
    elif kind == "pepperoni":
        for x, y in pts(rng, 11, 200, 150, 64, .2):
            b.append(circ(x, y, 12, "#b3261e", 2))
            b.append(dot(x - 3, y - 2, 1.8, "#7a1710"))
            b.append(dot(x + 4, y + 3, 1.8, "#7a1710"))
    else:
        for x, y in pts(rng, 13, 200, 150, 64):
            b.append(rect(x - 8, y - 6, 16, 12, "#ecd0a2", 4, rng.uniform(0, 90), 2))
        for x, y in pts(rng, 6, 200, 150, 62, .2):
            b.append(circ(x, y, 9, "none", 3).replace('fill="none"', 'fill="none" stroke="#a23a6a"'))
        b.append(path("M130 140 Q150 120 165 145 T200 140 T235 150 T270 130", "none", "#4a2210", 4))
        for x, y in pts(rng, 7, 200, 150, 66):
            b.append(leaf(x, y, rng.uniform(0, 180), 7, "#5a9a43"))
    for i in range(8):
        a = i * math.pi / 4 + .39
        b.append(line(200, 150, 200 + 104 * math.cos(a), 150 + 104 * math.sin(a), INK, 1.6))
    return "".join(b)


def spaghetti(rng, kind="bolognese"):
    b = [plate()]
    b.append(circ(200, 150, 62, "#edc873"))
    for i in range(7):
        r = 58 - i * 8
        b.append(path(f"M{200 - r} 150 A{r} {r * .85:.0f} 0 1 1 {200 + r} 150 A{r} {r * .85:.0f} 0 1 1 {200 - r} 150",
                      "none", "#b98d2f", 2.2))
    b.append(ell(200, 140, 36, 26, "#a1301f", -10))
    for x, y in pts(rng, 14, 200, 140, 28):
        b.append(dot(x, y, 3.4, "#5e1d12"))
    for x, y in pts(rng, 10, 200, 140, 28):
        b.append(dot(x, y, 1.7, "#fff4d1"))
    b.append(leaf(212, 128, 30, 12))
    b.append(leaf(190, 152, -40, 10))
    return "".join(b)


def fettuccine(rng):
    b = [plate()]
    for i in range(9):
        y = 100 + i * 12
        b.append(path(f"M130 {y} Q165 {y - 18} 200 {y} T270 {y}", "none", "#f1dca0", 8))
        b.append(path(f"M130 {y} Q165 {y - 18} 200 {y} T270 {y}", "none", "#d6b866", 1.5))
    b.append(ell(200, 148, 48, 30, "#fcf3da", 0, 2))
    for x, y in pts(rng, 7, 200, 146, 36):
        b.append(rect(x - 11, y - 4, 22, 8, "#e5c48d", 3, rng.uniform(-40, 40), 2))
    for x, y in pts(rng, 18, 200, 148, 44):
        b.append(dot(x, y, 2.2, "#4a8a35"))
    for x, y in pts(rng, 10, 200, 148, 44):
        b.append(dot(x, y, 1.3, INK))
    return "".join(b)


def penne(rng):
    b = [plate()]
    for x, y in pts(rng, 15, 200, 150, 62, .1):
        rot = rng.uniform(0, 180)
        b.append(rect(x - 20, y - 8, 40, 16, "#d9532f", 7, rot, 2.2))
        b.append(ell(x + 20 * math.cos(math.radians(rot)), y + 20 * math.sin(math.radians(rot)), 3.5, 6, "#f1d28a", rot, 1.4))
    for x, y in pts(rng, 18, 200, 150, 70):
        b.append(dot(x, y, 1.9, "#8f1b12"))
    b.append(leaf(205, 140, 25, 13))
    b.append(leaf(185, 160, -30, 11))
    return "".join(b)


def burger(rng, kind):
    b = [ell(200, 238, 128, 14, INK + "30", 0).replace(f'stroke-width', 'data-x')]
    b[0] = f'<ellipse cx="200" cy="238" rx="128" ry="14" fill="{INK}" fill-opacity=".18" stroke="none"/>'
    b.append(rect(112, 196, 176, 34, "#d99a4a", 15))
    b.append(rect(104, 174, 192, 26, "#5b2a17" if kind == "beef" else "#d6902f", 13))
    if kind == "chicken":
        for x, y in pts(rng, 16, 200, 187, 80):
            if 108 < x < 292 and 176 < y < 198:
                b.append(dot(x, y, 2.6, "#f1c15f"))
    if kind == "beef":
        b.append(path("M108 172 L292 172 L282 186 L262 174 L240 192 L218 174 L196 186 L172 174 L148 190 L128 176 Z", "#f6c445"))
    b.append(path("M102 164 Q122 150 140 164 T178 164 T216 164 T254 164 T298 164 L298 174 L102 174 Z", "#5aa044"))
    b.append(ell(150, 156, 34, 8, "#d63a2c")); b.append(ell(236, 156, 34, 8, "#d63a2c"))
    b.append(path("M104 150 Q104 78 200 78 Q296 78 296 150 Z", "#e2a257"))
    for x, y in [(150, 108), (180, 98), (215, 100), (250, 112), (165, 128), (200, 120), (238, 134), (135, 134)]:
        b.append(ell(x, y, 6, 3, "#fff1c9", rng.uniform(-30, 30), 1.4))
    b.append(line(200, 60, 200, 100, "#8a6a3a", 2.5))
    b.append(path("M200 60 L222 66 L200 72 Z", "#b3202f", None, 2))
    return "".join(b)


def steak(rng, kind):
    b = [plate()]
    if kind == "beef":
        b.append(ell(196, 148, 68, 46, "#7b3b21", -12))
        b.append(ell(196, 148, 56, 36, "#99502e", -12, 1.2))
        b.append(grill_marks(168, 150, 5, 15))
        b.append(rect(186, 134, 24, 14, "#f6dc7a", 3, -12, 2))
        b.append(ell(258, 168, 26, 14, "#4a2a18", 0, 2))
        b.append(path("M130 110 Q150 96 170 104", "none", "#3f7a2f", 3))
        b.append(leaf(160, 100, 10, 8, "#3f7a2f")); b.append(leaf(140, 106, -20, 8, "#3f7a2f"))
        b.append(potatoes(rng, 248, 116, 4))
        b.append(greens(rng, 138, 192, 4))
    elif kind == "chicken":
        b.append(ell(180, 142, 54, 34, "#d9a05b", -15))
        b.append(ell(228, 168, 48, 30, "#cf9450", 12))
        b.append(grill_marks(150, 146, 4, 15, "#7a4a1f"))
        b.append(grill_marks(204, 172, 4, 14, "#7a4a1f"))
        b.append(lemon_wedge(250, 106, 20))
        b.append(potatoes(rng, 140, 196, 5))
        b.append(greens(rng, 170, 96, 5))
    else:
        b.append(path("M120 150 Q150 108 230 124 Q282 136 272 168 Q230 196 160 186 Q118 180 120 150 Z", "#f2d9b5"))
        b.append(grill_marks(160, 152, 5, 17, "#b9793a"))
        b.append(circ(250, 98, 24, "#f7e07a"))
        for a in range(0, 360, 60):
            b.append(line(250, 98, 250 + 20 * math.cos(math.radians(a)), 98 + 20 * math.sin(math.radians(a)), INK, 1.2))
        b.append(potatoes(rng, 150, 208, 5))
        b.append(greens(rng, 120, 110, 4))
    return "".join(b)


def club(rng):
    b = [plate()]
    b.append(path("M120 96 L238 96 L180 176 Z", "#e8c27c"))
    b.append(path("M120 96 L238 96 L180 176 Z", "none", "#a8742a", 1))
    b.append(grill_marks(150, 112, 4, 14, "#b98a3f"))
    b.append(path("M170 118 L280 118 L228 192 Z", "#efcf8f"))
    b.append(path("M184 128 L268 128 L228 184 Z", "none", "#a8742a", 1.5))
    b.append(line(180, 100, 212, 70, "#8a6a3a", 2.5)); b.append(circ(212, 70, 5, "#b3202f", 2))
    b.append(line(236, 130, 262, 98, "#8a6a3a", 2.5)); b.append(circ(262, 98, 5, "#b3202f", 2))
    for x, y in pts(rng, 10, 130, 200, 36):
        b.append(circ(x, y, 12, "#f0c85a", 2))
    b.append(ell(265, 205, 18, 8, "#6a9a3a", -20, 2))
    return "".join(b)


def soup(rng):
    b = [plate(), circ(200, 150, 88, "#fffdf6"), circ(200, 150, 72, "#d4502f")]
    b.append(path("M150 150 Q175 120 200 150 T250 150", "none", "#f6e7c5", 6))
    b.append(path("M165 175 Q190 150 215 175", "none", "#f6e7c5", 5))
    for x, y in pts(rng, 7, 200, 150, 55):
        b.append(rect(x - 6, y - 6, 12, 12, "#e2b872", 2, rng.uniform(0, 90), 1.8))
    b.append(leaf(215, 138, 35, 14)); b.append(leaf(190, 160, -35, 12))
    for x, y in pts(rng, 10, 200, 150, 60):
        b.append(dot(x, y, 1.5, INK))
    b.append(ell(330, 80, 14, 9, "#e8e8e8", -35, 2)); b.append(line(320, 90, 285, 125, "#9a9a9a", 4))
    return "".join(b)


def salad(rng):
    b = [plate(), circ(200, 150, 92, "#f3f3e8"), circ(200, 150, 78, "#f9f9ef", 1.5)]
    for x, y in pts(rng, 26, 200, 150, 66):
        b.append(ell(x, y, 21, 11, rng.choice(["#5a9a43", "#78b255", "#4a8a3a"]), rng.uniform(0, 180), 2))
    for x, y in pts(rng, 4, 200, 150, 52):
        b.append(circ(x, y, 12, "#d63a2c", 2)); b.append(dot(x, y, 3, "#f9d9a0"))
    for x, y in pts(rng, 7, 200, 150, 58):
        b.append(rect(x - 6, y - 6, 12, 12, "#e2b872", 2, rng.uniform(0, 90), 1.8))
    for x, y in pts(rng, 5, 200, 150, 52):
        b.append(rect(x - 14, y - 4, 28, 8, "#e5c48d", 3, rng.uniform(-60, 60), 2))
    for x, y in pts(rng, 5, 200, 150, 56):
        b.append(path(f"M{x - 8} {y} Q{x} {y - 8} {x + 8} {y}", "none", "#fffdf4", 3))
    return "".join(b)


def wings(rng):
    b = [plate()]
    for i, (x, y, rot) in enumerate([(160, 108, -20), (225, 100, 15), (150, 168, 25), (215, 175, -15), (185, 138, 60)]):
        b.append(ell(x, y, 36, 22, "#c9661f", rot))
        b.append(ell(x - 4, y - 5, 22, 9, "#e08a3a", rot, 0).replace('stroke-width', 'x'))
        ex = x + 36 * math.cos(math.radians(rot + 180)); ey = y + 36 * math.sin(math.radians(rot + 180))
        b.append(line(x, y, ex, ey, "#f6efe0", 7)); b.append(circ(ex, ey, 5, "#f6efe0", 2))
        for sx, sy in pts(rng, 4, x, y, 20):
            b.append(dot(sx, sy, 1.6, "#fff1c9"))
    b.append(circ(290, 150, 24, "#fffdf5")); b.append(circ(290, 150, 17, "#f4e8c8", 1.4))
    b.append(rect(106, 214, 70, 12, "#9fcf7a", 5, -8, 2)); b.append(rect(112, 228, 66, 12, "#9fcf7a", 5, -4, 2))
    return "".join(b)


def bruschetta(rng):
    b = [circ(200, 150, 124, "#b98353"), circ(200, 150, 112, "#c9955f", 1.6)]
    for (x, y, rot) in [(150, 108, -8), (232, 104, 6), (146, 188, 5), (230, 190, -6)]:
        b.append(rect(x - 42, y - 30, 84, 60, "#e0b36a", 14, rot))
        b.append(rect(x - 36, y - 24, 72, 48, "#ecc888", 10, rot, 1.2))
        for tx, ty in pts(rng, 8, x, y, 24):
            b.append(rect(tx - 5, ty - 5, 10, 10, "#d63a2c", 2, rng.uniform(0, 90), 1.8))
        b.append(leaf(x + 6, y - 2, rng.uniform(0, 60), 10))
        for tx, ty in pts(rng, 3, x, y, 20):
            b.append(dot(tx, ty, 2, "#f8e58a"))
    return "".join(b)


def garlic_bread(rng):
    b = [plate(200, 150, 124)]
    spots = [(130, 120), (190, 110), (250, 120), (150, 175), (215, 172), (270, 170)]
    for i, (x, y) in enumerate(spots):
        rot = -25 if i < 3 else 20
        b.append(ell(x, y, 36, 26, "#c9863a", rot))
        b.append(ell(x, y, 29, 20, "#f0cf87", rot, 1.4))
        b.append(ell(x, y, 22, 14, "#f7e29a", rot, 0).replace('stroke-width', 'x'))
        for px, py in pts(rng, 5, x, y, 15):
            b.append(dot(px, py, 2, "#4f8a3c"))
    return "".join(b)


def lava_cake(rng):
    b = [plate_side(200, 218, 138, 40)]
    b.append(path("M110 212 Q150 188 215 206 T300 214 Q260 232 190 234 Q130 234 110 212 Z", "#4a1f12"))
    b.append(path("M122 196 Q122 112 200 112 Q278 112 278 196 Z", "#6b3320"))
    b.append(path("M122 196 L278 196 L270 214 L130 214 Z", "#5b2a17"))
    b.append(path("M170 114 Q200 138 232 114", "none", "#2e0f07", 5))
    b.append(path("M186 120 Q198 150 190 178 Q184 200 200 206", "none", "#2e0f07", 6))
    for x, y in [(150, 135), (190, 128), (240, 140), (225, 128), (165, 150)]:
        b.append(dot(x, y, 1.8, "#f4e7d2"))
    for x, y in [(246, 108), (262, 120), (230, 100)]:
        b.append(circ(x, y, 9, "#c4283d", 2)); b.append(dot(x - 2, y - 2, 1.6, "#ee7d8a"))
    b.append(leaf(210, 104, -20, 12))
    return "".join(b)


def tiramisu(rng):
    b = [plate_side(200, 224, 140, 38)]
    layers = [("#5a3220", 112, 14), ("#fbf0d4", 126, 20), ("#e1b878", 146, 20), ("#fbf0d4", 166, 20), ("#e1b878", 186, 22)]
    for color, y, h in layers:
        b.append(rect(120, y, 160, h, color, 3))
    for x, y in pts(rng, 18, 200, 118, 74):
        if 124 < x < 276 and 112 < y < 126:
            b.append(dot(x, y, 1.6, "#d8b9a0"))
    for x, y in [(110, 104), (292, 206)]:
        b.append(ell(x, y, 8, 5, "#3a1c10", 35, 1.8))
    b.append(leaf(250, 106, -30, 12))
    return "".join(b)


def cheesecake(rng):
    b = [plate_side(200, 224, 140, 38)]
    b.append(path("M112 206 L288 206 L288 188 L112 188 Z", "#b97b3e"))
    b.append(path("M112 190 L288 190 L288 136 Q200 118 112 136 Z", "#fbeed0"))
    b.append(path("M112 138 Q200 118 288 138 L288 150 Q270 168 252 150 Q236 176 218 152 Q200 172 182 150 Q164 178 146 152 Q128 168 112 150 Z", "#c8283c"))
    for x, y in [(160, 124), (205, 118), (250, 126)]:
        b.append(path(f"M{x - 17} {y} Q{x - 17} {y - 20} {x} {y - 20} Q{x + 17} {y - 20} {x + 17} {y} Q{x} {y + 18} {x - 17} {y} Z", "#d63a4c"))
        b.append(dot(x - 4, y - 8, 1.6, "#f6b4bb")); b.append(dot(x + 5, y - 7, 1.6, "#f6b4bb"))
    return "".join(b)


def glass(liquid, rng, kind):
    b = [f'<ellipse cx="200" cy="262" rx="82" ry="12" fill="{INK}" fill-opacity=".18" stroke="none"/>']
    b.append(path("M138 70 L262 70 L250 238 Q200 250 150 238 Z", "#fffaf0"))
    b.append(path("M143 98 L257 98 L247 232 Q200 243 153 232 Z", liquid))
    if kind == "coffee":
        b.append(path("M143 98 L257 98 L255 140 Q200 156 145 140 Z", "#ead6b4"))
        b.append(path("M148 128 Q175 150 200 130 T252 138", "none", "#c9a273", 3))
    for x, y, rot in [(170, 120, 12), (222, 112, -10), (192, 158, 28), (232, 168, -18), (168, 190, -8)]:
        b.append(rect(x - 16, y - 16, 32, 32, "#e8f4f8", 6, rot, 2))
    if kind == "lemon":
        b.append(circ(252, 76, 26, "#f6dc5a"))
        for a in range(0, 360, 45):
            b.append(line(252, 76, 252 + 22 * math.cos(math.radians(a)), 76 + 22 * math.sin(math.radians(a)), INK, 1.2))
        b.append(leaf(165, 66, -30, 16)); b.append(leaf(185, 58, 10, 14))
    elif kind == "mint":
        b.append(circ(252, 76, 26, "#8cc152"))
        for a in range(0, 360, 45):
            b.append(line(252, 76, 252 + 22 * math.cos(math.radians(a)), 76 + 22 * math.sin(math.radians(a)), INK, 1.2))
        b.append(leaf(165, 66, -30, 16)); b.append(leaf(190, 56, 15, 15)); b.append(leaf(150, 80, 30, 13))
        for x in range(150, 252, 11):
            b.append(dot(x, 70, 2.4, "#ffffff"))
    else:
        for x, y in [(110, 120), (292, 214)]:
            b.append(ell(x, y, 8, 5, "#3a1c10", 30, 1.8))
    b.append(line(205, 40, 188, 220, "#b3202f", 9)); b.append(line(205, 40, 188, 220, "#ffffff", 3))
    return "".join(b)


DISHES = {
    "bruschetta": lambda r: bruschetta(r),
    "garlic-bread": lambda r: garlic_bread(r),
    "tomato-soup": lambda r: soup(r),
    "chicken-wings": lambda r: wings(r),
    "caesar-salad": lambda r: salad(r),
    "margherita-pizza": lambda r: pizza(r, "margherita"),
    "pepperoni-pizza": lambda r: pizza(r, "pepperoni"),
    "bbq-chicken-pizza": lambda r: pizza(r, "bbq"),
    "spaghetti-bolognese": lambda r: spaghetti(r),
    "fettuccine-alfredo": lambda r: fettuccine(r),
    "penne-arrabbiata": lambda r: penne(r),
    "grilled-chicken": lambda r: steak(r, "chicken"),
    "beef-steak": lambda r: steak(r, "beef"),
    "beef-burger": lambda r: burger(r, "beef"),
    "chicken-burger": lambda r: burger(r, "chicken"),
    "grilled-fish": lambda r: steak(r, "fish"),
    "club-sandwich": lambda r: club(r),
    "lava-cake": lambda r: lava_cake(r),
    "tiramisu": lambda r: tiramisu(r),
    "cheesecake": lambda r: cheesecake(r),
    "lemonade": lambda r: glass("#f6e27a", r, "lemon"),
    "mint-margarita": lambda r: glass("#a5d96b", r, "mint"),
    "iced-coffee": lambda r: glass("#6b3a1f", r, "coffee"),
}

BACKGROUNDS = ["#f2e3cf", "#f1dcd0", "#efe6cf", "#f3dfd6"]


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for i, (slug, fn) in enumerate(DISHES.items()):
        rng = random.Random(zlib.crc32(slug.encode()))
        (OUT / f"{slug}.svg").write_text(wrap(fn(rng), BACKGROUNDS[i % len(BACKGROUNDS)]), encoding="utf-8")
    print(f"Wrote {len(DISHES)} illustrations to {OUT}")
