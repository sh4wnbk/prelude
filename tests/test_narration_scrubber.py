"""The waveform is a scrubber, and the opening word is not lost.

Two things were wrong with the player after Task 23.

**The first word was cut on an iPhone.** The 2022 Storyteller started at
"tina" rather than at "Argentina". The element is routed through a Web Audio
graph, and iOS hands back a suspended `AudioContext`: `audio.play()` called
before the context is running starts the element's clock into a graph that is
rendering nothing, and whatever plays in that gap is gone. So the tap asks for
`resume()` inside the gesture, waits for it, and only then plays, from the
start on the first play.

**The waveform only showed a position; it could not set one.** A click handler
read `e.clientX`, which touch gives too, but there was no drag and no keyboard.
It is now a pointer-event scrubber: `pointerdown`, `pointermove` and
`pointerup` with pointer capture, so touch and mouse share one path, with the
amber fill following the finger whether the recording is playing or paused.

These are source tests, as `tests/test_narration_player.py` and
`tests/test_narration_waveform.py` are; the browser half is a run in headless
Chromium on both matches, served with Range support, and it is recorded in
`HANDOFF.md`.
"""

import hashlib
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
PLAYER = WEB / "narration-player.js"
CARD = WEB / "prelude_03_moment_card.html"
MATCHES = WEB / "matches.json"

#: Five seconds an arrow press, which is what the card is built for.
ARROW_SECONDS = 5

#: The six recordings as they stand. The fix for the cut word was the order of
#: resume() and play(), so no audio file was re-encoded: these digests are what
#: says so. A lead-in of silence would change every one of them, which is a
#: change to make on purpose and with this list.
RECORDINGS = {
    "3750191_buddy_conceded.mp3": "fd5056abe8f0528072f586d36b404421fcc914fdb6f9994e73bed3c8277e58a9",
    "3750191_buddy_scored.mp3": "d9772ed292cb83a297419125e17a78acb98b946cbfc6052699f44bdc23c8fe8a",
    "3750191_storyteller_neutral.mp3": "9c28981a5c99a000d18f6d5d52c133e4865a8629e3ad51b070d12193b4e0c71b",
    "3869685_buddy_conceded.mp3": "db0acf1f8f5698db6a24539b8d90c4382bd17561dc2865193cc3cb73b38a8904",
    "3869685_buddy_scored.mp3": "07877fc839aa81151928d3f4f6b281868211f7e672ee7de6069c050f8bfc1318",
    "3869685_storyteller_neutral.mp3": "9ad12f9eaf9cd2296f5f6b0cb8fe812c175db1eb16ba1958d5ac1aa11d961d62",
}


def player():
    """The player's code, with its line comments taken out.

    The comments say what the code does, in the same words, so a test reading
    the raw file would count the prose as well as the call. This is the helper
    `tests/test_narration_waveform.py` uses, for the same reason.
    """
    text = PLAYER.read_text(encoding="utf-8")
    return "\n".join(re.sub(r"\s*//.*$", "", line) for line in text.splitlines())


def block_after(text, marker):
    """The brace-balanced block that opens after `marker`."""
    at = text.find(marker)
    assert at != -1, f"{marker!r} is not in the player"
    opened = text.find("{", at)
    assert opened != -1, f"no block opens after {marker!r}"
    depth = 0
    for i in range(opened, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[opened : i + 1]
    pytest.fail(f"the block after {marker!r} never closes")


def play_handler():
    return block_after(player(), "playBtn.addEventListener('click'")


def card():
    return CARD.read_text(encoding="utf-8")


def track_tag():
    """The opening tag of the waveform, which is the scrubber's element."""
    found = re.search(r'<div [^>]*id="scrubTrack"[^>]*>', card())
    assert found, "the card has no scrubTrack element"
    return found.group(0)


class TestTheContextIsRunningBeforePlay:
    def test_the_tap_waits_for_the_resume(self):
        """The whole fix for the cut first word: the element's clock starts
        when play() is called, and a suspended graph renders none of it."""
        body = play_handler()
        assert "await resumeContext()" in body, body
        assert body.index("await resumeContext()") < body.index("audio.play()")

    def test_the_handler_can_wait(self):
        assert re.search(
            r"playBtn\.addEventListener\('click',\s*async function", player()
        ), "the play handler is not async, so it cannot await the resume"

    def test_nothing_plays_before_the_resume(self):
        body = play_handler()
        assert body.count("audio.play()") == 1, "more than one play() in the tap"

    def test_the_graph_is_opened_before_the_resume_is_asked_for(self):
        """`resumeContext` resumes the context the opener built, so the order
        inside the gesture is open, then resume, then play."""
        body = play_handler()
        assert body.index("openAnalyser()") < body.index("await resumeContext()")

    def test_the_resume_answers_with_something_to_wait_on(self):
        """Every path out of it, including the two that have nothing to do and
        the one that throws, so the tap never waits on undefined."""
        body = block_after(player(), "function resumeContext(")
        assert body.count("return") == len(
            re.findall(r"return (?:resuming|Promise\.resolve\(\))", body)
        ), body
        assert "Promise.resolve()" in body
        assert "catch (err)" in body

    def test_the_first_play_starts_at_the_opening_word(self):
        body = play_handler()
        assert re.search(r"audio\.currentTime\s*=\s*0", body), body
        assert "firstPlay" in body

    def test_it_does_not_undo_a_scrub_the_fan_made_first(self):
        """A fan may drag before ever pressing play, and the first play has to
        start where they left the playhead rather than at zero."""
        body = play_handler()
        assert re.search(r"if\s*\(firstPlay\s*&&\s*!playheadMoved\)", body), body
        seek = block_after(player(), "function seekToFraction(")
        assert "playheadMoved = true" in seek

    def test_a_refused_play_does_not_leave_a_pause_icon(self):
        body = play_handler()
        assert ".catch(" in body
        assert body.count("'play_arrow'") == 2, body


class TestTheRecordingsWereNotTouched:
    @pytest.mark.parametrize("name", sorted(RECORDINGS))
    def test_every_recording_is_byte_for_byte_what_it_was(self, name):
        path = WEB / "assets" / "audio" / name
        assert path.is_file(), path
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == RECORDINGS[name], name

    def test_the_audio_map_still_names_exactly_those_six(self):
        doc = json.loads(MATCHES.read_text(encoding="utf-8"))
        named = set()
        for entry in doc["matches"]:
            for path in entry["hero"]["audio"].values():
                named.add(path.rsplit("/", 1)[-1])
        assert named == set(RECORDINGS)


class TestTheWaveformScrubs:
    def test_it_listens_for_the_three_pointer_events(self):
        text = player()
        for event in ("pointerdown", "pointermove", "pointerup"):
            assert f"scrubTrack.addEventListener('{event}'" in text, event

    def test_touch_and_mouse_share_one_path(self):
        """Pointer events cover both, so the click handler that used to read
        `e.clientX` is gone and there is no touch handler beside it."""
        text = player()
        assert "scrubTrack.addEventListener('click'" not in text
        for event in ("touchstart", "touchmove", "touchend", "mousedown"):
            assert event not in text, event

    def test_the_drag_is_captured(self):
        body = block_after(player(), "scrubTrack.addEventListener('pointerdown'")
        assert "setPointerCapture(e.pointerId)" in body
        assert "releasePointerCapture" in player()

    def test_a_move_without_a_drag_does_nothing(self):
        body = block_after(player(), "scrubTrack.addEventListener('pointermove'")
        assert re.search(
            r"if\s*\(scrubPointer === null \|\| e\.pointerId !== scrubPointer\)", body
        ), body
        assert "return;" in block_after(body, "if (scrubPointer === null")

    def test_the_position_is_a_fraction_of_the_width(self):
        body = block_after(player(), "function fractionAtX(")
        assert "getBoundingClientRect()" in body
        assert "clientX - rect.left" in body
        assert "rect.width" in body
        assert "Math.max(0, Math.min(1," in body, "the fraction is not clamped"

    def test_the_fraction_sets_the_time_and_is_clamped(self):
        body = block_after(player(), "function seekToFraction(")
        assert re.search(r"Math\.max\(0, Math\.min\(1, fraction\)\)", body), body
        assert re.search(r"audio\.currentTime\s*=\s*at \* total", body), body

    def test_a_seek_with_no_duration_is_dropped(self):
        """`audio.duration` is NaN until the metadata is in, and a fraction of
        NaN is not a position."""
        body = block_after(player(), "function playLength(")
        assert "isFinite(total)" in body
        seek = block_after(player(), "function seekToFraction(")
        assert "playLength()" in seek
        assert "return;" in block_after(seek, "if (!total)")

    def test_the_fill_follows_the_finger_at_once(self):
        """Not on the next timeupdate: a paused recording sends none."""
        body = block_after(player(), "function seekToFraction(")
        assert "paintProgress(at)" in body
        assert "paintClock(audio.currentTime)" in body

    def test_every_pointer_handler_moves_the_playhead(self):
        text = player()
        for event in ("pointerdown", "pointermove"):
            body = block_after(text, f"scrubTrack.addEventListener('{event}'")
            assert "seekToFraction(fractionAtX(e.clientX))" in body, event
        assert "endScrub(e, true)" in block_after(
            text, "scrubTrack.addEventListener('pointerup'"
        )

    def test_a_cancelled_gesture_leaves_the_playhead_where_it_got_to(self):
        text = player()
        assert "endScrub(e, false)" in block_after(
            text, "scrubTrack.addEventListener('pointercancel'"
        )


class TestTheDragDoesNotScrollThePage:
    def test_the_handlers_refuse_the_default(self):
        text = player()
        for event in ("pointerdown", "pointermove"):
            body = block_after(text, f"scrubTrack.addEventListener('{event}'")
            assert "e.preventDefault()" in body, event

    def test_the_waveform_takes_the_touch_itself(self):
        assert "touch-action: none" in track_tag(), track_tag()

    def test_and_only_the_waveform(self):
        """A page that cannot be scrolled is worse than a scrubber that is
        hard to grab, so nothing else in the card says it."""
        assert card().count("touch-action") == 1


class TestThePlayingStateSurvivesTheScrub:
    def test_the_seek_neither_plays_nor_pauses(self):
        body = block_after(player(), "function seekToFraction(")
        assert "audio.play()" not in body
        assert "audio.pause()" not in body

    def test_no_pointer_handler_plays_or_pauses(self):
        text = player()
        for event in ("pointerdown", "pointermove", "pointerup", "pointercancel"):
            body = block_after(text, f"scrubTrack.addEventListener('{event}'")
            assert "play()" not in body, event
            assert "pause()" not in body, event

    def test_the_voice_driven_heights_are_left_alone(self):
        """Task 23's bars are inline heights set by the analyser's loop. The
        scrub paints classes and `left`, so a drag cannot touch them."""
        for name in ("function seekToFraction(", "function paintProgress("):
            body = block_after(player(), name)
            assert "style.height" not in body, name
            assert "analyser" not in body, name
        assert "bars[i].style.height" in block_after(player(), "function drawLevels(")


class TestTheScrubberIsReachableWithoutAFinger:
    def test_the_waveform_is_a_slider(self):
        tag = track_tag()
        assert 'role="slider"' in tag, tag

    def test_it_says_what_it_is(self):
        assert re.search(r'aria-label="[^"]+"', track_tag()), track_tag()

    def test_it_carries_its_range_and_its_position(self):
        tag = track_tag()
        for name in ("aria-valuemin", "aria-valuemax", "aria-valuenow"):
            assert f'{name}="0"' in tag, name

    def test_it_can_be_focused(self):
        assert 'tabindex="0"' in track_tag(), track_tag()

    def test_the_position_is_kept_current_in_seconds(self):
        body = block_after(player(), "function paintClock(")
        assert re.search(
            r"setAttribute\('aria-valuenow', seconds\.toFixed\(1\)\)", body
        ), body
        for caller in ("audio.addEventListener('timeupdate'", "function seekToFraction("):
            assert "paintClock(" in block_after(player(), caller), caller

    def test_the_end_of_the_range_is_the_recording_s_length(self):
        text = player()
        body = block_after(text, "function paintRange(")
        assert "setAttribute('aria-valuemax'" in body
        assert "playLength()" in body
        for event in ("loadedmetadata", "durationchange"):
            assert f"audio.addEventListener('{event}', paintRange)" in text, event

    def test_the_arrows_move_five_seconds(self):
        text = player()
        assert re.search(r"var ARROW_SECONDS = %d;" % ARROW_SECONDS, text), text
        body = block_after(text, "scrubTrack.addEventListener('keydown'")
        assert "'ArrowRight'" in body and "'ArrowLeft'" in body
        assert "step = ARROW_SECONDS" in body
        assert "step = -ARROW_SECONDS" in body
        assert re.search(r"seekToFraction\(\(audio\.currentTime \+ step\) / total\)", body)

    def test_another_key_is_left_to_the_page(self):
        body = block_after(player(), "scrubTrack.addEventListener('keydown'")
        assert "return;" in block_after(body, "} else {")
        assert body.index("e.preventDefault()") > body.index("'ArrowLeft'")


class TestWithNoRecordingItDoesNothing:
    def test_nothing_is_wired_until_there_is_a_file(self):
        """The player returns before it builds the element, so with no
        recording for the fan's key there is no scrub handler to fire."""
        text = player()
        at = text.index("if (!file)")
        for marker in (
            "new Audio(file)",
            "scrubTrack.addEventListener('pointerdown'",
            "scrubTrack.addEventListener('keydown'",
        ):
            assert text.index(marker) > at, marker

    def test_the_play_button_still_starts_disabled(self):
        assert "playBtn.disabled = true" in player()

    def test_the_scrubber_is_the_only_thing_the_card_gained(self):
        """Nothing that decides which recording plays was touched."""
        text = player()
        assert "Prelude.slotFor(" in text
        assert "match.hero && match.hero.audio" in text
        assert "voice_for" not in text
        assert "audio.src" not in text
        assert ".load()" not in text

    def test_it_still_sends_nothing_and_parses_nothing(self):
        text = player()
        for call in ("fetch(", "XMLHttpRequest", "sendBeacon", "innerHTML"):
            assert call not in text, call
