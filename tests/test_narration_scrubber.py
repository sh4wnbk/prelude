"""The waveform is a scrubber, and the opening word is not lost.

Two things were wrong with the player after Task 23.

**The first word was cut on an iPhone.** The 2022 Storyteller started at
"tina" rather than at "Argentina". The element is routed through a Web Audio
graph, and iOS hands back a suspended `AudioContext`: `audio.play()` called
before the context is running starts the element's clock into a graph that is
rendering nothing, and whatever plays in that gap is gone. So the tap asks for
`resume()` inside the gesture, waits for it, and only then plays, from the
start on the first play.

**That was one of the two causes, and Task 25 covered the other.** The order
was right afterwards and the word was still clipped on the phone, because the
audio output itself wakes a moment after `play()` starts and the opening of the
file was landing inside that wake. So every recording now opens with half a
second of silence, put in front of the spoken frames by
`scripts/pad_hero_audio.py` and copied rather than re-encoded. The digests
below moved for it, and `TestTheLeadInIsThere` is what holds the silence to
being there.

**The waveform only showed a position; it could not set one.** A click handler
read `e.clientX`, which touch gives too, but there was no drag and no keyboard.
It is now a pointer-event scrubber: `pointerdown`, `pointermove` and
`pointerup` with pointer capture, so touch and mouse share one path, with the
amber fill following the finger whether the recording is playing or paused.

Most of these are source tests, as `tests/test_narration_player.py` and
`tests/test_narration_waveform.py` are; the browser half is a run in headless
Chromium on both matches, served with Range support, and it is recorded in
`HANDOFF.md`. The exception is `TestTheLeadInIsThere`, which reads the MP3s
themselves, and it decodes nothing: it reads each frame's side information,
where a frame holding no spectral data is silence by the format's own
definition. That keeps the suite free of a dependency on an installed ffmpeg,
which `scripts/pad_hero_audio.py --check` is for.
"""

import hashlib
import json
import re
from itertools import groupby
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
PLAYER = WEB / "narration-player.js"
CARD = WEB / "prelude_03_moment_card.html"
MATCHES = WEB / "matches.json"

#: Five seconds an arrow press, which is what the card is built for.
ARROW_SECONDS = 5

#: The six recordings as they stand.
#:
#: **These digests changed in Task 25, and that was the deliberate change the
#: list existed to force.** Task 24 fixed the order of resume() and play() and
#: re-encoded nothing, so the list then held the recordings exactly as the
#: speech service wrote them. It was not enough on an iPhone: the audio output
#: wakes after play() starts and the opening word was landing inside that wake,
#: so "Argentina" still came out as "tina". Task 25 put 500 ms of silence in
#: front of every file to cover the wake, which rewrote all six.
#:
#: **The spoken audio is still what the service wrote.** The lead-in was put in
#: front of the original's frames rather than mixed into them, by
#: `scripts/pad_hero_audio.py`, and the original frames were copied through and
#: not re-encoded. So every digest here is new while every spoken sample behind
#: the lead-in is the one it always was: `--check` decodes both sides and holds
#: that, and the figures it reported are in `HANDOFF.md`.
RECORDINGS = {
    "3750191_buddy_conceded.mp3": "478f1ff283457c59146536aae61969c74784fd103e4d8b2460c3264a8eee8075",
    "3750191_buddy_scored.mp3": "07899d9ee98747e8aea44de6ffb747f419e1d31c156549abc9443384a9468be3",
    "3750191_storyteller_neutral.mp3": "b648bb4b7e7532e2833f4a8b4e7689b098855761f262bfcac90946f44272478a",
    "3869685_buddy_conceded.mp3": "011690eea45ef449136ba146217c165ccd377dae767e69a65e1931dbd1c08a1c",
    "3869685_buddy_scored.mp3": "951eb973554c307aaa0460c22585fa98b09102448cc52be9811eaaa2ee55e12e",
    "3869685_storyteller_neutral.mp3": "275355af14536dc189d1116a6b4fb1e7887b73b99f27f754a82fbcf4aaaf534e",
}

#: The lead-in each recording has to open with, in seconds. Under the 500 ms
#: `scripts/pad_hero_audio.py` asks ffmpeg for, because an MP3 frame at
#: 24000 Hz carries 576 samples and half a second is not a whole number of
#: them: the six landed on 24 frames, which is 576 ms encoded and 506 ms once
#: the decoder has taken off the encoder's delay.
LEAD_IN_SECONDS = 0.4


def whole_file():
    """The whole player file, with its line comments taken out.

    The comments say what the code does, in the same words, so a test reading
    the raw file would count the prose as well as the call. This is the helper
    `tests/test_narration_waveform.py` uses, for the same reason.
    """
    text = PLAYER.read_text(encoding="utf-8")
    return "\n".join(re.sub(r"\s*//.*$", "", line) for line in text.splitlines())


def player():
    """The player, which is `wirePlayer()` and nothing else.

    Task 32 made it one function that both screens use: the moment card and
    the Moments list hand it their own markup, and everything about playing a
    recording is inside it. Before that it was the body of `start()`, with the
    Moments list's button a second, smaller player further up the same file;
    either way a search over the whole file would answer about whichever came
    first in it, which is why this is scoped. `card_player()` below is the
    half that is still only the card's.
    """
    return block_after(whole_file(), "function wirePlayer(")


def card_player():
    """`start()`, the moment card's own half: finding the markup, working out
    which recording this fan hears and handing it to `wirePlayer`. The
    mechanics live in `wirePlayer` because the Moments list uses them too;
    what is only the card's is here."""
    return block_after(whole_file(), "function start(")


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


class TestTheRecordingsAreTheOnesPinnedHere:
    @pytest.mark.parametrize("name", sorted(RECORDINGS))
    def test_every_recording_is_byte_for_byte_the_pinned_one(self, name):
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


#: Bitrates in kbps by index, for MPEG-2 and MPEG-2.5 Layer III, and sample
#: rates by index for MPEG-2. The six recordings are all MPEG-2 Layer III at
#: 24000 Hz in one channel, which `mp3_frames` asserts rather than assumes, so
#: a recording that ever arrives in another format fails here instead of being
#: misread.
LSF_BITRATES = (
    None, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, None)
LSF_RATES = (22050, 24000, 16000, None)

#: Samples one MPEG-2 Layer III frame carries. It is half MPEG-1's 1152, which
#: is what "low sampling frequency" means, and at 24000 Hz it makes a frame
#: 24 ms long.
LSF_FRAME_SAMPLES = 576

#: Bytes of side information in an MPEG-2 Layer III frame with one channel.
LSF_MONO_SIDE_INFO = 9


def mp3_frames(data):
    """Every Layer III frame in the file, as (bytes, has_crc, sample_rate).

    An ID3v2 tag is skipped by the length in its own header, and the frames are
    then walked by the length each header gives, which is how a frame holding
    `0xFF` in its payload is not mistaken for the next header.
    """
    at = 0
    if data[:3] == b"ID3":
        # A synchsafe 32-bit length: seven bits per byte.
        at = 10 + ((data[6] << 21) | (data[7] << 14) | (data[8] << 7) | data[9])
    found = []
    while at + 4 <= len(data):
        header = data[at: at + 4]
        if header[0] != 0xFF or (header[1] & 0xE0) != 0xE0:
            at += 1
            continue
        version = (header[1] >> 3) & 0x03
        layer = (header[1] >> 1) & 0x03
        bitrate = LSF_BITRATES[(header[2] >> 4) & 0x0F]
        rate = LSF_RATES[(header[2] >> 2) & 0x03]
        channel_mode = (header[3] >> 6) & 0x03
        assert layer == 1, "not Layer III at byte {}".format(at)
        assert version == 2, "not MPEG-2 at byte {}".format(at)
        assert channel_mode == 3, "not one channel at byte {}".format(at)
        assert bitrate and rate, "no bitrate or rate at byte {}".format(at)
        size = 72 * bitrate * 1000 // rate + ((header[2] >> 1) & 0x01)
        # Bit 0 of the second header byte is the protection bit, and it is low
        # when a 16-bit CRC sits between the header and the side information.
        found.append((data[at: at + size], not header[1] & 0x01, rate))
        at += size
    return found


def carries_no_sound(frame, has_crc):
    """Whether this frame holds no spectral data at all, which is silence.

    `part2_3_length` is the number of main-data bits the granule was given and
    `big_values` is how many spectral value pairs it coded. Both zero means the
    frame describes no sound, so the decoder puts out zeros: it is silence by
    the format's own account of itself, not a level compared against a
    threshold. The two fields sit at a fixed place in the side information, so
    reading them needs no decoder and no library.
    """
    side = frame[4 + (2 if has_crc else 0):]
    assert len(side) >= LSF_MONO_SIDE_INFO, "the frame is short of side info"
    position = 0

    def take(count):
        nonlocal position
        value = 0
        for _ in range(count):
            byte = side[position >> 3]
            value = (value << 1) | ((byte >> (7 - (position & 7))) & 1)
            position += 1
        return value

    take(8)   # main_data_begin, the bit reservoir pointer
    take(1)   # private_bits, one of them with a single channel
    part2_3_length = take(12)
    big_values = take(9)
    return part2_3_length == 0 and big_values == 0


class TestTheLeadInIsThere:
    """Every recording opens with silence, because the phone's output wakes
    after `play()` starts and the first word was landing inside that wake."""

    @pytest.mark.parametrize("name", sorted(RECORDINGS))
    def test_it_opens_with_at_least_four_hundred_milliseconds_of_silence(
            self, name):
        frames = mp3_frames((WEB / "assets" / "audio" / name).read_bytes())
        assert frames, name
        silent = 0
        for frame, has_crc, _rate in frames:
            if not carries_no_sound(frame, has_crc):
                break
            silent += 1
        rate = frames[0][2]
        seconds = silent * LSF_FRAME_SAMPLES / rate
        assert seconds >= LEAD_IN_SECONDS, (
            "{}: {:.3f} s of opening silence, under the {:.1f} s the phone "
            "needs".format(name, seconds, LEAD_IN_SECONDS))

    @pytest.mark.parametrize("name", sorted(RECORDINGS))
    def test_the_narration_still_follows_the_silence(self, name):
        """A file of nothing but silence would pass the test above."""
        frames = mp3_frames((WEB / "assets" / "audio" / name).read_bytes())
        speaking = [one for one, has_crc, _rate in frames
                    if not carries_no_sound(one, has_crc)]
        assert len(speaking) > 500, "{}: only {} frames carry sound".format(
            name, len(speaking))

    @pytest.mark.parametrize("name", sorted(RECORDINGS))
    def test_the_lead_in_is_the_longest_silence_in_the_file(self, name):
        """A narration has pauses in it, and the longest of those reaches
        408 ms, so silence inside the file is not a fault. The lead-in being
        the longest run of it, and the first, is what says the half second was
        put in front of the narration rather than opened up inside it."""
        frames = mp3_frames((WEB / "assets" / "audio" / name).read_bytes())
        runs = [(silent, len(list(group))) for silent, group in groupby(
            carries_no_sound(one, has_crc) for one, has_crc, _rate in frames)]
        silences = [length for silent, length in runs if silent]
        assert runs[0][0], "{}: the file does not open with silence".format(name)
        assert runs[0][1] == max(silences), (
            "{}: the opening silence is {} frames and a later one reaches "
            "{}".format(name, runs[0][1], max(silences)))
    def test_it_listens_for_the_three_pointer_events(self):
        text = player()
        for event in ("pointerdown", "pointermove", "pointerup"):
            assert f"track.addEventListener('{event}'" in text, event

    def test_touch_and_mouse_share_one_path(self):
        """Pointer events cover both, so the click handler that used to read
        `e.clientX` is gone and there is no touch handler beside it."""
        text = player()
        assert "track.addEventListener('click'" not in text
        for event in ("touchstart", "touchmove", "touchend", "mousedown"):
            assert event not in text, event

    def test_the_drag_is_captured(self):
        body = block_after(player(), "track.addEventListener('pointerdown'")
        assert "setPointerCapture(e.pointerId)" in body
        assert "releasePointerCapture" in player()

    def test_a_move_without_a_drag_does_nothing(self):
        body = block_after(player(), "track.addEventListener('pointermove'")
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
            body = block_after(text, f"track.addEventListener('{event}'")
            assert "seekToFraction(fractionAtX(e.clientX))" in body, event
        assert "endScrub(e, true)" in block_after(
            text, "track.addEventListener('pointerup'"
        )

    def test_a_cancelled_gesture_leaves_the_playhead_where_it_got_to(self):
        text = player()
        assert "endScrub(e, false)" in block_after(
            text, "track.addEventListener('pointercancel'"
        )


class TestTheDragDoesNotScrollThePage:
    def test_the_handlers_refuse_the_default(self):
        text = player()
        for event in ("pointerdown", "pointermove"):
            body = block_after(text, f"track.addEventListener('{event}'")
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
            body = block_after(text, f"track.addEventListener('{event}'")
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
        # The constant is at the top of the file rather than inside the
        # player: both screens' scrubbers move by the same five seconds.
        text = whole_file()
        assert re.search(r"var ARROW_SECONDS = %d;" % ARROW_SECONDS, text), text
        body = block_after(text, "track.addEventListener('keydown'")
        assert "'ArrowRight'" in body and "'ArrowLeft'" in body
        assert "step = ARROW_SECONDS" in body
        assert "step = -ARROW_SECONDS" in body
        assert re.search(r"seekToFraction\(\(audio\.currentTime \+ step\) / total\)", body)

    def test_another_key_is_left_to_the_page(self):
        body = block_after(player(), "track.addEventListener('keydown'")
        assert "return;" in block_after(body, "} else {")
        assert body.index("e.preventDefault()") > body.index("'ArrowLeft'")


class TestWithNoRecordingItDoesNothing:
    def test_nothing_is_wired_until_there_is_a_file(self):
        """The card returns before it hands anything over, so with no
        recording for the fan's key there is no scrub handler to fire.

        The handlers are in `wirePlayer` now and the card reaches them by
        calling it, so what is asked here is that the call comes after the
        refusal: nothing is wired at all on a fan whose slot has no file.
        """
        text = card_player()
        at = text.index("if (!file)")
        assert text.index("wirePlayer({") > at
        assert text.count("wirePlayer({") == 1

    def test_the_play_button_still_starts_disabled(self):
        assert "playBtn.disabled = true" in card_player()

    def test_the_scrubber_is_the_only_thing_the_card_gained(self):
        """Nothing that decides which recording plays was touched."""
        text = card_player()
        assert "Prelude.slotFor(" in text
        assert "match.hero && match.hero.audio" in text
        assert "voice_for" not in text
        assert "audio.src" not in text
        assert ".load()" not in text

    def test_it_still_sends_nothing_and_parses_nothing(self):
        text = player()
        for call in ("fetch(", "XMLHttpRequest", "sendBeacon", "innerHTML"):
            assert call not in text, call
