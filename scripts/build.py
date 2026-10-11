"""Generate the profile README artwork in assets/.

All text is converted to vector outlines, so the SVGs render the same inside
GitHub's <img> sandbox, which blocks web fonts. Facts come from brxerq.github.io/app.

    pip install fonttools
    python scripts/build.py    # artwork
    python scripts/readme.py   # README.md

Fonts (SIL OFL) download into scripts/fonts/ on first run.
"""
import json
import math
import re
import pathlib
import urllib.request
from xml.sax.saxutils import escape
from datetime import date

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONTS = ROOT / "scripts" / "fonts"
OUT = ROOT / "assets"
OFL = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
SOURCES = {
    "Unbounded.ttf": OFL + "unbounded/Unbounded%5Bwght%5D.ttf",
    "MartianMono.ttf": OFL + "martianmono/MartianMono%5Bwdth%2Cwght%5D.ttf",
    "Geist.ttf": OFL + "geist/Geist%5Bwght%5D.ttf",
}

# Tokens from the portfolio site. Light mode swaps ink and paper.
THEMES = {
    "dark": dict(bg="#05060a", bg2="#0b0d15", fg="#ece8df", dim="#a3a09a", faint="#1d1f26",
                 line="#33343a", sig="#ffd23f", sig_ink="#05060a", cob="#6b86ff", alarm="#ff5a45"),
    "light": dict(bg="#ece8df", bg2="#e3ded2", fg="#05060a", dim="#55534e", faint="#d6d0c3",
                  line="#bdb7aa", sig="#ffd23f", sig_ink="#05060a", cob="#3a55d6", alarm="#d8402d"),
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
        self.cache = {}

    def width(self, s, size, ls=0):
        adv = sum(self.glyphs[self.cmap.get(ord(c), ".notdef")].width for c in s)
        return adv * size / self.upm + ls * max(len(s) - 1, 0)

    def path(self, s, x, y, size, ls=0, anchor="start"):
        if anchor != "start":
            x -= self.width(s, size, ls) / (2 if anchor == "middle" else 1)
        k = size / self.upm
        out = []
        for c in s:
            name = self.cmap.get(ord(c), ".notdef")
            g = self.glyphs[name]
            pen = SVGPathPen(self.glyphs, lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
            g.draw(TransformPen(pen, (k, 0, 0, -k, x, y)))
            out.append(pen.getCommands())
            x += g.width * k + ls
        return "".join(out)


DISPLAY = DISPLAY_LIGHT = MONO = BODY = None


def load_fonts():
    global DISPLAY, DISPLAY_LIGHT, MONO, BODY
    DISPLAY = Face("Unbounded.ttf", wght=700)
    DISPLAY_LIGHT = Face("Unbounded.ttf", wght=300)
    MONO = Face("MartianMono.ttf", wght=400, wdth=100)
    BODY = Face("Geist.ttf", wght=400)


def T(face, s, x, y, size, fill, ls=0, anchor="start", cls="", extra=""):
    c = f' class="{cls}"' if cls else ""
    return f'<path{c} d="{face.path(s, x, y, size, ls, anchor)}" fill="{fill}"{extra}/>'


def label(s, x, y, fill, size=11, anchor="start", cls=""):
    return T(MONO, s.upper(), x, y, size, fill, ls=size * 0.08, anchor=anchor, cls=cls)


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


def para(face, s, x, y, size, fill, max_w, lh=1.5):
    lines = wrap(face, s, size, max_w)
    return "".join(T(face, ln, x, y + i * size * lh, size, fill) for i, ln in enumerate(lines)), len(lines) * size * lh


# ---------------------------------------------------------------- frame

BASE_CSS = """
@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}
@keyframes pulse{0%,100%{opacity:.35}50%{opacity:1}}
@keyframes ring{0%{transform:scale(.4);opacity:.9}100%{transform:scale(2.6);opacity:0}}
@keyframes rise{from{transform:translateY(14px);opacity:0}to{transform:none;opacity:1}}
@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes scan{from{transform:translateX(-120px)}to{transform:translateX(var(--w))}}
.blink{animation:blink 1.1s steps(1) infinite}
.pulse{animation:pulse 2.4s ease-in-out infinite}
.ring{transform-box:fill-box;transform-origin:center;animation:ring 2.4s ease-out infinite}
.rise{animation:rise .9s cubic-bezier(.2,.8,.2,1) both}
.grow{transform-box:fill-box;transform-origin:left;animation:grow 1.4s cubic-bezier(.2,.8,.2,1) both}
"""
REDUCE = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


def svg(w, h, t, title, body, css=""):
    title = escape(title, {'"': "&quot;"})
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{title}">'
        f"<title>{title}</title><style>{BASE_CSS}{css}{REDUCE}</style>"
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="18" fill="{t["bg"]}" stroke="{t["line"]}"/>'
        f"{body}</svg>"
    )


def section_head(t, num, name, x, y):
    """`01 — CLIENTS` style kicker with a signal tick."""
    return (f'<rect x="{x}" y="{y - 9}" width="8" height="8" fill="{t["sig"]}"/>'
            + label(f"{num} / {name}", x + 18, y, t["dim"]))


def dot_grid(t, w, h, step=26):
    return (f'<defs><pattern id="grid" width="{step}" height="{step}" patternUnits="userSpaceOnUse">'
            f'<circle cx="1" cy="1" r="1" fill="{t["faint"]}"/></pattern></defs>'
            f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="18" fill="url(#grid)"/>')


# ---------------------------------------------------------------- hero

STATS = [("12", "client countries"), ("13", "products & sites shipped"),
         ("4,500+", "automation runs / 90 days"), ("95%", "voice-agent booking accuracy")]

WHOAMI = [
    ("$ ", "whoami"),
    ("", "hassaan — ai engineer, full-stack dev"),
    ("$ ", "cat now.txt"),
    ("", "lead eng      global health  [IE]"),
    ("", "co-founder    jordy          [AE]"),
    ("", "founding eng  aertonic       [AE]"),
    ("", "building      zao fi         [own]"),
    ("$ ", "status"),
    ("", "available for freelance projects"),
]


def odometer(t, value, x, y, size, delay, cid):
    """Digits roll from 0 to their value. With motion off, they sit at the value."""
    out, cx = [], x
    for i, ch in enumerate(value):
        w = DISPLAY.width(ch, size)
        if ch.isdigit():
            n = int(ch) + 10  # one full turn, then land
            stack = "".join(T(DISPLAY, str((int(ch) - k) % 10), cx, y - k * size * 1.2, size, t["fg"])
                            for k in range(n + 1))
            out.append(f'<g class="roll" style="--n:{n * size * 1.2:.0f}px;animation-delay:{delay + i * .08:.2f}s">{stack}</g>')
        else:
            out.append(T(DISPLAY, ch, cx, y, size, t["sig"]))
        cx += w
    return f'<g clip-path="url(#{cid})">{"".join(out)}</g>'


def hero(t, mobile):
    W = 480 if mobile else 1040
    pad = 40
    body = [dot_grid(t, W, 2000)]
    # status pill
    pill = "available for freelance · karachi, pk · utc+5"
    pw = MONO.width(pill.upper(), 10, .8) + 44
    body.append(f'<rect x="{pad}" y="34" width="{pw:.0f}" height="28" rx="14" fill="{t["bg2"]}" stroke="{t["line"]}"/>'
                f'<circle cx="{pad + 16}" cy="48" r="4" fill="{t["sig"]}"/>'
                f'<circle class="ring" cx="{pad + 16}" cy="48" r="4" fill="none" stroke="{t["sig"]}"/>'
                + label(pill, pad + 30, 52, t["fg"], 10))
    if not mobile:
        body.append(label("fig. 00 — the engineer", W - pad, 52, t["dim"], 10, "end"))

    # name
    y = 132 if not mobile else 128
    body.append(T(DISPLAY_LIGHT, "Syed Muhammad", pad, y, 40 if not mobile else 30, t["fg"], cls="rise"))
    y += 72 if not mobile else 64
    big = 76 if not mobile else 56
    body.append(T(DISPLAY, "Hassaan", pad, y, big, t["fg"], cls="rise", extra=' style="animation-delay:.12s"'))
    hw = DISPLAY.width("Hassaan", big)
    body.append(f'<rect class="blink" x="{pad + hw + 10:.0f}" y="{y - big * .72:.0f}" width="{big * .14:.0f}" height="{big * .72:.0f}" fill="{t["sig"]}"/>')
    y += 44
    body.append(T(MONO, "AI ENGINEER & FULL-STACK DEVELOPER", pad, y, 13, t["sig"] if t["bg"] == "#05060a" else t["cob"], ls=1.2))
    y += 34
    blurb = ("I design and build AI products, web platforms and automation for startups and businesses "
             "around the world. Clients in 12 countries. Co-founded Jordy, built Zao Fi.")
    p, ph = para(BODY, blurb, pad, y, 17, t["dim"], 470 if not mobile else W - 2 * pad)
    body.append(p)
    y += ph

    # terminal
    if mobile:
        tx, ty, tw = pad, y + 18, W - 2 * pad
    else:
        tx, ty, tw = 600, 86, W - 600 - pad
    lh = 25
    th = 46 + lh * (len(WHOAMI) + 1) + 10
    body.append(f'<rect x="{tx}" y="{ty}" width="{tw}" height="{th}" rx="12" fill="{t["bg2"]}" stroke="{t["line"]}"/>'
                + "".join(f'<circle cx="{tx + 20 + i * 16}" cy="{ty + 20}" r="4.5" fill="{c}"/>'
                          for i, c in enumerate((t["alarm"], t["sig"], t["cob"])))
                + label("~/brxerq — zsh", tx + tw - 16, ty + 24, t["dim"], 9, "end"))
    css = []
    clock = 0.4
    body.append(f'<clipPath id="term"><rect x="{tx}" y="{ty}" width="{tw}" height="{th}" rx="12"/></clipPath><g clip-path="url(#term)">')
    ly = ty + 50
    for i, (prompt, text) in enumerate(WHOAMI):
        ly += lh
        lx = tx + 18
        color = t["fg"] if prompt else t["dim"]
        if prompt:
            body.append(T(MONO, prompt, lx, ly, 12, t["sig"] if t["bg"] == "#05060a" else t["cob"]))
            lx += MONO.width(prompt, 12)
        body.append(T(MONO, text, lx, ly, 12, color))
        # typing: a cover slides off the line in character-sized steps
        n = len(text)
        dur = n * (0.045 if prompt else 0.012)
        cw = MONO.width(text, 12) + 14
        body.append(f'<rect class="type" x="{lx - 1:.0f}" y="{ly - 15}" width="{cw:.0f}" height="{lh - 2}" fill="{t["bg2"]}"'
                    f' style="--w:{cw:.0f}px;animation:type {dur:.2f}s steps({n}) {clock:.2f}s both"/>')
        clock += dur + (0.25 if prompt else 0.08)
    body.append("</g>")
    body.append(f'<rect class="blink" x="{tx + 18}" y="{ly + 10}" width="8" height="15" fill="{t["sig"]}" '
                f'style="animation-delay:{clock:.1f}s"/>')
    css.append("@keyframes type{from{transform:translateX(0)}to{transform:translateX(var(--w))}}"
               ".type{transform:translateX(var(--w))}")

    # stats strip
    sy = max(y, ty + th) + 36 if not mobile else ty + th + 36
    body.append(f'<path d="M{pad} {sy}H{W - pad}" stroke="{t["line"]}"/>')
    cols = 2 if mobile else 4
    cw = (W - 2 * pad) / cols
    defs = []
    for i, (v, k) in enumerate(STATS):
        cx = pad + (i % cols) * cw
        cy = sy + 62 + (i // cols) * 92
        cid = f"odo{i}"
        defs.append(f'<clipPath id="{cid}"><rect x="{cx}" y="{cy - 46}" width="{cw}" height="56"/></clipPath>')
        body.append(odometer(t, v, cx, cy, 42 if not mobile else 34, 0.6 + i * .25, cid))
        body.append(label(k, cx, cy + 26, t["dim"], 9.5 if not mobile else 8.5))
    css.append("@keyframes roll{from{transform:translateY(var(--n))}to{transform:none}}"
               ".roll{animation:roll 1.8s cubic-bezier(.2,.8,.2,1) both}")
    H = int(cy + 60)
    body.insert(0, f"<defs>{''.join(defs)}</defs>")
    alt = "Syed Muhammad Hassaan. AI engineer and full-stack developer. Clients in 12 countries."
    return svg(W, H, t, alt, "".join(body), "".join(css))


# ---------------------------------------------------------------- client map

KARACHI = (24.86, 67.01)
CLIENTS = [  # name, lat, lon, what I built there, Natural Earth name (None: too small at 110m), badge offset px
    ("UAE", 25.20, 55.27, "Jordy, Aertonic, RyzunTech", "United Arab Emirates", (14, 13)),
    ("Saudi Arabia", 24.71, 46.68, "Endifaa, voice booking agents", "Saudi Arabia", (-16, 13)),
    ("Singapore", 1.35, 103.82, "dental, yacht & salon sites", None, (-16, 12)),
    ("Malaysia", 1.55, 110.35, "Sales Navigator, an AI CRM", "Malaysia", (16, 10)),
    ("Hong Kong", 22.30, 114.17, "Surplus Alliance site", None, (16, -6)),
    ("Czechia", 50.08, 14.43, "Global Health automation", "Czechia", (16, 6)),
    ("Norway", 59.91, 10.75, "an AI calling agent", "Norway", (14, -11)),
    ("Ireland", 53.35, -6.26, "lead engineer, Global Health", "Ireland", (-17, -8)),
    ("Spain", 40.42, -3.70, "GP booking, 5 steps to 3", "Spain", (16, 9)),
    ("Portugal", 38.72, -9.14, "Global Health in Portuguese", "Portugal", (-17, 9)),
    ("Brazil", -15.79, -47.88, "LGPD consent & encryption", "Brazil", (16, 0)),
    ("USA", 40.71, -74.00, "client websites", "United States of America", (-17, -8)),
]
COUNTRIES = json.loads((ROOT / "scripts" / "geo" / "countries.json").read_text(encoding="utf-8"))  # Natural Earth, public domain


def bearing_distance(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    d = math.acos(min(1, math.sin(la1) * math.sin(la2) + math.cos(la1) * math.cos(la2) * math.cos(lo2 - lo1)))
    brg = math.atan2(math.sin(lo2 - lo1) * math.cos(la2),
                     math.cos(la1) * math.sin(la2) - math.sin(la1) * math.cos(la2) * math.cos(lo2 - lo1))
    return math.degrees(brg) % 360, d * 6371


def geo_path(geom, P):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    out = []
    for poly in polys:
        for ring in poly:
            pts = [P(lon, lat) for lon, lat in ring]
            out.append("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z")
    return "".join(out)


def world(t, mobile):
    W = 480 if mobile else 1040
    pad = 40 if not mobile else 20
    acc = t["sig"] if t["bg"] == "#05060a" else t["cob"]
    # crop to where the clients are: the Americas to East Asia
    lon0, lon1, lat0, lat1 = (-100, 150, -38, 72) if not mobile else (-82, 122, -26, 66)
    mw = W - 2 * pad
    k = mw / (lon1 - lon0)
    mx, my = pad, 150 if not mobile else 160
    mh = (lat1 - lat0) * k
    P = lambda lon, lat: (mx + (lon - lon0) * k, my + (lat1 - lat) * k)
    hp = 40 if not mobile else 20
    body = [section_head(t, "01", "clients", hp, 52), T(DISPLAY, "Twelve countries,", hp, 96, 30, t["fg"])]
    if mobile:
        body.append(T(DISPLAY_LIGHT, "one desk in Karachi.", hp, 134, 30, t["fg"]))
    else:
        body.append(T(DISPLAY_LIGHT, "one desk in Karachi.", hp + DISPLAY.width("Twelve countries, ", 30), 96, 30, t["fg"]))

    step = 5 if not mobile else 4.2
    body.append(
        f'<defs><clipPath id="crop"><rect x="{mx}" y="{my}" width="{mw}" height="{mh:.0f}"/></clipPath>'
        f'<pattern id="land" width="{step}" height="{step}" patternUnits="userSpaceOnUse"><circle cx="{step / 2}" cy="{step / 2}" r="{step * .26:.2f}" fill="{t["dim"]}" fill-opacity=".32"/></pattern>'
        f'<pattern id="lit" width="{step}" height="{step}" patternUnits="userSpaceOnUse"><circle cx="{step / 2}" cy="{step / 2}" r="{step * .36:.2f}" fill="{t["sig"]}"/></pattern>'
        f'<pattern id="home" width="{step}" height="{step}" patternUnits="userSpaceOnUse"><circle cx="{step / 2}" cy="{step / 2}" r="{step * .36:.2f}" fill="{t["fg"]}"/></pattern>'
        f"</defs>")
    lit = {c[4] for c in CLIENTS if c[4]}
    def visible(g):  # skip countries entirely outside the crop
        flat = json.dumps(g["coordinates"])
        lons = [float(v) for v in re.findall(r"\[(-?[\d.]+),", flat)]
        return max(lons) > lon0 - 5 and min(lons) < lon1 + 5
    land = "".join(geo_path(g, P) for name, g in COUNTRIES.items()
                   if name not in lit and name != "Pakistan" and visible(g))
    body.append(f'<g clip-path="url(#crop)"><path d="{land}" fill="url(#land)"/>')
    body.append(f'<path d="{geo_path(COUNTRIES["Pakistan"], P)}" fill="url(#home)"/>')
    for i, c in enumerate(c for c in CLIENTS if c[4]):
        body.append(f'<path class="rise" d="{geo_path(COUNTRIES[c[4]], P)}" fill="url(#lit)" style="animation-delay:{.3 + i * .08:.2f}s"/>')
    body.append("</g>")
    # equator and tropics, faint
    for lat, dash in ((0, "2 6"), (23.44, "1 6"), (-23.44, "1 6")):
        y = P(0, lat)[1]
        body.append(f'<path d="M{mx} {y:.1f}H{mx + mw}" stroke="{t["line"]}" stroke-dasharray="{dash}"/>')

    hx, hy = P(67.01, 24.86)
    nodes = []
    for i, (name, la, lo, what, _, off) in enumerate(sorted(CLIENTS, key=lambda c: bearing_distance(KARACHI, c[1:3])[1])):
        nodes.append(dict(n=f"{i + 1:02d}", name=name, what=what, xy=P(lo, la), off=off,
                          km=bearing_distance(KARACHI, (la, lo))[1]))
    # arcs from Karachi: drawn in once, then a packet keeps travelling along each
    for i, nd in enumerate(nodes):
        x, y = nd["xy"]
        dist = math.hypot(x - hx, y - hy)
        cxq, cyq = (hx + x) / 2, (hy + y) / 2 - dist * .28
        route = f"M{hx:.1f} {hy:.1f}Q{cxq:.1f} {cyq:.1f} {x:.1f} {y:.1f}"
        body.append(f'<path class="draw" d="{route}" fill="none" stroke="{t["sig"]}" stroke-opacity=".45" pathLength="100" '
                    f'stroke-dasharray="100" style="animation-delay:{.6 + i * .12:.2f}s"/>'
                    f'<path class="packet" d="{route}" fill="none" stroke="{t["sig"]}" stroke-width="2" stroke-linecap="round" '
                    f'pathLength="100" stroke-dasharray="2.5 97.5" style="animation-delay:{-(i * .37) % 3.2:.2f}s"/>')
    # markers + numbered badges
    for i, nd in enumerate(nodes):
        x, y = nd["xy"]
        dx, dy = nd["off"]
        bx, by = x + dx, y + dy
        body.append(f'<path d="M{x:.1f} {y:.1f}L{bx:.1f} {by:.1f}" stroke="{t["fg"]}" stroke-opacity=".5"/>'
                    f'<circle class="ring" cx="{x:.1f}" cy="{y:.1f}" r="3" fill="none" stroke="{t["sig"]}" style="animation-delay:{i * .2:.1f}s"/>'
                    f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{t["sig"]}" stroke="{t["bg"]}" stroke-width="1.5"/>'
                    f'<rect x="{bx - 11:.1f}" y="{by - 7.5:.1f}" width="22" height="15" rx="7.5" fill="{t["bg"]}" stroke="{t["sig"]}" stroke-opacity=".7"/>'
                    + label(nd["n"], bx + .5, by + 3.3, t["fg"], 8, "middle"))
    # Karachi
    body.append(f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="5" fill="{t["fg"]}" stroke="{t["bg"]}" stroke-width="2"/>'
                f'<circle class="ring" cx="{hx:.1f}" cy="{hy:.1f}" r="5" fill="none" stroke="{t["fg"]}"/>'
                + f'<rect x="{hx + 6:.1f}" y="{hy + 7:.1f}" width="{MONO.width("KARACHI", 8, .64) + 8:.1f}" height="13" rx="3" fill="{t["bg"]}"/>'
                + label("karachi", hx + 10, hy + 16.5, t["fg"], 8))

    css = ("@keyframes draw{from{stroke-dashoffset:100}to{stroke-dashoffset:0}}"
           ".draw{animation:draw 1.4s cubic-bezier(.4,0,.2,1) both}"
           "@keyframes packet{from{stroke-dashoffset:100}to{stroke-dashoffset:0}}"
           ".packet{animation:packet 3.2s linear infinite}")

    # ledger under the map
    ly = my + mh + 46
    cols = 1 if mobile else 3
    cw = (W - 2 * hp) / cols
    rowh = 30
    rows = math.ceil(len(nodes) / cols)
    for i, nd in enumerate(nodes):
        x = hp + (i // rows) * cw
        y = ly + (i % rows) * rowh
        body.append(f'<path d="M{x:.0f} {y + 11}H{x + cw - 24:.0f}" stroke="{t["line"]}" stroke-opacity=".6"/>')
        body.append(label(nd["n"], x, y, acc, 9))
        body.append(T(BODY, nd["name"], x + 28, y, 13.5, t["fg"]))
        body.append(T(BODY, nd["what"], x + 28 + 94, y, 12, t["dim"]))
    H = int(ly + rows * rowh + 14)
    alt = ("World map of clients in 12 countries, with arcs from Karachi to " + ", ".join(nd["name"] for nd in nodes) + ".")
    return svg(W, H, t, alt, "".join(body), css)


# ---------------------------------------------------------------- project cards

PROJECTS = [
    dict(slug="global-health", n="01", name="Global Health", meta="lead software engineer · ireland · since dec 2025",
         blurb="Online doctor visits in six countries. I rebuilt the platform and lead it end to end, from architecture and security to automation and deployment, under GDPR and LGPD.",
         metrics=[("86.5%", "bookings, no admin touch"), ("4,500+", "automation runs / 90d"), ("5→3", "same-day GP steps"), ("96–98", "desktop lighthouse")],
         tags=["TypeScript", "PostgreSQL", "Payments", "Automation", "GDPR/LGPD"], motif="pulse"),
    dict(slug="jordy", n="02", name="Jordy", meta="co-founder · dubai · since mar 2026",
         blurb="An AI sales rep: it reads your product, finds buyers who need it now, and books meetings through personalised LinkedIn outreach. I built the engine.",
         tags=["React", "TypeScript", "LLMs", "Automation", "Analytics"], motif="pipeline",
         steps=["read product", "find buyers", "research", "write", "book"]),
    dict(slug="aertonic", n="03", name="Aertonic", meta="founding engineer · dubai · since nov 2025",
         blurb="Books qualified sales meetings for B2B software companies in the US and UAE, and only charges for the ones that happen. Built from zero.",
         tags=["TypeScript", "AI", "Product engineering"], motif="calendar"),
    dict(slug="endifaa", n="04", name="Endifaa", meta="full-stack developer · saudi arabia · oct 2025 – jun 2026",
         blurb="A sports-academy platform in English and Arabic: user, academy and admin portals, subscriptions and checkout, full right-to-left Arabic.",
         tags=["React", "RTK Query", "Django/DRF", "PostgreSQL", "Docker"], motif="rtl"),
    dict(slug="zaofi", n="05", name="Zao Fi", meta="my own product · stock ai",
         blurb="Watches what whales, insiders and Congress are buying, and turns it into one 0–100 conviction score with the reasons in plain English.",
         tags=["AI", "Market data", "Explainable scores"], motif="gauge"),
]


def motif(t, p, x, y, w, h):
    s, c = t["sig"], t["line"]
    if p["motif"] == "pulse":  # heartbeat trace scrolling past
        pts, px = [], 0
        while px < w * 2:
            seg = [(0, 0), (30, 0), (38, -18), (46, 26), (54, -44), (62, 10), (70, 0), (110, 0)]
            pts += [(px + a, b) for a, b in seg]
            px += 110
        d = "M" + "L".join(f"{x + a:.0f} {y + h / 2 + b:.0f}" for a, b in pts)
        return (f'<clipPath id="mc"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath>'
                f'<g clip-path="url(#mc)"><g class="ekg" style="--w:-{110 * math.ceil(w / 110)}px">'
                f'<path d="{d}" fill="none" stroke="{s}" stroke-width="2" stroke-linejoin="round"/></g></g>'
                f'<path d="M{x} {y + h / 2}H{x + w}" stroke="{c}" stroke-dasharray="2 4"/>')
    if p["motif"] == "pipeline":  # a lead travels through the stages
        n = len(p["steps"])
        gap = w / (n - 1)
        out = [f'<path d="M{x} {y + h / 2}H{x + w}" stroke="{c}"/>']
        for i, st in enumerate(p["steps"]):
            sx = x + i * gap
            out.append(f'<circle cx="{sx:.0f}" cy="{y + h / 2:.0f}" r="6" fill="{t["bg2"]}" stroke="{s}"/>')
            out.append(f'<circle class="lit" cx="{sx:.0f}" cy="{y + h / 2:.0f}" r="3" fill="{s}" style="animation-delay:{i * .6:.1f}s"/>')
            out.append(label(st, sx, y + h / 2 + 26, t["dim"], 7.5, "middle"))
        out.append(f'<circle class="lead" cx="{x}" cy="{y + h / 2}" r="4" fill="{s}" style="--w:{w:.0f}px"/>')
        return "".join(out)
    if p["motif"] == "calendar":  # meeting slots filling in a week grid
        out, cw, rh = [], w / 5, (h - 18) / 4
        for i, d in enumerate("MTWTF"):
            out.append(label(d, x + i * cw + cw / 2, y + 8, t["dim"], 8, "middle"))
        k = 0
        for r in range(4):
            for i in range(5):
                bx, by = x + i * cw + 4, y + 18 + r * rh + 2
                out.append(f'<rect x="{bx:.0f}" y="{by:.0f}" width="{cw - 8:.0f}" height="{rh - 6:.0f}" rx="3" fill="none" stroke="{c}"/>')
                if (r * 7 + i * 3) % 4 == 0:
                    out.append(f'<rect class="book" x="{bx:.0f}" y="{by:.0f}" width="{cw - 8:.0f}" height="{rh - 6:.0f}" rx="3" fill="{s}" style="animation-delay:{k * .45:.2f}s"/>')
                    k += 1
        return "".join(out)
    if p["motif"] == "rtl":  # one layout mirrored between LTR and RTL
        out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="none" stroke="{c}"/>']
        bars = [(0.55, 10), (0.8, 30), (0.4, 50), (0.68, 70)]
        g = "".join(f'<rect x="{x + 12}" y="{y + 12 + b}" width="{(w - 24) * f:.0f}" height="9" rx="4" fill="{s if i == 0 else t["dim"]}" fill-opacity="{1 if i == 0 else .5}"/>'
                    for i, (f, b) in enumerate(bars))
        out.append(f'<g class="flip" style="transform-origin:{x + w / 2:.0f}px 0">{g}</g>')
        out.append(label("en", x, y + h + 16, t["dim"], 8))
        out.append(label("ar · rtl", x + w, y + h + 16, t["dim"], 8, "end"))
        return "".join(out)
    if p["motif"] == "gauge":  # conviction score needle
        r = min(w / 2, h) - 6
        gx, gy = x + w / 2, y + h - 4
        out = [f'<path d="M{gx - r:.0f} {gy:.0f}A{r:.0f} {r:.0f} 0 0 1 {gx + r:.0f} {gy:.0f}" fill="none" stroke="{c}" stroke-width="10"/>',
               f'<path d="M{gx - r:.0f} {gy:.0f}A{r:.0f} {r:.0f} 0 0 1 {gx + r:.0f} {gy:.0f}" fill="none" stroke="{s}" stroke-width="10" pathLength="100" stroke-dasharray="78 100" class="arc"/>',
               f'<g class="needle" style="transform-origin:{gx:.0f}px {gy:.0f}px"><path d="M{gx:.0f} {gy:.0f}L{gx:.0f} {gy - r + 14:.0f}" stroke="{t["fg"]}" stroke-width="2.5" stroke-linecap="round"/></g>',
               f'<circle cx="{gx:.0f}" cy="{gy:.0f}" r="5" fill="{t["fg"]}"/>',
               label("0", gx - r, gy + 18, t["dim"], 8, "middle"), label("100", gx + r, gy + 18, t["dim"], 8, "middle")]
        return "".join(out)
    return ""


MOTIF_CSS = """
@keyframes ekg{to{transform:translateX(var(--w))}}.ekg{animation:ekg 4s linear infinite}
@keyframes lit{0%,8%{opacity:1}30%,100%{opacity:.15}}.lit{animation:lit 3s linear infinite}
@keyframes lead{0%{transform:none;opacity:0}5%{opacity:1}95%{opacity:1}100%{transform:translateX(var(--w));opacity:0}}.lead{animation:lead 3s linear infinite}
@keyframes book{0%,10%{opacity:0}20%,85%{opacity:.9}100%{opacity:0}}.book{animation:book 9s ease-in-out infinite both}
@keyframes flip{0%,40%{transform:none}50%,90%{transform:scaleX(-1)}100%{transform:none}}.flip{animation:flip 6s cubic-bezier(.6,0,.2,1) infinite}
@keyframes needle{0%{transform:rotate(-90deg)}60%{transform:rotate(58deg)}75%{transform:rotate(44deg)}100%{transform:rotate(50deg)}}.needle{transform:rotate(50deg);animation:needle 2.6s cubic-bezier(.2,.8,.2,1) both}
@keyframes arc{from{stroke-dasharray:0 100}}.arc{animation:arc 2.6s cubic-bezier(.2,.8,.2,1) both}
"""


def project(t, p, mobile):
    W = 480 if mobile else 1040
    pad = 36
    body = []
    acc = t["sig"] if t["bg"] == "#05060a" else t["cob"]
    # big index number as a watermark
    body.append(T(DISPLAY, p["n"], W - pad, 132 if not mobile else 52, 120 if not mobile else 36, t["faint"], anchor="end"))
    body.append(label(f"{p['n']} / project", pad, 46, acc, 10))
    body.append(label(p["meta"], pad, 66, t["dim"], 9 if not mobile else 8))
    body.append(T(DISPLAY, p["name"], pad, 118, 40, t["fg"]))
    nw = DISPLAY.width(p["name"], 40)
    body.append(T(BODY, "↗", pad + nw + 14, 112, 26, acc))
    tw = 560 if not mobile else W - 2 * pad
    para_svg, ph = para(BODY, p["blurb"], pad, 152, 15.5, t["dim"], tw)
    body.append(para_svg)
    y = 152 + ph + 6
    if p.get("metrics"):
        cols = 4 if not mobile else 2
        mw = (tw if not mobile else W - 2 * pad) / cols
        for i, (v, k) in enumerate(p["metrics"]):
            mx, my = pad + (i % cols) * mw, y + 30 + (i // cols) * 58
            body.append(f'<g class="rise" style="animation-delay:{.2 + i * .12:.2f}s">'
                        + T(DISPLAY, v, mx, my, 22, t["fg"]) + label(k, mx, my + 20, t["dim"], 7.5) + "</g>")
        y = my + 36
    # tags
    tx = pad
    ty = y + 16
    for tag in p["tags"]:
        w = MONO.width(tag.upper(), 8.5, .7) + 22
        if tx + w > (pad + tw):
            tx, ty = pad, ty + 32
        body.append(f'<rect x="{tx:.0f}" y="{ty}" width="{w:.0f}" height="24" rx="12" fill="none" stroke="{t["line"]}"/>'
                    + label(tag, tx + 11, ty + 15.5, t["fg"], 8.5))
        tx += w + 8
    bottom = ty + 24
    # motif panel
    if mobile:
        mx, my, mw, mh = pad + 10, bottom + 34, W - 2 * pad - 20, 90
        body.append(motif(t, p, mx, my, mw, mh))
        bottom = my + mh + (30 if p["motif"] in ("pipeline", "rtl", "gauge") else 4)
    else:
        mx, my, mw, mh = 680, 140, 300, 110
        body.append(motif(t, p, mx, my, mw, mh))
        bottom = max(bottom, my + mh + 30)
    H = int(bottom + 34)
    body.append(f'<rect x="0" y="{H - 4}" width="{W}" height="4" fill="{acc}" class="grow" style="animation-duration:2.4s"/>')
    alt = f"{p['name']}. {p['blurb']}"
    return svg(W, H, t, alt, "".join(body), MOTIF_CSS)


# ---------------------------------------------------------------- timeline

ROLES = [  # name, role, start (y, m), end or None
    ("Quest Marketing", "lead ai & software eng", (2024, 3), (2024, 12)),
    ("Freelance", "ai/ml eng & web dev", (2024, 7), None),
    ("Stackloom", "ai & prompt engineer", (2025, 1), (2025, 9)),
    ("Endifaa", "full-stack developer", (2025, 10), (2026, 6)),
    ("Aertonic", "founding engineer", (2025, 11), None),
    ("Global Health", "lead software engineer", (2025, 12), None),
    ("Jordy", "co-founder", (2026, 3), None),
]


def timeline(t, mobile, today):
    W = 480 if mobile else 1040
    pad = 40
    gutter = 0 if mobile else 230
    x0, x1 = pad + gutter, W - pad
    start, end = (2024, 1), (today.year + (today.month >= 10), (today.month + 2) % 12 + 1)
    span = (end[0] - start[0]) * 12 + end[1] - start[1]
    X = lambda ym: x0 + ((ym[0] - start[0]) * 12 + ym[1] - start[1]) / span * (x1 - x0)
    acc = t["sig"] if t["bg"] == "#05060a" else t["cob"]
    body = [section_head(t, "03", "experience", pad, 52),
            T(DISPLAY, "Experience.", pad, 96, 30, t["fg"])]
    top = 140
    rowh = 52 if mobile else 44
    # year grid
    for yr in range(start[0], end[0] + 1):
        gx = X((yr, 1))
        if gx <= x1:
            body.append(f'<path d="M{gx:.1f} {top - 8}V{top + rowh * len(ROLES)}" stroke="{t["line"]}" stroke-dasharray="2 4"/>')
            body.append(label(str(yr), gx + 4, top - 12, t["dim"], 9))
    now = (today.year, today.month)
    for i, (name, role, s, e) in enumerate(ROLES):
        y = top + i * rowh + (22 if mobile else 10)
        live = e is None
        bx, bw = X(s), X(e or now) - X(s)
        if mobile:
            body.append(T(BODY, name, x0, y - 8, 13, t["fg"]) + label(role, x0 + BODY.width(name, 13) + 10, y - 8, t["dim"], 7.5))
        else:
            body.append(T(BODY, name, pad, y + 13, 14, t["fg"]) + label(role, pad, y + 27, t["dim"], 7.5))
        body.append(f'<rect class="grow" x="{bx:.1f}" y="{y}" width="{max(bw, 6):.1f}" height="16" rx="3" '
                    f'fill="{acc if live else t["dim"]}" fill-opacity="{1 if live else .45}" style="animation-delay:{.15 * i:.2f}s"/>')
        if live:
            body.append(f'<rect class="pulse" x="{bx + bw - 3:.1f}" y="{y}" width="3" height="16" fill="{t["fg"]}"/>')
    nx = X(now)
    body.append(f'<path d="M{nx:.1f} {top - 4}V{top + rowh * len(ROLES) + 4}" stroke="{t["alarm"]}" stroke-width="1.5"/>'
                f'<circle class="pulse" cx="{nx:.1f}" cy="{top - 4}" r="4" fill="{t["alarm"]}"/>'
                + label("now", nx - 6, top + rowh * len(ROLES) + 20, t["alarm"], 9, "end"))
    H = int(top + rowh * len(ROLES) + 44)
    alt = "Experience timeline: " + "; ".join(f"{r[0]}, {r[1]}" for r in reversed(ROLES)) + "."
    return svg(W, H, t, alt, "".join(body))


# ---------------------------------------------------------------- contact

def contact(t, mobile):
    W = 480 if mobile else 1040
    pad = 40
    acc = t["sig"] if t["bg"] == "#05060a" else t["cob"]
    body = [dot_grid(t, W, 400), section_head(t, "05", "contact", pad, 52)]
    size = 92 if not mobile else 56
    body.append(T(DISPLAY, "Let's talk.", pad, 60 + size * 1.05, size, t["fg"], cls="rise"))
    y = 60 + size * 1.05 + 46
    p, ph = para(BODY, "Have a project in mind, or something half-built that needs finishing? "
                       "Send a message and I'll get back to you within a day.", pad, y, 17, t["dim"], 520 if not mobile else W - 2 * pad)
    body.append(p)
    y += ph + 18
    mail = "sm.hassaan99@gmail.com"
    mw = MONO.width(mail, 15) + 70
    body.append(f'<rect x="{pad}" y="{y}" width="{mw:.0f}" height="46" rx="23" fill="{t["sig"]}"/>'
                + T(MONO, mail, pad + 24, y + 28, 15, t["sig_ink"])
                + T(BODY, "→", pad + mw - 34, y + 30, 20, t["sig_ink"]))
    if not mobile:
        rx = 700
        rows = [("reply time", "about a day"), ("based in", "karachi, pk"), ("time zone", "utc+5"), ("status", "open to projects")]
        for i, (k, v) in enumerate(rows):
            ry = 150 + i * 42
            body.append(f'<path d="M{rx} {ry + 14}H{W - pad}" stroke="{t["line"]}"/>'
                        + label(k, rx, ry, t["dim"], 9) + label(v, W - pad, ry, t["fg"], 9, "end"))
        body.append(f'<circle class="pulse" cx="{W - pad - MONO.width("OPEN TO PROJECTS", 9, .72) - 14:.0f}" cy="{150 + 3 * 42 - 3}" r="4" fill="{acc}"/>')
    H = int(y + 46 + 44)
    return svg(W, H, t, "Let's talk. Email sm.hassaan99@gmail.com, replies within about a day.", "".join(body))


# ---------------------------------------------------------------- main

STACK = [  # label, [(name, simple-icons slug or None)]
    ("languages", [("Python", "python"), ("TypeScript", "typescript"), ("C++", "cplusplus"), ("Dart", "dart")]),
    ("ai / data", [("TensorFlow", "tensorflow"), ("PyTorch", "pytorch"), ("OpenCV", "opencv"),
                   ("LLMs / NLP", None), ("Hugging Face", "huggingface")]),
    ("frameworks", [("React", "react"), ("Django / DRF", "django"), ("FastAPI", "fastapi"), ("Flutter", "flutter")]),
    ("backend & infra", [("PostgreSQL", "postgresql"), ("MySQL", "mysql"), ("Docker", "docker"),
                         ("AWS", "amazonwebservices"), ("RabbitMQ", "rabbitmq")]),
]
SPARKLE = "M12 1.5l2.6 7.9 7.9 2.6-7.9 2.6-2.6 7.9-2.6-7.9-7.9-2.6 7.9-2.6z"  # no brand mark for LLMs


def icon_path(slug):
    """24x24 path data from Simple Icons (CC0), vendored in scripts/icons/."""
    if slug is None:
        return SPARKLE
    return re.search(r' d="([^"]+)"', (ROOT / "scripts" / "icons" / f"{slug}.svg").read_text()).group(1)


def stack(t, mobile):
    W = 480 if mobile else 1040
    pad = 40
    acc = t["sig"] if t["bg"] == "#05060a" else t["cob"]
    body = [section_head(t, "04", "stack", pad, 52), T(DISPLAY, "Tools I ship with.", pad, 96, 30, t["fg"])]
    gutter = 0 if mobile else 170
    tw, th, gap = (128, 44, 8) if mobile else (148, 48, 10)
    per_row = max(1, int((W - 2 * pad - gutter + gap) // (tw + gap)))
    y = 140
    k = 0
    total = sum(len(items) for _, items in STACK)
    for name, items in STACK:
        if mobile:
            body.append(label(name, pad, y + 4, t["dim"], 9))
            y += 16
        else:
            body.append(label(name, pad, y + th / 2 + 4, t["dim"], 9))
        for i, (tool, slug) in enumerate(items):
            x = pad + gutter + (i % per_row) * (tw + gap)
            ty = y + (i // per_row) * (th + gap)
            s = 20 / 24
            ix, iy = x + 14, ty + (th - 20) / 2
            # tiles light up one after another, left to right, top to bottom
            delay = k / total * 6
            body.append(f'<g class="tile" style="animation-delay:{k * .05:.2f}s">'
                        f'<rect x="{x}" y="{ty:.0f}" width="{tw}" height="{th}" rx="10" fill="{t["bg2"]}" stroke="{t["line"]}"/>'
                        f'<path class="glow" transform="translate({ix:.1f} {iy:.1f}) scale({s:.4f})" d="{icon_path(slug)}" fill="{t["fg"]}" style="animation-delay:{delay:.2f}s"/>'
                        + T(BODY, tool, x + 44, ty + th / 2 + 4.5, 13, t["fg"]) + "</g>")
            k += 1
        rows = math.ceil(len(items) / per_row)
        y += rows * (th + gap) + (14 if mobile else 8)
    css = (f"@keyframes glow{{0%,4%{{fill:{acc}}}14%,100%{{fill:{t['fg']}}}}}.glow{{animation:glow 6s linear infinite}}"
           f"@keyframes tile{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}"
           f".tile{{animation:tile .6s cubic-bezier(.2,.8,.2,1) both}}")
    H = int(y + 26)
    alt = "Stack. " + ". ".join(f"{n}: " + ", ".join(tool for tool, _ in items) for n, items in STACK) + "."
    return svg(W, H, t, alt, "".join(body), css)


def main():
    load_fonts()
    OUT.mkdir(exist_ok=True)
    today = date.today()
    cards = {"hero": hero, "clients": world, "experience": lambda t, m: timeline(t, m, today), "contact": contact,
             "stack": stack}
    for p in PROJECTS:
        cards[p["slug"]] = lambda t, m, p=p: project(t, p, m)
    for slug, fn in cards.items():
        for theme, t in THEMES.items():
            for mobile in (False, True):
                name = f"{slug}-{'mobile-' if mobile else ''}{theme}.svg"
                (OUT / name).write_text(fn(t, mobile), encoding="utf-8")
                print(name)


if __name__ == "__main__":
    main()
