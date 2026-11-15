r"""One source for the Prelude mark. Every brand file is drawn from these numbers.

The mark is "Prelude." in Syne ExtraBold, off-white, with two parts in amber:
the "u" is redrawn as seven rounded bars, and the full stop is amber too. The
bars are the icon: on its own, the row of seven is what a home screen shows.

| Piece | Colour |
| ----- | ------ |
| the letters P, r, e, l, d, e | `#FFFFFF` |
| the seven bars and the full stop | `#FFB703` |
| the background of the icon and the launch screen | `#101319` |

What it writes, under `app/web/assets/brand/`:

| File | What uses it |
| ---- | ------------ |
| `prelude_mark.svg` | the wordmark, no background; inlined into the launch screen |
| `prelude_icon.svg` | the bars on a rounded square; copied to `favicon.svg` |
| `prelude_icon_square.svg` | the bars on a plain square; the source of the PNGs |
| `prelude_launch.svg` | the launch screen's layout, 390 by 844 |

and under `app/web/assets/launch/`, one PNG per iPhone screen:

| File | What uses it |
| ---- | ------------ |
| `launch-<w>x<h>.png` | `app/web/index.html`, as an `apple-touch-startup-image` behind the media query for that screen |

**The startup images are the launch screen, drawn.** iOS shows one while a web
app opened from the home screen is starting, before any of its markup has run,
and it is shown only where the file is exactly the device's own pixel size.
They are drawn here rather than read out of `prelude_launch.svg`, from the
layout both come from: a screen taller or wider than 390 by 844 is not that
file stretched, because the mark stays 300 CSS px wide on every screen and the
CSS does not scale it. `launch_layout` is that layout as numbers, and
`app/web/index.html` is the same rules in CSS.

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
are still what these numbers draw. A PNG is compared pixel by pixel rather
than byte by byte, for the reason `scripts/make_icons.py` records: Pillow
encodes the same image a few bytes differently on Windows and on the Linux
runner CI uses, so a byte comparison there is a claim about zlib. Needs
`fonttools` and `pillow`, both in the dev group.

A billboard panel was drawn from the same numbers for the pitch deck. It is
not in this repo and this does not write it: nothing in the app serves it.
"""

import argparse
import io
import math
import sys
from pathlib import Path

from fontTools.pens.basePen import BasePen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent.parent
FONTS = ROOT / "scripts" / "brand" / "fonts"
OUT = ROOT / "app" / "web" / "assets" / "brand"
LAUNCH_OUT = ROOT / "app" / "web" / "assets" / "launch"

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


def mark_pieces(x0=0.0, base=0.0, s=1.0):
    """The wordmark as geometry rather than as a path string.

    Returns `(letters, bars, stop, bbox)`: the six white glyphs as
    `(character, x)` on the baseline, the seven amber bars as `(x, y, w, h)`
    boxes, the amber full stop as one `(character, x)`, and the tight box
    around the lot. `mark` writes the SVG path from this and the bitmaps are
    drawn from the same list, so the two renderings cannot be of different
    marks.
    """
    xh = bounds(SYNE, "x")[3] * s
    ub = bounds(SYNE, "u"); uw = (ub[2] - ub[0]) * s
    bw = uw / (6 * BAR_THIN); g = (uw - 6 * bw) / 5; need = 7 * bw + 6 * g - uw
    mid = base - xh / 2; letters, bars = [], []; x = x0
    for ch in "Prelude":
        if ch == "u":
            bx0 = x + ub[0] * s
            for k, hk in enumerate(BARS):
                h = max(bw, xh * hk); bars.append((bx0 + k * (bw + g), mid - h / 2, bw, h))
            x += glyph(SYNE, "u")[1] * s + need
        else:
            letters.append((ch, x)); x += glyph(SYNE, ch)[1] * s
    stop = (".", x)
    # tight box from the outlines
    top = base - bounds(SYNE, "l")[3] * s; bottom = base - min(bounds(SYNE, c)[1] for c in "Preld.") * s
    left = x0 + bounds(SYNE, "P")[0] * s; right = x + bounds(SYNE, ".")[2] * s
    return letters, bars, stop, (left, top, right, bottom)


def mark(x0=0.0, base=0.0, s=1.0):
    """The wordmark at scale s (font units * s), baseline at y=base. Returns (white path, amber path, bbox)."""
    letters, bars, stop, box = mark_pieces(x0, base, s)
    white = [path(SYNE, ch, x, base, s)[0] for ch, x in letters]
    amber = [rrect(*one) for one in bars] + [path(SYNE, stop[0], stop[1], base, s)[0]]
    return "".join(white), "".join(amber), box


def line_pieces(font, string, size, x):
    """A line of text as `([(character, x)], width)`, spaces left out."""
    upm = font["head"].unitsPerEm; s = size / upm; out = []; cx = x
    for ch in string:
        if ch != " ": out.append((ch, cx))
        cx += glyph(font, ch)[1] * s
    return out, cx - x


def line(font, string, size, x, base):
    upm = font["head"].unitsPerEm; s = size / upm
    glyphs, width = line_pieces(font, string, size, x)
    return "".join(path(font, ch, cx, base, s)[0] for ch, cx in glyphs), width


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


TAG = "Leave your seat. Not the game."
HUPM = HANK["head"].unitsPerEm
HASC = HANK["hhea"].ascent

#: The launch screen, as `app/web/index.html` lays it out in CSS: the mark
#: 300 px wide, 20 px of air, then the tagline at 16 px in a 20 px line box,
#: and the pair lifted 24 px off the middle of the screen. The reference
#: screen is 390 by 844, which is the one `prelude_launch.svg` is drawn at,
#: but none of these is a share of it: the mark is 300 px wide on a 375 px
#: screen and on a 440 px one alike, because the CSS does not scale it.
LAUNCH_W, LAUNCH_H = 390, 844
LAUNCH_MARK_W = 300
LAUNCH_GAP = 20
LAUNCH_LIFT = 24
TAG_SIZE = 16
TAG_LINE = 20
HDESC = HANK["hhea"].descent


def launch_layout(width, height):
    """Where the mark and the tagline sit on a launch screen of this size.

    In CSS pixels from the top left, and the one place those rules are
    written as numbers: `app/web/index.html` is the same rules in CSS, and
    both `prelude_launch.svg` and the startup images are drawn from this.

    **The block is measured with the tagline's line box and not its type
    size**, because a flex column centres line boxes: the box is 20 px and the
    glyphs are 16 px. The baseline inside it is the box's top plus half the
    leading plus the ascent, and for Hanken Grotesk at 16 px the half-leading
    is negative, by 0.42 px, because the font's own ascent and descent come to
    20.85 px and overflow the 20 px box. Reading the glyph height instead put
    the mark 2 px below where the shell paints it, which is what the startup
    images found: an image that is not the screen it covers shows the fan the
    mark moving as the app takes over.
    """
    mw = LAUNCH_MARK_W
    mh = MH * mw / MW
    top = (height - (mh + LAUNCH_GAP + TAG_LINE)) / 2 - LAUNCH_LIFT
    line_top = top + mh + LAUNCH_GAP
    content = (HASC - HDESC) * TAG_SIZE / HUPM
    _, tw = line_pieces(HANK, TAG, TAG_SIZE, 0)
    return {
        "mark": ((width - mw) / 2, top, mw, mh),
        "line_top": line_top,
        "line_left": (width - tw) / 2,
        "baseline": line_top + (TAG_LINE - content) / 2 + HASC * TAG_SIZE / HUPM,
    }


#: The iPhone screens a startup image is drawn for, as (CSS width, CSS height,
#: device pixels per CSS pixel) in portrait. iOS takes one only where the file
#: is exactly that screen's own pixel size, so this is a list of screens
#: rather than of models and the models sharing a line are named beside it.
#: Read on 2026-11-15 off Apple's point sizes as
#: https://useyourloaf.com/blog/iphone-17-screen-sizes/ tabulates them, and it
#: covers every iPhone that runs a current iOS.
IPHONES = (
    (375, 667, 2),   # SE, 2nd and 3rd generation
    (375, 812, 3),   # 11 Pro, 12 mini, 13 mini
    (390, 844, 3),   # 12, 12 Pro, 13, 13 Pro, 14, 16e
    (393, 852, 3),   # 14 Pro, 15, 15 Pro, 16
    (402, 874, 3),   # 16 Pro, 17, 17 Pro
    (414, 896, 2),   # XR, 11
    (414, 896, 3),   # 11 Pro Max
    (420, 912, 3),   # Air
    (428, 926, 3),   # 12 Pro Max, 13 Pro Max, 14 Plus
    (430, 932, 3),   # 14 Pro Max, 15 Plus, 15 Pro Max, 16 Plus
    (440, 956, 3),   # 16 Pro Max, 17 Pro Max
)


def startup_name(css_w, css_h, scale):
    """The file one screen's startup image is written to, named for the pixels
    in it, because the pixels are what iOS matches the file against."""
    return "launch-%dx%d.png" % (round(css_w * scale), round(css_h * scale))


def startup_media(css_w, css_h, scale):
    """The media query that picks it. The pixel ratio is part of it because
    two screens share 414 by 896 at two ratios, and the wrong one of those is
    a quarter of the pixels."""
    return ("(device-width: %dpx) and (device-height: %dpx) and "
            "(-webkit-device-pixel-ratio: %d) and (orientation: portrait)"
            % (css_w, css_h, scale))


#: How many straight segments one curve becomes in a bitmap. The mark is at
#: most 900 device pixels wide here and a curve in it a few tens of those, so
#: sixteen is below what the reduction could show.
CURVE_STEPS = 16

#: The mark and the tagline are drawn this many times larger and reduced, so
#: an edge is the outline's own curve rather than a polygon fill's idea of it.
#: `scripts/make_icons.py` oversamples the icon by the same factor.
OVERSAMPLE = 4


class Outline(BasePen):
    """A glyph's contours as closed polygons, curves flattened.

    `BasePen` turns a TrueType quadratic into a cubic for us, so one curve
    method is the whole of it.
    """

    def __init__(self, glyph_set, steps=CURVE_STEPS):
        super().__init__(glyph_set)
        self.steps = steps
        self.contours = []
        self.here = []

    def _moveTo(self, pt):
        self._shut(); self.here = [pt]

    def _lineTo(self, pt):
        self.here.append(pt)

    def _curveToOne(self, one, two, pt):
        x0, y0 = self.here[-1]
        (x1, y1), (x2, y2), (x3, y3) = one, two, pt
        for i in range(1, self.steps + 1):
            t = i / self.steps; u = 1 - t
            self.here.append((
                u*u*u*x0 + 3*u*u*t*x1 + 3*u*t*t*x2 + t*t*t*x3,
                u*u*u*y0 + 3*u*u*t*y1 + 3*u*t*t*y2 + t*t*t*y3))

    def _closePath(self):
        self._shut()

    def _endPath(self):
        self._shut()

    def _shut(self):
        if len(self.here) > 2:
            self.contours.append(self.here)
        self.here = []


def outline(font, ch):
    """One glyph as a list of contours, in font units with y pointing up."""
    pen = Outline(font.getGlyphSet())
    glyph(font, ch)[0].draw(pen)
    return pen.contours


def shape_mask(contours):
    """One shape as (mask, left, top), filled even-odd so a counter is a hole.

    The mask is no bigger than the shape. A glyph is a few hundred pixels
    across and the band it is drawn into is thousands, and every contour costs
    one of these.
    """
    from PIL import Image, ImageChops, ImageDraw

    xs = [x for one in contours for x, _ in one]
    ys = [y for one in contours for _, y in one]
    left, top = math.floor(min(xs)) - 1, math.floor(min(ys)) - 1
    size = (math.ceil(max(xs)) - left + 2, math.ceil(max(ys)) - top + 2)
    mask = Image.new("1", size, 0)
    for points in contours:
        one = Image.new("1", size, 0)
        ImageDraw.Draw(one).polygon(
            [(x - left, y - top) for x, y in points], fill=1)
        mask = ImageChops.logical_xor(mask, one)
    return mask, left, top


def ink(size, shapes, capsules=()):
    """Every shape in one colour, as a mask: even-odd inside a shape, taken
    together across them, so two shapes that touch do not cancel out."""
    from PIL import Image, ImageDraw

    mask = Image.new("1", size, 0)
    for contours in shapes:
        one, left, top = shape_mask(contours)
        mask.paste(1, (left, top), one)
    draw = ImageDraw.Draw(mask)
    for x0, y0, x1, y1 in capsules:
        draw.rounded_rectangle((x0, y0, x1 - 1, y1 - 1),
                               radius=(x1 - x0) / 2, fill=1)
    return mask


def launch_png(css_w, css_h, scale):
    """One startup image, as PNG bytes: the launch screen at this screen size.

    The background is a flat fill at the image's own size, because the rest of
    a launch screen is one colour. The mark and the tagline are drawn into a
    band across it, OVERSAMPLE times larger and reduced. The band's top is
    floored to a whole device pixel and the remainder stays in the
    coordinates, so the drawing lands where the layout puts it rather than on
    a rounded row.
    """
    from PIL import Image

    at = launch_layout(css_w, css_h)
    mx, my, mw, mh = at["mark"]
    width, height = round(css_w * scale), round(css_h * scale)
    top = math.floor(my * scale)
    band_h = math.ceil((at["line_top"] + TAG_LINE) * scale) - top
    band = (width * OVERSAMPLE, band_h * OVERSAMPLE)
    k = scale * OVERSAMPLE

    def at_px(x, y):
        """CSS pixels on the screen to pixels in the band."""
        return (x * k, y * k - top * OVERSAMPLE)

    letters, bars, stop, (l, t, _, _) = mark_pieces()
    s = mw / MW                                   # font units to CSS pixels

    def of_mark(px, py):
        """A point in the mark's own space, as a point in the band."""
        return at_px(px * s + mx - l * s, py * s + my - t * s)

    def mark_glyph(ch, ox):
        return [[of_mark(fx + ox, -fy) for fx, fy in one]
                for one in outline(SYNE, ch)]

    capsules = []
    for bx, by, bwide, bhigh in bars:
        x0, y0 = of_mark(bx, by)
        x1, y1 = of_mark(bx + bwide, by + bhigh)
        capsules.append((x0, y0, x1, y1))

    sh = TAG_SIZE / HUPM
    glyphs, _ = line_pieces(HANK, TAG, TAG_SIZE, at["line_left"])

    def tag_glyph(ch, cx):
        return [[at_px(fx * sh + cx, at["baseline"] - fy * sh) for fx, fy in one]
                for one in outline(HANK, ch)]

    white = ink(band, [mark_glyph(ch, ox) for ch, ox in letters])
    amber = ink(band,
                [mark_glyph(*stop)] + [tag_glyph(ch, cx) for ch, cx in glyphs],
                capsules)

    canvas = Image.new("RGB", (width, height), BG)
    for mask, colour in ((white, WHITE), (amber, AMBER)):
        canvas.paste(colour, (0, top),
                     mask.convert("L").resize((width, band_h), Image.LANCZOS))
    out = io.BytesIO()
    canvas.save(out, "PNG", optimize=True)
    return out.getvalue()


def startup():
    """Every startup image, as {filename: bytes}. Nothing touches the disk."""
    return {startup_name(*screen): launch_png(*screen) for screen in IPHONES}


def pixels(blob):
    """Every pixel of a PNG, with no encoder in the way."""
    from PIL import Image

    with Image.open(io.BytesIO(blob)) as image:
        return image.convert("RGBA").tobytes()


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

    # 3. The launch screen at the reference size, from `launch_layout`, which
    #    is also what the startup images and app/web/index.html's CSS lay the
    #    screen out by. This file is what a designer opens; nothing at runtime
    #    serves it.
    at = launch_layout(LAUNCH_W, LAUNCH_H)
    mx, my, mw, _ = at["mark"]
    body, _ = place_mark(mw, mx, my)
    tag, _ = line(HANK, TAG, TAG_SIZE, at["line_left"], at["baseline"])
    files["prelude_launch.svg"] = svg(
        LAUNCH_W, LAUNCH_H, body + f'<path fill="{AMBER}" d="{tag}"/>', bg=BG,
        title=f"Prelude. {TAG}")
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
    shots = startup()
    print("mark     {:.0f} x {:.0f} font units, Syne wght 800".format(MW, MH))
    print("tagline  {!r}, Hanken Grotesk wght 500".format(TAG))
    print("out      {}".format(OUT.relative_to(ROOT).as_posix()))
    print("startup  {} iPhone screens into {}".format(
        len(shots), LAUNCH_OUT.relative_to(ROOT).as_posix()))
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
        # A PNG is compared pixel by pixel: Pillow encodes the same image a
        # few bytes differently on Windows and on the Linux runner, which
        # scripts/make_icons.py measured. The SVGs above are text and are
        # compared as they are written.
        for name, blob in shots.items():
            there = LAUNCH_OUT / name
            if not there.is_file():
                print("  MISSING  {}".format(name)); bad += 1
            elif pixels(there.read_bytes()) != pixels(blob):
                print("  DIFFERS  {}".format(name)); bad += 1
            else:
                print("  same     {:<26} {:>6,} bytes".format(
                    name, there.stat().st_size))
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
        for name, blob in shots.items():
            print("  would write {:<26} {:>6,} bytes".format(name, len(blob)))
        print()
        print("nothing was written. --confirm is what writes it.")
        return 0

    OUT.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (OUT / name).write_text(text, encoding="utf-8", newline="\n")
        print("  {:>6,} bytes  {}".format(len(text), name))
    LAUNCH_OUT.mkdir(parents=True, exist_ok=True)
    for name, blob in shots.items():
        (LAUNCH_OUT / name).write_bytes(blob)
        print("  {:>6,} bytes  {}".format(len(blob), name))
    print()
    print("wrote {} and {}".format(OUT.relative_to(ROOT).as_posix(),
                                   LAUNCH_OUT.relative_to(ROOT).as_posix()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
