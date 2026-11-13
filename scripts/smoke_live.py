"""Check the deployed site and the hosted API, after a deploy.

The suite in `tests/browser/` drives the working tree over a local server. It
cannot say that what a judge opens is the same app: the deploy stamps a version
into every local asset URL, GitHub Pages serves from its own cache, and the API
runs somewhere else entirely. This is the short subset that answers that, and
`.github/workflows/smoke.yml` runs it when a Pages deploy succeeds.

What it asks of the site, for both matches:

- the screens are the new version, which is the deploy's own commit stamped
  into `match-content.js?v=` and the rest,
- the moment card shows the frozen narration for this listener's slot, under
  the grounding label, and the play button is enabled with the recording that
  reads those words,
- and under two seconds of latency the card shows no narration, no label and
  no offer of the voice.

The latency is set through the DevTools protocol rather than in a route
handler. `tests/browser/server.py` records why: a sleep inside the driver
blocks its own event loop, so the page is read after it has moved on. There is
no server to slow here, so the browser's own network emulation is what is left.

What it asks of the API: `/health`, `/moments` and `/buildup` answer, and the
narration `/buildup` returns is the one `app/web/narrations.json` holds for
that slot. Render spins the free service down after fifteen minutes, so the
first call waits through a cold wake; `HANDOFF.md` records 82 seconds on the
keepalive run of 2026-11-07, and the wait here is ninety.

Nothing here is a test: it reaches the network, and `tests/conftest.py` blocks
that for every test in the suite. Run it by hand the same way the workflow
does:

    .\\.venv-prelude\\Scripts\\python.exe scripts\\smoke_live.py --version abc1234
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"

sys.path.insert(0, str(ROOT))

from app.api import slot_for   # noqa: E402

SITE = "https://sh4wnbk.github.io/prelude/"
API = "https://prelude-api.onrender.com"

#: One listener per match, chosen so the two are not the same slot: the 1986
#: fan is with England and hears the goal conceded, the 2022 fan is with
#: Argentina and hears it scored.
LISTENERS = {3750191: "team_b", 3869685: "team_a"}

#: The phone the screens are designed for.
VIEWPORT = {"width": 390, "height": 844}

#: Two seconds, which is what Task 29 read the card at and what the suite's
#: own slow state uses.
LATENCY_MS = 2000

#: Written to answer false rather than throw. `wait_for_function` tries a
#: false predicate again on the next frame and gives up at once on one that
#: throws, and this runs while the page may still be navigating, where the
#: button is not there yet. The browser suite learned the same thing on its
#: first CI run.
PLAY_OFFERED = (
    "() => { const b = document.getElementById('playBtn'); "
    "return !!b && !b.disabled; }"
)

#: How long a cold Render service may take to answer. A wake took 82 seconds
#: on 2026-11-07.
COLD_WAKE_SECONDS = 90


class Failed(Exception):
    """A check that did not hold. The message is what to print."""


def load(name):
    return json.loads((WEB / name).read_text(encoding="utf-8"))


def expected(match_id, listener, narrator=None):
    """The slot, the words and the file, from the three files the app reads."""
    hero = {entry["match_id"]: entry for entry in load("matches.json")["matches"]}
    hero = hero[match_id]["hero"]
    slot = slot_for(hero["voice_for"], listener, narrator)
    frozen = load("narrations.json")["narrations"][str(match_id)]["slots"][slot]
    return slot, frozen["text"], hero["audio"][slot]


def say(ok, line):
    print(("  ok   " if ok else "  FAIL ") + line)
    return ok


def fetch(url, timeout=30):
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as answer:
        return answer.status, answer.read().decode("utf-8")


# ---------------------------------------------------------------- the site

def check_site(site, version):
    """Returns the number of failures."""
    from playwright.sync_api import sync_playwright

    base = site.rstrip("/")
    bad = 0
    print("the deployed site: " + base)

    with sync_playwright() as driver:
        browser = driver.chromium.launch()
        try:
            for match_id, listener in sorted(LISTENERS.items()):
                bad += check_one_match(browser, base, match_id, listener, version)
        finally:
            browser.close()
    return bad


def open_card(browser, base, match_id, listener, latency=0):
    """A context on the site with this listener stored, on the moment card."""
    context = browser.new_context(
        viewport=VIEWPORT, has_touch=True, is_mobile=True, device_scale_factor=3
    )
    context.add_init_script(AUDIO_SHIM)
    page = context.new_page()
    page.goto(base + "/prelude_01_picker.html", wait_until="domcontentloaded")
    page.evaluate(
        "([match, side]) => sessionStorage.setItem('prelude.listener.' + match, side)",
        [match_id, listener],
    )
    if latency:
        client = context.new_cdp_session(page)
        client.send("Network.enable")
        client.send(
            "Network.emulateNetworkConditions",
            {
                "offline": False,
                "latency": latency,
                "downloadThroughput": -1,
                "uploadThroughput": -1,
            },
        )
    page.goto(
        "%s/prelude_03_moment_card.html?match=%d" % (base, match_id),
        wait_until="commit",
    )
    return context, page


#: The player builds its audio element and never puts it in the document, so
#: the file it loaded cannot be read off the page. This records every element
#: as it is built, exactly as `tests/browser/conftest.py` does, and hands back
#: a real one.
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

CARD = """() => {
  const words = document.querySelector('[data-field=hero_narration]');
  const label = document.querySelector('[data-field=hero_label]');
  const play = document.getElementById('playBtn');
  return {
    text: words ? words.textContent : null,
    wordsShown: words ? getComputedStyle(words).display !== 'none' : null,
    labelShown: label ? getComputedStyle(label).display !== 'none' : null,
    playDisabled: play ? play.disabled : null,
    version: (document.querySelector('script[src*="match-content.js"]') || {}).src,
  };
}"""


def check_one_match(browser, base, match_id, listener, version):
    slot, text, file = expected(match_id, listener)
    print("  match %d, a fan with %s, slot %s" % (match_id, listener, slot))
    bad = 0

    context, page = open_card(browser, base, match_id, listener)
    try:
        page.wait_for_function(PLAY_OFFERED, timeout=30000)
        state = page.evaluate(CARD)
        bad += not say(state["text"] == text, "the card shows this slot's words")
        bad += not say(state["labelShown"] is True, "the label is over them")
        bad += not say(state["playDisabled"] is False, "the play button is offered")
        loaded = page.evaluate("() => window.__preludeAudio")
        bad += not say(loaded == [file], "the player loaded " + file)
        served = (state["version"] or "").split("?v=")[-1]
        if version:
            bad += not say(
                ("?v=" + version) in (state["version"] or ""),
                "the screens are version %s (serving %s)" % (version, served),
            )
        else:
            say(True, "the screens are serving version " + served)
    except Exception as error:
        bad += not say(False, "the card did not settle: %s" % error)
    finally:
        context.close()

    # And the same card with two seconds of latency, read while the fetch is
    # still in the air.
    context, page = open_card(browser, base, match_id, listener, latency=LATENCY_MS)
    try:
        page.wait_for_selector("#playBtn", timeout=30000)
        slow = page.evaluate(CARD)
        bad += not say(slow["text"] == "", "under latency the paragraph is empty")
        bad += not say(slow["labelShown"] is False, "under latency there is no label")
        bad += not say(
            slow["playDisabled"] is True, "under latency the voice is not offered"
        )
    except Exception as error:
        bad += not say(False, "the throttled load did not paint: %s" % error)
    finally:
        context.close()
    return bad


# ----------------------------------------------------------------- the API

def wake(api):
    """`/health` answering ok, waiting through a cold start."""
    deadline = time.time() + COLD_WAKE_SECONDS
    last = None
    while time.time() < deadline:
        try:
            status, body = fetch(api + "/health", timeout=30)
            if status == 200 and json.loads(body).get("status") == "ok":
                return json.loads(body)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as error:
            last = error
        time.sleep(5)
    raise Failed("/health did not answer ok within %ds (%s)" % (COLD_WAKE_SECONDS, last))


def check_api(api):
    base = api.rstrip("/")
    bad = 0
    print("the hosted API: " + base)
    try:
        health = wake(base)
    except Failed as error:
        return not say(False, str(error))
    say(True, "/health is awake: " + json.dumps(health))

    for match_id, listener in sorted(LISTENERS.items()):
        slot, text, _file = expected(match_id, listener)
        try:
            status, body = fetch("%s/moments?match=%d" % (base, match_id))
            moments = json.loads(body)
            narrated = [goal for goal in moments["goals"] if goal["narrated"]]
            bad += not say(status == 200, "/moments?match=%d answered" % match_id)
            bad += not say(
                len(narrated) == 1,
                "/moments names one narrated goal of %d" % len(moments["goals"]),
            )
        except Exception as error:
            bad += not say(False, "/moments?match=%d: %s" % (match_id, error))

        try:
            status, body = fetch(
                "%s/buildup?match=%d&listener=%s" % (base, match_id, listener)
            )
            buildup = json.loads(body)
            bad += not say(status == 200, "/buildup?match=%d answered" % match_id)
            bad += not say(buildup.get("slot") == slot, "/buildup is slot " + slot)
            bad += not say(
                buildup.get("text") == text, "/buildup carries the frozen words"
            )
            bad += not say(
                buildup.get("audio_url", "").endswith(_file),
                "/buildup names the recording that reads them",
            )
        except Exception as error:
            bad += not say(False, "/buildup?match=%d: %s" % (match_id, error))
    return bad


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--site", default=SITE, help="the deployed site")
    parser.add_argument("--api", default=API, help="the hosted API")
    parser.add_argument(
        "--version", default=None,
        help=("the seven character commit the deploy stamped into the assets. "
              "Left out, the version the site is serving is reported rather "
              "than held to anything, which is what a run that did not follow "
              "a deploy can honestly say"),
    )
    parser.add_argument("--skip-site", action="store_true")
    parser.add_argument("--skip-api", action="store_true")
    args = parser.parse_args(argv)

    bad = 0
    if not args.skip_site:
        bad += check_site(args.site, args.version or None)
    if not args.skip_api:
        bad += check_api(args.api)

    print()
    if bad:
        print("%d check(s) failed." % bad)
        return 1
    print("every check held.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
