"""The opening word of the narration is not lost.

**The first word was cut on an iPhone.** The 2022 Storyteller started at
"tina" rather than at "Argentina". The element is routed through a Web Audio
graph, and iOS hands back a suspended `AudioContext`: `audio.play()` called
before the context is running starts the element's clock into a graph that is
rendering nothing, and whatever plays in that gap is gone. So the tap asks for
`resume()` inside the gesture, waits for it, and only then plays, from the
start on the first play.

These are source tests, as `tests/test_narration_player.py` and
`tests/test_narration_waveform.py` are; the browser half is a run in headless
Chromium on both matches and it is recorded in `HANDOFF.md`.
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
