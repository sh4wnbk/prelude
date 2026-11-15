"""Prelude's mark: the icon every screen links and the manifest beside it.

The mark is "Prelude." in Syne ExtraBold with the "u" redrawn as seven amber
bars, and **the icon is those bars alone**: at 32 px a wordmark is a smudge,
and the row of seven is the part of the mark that survives being small.
`scripts/brand/build_svg.py` draws the brand files from one set of numbers and
`scripts/make_icons.py` writes the icon set the screens link from two of them.

**The bars are drawn, not typed.** An icon is rendered where no font is
loaded, so a `<text font-family="Syne">` would be whatever font the machine
happens to have. The brand generator writes outlines, and the bitmaps are
rasterised from the square SVG's own path rather than from numbers written
out a second time.

**The two colours are tokens.** `surface` and `primary-container` as the
`tailwind-config` block the screens share defines them, and this holds the
brand file, the script and that block to one another.

**The icon this replaced** was "P." in Syne Bold, drawn by
`scripts/make_mark.py` in Task 32 from a font downloaded at build time. The
brand settles the question that stood in for: the mark exists, so the icon is
the mark's own element rather than its first two letters.
"""

import json
import re
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
BRAND = WEB / "assets" / "brand"
ICONS = WEB / "assets" / "icon"
MANIFEST = WEB / "manifest.webmanifest"
SHELL = WEB / "index.html"
ICON_SCRIPT = ROOT / "scripts" / "make_icons.py"
BRAND_SCRIPT = ROOT / "scripts" / "brand" / "build_svg.py"

SCREENS = sorted(WEB.glob("prelude_*.html"))
PAGES = SCREENS + [SHELL]

#: The two colours of the icon, by the token each one is. The brand files are
#: written in upper case and the screens' config block in lower.
SURFACE = "#101319"
PRIMARY_CONTAINER = "#ffb703"

#: The off-white the wordmark's letters take. The icon carries none of it:
#: there are no letters in the icon.
WHITE = "#FFFFFF"

#: The four brand files, and what each is for.
BRAND_FILES = (
    "prelude_mark.svg",
    "prelude_icon.svg",
    "prelude_icon_square.svg",
    "prelude_launch.svg",
)

#: Each bitmap and the square it has to be.
SIZES = {
    "favicon-32.png": 32,
    "apple-touch-icon-180.png": 180,
    "icon-192.png": 192,
    "icon-512.png": 512,
}

#: The seven bars, as a share of the x-height, left to right. The shape of the
#: icon in one line: written here so that a redraw that changed it has to
#: change this too.
BAR_HEIGHTS = (0.55, 1.0, 0.70, 0.92, 0.58, 0.32, 0.14)


def read(path):
    return path.read_text(encoding="utf-8")


def png_size(path):
    """The width and height out of a PNG's IHDR, without a decoder."""
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", path.name
    assert data[12:16] == b"IHDR", path.name
    return struct.unpack(">II", data[16:24])


def run(script, *args):
    return subprocess.run(
        [sys.executable, "-I", str(script), *args],
        cwd=ROOT, capture_output=True, text=True,
    )


class TestTheFilesAreThere:
    def test_every_brand_file(self):
        for name in BRAND_FILES:
            assert (BRAND / name).is_file(), name

    def test_the_vector(self):
        assert (ICONS / "favicon.svg").is_file()

    def test_every_bitmap(self):
        for name in SIZES:
            assert (ICONS / name).is_file(), name

    def test_each_bitmap_is_the_square_it_says(self):
        for name, size in SIZES.items():
            assert png_size(ICONS / name) == (size, size), name

    def test_the_manifest(self):
        assert MANIFEST.is_file()

    def test_the_icon_this_replaced_has_no_generator_left(self):
        assert not (ROOT / "scripts" / "make_mark.py").exists()


class TestTheCommittedFilesAreWhatTheNumbersDraw:
    """Both generators compare rather than trust. A brand file edited by hand,
    a number changed without a redraw, or a bitmap left behind by a redraw is
    a failing run here and not a difference nobody looks at."""

    def test_the_brand_files(self):
        done = run(BRAND_SCRIPT, "--check")
        assert done.returncode == 0, done.stdout + done.stderr
        assert "every committed brand file is what these numbers draw" in done.stdout

    def test_the_icon_set(self):
        done = run(ICON_SCRIPT, "--check")
        assert done.returncode == 0, done.stdout + done.stderr
        assert "every committed icon is what the brand icon draws" in done.stdout

    def test_neither_check_writes_anything(self):
        """`--check` is run by this suite, and a suite that rewrote a tracked
        file would be a suite whose own run is a change to the repo."""
        before = {p: p.read_bytes() for p in
                  sorted(BRAND.iterdir()) + sorted(ICONS.iterdir()) + [MANIFEST]}
        run(BRAND_SCRIPT, "--check")
        run(ICON_SCRIPT, "--check")
        assert {p: p.read_bytes() for p in before} == before


class TestTheIconIsTheBarsAndNothingElse:
    def svg(self):
        return read(ICONS / "favicon.svg")

    def test_it_is_the_brand_icon_itself(self):
        """`favicon.svg` is a copy, not a redrawing: the file the browser
        loads and the file the brand carries are one shape."""
        assert self.svg() == read(BRAND / "prelude_icon.svg")

    def test_it_holds_no_text_element(self):
        assert "<text" not in self.svg()
        assert "font-family" not in self.svg()

    def test_it_holds_one_path_and_that_path_is_the_bars(self):
        assert self.svg().count("<path ") == 1
        assert self.svg().count("Z") == len(BAR_HEIGHTS)

    def test_the_background_is_the_app_background(self):
        assert 'fill="%s"' % SURFACE.upper() in self.svg()

    def test_the_bars_are_amber(self):
        paths = re.findall(r'<path [^>]*fill="([^"]+)"', self.svg())
        assert paths == [PRIMARY_CONTAINER.upper()], paths

    def test_it_carries_none_of_the_wordmark_off_white(self):
        assert WHITE not in self.svg()

    def test_it_is_square(self):
        assert 'viewBox="0 0 1024.00 1024.00"' in self.svg()

    def test_its_corners_are_rounded_for_a_browser_tab(self):
        """A tab draws an icon as it is given, so this one rounds itself."""
        assert 'rx="229.1"' in self.svg()

    def test_the_square_source_does_not_round_them(self):
        """Every platform that shows a PNG rounds or crops it, and a second
        rounding reads as a shrunken badge."""
        assert "rx=" not in read(BRAND / "prelude_icon_square.svg")

    def test_it_says_what_it_is(self):
        assert "<title>Prelude icon</title>" in self.svg()
        assert 'aria-label="Prelude icon"' in self.svg()

    def test_it_names_no_one_else(self):
        for word in ("statsbomb", "ibm", "watson", "hudl"):
            assert word not in self.svg().lower(), word


class TestTheBitmapsAreTheSameIcon:
    """Read with a decoder, because the claim is about what a fan sees and
    not about the bytes."""

    def opened(self, name):
        from PIL import Image

        return Image.open(ICONS / name).convert("RGBA")

    def rgb(self, pixel):
        return "#%02x%02x%02x" % pixel[:3]

    def test_every_corner_is_the_app_background(self):
        """Square and opaque: a transparent corner would be a rounded icon,
        and the rounding is the platform's to do."""
        for name in SIZES:
            image = self.opened(name)
            side = image.size[0]
            for at in ((0, 0), (side - 1, 0), (0, side - 1), (side - 1, side - 1)):
                assert self.rgb(image.getpixel(at)) == SURFACE, (name, at)
                assert image.getpixel(at)[3] == 255, (name, at)

    def test_the_middle_is_amber_at_every_size(self):
        """The second bar is the tallest, so the centre row crosses every one
        of them; the centre of the square is inside the fourth."""
        for name in SIZES:
            image = self.opened(name)
            side = image.size[0]
            pixel = image.getpixel((side // 2, side // 2))
            assert pixel[0] > pixel[1] > pixel[2], (name, pixel)

    def runs_across_the_middle(self, name, size):
        """How many separate amber runs the centre row of the icon crosses."""
        image = self.opened(name)
        row = [image.getpixel((x, size // 2))[:3] for x in range(size)]
        amber = [r > g > b for r, g, b in row]
        return sum(1 for i, lit in enumerate(amber) if lit and not amber[i - 1])

    def test_all_seven_bars_are_separate_from_180_px_up(self):
        """The centre row crosses every bar, so seven runs of amber is the
        seven bars with daylight between them."""
        for name, size in SIZES.items():
            if size < 180:
                continue
            assert self.runs_across_the_middle(name, size) == len(BAR_HEIGHTS), name

    def test_the_32_px_bitmap_still_reads_as_bars(self):
        """At 32 px a bar is 1.5 px wide and a gap 1.25 px, so some gaps do
        not survive the reduction: measured on 2026-11-14, the seven come
        back as three runs rather than seven. It is still a row of bars and
        not a blob, and it is the fallback: a browser that can read
        `favicon.svg` takes the vector, where nothing is reduced."""
        assert self.runs_across_the_middle("favicon-32.png", 32) >= 3

    def test_nothing_is_drawn_in_the_wordmark_off_white(self):
        for name in SIZES:
            colours = self.opened(name).getcolors(1 << 20) or []
            assert (255, 255, 255, 255) not in [one for _, one in colours], name


class TestTheColoursAreTheScreensOwn:
    """The brand file holds two literals; the screens define two tokens. This
    is the read that keeps them one set."""

    def config(self):
        found = re.search(
            r'<script id="tailwind-config"[^>]*>(.*?)</script>',
            read(SCREENS[0]), re.S,
        )
        assert found, "no tailwind-config block on the first screen"
        return found.group(1)

    def test_the_background_is_surface(self):
        assert '"surface": "%s"' % SURFACE in self.config()

    def test_the_bars_are_primary_container(self):
        assert '"primary-container": "%s"' % PRIMARY_CONTAINER in self.config()

    def test_the_brand_generator_draws_in_those_two(self):
        source = read(BRAND_SCRIPT)
        assert 'WHITE, AMBER, BG = "%s", "%s", "%s"' % (
            WHITE, PRIMARY_CONTAINER.upper(), SURFACE.upper()) in source

    def test_the_icon_script_holds_the_same_two(self):
        source = read(ICON_SCRIPT)
        assert 'SURFACE = "%s"' % SURFACE in source
        assert 'PRIMARY_CONTAINER = "%s"' % PRIMARY_CONTAINER in source

    def test_the_bar_heights_are_the_generator_s_own(self):
        found = re.search(r"^BARS = \(([^)]+)\)", read(BRAND_SCRIPT), re.M)
        assert found, "no BARS tuple in the brand generator"
        assert tuple(float(v) for v in found.group(1).split(",")) == BAR_HEIGHTS


class TestEveryScreenLinksIt:
    def test_the_vector_first(self):
        for page in PAGES:
            assert (
                '<link href="assets/icon/favicon.svg?v=__V__" rel="icon" '
                'type="image/svg+xml"/>'
            ) in read(page), page.name

    def test_the_fallback_bitmap(self):
        for page in PAGES:
            assert (
                '<link href="assets/icon/favicon-32.png?v=__V__" rel="icon" '
                'sizes="32x32" type="image/png"/>'
            ) in read(page), page.name

    def test_the_home_screen_icon(self):
        for page in PAGES:
            assert (
                '<link href="assets/icon/apple-touch-icon-180.png?v=__V__" '
                'rel="apple-touch-icon" sizes="180x180"/>'
            ) in read(page), page.name

    def test_the_manifest(self):
        for page in PAGES:
            assert (
                '<link href="manifest.webmanifest?v=__V__" rel="manifest"/>'
            ) in read(page), page.name

    def test_the_browser_chrome_takes_the_app_background(self):
        for page in PAGES:
            assert '<meta content="%s" name="theme-color"/>' % SURFACE in read(page), (
                page.name
            )

    def test_nothing_links_an_ico(self):
        """The one file a browser used to ask for on its own. There is no
        `.ico` in the repo and nothing points at one."""
        for page in PAGES:
            assert ".ico" not in read(page), page.name
        assert not list(WEB.rglob("*.ico"))

    def test_the_links_carry_the_deploy_version(self):
        """`.github/workflows/pages.yml` stamps the commit into every `__V__`,
        so a deploy cannot serve last version's icon out of a cache."""
        for page in PAGES:
            for link in re.findall(r'<link href="(assets/icon/[^"]+)"', read(page)):
                assert link.endswith("?v=__V__"), (page.name, link)


class TestTheManifest:
    def doc(self):
        return json.loads(read(MANIFEST))

    def test_it_is_json(self):
        assert isinstance(self.doc(), dict)

    def test_it_names_the_app(self):
        assert self.doc()["name"] == "Prelude"
        assert self.doc()["short_name"] == "Prelude"

    def test_it_opens_on_the_shell(self):
        # The shell, not a screen: a screen reached with no match chosen sends
        # the fan to the list, and the shell is where the ticket query string
        # is read.
        assert self.doc()["start_url"] == "./index.html"

    def test_it_takes_the_app_background(self):
        assert self.doc()["background_color"] == SURFACE
        assert self.doc()["theme_color"] == SURFACE

    def test_it_offers_the_two_install_sizes(self):
        icons = self.doc()["icons"]
        assert [one["sizes"] for one in icons] == ["192x192", "512x512"]
        for one in icons:
            assert one["type"] == "image/png"
            assert (WEB / one["src"]).is_file(), one["src"]

    def test_the_large_icon_is_maskable(self):
        """An installer crops a maskable icon to a circle of 80% of the
        square. The bars sit inside that: the outermost corner of the widest
        bar is 30% of the square from the centre, against a safe 40%."""
        large = next(one for one in self.doc()["icons"] if one["sizes"] == "512x512")
        assert "maskable" in large["purpose"].split()

    def test_the_large_icon_is_offered_as_itself_too(self):
        """The square it is drawn on is the icon rather than padding around
        one, so it is also what an installer should show uncropped."""
        large = next(one for one in self.doc()["icons"] if one["sizes"] == "512x512")
        assert "any" in large["purpose"].split()

    def test_it_claims_nothing_about_the_app(self):
        # A manifest has a `description` field and this one does not use it:
        # there is no line about what Prelude does that belongs in an install
        # prompt and is also true at the moment it is shown.
        assert "description" not in self.doc()
