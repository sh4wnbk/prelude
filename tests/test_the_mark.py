"""Prelude's mark: the icon every screen links and the manifest beside it.

The app had no icon. A browser asked for `/favicon.ico`, got a 404 and drew
its blank page glyph, and an iPhone home screen would have taken a screenshot
of the page instead. The mark is the wordmark's first two characters, a
capital P in Syne Bold with the full stop after it in amber, and
`scripts/make_mark.py` draws it.

**The glyphs are outlines, not text.** A favicon is rendered in a sandbox that
loads no font, so `<text font-family="Syne">` in an SVG icon would be whatever
font the machine happens to have, which on a judge's laptop is not Syne. The
script reads the two glyphs out of Syne Bold and writes them into the SVG as
paths, and draws the bitmaps with the same font, so the vector and the
rasters are one shape.

**The three colours are tokens.** `surface`, `on-surface` and
`primary-container` as the `tailwind-config` block the screens share defines
them, and this holds the script's copy to that block rather than to three
literals written twice.
"""

import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
ICONS = WEB / "assets" / "icon"
MANIFEST = WEB / "manifest.webmanifest"
SHELL = WEB / "index.html"
SCRIPT = ROOT / "scripts" / "make_mark.py"

SCREENS = sorted(WEB.glob("prelude_*.html"))
PAGES = SCREENS + [SHELL]

#: The three colours of the mark, by the token each one is.
SURFACE = "#101319"
ON_SURFACE = "#e1e2ea"
PRIMARY_CONTAINER = "#ffb703"

#: Each bitmap and the square it has to be.
SIZES = {
    "favicon-32.png": 32,
    "apple-touch-icon-180.png": 180,
    "icon-192.png": 192,
    "icon-512.png": 512,
}


def read(path):
    return path.read_text(encoding="utf-8")


def png_size(path):
    """The width and height out of a PNG's IHDR, without a decoder."""
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", path.name
    assert data[12:16] == b"IHDR", path.name
    return struct.unpack(">II", data[16:24])


class TestTheFilesAreThere:
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


class TestTheMarkIsDrawnRatherThanTyped:
    def svg(self):
        return read(ICONS / "favicon.svg")

    def test_it_holds_no_text_element(self):
        # An SVG icon is rendered with no font loading, so a `<text>` would be
        # a different letter on every machine.
        assert "<text" not in self.svg()
        assert "font-family" not in self.svg()

    def test_it_holds_one_path_per_glyph(self):
        assert self.svg().count("<path ") == 2

    def test_the_background_is_the_app_background(self):
        assert '<rect width="512" height="512" fill="%s"/>' % SURFACE in self.svg()

    def test_the_letter_is_off_white_and_the_stop_is_amber(self):
        paths = re.findall(r'<path [^>]*fill="([^"]+)"', self.svg())
        assert paths == [ON_SURFACE, PRIMARY_CONTAINER], paths

    def test_it_is_square(self):
        assert 'viewBox="0 0 512 512"' in self.svg()

    def test_it_says_what_it_is(self):
        # It is linked as an icon and used as an image, so it carries a name.
        assert "<title>Prelude</title>" in self.svg()
        assert 'aria-label="Prelude"' in self.svg()

    def test_it_names_no_one_else(self):
        # A mark is the one place a borrowed logo would not look out of place.
        for word in ("statsbomb", "ibm", "watson", "hudl"):
            assert word not in self.svg().lower(), word


class TestTheColoursAreTheScreensOwn:
    """The script writes three literals; the screens define three tokens. This
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

    def test_the_letter_is_on_surface(self):
        assert '"on-surface": "%s"' % ON_SURFACE in self.config()

    def test_the_stop_is_primary_container(self):
        assert '"primary-container": "%s"' % PRIMARY_CONTAINER in self.config()

    def test_the_script_uses_those_three_and_no_others(self):
        source = read(SCRIPT)
        assert 'SURFACE = "%s"' % SURFACE in source
        assert 'ON_SURFACE = "%s"' % ON_SURFACE in source
        assert 'PRIMARY_CONTAINER = "%s"' % PRIMARY_CONTAINER in source

    def test_the_script_draws_the_stop_in_the_amber(self):
        source = read(SCRIPT)
        assert 'MARK = (("P", ON_SURFACE), (".", PRIMARY_CONTAINER))' in source


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

    def test_it_claims_nothing_about_the_app(self):
        # A manifest has a `description` field and this one does not use it:
        # there is no line about what Prelude does that belongs in an install
        # prompt and is also true at the moment it is shown.
        assert "description" not in self.doc()
