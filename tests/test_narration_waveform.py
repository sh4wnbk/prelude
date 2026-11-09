"""The moment card's waveform bars follow the real audio.

Before this, the waveform was a progress bar: the bar heights were fixed in
the markup and the amber fill ran left to right with the clock. The film's
listening shot shows bars that move with the voice, and the condition was that
the app ships the same thing.

So `app/web/narration-player.js` puts the Audio element through a Web Audio
analyser and sets each bar's height from its levels while the narration plays.
Three things about that are easy to get wrong and are what these tests hold.

The context has to be created and resumed inside the tap, because iOS starts
every AudioContext suspended and resumes one only on a user gesture. The
element has to reach the destination through the analyser, because a capture
that connects to nothing is silence rather than a quiet visualiser. And the
source node has to be made once per element, because a second
`createMediaElementSource` on the same element throws and takes the sound with
it, which a fan would meet on the second tap rather than the first.

Everything Web Audio adds is optional. With no `AudioContext`, or if any of
the wiring throws, the player keeps what it did before: fixed bars, the amber
fill as progress, and the narration playing. These are source tests, as the
rest of `tests/test_narration_player.py` is; the browser half of the check is
a run in headless Chromium on both matches, recorded in `HANDOFF.md`.
"""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
PLAYER = WEB / "narration-player.js"
CARD = WEB / "prelude_03_moment_card.html"


def player():
    """The player's code, with its line comments taken out.

    The comments say what the code does, in the same words, so a test reading
    the raw file would count the prose as well as the call. There is no `//`
    inside a string literal in this file.
    """
    text = PLAYER.read_text(encoding="utf-8")
    return "\n".join(re.sub(r"\s*//.*$", "", line) for line in text.splitlines())


def block_after(text, marker):
    """The brace-balanced block that opens after `marker`.

    Reading a handler's own body is the only way to tell "the context is
    created inside the tap" from "the context is created somewhere in this
    file", which is the whole point of step 1.
    """
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


def opener():
    return block_after(player(), "function openAnalyser(")


def play_handler():
    return block_after(player(), "playBtn.addEventListener('click'")


class TestTheContextIsOpenedInTheTap:
    def test_the_play_tap_opens_it(self):
        assert "openAnalyser()" in play_handler()

    def test_the_tap_is_the_only_thing_that_opens_it(self):
        """Not at load: a context created before any gesture is a context iOS
        leaves suspended, and the narration would play with dead bars."""
        text = player()
        calls = re.findall(r"(?<!function )openAnalyser\(\)", text)
        assert len(calls) == 2, f"openAnalyser() is called {len(calls)} times"
        assert "openAnalyser()" in play_handler()
        assert "openAnalyser()" in block_after(
            text, "replayAction.addEventListener('click'"
        )

    def test_the_context_is_built_there_and_nowhere_else(self):
        text = player()
        assert re.search(r"new Ctx\(", opener()), "the opener does not construct one"
        built = re.findall(
            r"new\s+(?:Ctx|AudioContext|webkitAudioContext)\s*\(", text
        )
        assert len(built) == 1, built

    def test_it_resumes_a_suspended_context_inside_the_tap(self):
        """Task 24 moved the resume out of the opener and into
        `resumeContext`, which the tap calls and then waits on before play().
        It is still asked for inside the gesture, which is the part iOS cares
        about, and `tests/test_narration_scrubber.py` holds the waiting."""
        body = block_after(player(), "function resumeContext(")
        assert "suspended" in body
        assert ".resume()" in body
        assert "resumeContext()" in play_handler()


class TestTheSoundStillReachesTheSpeakers:
    def test_the_element_goes_through_the_analyser(self):
        body = opener()
        assert "createMediaElementSource(audio)" in body
        assert "createAnalyser()" in body
        assert re.search(r"src\.connect\(\s*node\s*\)", body)

    def test_the_analyser_goes_on_to_the_destination(self):
        assert re.search(r"node\.connect\(\s*ctx\.destination\s*\)", opener())

    def test_a_capture_that_fails_late_is_still_connected(self):
        """If the element is captured and then the wiring throws, the sound is
        inside a graph that goes nowhere. The catch sends it to the
        destination, so a failure costs the bars and not the narration."""
        failure = block_after(opener(), "catch (err)")
        assert re.search(r"src\.connect\(\s*ctx\.destination\s*\)", failure)


class TestOneSourceNodePerElement:
    def test_the_element_is_captured_once(self):
        text = player()
        assert text.count("createMediaElementSource") == 1
        assert text.count("new Audio(") == 1

    def test_replay_reuses_what_the_first_tap_made(self):
        body = opener()
        assert re.search(r"if\s*\(audioCtx\s*\|\|\s*webAudioOff\)", body), body
        assert "return;" in block_after(body, "if (audioCtx || webAudioOff)")


class TestTheAudioSession:
    def test_it_asks_for_playback_where_the_session_exists(self):
        text = player()
        assert "navigator.audioSession" in text
        assert re.search(
            r"navigator\.audioSession\.type\s*=\s*'playback'", text
        ), "the session type is not set to playback"

    def test_it_is_guarded_and_cannot_throw(self):
        body = block_after(player(), "function claimPlaybackSession(")
        assert "if (navigator.audioSession)" in body
        assert "try {" in body
        assert "catch" in body

    def test_the_tap_asks_before_the_context_is_built(self):
        body = opener()
        assert "claimPlaybackSession()" in body
        assert body.index("claimPlaybackSession()") < body.index("new Ctx(")


class TestItFallsBackWithoutWebAudio:
    def test_no_audio_context_is_not_an_error(self):
        body = opener()
        assert "window.AudioContext || window.webkitAudioContext" in body
        assert "if (!Ctx)" in body
        assert "return;" in block_after(body, "if (!Ctx)")

    def test_the_wiring_is_wrapped(self):
        body = opener()
        assert body.index("try {") < body.index("createMediaElementSource")
        assert "catch (err)" in body

    def test_the_frames_stop_at_a_missing_analyser(self):
        body = block_after(player(), "function drawLevels(")
        assert "if (!analyser" in body

    def test_the_progress_fill_does_not_depend_on_any_of_it(self):
        """The fill is classes on the bars and the heights are inline styles,
        so the fallback keeps the fill the player always had."""
        body = block_after(player(), "audio.addEventListener('timeupdate'")
        assert "bg-primary-container" in body
        assert "style.height" not in body
        assert "analyser" not in body


class TestTheBarsFollowTheVoice:
    def test_it_reads_levels_every_frame(self):
        body = block_after(player(), "function drawLevels(")
        assert "getByteFrequencyData(levels)" in body
        assert "window.requestAnimationFrame(drawLevels)" in body

    def test_the_height_comes_from_the_level(self):
        body = block_after(player(), "function drawLevels(")
        assert re.search(r"bars\[i\]\.style\.height", body)
        assert "REST_MIN_PX" in body and "REST_MAX_PX" in body

    def test_the_frames_start_when_the_audio_does(self):
        body = block_after(player(), "audio.addEventListener('play'")
        assert "requestAnimationFrame(drawLevels)" in body
        assert "!frame" in body, "a second play would start a second loop"


class TestTheBarsRest:
    def test_pause_rests_them(self):
        assert "restBars()" in block_after(
            player(), "audio.addEventListener('pause'"
        )

    def test_the_end_rests_them(self):
        assert "restBars()" in block_after(
            player(), "audio.addEventListener('ended'"
        )

    def test_resting_cancels_the_loop_and_clears_the_override(self):
        body = block_after(player(), "function restBars(")
        assert "cancelAnimationFrame(frame)" in body
        assert "frame = 0" in body
        assert re.search(r"bar\.style\.height\s*=\s*''", body)

    def test_the_markup_still_says_where_rest_is(self):
        """Clearing the inline height hands a bar back to its class, so the
        heights in the card are what the bars return to."""
        heights = re.findall(
            r'class="w-\[3px\] (h-[0-9.]+) ', CARD.read_text(encoding="utf-8")
        )
        assert len(heights) == 24, len(heights)
        assert len(set(heights)) > 1, "the resting heights are all the same"


class TestNothingAboutTheRecordingChanged:
    def test_the_player_still_picks_the_file_the_same_way(self):
        text = player()
        assert "Prelude.slotFor(" in text
        assert "match.hero && match.hero.audio" in text
        assert "voice_for" not in text

    def test_it_never_repoints_the_element(self):
        text = player()
        assert "audio.src" not in text
        assert ".load()" not in text
