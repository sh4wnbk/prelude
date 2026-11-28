"""The bird's-eye renderer and its football adapter, on a test page.

`app/web/birdseye.js` draws primitives up to a time and `app/web/birdseye-
football.js` turns a slot's records into them. Neither is on a screen yet, so
the page they are checked on is `tests/browser/pages/birdseye.html`, served
from a temporary directory beside copies of the two scripts and the two files
they read. Nothing is written into the repo.

What is held, for every slot of both matches:

* the finished picture, at the last segment's `start_ms`, draws exactly the
  records in `draw_from`, once each, and nothing else;
* just before each segment's `start_ms`, nothing from that segment on is
  drawn, and everything before it is;
* the frame, the sides, the listener's colour and the names, from the records;
* the renderer names no sport, and no "Verified from play data" appears.
"""

import json
import shutil
from pathlib import Path

import pytest

from tests.browser import server as local_server
from tests.browser.conftest import WEB

PAGE = Path(__file__).resolve().parent / "pages" / "birdseye.html"
SERVED = (
    "birdseye.js",
    "birdseye-football.js",
    "play_segments.json",
    "segment_timings.json",
)

SEGMENTS = json.loads((WEB / "play_segments.json").read_text(encoding="utf-8"))
TIMINGS = json.loads((WEB / "segment_timings.json").read_text(encoding="utf-8"))
NARRATIONS = json.loads((WEB / "narrations.json").read_text(encoding="utf-8"))[
    "narrations"
]

EVERY_SLOT = tuple(
    (match_id, slot)
    for match_id in sorted(SEGMENTS["matches"])
    for slot in sorted(SEGMENTS["matches"][match_id]["slots"])
)

SPORT_WORDS = ("pitch", "ball", "goal", "shot", "player", "football", "soccer")
LABEL = "Verified from play data"

#: The adapter's two colours, read off the page rather than written here.
TONES = "() => [Prelude.birdseyeFootball.AMBER, Prelude.birdseyeFootball.CHALK]"

#: What one picture drew: the mark ids and every other child of the layer.
DRAWN = """(ms) => {
  window.__view.picture(ms);
  const layer = document.querySelector('[data-layer="marks"]');
  const marks = [], labels = [], other = [];
  for (const child of layer.children) {
    if (child.hasAttribute('data-mark')) marks.push(child.getAttribute('data-mark'));
    else if (child.tagName === 'text' && child.hasAttribute('data-label-for'))
      labels.push([child.getAttribute('data-label-for'), child.textContent]);
    else other.push(child.outerHTML);
  }
  return {marks, labels, other};
}"""


def listener_for(match_id, slot):
    return NARRATIONS[match_id]["slots"][slot]["listener_side"]


def starts(match_id, slot):
    return [one["start_ms"] for one in TIMINGS["matches"][match_id][slot]["segments"]]


@pytest.fixture(scope="module")
def birdseye_server(tmp_path_factory):
    root = tmp_path_factory.mktemp("birdseye")
    shutil.copy(PAGE, root / "index.html")
    for name in SERVED:
        shutil.copy(WEB / name, root / name)
    running = local_server.serve(root)
    yield running
    running.shutdown()
    running.server_close()


@pytest.fixture
def mount(playwright_browser, birdseye_server):
    contexts = []

    def open_slot(match_id, slot, listener="from-slot", viewport=None):
        if listener == "from-slot":
            listener = listener_for(match_id, slot)
        context = playwright_browser.new_context(
            viewport=viewport or {"width": 390, "height": 844}
        )
        contexts.append(context)
        page = context.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(birdseye_server.url(
            "index.html", match=match_id, slot=slot,
            listener=listener and listener.replace(" ", "%20"),
        ))
        page.wait_for_function(
            "() => document.documentElement.hasAttribute('data-mounted') || "
            "document.documentElement.hasAttribute('data-failed')"
        )
        failed = page.evaluate(
            "() => document.documentElement.getAttribute('data-failed')"
        )
        assert failed is None, failed
        page.errors = errors
        return page

    yield open_slot
    for context in contexts:
        context.close()


def test_the_renderer_names_no_sport():
    text = (WEB / "birdseye.js").read_text(encoding="utf-8").lower()
    found = [word for word in SPORT_WORDS if word in text]
    assert found == []


def test_neither_script_carries_the_label():
    for name in ("birdseye.js", "birdseye-football.js"):
        assert LABEL.lower() not in (WEB / name).read_text(encoding="utf-8").lower()


@pytest.mark.parametrize("match_id,slot", EVERY_SLOT)
def test_the_finished_picture_is_exactly_draw_from(mount, match_id, slot):
    page = mount(match_id, slot)
    drawn = page.evaluate(DRAWN, starts(match_id, slot)[-1])
    expected = set(SEGMENTS["matches"][match_id]["slots"][slot]["draw_from"])
    assert sorted(drawn["marks"]) == sorted(expected)
    assert len(drawn["marks"]) == len(set(drawn["marks"]))
    assert drawn["other"] == []
    assert {for_id for for_id, _ in drawn["labels"]} <= expected
    assert page.errors == []


@pytest.mark.parametrize("match_id,slot", EVERY_SLOT)
def test_nothing_is_drawn_before_its_segment_starts(mount, match_id, slot):
    page = mount(match_id, slot)
    draw_from = SEGMENTS["matches"][match_id]["slots"][slot]["draw_from"]
    times = starts(match_id, slot)
    assert page.evaluate(DRAWN, times[0] - 1) == {
        "marks": [], "labels": [], "other": [],
    }
    for number, start in enumerate(times):
        drawn = set(page.evaluate(DRAWN, start - 1)["marks"])
        assert all(draw_from[one] < number for one in drawn), (number, drawn)
        assert drawn == {
            one for one, at in draw_from.items() if times[at] <= start - 1
        }, number


def test_butchers_dribbled_past_is_turned_into_the_one_frame(mount):
    records = SEGMENTS["matches"]["3750191"]["records"]
    found = [
        (event_id, record) for event_id, record in records.items()
        if record["index"] == 1961
    ]
    assert len(found) == 1
    event_id, record = found[0]
    assert (record["type"], record["player"]) == ("Dribbled Past", "Terry Butcher")
    assert record["location"] == [33.0, 11.5]
    page = mount("3750191", "storyteller_neutral")
    mark = page.evaluate(
        "(id) => window.__view.marks.find((one) => one.id === id)", event_id
    )
    assert mark["at"] == [87.0, 68.5]
    assert mark["kind"] == "ring"
    assert mark["crossed"] is True
    page.evaluate(DRAWN, starts("3750191", "storyteller_neutral")[-1])
    ring = page.evaluate(
        "(id) => { const c = document.querySelector("
        "'[data-mark=\"' + id + '\"] circle'); "
        "return [Number(c.getAttribute('cx')), Number(c.getAttribute('cy'))]; }",
        event_id,
    )
    assert ring == [87.0, 68.5]


@pytest.mark.parametrize("match_id,slot", EVERY_SLOT)
def test_every_mark_is_its_record_in_the_one_frame(mount, match_id, slot):
    match = SEGMENTS["matches"][match_id]
    scorer = {r["team"] for r in match["records"].values() if r["type"] == "Shot"}
    assert len(scorer) == 1
    scorer = scorer.pop()
    kinds = {
        "Pass": "object", "Carry": "actor", "Dribble": "ring",
        "Dribbled Past": "ring", "Shot": "burst", "Ball Receipt*": "dot",
        "Ball Recovery": "dot", "Pressure": "dot",
    }
    page = mount(match_id, slot)
    amber, chalk = page.evaluate(TONES)
    listener = listener_for(match_id, slot)
    times = starts(match_id, slot)
    draw_from = match["slots"][slot]["draw_from"]
    for mark in page.evaluate("() => window.__view.marks"):
        record = match["records"][mark["id"]]
        turned = record["team"] != scorer

        def framed(point):
            if point is None:
                return None
            x, y = point[0], point[1]
            return [120 - x, 80 - y] if turned else [x, y]

        assert mark["kind"] == kinds[record["type"]]
        assert mark["at"] == framed(record["location"])
        assert mark["to"] == framed(record["end_location"])
        assert mark["crossed"] is turned
        assert mark["tone"] == (amber if record["team"] == listener else chalk)
        assert mark["label"] == record["label"]
        assert mark["startMs"] == times[draw_from[mark["id"]]]


@pytest.mark.parametrize("match_id", sorted(SEGMENTS["matches"]))
def test_a_neutral_listener_gets_no_amber(mount, match_id):
    page = mount(match_id, "storyteller_neutral", listener=None)
    amber, _chalk = page.evaluate(TONES)
    page.evaluate(DRAWN, starts(match_id, "storyteller_neutral")[-1])
    svg = page.evaluate("() => document.getElementById('surface').outerHTML")
    assert amber.lower() not in svg.lower()


def test_the_listeners_side_is_amber_and_only_it(mount):
    page = mount("3750191", "buddy_conceded")
    amber, chalk = page.evaluate(TONES)
    records = SEGMENTS["matches"]["3750191"]["records"]
    tones = {
        (records[mark["id"]]["team"], mark["tone"])
        for mark in page.evaluate("() => window.__view.marks")
    }
    assert tones == {("England", amber), ("Argentina", chalk)}


@pytest.mark.parametrize("match_id,slot", EVERY_SLOT)
def test_a_name_is_written_from_when_its_segment_starts(mount, match_id, slot):
    match = SEGMENTS["matches"][match_id]
    draw_from = match["slots"][slot]["draw_from"]
    times = starts(match_id, slot)
    page = mount(match_id, slot)
    for start in times:
        drawn = page.evaluate(DRAWN, start)
        names = {text for _, text in drawn["labels"]}
        wanted = {
            match["records"][one]["label"]
            for one, at in draw_from.items()
            if times[at] <= start and match["records"][one]["label"]
        }
        assert names == wanted, start


@pytest.mark.parametrize("match_id,slot", EVERY_SLOT)
def test_no_verified_label_in_the_view(mount, match_id, slot):
    page = mount(match_id, slot)
    page.evaluate(DRAWN, starts(match_id, slot)[-1])
    shown = page.evaluate(
        "() => document.body.innerText + ' ' + "
        "document.getElementById('surface').textContent"
    )
    assert LABEL.lower() not in shown.lower()
