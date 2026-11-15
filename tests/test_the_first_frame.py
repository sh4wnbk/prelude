"""What every page does before anything it links has loaded.

`CLAUDE.md` counts the frames before any script has run as a state a fan can
see, and the first of those frames is drawn before a stylesheet has arrived.
Three things keep that frame from being white, and all three are in markup
rather than in script:

- **Every page sets the app background in its own head**, on `html` and
  `body`, in front of every `<link>` it carries. The same bytes in all eight,
  so no page can be the one that was missed.
- **Every screen says when it has painted**, with `data-painted` on its own
  root element, two animation frames after `DOMContentLoaded`: one frame has
  been drawn with that background and its own stylesheet applied.
- **The shell's iframe carries the same background and starts invisible.** A
  browser paints an empty frame white, and the launch screen covers it only
  until the fade begins, so without this the white is what the fade uncovers.
  Shawn saw that flash at the top of an iPhone XR on 2026-11-15.

`tests/browser/test_the_launch_screen.py` is where the behaviour is measured
in a browser: that no sampled frame of the top of the screen is white, and
that the list is painted before it is ever visible. This file is about the
markup those measurements rest on.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
SHELL = WEB / "index.html"
SCREENS = tuple(sorted(WEB.glob("prelude_*.html")))
PAGES = (SHELL,) + SCREENS

#: `surface`, the app background, read out of the shared Tailwind config block
#: by `tests/test_the_mark.py` and written here as the literal it is: a test
#: value is a literal next to the check and not a value derived from another.
SURFACE = "#101319"

#: The block every page carries, byte for byte.
BACKGROUND = "<style>html,body{background-color:%s;}</style>" % SURFACE

#: Every `<link>` and every inline `<style>`, in the order the parser meets
#: them, so "before any stylesheet" can be asked as a question about order.
LINK_OR_STYLE = re.compile(r"<link\b[^>]*>|<style\b[^>]*>", re.IGNORECASE)


def read(path):
    return path.read_text(encoding="utf-8")


class TestTheBackgroundIsSetFirst:
    def test_every_page_carries_the_same_block(self):
        for page in PAGES:
            assert BACKGROUND in read(page), page.name

    def test_it_names_the_app_background(self):
        """The one colour. `tests/test_the_mark.py` holds the manifest, the
        startup images and this to the same value."""
        assert SURFACE in BACKGROUND

    def test_it_is_in_front_of_every_stylesheet(self):
        """A stylesheet blocks the first paint, so a background that arrived
        with one would be a background that arrived after the frame it was
        for. This is the first style in the document either way."""
        for page in PAGES:
            text = read(page)
            found = [match.group(0) for match in LINK_OR_STYLE.finditer(text)]
            assert found, page.name
            assert found[0] == "<style>", (page.name, found[0])
            at = text.index(BACKGROUND)
            for match in LINK_OR_STYLE.finditer(text):
                if "stylesheet" in match.group(0):
                    assert at < match.start(), (page.name, match.group(0))

    def test_it_is_both_elements(self):
        """`html` and `body`: the canvas takes the root element's background,
        and a short page leaves the rest of the viewport to the body's."""
        assert "html,body{" in BACKGROUND


class TestEveryScreenSaysWhenItHasPainted:
    """`data-painted`, which the shell waits for before it reveals the frame.

    Two animation frames after `DOMContentLoaded`: the first callback runs
    before the paint it is scheduled for and the second after it, so the
    attribute means a frame has been drawn and not that one is due.
    """

    def painted(self):
        """The block, read off the first screen rather than written twice."""
        text = read(SCREENS[0])
        at = text.index("data-painted")
        return text[text.rindex("<script>", 0, at):
                    text.index("</script>", at) + len("</script>")]

    def test_every_screen_carries_it(self):
        for screen in SCREENS:
            assert "data-painted" in read(screen), screen.name

    def test_it_is_the_same_block_in_every_screen(self):
        block = self.painted()
        for screen in SCREENS:
            assert block in read(screen), screen.name

    def test_it_waits_two_animation_frames(self):
        block = self.painted()
        assert block.count("requestAnimationFrame") == 2, block
        assert "DOMContentLoaded" in block, block

    def test_it_sets_the_attribute_on_the_root_element(self):
        """Where the shell reads it: `contentDocument.documentElement`."""
        block = self.painted()
        assert 'documentElement.setAttribute("data-painted","1")' in block, block

    def test_the_shell_carries_no_such_signal(self):
        """Nothing frames the shell, so it has nobody to tell."""
        assert "data-painted" in read(SHELL)       # it reads one
        assert "setAttribute('data-painted'" not in read(SHELL)
        assert 'setAttribute("data-painted"' not in read(SHELL)

    def test_it_is_in_front_of_every_stylesheet_too(self):
        """It is two lines of script in the head and it runs on an event, so
        where it sits changes nothing about when it fires. It sits with the
        background block because the two are one answer to one question."""
        for screen in SCREENS:
            text = read(screen)
            at = text.index("data-painted")
            for match in LINK_OR_STYLE.finditer(text):
                if "stylesheet" in match.group(0):
                    assert at < match.start(), (screen.name, match.group(0))


class TestTheFrameIsNeverWhite:
    """The shell's iframe: the app background on the element, and invisible
    until the screen inside it has painted."""

    def block(self):
        return read(SHELL).split("  #screen {")[1].split("}")[0]

    def test_it_carries_the_app_background(self):
        """On the element, which this page paints, as well as in the screen's
        own head, which the screen paints. The frame exists before the
        document in it does."""
        assert "background-color: %s;" % SURFACE in self.block(), self.block()

    def test_it_starts_invisible(self):
        assert "opacity: 0;" in self.block(), self.block()

    def test_it_is_revealed_by_an_attribute_and_not_by_a_style(self):
        """One attribute, set in one place, so the state is readable from the
        markup in any frame a check recorded."""
        assert "#screen[data-shown] { opacity: 1; }" in read(SHELL)

    def test_it_is_revealed_only_where_the_screen_said_it_painted(self):
        """`ready()` asks for both: matches.json answered, and a frame
        painted. The cap is the one other way through, and it reveals the
        frame as it ends the launch screen."""
        shell = read(SHELL)
        at = shell.index("function ready()")
        body = shell[at:shell.index("}", shell.index("{", at))]
        assert "data-matches-loaded" in body, body
        assert "data-painted" in body, body
        assert shell.count("function show()") == 1, shell.count("function show()")
