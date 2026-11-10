"""Generate the profile README artwork in art/, in the look of the Classic theme on hassaan.space.

All text is converted to vector outlines, so the SVGs render the same inside
GitHub's <img> sandbox, which blocks web fonts. Facts come from https://hassaan.space/.

    pip install fonttools
    python scripts/build.py    # artwork
    python scripts/readme.py   # README.md

Fonts (SIL OFL) download into scripts/fonts/ on first run.
scripts/img/ holds the stadium, the players and the ball from the site's football game.
scripts/game/track.json is one recorded stretch of the site's demo match: two goals, then it loops.
"""
import base64
import json
import math
import re
import pathlib
import urllib.request
from datetime import date
from xml.sax.saxutils import escape

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT / "scripts" / "fonts"
IMG = ROOT / "scripts" / "img"
OUT = ROOT / "art"
OFL = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
SOURCES = {
    "Inter.ttf": OFL + "inter/Inter%5Bopsz%2Cwght%5D.ttf",
    "CascadiaCode.ttf": OFL + "cascadiacode/CascadiaCode%5Bwght%5D.ttf",
}

# Classic tokens from styles/globals.css on the site. `line` is --line (border mixed into background).
THEMES = {
    "light": dict(bg="#fcfcfe", fg="#0f1428", dim="#586178", line="#e8ebf4", border="#dde2ee", muted="#f0f3fa",
                  pop="#ffffff", acc="#2e5ce6", info="#e8930c", ok="#10b981", frame="#151b2c", hatch=".13"),
    "dark": dict(bg="#070a14", fg="#eef1f8", dim="#9aa3b8", line="#151b2b", border="#1d2438", muted="#151b2c",
                 pop="#0f1424", acc="#5b84f7", info="#ffc24a", ok="#34d399", frame="#2a3350", hatch=".16"),
}


# ---------------------------------------------------------------- type

class Face:
    def __init__(self, file, **axes):
        path = FONTS / file
        if not path.exists():
            FONTS.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(SOURCES[file], path)
        self.font = instancer.instantiateVariableFont(TTFont(path), axes)
        self.glyphs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upm = self.font["head"].unitsPerEm

    def name(self, c):
        assert ord(c) in self.cmap, f"font has no glyph for {c!r}"  # a missing glyph draws an empty box
        return self.cmap[ord(c)]

    def width(self, s, size, ls=0):
        adv = sum(self.glyphs[self.name(c)].width for c in s)
        return adv * size / self.upm + ls * max(len(s) - 1, 0)

    def path(self, s, x, y, size, ls=0, anchor="start"):
        if anchor != "start":
            x -= self.width(s, size, ls) / (2 if anchor == "middle" else 1)
        k = size / self.upm
        out = []
        for c in s:
            g = self.glyphs[self.name(c)]
            pen = SVGPathPen(self.glyphs, lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
            g.draw(TransformPen(pen, (k, 0, 0, -k, x, y)))
            out.append(pen.getCommands())
            x += g.width * k + ls
        return "".join(out)


SEMI = MED = BODY = MONO = MONOB = None


def load_fonts():
    global SEMI, MED, BODY, MONO, MONOB
    SEMI = Face("Inter.ttf", wght=600, opsz=32)
    MED = Face("Inter.ttf", wght=500, opsz=14)
    BODY = Face("Inter.ttf", wght=400, opsz=14)
    MONO = Face("CascadiaCode.ttf", wght=400)
    MONOB = Face("CascadiaCode.ttf", wght=700)


def T(face, s, x, y, size, fill, ls=0, anchor="start"):
    return f'<path d="{face.path(s, x, y, size, ls, anchor)}" fill="{fill}"/>'


def wrap(face, s, size, max_w):
    lines, cur = [], ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        if cur and face.width(trial, size) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + [cur]


def para(face, s, x, y, size, fill, max_w, lh=1.55):
    lines = wrap(face, s, size, max_w)
    return "".join(T(face, ln, x, y + i * size * lh, size, fill) for i, ln in enumerate(lines)), len(lines) * size * lh


# ---------------------------------------------------------------- frame

CSS = ("@keyframes pulse{0%,100%{opacity:.15}50%{opacity:.5}}.pulse{animation:pulse 2.4s ease-in-out infinite}"
       "@media (prefers-reduced-motion:reduce){*{animation:none!important}}")
BAND = 28  # the hatched divider between sections


def lay(mobile):
    """Width, gutter (the hatched strip outside the column) and the left edge of content."""
    return (420, 8, 22) if mobile else (860, 14, 32)


def hline(t, W, g, y):
    return f'<path d="M{g} {y}H{W - g}" stroke="{t["line"]}"/>'


def svg(W, H, t, g, title, body, css=""):
    """The page column: hatched gutters, a hairline down each side."""
    title = escape(title, {'"': "&quot;"})
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{title}">'
        f"<title>{title}</title><style>{css}{CSS}</style><defs>"
        f'<pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)">'
        f'<path d="M0 .5H6" stroke="{t["acc"]}" stroke-opacity="{t["hatch"]}"/></pattern>'
        f'<linearGradient id="prism" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t["acc"]}" stop-opacity=".55"/>'
        f'<stop offset="1" stop-color="{t["info"]}" stop-opacity=".75"/></linearGradient></defs>'
        f'<rect width="{W}" height="{H}" fill="{t["bg"]}"/>'
        f'<rect width="{g}" height="{H}" fill="url(#hatch)"/><rect x="{W - g}" width="{g}" height="{H}" fill="url(#hatch)"/>'
        f'<path d="M{g}.5 0V{H}M{W - g}.5 0V{H}" stroke="{t["line"]}"/>'
        f'{body}<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" fill="none" stroke="{t["border"]}"/></svg>'
    )


def band(t, W, g, y):
    """The hatched divider, with a small square on each corner as on the site."""
    sq = lambda x, yy, c: f'<rect x="{x - 2.5}" y="{yy - 2.5}" width="6" height="6" fill="{t["bg"]}" stroke="{c}"/>'
    top = sq(g, y, t["info"]) + sq(W - g, y, t["info"]) if y else ""  # at the top edge of a card they would be cut in half
    return (f'<rect x="{g}" y="{y}" width="{W - 2 * g}" height="{BAND}" fill="url(#hatch)"/>'
            + hline(t, W, 0, y + .5) + hline(t, W, 0, y + BAND + .5)
            + top + sq(g, y + BAND, t["dim"]) + sq(W - g, y + BAND, t["dim"]))


def section(t, mobile, title, idx, sup=""):
    """Divider, then the title with its count and the section number on the right. Returns (svg, y of content)."""
    W, g, pad = lay(mobile)
    size = 22 if mobile else 26
    y = BAND + (36 if mobile else 40)
    out = [band(t, W, g, 0), T(SEMI, title, pad, y, size, t["fg"], ls=-size * .02)]
    if sup:
        out.append(T(MED, sup, pad + SEMI.width(title, size, -size * .02) + 5, y - size * .45, 12.5, t["dim"]))
    out.append(T(MONO, idx, W - pad, y, 12, t["dim"], anchor="end"))
    y += 16
    out.append(hline(t, W, g, y + .5))
    return "".join(out), y


ICONS = {  # Lucide (ISC), 24x24, stroked
    "code": '<path d="m18 16 4-4-4-4M6 8l-4 4 4 4M14.5 4l-5 16"/>',
    "pin": '<path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/>',
    "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    "work": '<path d="M12 12h.01M16 6V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2M22 13a18.15 18.15 0 0 1-20 0"/><rect x="2" y="6" width="20" height="14" rx="2"/>',
    "out": '<path d="M7 7h10v10M7 17 17 7"/>',
}


def icon(name, x, y, size, color):
    return (f'<g transform="translate({x:.1f} {y:.1f}) scale({size / 24:.4f})" fill="none" stroke="{color}" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</g>')


def tile(t, name, x, y, size=26):
    """The site's raised icon tile."""
    return (f'<rect x="{x}" y="{y}" width="{size}" height="{size}" rx="6" fill="{t["muted"]}" stroke="{t["border"]}"/>'
            + icon(name, x + (size - 15) / 2, y + (size - 15) / 2, 15, t["dim"]))


def tags(t, items, x, y, max_x):
    """Mono tags with the blue-to-amber edge. Returns (svg, bottom y)."""
    out, tx = [], x
    for tag in items:
        w = MONO.width(tag, 11.5) + 16
        if tx + w > max_x and tx > x:
            tx, y = x, y + 28
        out.append(f'<rect x="{tx:.1f}" y="{y}" width="{w:.1f}" height="22" rx="5" fill="{t["pop"]}" stroke="url(#prism)"/>'
                   + T(MONO, tag, tx + 8, y + 15.5, 11.5, t["dim"]))
        tx += w + 6
    return "".join(out), y + 22


def now_dot(t, x, y):
    """Amber: this is current."""
    return (f'<circle class="pulse" cx="{x}" cy="{y}" r="8" fill="{t["info"]}" opacity=".3"/>'
            f'<circle cx="{x}" cy="{y}" r="3" fill="{t["info"]}"/>')


def data_uri(file):
    kind = {"png": "image/png", "webp": "image/webp"}[file.rsplit(".", 1)[1]]
    return f"data:{kind};base64," + base64.b64encode((IMG / file).read_bytes()).decode()


# ---------------------------------------------------------------- the football game

TRACK = json.loads((ROOT / "scripts" / "game" / "track.json").read_text())  # 30 samples a second
GW, GROUND = 240, 101            # the game's own units, as in lib/game/config.ts on the site
VIEW_Y, VIEW_H = 24, 94          # the part of the stadium that shows
GOLD, BLUE, CREAM, PLATE = "#ffc873", "#76d4ff", "#fff3d6", "#12142a"


def game(t, x, y, w, mobile, dark):
    """The site's demo match as an animated picture: two players, one ball, two goals, then it loops.
    Positions come from the site's own game rules. Returns (svg, css, height)."""
    t0 = TRACK[0]["t"]
    L = TRACK[-1]["t"] - t0 + 1 / 30
    pct = lambda r: (r["t"] - t0) / L * 100

    def series(get):
        pts = []
        for i, r in enumerate(TRACK):
            if i and TRACK[i - 1]["goal"] and not r["goal"]:  # kick-off: jump there, do not slide
                pts.append((pct(r) - .01, get(TRACK[i - 1])))
            pts.append((pct(r), get(r)))
        return pts + [(100, pts[-1][1])]

    css = []

    def anim(name, get, fmt, step=False):
        pts = series(get)
        keep = [(p, v) for i, (p, v) in enumerate(pts)
                if not (0 < i < len(pts) - 1 and pts[i - 1][1] == v and (step or pts[i + 1][1] == v))]
        css.append(f"@keyframes {name}{{" + "".join(f"{p:.2f}%{{{fmt(v)}}}" for p, v in keep) + "}"
                   f".{name}{{animation:{name} {L:.3f}s {'step-end' if step else 'linear'} infinite}}")

    def shown(name, a, b):
        """Visible only between a% and b% of the loop."""
        on = f"{a:.2f}%{{opacity:1}}" if a else ""
        css.append(f"@keyframes {name}{{0%{{opacity:{0 if a else 1}}}{on}{b:.2f}%{{opacity:0}}100%{{opacity:0}}}}"
                   f".{name}{{animation:{name} {L:.3f}s step-end infinite}}")

    first = TRACK[0]
    k = w / GW
    fh = VIEW_H * k
    px = 'style="image-rendering:pixelated"'
    out = [f'<image href="{data_uri(f"stadium-{"dark" if dark else "light"}.png")}" width="240" height="120" {px}/>']

    def player(key, kit):
        """kit: the row of the sprite sheet for this shirt, by the way the player faces."""
        cell = lambda v: (v[3] % 4, v[3] // 4 + kit(v[2]))
        anim(f"{key}p", lambda r: tuple(r[key][:2]), lambda v: f"transform:translate({v[0]}px,{v[1]}px)")
        anim(f"{key}s", lambda r: r[key][0], lambda v: f"transform:translate({v}px,0)")
        anim(f"{key}d", lambda r: r[key][2], lambda v: f"transform:scaleX({v})", step=True)
        anim(f"{key}f", lambda r: cell(r[key]), lambda v: f"transform:translate({-28 * v[0]}px,{-28 * v[1]}px)", step=True)
        x0, y0, d0, _ = first[key]
        c0 = cell(first[key])
        return (f'<ellipse class="{key}s" transform="translate({x0} 0)" cy="{GROUND + 2}" rx="8" ry="1.5" fill="#06161c" opacity=".5"/>'
                f'<g class="{key}p" transform="translate({x0} {y0})"><g class="{key}d" transform="scale({d0} 1)">'
                f'<svg x="-14" y="-28" width="28" height="28" viewBox="0 0 28 28">'
                f'<image class="{key}f" transform="translate({-28 * c0[0]} {-28 * c0[1]})" href="{data_uri("players.png")}" width="112" height="336" {px}/>'
                f'</svg></g></g>')

    out.append(player("c", lambda d: 8 if d < 0 else 0))   # BRXERQ, in red
    out.append(player("p", lambda d: 4))                    # "You", in blue
    anim("bb", lambda r: tuple(r["b"]), lambda v: f"transform:translate({v[0]}px,{v[1]}px) rotate({v[2]}deg)")
    anim("bs", lambda r: r["b"][0], lambda v: f"transform:translate({v}px,0)")
    bx0, by0, _ = first["b"]
    out.append(f'<ellipse class="bs" transform="translate({bx0} 0)" cy="{GROUND + 2}" rx="4.5" ry="1.2" fill="#06161c" opacity=".4"/>'
               f'<g class="bb" transform="translate({bx0} {by0})"><image href="{data_uri("ball.png")}" x="-5.5" y="-5.5" width="11" height="11" {px}/></g>')

    # each goal: the plate above the net, and the score goes up
    goals, i = [], 0
    while i < len(TRACK):
        if TRACK[i]["goal"]:
            j = i
            while j + 1 < len(TRACK) and TRACK[j + 1]["goal"]:
                j += 1
            goals.append((pct(TRACK[i]), pct(TRACK[j]) + 100 / L / 30, TRACK[i]["last"]))
            i = j
        i += 1
    for n, (a, b, side) in enumerate(goals):
        tint = GOLD if side < 0 else BLUE
        gx = 18 if side < 0 else GW - 62
        shown(f"gl{n}", a, b)
        out.append(f'<g class="gl{n}" opacity="0"><rect x="{gx}" y="54" width="44" height="13" fill="#1c233b"/>'
                   f'<rect x="{gx}" y="54" width="44" height="1" fill="{tint}"/>'
                   + T(MONOB, "GOAL!", gx + 22, 63.6, 8, tint, ls=.6, anchor="middle") + "</g>")

    scene = (f'<clipPath id="pitch"><rect x="{x}" y="{y}" width="{w}" height="{fh:.1f}"/></clipPath>'
             f'<g clip-path="url(#pitch)"><g transform="translate({x} {y - VIEW_Y * k:.2f}) scale({k:.4f})">{"".join(out)}</g></g>')

    # scoreboard: You 0 | 0:59 | 0 BRXERQ
    fs = 8 if mobile else 12.5
    pad, big = fs * .7, fs * 1.3
    dw = MONOB.width("0", big)
    cells = [MONOB.width("You", fs) + pad * 3 + dw + 3, MONOB.width("0:00", fs) + pad * 2.4, MONOB.width("BRXERQ", fs) + pad * 3 + dw + 3]
    sw, sh = sum(cells), fs * 2.3
    sx, sy = x + (w - sw) / 2, y + (5 if mobile else 10)
    base = sy + sh / 2 + fs * .36
    hud = [f'<rect x="{sx - 2:.1f}" y="{sy - 2:.1f}" width="{sw + 4:.1f}" height="{sh + 4:.1f}" fill="#3a3d63" stroke="#0b0d1a"/>'
           f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{sw:.1f}" height="{sh:.1f}" fill="{PLATE}"/>'
           f'<rect x="{sx + cells[0]:.1f}" y="{sy:.1f}" width="{cells[1]:.1f}" height="{sh:.1f}" fill="#2b2b48"/>'
           f'<rect x="{sx:.1f}" y="{sy:.1f}" width="3" height="{sh:.1f}" fill="{BLUE}"/>'
           f'<rect x="{sx + sw - 3:.1f}" y="{sy:.1f}" width="3" height="{sh:.1f}" fill="{GOLD}"/>',
           T(MONOB, "You", sx + 3 + pad, base, fs, "#a9e5ff"),
           T(MONOB, "BRXERQ", sx + sw - 3 - pad, base, fs, "#ffd995", anchor="end")]

    def digits(name, key, dx):
        """One number per value it takes in the loop; only the current one shows."""
        runs = []
        for r in TRACK:
            if not runs or runs[-1][0] != key(r):
                runs.append([key(r), pct(r), 100])
                if len(runs) > 1:
                    runs[-2][2] = pct(r)
        for n, (value, a, b) in enumerate(runs):
            shown(f"{name}{n}", a, b)
            hud.append(f'<g class="{name}{n}" opacity="{0 if n else 1}">' + T(MONOB, value, dx, base + (big - fs) * .3 if len(value) == 1 else base,
                                                                         big if len(value) == 1 else fs, CREAM, anchor="middle") + "</g>")

    digits("sp", lambda r: str(r["score"]), sx + cells[0] - pad - dw / 2)
    digits("sc", lambda r: str(r["cpu"]), sx + cells[0] + cells[1] + pad + dw / 2)
    digits("ck", lambda r: f"0:{math.ceil(r['time']) - 1:02d}", sx + cells[0] + cells[1] / 2)

    # the bar under the pitch
    bh = 24 if mobile else 36
    bs = 8 if mobile else 11
    by = y + fh
    bar = (f'<rect x="{x}" y="{by:.1f}" width="{w}" height="{bh}" fill="{PLATE}"/><path d="M{x} {by + .5:.1f}H{x + w}" stroke="#596579"/>'
           + T(MONOB, "KARACHI ARENA / 1V1", x + (10 if mobile else 18), by + bh / 2 + bs * .36, bs, "#ffd995", ls=bs * .07)
           + T(MONO, "Play it on hassaan.space", x + w - (10 if mobile else 18) - bs * 1.6, by + bh / 2 + bs * .36, bs, "#c9cfe6", anchor="end")
           + icon("out", x + w - (10 if mobile else 18) - bs * 1.15, by + bh / 2 - bs * .55, bs * 1.1, "#c9cfe6"))
    return scene + "".join(hud) + bar, "".join(css), fh + bh


# ---------------------------------------------------------------- hero

INTRO = [("code", "Lead Software Engineer @Global Health"), ("pin", "Karachi, Pakistan"),
         ("mail", "sm.hassaan99@gmail.com"), (None, "Available for freelance projects")]
ROLE = "AI Engineer · Full-Stack Software Developer"


def hero(t, mobile):
    W, g, pad = lay(mobile)
    body = []
    bx, by, bw = pad, pad - g, W - 2 * pad
    r = 6 if mobile else 11
    scene, css, bh = game(t, bx, by, bw, mobile, t is THEMES["dark"])
    bh = round(bh)
    body.append(f'<clipPath id="bn"><rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="{r}"/></clipPath>'
                f'<g clip-path="url(#bn)">{scene}</g>'
                f'<rect x="{bx + .5}" y="{by + .5}" width="{bw - 1}" height="{bh - 1}" rx="{r}" fill="none" stroke="{t["frame"]}" stroke-width="2"/>')
    y = by + bh + (pad - g)
    body.append(hline(t, W, g, y + .5))

    # name and role, under a strip of dots as on the site
    dots, row1, row2 = (26, 36, 30) if mobile else (44, 50, 38)
    body.append(f'<defs><pattern id="dots" width="8" height="8" patternUnits="userSpaceOnUse"><circle cx="4" cy="4" r=".9" fill="{t["acc"]}"/></pattern>'
                f'<linearGradient id="fade" x1="0" x2="1" y1="1" y2="0"><stop offset=".3" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#fff" stop-opacity=".55"/></linearGradient>'
                f'<mask id="dm"><rect x="{g}" y="{y}" width="{W - 2 * g}" height="{dots}" fill="url(#fade)"/></mask></defs>'
                f'<rect x="{g}" y="{y}" width="{W - 2 * g}" height="{dots}" fill="url(#dots)" mask="url(#dm)"/>')
    body.append(hline(t, W, g, y + dots + .5) + hline(t, W, g, y + dots + row1 + .5))
    size = 24 if mobile else 36
    body.append(T(SEMI, "Syed Muhammad Hassaan", pad, y + dots + row1 - (10 if mobile else 12), size, t["fg"], ls=-size * .025))
    body.append(T(MONO, ROLE, pad, y + dots + row1 + row2 / 2 + 4.5, 11.5 if mobile else 14, t["dim"]))
    y += dots + row1 + row2
    body.append(band(t, W, g, y))
    y += BAND

    # what I do now, where, how to reach me
    step = 36
    y += 18
    fs = 12 if mobile else 14
    for i, (ic, text) in enumerate(INTRO):
        ry = y + i * step
        if ic:
            body.append(tile(t, ic, pad, ry))
        else:
            body.append(f'<circle class="pulse" cx="{pad + 13}" cy="{ry + 13}" r="8" fill="{t["ok"]}" opacity=".3"/>'
                        f'<circle cx="{pad + 13}" cy="{ry + 13}" r="3.5" fill="{t["ok"]}"/>')
        body.append(T(MONO, text, pad + 40, ry + 13 + fs * .34, fs, t["fg"]))
    H = int(y + len(INTRO) * step + 8)
    alt = ("A pixel football match from hassaan.space: two players, one ball. Syed Muhammad Hassaan. "
           + ROLE + ". " + ". ".join(text for _, text in INTRO) + ".")
    return svg(W, H, t, g, alt, "".join(body), css)


# ---------------------------------------------------------------- experience

ROLES = [  # company, role, start (y, m), end or None
    ("Global Health", "Lead Software Engineer", (2025, 12), None),
    ("Jordy", "Co-Founder", (2026, 3), None),
    ("Aertonic", "Founding Engineer", (2025, 11), None),
    ("Zao Fi", "Founding Engineer", (2025, 1), None),
    ("Endifaa", "Full-Stack Developer", (2025, 10), (2026, 6)),
    ("Stackloom Technologies", "AI & Prompt Engineer", (2025, 1), (2025, 9)),
    ("Freelance", "AI/ML Engineer & Web Developer", (2024, 7), None),
    ("Quest Marketing Kuching", "Lead AI & Software Engineer", (2024, 3), (2024, 12)),
]


def timeline(t, mobile, today):
    """Experience as bars on a time axis: the site shows a list, the readme shows the overlap."""
    W, g, pad = lay(mobile)
    head, y = section(t, mobile, "Experience", "01")
    body = [head]
    x0, x1 = (pad if mobile else g + 250), W - pad - 6
    start, now = (2024, 1), (today.year, today.month)
    months = lambda ym: (ym[0] - start[0]) * 12 + ym[1] - start[1]
    span = months(now) + 1
    X = lambda ym: x0 + months(ym) / span * (x1 - x0)
    top = y + 34
    rowh = 54 if mobile else 46
    bottom = top + rowh * len(ROLES)
    for yr in range(start[0], today.year + 1):
        gx = X((yr, 1))
        body.append(f'<path d="M{gx:.1f} {y + 12}V{bottom}" stroke="{t["border"]}" stroke-dasharray="2 4"/>'
                    + T(MONO, str(yr), gx + 5, y + 22, 11, t["dim"]))
    if not mobile:
        body.append(f'<path d="M{x0 - 18}.5 {y}V{bottom}" stroke="{t["line"]}"/>')
    for i, (name, role, s, e) in enumerate(ROLES):
        ry = top + i * rowh
        body.append(hline(t, W, g, ry + .5))
        end = e or now
        bx, bw = X(s), X((end[0], end[1] + 1)) - X(s)  # a bar covers its last month
        if mobile:
            body.append(T(MED, name, pad, ry + 21, 13.5, t["fg"]) + T(MONO, role, pad + MED.width(name, 13.5) + 8, ry + 21, 9.5, t["dim"]))
            by = ry + 31
        else:
            body.append(T(MED, name, pad, ry + 21, 14.5, t["fg"]) + T(MONO, role, pad, ry + 36, 10.5, t["dim"]))
            by = ry + 16
        live = e is None
        body.append(f'<rect x="{bx:.1f}" y="{by}" width="{bw:.1f}" height="14" rx="4" fill="{t["acc"] if live else t["dim"]}" fill-opacity="{1 if live else .35}"/>')
        if live:
            body.append(now_dot(t, f"{bx + bw:.1f}", by + 7))
    alt = "Experience, as a timeline from 2024 to now. " + " ".join(
        f"{n}, {r}, {s[1]:02d}.{s[0]} to {'now' if e is None else f'{e[1]:02d}.{e[0]}'}." for n, r, s, e in ROLES)
    return svg(W, int(bottom + 14), t, g, alt, "".join(body))


# ---------------------------------------------------------------- clients

CLIENTS = [  # name, lat, lon, what I built there, Natural Earth name (None: too small at 110m). In the site's order.
    ("Hong Kong", 22.30, 114.17, "Surplus Alliance site", None),
    ("Malaysia", 1.55, 110.35, "Sales Navigator, an AI CRM", "Malaysia"),
    ("Singapore", 1.35, 103.82, "dental, yacht & salon sites", None),
    ("UAE", 25.20, 55.27, "Jordy, Aertonic, RyzunTech", "United Arab Emirates"),
    ("Saudi Arabia", 24.71, 46.68, "Endifaa, voice booking agents", "Saudi Arabia"),
    ("Czechia", 50.08, 14.43, "Global Health automation", "Czechia"),
    ("Norway", 59.91, 10.75, "an AI calling agent", "Norway"),
    ("Spain", 40.42, -3.70, "GP booking, 5 steps to 3", "Spain"),
    ("Portugal", 38.72, -9.14, "Global Health in Portuguese", "Portugal"),
    ("Ireland", 53.35, -6.26, "lead engineer, Global Health", "Ireland"),
    ("Brazil", -15.79, -47.88, "LGPD consent & encryption", "Brazil"),
    ("USA", 40.71, -74.00, "client websites", "United States of America"),
]
COUNTRIES = json.loads((ROOT / "scripts" / "geo" / "countries.json").read_text(encoding="utf-8"))  # Natural Earth, public domain


def geo_path(geom, P):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    out = []
    for poly in polys:
        for ring in poly:
            pts = [P(lon, lat) for lon, lat in ring]
            out.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z")
    return "".join(out)


def world(t, mobile):
    W, g, pad = lay(mobile)
    head, y = section(t, mobile, "Clients", "02", "(12 countries)")
    body = [head]
    # crop to where the clients are: the Americas to East Asia
    lon0, lon1, lat0, lat1 = (-100, 150, -38, 72) if not mobile else (-82, 122, -26, 66)
    mw = W - 2 * pad
    k = mw / (lon1 - lon0)
    mx, my = pad, y + 18
    mh = (lat1 - lat0) * k
    P = lambda lon, lat: (mx + (lon - lon0) * k, my + (lat1 - lat) * k)
    step = 4.4 if not mobile else 3.6
    dot = lambda pid, c, r, o=1: (f'<pattern id="{pid}" width="{step}" height="{step}" patternUnits="userSpaceOnUse">'
                                  f'<circle cx="{step / 2}" cy="{step / 2}" r="{step * r:.2f}" fill="{c}" fill-opacity="{o}"/></pattern>')
    body.append(f'<defs><clipPath id="crop"><rect x="{mx}" y="{my}" width="{mw}" height="{mh:.0f}"/></clipPath>'
                + dot("land", t["dim"], .26, .4) + dot("lit", t["acc"], .38) + dot("home", t["info"], .38) + "</defs>")
    lit = {c[4] for c in CLIENTS if c[4]}

    def visible(geom):  # skip countries entirely outside the crop
        lons = [float(v) for v in re.findall(r"\[(-?[\d.]+),", json.dumps(geom["coordinates"]))]
        return max(lons) > lon0 - 5 and min(lons) < lon1 + 5

    land = "".join(geo_path(geom, P) for name, geom in COUNTRIES.items()
                   if name not in lit and name != "Pakistan" and visible(geom))
    body.append(f'<g clip-path="url(#crop)"><path d="{land}" fill="url(#land)"/>'
                f'<path d="{geo_path(COUNTRIES["Pakistan"], P)}" fill="url(#home)"/>'
                + "".join(f'<path d="{geo_path(COUNTRIES[c[4]], P)}" fill="url(#lit)"/>' for c in CLIENTS if c[4]) + "</g>")
    for name, la, lo, _, shape in CLIENTS:
        if not shape:  # a city state: no outline at this scale, so a dot
            x, yy = P(lo, la)
            body.append(f'<circle cx="{x:.1f}" cy="{yy:.1f}" r="3" fill="{t["acc"]}" stroke="{t["bg"]}" stroke-width="1.5"/>')
    hx, hy = P(67.01, 24.86)
    body.append(now_dot(t, f"{hx:.1f}", f"{hy:.1f}")
                + f'<rect x="{hx + 7:.1f}" y="{hy + 6:.1f}" width="{MONO.width("Karachi", 10) + 10:.1f}" height="16" rx="4" fill="{t["bg"]}" stroke="{t["line"]}"/>'
                + T(MONO, "Karachi", hx + 12, hy + 17.5, 10, t["fg"]))

    # the numbered list, in cells
    y = int(my + mh + 18)
    cols = 2 if mobile else 3
    cw = (W - 2 * g) / cols
    rowh = 40 if mobile else 56
    rows = math.ceil(len(CLIENTS) / cols)
    for i, (name, _, _, what, _) in enumerate(CLIENTS):
        x = g + (i % cols) * cw
        ry = y + (i // cols) * rowh
        ty = ry + (25 if mobile else 24)
        body.append(T(MONO, f"{i + 1:02d}", x + 18, ty, 12, t["dim"]) + T(BODY, name, x + 46, ty, 14.5, t["fg"]))
        if not mobile:
            body.append(T(BODY, what, x + 46, ty + 19, 12.5, t["dim"]))
    for r in range(rows):
        body.append(hline(t, W, g, y + r * rowh + .5))
    for c in range(1, cols):
        body.append(f'<path d="M{g + c * cw:.0f}.5 {y}V{y + rows * rowh}" stroke="{t["line"]}"/>')
    alt = "Clients in 12 countries: " + ", ".join(c[0] for c in CLIENTS) + ". Based in Karachi."
    return svg(W, y + rows * rowh, t, g, alt, "".join(body))


# ---------------------------------------------------------------- live sites

PROJECTS = [  # in the site's order
    dict(slug="global-health", name="Global Health", meta="Lead Software Engineer · Ireland",
         blurb="Online doctor visits in six countries. I rebuilt the platform and lead it end to end, from architecture and security to automation and deployment, under GDPR and LGPD. 86.5% of bookings need no admin touch.",
         tags=["TypeScript", "PostgreSQL", "Payments", "Automation", "GDPR/LGPD"]),
    dict(slug="endifaa", name="Endifaa", meta="Full-Stack Developer · Saudi Arabia",
         blurb="A sports-academy platform in English and Arabic: user, academy and admin portals, subscriptions and checkout, and full right-to-left Arabic.",
         tags=["React", "TypeScript", "RTK Query", "Django/DRF", "PostgreSQL", "Docker"]),
    dict(slug="jordy", name="Jordy", meta="Co-Founder · Dubai",
         blurb="An AI sales rep: it reads your product, finds buyers who need it now, and books meetings through personalised LinkedIn outreach. I built the engine: prospect discovery, research and message writing.",
         tags=["React", "TypeScript", "LLMs", "Automation", "Analytics"]),
    dict(slug="aertonic", name="Aertonic", meta="Founding Engineer · Dubai",
         blurb="Books qualified sales meetings for B2B software companies in the US and UAE, and only charges for the ones that happen. I build the product from zero and set its architecture.",
         tags=["TypeScript", "AI", "Product Engineering"]),
    dict(slug="zaofi", name="Zao Fi", meta="Founding Engineer · Stock AI",
         blurb="A stock AI that watches what whales, insiders and Congress are buying, and turns it into one 0–100 conviction score with the reasons in plain English.",
         tags=["AI", "Market Data", "Explainable Scores"]),
]


def project(t, p, mobile, first):
    """One row of Live sites. Each row is its own picture so that it can link to its own site."""
    W, g, pad = lay(mobile)
    body, y = [], 0
    if first:
        head, y = section(t, mobile, "Live sites", "03", "(12)")
        body.append(head)
    y += 34
    body.append(T(MED, p["name"], pad, y, 20, t["fg"], ls=-.2) + T(MONO, p["meta"], pad, y + 20, 12, t["dim"]))
    bx, by = W - pad - 17, y - 2
    body.append(f'<circle cx="{bx}" cy="{by}" r="16.5" fill="{t["pop"]}" stroke="{t["border"]}"/>' + icon("out", bx - 7.5, by - 7.5, 15, t["fg"]))
    y += 46
    para_svg, ph = para(BODY, p["blurb"], pad, y, 14, t["dim"], W - 2 * pad)
    body.append(para_svg)
    y += ph - 2
    tg_svg, y = tags(t, p["tags"], pad, y, W - pad)
    body.append(tg_svg)
    return svg(W, int(y + 20), t, g, f"{p['name']}. {p['meta']}. {p['blurb']}", "".join(body))


# ---------------------------------------------------------------- stack

STACK = [  # label, [(name, icon file in scripts/icons/, or the letters the site shows)]
    ("Languages", [("Python", "python"), ("TypeScript", "typescript"), ("C++", "cplusplus"), ("Dart", "dart")]),
    ("AI / Data", [("TensorFlow", "tensorflow"), ("PyTorch", "pytorch"), ("OpenCV", "opencv"),
                   ("OpenAI API", "openai"), ("LLMs / NLP", "L")]),
    ("Frameworks", [("React", "react"), ("Next.js", "nextdotjs"), ("Django / DRF", "django"), ("Flutter", "flutter")]),
    ("Backend", [("PostgreSQL", "postgresql"), ("MySQL", "mysql"), ("FastAPI", "fastapi"), ("RabbitMQ", "rabbitmq")]),
    ("Tools", [("Docker", "docker"), ("AWS", "amazonwebservices"), ("Vercel", "vercel"), ("Railway", "railway"), ("Git", "git")]),
    ("AI Workflow", [("Claude", "claude"), ("Codex", "openai"), ("Antigravity", "A"), ("T3 Code", "T3")]),
]


def mark(t, slug, x, y):
    """A 15px brand mark: Simple Icons (CC0) from scripts/icons/, or letters where the site has no mark."""
    file = ROOT / "scripts" / "icons" / f"{slug}.svg"
    if file.exists():
        d = re.search(r' d="([^"]+)"', file.read_text()).group(1)
        return f'<path transform="translate({x:.1f} {y:.1f}) scale({15 / 24:.4f})" d="{d}" fill="{t["dim"]}"/>'
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="15" height="15" rx="3.5" fill="{t["border"]}"/>'
            + T(MONO, slug, x + 7.5, y + 10.8, 8.5, t["dim"], anchor="middle"))


def stack(t, mobile):
    W, g, pad = lay(mobile)
    head, y = section(t, mobile, "Stack", "04")
    body = [head]
    x0 = pad if mobile else g + 196      # where the chips start
    for i, (name, items) in enumerate(STACK):
        if i:
            body.append(hline(t, W, g, y + .5))
        top = y
        y += 16
        if mobile:
            body.append(T(MONO, f"{i + 1:02d}", pad, y + 12, 12, t["dim"]) + T(BODY, name, pad + 26, y + 12, 14, t["fg"]))
            y += 26
        else:
            body.append(T(MONO, f"{i + 1:02d}", pad, y + 21, 12.5, t["dim"]) + T(BODY, name, pad + 27, y + 21, 14.5, t["fg"]))
        cx = x0
        for tool, slug in items:
            w = MED.width(tool, 13.5) + 46
            if cx + w > W - pad and cx > x0:
                cx, y = x0, y + 40
            body.append(f'<rect x="{cx:.1f}" y="{y}" width="{w:.1f}" height="32" rx="8" fill="{t["muted"]}" stroke="{t["border"]}"/>'
                        + mark(t, slug, cx + 11, y + 8.5) + T(MED, tool, cx + 34, y + 20.8, 13.5, t["fg"]))
            cx += w + 8
        y += 32 + 16
        if not mobile:
            body.append(f'<path d="M{x0 - 16}.5 {top}V{y}" stroke="{t["line"]}"/>')
    alt = "Stack. " + ". ".join(f"{n}: " + ", ".join(tool for tool, _ in items) for n, items in STACK) + "."
    return svg(W, int(y), t, g, alt, "".join(body))


# ---------------------------------------------------------------- contact

def contact(t, mobile):
    W, g, pad = lay(mobile)
    head, y = section(t, mobile, "Contact", "05")
    body = [head]
    y += 16
    for ic, text in (("mail", "sm.hassaan99@gmail.com"), ("pin", "Karachi, Pakistan · UTC+5")):
        body.append(tile(t, ic, pad, y) + T(MONO, text, pad + 40, y + 17.8, 13 if mobile else 14, t["fg"]))
        y += 36
    y += 4
    body.append(hline(t, W, g, y + .5))
    y += 18
    bw = SEMI.width("Send message", 14.5) + 44
    body.append(f'<rect x="{pad}" y="{y}" width="{bw:.0f}" height="44" rx="8" fill="{t["fg"]}"/>'
                + T(SEMI, "Send message", pad + 22, y + 27, 14.5, t["bg"]))
    return svg(W, int(y + 44 + 20), t, g, "Contact. Email sm.hassaan99@gmail.com. Karachi, Pakistan, UTC+5.", "".join(body))


# ---------------------------------------------------------------- main

def main():
    load_fonts()
    OUT.mkdir(exist_ok=True)
    today = date.today()
    cards = {"hero": hero, "experience": lambda t, m: timeline(t, m, today), "clients": world, "stack": stack, "contact": contact}
    for i, p in enumerate(PROJECTS):
        cards[p["slug"]] = lambda t, m, p=p, first=i == 0: project(t, p, m, first)
    for slug, fn in cards.items():
        for theme, t in THEMES.items():
            for mobile in (False, True):
                name = f"{slug}-{'mobile-' if mobile else ''}{theme}.svg"
                (OUT / name).write_text(fn(t, mobile), encoding="utf-8")
                print(name)


if __name__ == "__main__":
    main()
