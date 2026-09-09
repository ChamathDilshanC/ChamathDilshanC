#!/usr/bin/env python3
"""Generate dark.svg / light.svg profile banners from a photo.

Usage:  python banner_maker.py [path/to/photo.jpg]
If no photo is given, avatar.png next to this script is used.
"""
import random
import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parent

# ---------------------------------------------------------------- profile data
NAME = "Chamath Dilshan"
HOST = "chamath@devos"

INFO = [
    ("Subject", NAME),
    ("Role", "Full-Stack Software Engineer"),
    ("Origin", "Colombo, Sri Lanka"),
    ("Focus", "Enterprise Web Apps · Cloud Native"),
    ("Status", "Building · Learning · Clean Code"),
    ("ToolChain", "VS Code, Git, Docker, Postman"),
]
STACK = [
    ("Core.Lang", "TypeScript, JavaScript, Python, Java, C++"),
    ("Core.Frontend", "React, Next.js, Vue, Tailwind"),
    ("Core.Backend", "Node.js, Express, Spring Boot, FastAPI"),
    ("Core.Database", "PostgreSQL, MongoDB, Redis, MySQL"),
    ("Core.Infra", "Docker, Kubernetes, AWS, Azure"),
]
CONTACT = [
    ("Grid.Mail", "dilshanColonne123@gmail.com"),
    ("Grid.Portfolio", "chamathdilshanc.com"),
    ("Grid.LinkedIn", "chamath-dilshan-6aa8022ab"),
    ("Grid.Github", "ChamathDilshanC"),
]

# ------------------------------------------------------------------- geometry
W, H = 1400, 800
PANEL_Y, PANEL_H = 174, 564
ART_COLS, ART_ROWS = 95, 58
ART_FS = 9.19
ART_LH = 9.7
LEADER_COL = 29          # column where every value starts

# Crop box (left, top, right, bottom) applied to the source photo before the
# ascii pass — keeps the subject filling the panel. Set to None for the whole
# image; tune it if you swap in a different photo.
CROP = (198, 132, 422, 368)
FLOOR = 0.18             # ink below this is dropped, so the backdrop stays open

# --------------------------------------------------------------------- themes
DARK = dict(
    bg0="#05070C", bg1="#0A0E1A",
    accent=("#7C3AED", "#22D3EE", "#10B981"),
    map=("#3B82F6", "#22D3EE"),
    hairline="rgba(255,255,255,.10)",
    window="#0B1220", window_op="0.55",
    title="#F1F5F9", muted="#7C8CA6", dots="#3A4558",
    cyan="#22D3EE", label="#3B82F6", host="#C084FC", section="#34D399",
    particle="#22D3EE", grain=True,
)
LIGHT = dict(
    bg0="#FFFFFF", bg1="#F1F5F9",
    accent=("#2563EB", "#06B6D4", "#10B981"),
    map=("#1D4ED8", "#0369A1"),
    hairline="rgba(15,23,42,.10)",
    window="#F8FAFC", window_op="0.6",
    title="#0F172A", muted="#64748B", dots="#CBD5E1",
    cyan="#06B6D4", label="#2563EB", host="#7C3AED", section="#059669",
    particle="#06B6D4", grain=False,
)

# ------------------------------------------------------------------ ascii art
RAMP = " .:-=+*#%@"
NOISE = "01{}</>[]"


def ascii_art(photo):
    """Render the photo as ART_COLS x ART_ROWS characters.

    Dark pixels get the dense glyphs, so the subject is drawn in ink and the
    backdrop stays open — that reads the same way on either theme.
    """
    im = Image.open(photo).convert("L")
    if CROP:
        im = im.crop(CROP)
    im = ImageOps.autocontrast(im, cutoff=1)
    im = ImageEnhance.Contrast(im).enhance(1.55)
    im = im.resize((ART_COLS, ART_ROWS), Image.LANCZOS)

    px = list(im.getdata())
    lo, hi = min(px), max(px)
    span = max(hi - lo, 1)

    rnd = random.Random(20240909)
    rows = []
    for r in range(ART_ROWS):
        line = []
        for c in range(ART_COLS):
            ink = 1.0 - (px[r * ART_COLS + c] - lo) / span
            ink = max(ink - FLOOR, 0.0) / (1.0 - FLOOR)
            ch = RAMP[int(ink * (len(RAMP) - 1) + 0.5)]
            if ch == " " and rnd.random() < 0.012:       # matrix speckle
                ch = rnd.choice(NOISE)
            line.append(ch)
        rows.append("".join(line).rstrip())
    return rows


# ---------------------------------------------------------------- svg helpers
def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def leader(label):
    n = max(LEADER_COL - len(label) - 3, 3)
    return " " + "." * n + " "


def info_row(t, label, value, y, begin):
    return (
        '        <g transform="translate(0,%s)" opacity="0">\n'
        '          <animate attributeName="opacity" begin="%.2fs" dur="0.4s" from="0" to="1" fill="freeze"/>\n'
        '          <text font-family="\'JetBrains Mono\',monospace" font-size="14.5" xml:space="preserve">'
        '<tspan fill="%s" font-weight="700">%s</tspan>'
        '<tspan fill="%s">:</tspan>'
        '<tspan fill="%s">%s</tspan>'
        '<tspan fill="%s">%s</tspan></text>\n'
        '        </g>\n'
        % (y, begin, t["label"], esc(label), t["muted"], t["dots"],
           leader(label), t["title"], esc(value))
    )


def section(t, label, y, begin, line_x):
    return (
        '      <g transform="translate(0,%s)" opacity="0">\n'
        '        <animate attributeName="opacity" begin="%.2fs" dur="0.4s" from="0" to="1" fill="freeze"/>\n'
        '        <text font-family="\'JetBrains Mono\',monospace" font-size="15.5" font-weight="700" fill="%s">%s</text>\n'
        '        <line x1="%s" y1="-6" x2="662" y2="-6" stroke="%s" stroke-width="1" stroke-dasharray="2,3"/>\n'
        '      </g>\n'
        % (y, begin, t["section"], esc(label), line_x, t["hairline"])
    )


def particles(t, seed):
    rnd = random.Random(seed)
    out = []
    for _ in range(12):
        cx = round(rnd.uniform(40, 1380), 1)
        cy = round(rnd.uniform(40, 760), 1)
        r = round(rnd.uniform(1.3, 2.3), 1)
        op = round(rnd.uniform(0.13, 0.32), 2)
        dur = round(rnd.uniform(6.0, 11.0), 1)
        rise = round(cy - rnd.uniform(15, 40), 1)
        out.append(
            '      <circle cx="%s" cy="%s" r="%s" fill="%s" opacity="%s">\n'
            '        <animate attributeName="cy" values="%s;%s;%s" dur="%ss" repeatCount="indefinite"/>\n'
            '        <animate attributeName="opacity" values="0;%s;0" dur="%ss" repeatCount="indefinite"/>\n'
            '      </circle>'
            % (cx, cy, r, t["particle"], op, cy, rise, cy, dur, op, dur))
    return "\n".join(out)


def build(t, art):
    a0, a1, a2 = t["accent"]
    m0, m1 = t["map"]

    # ---- ascii art block
    art_lines = []
    for i, line in enumerate(art):
        y = round(7.4 + i * ART_LH, 1)
        begin = 0.50 + i * 0.045
        art_lines.append(
            '      <text x="0" y="%s" font-family="\'JetBrains Mono\',monospace" '
            'font-size="%s" letter-spacing="0.5" fill="url(#mapGrad)" opacity="0" '
            'xml:space="preserve">%s'
            '<animate attributeName="opacity" begin="%.2fs" dur="0.35s" from="0" to="1" fill="freeze"/>'
            '</text>' % (y, ART_FS, esc(line), begin))
    art_svg = "\n".join(art_lines)

    # ---- right hand info column
    body, y, begin = [], 32.5, 0.40
    for label, value in INFO:
        body.append(info_row(t, label, value, y, begin))
        y += 25.0
        begin += 0.13
    y += 10.0
    begin += 0.10
    for label, value in STACK:
        body.append(info_row(t, label, value, y, begin))
        y += 25.0
        begin += 0.13

    y += 7.5
    begin += 0.10
    body.append(section(t, "- Contact", y, begin, 118))
    y += 30.0
    begin += 0.15
    for label, value in CONTACT:
        body.append(info_row(t, label, value, y, begin))
        y += 25.0
        begin += 0.13

    y += 10.0
    begin += 0.10
    body.append(section(t, "- Live Stats", y, begin, 150))
    y += 30.0
    begin += 0.15
    body.append(
        '      <g transform="translate(0,%s)" opacity="0">\n'
        '        <animate attributeName="opacity" begin="%.2fs" dur="0.4s" from="0" to="1" fill="freeze"/>\n'
        '        <rect x="0" y="-13" width="5" height="18" fill="%s"/>\n'
        '        <text x="14" y="1" font-family="\'JetBrains Mono\',monospace" font-size="14.5" fill="%s">'
        'See live GitHub stats below in README &#8595;</text>\n'
        '      </g>\n' % (y, begin, t["cyan"], t["title"]))
    body = "".join(body)

    noise = ('  <rect x="0" y="0" width="1400" height="800" filter="url(#noise)"/>\n'
             if t["grain"] else "")

    return SVG_TEMPLATE.format(
        W=W, H=H, a0=a0, a1=a1, a2=a2, m0=m0, m1=m1,
        panel_y=PANEL_Y, panel_h=PANEL_H, panel_end=PANEL_Y + PANEL_H,
        bg0=t["bg0"], bg1=t["bg1"], hairline=t["hairline"],
        window=t["window"], window_op=t["window_op"], title=t["title"],
        muted=t["muted"], cyan=t["cyan"], host_fill=t["host"],
        host=HOST, host_rule=round(len(HOST) * 11.6, 1),
        noise=noise, particles=particles(t, 7), art=art_svg, body=body,
    )


SVG_TEMPLATE = '''<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{bg0}"/>
      <stop offset="100%" stop-color="{bg1}"/>
    </linearGradient>

    <linearGradient id="accentGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{a0}"/>
      <stop offset="50%" stop-color="{a1}"/>
      <stop offset="100%" stop-color="{a2}"/>
      <animate attributeName="x1" values="0%;100%;0%" dur="8s" repeatCount="indefinite"/>
      <animate attributeName="x2" values="100%;200%;100%" dur="8s" repeatCount="indefinite"/>
    </linearGradient>

    <linearGradient id="mapGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{m0}"/>
      <stop offset="100%" stop-color="{m1}"/>
      <animate attributeName="x1" values="0%;100%;0%" dur="7s" repeatCount="indefinite"/>
    </linearGradient>

    <linearGradient id="borderShimmer" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{hairline}" stop-opacity="0"/>
      <stop offset="45%" stop-color="{a0}" stop-opacity="0.9"/>
      <stop offset="55%" stop-color="{a1}" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="{hairline}" stop-opacity="0"/>
      <animate attributeName="x1" values="-100%;150%" dur="5s" repeatCount="indefinite"/>
      <animate attributeName="x2" values="0%;250%" dur="5s" repeatCount="indefinite"/>
    </linearGradient>

    <radialGradient id="glowA" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{a0}" stop-opacity="0.28"/>
      <stop offset="100%" stop-color="{a0}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="glowB" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="{a2}" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="{a2}" stop-opacity="0"/>
    </radialGradient>

    <clipPath id="mapClip">
      <rect x="62" y="{panel_y}" width="590" height="{panel_h}" rx="8"/>
    </clipPath>

    <filter id="noise">
      <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" stitchTiles="stitch" result="noise"/>
      <feColorMatrix in="noise" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.02 0"/>
    </filter>
  </defs>

  <rect x="0" y="0" width="1400" height="800" fill="url(#bgGrad)"/>
{noise}
  <circle cx="150" cy="120" r="240" fill="url(#glowA)">
    <animateTransform attributeName="transform" type="translate" values="0,0;30,20;0,0" dur="12s" repeatCount="indefinite"/>
  </circle>
  <circle cx="1250" cy="680" r="280" fill="url(#glowB)">
    <animateTransform attributeName="transform" type="translate" values="0,0;-25,-15;0,0" dur="14s" repeatCount="indefinite"/>
  </circle>

{particles}

  <!-- title line -->
  <text x="40" y="52" font-family="'JetBrains Mono',monospace" font-size="26" font-weight="700" fill="{title}">Chamath<tspan fill="{muted}" font-weight="400">/README</tspan><tspan fill="{cyan}">.md</tspan></text>

  <!-- main window -->
  <rect x="40" y="96" width="1320" height="668" rx="16" fill="{window}" fill-opacity="{window_op}" stroke="{hairline}" stroke-width="1"/>
  <rect x="40" y="96" width="1320" height="668" rx="16" fill="none" stroke="url(#borderShimmer)" stroke-width="1.3"/>

  <!-- title bar -->
  <line x1="40" y1="148" x2="1360" y2="148" stroke="{hairline}" stroke-width="1"/>
  <circle cx="70" cy="122.0" r="7" fill="#FF5F57"/>
  <circle cx="94" cy="122.0" r="7" fill="#FEBC2E"/>
  <circle cx="118" cy="122.0" r="7" fill="#28C840"/>
  <text x="700.0" y="127.0" text-anchor="middle" font-family="'JetBrains Mono',monospace" font-size="14.5" fill="{muted}">{host} ~ % ./profile.sh --live</text>
  <g>
    <circle cx="1242" cy="122.0" r="4" fill="#F87171">
      <animate attributeName="opacity" values="1;0.2;1" dur="1.2s" repeatCount="indefinite"/>
    </circle>
    <text x="1254" y="126.0" font-family="'JetBrains Mono',monospace" font-size="12" letter-spacing="1.5" fill="#F87171">SCANNING</text>
  </g>

  <!-- DEV.AVATAR panel -->
  <rect x="62" y="{panel_y}" width="590" height="{panel_h}" rx="8" fill="none" stroke="{hairline}" stroke-width="1"/>
  <text x="62" y="164" font-family="'JetBrains Mono',monospace" font-size="12.5" letter-spacing="2" fill="{muted}">DEV.AVATAR</text>
  <g clip-path="url(#mapClip)">
    <g transform="translate(76,182)">
      <animateTransform attributeName="transform" type="translate" values="76,182;76,176;76,182" dur="6s" repeatCount="indefinite"/>
{art}
    </g>
    <rect x="62" y="{panel_y}" width="590" height="2.5" fill="{m0}" opacity="0.15">
      <animate attributeName="y" values="{panel_y};{panel_end};{panel_y}" dur="5s" repeatCount="indefinite"/>
    </rect>
  </g>

  <!-- SYSTEM.INFO panel -->
  <rect x="676" y="{panel_y}" width="662" height="{panel_h}" rx="8" fill="none" stroke="{hairline}" stroke-width="1"/>
  <text x="676" y="164" font-family="'JetBrains Mono',monospace" font-size="12.5" letter-spacing="2" fill="{muted}">SYSTEM.INFO</text>
  <g transform="translate(698,208)">
      <g opacity="0">
        <animate attributeName="opacity" begin="0.15s" dur="0.4s" from="0" to="1" fill="freeze"/>
        <text x="0" y="0" font-family="'JetBrains Mono',monospace" font-size="19" font-weight="700" fill="{host_fill}">{host}</text>
        <line x1="{host_rule}" y1="-6" x2="662" y2="-6" stroke="{hairline}" stroke-width="1" stroke-dasharray="2,3"/>
      </g>
{body}  </g>
</svg>
'''


def main():
    photo = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "avatar.png"
    if not photo.exists():
        sys.exit("photo not found: %s" % photo)

    art = ascii_art(photo)
    for name, theme in (("dark.svg", DARK), ("light.svg", LIGHT)):
        (ROOT / name).write_text(build(theme, art), encoding="utf-8")
        print("wrote %s" % name)


if __name__ == "__main__":
    main()
