"""The launch screen: the mark and the tagline, on every load of the shell.

`app/web/index.html` is the shell every visit opens on, and it paints the mark
over the tagline while the event list loads behind it. What it has to be true
about:

- **It is the first frame, not a frame later.** The markup ships visible and
  the mark is inline, so it is up before any script has run and before any
  request of its own has been answered. `CLAUDE.md` counts the frames before
  any script has run as a state a fan can see.
- **It is the brand's mark**, the paths out of
  `app/web/assets/brand/prelude_mark.svg`, with the tagline under it as real
  text in Hanken Grotesk rather than as part of the picture.
- **It goes when the list is ready**, which is `data-matches-loaded` on the
  framed document: matches.json was answered. It is not
  `data-match-rendered`, which the list never sets, because Prelude renders no
  match until the fan has picked one.
- **It costs no waiting the list did not already cost.** From the list being
  ready to the screen being gone is the fade and nothing else, well inside a
  second.
- **It never outlives its cap.** A matches.json that fails or never answers
  would otherwise leave a fan looking at a mark; the list behind it has its
  own inline copy for exactly that case.
- **Every full load paints it**, a reload in the same tab included. It used to
  paint once per tab, out of `sessionStorage`, which made the mark something a
  fan saw once and could not get back to.
- **It honours `prefers-reduced-motion`** by not fading, and it is announced
  as the mark and the tagline together and says nothing else.
"""

import pytest

SHELL = "index.html"

#: The tagline, as the brand file draws it and the shell writes it.
TAGLINE = "Leave your seat. Stay in the game."

#: Long enough to read the screen while matches.json is still in the air.
SLOW_SECONDS = 1.5

#: What the shell's own script allows itself, from `LAUNCH_CAP_MS`.
CAP_MS = 2000

#: Installed before any of the page's own scripts, so what is recorded is
#: every state the launch screen passed through rather than the one it was
#: sampled in. The same method `tests/browser/test_the_label_waits.py` uses.
WATCH = """
window.__launchFrames = [];
(function () {
  function read() {
    // Every step answers rather than throwing: this runs before the document
    // element exists, and a page error here would be counted against the
    // screen. Task 30 found the same thing in a wait predicate.
    const root = document.documentElement;
    const el = root ? document.getElementById('launch') : null;
    window.__launchFrames.push({
      present: !!el,
      shown: el ? (getComputedStyle(el).display !== 'none' && !el.hidden) : false,
      going: el ? el.hasAttribute('data-going') : false,
      marked: !!(el && el.querySelector('#launch-mark path')),
    });
  }
  read();
  const observer = new MutationObserver(read);
  document.addEventListener('DOMContentLoaded', function () {
    read();
    observer.observe(document.documentElement, {
      subtree: true, childList: true,
      attributes: true, attributeFilter: ['class', 'hidden', 'data-going'],
    });
  });
})();
"""

STATE = """() => {
  const el = document.getElementById('launch');
  const mark = document.getElementById('launch-mark');
  const line = document.getElementById('launch-line');
  const frame = document.getElementById('screen');
  return {
    present: !!el,
    shown: el ? (getComputedStyle(el).display !== 'none' && !el.hidden) : false,
    hidden: el ? el.hidden : null,
    going: el ? el.hasAttribute('data-going') : null,
    role: el ? el.getAttribute('role') : null,
    label: el ? el.getAttribute('aria-label') : null,
    transition: el ? getComputedStyle(el).transitionDuration : null,
    markIsSvg: !!mark && mark.tagName.toLowerCase() === 'svg',
    markHidden: mark ? mark.getAttribute('aria-hidden') : null,
    markFills: mark
      ? Array.from(mark.querySelectorAll('path')).map(p => p.getAttribute('fill'))
      : null,
    markWidth: mark ? Math.round(mark.getBoundingClientRect().width) : null,
    markHeight: mark ? Math.round(mark.getBoundingClientRect().height) : null,
    line: line ? line.textContent : null,
    lineColour: line ? getComputedStyle(line).color : null,
    lineFamily: line ? getComputedStyle(line).fontFamily : null,
    lineSize: line ? getComputedStyle(line).fontSize : null,
    gap: (mark && line)
      ? Math.round(line.getBoundingClientRect().top
                   - mark.getBoundingClientRect().bottom)
      : null,
    framed: frame ? frame.getAttribute('src') : null,
  };
}"""

GONE = (
    "() => { const el = document.getElementById('launch'); "
    "return !!el && el.hidden; }"
)

LIST_READY = """() => {
  const frame = document.getElementById('screen');
  try {
    const doc = frame && frame.contentDocument;
    return !!doc && !!doc.documentElement &&
           doc.documentElement.hasAttribute('data-matches-loaded');
  } catch (e) { return false; }
}"""


def open_shell(fan, watch=True):
    if watch:
        fan.page.add_init_script(WATCH)
    fan.page.goto(fan.server.url(SHELL), wait_until="commit")
    return fan.page


def frames(fan):
    return fan.page.evaluate("() => window.__launchFrames || []")


def test_it_is_up_in_the_first_frame_of_a_visit(fan, plan):
    """Held still by delaying matches.json, so the screen can be read rather
    than raced."""
    plan.delay["matches.json"] = SLOW_SECONDS
    page = open_shell(fan)
    page.wait_for_selector("#launch", state="visible")
    state = page.evaluate(STATE)
    assert state["shown"] is True, state
    assert state["going"] is False, state
    # The mark is inline, so it is drawn in that first frame rather than
    # fetched: every frame the observer recorded has its paths in it.
    recorded = frames(fan)
    assert recorded, "the observer recorded nothing"
    assert all(one["marked"] for one in recorded if one["present"]), recorded


def test_it_says_the_mark_and_the_tagline_and_nothing_else_to_a_reader(fan, plan):
    plan.delay["matches.json"] = SLOW_SECONDS
    page = open_shell(fan)
    page.wait_for_selector("#launch", state="visible")
    state = page.evaluate(STATE)
    # One image, named. The mark and the tagline are one thing seen, not two
    # things read out, so the mark itself is hidden from a reader.
    assert state["role"] == "img", state
    assert state["label"] == "Prelude. " + TAGLINE, state
    assert state["markIsSvg"] is True, state
    assert state["markHidden"] == "true", state
    assert state["line"] == TAGLINE, state


def test_the_mark_is_drawn_and_the_tagline_is_text(fan, plan):
    """The tagline is real text in Hanken Grotesk, not part of the picture:
    it is the one line here a fan could select, and a drawn one would be the
    wrong size on a screen the brand file was not measured at."""
    plan.delay["matches.json"] = SLOW_SECONDS
    page = open_shell(fan)
    page.wait_for_selector("#launch", state="visible")
    state = page.evaluate(STATE)
    assert state["markFills"] == ["#FFFFFF", "#FFB703"], state
    assert state["lineColour"] == "rgb(255, 183, 3)", state     # primary-container
    assert "Hanken Grotesk" in state["lineFamily"], state
    assert state["lineSize"] == "16px", state


def test_it_is_laid_out_the_way_the_brand_file_is(fan, plan):
    """`app/web/assets/brand/prelude_launch.svg` is 390 by 844 with the mark
    300 wide and 20 px of air under it. These are the same numbers, measured
    in the browser rather than read off the file."""
    plan.delay["matches.json"] = SLOW_SECONDS
    page = open_shell(fan)
    page.wait_for_selector("#launch", state="visible")
    state = page.evaluate(STATE)
    assert state["markWidth"] == 300, state
    assert state["markHeight"] == 32, state      # 300 * 705 / 6583.8
    assert state["gap"] == 20, state


def test_it_goes_when_the_list_is_ready_and_costs_no_more_than_the_fade(fan, plan):
    """The measurement Shawn asked for: from the list being ready to the
    screen being gone."""
    plan.delay["matches.json"] = SLOW_SECONDS
    page = open_shell(fan)
    page.wait_for_selector("#launch", state="visible")
    page.wait_for_function(LIST_READY, timeout=(SLOW_SECONDS + 8) * 1000)
    took = page.evaluate(
        """() => new Promise(resolve => {
             const started = performance.now();
             const el = document.getElementById('launch');
             if (el.hidden) { resolve(0); return; }
             const tick = setInterval(() => {
               if (el.hidden) {
                 clearInterval(tick);
                 resolve(performance.now() - started);
               }
             }, 10);
           })"""
    )
    assert took < 1000, "the launch screen added %.0f ms after the list was ready" % took
    assert page.evaluate(STATE)["shown"] is False


def test_it_never_outlives_its_cap_when_the_list_fails(fan, plan):
    """matches.json refused. The list falls back to its inline copy, which is
    a correct screen, and the launch screen has to get out of its way."""
    plan.status["matches.json"] = 503
    page = open_shell(fan)
    page.wait_for_selector("#launch", state="visible")
    page.wait_for_function(GONE, timeout=CAP_MS + 4000)
    assert page.evaluate(STATE)["shown"] is False
    assert not fan.errors, fan.errors


def test_it_never_outlives_its_cap_when_the_list_never_answers(fan, plan):
    plan.hang.add("matches.json")
    page = open_shell(fan)
    page.wait_for_selector("#launch", state="visible")
    page.wait_for_function(GONE, timeout=CAP_MS + 4000)
    assert page.evaluate(STATE)["shown"] is False


def test_a_second_load_in_the_same_tab_paints_it_again(fan, plan):
    """A reload is a full load. Nothing is read out of storage to decide it,
    so there is no state a cleared, blocked or full storage could change."""
    plan.delay["matches.json"] = SLOW_SECONDS
    page = open_shell(fan)
    page.wait_for_function(GONE, timeout=(SLOW_SECONDS + 8) * 1000)

    page.add_init_script(WATCH)
    page.goto(fan.server.url(SHELL), wait_until="commit")
    page.wait_for_selector("#launch", state="visible")
    assert page.evaluate(STATE)["shown"] is True
    page.wait_for_function(GONE, timeout=(SLOW_SECONDS + 8) * 1000)


def test_the_shell_stores_nothing_about_having_been_launched(fan, plan):
    """The key the old behaviour hung on. A fan who saw the mark once is not
    a fan the app remembers."""
    plan.delay["matches.json"] = SLOW_SECONDS
    page = open_shell(fan)
    page.wait_for_function(GONE, timeout=(SLOW_SECONDS + 8) * 1000)
    stored = page.evaluate(
        """() => {
             const keys = [];
             for (let i = 0; i < sessionStorage.length; i++) {
               keys.push(sessionStorage.key(i));
             }
             return keys;
           }"""
    )
    assert not [one for one in stored if "launch" in one], stored


def test_a_new_tab_paints_it_too(fan, plan):
    plan.delay["matches.json"] = SLOW_SECONDS
    page = open_shell(fan)
    page.wait_for_function(GONE, timeout=(SLOW_SECONDS + 8) * 1000)

    page = fan.reopen()
    page.add_init_script(WATCH)
    page.goto(fan.server.url(SHELL), wait_until="commit")
    page.wait_for_selector("#launch", state="visible")
    assert page.evaluate(STATE)["shown"] is True


@pytest.mark.parametrize("motion", ["reduce", "no-preference"])
def test_it_honours_a_request_for_less_motion(playwright_browser, web_server,
                                              plan, motion):
    """With `reduce` it is shown and then it is not: no fade, so the state in
    between never exists."""
    plan.delay["matches.json"] = SLOW_SECONDS
    context = playwright_browser.new_context(
        viewport={"width": 390, "height": 844}, reduced_motion=motion,
    )
    page = context.new_page()
    try:
        page.add_init_script(WATCH)
        page.goto(web_server.url(SHELL), wait_until="commit")
        page.wait_for_selector("#launch", state="visible")
        if motion == "reduce":
            assert page.evaluate(STATE)["transition"] == "0s"
        else:
            assert page.evaluate(STATE)["transition"] != "0s"
        page.wait_for_function(GONE, timeout=(SLOW_SECONDS + 8) * 1000)
        recorded = page.evaluate("() => window.__launchFrames || []")
        faded = [one for one in recorded if one["going"]]
        if motion == "reduce":
            assert not faded, faded
        else:
            assert faded, recorded
    finally:
        context.close()


def test_the_list_is_reachable_the_moment_it_is_gone(fan, plan):
    """The point of the cover: the picker loads behind it, so there is nothing
    left to wait for."""
    plan.delay["matches.json"] = SLOW_SECONDS
    page = open_shell(fan)
    page.wait_for_function(GONE, timeout=(SLOW_SECONDS + 8) * 1000)
    assert page.evaluate(LIST_READY) is True
    cards = page.evaluate(
        """() => {
             const doc = document.getElementById('screen').contentDocument;
             return doc.querySelectorAll('.event-card').length;
           }"""
    )
    assert cards == 2, cards
    assert not fan.errors, fan.errors
