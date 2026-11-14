r"""One source for the Prelude mark. Every brand file is drawn from these numbers.

The mark is "Prelude." in Syne ExtraBold, off-white, with two parts in amber:
the "u" is redrawn as seven rounded bars, and the full stop is amber too. The
bars are the icon: on its own, the row of seven is what a home screen shows.

| Piece | Colour |
| ----- | ------ |
| the letters P, r, e, l, d, e | `#FFFFFF` |
| the seven bars and the full stop | `#FFB703` |
| the background of the icon and the launch screen | `#101319` |

What it writes, all under `app/web/assets/brand/`:

| File | What uses it |
| ---- | ------------ |
| `prelude_mark.svg` | the wordmark, no background; inlined into the launch screen |
| `prelude_icon.svg` | the bars on a rounded square; copied to `favicon.svg` |
| `prelude_icon_square.svg` | the bars on a plain square; the source of the PNGs |
| `prelude_launch.svg` | the launch screen's layout, 390 by 844 |

`scripts/make_icons.py` reads the two icon files and writes the icon set the
screens link. Nothing else reads these.

**The two fonts are committed beside this script**, under
`scripts/brand/fonts/`, because the mark is their outlines and a redraw from a
different copy of a font is a different mark:

| File | Family | Axis used | Licence |
| ---- | ------ | --------- | ------- |
| `scripts/brand/fonts/Syne-wght.ttf` | Syne, variable | `wght` 800 | SIL Open Font License 1.1, `scripts/brand/fonts/OFL-Syne.txt` |
| `scripts/brand/fonts/HankenGrotesk-wght.ttf` | Hanken Grotesk, variable | `wght` 500 | SIL Open Font License 1.1, `scripts/brand/fonts/OFL-HankenGrotesk.txt` |

Both are the variable fonts, not static instances: this instantiates the one
weight it wants. `scripts/brand/README.md` records where each came from and
its checksum.

The glyphs are written as outlines rather than as `<text>`, because a favicon
and a home-screen icon are rendered where no font is loaded.

Run it:

    .\.venv-prelude\Scripts\python.exe -I scripts\brand\build_svg.py --plan
    .\.venv-prelude\Scripts\python.exe -I scripts\brand\build_svg.py --check
    .\.venv-prelude\Scripts\python.exe -I scripts\brand\build_svg.py --confirm

`--check` draws everything and compares it with what is committed, writing
nothing; it is how `tests/test_the_mark.py` asks whether the committed files
are still what these numbers draw. Needs `fonttools`, in the dev group.

A billboard panel was drawn from the same numbers for the pitch deck. It is
not in this repo and this does not write it: nothing in the app serves it.
"""

import argparse
import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent.parent
FONTS = ROOT / "scripts" / "brand" / "fonts"
OUT = ROOT / "app" / "web" / "assets" / "brand"

WHITE, AMBER, BG = "#FFFFFF", "#FFB703", "#101319"
BARS = (0.55, 1.0, 0.70, 0.92, 0.58, 0.32, 0.14)   # bar heights as a share of the x-height, left to right
BAR_THIN = 1.7                                      # bar width = u width / (6 * 1.7), the d's weight
SYNE = instancer.instantiateVariableFont(
    TTFont(FONTS / "Syne-wght.ttf"), {"wght": 800})
HANK = instancer.instantiateVariableFont(
    TTFont(FONTS / "HankenGrotesk-wght.ttf"), {"wght": 500})


def glyph(font, ch):
    gs = font.getGlyphSet(); name = font.getBestCmap()[ord(ch)]; return gs[name], font["hmtx"][name][0]


def bounds(font, ch):
    g, _ = glyph(font, ch); bp = BoundsPen(font.getGlyphSet()); g.draw(bp); return bp.bounds


def path(font, ch, x, base, s):
    """Glyph outline in SVG space: scaled by s, origin on the baseline at x, y pointing down."""
    g, adv = glyph(font, ch); sp = SVGPathPen(font.getGlyphSet(), lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
    g.draw(TransformPen(sp, (s, 0, 0, -s, x, base))); return sp.getCommands(), adv * s


def rrect(x, y, w, h):
    r = w / 2; f = lambda v: f"{v:.2f}".rstrip("0").rstrip(".")
    return (f"M{f(x)} {f(y+r)}A{f(r)} {f(r)} 0 0 1 {f(x+w)} {f(y+r)}V{f(y+h-r)}"
            f"A{f(r)} {f(r)} 0 0 1 {f(x)} {f(y+h-r)}Z")


def mark(x0=0.0, base=0.0, s=1.0):
    """The wordmark at scale s (font units * s), baseline at y=base. Returns (white path, amber path, bbox)."""
    xh = bounds(SYNE, "x")[3] * s
    ub = bounds(SYNE, "u"); uw = (ub[2] - ub[0]) * s
    bw = uw / (6 * BAR_THIN); g = (uw - 6 * bw) / 5; need = 7 * bw + 6 * g - uw
    mid = base - xh / 2; white, amber = [], []; x = x0
    for ch in "Prelude":
        if ch == "u":
            bx0 = x + ub[0] * s
            for k, hk in enumerate(BARS):
                h = max(bw, xh * hk); amber.append(rrect(bx0 + k * (bw + g), mid - h / 2, bw, h))
            x += glyph(SYNE, "u")[1] * s + need
        else:
            d, adv = path(SYNE, ch, x, base, s); white.append(d); x += adv
    d, adv = path(SYNE, ".", x, base, s); amber.append(d)
    # tight box from the outlines
    top = base - bounds(SYNE, "l")[3] * s; bottom = base - min(bounds(SYNE, c)[1] for c in "Preld.") * s
    left = x0 + bounds(SYNE, "P")[0] * s; right = x + bounds(SYNE, ".")[2] * s
    return "".join(white), "".join(amber), (left, top, right, bottom)


def line(font, string, size, x, base):
    upm = font["head"].unitsPerEm; s = size / upm; out = []; cx = x
    for ch in string:
        if ch == " ": cx += glyph(font, ch)[1] * s; continue
        d, adv = path(font, ch, cx, base, s); out.append(d); cx += adv
    return "".join(out), cx - x


def svg(w, h, body, bg=None, title="Prelude"):
    b = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.2f} {h:.2f}" width="{w:.0f}" height="{h:.0f}" role="img" aria-label="{title}">'
            f'<title>{title}</title>{b}{body}</svg>\n')


UPM = SYNE["head"].unitsPerEm
# The mark, master: drawn at 1 unit per font unit, then framed to its own outline
w0, a0, (l, t, r, b) = mark(0, 0, 1.0)
MW, MH = r - l, b - t


def place_mark(width, x, y):
    """The mark scaled to `width`, its top-left at (x, y)."""
    s = width / MW; return (f'<g transform="translate({x - l*s:.2f} {y - t*s:.2f}) scale({s:.6f})">'
                            f'<path fill="{WHITE}" d="{w0}"/><path fill="{AMBER}" d="{a0}"/></g>'), MH * s


TAG = "Leave your seat. Stay in the game."
HUPM = HANK["head"].unitsPerEm
HASC = HANK["hhea"].ascent

#: The icon's square, in SVG user units, and how much of it the bars fill.
ICON = 1024
ICON_FILL = 0.56
#: The corner radius of the rounded icon, as a share of the square. It is
#: iOS's own superellipse radius, close enough that the two read alike.
ICON_RADIUS = 0.2237


def drawn():
    """Every brand file, as {filename: text}. Nothing here touches the disk."""
    files = {}

    # 1. The wordmark, with no background: what the launch screen inlines.
    body, _ = place_mark(MW, 0, 0)
    files["prelude_mark.svg"] = svg(MW, MH, body, title="Prelude")

    # 2. The app icon: the seven bars from the mark, centred on the dark square.
    #    Twice: once with the corners rounded, for a browser tab, and once
    #    square, which is what the PNGs are drawn from because every platform
    #    that shows them rounds the corners itself.
    xh = bounds(SYNE, "x")[3]; ub = bounds(SYNE, "u"); uw = ub[2] - ub[0]
    bw = uw / (6 * BAR_THIN); g = (uw - 6 * bw) / 5
    gw = 7 * bw + 6 * g
    k = ICON * ICON_FILL / gw; ox = (ICON - gw * k) / 2; oy = ICON / 2
    bars = "".join(rrect(ox + i * (bw + g) * k, oy - max(bw, xh * hk) * k / 2,
                         bw * k, max(bw, xh * hk) * k)
                   for i, hk in enumerate(BARS))
    for name, back in (
        ("prelude_icon.svg",
         f'<rect width="{ICON}" height="{ICON}" rx="{ICON*ICON_RADIUS:.1f}" fill="{BG}"/>'),
        ("prelude_icon_square.svg",
         f'<rect width="{ICON}" height="{ICON}" fill="{BG}"/>'),
    ):
        files[name] = svg(ICON, ICON, back + f'<path fill="{AMBER}" d="{bars}"/>',
                          title="Prelude icon")

    # 3. The launch screen, 390 by 844: the mark 300 wide above centre, the
    #    tagline under it. app/web/index.html draws this layout in CSS with
    #    the mark inlined and the tagline as real text; this file is what it
    #    was measured against.
    W, H = 390, 844; mw = 300; mx = (W - mw) / 2
    fs = 16; gap = 20
    block = MH * mw / MW + gap + fs; my = (H - block) / 2 - 24
    body, mh = place_mark(mw, mx, my)
    tag, tw = line(HANK, TAG, fs, 0, 0)
    tag, tw = line(HANK, TAG, fs, (W - tw) / 2, my + mh + gap + HASC * fs / HUPM)
    files["prelude_launch.svg"] = svg(
        W, H, body + f'<path fill="{AMBER}" d="{tag}"/>', bg=BG,
        title="Prelude. Leave your seat. Stay in the game.")
    return files


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--plan", action="store_true",
                        help="print what would be written and write nothing")
    parser.add_argument("--check", action="store_true",
                        help="compare what this draws with what is committed")
    parser.add_argument("--confirm", action="store_true",
                        help="draw the brand files and write them")
    args = parser.parse_args(argv)

    files = drawn()
    print("mark     {:.0f} x {:.0f} font units, Syne wght 800".format(MW, MH))
    print("tagline  {!r}, Hanken Grotesk wght 500".format(TAG))
    print("out      {}".format(OUT.relative_to(ROOT).as_posix()))
    print()

    if args.check:
        bad = 0
        for name, text in files.items():
            there = OUT / name
            if not there.is_file():
                print("  MISSING  {}".format(name)); bad += 1
            elif there.read_text(encoding="utf-8") != text:
                print("  DIFFERS  {}".format(name)); bad += 1
            else:
                print("  same     {:<26} {:>6,} bytes".format(name, len(text)))
        print()
        if bad:
            print("{} file(s) are not what these numbers draw; "
                  "--confirm rewrites them".format(bad))
            return 1
        print("every committed brand file is what these numbers draw")
        return 0

    if args.plan or not args.confirm:
        for name, text in files.items():
            print("  would write {:<26} {:>6,} bytes".format(name, len(text)))
        print()
        print("nothing was written. --confirm is what writes it.")
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (OUT / name).write_text(text, encoding="utf-8", newline="\n")
        print("  {:>6,} bytes  {}".format(len(text), name))
    print()
    print("wrote {}".format(OUT.relative_to(ROOT).as_posix()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
