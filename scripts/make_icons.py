r"""Write the icon set the screens link, from the brand icon.

The icon is the Prelude mark's seven amber bars on the app background, with
no letters: at 32 px a wordmark is a smudge, and the bars are the part of the
mark that survives being small. `scripts/brand/build_svg.py` draws the two
sources this reads, and `scripts/brand/README.md` says where they come from.

| Source | What this does with it |
| ------ | ---------------------- |
| `app/web/assets/brand/prelude_icon.svg` | copied as `favicon.svg`; its corners are rounded, because a browser tab draws an icon as it is given |
| `app/web/assets/brand/prelude_icon_square.svg` | drawn as the four PNGs; its corners are square, because iOS, Android and a maskable install all round or crop an icon themselves and a second rounding reads as a shrunken badge |

What it writes, all under `app/web/assets/icon/`:

| File | What links it |
| ---- | ------------- |
| `favicon.svg` | every screen, as the first `icon` |
| `favicon-32.png` | every screen, for a browser with no SVG icon |
| `apple-touch-icon-180.png` | every screen, for an iPhone home screen |
| `icon-192.png`, `icon-512.png` | `app/web/manifest.webmanifest` |

**The bitmaps are drawn from the square SVG's own geometry, not from numbers
typed again here.** The path is matched whole against one shape repeated: a
capsule, as `scripts/brand/build_svg.py` emits one. Nothing in it may be left
over, and each capsule's own numbers have to agree with each other to inside
the two decimals the file is written to. A file this cannot read that way is a
file this refuses to rasterise, rather than one it guesses at.

**The 512 is marked maskable.** A maskable icon is cropped to a circle of 80%
of the square, and the bars sit inside that: the widest is 28% of the square
from the centre and the tallest 11%, which is 30% from the centre at the
corner of the outermost bar against a safe radius of 40%. The same file is
offered as `any`, because the square it is drawn on is the icon rather than
padding around one.

Run it:

    .\.venv-prelude\Scripts\python.exe -I scripts\make_icons.py --plan
    .\.venv-prelude\Scripts\python.exe -I scripts\make_icons.py --check
    .\.venv-prelude\Scripts\python.exe -I scripts\make_icons.py --confirm

`--check` draws everything and compares it with what is committed, writing
nothing. A PNG is compared pixel by pixel rather than byte by byte, because
Pillow encodes the same image a few bytes differently on Windows and on the
Linux runner CI uses. Needs `pillow`, in the dev group. It reaches nothing:
both sources are in this repo.
"""

import argparse
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
BRAND = WEB / "assets" / "brand"
ICONS = WEB / "assets" / "icon"
MANIFEST = WEB / "manifest.webmanifest"

ROUNDED = BRAND / "prelude_icon.svg"
SQUARE = BRAND / "prelude_icon_square.svg"

#: The two colours, which are tokens from the `tailwind-config` block the
#: screens share: `surface` and `primary-container`. They are read out of the
#: brand SVG rather than written here, and these are what they have to be.
#: `tests/test_the_mark.py` holds all three copies to each other.
SURFACE = "#101319"
PRIMARY_CONTAINER = "#ffb703"

#: The PNGs, by the file each is written to.
SIZES = {
    "favicon-32.png": 32,
    "apple-touch-icon-180.png": 180,
    "icon-192.png": 192,
    "icon-512.png": 512,
}

#: Each bitmap is drawn this many times larger and reduced, so an edge is the
#: shape's own curve rather than a rasteriser's idea of it at 32 px.
OVERSAMPLE = 4


N = r"-?[0-9.]+"
#: One bar: the capsule `scripts/brand/build_svg.py` emits, whose first arc is
#: the top half, then a vertical to the bottom, then the bottom half.
BAR = (rf"M({N}) ({N})A({N}) ({N}) 0 0 1 ({N}) ({N})V({N})"
       rf"A({N}) ({N}) 0 0 1 ({N}) ({N})Z")
BARS = re.compile(rf"(?:{BAR})+")
ONE_BAR = re.compile(BAR)

#: The file is written to two decimals, so two numbers meant to be equal can
#: differ by this much and no more.
ROUNDING = 0.0101
VIEWBOX = re.compile(r'viewBox="0 0 ([0-9.]+) ([0-9.]+)"')
BACKGROUND = re.compile(r'<rect width="([0-9.]+)" height="[0-9.]+"[^>]*fill="(#[0-9A-Fa-f]{6})"')
BARS_PATH = re.compile(r'<path fill="(#[0-9A-Fa-f]{6})" d="([^"]+)"')


def bar_box(numbers, where):
    """One capsule's (x, y, width, height), from the eleven numbers in it."""
    x, top_y, r1, r2, right, right_y, bottom_y, r3, r4, back_x, back_y = numbers
    radii = (r1, r2, r3, r4)
    width = right - x
    pairs = (
        ("the two radii of an arc", max(radii) - min(radii)),
        ("the width and twice the radius", width - 2 * max(radii)),
        ("the two ends of the top arc", top_y - right_y),
        ("the two ends of the bottom arc", bottom_y - back_y),
        ("the left edge and where the bottom arc returns to it", x - back_x),
    )
    for what, slack in pairs:
        if abs(slack) > ROUNDING:
            raise SystemExit(f"{where}: {what} differ by {slack:.4f}, which is "
                             "more than the file's two decimals allow")
    y = top_y - radii[0]
    if bottom_y + radii[0] - y < width - ROUNDING:
        raise SystemExit(f"{where}: a bar shorter than it is wide")
    return x, y, width, bottom_y + radii[0] - y


def read_icon(path):
    """The square, the two colours and the bars, out of a brand SVG.

    The path has to be capsules and nothing else, start to end, and each one's
    own numbers have to agree: that is this function saying it understood the
    file rather than that it found something path-shaped in it.
    """
    text = path.read_text(encoding="utf-8")
    box = VIEWBOX.search(text)
    back = BACKGROUND.search(text)
    drawn = BARS_PATH.search(text)
    if not (box and back and drawn):
        raise SystemExit(f"{path.name}: not the shape this can read "
                         "(a viewBox, a background rect and one filled path)")
    side = float(box.group(1))
    if float(box.group(2)) != side or float(back.group(1)) != side:
        raise SystemExit(f"{path.name}: the icon is not square")
    if not BARS.fullmatch(drawn.group(2)):
        raise SystemExit(f"{path.name}: the path is not capsules from end to "
                         "end, so it will not be redrawn from here")
    bars = [bar_box([float(v) for v in one.groups()], path.name)
            for one in ONE_BAR.finditer(drawn.group(2))]
    if not bars:
        raise SystemExit(f"{path.name}: the path draws no bars")
    return {
        "side": side,
        "background": back.group(2),
        "bars_colour": drawn.group(1),
        "bars": bars,
    }


def png(icon, size):
    """One bitmap of the square icon, as bytes."""
    from PIL import Image, ImageDraw

    canvas = size * OVERSAMPLE
    scale = canvas / icon["side"]
    image = Image.new("RGBA", (canvas, canvas), icon["background"])
    draw = ImageDraw.Draw(image)
    for x, y, w, h in icon["bars"]:
        left, top = x * scale, y * scale
        right, bottom = (x + w) * scale, (y + h) * scale
        draw.rounded_rectangle(
            (left, top, right - 1, bottom - 1),
            radius=(right - left) / 2, fill=icon["bars_colour"],
        )
    image = image.resize((size, size), Image.LANCZOS)
    out = io.BytesIO()
    image.save(out, "PNG", optimize=True)
    return out.getvalue()


def pixels(blob):
    """Every pixel of a PNG, as bytes, with no encoder in the way."""
    from PIL import Image

    with Image.open(io.BytesIO(blob)) as image:
        return image.convert("RGBA").tobytes()


def same(there, blob):
    """Whether the committed file is the file this draws.

    **A PNG is compared pixel by pixel and not byte by byte.** Pillow writes
    the same image through whatever zlib its wheel was built against, so the
    four bitmaps come out a few bytes different on Windows and on the Linux
    runner CI uses from the same Pillow version and the same drawing. The
    claim worth making is about the image, so the bytes are decoded and the
    pixels are compared; everything else here is text and is compared as it
    is written.
    """
    if there.suffix != ".png":
        return there.read_bytes() == blob
    return pixels(there.read_bytes()) == pixels(blob)


def manifest():
    """The manifest. `display: standalone` and the icons are what an install
    prompt asks for; nothing here claims anything about the app."""
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
                    "purpose": "any maskable",
                },
            ],
        },
        indent=2,
    ) + "\n"


def drawn():
    """Every file this writes, as {name: bytes}. Nothing here touches the disk."""
    rounded = ROUNDED.read_text(encoding="utf-8")
    square = read_icon(SQUARE)
    for which, colours in (("rounded", read_icon(ROUNDED)), ("square", square)):
        if colours["background"].lower() != SURFACE:
            raise SystemExit(f"the {which} brand icon's background is "
                             f"{colours['background']}, not {SURFACE}")
        if colours["bars_colour"].lower() != PRIMARY_CONTAINER:
            raise SystemExit(f"the {which} brand icon's bars are "
                             f"{colours['bars_colour']}, not {PRIMARY_CONTAINER}")
    files = {"favicon.svg": rounded.encode("utf-8")}
    for name, size in SIZES.items():
        files[name] = png(square, size)
    return files, square


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--plan", action="store_true",
                        help="print what would be written and write nothing")
    parser.add_argument("--check", action="store_true",
                        help="compare what this draws with what is committed")
    parser.add_argument("--confirm", action="store_true",
                        help="draw the icon set and write it")
    args = parser.parse_args(argv)

    files, square = drawn()
    body = manifest()
    print("icon     {} bars in {} on {}, read out of {}".format(
        len(square["bars"]), PRIMARY_CONTAINER, SURFACE,
        SQUARE.relative_to(ROOT).as_posix()))
    print("vector   {} is {}".format(
        (ICONS / "favicon.svg").relative_to(ROOT).as_posix(),
        ROUNDED.relative_to(ROOT).as_posix()))
    print("bitmaps  {}".format(", ".join(
        "{} at {} px".format(name, size) for name, size in SIZES.items())))
    print("manifest {}".format(MANIFEST.relative_to(ROOT).as_posix()))
    print()

    if args.check:
        bad = 0
        for name, blob in files.items():
            there = ICONS / name
            if not there.is_file():
                print("  MISSING  {}".format(name)); bad += 1
            elif not same(there, blob):
                print("  DIFFERS  {}".format(name)); bad += 1
            else:
                print("  same     {:<26} {:>6,} bytes".format(
                    name, there.stat().st_size))
        if not MANIFEST.is_file():
            print("  MISSING  manifest.webmanifest"); bad += 1
        elif MANIFEST.read_text(encoding="utf-8") != body:
            print("  DIFFERS  manifest.webmanifest"); bad += 1
        else:
            print("  same     {:<26} {:>6,} bytes".format(
                "manifest.webmanifest", len(body)))
        print()
        if bad:
            print("{} file(s) are not what the brand icon draws; "
                  "--confirm rewrites them".format(bad))
            return 1
        print("every committed icon is what the brand icon draws")
        return 0

    if args.plan or not args.confirm:
        for name, blob in files.items():
            print("  would write {:<26} {:>6,} bytes".format(name, len(blob)))
        print("  would write {:<26} {:>6,} bytes".format(
            "manifest.webmanifest", len(body)))
        print()
        print("nothing was written. --confirm is what writes it.")
        return 0

    ICONS.mkdir(parents=True, exist_ok=True)
    for name, blob in files.items():
        (ICONS / name).write_bytes(blob)
        print("  {:>6,} bytes  {}".format(len(blob), name))
    MANIFEST.write_text(body, encoding="utf-8", newline="\n")
    print()
    print("wrote {} and {}".format(ICONS.relative_to(ROOT).as_posix(),
                                   MANIFEST.relative_to(ROOT).as_posix()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
