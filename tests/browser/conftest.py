"""Fixtures for the browser suite, and the facts it checks the app against.

Every check in this directory drives a real browser over a real server, so it
is slower than the unit suite and it needs a browser installed. It is kept out
of the default run by `norecursedirs` in `pyproject.toml` and is run by naming
it:

    .\\.venv-prelude\\Scripts\\python.exe -m pytest tests/browser

Every test collected here is marked `browser`, so `-m browser` and
`-m "not browser"` both mean what they say inside this path.

**What the expectations come from.** Nothing here writes down which words or
which file a fan should get. The slot rule is `app.api.slot_for`, which is the
Python copy of `Prelude.slotFor`, and the words and the files come from
`app/web/narrations.json` and `hero.audio` in `app/web/matches.json`. So a
check reads what the browser resolved and compares it with what those three
answer. A rule changed in one language and not the other fails here as well as
in `tests/test_api.py`.

**Storage.** `prelude.listener.<match>` and `prelude.name` are session values
and `prelude.narrator` is a standing one in localStorage, which is why the
narrator survives a closed tab. The fixtures write them through the page the
way the app does, from a URL on the same origin, and `fresh` is a context with
neither.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
WEB = ROOT / "app" / "web"

sys.path.insert(0, str(ROOT))

from tests.browser import server as local_server   # noqa: E402

#: The phone the screens are designed for, which every HANDOFF browser run
#: used: 390 by 844.
VIEWPORT = {"width": 390, "height": 844}

#: The answers to "Who are you with", and the narrator states a fan can be in.
#: `None` is a fan who has chosen no narrator, which is how the app ships.
LISTENERS = ("team_a", "team_b", "neutral")
NARRATORS = (None, "storyteller", "buddy")

#: The screens that are about one match, so reaching one with no match chosen
#: sends the fan to the list. The same five `MATCH_REQUIRED` names in
#: `app/web/match-content.js`.
MATCH_REQUIRED = (
    "prelude_02_live_seated.html",
    "prelude_03_moment_card.html",
    "prelude_04_moments.html",
    "prelude_06_ticket.html",
    "prelude_07_profile.html",
)

PICKER = "prelude_01_picker.html"
SCANNER = "prelude_05_scan.html"
MOMENT_CARD = "prelude_03_moment_card.html"
MOMENTS = "prelude_04_moments.html"
LIVE = "prelude_02_live_seated.html"
PROFILE = "prelude_07_profile.html"

ALL_SCREENS = tuple(sorted(path.name for path in WEB.glob("prelude_*.html")))

#: The one 404 a browser asks for on its own and which no screen links to.
EXPECTED_404 = "favicon.ico"

#: Where the screens get Tailwind and their fonts. The suite serves
#: `app/web/` and not these, and the deployed site loads them from the same
#: places, so a slow or blocked CDN is not the screens being broken. A failure
#: from one of these is kept on `Fan.outside` rather than counted against the
#: page, and anything on the suite's own origin still counts.
OUTSIDE = (
    "cdn.tailwindcss.com",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
)


def from_outside(text):
    return any(host in (text or "") for host in OUTSIDE)


#: Predicates for `wait_for_function`, written to answer false rather than
#: throw. `wait_for_function` tries a false predicate again on the next frame
#: and gives up at once on one that throws, and every one of these runs while
#: the page may still be navigating: `document.documentElement` is null then,
#: and the elements are not there yet. The first CI run failed 38 checks on
#: exactly that, on a runner faster than the machine they were written on.
RENDERED = (
    "() => !!document.documentElement && "
    "document.documentElement.hasAttribute('data-match-rendered')"
)

PLAY_OFFERED = (
    "() => { const b = document.getElementById('playBtn'); "
    "return !!b && !b.disabled; }"
)


def track_reads(attribute, comparison):
    """A null-safe predicate about one of the scrubber's aria values.

    `comparison` is written against `v`, the number the attribute holds, for
    example `track_reads("valuenow", "v > 1.2")`.
    """
    return (
        "() => { const t = document.getElementById('scrubTrack'); "
        "if (!t) return false; "
        "const v = Number(t.getAttribute('aria-" + attribute + "')); "
        "return " + comparison + "; }"
    )


def pytest_collection_modifyitems(items):
    """Mark everything here `browser`, so the mark and the path agree."""
    for item in items:
        item.add_marker(pytest.mark.browser)


@pytest.fixture(scope="session")
def matches():
    doc = json.loads((WEB / "matches.json").read_text(encoding="utf-8"))
    return {entry["match_id"]: entry for entry in doc["matches"]}


@pytest.fixture(scope="session")
def narrations():
    doc = json.loads((WEB / "narrations.json").read_text(encoding="utf-8"))
    return doc["narrations"]


@pytest.fixture(scope="session")
def narrators():
    doc = json.loads((WEB / "narrators.json").read_text(encoding="utf-8"))
    return doc["narrators"]


@pytest.fixture(scope="session")
def match_ids(matches):
    return tuple(sorted(matches))


@pytest.fixture(scope="session")
def slot_rule():
    """`app.api.slot_for`, the Python copy of the rule the browser applies."""
    from app.api import slot_for

    return slot_for


@pytest.fixture(scope="session")
def expected(matches, narrations, slot_rule):
    """What a fan should get, by (match, listener, narrator).

    The slot from the rule, the words from `narrations.json` and the file from
    `hero.audio`, which is the three sources the app reads and none of them
    written down here.
    """

    def answer(match_id, listener, narrator=None):
        hero = matches[match_id]["hero"]
        slot = slot_rule(hero["voice_for"], listener, narrator)
        assert slot, (match_id, listener, narrator)
        frozen = narrations[str(match_id)]["slots"][slot]
        return {
            "slot": slot,
            "text": frozen["text"],
            "file": hero["audio"][slot],
        }

    return answer


@pytest.fixture(scope="session")
def web_server():
    """One server for the whole run, serving the working tree's `app/web/`."""
    running = local_server.serve(WEB)
    yield running
    running.shutdown()
    running.server_close()


@pytest.fixture
def plan(web_server):
    """The server's answering plan, emptied before and after each test."""
    web_server.plan.clear()
    yield web_server.plan
    web_server.plan.clear()


@pytest.fixture(scope="session")
def playwright_browser():
    """Headless Chromium, or a skip that says what is missing.

    Playwright is in the dev group, so `uv sync` installs the package; the
    browser itself is a separate download (`playwright install chromium`) and
    a machine without it should say so rather than fail as though the app were
    broken.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:   # pragma: no cover - only without the dev group
        pytest.skip("playwright is not installed; it is in the dev group")

    driver = sync_playwright().start()
    try:
        browser = driver.chromium.launch()
    except Exception as error:   # pragma: no cover - only without the browser
        driver.stop()
        pytest.skip(
            "chromium is not installed for playwright. Run "
            "'python -m playwright install chromium'. (%s)" % error
        )
    yield browser
    browser.close()
    driver.stop()


#: Records the file of every audio element a page builds, in order, so a test
#: can see which recording the player loaded without reaching into a closure.
#: A real element comes back, so the player behaves exactly as it does without
#: this, the Web Audio analyser included. Installed once per tab in `Fan`,
#: because adding it twice would wrap the wrapper and count every element
#: twice.
AUDIO_SHIM = """
window.__preludeAudio = [];
(function () {
  const Real = window.Audio;
  function Shim(src) {
    const element = src === undefined ? new Real() : new Real(src);
    window.__preludeAudio.push(element.getAttribute('src'));
    return element;
  }
  Shim.prototype = Real.prototype;
  window.Audio = Shim;
})();
"""


class Fan:
    """One browser context: one tab's worth of a fan, and its storage.

    A context is what a tab's storage belongs to, so closing one and opening
    another is a fan closing the tab and coming back: `sessionStorage` goes
    and `localStorage` stays. `reopen` is that, and it is how the narrator's
    outliving the tab is checked.
    """

    def __init__(self, browser, server):
        self.browser = browser
        self.server = server
        self.context = None
        self.page = None
        self.errors = []
        self.console = []
        self.requests_404 = []
        #: What the CDNs failed to answer, kept for a reader rather than
        #: asserted on.
        self.outside = []
        self.open()

    def open(self):
        self.context = self.browser.new_context(
            viewport=VIEWPORT, has_touch=True, is_mobile=True,
            device_scale_factor=3,
        )
        self.context.add_init_script(AUDIO_SHIM)
        self.page = self.context.new_page()
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        self.page.on("console", self.note_console)
        self.page.on("response", self.note_response)
        self.page.on(
            "requestfailed",
            lambda request: self.outside.append(request.url)
            if from_outside(request.url) else None,
        )

    def reopen(self):
        """Close the tab and open a new one, keeping what localStorage holds."""
        state = self.context.storage_state()
        self.context.close()
        self.context = self.browser.new_context(
            viewport=VIEWPORT, has_touch=True, is_mobile=True,
            device_scale_factor=3, storage_state=state,
        )
        self.context.add_init_script(AUDIO_SHIM)
        self.page = self.context.new_page()
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))
        return self.page

    def goto(self, screen, **query):
        self.page.goto(self.server.url(screen, **query), wait_until="commit")
        return self.page

    def visit(self, screen, **query):
        """Open a screen and wait for the match to be rendered."""
        self.goto(screen, **query)
        self.page.wait_for_function(RENDERED)
        return self.page

    def remember(self, match_id=None, listener=None, name=None, narrator=None):
        """Write the fan's answers, from a page on the server's own origin.

        The picker is the page used for it, because it needs no match and
        renders nothing, so nothing is painted on the way past.
        """
        self.goto(PICKER)
        self.page.wait_for_load_state("domcontentloaded")
        self.page.evaluate(
            """([matchId, listener, name, narrator]) => {
                 if (listener) {
                   sessionStorage.setItem('prelude.listener.' + matchId, listener);
                 }
                 if (name) sessionStorage.setItem('prelude.name', name);
                 if (narrator) localStorage.setItem('prelude.narrator', narrator);
               }""",
            [match_id, listener, name, narrator],
        )
        return self

    def note_console(self, message):
        if message.type != "error":
            return
        if from_outside(message.text):
            self.outside.append(message.text)
            return
        self.console.append((message.type, message.text))

    def note_response(self, response):
        if response.status != 404:
            return
        if from_outside(response.url):
            self.outside.append(response.url)
            return
        self.requests_404.append(response.url)

    def audio_loaded(self):
        """The files the page's audio elements were built with, in order."""
        return self.page.evaluate("() => window.__preludeAudio")

    def unexpected_404s(self):
        return [url for url in self.requests_404 if EXPECTED_404 not in url]

    def close(self):
        self.context.close()


@pytest.fixture
def fan(playwright_browser, web_server, plan):
    """A fan with nothing stored. `plan` is asked for so it is cleared first."""
    one = Fan(playwright_browser, web_server)
    yield one
    one.close()


# The card's two elements, read together, because the rule they are held to is
# about the two of them at once.
CARD_STATE = """() => {
  const words = document.querySelector('[data-field="hero_narration"]');
  const label = document.querySelector('[data-field="hero_label"]');
  const block = document.querySelector('[data-field="hero_narration_block"]');
  const play = document.getElementById('playBtn');
  return {
    text: words ? words.textContent : null,
    wordsShown: words ? getComputedStyle(words).display !== 'none' : false,
    labelShown: label ? getComputedStyle(label).display !== 'none' : false,
    blockHeight: block ? Math.round(block.getBoundingClientRect().height) : null,
    playDisabled: play ? play.disabled : null,
    header: (document.querySelector('[data-field="hero_header"]') || {}).textContent,
  };
}"""

#: Installed before any of the page's own scripts run, so every state the card
#: passes through is recorded rather than sampled. Task 29 found the states
#: that matter are the ones between two frames.
WATCH_THE_CARD = """
window.__preludeFrames = [];
(function () {
  function read() {
    const words = document.querySelector('[data-field="hero_narration"]');
    const label = document.querySelector('[data-field="hero_label"]');
    const play = document.getElementById('playBtn');
    if (!words) return;
    window.__preludeFrames.push({
      text: words.textContent,
      wordsShown: getComputedStyle(words).display !== 'none',
      labelShown: label ? getComputedStyle(label).display !== 'none' : false,
      playDisabled: play ? play.disabled : null,
    });
  }
  const observer = new MutationObserver(read);
  document.addEventListener('DOMContentLoaded', function () {
    read();
    observer.observe(document.documentElement, {
      subtree: true, childList: true, characterData: true,
      attributes: true, attributeFilter: ['style', 'disabled'],
    });
  });
})();
"""
