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
- **It is held, and then it fades.** The hold is 1.5 seconds on every full
  load, so the same screen is not a flicker on a fast load and a launch
  screen on a slow one; then it fades over 300 ms. Settled on 2026-11-15.
- **It costs no waiting the list did not already cost.** With the list
  answered after the hold has been served, from the list being ready to the
  screen being gone is the fade and nothing else.
- **It never outlives its cap.** A matches.json that fails or never answers
  would otherwise leave a fan looking at a mark; the list behind it has its
  own inline copy for exactly that case. The cap is the last moment a fan can
  see it and not the moment the fade starts, so the shell begins the fade a
  fade's length before it.
- **Every full load paints it**, a reload in the same tab included. It used to
  paint once per tab, out of `sessionStorage`, which made the mark something a
  fan saw once and could not get back to.
- **It crossfades with the list.** The mark fades out over 300 ms while the
  list fades in over the same 300 ms, both opacity and nothing else, and the
  list is revealed in the step that starts the fade rather than before it: a
  list already up behind a fading mark is a fade and not a crossfade.
- **The list is never visible before it has painted**, which is
  `data-painted` on the framed document: one frame drawn with the app
  background and its own stylesheet applied. A browser paints an empty frame
  white.
- **A request for less motion keeps the fade.** An opacity fade is not
  motion, and nothing on either screen moves; what `reduce` used to get was
  a hard cut, which is the one thing in the sequence that reads as a jolt.
- **It is announced** as the mark and the tagline together and says nothing
  else.
- **The startup image iOS shows is this screen.** A web app opened from the
  home screen shows `apple-touch-startup-image` while it starts, before any
  of this markup has run, so the drawing in that file and the drawing the CSS
  paints have to be the same one or the mark moves as the app takes over.
"""

import importlib.util
import io
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
WEB = ROOT / "app" / "web"
BRAND_SCRIPT = ROOT / "scripts" / "brand" / "build_svg.py"


def brand():
    """`scripts/brand/build_svg.py`, imported for its own device table.

    The eleven screens and the name of each one's file are read out of the
    script that draws them rather than written down here, so a screen added
    to `IPHONES` arrives in this comparison with it.
    """
    spec = importlib.util.spec_from_file_location("build_svg", BRAND_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


#: Chrome on Android draws its own launch screen out of the manifest and then
#: hands the page over, so this page's own launch screen and crossfade have to
#: behave there too. A Pixel-sized viewport, which is not in `IPHONES` and is
#: not a screen a startup image is drawn for.
ANDROID = (412, 915, 3)

SHELL = "index.html"

#: The tagline, as the brand file draws it and the shell writes it.
TAGLINE = "Leave your seat. Stay in the game."

#: Long enough to read the screen while matches.json is still in the air.
SLOW_SECONDS = 1.5

#: The shell's own three numbers, from `MIN_HOLD_MS`, `FADE_MS` and `CAP_MS`.
#: The hold is measured from the start of the navigation, which is what
#: `performance.now()` counts from, so a frame's timestamp is comparable with
#: it directly.
MIN_HOLD_MS = 1500
FADE_MS = 300
CAP_MS = 2500

#: matches.json answered after the hold has been served, so that what is
#: measured from the list being ready is the fade and nothing left of the
#: hold. It is inside the cap, so the list and not the cap is what releases
#: the screen.
AFTER_THE_HOLD_SECONDS = 1.9

#: A `setTimeout` is a floor and not a ceiling: the browser runs it no earlier
#: than asked and no promise about later, and a loaded runner is later. So the
#: cap is asserted with the runner's own scheduling allowed for, and the
#: measurement that matters underneath it is that the screen is gone long
#: before a fan would wonder.
SLACK_MS = 600

#: How far apart the shell's painting of the launch screen and the startup
#: image drawn for the same screen may be, in device pixels. Measured at 1 for
#: the mark and 3 for the tagline on 2026-11-15; the allowance is what a
#: different rasteriser's idea of the faintest edge is worth, not room for the
#: layout to move. Four device pixels is 1.3 CSS pixels.
SAME_DRAWING_PX = 4

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
    const frame = root ? document.getElementById('screen') : null;
    let painted = false;
    try {
      const doc = frame && frame.contentDocument;
      painted = !!doc && !!doc.documentElement &&
                doc.documentElement.hasAttribute('data-painted');
    } catch (e) { painted = false; }
    window.__launchFrames.push({
      // Milliseconds since the navigation started, which is the clock the
      // shell's own hold and cap are measured on.
      at: performance.now(),
      present: !!el,
      shown: el ? (getComputedStyle(el).display !== 'none' && !el.hidden) : false,
      going: el ? el.hasAttribute('data-going') : false,
      marked: !!(el && el.querySelector('#launch-mark path')),
      // The list behind it: whether it has been revealed, and whether it had
      // painted by the time it was. The second is the rule, asked of every
      // frame rather than of the state the shell settled in.
      listShown: frame ? frame.hasAttribute('data-shown') : false,
      listOpacity: frame ? Number(getComputedStyle(frame).opacity) : null,
      listPainted: painted,
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
    listTransition: frame ? getComputedStyle(frame).transitionDuration : null,
    listShown: frame ? frame.hasAttribute('data-shown') : null,
    listOpacity: frame ? Number(getComputedStyle(frame).opacity) : null,
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

#: The list at full opacity. Waited for rather than asserted on the frame the
#: mark was hidden in: the mark is hidden by a `setTimeout` at FADE_MS and the
#: list's own transition of the same length can still be a thousandth short of
#: settled in that frame. Measured on 2026-11-15: 0.992923 at 412 by 915.
LIST_UP = (
    "() => { const f = document.getElementById('screen'); "
    "return !!f && Number(getComputedStyle(f).opacity) === 1; }"
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


def recorded(page):
    return page.evaluate("() => window.__launchFrames || []")


def first(timeline, **wanted):
    """When the first recorded frame matching `wanted` happened, or None.

    The timeline is what the `MutationObserver` recorded, so this reads the
    moment a state was entered rather than sampling the state the screen
    settled in. `CLAUDE.md` asks the rules of every frame a fan could see.
    """
    for one in timeline:
        if all(one.get(key) == value for key, value in wanted.items()):
            return one["at"]
    return None


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


def test_the_fade_is_the_one_the_shell_says_it_is(fan, plan):
    """The stylesheet and the script carry the same number, and the script's
    cap arithmetic is written against it, so the two cannot be read apart."""
    plan.delay["matches.json"] = SLOW_SECONDS
    page = open_shell(fan)
    page.wait_for_selector("#launch", state="visible")
    assert page.evaluate(STATE)["transition"] == "%gs" % (FADE_MS / 1000)


def test_it_is_held_for_the_hold_even_when_the_list_is_ready_at_once(fan, plan):
    """No delay at all: matches.json is answered off a local server while the
    shell is still parsing. The mark is still on screen for the hold.

    This is the case the hold was added for. Before it, a fast load painted
    the mark and took it away inside a couple of hundred milliseconds, which
    reads as something going wrong rather than as the app opening.
    """
    page = open_shell(fan)
    page.wait_for_function(GONE, timeout=CAP_MS + 4000)
    timeline = recorded(page)
    faded = first(timeline, going=True)
    gone = first(timeline, present=True, shown=False)
    assert faded is not None, timeline
    assert gone is not None, timeline
    assert faded >= MIN_HOLD_MS, (faded, timeline)
    assert gone >= MIN_HOLD_MS + FADE_MS, (gone, timeline)
    assert gone <= CAP_MS + SLACK_MS, (gone, timeline)


def test_the_hold_is_served_before_the_fade_however_slow_the_list_is(fan, plan):
    """The other side of the same rule: a list that lands inside the hold does
    not shorten it, and one that lands after it does not extend it past the
    fade."""
    plan.delay["matches.json"] = SLOW_SECONDS
    page = open_shell(fan)
    page.wait_for_function(GONE, timeout=(SLOW_SECONDS + 8) * 1000)
    timeline = recorded(page)
    faded = first(timeline, going=True)
    assert faded >= MIN_HOLD_MS, (faded, timeline)
    assert faded <= CAP_MS - FADE_MS + SLACK_MS, (faded, timeline)


def test_it_goes_when_the_list_is_ready_and_costs_no_more_than_the_fade(fan, plan):
    """The measurement Shawn asked for: from the list being ready to the
    screen being gone. The list is answered after the hold has been served,
    so what is left to measure is the fade."""
    plan.delay["matches.json"] = AFTER_THE_HOLD_SECONDS
    page = open_shell(fan)
    page.wait_for_selector("#launch", state="visible")
    page.wait_for_function(LIST_READY,
                           timeout=(AFTER_THE_HOLD_SECONDS + 8) * 1000)
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
    a correct screen, and the launch screen has to get out of its way.

    The cap is the last moment a fan can see the screen, so the frame that
    hid it is what is measured and not the frame that started the fade."""
    plan.status["matches.json"] = 503
    page = open_shell(fan)
    page.wait_for_selector("#launch", state="visible")
    page.wait_for_function(GONE, timeout=CAP_MS + 4000)
    assert page.evaluate(STATE)["shown"] is False
    timeline = recorded(page)
    gone = first(timeline, present=True, shown=False)
    assert gone is not None, timeline
    assert MIN_HOLD_MS <= gone <= CAP_MS + SLACK_MS, (gone, timeline)
    assert not fan.errors, fan.errors


def test_it_never_outlives_its_cap_when_the_list_never_answers(fan, plan):
    plan.hang.add("matches.json")
    page = open_shell(fan)
    page.wait_for_selector("#launch", state="visible")
    page.wait_for_function(GONE, timeout=CAP_MS + 4000)
    assert page.evaluate(STATE)["shown"] is False
    timeline = recorded(page)
    gone = first(timeline, present=True, shown=False)
    assert gone is not None, timeline
    assert MIN_HOLD_MS <= gone <= CAP_MS + SLACK_MS, (gone, timeline)


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
def test_the_crossfade_runs_for_a_fan_who_asked_for_less_motion(
        playwright_browser, web_server, plan, motion):
    """The same crossfade either way, which is the correction Task 35 made.

    Task 34 took the fade away under `reduce` and that was wrong: an opacity
    fade is not motion. Nothing on the launch screen or on the list behind it
    moves, scales, slides or spins, so there is nothing for the preference to
    be about, and what it got instead was a hard cut from the mark to the
    list. Shawn saw that cut on an iPhone XR with Reduce Motion on.
    """
    plan.delay["matches.json"] = SLOW_SECONDS
    context = playwright_browser.new_context(
        viewport={"width": 390, "height": 844}, reduced_motion=motion,
    )
    page = context.new_page()
    try:
        page.add_init_script(WATCH)
        page.goto(web_server.url(SHELL), wait_until="commit")
        page.wait_for_selector("#launch", state="visible")
        # The fade is the shell's one number, under either preference.
        assert page.evaluate(STATE)["transition"] == "%gs" % (FADE_MS / 1000)
        assert page.evaluate(STATE)["listTransition"] == "%gs" % (FADE_MS / 1000)
        page.wait_for_function(GONE, timeout=(SLOW_SECONDS + 8) * 1000)
        timeline = recorded(page)
        assert [one for one in timeline if one["going"]], (motion, timeline)
        # And the two cross: the list is revealed in the frame the fade
        # starts in, not before it and not after it.
        faded = first(timeline, going=True)
        shown = first(timeline, listShown=True)
        assert faded is not None, timeline
        assert shown is not None, timeline
        assert shown == faded, (motion, shown, faded, timeline)
        gone = first(timeline, present=True, shown=False)
        assert gone is not None, timeline
        assert gone >= MIN_HOLD_MS + FADE_MS, (motion, gone, timeline)
        assert gone <= CAP_MS + SLACK_MS, (motion, gone, timeline)
    finally:
        context.close()


def ink(image):
    """The box the near-white pixels fall in and the box the amber ones do.

    A box rather than a pixel comparison: the browser rasterises the tagline
    with its own hinting and anti-aliasing and the generator fills polygons,
    so the two agree on where the drawing is and differ in the last shade of
    an edge. Where it is, is the claim worth making.
    """
    rgb = image.convert("RGB")
    width, height = rgb.size
    read = rgb.load()
    found = {"white": None, "amber": None}

    def note(key, x, y):
        box = found[key]
        found[key] = ((x, y, x, y) if box is None else
                      (min(box[0], x), min(box[1], y),
                       max(box[2], x), max(box[3], y)))

    for y in range(height):
        for x in range(width):
            r, g, b = read[x, y]
            if r > 200 and g > 200 and b > 200:
                note("white", x, y)
            elif r > 170 and 90 < g < 200 and b < 90:
                note("amber", x, y)
    return found


@pytest.mark.parametrize("screen", brand().IPHONES,
                         ids=lambda one: "%dx%d@%dx" % one)
def test_the_startup_image_is_this_screen(playwright_browser, web_server, plan,
                                          screen):
    """Every one of the eleven startup images against a screenshot of the
    shell at the screen that image is drawn for, at that screen's own device
    pixel ratio.

    This is what holds `scripts/brand/build_svg.py`'s `launch_layout` to the
    CSS in `app/web/index.html`: they are the same rules written twice, and
    the only way to know they still say the same thing is to draw both and
    measure. Reading the tagline's type size where the CSS centres its 20 px
    line box put the mark 2 CSS px out, which is what the first of these
    found.

    It is the eleven rather than the one because the layout is not a share of
    the screen: the mark is 300 CSS px wide on a 375 px screen and on a 440 px
    one alike, and the block is centred on the height and lifted a fixed
    24 px. One screen agreeing says nothing about the arithmetic on the other
    ten, and the iPhone a fan opened it on was not the one that was checked.

    The shell is the whole screen here, which is what makes the comparison
    the right one to make: `black-translucent` and `viewport-fit=cover` mean
    the page covers the status bar, so the image iOS shows while the app
    starts and the screen the app paints are drawings of one rectangle.
    """
    from PIL import Image

    css_w, css_h, scale = screen
    name = brand().startup_name(*screen)

    # Held still: matches.json never answers, so the screen is up until the
    # cap and the screenshot is of the state rather than of a fade.
    plan.hang.add("matches.json")
    context = playwright_browser.new_context(
        viewport={"width": css_w, "height": css_h}, has_touch=True,
        is_mobile=True, device_scale_factor=scale,
    )
    try:
        page = context.new_page()
        page.goto(web_server.url(SHELL), wait_until="commit")
        page.wait_for_selector("#launch", state="visible")
        # The tagline is real text in a web font, and the font arrives after
        # the screen does: the markup ships visible and the mark is inline, so
        # the launch screen is up before any request of its own is answered,
        # which is the point of it. A screenshot taken in that window is a
        # screenshot of the fallback family, which is a different width.
        #
        # CI found it, on two of the eleven and not on the nine: the Linux
        # runner drew the tagline 52 device pixels wider on the left of
        # launch-1206x2622 and launch-1290x2796 and agreed to the pixel on
        # every other edge, which is a race and not a layout. This machine won
        # it eleven times out of eleven.
        #
        # The weight is part of the question. `document.fonts.check` is asked
        # whether a font matching the whole shorthand is ready, and the 400
        # faces of this family stay unloaded because nothing on this screen is
        # set in them: asking without the 500 is asking about a face that
        # never arrives.
        page.wait_for_function(
            "() => document.fonts.check('500 16px \"Hanken Grotesk\"')",
            timeout=10000,
        )
        shot = Image.open(io.BytesIO(page.screenshot()))
    finally:
        context.close()

    drawn = Image.open(WEB / "assets" / "launch" / name)
    assert shot.size == drawn.size == (css_w * scale, css_h * scale), (
        name, shot.size, drawn.size)

    painted, generated = ink(shot), ink(drawn)
    for key in ("white", "amber"):
        assert painted[key] is not None, (name, key)
        assert generated[key] is not None, (name, key)
        apart = [abs(a - b) for a, b in zip(painted[key], generated[key])]
        assert max(apart) <= SAME_DRAWING_PX, (name, key, painted[key],
                                               generated[key], apart)


#: Insets to force on the shell, to stand in for a screen that has them:
#: Chromium reports 0 for all four, and a layout that has moved out of the way
#: of nothing is not a layout that has been checked. They are a bound and not
#: a device's own numbers: more room than a status bar and a home indicator
#: take on any of the screens above.
FORCED_INSETS = {"top": 64, "right": 16, "bottom": 48, "left": 16}

#: The shell's four variables, set to `FORCED_INSETS` on the root element,
#: which beats the `:root` rule the stylesheet carries.
FORCE_INSETS = (
    "() => { const r = document.documentElement; "
    + " ".join(
        "r.style.setProperty('--safe-%s', '%dpx');" % (side, size)
        for side, size in FORCED_INSETS.items()
    )
    + " }"
)

INSET_STATE = """() => {
  const frame = document.getElementById('frame').getBoundingClientRect();
  const inner = document.getElementById('screen').getBoundingClientRect();
  const mark = document.getElementById('launch-mark').getBoundingClientRect();
  const line = document.getElementById('launch-line').getBoundingClientRect();
  return {
    screen: {width: window.innerWidth, height: window.innerHeight},
    frame: {top: frame.top, left: frame.left,
            right: frame.right, bottom: frame.bottom},
    inner: {top: inner.top, left: inner.left,
            right: inner.right, bottom: inner.bottom},
    block: {top: Math.min(mark.top, line.top),
            left: Math.min(mark.left, line.left),
            right: Math.max(mark.right, line.right),
            bottom: Math.max(mark.bottom, line.bottom)},
  };
}"""


@pytest.mark.parametrize("screen", brand().IPHONES + (ANDROID,),
                         ids=lambda one: "%dx%d@%dx" % one)
def test_nothing_sits_under_the_clock_or_the_home_indicator(
        playwright_browser, web_server, plan, screen):
    """With the insets forced, on every screen in the table and on Android.

    The shell is the one page iOS reports a safe area to: a screen is inside
    the iframe, where `env()` is 0, so a screen that asked would be told
    there is nothing to move out of the way. So the shell reads the four
    insets and pads the frame by them, and this is that padding measured.

    **The launch screen is deliberately not inset**, because it is the
    drawing the startup image has to match and that image is drawn for the
    whole screen. What is asked of it instead is that the mark and the
    tagline clear the insets where they sit, which they do on every screen
    here with room to spare: the block is a little above the middle and the
    insets are at the two ends.
    """
    css_w, css_h, scale = screen
    plan.hang.add("matches.json")
    context = playwright_browser.new_context(
        viewport={"width": css_w, "height": css_h}, has_touch=True,
        is_mobile=True, device_scale_factor=scale,
    )
    try:
        page = context.new_page()
        page.goto(web_server.url(SHELL), wait_until="commit")
        page.wait_for_selector("#launch", state="visible")
        page.evaluate(FORCE_INSETS)
        state = page.evaluate(INSET_STATE)
    finally:
        context.close()

    # The frame fills the screen, and the screens inside it start below the
    # clock and stop above the home indicator.
    assert state["inner"]["top"] >= FORCED_INSETS["top"], state
    assert state["inner"]["left"] >= FORCED_INSETS["left"], state
    assert (state["screen"]["width"] - state["inner"]["right"]
            >= FORCED_INSETS["right"]), state
    assert (state["screen"]["height"] - state["inner"]["bottom"]
            >= FORCED_INSETS["bottom"]), state

    # And the launch screen's own words clear them where they sit.
    block = state["block"]
    assert block["top"] >= FORCED_INSETS["top"], state
    assert block["left"] >= FORCED_INSETS["left"], state
    assert (state["screen"]["width"] - block["right"]
            >= FORCED_INSETS["right"]), state
    assert (state["screen"]["height"] - block["bottom"]
            >= FORCED_INSETS["bottom"]), state


# --------------------------------------------------------------------------
# No white frame, and a list that has painted before it is seen.
#
# The two rules Task 35 added, and the two the iPhone found. Shawn opened the
# app from the home-screen icon on an iPhone XR on 2026-11-15 and got a brief
# white flash at the top of the screen between the mark and the event list.
# Nothing in the suite was looking at pixels, so nothing had anything to say
# about it.
# --------------------------------------------------------------------------

#: The top of the screen, in CSS pixels. Where the flash was, and the band a
#: status bar sits over: it is the part of a load a fan is looking at.
TOP_BAND = {"x": 0, "y": 0, "width": 390, "height": 40}

#: A pixel is near-white when its darkest channel is above this. The app
#: background's three channels are 16, 19 and 25.
NEAR_WHITE = 170

#: How much of that band may be near-white in a sampled frame. Measured on
#: 2026-11-15 with the samples below: the worst any state reached was 0.0201,
#: which is the light text in the list's own header once the list is up. A
#: flash is the whole band, so a tenth of it is a long way above what the app
#: draws and a long way below what the defect drew.
WHITE_SHARE = 0.10

#: How long to keep sampling, in milliseconds on the page's own clock: past
#: the cap, so the samples cover the launch and the frames after it.
SAMPLE_UNTIL_MS = 3200

#: The defect, forced, so the sampler is known to be able to see one: the
#: launch screen taken away and the frame left white and visible. With the
#: list's own page never answering, nothing paints over it.
FORCE_A_WHITE_FRAME = """
document.addEventListener('DOMContentLoaded', function () {
  const style = document.createElement('style');
  style.textContent = '#launch { display: none !important; }' +
    '#screen { background-color: #fff !important; opacity: 1 !important; }';
  document.head.appendChild(style);
});
"""


def band_samples(page, band=None, until=SAMPLE_UNTIL_MS):
    """(when, share of near-white) for as many frames as can be screenshotted.

    A sample is a screenshot, so this is a sample of the load and not every
    frame of it: `CLAUDE.md` asks the rules of every frame a `MutationObserver`
    recorded, and an observer records attributes rather than pixels. What this
    can say is that none of the frames it caught was white, across a window
    that covers the hold, the crossfade and the frames after it.
    """
    from PIL import Image

    got = []
    while True:
        at = page.evaluate("() => performance.now()")
        shot = Image.open(io.BytesIO(page.screenshot(clip=band or TOP_BAND)))
        # A colour histogram rather than every pixel: the same arithmetic over
        # a few hundred entries instead of a few hundred thousand, which is
        # more samples over the same window.
        colours = shot.convert("RGB").getcolors(1 << 22)
        assert colours is not None, "more colours in the band than expected"
        total = sum(count for count, _ in colours)
        light = sum(count for count, colour in colours
                    if min(colour) > NEAR_WHITE)
        got.append((at, light / total))
        if at > until:
            return got


def sampling_context(playwright_browser):
    """A tab for the pixel samples, at one device pixel to the CSS pixel.

    The band's colour is the claim, not its resolution, and a screenshot at
    three device pixels is nine times the pixels to read per sample, which is
    fewer samples over the same window.
    """
    return playwright_browser.new_context(
        viewport={"width": 390, "height": 844}, has_touch=True, is_mobile=True,
        device_scale_factor=1,
    )


#: The four states the top of the screen is sampled in, as what to do to the
#: plan. The last is the one the white frame was hiding in: the list's own page
#: never answers, so nothing ever paints inside the frame and what a fan sees
#: after the cap is the frame's own colour.
WHITE_STATES = {
    "answered at once": lambda plan: None,
    "answered late": lambda plan: plan.delay.__setitem__("matches.json",
                                                         SLOW_SECONDS),
    "refused": lambda plan: plan.status.__setitem__("matches.json", 503),
    "the list never answers": lambda plan: plan.hang.add("matches.json"),
    "the list's page never answers": lambda plan: plan.hang.add(
        "prelude_01_picker.html"),
}


@pytest.mark.parametrize("state", sorted(WHITE_STATES))
def test_no_frame_of_the_top_of_the_screen_is_white(playwright_browser,
                                                    web_server, plan, state):
    """From the navigation to past the cap, in five states.

    The three things that make this true are in markup rather than in script,
    so they hold in the frames before any script has run: every page sets the
    app background in its own head in front of every stylesheet, the shell's
    iframe carries the same colour on the element, and it is invisible until
    the screen inside it says it has painted.

    The last state is the one the flash was hiding in. With the list's own
    page never answering there is no document in the frame to paint it, so
    what is left after the cap is the frame's own background: the app's
    colour, and not the white a browser paints an empty frame.
    """
    WHITE_STATES[state](plan)
    context = sampling_context(playwright_browser)
    try:
        page = context.new_page()
        page.goto(web_server.url(SHELL), wait_until="commit")
        samples = band_samples(page)
    finally:
        context.close()

    assert len(samples) > 8, (state, len(samples))
    worst = max(samples, key=lambda one: one[1])
    assert worst[1] <= WHITE_SHARE, (state, worst, len(samples))


def test_the_sampler_can_see_a_white_frame(playwright_browser, web_server,
                                           plan):
    """The check above, checked: the defect forced, and found.

    A sampler that reads the wrong pixels, or a threshold above what a white
    screen measures, passes everything. So the launch screen is taken away and
    the frame is left white and visible, with the list's own page never
    answering so nothing paints over it, and the same sampler is asked.
    """
    plan.hang.add("prelude_01_picker.html")
    context = sampling_context(playwright_browser)
    try:
        page = context.new_page()
        page.add_init_script(FORCE_A_WHITE_FRAME)
        page.goto(web_server.url(SHELL), wait_until="commit")
        samples = band_samples(page, until=1200)
    finally:
        context.close()

    worst = max(one[1] for one in samples)
    assert worst > 0.9, (worst, samples)
    assert worst > WHITE_SHARE, (worst, WHITE_SHARE)


@pytest.mark.parametrize("state", ["answered at once", "answered late",
                                   "refused", "the list never answers"])
def test_the_list_has_painted_before_it_is_ever_visible(fan, plan, state):
    """Asked of every frame the observer recorded, not of the state it
    settled in: `data-painted` on the framed document is true in every frame
    where the frame was revealed or had any opacity at all.

    `data-painted` is the screen's own and is about the drawing rather than
    the data: one frame drawn with the app background and its own stylesheet
    applied. It does not wait on matches.json, which is why it is true in all
    four of these states well before the cap, and why the cap's own reveal
    (which does not wait for it) is not a state the suite can reach. The one
    way to reach it is a screen whose page never answers, and
    `test_no_frame_of_the_top_of_the_screen_is_white` shows what a fan sees
    then: the frame's own background.
    """
    WHITE_STATES[state](plan)
    page = open_shell(fan)
    page.wait_for_function(GONE, timeout=CAP_MS + 4000)
    timeline = recorded(page)
    assert timeline, "the observer recorded nothing"
    seen = [one for one in timeline
            if one["listShown"] or (one["listOpacity"] or 0) > 0]
    assert seen, (state, timeline)
    for one in seen:
        assert one["listPainted"], (state, one)


def test_the_frame_is_invisible_until_the_launch_screen_goes(fan, plan):
    """The other half of the crossfade: the list is not up behind the mark
    waiting to be uncovered, it comes up as the mark goes.

    Measured as opacity rather than as the attribute, because the attribute
    is the cause and the opacity is what a fan sees.
    """
    plan.delay["matches.json"] = SLOW_SECONDS
    page = open_shell(fan)
    page.wait_for_selector("#launch", state="visible")
    assert page.evaluate(STATE)["listOpacity"] == 0
    page.wait_for_function(GONE, timeout=(SLOW_SECONDS + 8) * 1000)
    page.wait_for_function(LIST_UP, timeout=4000)
    assert page.evaluate(STATE)["listOpacity"] == 1

    timeline = recorded(page)
    # No frame has the list up while the mark is still solid.
    for one in timeline:
        if (one["listOpacity"] or 0) > 0:
            assert one["going"] or not one["shown"], one


def test_no_white_frame_at_an_android_viewport(playwright_browser, web_server,
                                              plan):
    """The same sampling at 412 by 915, where Chrome draws its own launch
    screen from the manifest and then hands the page over.

    Chrome's part is the manifest's `background_color` with the icon on it,
    which `tests/test_the_mark.py` holds to the app background and to holding
    no white pixel. This is the page's own part, after the hand over.
    """
    css_w, css_h, scale = ANDROID
    context = playwright_browser.new_context(
        viewport={"width": css_w, "height": css_h}, has_touch=True,
        is_mobile=True, device_scale_factor=1,
    )
    try:
        page = context.new_page()
        page.goto(web_server.url(SHELL), wait_until="commit")
        samples = band_samples(
            page, band={"x": 0, "y": 0, "width": css_w, "height": 40})
    finally:
        context.close()

    worst = max(samples, key=lambda one: one[1])
    assert worst[1] <= WHITE_SHARE, (worst, len(samples))


@pytest.mark.parametrize("screen", brand().IPHONES + (ANDROID,),
                         ids=lambda one: "%dx%d@%dx" % one)
def test_the_launch_runs_the_same_at_every_screen_size(playwright_browser,
                                                       web_server, plan,
                                                       screen):
    """The hold, the crossfade and the cap, on all eleven iPhone screens and
    at an Android viewport.

    None of the three numbers is a share of anything, so none of them should
    move with the screen; this is what says they do not. The Android row is
    what makes the claim about Chrome on Android the page's own rather than
    an inference from the iPhone sizes.
    """
    css_w, css_h, scale = screen
    plan.delay["matches.json"] = SLOW_SECONDS
    context = playwright_browser.new_context(
        viewport={"width": css_w, "height": css_h}, has_touch=True,
        is_mobile=True, device_scale_factor=scale,
    )
    try:
        page = context.new_page()
        page.add_init_script(WATCH)
        page.goto(web_server.url(SHELL), wait_until="commit")
        page.wait_for_selector("#launch", state="visible")
        assert page.evaluate(STATE)["listOpacity"] == 0
        page.wait_for_function(GONE, timeout=(SLOW_SECONDS + 8) * 1000)
        timeline = recorded(page)
        page.wait_for_function(LIST_UP, timeout=4000)
        state = page.evaluate(STATE)
    finally:
        context.close()

    faded = first(timeline, going=True)
    shown = first(timeline, listShown=True)
    gone = first(timeline, present=True, shown=False)
    assert faded is not None, (screen, timeline)
    assert shown == faded, (screen, shown, faded, timeline)
    assert faded >= MIN_HOLD_MS, (screen, faded, timeline)
    assert gone >= MIN_HOLD_MS + FADE_MS, (screen, gone, timeline)
    assert gone <= CAP_MS + SLACK_MS, (screen, gone, timeline)
    assert state["listOpacity"] == 1, (screen, state)
    for one in timeline:
        if (one["listOpacity"] or 0) > 0:
            assert one["listPainted"], (screen, one)


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
