"""The recording plays, the bars move with the voice, and the waveform seeks.

The unit suite reads the player's code and holds its shape. What it cannot do
is play a sound: the clock, the amber fill, the inline bar heights the Web
Audio analyser writes and a drag that lands on a position all need a browser,
a decoder and a server that answers a byte range. `tests/browser/server.py`
answers ranges with `206` for that reason, which is what GitHub Pages does.

What each check is about:

- **The clock and the fill follow the voice.** The readout moves off `0:00`,
  `aria-valuemax` picks up the recording's length and `aria-valuenow` moves
  with it, and the amber fill grows.
- **The bars move with the voice.** `drawLevels` writes an inline height on
  each bar from the analyser, so a playing recording leaves heights that
  differ from each other and from the resting classes, and a pause clears
  them.
- **The waveform is a scrubber.** A press at four fifths of the track moves
  the position to four fifths of the recording, playing or paused, which is a
  forward seek into bytes the element has not necessarily buffered.
- **The arrow keys move five seconds**, and the ends clamp.
- **Replay 10s goes back ten seconds** and does not go below zero.
- **The Moments hero card is the same player.** Its bars follow the voice and
  its track scrubs, because `wirePlayer` is one function and both screens hand
  it their own markup. The cards with no recording are the other half of that
  check: nothing is handed over for them, so their bars keep the heights the
  markup gives them, their track is not a slider and there is nothing on it to
  focus.
"""

import pytest

from tests.browser.conftest import MOMENT_CARD, PLAY_OFFERED, track_reads

#: The bars, by the class the markup gives them, which is how the player finds
#: them too.
BARS = "#scrubTrack div.w-\\[3px\\]"

STATE = """() => {
  const track = document.getElementById('scrubTrack');
  const bars = Array.from(document.querySelectorAll('#scrubTrack div.w-\\\\[3px\\\\]'));
  return {
    clock: document.getElementById('timerReadout').textContent,
    icon: document.getElementById('playIcon').textContent,
    now: Number(track.getAttribute('aria-valuenow')),
    max: Number(track.getAttribute('aria-valuemax')),
    filled: bars.filter(b => b.classList.contains('bg-primary-container')).length,
    bars: bars.length,
    heights: bars.map(b => b.style.height),
    playhead: (document.querySelector('#scrubTrack .absolute') || {}).style.left,
  };
}"""


def press_at(page, fraction):
    """Press the waveform at `fraction` of its width.

    Through the locator rather than through raw coordinates: it waits for the
    track to hold still and measures it at the moment of the press, so a font
    arriving late and moving the row cannot send the press somewhere else.
    """
    track = page.locator("#scrubTrack")
    box = track.bounding_box()
    track.click(position={"x": box["width"] * fraction, "y": box["height"] / 2})
    return box


@pytest.fixture
def playing(fan, match_ids):
    """The moment card with a recording ready, for the 1986 neutral listener."""
    match_id = match_ids[0]
    fan.remember(match_id=match_id, listener="neutral")
    page = fan.visit(MOMENT_CARD, match=match_id)
    page.wait_for_function(PLAY_OFFERED)
    page.wait_for_function(track_reads("valuemax", "v > 0"))
    return page


def test_the_recording_plays_and_the_clock_follows_it(playing):
    before = playing.evaluate(STATE)
    assert before["clock"] in ("", "0:00"), before
    assert before["max"] > 0, before
    assert before["now"] == 0, before
    assert before["filled"] == 0, before

    playing.click("#playBtn")
    # Past a whole second, because the readout is floored: it reads 0:00 until
    # the voice has been going for one.
    playing.wait_for_function(track_reads("valuenow", "v > 1.2"))
    after = playing.evaluate(STATE)
    assert after["icon"] == "pause", after
    assert after["clock"] != "0:00", after
    assert after["now"] > 1.2, after
    assert after["filled"] >= 1, after
    assert after["playhead"] not in (None, "", "0%"), after


def test_the_bars_move_with_the_voice_and_rest_on_pause(playing):
    resting = playing.evaluate(STATE)
    assert set(resting["heights"]) == {""}, resting["heights"]

    playing.click("#playBtn")
    playing.wait_for_function(
        """() => {
             const bars = Array.from(document.querySelectorAll(
               '#scrubTrack div.w-\\\\[3px\\\\]'));
             const set = new Set(bars.map(b => b.style.height));
             return !set.has('') && set.size > 2;
           }"""
    )
    moving = playing.evaluate(STATE)
    assert len(set(moving["heights"])) > 2, moving["heights"]
    for height in moving["heights"]:
        pixels = float(height.rstrip("px"))
        assert 6 <= pixels <= 36, moving["heights"]

    playing.click("#playBtn")
    playing.wait_for_function(
        """() => Array.from(document.querySelectorAll(
             '#scrubTrack div.w-\\\\[3px\\\\]')).every(b => b.style.height === '')"""
    )
    rested = playing.evaluate(STATE)
    assert set(rested["heights"]) == {""}, rested["heights"]
    assert rested["icon"] == "play_arrow", rested


def test_a_drag_on_the_waveform_seeks(playing):
    length = playing.evaluate(STATE)["max"]

    press_at(playing, 0.8)
    playing.wait_for_function(track_reads("valuenow", "v > 0"))
    seeked = playing.evaluate(STATE)
    assert abs(seeked["now"] - length * 0.8) < length * 0.08, (seeked, length)
    assert seeked["icon"] == "play_arrow", "a seek does not start the voice"
    assert seeked["filled"] > seeked["bars"] / 2, seeked

    # And back to the start, still paused.
    press_at(playing, 0.02)
    playing.wait_for_function(track_reads("valuenow", "v < 1"))
    back = playing.evaluate(STATE)
    assert back["now"] < length * 0.1, back
    assert back["icon"] == "play_arrow", back
    assert back["filled"] <= 2, back


def test_a_forward_seek_then_play_keeps_the_position(playing):
    """The first play starts at the opening word unless the fan has moved the
    playhead, which is Task 24's rule and the one a seek has to not undo."""
    length = playing.evaluate(STATE)["max"]
    press_at(playing, 0.5)
    playing.wait_for_function(track_reads("valuenow", "v > 0"))
    playing.click("#playBtn")
    playing.wait_for_timeout(700)
    state = playing.evaluate(STATE)
    assert state["now"] > length * 0.4, state
    assert state["icon"] == "pause", state


def test_the_arrow_keys_move_five_seconds(playing):
    playing.focus("#scrubTrack")
    length = playing.evaluate(STATE)["max"]

    playing.keyboard.press("ArrowRight")
    playing.wait_for_timeout(150)
    once = playing.evaluate(STATE)["now"]
    assert abs(once - 5) < 0.6, once

    playing.keyboard.press("ArrowRight")
    playing.wait_for_timeout(150)
    twice = playing.evaluate(STATE)["now"]
    assert abs(twice - 10) < 0.6, twice

    playing.keyboard.press("ArrowLeft")
    playing.wait_for_timeout(150)
    assert abs(playing.evaluate(STATE)["now"] - 5) < 0.6

    # The start clamps rather than going negative.
    for _ in range(4):
        playing.keyboard.press("ArrowLeft")
    playing.wait_for_timeout(200)
    assert playing.evaluate(STATE)["now"] == 0

    # And the end clamps rather than running past the recording.
    for _ in range(int(length // 5) + 3):
        playing.keyboard.press("ArrowRight")
    playing.wait_for_timeout(300)
    assert playing.evaluate(STATE)["now"] <= length + 0.1


def test_replay_goes_back_ten_seconds(playing):
    playing.focus("#scrubTrack")
    for _ in range(3):
        playing.keyboard.press("ArrowRight")
    playing.wait_for_timeout(200)
    at = playing.evaluate(STATE)["now"]
    assert at > 10, at

    playing.click("#replayAction")
    playing.wait_for_timeout(400)
    after = playing.evaluate(STATE)
    assert after["now"] < at, after
    assert after["icon"] == "pause", after

    # From near the start it clamps at zero rather than going negative.
    playing.click("#playBtn")
    playing.focus("#scrubTrack")
    playing.keyboard.press("ArrowLeft")
    playing.keyboard.press("ArrowLeft")
    playing.keyboard.press("ArrowLeft")
    playing.click("#replayAction")
    playing.wait_for_timeout(300)
    assert playing.evaluate(STATE)["now"] >= 0


#: One Moments card's player strip, read the way `STATE` reads the moment
#: card's. `index` is the card's position in the list.
MOMENTS_STATE = """(index) => {
  const cards = Array.from(document.querySelectorAll(
    '[data-field=moments_list] > *'));
  const card = cards[index];
  const track = card.querySelector('[data-field=moment_track]');
  const bars = Array.from(track.querySelectorAll('div.w-1'));
  const button = card.querySelector('[data-field=moment_play]');
  return {
    cards: cards.length,
    disabled: button.disabled,
    role: track.getAttribute('role'),
    tabindex: track.getAttribute('tabindex'),
    label: track.getAttribute('aria-label'),
    now: Number(track.getAttribute('aria-valuenow')),
    max: Number(track.getAttribute('aria-valuemax')),
    clock: card.querySelector('[data-field=moment_time]').textContent,
    icon: card.querySelector('[data-field=moment_play_icon]').textContent,
    bars: bars.length,
    filled: bars.filter(b => b.classList.contains('bg-primary-container')).length,
    heights: bars.map(b => b.style.height),
  };
}"""


def hero_index(page):
    """Which card in the list is the one with a recording."""
    return page.evaluate(
        """() => Array.from(document.querySelectorAll(
             '[data-field=moments_list] > *'))
           .findIndex(c => !c.querySelector('[data-field=moment_play]').disabled)"""
    )


@pytest.fixture
def moments(fan, match_ids):
    """The Moments screen with the hero card's recording ready, 1986 neutral."""
    from tests.browser.conftest import MOMENTS

    match_id = match_ids[0]
    fan.remember(match_id=match_id, listener="neutral")
    page = fan.visit(MOMENTS, match=match_id)
    page.wait_for_function(
        """() => Array.from(document.querySelectorAll(
             '[data-field=moments_list] [data-field=moment_play]'))
           .some(b => !b.disabled)"""
    )
    return page


def test_the_moments_hero_card_is_a_scrubber(moments):
    """The track it was handed is a slider, with the recording's length in it
    once the metadata lands. Before Task 32 those bars were fixed and the
    track was not a control at all."""
    page = moments
    at = hero_index(page)
    assert at >= 0
    page.wait_for_function(
        """(index) => {
             const card = document.querySelectorAll(
               '[data-field=moments_list] > *')[index];
             const t = card && card.querySelector('[data-field=moment_track]');
             return !!t && Number(t.getAttribute('aria-valuemax')) > 0;
           }""",
        arg=at,
    )
    state = page.evaluate(MOMENTS_STATE, at)
    assert state["disabled"] is False
    assert state["role"] == "slider"
    assert state["tabindex"] == "0"
    assert state["label"] == "Narration position in seconds"
    assert state["max"] > 0, state
    assert state["bars"] > 0


def test_the_moments_cards_without_a_recording_stay_fixed(moments):
    """Nothing is handed over for them, so the markup is what they are: the
    button disabled, no slider, no inline height on any bar and nothing in the
    clock."""
    page = moments
    hero = hero_index(page)
    total = page.evaluate(MOMENTS_STATE, hero)["cards"]
    assert total > 1, total
    for index in range(total):
        if index == hero:
            continue
        state = page.evaluate(MOMENTS_STATE, index)
        assert state["disabled"] is True, (index, state)
        assert state["role"] is None, (index, state)
        assert state["tabindex"] is None, (index, state)
        assert state["clock"] == "", (index, state)
        assert set(state["heights"]) == {""}, (index, state)
        # And the bars are still the ones the markup painted, which is not all
        # of them: the templates ship a played run and a rest run.
        assert 0 < state["filled"] < state["bars"], (index, state)


def test_the_moments_bars_move_with_the_voice(moments, match_ids):
    """The analyser writes an inline height on each bar while the recording
    plays, and a pause clears them. The same check
    `test_the_bars_move_with_the_voice_and_rest_on_pause` makes of the moment
    card, on the markup the Moments cards have."""
    page = moments
    at = hero_index(page)
    before = page.evaluate(MOMENTS_STATE, at)
    assert set(before["heights"]) == {""}, before

    page.locator(
        "[data-field=moments_list] [data-field=moment_play]:not([disabled])"
    ).click()
    page.wait_for_function(
        """(index) => {
             const card = document.querySelectorAll(
               '[data-field=moments_list] > *')[index];
             const bars = Array.from(card.querySelectorAll(
               '[data-field=moment_track] div.w-1'));
             const set = new Set(bars.map(b => b.style.height));
             return set.size > 1 && !set.has('');
           }""",
        arg=at,
        timeout=15000,
    )
    moving = page.evaluate(MOMENTS_STATE, at)
    assert len(set(moving["heights"])) > 1, moving
    assert moving["icon"] == "pause"
    assert moving["clock"] != "", moving

    page.locator(
        "[data-field=moments_list] [data-field=moment_play]:not([disabled])"
    ).click()
    page.wait_for_function(
        """(index) => {
             const card = document.querySelectorAll(
               '[data-field=moments_list] > *')[index];
             const bars = Array.from(card.querySelectorAll(
               '[data-field=moment_track] div.w-1'));
             return bars.every(b => b.style.height === '');
           }""",
        arg=at,
    )


def test_a_drag_on_the_moments_waveform_seeks(moments):
    """A press at four fifths of the track moves the position to four fifths
    of the recording, with nothing playing."""
    page = moments
    at = hero_index(page)
    page.wait_for_function(
        """(index) => {
             const card = document.querySelectorAll(
               '[data-field=moments_list] > *')[index];
             const t = card && card.querySelector('[data-field=moment_track]');
             return !!t && Number(t.getAttribute('aria-valuemax')) > 0;
           }""",
        arg=at,
    )
    total = page.evaluate(MOMENTS_STATE, at)["max"]
    track = page.locator(
        "[data-field=moments_list] > *:nth-child(%d) [data-field=moment_track]"
        % (at + 1)
    )
    box = track.bounding_box()
    track.click(position={"x": box["width"] * 0.8, "y": box["height"] / 2})
    page.wait_for_function(
        """([index, want]) => {
             const card = document.querySelectorAll(
               '[data-field=moments_list] > *')[index];
             const t = card.querySelector('[data-field=moment_track]');
             return Math.abs(Number(t.getAttribute('aria-valuenow')) - want) < 2.5;
           }""",
        arg=[at, total * 0.8],
    )
    state = page.evaluate(MOMENTS_STATE, at)
    assert state["icon"] == "play_arrow", "the seek started it playing"
    assert state["filled"] > state["bars"] / 2, state


def test_the_moments_hero_card_plays_and_pauses(fan, match_ids, expected):
    """The compact button: one tap plays, a second pauses, and the icon says
    which."""
    from tests.browser.conftest import MOMENTS

    match_id = match_ids[1]
    fan.remember(match_id=match_id, listener="team_b")
    page = fan.visit(MOMENTS, match=match_id)
    button = page.locator(
        "[data-field=moments_list] [data-field=moment_play]:not([disabled])"
    )
    assert button.count() == 1
    icon = page.locator("[data-field=moments_list] [data-field=moment_play_icon]")

    button.click()
    page.wait_for_function(
        """() => Array.from(document.querySelectorAll(
             '[data-field=moments_list] [data-field=moment_play_icon]'
           )).some(i => i.textContent === 'pause')"""
    )
    assert "pause" in icon.nth(1).text_content()

    button.click()
    page.wait_for_function(
        """() => Array.from(document.querySelectorAll(
             '[data-field=moments_list] [data-field=moment_play_icon]'
           )).every(i => i.textContent === 'play_arrow')"""
    )
    assert fan.audio_loaded() == [expected(match_id, "team_b")["file"]]
    assert not fan.errors, fan.errors


def test_the_server_answers_a_byte_range(playing, match_ids, matches):
    """The suite's own server, which has to behave like the deployed host or a
    forward seek is never exercised. `docs/HARNESS.md` records the
    difference: `http.server` answers `200` with the whole file."""
    file = matches[match_ids[0]]["hero"]["audio"]["storyteller_neutral"]
    answer = playing.evaluate(
        """async (file) => {
             const r = await fetch(file, {headers: {Range: 'bytes=0-99'}});
             const body = await r.arrayBuffer();
             return {
               status: r.status,
               range: r.headers.get('content-range'),
               accept: r.headers.get('accept-ranges'),
               bytes: body.byteLength,
             };
           }""",
        file,
    )
    assert answer["status"] == 206, answer
    assert answer["bytes"] == 100, answer
    assert answer["accept"] == "bytes", answer
    assert answer["range"].startswith("bytes 0-99/"), answer
