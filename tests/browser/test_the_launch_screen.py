"""The launch screen: the first frame of a visit, and then never again.

`app/web/index.html` is the shell every visit opens on, and it now paints the
wordmark and the line over the frame while the event list loads behind it.
What it has to be true about:

- **It is the first frame, not a frame later.** Whether it paints at all is
  decided in the head, before the body is parsed, by a class on `<html>`. A
  decision made in the body would be a flash of one state before the other,
  and `CLAUDE.md` counts the frames before any script has run as a state a fan
  can see.
- **It goes when the list is ready**, which is `data-matches-loaded` on the
  framed document: matches.json was answered. It is not
  `data-match-rendered`, which the list never sets, because Prelude renders no
  match until the fan has picked one.
- **It costs no waiting the list did not already cost.** From the list being
  ready to the screen being gone is the fade and nothing else, well inside a
  second.
- **It never outlives its cap.** A matches.json that fails or never answers
  would otherwise leave a fan looking at a wordmark; the list behind it has
  its own inline copy for exactly that case.
- **First load of a visit only.** A reload in the same tab does not paint it.
  A new tab is a new visit and does.
- **It honours `prefers-reduced-motion`** by not fading, and it is announced
  as Prelude and says nothing else.
"""

import pytest

SHELL = "index.html"

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
      launched: !!root && String(root.className).indexOf('launched') >= 0,
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
    mark: mark ? mark.textContent : null,
    stopColour: document.getElementById('launch-stop')
      ? getComputedStyle(document.getElementById('launch-stop')).color : null,
    markColour: mark ? getComputedStyle(mark).color : null,
    line: line ? line.textContent : null,
    lineColour: line ? getComputedStyle(line).color : null,
    launched: document.documentElement.className.indexOf('launched') >= 0,
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
    assert state["launched"] is False, state
    assert state["going"] is False, state


def test_it_says_prelude_and_nothing_else_to_a_reader(fan, plan):
    plan.delay["matches.json"] = SLOW_SECONDS
    page = open_shell(fan)
    page.wait_for_selector("#launch", state="visible")
    state = page.evaluate(STATE)
    # One image, named. The wordmark and the line are one thing seen, not two
    # things read out.
    assert state["role"] == "img", state
    assert state["label"] == "Prelude", state
    assert state["mark"] == "Prelude.", state
    assert state["line"] == "Be there. Even when you're not.", state


def test_the_full_stop_is_amber_and_the_word_is_not(fan, plan):
    plan.delay["matches.json"] = SLOW_SECONDS
    page = open_shell(fan)
    page.wait_for_selector("#launch", state="visible")
    state = page.evaluate(STATE)
    assert state["stopColour"] == "rgb(255, 183, 3)", state     # primary-container
    assert state["markColour"] == "rgb(225, 226, 234)", state   # on-surface
    assert state["lineColour"] == "rgb(255, 183, 3)", state


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


def test_a_second_load_in_the_same_tab_never_paints_it(fan, plan):
    """Not "shows it and hides it": every frame a `MutationObserver` recorded
    has it hidden, because the class is set in the head before the element is
    parsed."""
    plan.delay["matches.json"] = SLOW_SECONDS
    page = open_shell(fan)
    page.wait_for_function(GONE, timeout=(SLOW_SECONDS + 8) * 1000)

    page.add_init_script(WATCH)
    page.goto(fan.server.url(SHELL), wait_until="commit")
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(300)
    state = page.evaluate(STATE)
    assert state["launched"] is True, state
    assert state["shown"] is False, state
    recorded = frames(fan)
    assert recorded, "the observer recorded nothing"
    assert all(not one["shown"] for one in recorded), recorded


def test_a_new_tab_is_a_new_visit(fan, plan):
    """The flag is `sessionStorage`, so a closed and reopened tab starts
    over, which is what "first load of a visit" means."""
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
