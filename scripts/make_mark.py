r"""Draw Prelude's mark and write the icon set the screens link.

The mark is the wordmark's first two characters: a capital P in Syne Bold in
the app's off-white, and the full stop after it in the app's amber, on the app
background. Nothing in it is a word, a claim or a logo of anyone else's.

| Piece | Colour |
| ----- | ------ |
| background | `#101319`, `surface` |
| the P | `#e1e2ea`, `on-surface` |
| the full stop | `#ffb703`, `primary-container` |

**The glyphs are outlines, not text.** A favicon is rendered in a sandbox that
loads no font, so `<text font-family="Syne">` in an SVG icon is whatever font
the machine happens to have. So the two glyphs are read out of Syne Bold and
written into `favicon.svg` as paths, and the same font draws the PNGs through
Pillow, which is why the vector and the bitmaps are one shape.

**Syne Bold is downloaded, not committed.** `app/web/assets/fonts/` holds the
`woff2` subsets a browser reads, and `woff2` needs Brotli to open; the static
`700` instance Google serves an old client is a plain TrueType file. It is
read in a temporary directory and nothing of it is kept: what the repo carries
is the five files this writes.

What it writes, all under `app/web/assets/icon/`:

| File | What links it |
| ---- | ------------- |
| `favicon.svg` | every screen, as the first `icon` |
| `favicon-32.png` | every screen, for a browser with no SVG icon |
| `apple-touch-icon-180.png` | every screen, for an iPhone home screen |
| `icon-192.png`, `icon-512.png` | `app/web/manifest.webmanifest` |

The PNGs are square and the SVG is a square viewBox, because every consumer of
them crops to a square or a circle and a mark that is not centred in one is a
mark that is cut.

Run it:

    .\.venv-prelude\Scripts\python.exe -I scripts\make_mark.py --plan
    .\.venv-prelude\Scripts\python.exe -I scripts\make_mark.py --confirm

Needs `fonttools` and `pillow`, both in the dev group.
"""

import argparse
import json
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
ICONS = WEB / "assets" / "icon"
MANIFEST = WEB / "manifest.webmanifest"

#: The three colours, which are tokens from the `tailwind-config` block the
#: screens share. Written here rather than read from it: this file draws an
#: icon and does not compile a stylesheet, and `tests/test_the_mark.py` holds
#: the two copies to each other.
SURFACE = "#101319"
ON_SURFACE = "#e1e2ea"
PRIMARY_CONTAINER = "#ffb703"

#: The glyphs, in order, and the colour each one takes.
MARK = (("P", ON_SURFACE), (".", PRIMARY_CONTAINER))

#: The square the mark is drawn in, in SVG user units. A round number, so the
#: numbers in the file are readable.
BOX = 512

#: How much of the box the mark fills across, and where its baseline sits as a
#: share of the box. Picked by eye at 32 px, which is the size that decides
#: whether a mark reads: too large and the P touches the edge in a circular
#: crop, too small and the full stop disappears.
FILL = 0.62
BASELINE = 0.72

#: The PNGs, by the file they are written to.
SIZES = {
    "favicon-32.png": 32,
    "apple-touch-icon-180.png": 180,
    "icon-192.png": 192,
    "icon-512.png": 512,
}

#: Where Syne Bold comes from. The `css2` endpoint answers a client that does
#: not say it reads `woff2` with the static `700` instance in TrueType, which
#: is what both fontTools and Pillow open without a Brotli decoder. The client
#: name is this build and nothing about the machine running it.
SYNE_CSS = "https://fonts.googleapis.com/css2?family=Syne:wght@700"
PLAIN_UA = "prelude-build"


def syne_bold(into: Path) -> Path:
    """Download the static Syne Bold instance and hand back the file."""
    import re

    request = urllib.request.Request(SYNE_CSS, headers={"User-Agent": PLAIN_UA})
    with urllib.request.urlopen(request, timeout=60) as answer:
        css = answer.read().decode("utf-8")
    found = re.search(r"src:\s*url\(([^)]+)\)", css)
    if not found:
        raise SystemExit(
            "Google answered with no font URL for Syne Bold:\n" + css
        )
    url = found.group(1)
    with urllib.request.urlopen(
        urllib.request.Request(url, headers={"User-Agent": PLAIN_UA}), timeout=60
    ) as answer:
        body = answer.read()
    if body[:4] not in (b"\x00\x01\x00\x00", b"true", b"ttcf", b"OTTO"):
        raise SystemExit(
            "that URL did not answer with a TrueType file (first bytes "
            "{!r})".format(body[:8])
        )
    path = into / "Syne-Bold.ttf"
    path.write_bytes(body)
    return path


def outlines(font_path: Path):
    """Each glyph of the mark as an SVG path, with the pen's advance.

    The paths come back in font units with y upwards, which is the opposite of
    SVG; the caller flips and scales them in one transform rather than
    rewriting the numbers.
    """
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.ttLib import TTFont

    font = TTFont(str(font_path))
    cmap = font.getBestCmap()
    glyphs = font.getGlyphSet()
    drawn = []
    for character, colour in MARK:
        name = cmap.get(ord(character))
        if name is None:
            raise SystemExit(
                "Syne Bold has no glyph for {!r}".format(character)
            )
        pen = SVGPathPen(glyphs)
        glyphs[name].draw(pen)
        drawn.append({
            "character": character,
            "colour": colour,
            "path": pen.getCommands(),
            "width": glyphs[name].width,
        })
    return drawn, font["head"].unitsPerEm


def svg(drawn, units_per_em: int) -> str:
    """The mark as one square SVG, with the glyphs as paths."""
    advance = sum(one["width"] for one in drawn)
    scale = (BOX * FILL) / advance
    left = (BOX - advance * scale) / 2
    baseline = BOX * BASELINE

    pieces = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {box} {box}" '
        'width="{box}" height="{box}" role="img" '
        'aria-label="Prelude">'.format(box=BOX),
        "<title>Prelude</title>",
        '<rect width="{box}" height="{box}" fill="{fill}"/>'.format(
            box=BOX, fill=SURFACE
        ),
        '<g transform="translate({left:.3f} {baseline:.3f}) '
        'scale({scale:.6f} -{scale:.6f})">'.format(
            left=left, baseline=baseline, scale=scale
        ),
    ]
    at = 0.0
    for one in drawn:
        pieces.append(
            '<path transform="translate({at:.3f} 0)" fill="{colour}" '
            'd="{path}"/>'.format(at=at, colour=one["colour"], path=one["path"])
        )
        at += one["width"]
    pieces.append("</g>")
    pieces.append("</svg>")
    return "\n".join(pieces) + "\n"


def pngs(font_path: Path) -> dict:
    """The four bitmaps, drawn with the same font at each size."""
    from PIL import Image, ImageDraw, ImageFont

    written = {}
    for name, size in SIZES.items():
        # Drawn four times larger and reduced, so the edges are the font's own
        # curves rather than the hinter's idea of them at 32 px.
        scale = 4
        canvas = size * scale
        image = Image.new("RGBA", (canvas, canvas), SURFACE)
        draw = ImageDraw.Draw(image)

        # Find the point size that fills the box across, by measuring.
        points = canvas
        for _ in range(40):
            font = ImageFont.truetype(str(font_path), points)
            width = draw.textlength("".join(c for c, _ in MARK), font=font)
            if width <= canvas * FILL or points <= 4:
                break
            points = max(4, int(points * (canvas * FILL) / max(width, 1)))
        font = ImageFont.truetype(str(font_path), points)
        width = draw.textlength("".join(c for c, _ in MARK), font=font)
        at = (canvas - width) / 2
        baseline = canvas * BASELINE
        for character, colour in MARK:
            draw.text((at, baseline), character, font=font, fill=colour,
                      anchor="ls")
            at += draw.textlength(character, font=font)
        image = image.resize((size, size), Image.LANCZOS)
        image.save(ICONS / name, "PNG", optimize=True)
        written[name] = (ICONS / name).stat().st_size
    return written


#: The manifest. `display: standalone` and the two icons are what an install
#: prompt asks for; nothing here claims anything about the app.
def manifest() -> str:
    return json.dumps(
        {
            "name": "Prelude",
            "short_name": "Prelude",
            "start_url": "./index.html",
            "scope": "./",
            "display": "standalone",
            "background_color": SURFACE,
            "theme_color": SURFACE,
            "icons": [
                {
                    "src": "assets/icon/icon-192.png",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any",
                },
                {
                    "src": "assets/icon/icon-512.png",
                    "sizes": "512x512",
                    "type": "image/png",
                    "purpose": "any",
                },
            ],
        },
        indent=2,
    ) + "\n"


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--plan", action="store_true",
        help="print what would be written and write nothing",
    )
    parser.add_argument(
        "--confirm", action="store_true", help="draw the mark and write it",
    )
    args = parser.parse_args(argv)

    print("mark     {!r} in Syne Bold, {} on {}, the stop in {}".format(
        "".join(c for c, _ in MARK), ON_SURFACE, SURFACE, PRIMARY_CONTAINER
    ))
    print("vector   {}".format(
        (ICONS / "favicon.svg").relative_to(ROOT).as_posix()
    ))
    print("bitmaps  {}".format(", ".join(
        "{} at {} px".format(name, size) for name, size in SIZES.items()
    )))
    print("manifest {}".format(MANIFEST.relative_to(ROOT).as_posix()))
    print()
    if args.plan or not args.confirm:
        print("nothing was written. --confirm is what writes it.")
        return 0

    ICONS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="prelude-mark-") as tmp:
        font_path = syne_bold(Path(tmp))
        print("  downloaded Syne Bold, {:,} bytes".format(
            font_path.stat().st_size
        ))
        drawn, units = outlines(font_path)
        for one in drawn:
            print("  {!r}: {:,} path characters, advance {}".format(
                one["character"], len(one["path"]), one["width"]
            ))
        (ICONS / "favicon.svg").write_text(
            svg(drawn, units), encoding="utf-8", newline="\n"
        )
        print("  {:>7,} bytes  favicon.svg".format(
            (ICONS / "favicon.svg").stat().st_size
        ))
        for name, size in pngs(font_path).items():
            print("  {:>7,} bytes  {}".format(size, name))
    MANIFEST.write_text(manifest(), encoding="utf-8", newline="\n")
    print()
    print("wrote {} and {}".format(
        ICONS.relative_to(ROOT).as_posix(), MANIFEST.relative_to(ROOT).as_posix()
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
