r"""Draw the pictures `README.md` shows, from the app itself.

Seven files into `docs/images/`. Five are screenshots of the running app,
taken at 390 by 844 with a device scale factor of 2, which is the phone the
screens are designed for and the phone every browser run in `HANDOFF.md`
used. The sixth is the flow diagram, drawn here as one SVG and rasterised by
the same browser so it uses the app's own fonts and the app's own palette.
The seventh is the committed mark on the app's own background, for a README
that is read on whichever background the reader's theme sets.

**The screenshots are taken through the app's own controls.** Nothing writes
`sessionStorage` and nothing visits a screen with a query string that puts it
in the state wanted. The run opens `index.html` and taps: the 2022 card, then
Confirm event, then Argentina on the "Who are you with" card, then Continue,
then Profile, then the Buddy, then Live, then Heading out, then Moments. So a
screen that cannot be reached by tapping cannot be photographed either, and
the pictures in `README.md` are a path a fan can walk.

**It serves `app/web/` itself**, on a port the operating system picks, the way
`tests/browser/server.py` does for the browser suite. The deployed site is the
same files; serving them here means the picture is of the working tree, so a
screenshot cannot quietly be of an older deploy.

The diagram is drawn rather than rendered from the Mermaid block in
`README.md`, because nothing in this repo renders Mermaid and reaching for a
CDN to do it would make a committed image depend on a network. The two carry
the same nodes and the same edges; `NODES` and `EDGES` below are the diagram,
and the README's block is the same graph in Mermaid's own syntax.

Run it:

    .\.venv-prelude\Scripts\python.exe scripts\make_docs_images.py

`--check` draws everything into a temporary directory, compares it with what
is committed and writes nothing, which is the same bargain
`scripts/brand/build_svg.py` and `scripts/make_icons.py` offer. A screenshot
is a rasterised browser render, so `--check` reports a size and a pixel
difference rather than demanding the bytes be identical.
"""

import argparse
import functools
import http.server
import socketserver
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
IMAGES = ROOT / "docs" / "images"

#: The phone the screens are designed for, and the scale a retina screenshot
#: is taken at. 390 by 844 at 2 is a 780 by 1688 file.
VIEWPORT = {"width": 390, "height": 844}
SCALE = 2

#: The match the moment card is photographed on, and the side the fan is with.
#: Argentina is `team_a` in both matches, so an Argentina fan on the 2022
#: final is the `buddy_scored` slot, which is the Buddy telling it to the side
#: that scored.
MATCH = "3869685"
SIDE = "Argentina"
NARRATOR = "The Buddy"

#: The path the diagram is served at, so it is same origin with `fonts.css`
#: and the font files load. It is served out of memory and no such file exists
#: in `app/web/`.
DIAGRAM_PATH = "/__architecture__.html"

#: The same, for the mark. `app/web/assets/brand/prelude_mark.svg` is white
#: letters on nothing, which is right in the app, where the background is
#: always the app's own, and wrong in a README: GitHub renders it on whichever
#: background the reader's theme sets, and on a light one the wordmark is
#: invisible and the seven amber elements are not. So the mark is drawn here
#: on the surface colour it is designed over, and `README.md` shows that.
MARK_PATH = "/__mark__.html"

#: The mark's width in the picture, and the air around it.
MARK_WIDTH = 560
MARK_PADDING = 56


# ---------------------------------------------------------------- the server

class Handler(http.server.SimpleHTTPRequestHandler):
    """`app/web/`, plus the diagram page at `DIAGRAM_PATH`."""

    diagram = b""
    mark = b""

    def do_GET(self):
        made = {DIAGRAM_PATH: self.diagram, MARK_PATH: self.mark}
        body = made.get(self.path.split("?")[0])
        if body is not None:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def log_message(self, *args):
        pass


def serve(diagram, mark):
    """`app/web/` on a port the operating system picks."""
    # On the class, not on the partial: the handler instances read it as a
    # class attribute, and a partial's own attributes never reach them.
    Handler.diagram = diagram
    Handler.mark = mark
    handler = functools.partial(Handler, directory=str(WEB))
    server = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, "http://127.0.0.1:%d" % server.server_address[1]


# --------------------------------------------------------------- the diagram

#: One box: its key, where it sits, how wide it is, and the two lines in it.
#: The second line names the part of the stack the box is, which is what makes
#: the diagram answer "built with what" as well as "what happens next".
NODES = (
    ("facts", 16, 40, 206, "StatsBomb play data", "two matches, open data"),
    ("feed", 262, 40, 206, "EventFeed and orchestrator", "built with IBM Bob"),
    ("pipe", 508, 40, 206, "Narration pipeline", "watsonx.ai"),
    ("check", 754, 40, 206, "Grounding check", "every claim traced to a record"),
    ("six", 1000, 40, 206, "Six frozen narrations", "Watson Text to Speech"),
    ("agent", 16, 258, 250, "watsonx Orchestrate agent", "asks about a match"),
    ("api", 508, 258, 206, "The API", "Render"),
    ("app", 1000, 258, 206, "The app", "GitHub Pages"),
)

#: The same five edges the README's Mermaid block carries, as the sides they
#: leave and arrive on. "elbow" goes out of the bottom, across, and into the
#: top.
EDGES = (
    ("facts", "feed", "straight"),
    ("feed", "pipe", "straight"),
    ("pipe", "check", "straight"),
    ("check", "six", "straight"),
    ("six", "app", "down"),
    ("six", "api", "elbow"),
    ("agent", "api", "straight"),
)

#: The app's own palette, out of the Tailwind config the screens share.
SURFACE = "#101319"
CONTAINER = "#1d2025"
OUTLINE = "#514532"
AMBER = "#ffb703"
ON_AMBER = "#422c00"
ON_SURFACE = "#e1e2ea"
MUTED = "#9e8f78"

#: The boxes the grounding check guards, drawn in amber so the one thing the
#: diagram is about is the one thing that is not grey.
GUARD = {"check"}

BOX_HEIGHT = 92
WIDTH = 1222
HEIGHT = 400


def box_of(key):
    for name, x, y, w, line, sub in NODES:
        if name == key:
            return x, y, w, line, sub
    raise KeyError(key)


def wrap(text, limit=22):
    """Break a box's first line at `limit` characters, on a space."""
    words, lines, line = text.split(), [], ""
    for word in words:
        candidate = (line + " " + word).strip()
        if len(candidate) > limit and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


def arrow(a, b, shape):
    """One edge, as a path and an arrow head."""
    ax, ay, aw, _, _ = box_of(a)
    bx, by, bw, _, _ = box_of(b)
    stroke = AMBER if a in GUARD or b in GUARD else MUTED
    if shape == "straight":
        start = (ax + aw + 6, ay + BOX_HEIGHT / 2)
        end = (bx - 12, by + BOX_HEIGHT / 2)
        path = "M %.1f %.1f H %.1f" % (start[0], start[1], end[0])
        head = "%.1f,%.1f %.1f,%.1f %.1f,%.1f" % (
            end[0], end[1], end[0] - 9, end[1] - 5.5, end[0] - 9, end[1] + 5.5,
        )
    elif shape == "down":
        mid = ax + aw / 2
        path = "M %.1f %.1f V %.1f" % (mid, ay + BOX_HEIGHT + 6, by - 12)
        head = "%.1f,%.1f %.1f,%.1f %.1f,%.1f" % (
            mid, by, mid - 5.5, by - 9, mid + 5.5, by - 9,
        )
    else:   # elbow: out of the bottom, across, into the top
        mid = ax + aw / 2
        target = bx + bw / 2
        drop = ay + BOX_HEIGHT + 58
        path = "M %.1f %.1f V %.1f H %.1f V %.1f" % (
            mid, ay + BOX_HEIGHT + 6, drop, target, by - 12,
        )
        head = "%.1f,%.1f %.1f,%.1f %.1f,%.1f" % (
            target, by, target - 5.5, by - 9, target + 5.5, by - 9,
        )
    return (
        '<path d="%s" fill="none" stroke="%s" stroke-width="2" '
        'stroke-linejoin="round"/>\n<polygon points="%s" fill="%s"/>'
        % (path, stroke, head, stroke)
    )


def diagram_svg():
    """The flow diagram: the same graph as the README's Mermaid block."""
    parts = [
        '<svg id="architecture" xmlns="http://www.w3.org/2000/svg" '
        'width="%d" height="%d" viewBox="0 0 %d %d">' % (
            WIDTH, HEIGHT, WIDTH, HEIGHT),
        '<rect width="%d" height="%d" fill="%s"/>' % (WIDTH, HEIGHT, SURFACE),
    ]
    for a, b, shape in EDGES:
        parts.append(arrow(a, b, shape))
    for key, x, y, w, line, sub in NODES:
        amber = key in GUARD
        parts.append(
            '<rect x="%d" y="%d" width="%d" height="%d" rx="14" fill="%s" '
            'stroke="%s" stroke-width="%s"/>' % (
                x, y, w, BOX_HEIGHT,
                AMBER if amber else CONTAINER,
                AMBER if amber else OUTLINE, "2" if amber else "1.5",
            )
        )
        lines = wrap(line)
        top = y + (34 if len(lines) == 1 else 26)
        for index, text in enumerate(lines):
            parts.append(
                '<text x="%.1f" y="%.1f" text-anchor="middle" '
                'font-family="Syne" font-size="17" font-weight="600" '
                'fill="%s">%s</text>' % (
                    x + w / 2, top + index * 21,
                    ON_AMBER if amber else ON_SURFACE, text,
                )
            )
        parts.append(
            '<text x="%.1f" y="%.1f" text-anchor="middle" '
            'font-family="Hanken Grotesk" font-size="14" fill="%s">%s</text>'
            % (x + w / 2, y + BOX_HEIGHT - 24, ON_AMBER if amber else MUTED, sub)
        )
    parts.append(
        '<text x="%.1f" y="%d" text-anchor="middle" '
        'font-family="JetBrains Mono" font-size="13" letter-spacing="0.08em" '
        'fill="%s">THE GROUNDING CHECK SITS BETWEEN THE FACTS AND EVERY '
        'VOICE</text>' % (WIDTH / 2, HEIGHT - 28, MUTED)
    )
    parts.append("</svg>")
    return "\n".join(parts)


def diagram_page():
    return (
        "<!DOCTYPE html>\n<html><head><meta charset='utf-8'>"
        "<link href='fonts.css' rel='stylesheet'>"
        "<style>html,body{margin:0;padding:0;background:%s;}</style>"
        "</head><body>%s</body></html>" % (SURFACE, diagram_svg())
    ).encode("utf-8")


def mark_page():
    """The committed mark, on the surface colour it is drawn over."""
    return (
        "<!DOCTYPE html>"
        "<html><head><meta charset='utf-8'>"
        "<style>html,body{margin:0;padding:0;background:%s;}"
        "#mark{display:inline-block;padding:%dpx;background:%s;line-height:0;}"
        "#mark img{display:block;width:%dpx;height:auto;}</style>"
        "</head><body><div id='mark'>"
        "<img alt='' src='assets/brand/prelude_mark.svg'></div></body></html>"
        % (SURFACE, MARK_PADDING, SURFACE, MARK_WIDTH)
    ).encode("utf-8")


# ------------------------------------------------------------- the app's taps

#: Predicates about the document inside the shell's iframe, written to answer
#: false rather than throw: every one of them runs while that frame may still
#: be navigating, and `contentDocument.documentElement` is null then.
def flagged(attribute):
    """True once the screen in the frame has set `attribute` on its root."""
    return (
        "() => { const f = document.getElementById('screen'); "
        "const d = f && f.contentDocument; "
        "const r = d && d.documentElement; "
        "return !!r && r.hasAttribute('%s'); }" % attribute
    )


PLAY_OFFERED = (
    "() => { const f = document.getElementById('screen'); "
    "const d = f && f.contentDocument; "
    "const b = d && d.getElementById('playBtn'); "
    "return !!b && !b.disabled; }"
)

LAUNCH_GONE = (
    "() => { const l = document.getElementById('launch'); "
    "return !l || l.hasAttribute('hidden'); }"
)


def screen(page):
    """The document inside the shell's iframe."""
    return page.frame_locator("#screen")


def shoot(page, path):
    page.screenshot(path=str(path))
    return path


def take_the_screenshots(page, base, into):
    """The five app pictures, in the order a fan reaches them."""
    taken = {}

    # The launch screen, during the hold. The tagline is web type, so the
    # shot waits for the font: without that the mark is drawn and the line
    # under it is drawn in a fallback or not at all.
    page.goto(base + "/index.html", wait_until="commit")
    page.wait_for_selector("#launch-mark")
    page.wait_for_function(
        "() => document.fonts.check('500 16px \"Hanken Grotesk\"')"
    )
    assert not page.locator("#launch").get_attribute("data-going"), (
        "the launch screen had already begun to fade"
    )
    taken["launch.png"] = shoot(page, into / "launch.png")

    # The list, once the crossfade is over and no match is chosen.
    page.wait_for_function(LAUNCH_GONE, timeout=15000)
    screen(page).locator("#confirm-btn").wait_for()
    page.wait_for_function(flagged("data-matches-loaded"))
    assert screen(page).locator(".event-card[aria-checked='true']").count() == 0, (
        "a card was already selected on the list"
    )
    taken["picker.png"] = shoot(page, into / "picker.png")

    # Tap the 2022 card, confirm it, and answer "Who are you with".
    screen(page).locator(".event-card[data-match='%s']" % MATCH).click()
    screen(page).locator("#confirm-btn").click()
    screen(page).locator("#listener-choices").wait_for()
    screen(page).locator(
        "#listener-choices button[data-value='team_a']"
    ).click()
    screen(page).locator("#listener-continue").click()
    screen(page).locator("#listener-choices").wait_for(state="detached")

    # Profile, and the Buddy chosen on it.
    screen(page).locator("nav a[data-path='profile']").click()
    screen(page).locator(
        "[data-field='narrator_list'] button"
    ).first.wait_for()
    screen(page).get_by_role("button", name=NARRATOR, exact=False).click()
    screen(page).locator(
        "[data-field='narrator_list'] button[aria-current='true']"
    ).wait_for()
    page.wait_for_timeout(300)
    taken["profile.png"] = shoot(page, into / "profile.png")

    # Live, then heading out, which is what produces a buildup.
    screen(page).locator("nav a[data-path='live']").click()
    screen(page).locator("#headingOutBtn").click()
    screen(page).locator("[data-field='hero_label']").wait_for()
    screen(page).locator("[data-field='hero_claims']").wait_for()
    page.wait_for_function(PLAY_OFFERED)
    page.wait_for_timeout(300)
    for field in ("hero_label", "hero_claims"):
        box = screen(page).locator("[data-field='%s']" % field).bounding_box()
        assert box and 0 <= box["y"] <= VIEWPORT["height"] - box["height"], (
            "%s is not in the viewport: %r" % (field, box)
        )
    taken["moment_card.png"] = shoot(page, into / "moment_card.png")

    # Moments.
    screen(page).locator("nav a[data-path='moments']").click()
    page.wait_for_function(flagged("data-match-rendered"))
    page.wait_for_timeout(300)
    taken["moments.png"] = shoot(page, into / "moments.png")
    return taken


def take_the_diagram(browser, base, into):
    context = browser.new_context(device_scale_factor=SCALE)
    page = context.new_page()
    page.goto(base + DIAGRAM_PATH)
    page.wait_for_function(
        "() => document.fonts.check('600 17px Syne') && "
        "document.fonts.check('400 14px \"Hanken Grotesk\"') && "
        "document.fonts.check('13px \"JetBrains Mono\"')"
    )
    page.locator("#architecture").screenshot(path=str(into / "architecture.png"))

    page.goto(base + MARK_PATH)
    page.wait_for_selector("#mark img")
    page.wait_for_function(
        "() => { const i = document.querySelector('#mark img'); "
        "return !!i && i.complete && i.naturalWidth > 0; }"
    )
    page.locator("#mark").screenshot(path=str(into / "mark.png"))
    context.close()
    return {
        "architecture.png": into / "architecture.png",
        "mark.png": into / "mark.png",
    }


def draw(into):
    """Every picture, into `into`. Returns {name: path}."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit(
            "playwright is not installed; it is in the dev group "
            "(uv sync --group dev, then python -m playwright install chromium)"
        )

    server, base = serve(diagram_page(), mark_page())
    try:
        with sync_playwright() as driver:
            browser = driver.chromium.launch()
            context = browser.new_context(
                viewport=VIEWPORT, has_touch=True, is_mobile=True,
                device_scale_factor=SCALE,
            )
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            taken = take_the_screenshots(page, base, into)
            assert not errors, errors
            context.close()
            taken.update(take_the_diagram(browser, base, into))
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    return taken


def report(taken):
    for name in sorted(taken):
        path = taken[name]
        print("  %-20s %7d bytes" % (name, path.stat().st_size))


def compare(drawn):
    """Each drawn file against the committed one, by size and by pixels."""
    from PIL import Image, ImageChops

    stale = []
    for name in sorted(drawn):
        committed = IMAGES / name
        if not committed.exists():
            stale.append("%s: not committed" % name)
            continue
        fresh, old = Image.open(drawn[name]), Image.open(committed)
        if fresh.size != old.size:
            stale.append("%s: %r drawn, %r committed" % (name, fresh.size, old.size))
            continue
        box = ImageChops.difference(fresh.convert("RGB"), old.convert("RGB"))
        # Every non-black pixel of the difference, counted out of the
        # histogram rather than pixel by pixel.
        differing = sum(box.convert("L").histogram()[1:])
        total = fresh.size[0] * fresh.size[1]
        share = 100.0 * differing / total
        print("  %-20s %s (%d of %d pixels, %.2f%%)" % (
            name, "same" if not differing else "differs", differing, total, share,
        ))
        if share > 1.0:
            stale.append("%s: %.2f%% of pixels differ" % (name, share))
    return stale


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true",
        help="draw into a temporary directory and compare; write nothing",
    )
    args = parser.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory() as into:
            drawn = draw(Path(into))
            print("checking docs/images against the app")
            stale = compare(drawn)
        if stale:
            print("\n%d stale image(s):" % len(stale))
            for one in stale:
                print("  " + one)
            return 1
        print("\nevery image is what the app draws")
        return 0

    IMAGES.mkdir(parents=True, exist_ok=True)
    taken = draw(IMAGES)
    print("wrote %d image(s) into docs/images/" % len(taken))
    report(taken)
    return 0


if __name__ == "__main__":
    sys.exit(main())
