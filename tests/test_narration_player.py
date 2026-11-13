"""Acceptance tests for audio playback on the moment card, written before it exists.

The moment card's player is a mock: the play button swaps its icon and plays
nothing, and the waveform shows a fixed progress. Bob's Task 11 in
`docs/bob_brief.md` wires it to real audio.

Which recording a fan hears is decided the way the header is: in Python,
ahead of time, by the orchestrator. `default_persona` picks the voice from the
listener's side and `app/delivery.py`'s `situation` picks the delivery, so
`scripts/write_headers.py` writes `hero.voice_for`, one key per possible
answer to "Who are you with", and the browser only looks its answer up. No
rule about personas is written twice.

A fan may choose a narrator since Task 14, and the choice is read in the same
one place: `Prelude.slotFor` answers with the side rule until the fan has
chosen, and with the chosen narrator's own key after. No rule about personas is
written twice and no rule about the choice is either.

`hero.audio` maps those keys to files. It is empty until the hero audio is
generated after the November 1 TTS reset, and the player has to cope with
that: with no file for the fan's key, the play button is disabled.
"""

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
MATCHES = WEB / "matches.json"
SCRIPT = ROOT / "scripts" / "write_headers.py"
CARD = WEB / "prelude_03_moment_card.html"
PLAYER = WEB / "narration-player.js"

#: For both heroes Argentina scored, so a fan of Argentina hears the Buddy
#: delivering a goal for their side, a fan of the other team hears the Buddy
#: delivering one against it, and a listener with no side hears the
#: Storyteller. Literals, produced by the orchestrator's own rules.
EXPECTED = {
    3750191: {"team_a": "buddy_scored", "team_b": "buddy_conceded",
              "neutral": "storyteller_neutral"},
    3869685: {"team_a": "buddy_scored", "team_b": "buddy_conceded",
              "neutral": "storyteller_neutral"},
}


def heroes():
    doc = json.loads(MATCHES.read_text(encoding="utf-8"))
    return {entry["match_id"]: entry["hero"] for entry in doc["matches"]}


def script():
    spec = importlib.util.spec_from_file_location("write_headers", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "voice_keys"):
        pytest.fail(
            "scripts/write_headers.py has no voice_keys() yet. It is Task 11 "
            "in docs/bob_brief.md."
        )
    return module


def player():
    if not PLAYER.exists():
        pytest.fail(
            "app/web/narration-player.js does not exist yet. It is Task 11 in "
            "docs/bob_brief.md."
        )
    return PLAYER.read_text(encoding="utf-8")


class TestWhichRecordingIsHeard:
    def test_the_script_computes_it(self):
        assert script().voice_keys() == EXPECTED

    def test_the_1986_hero_carries_it(self):
        assert heroes()[3750191].get("voice_for") == EXPECTED[3750191]

    def test_the_2022_hero_carries_it(self):
        assert heroes()[3869685].get("voice_for") == EXPECTED[3869685]

    def test_check_fails_when_it_drifts(self, tmp_path):
        script()
        copy = tmp_path / "matches.json"
        shutil.copy(MATCHES, copy)
        doc = json.loads(copy.read_text(encoding="utf-8"))
        for entry in doc["matches"]:
            entry["hero"]["voice_for"] = {"team_a": "caller_scored"}
        copy.write_text(json.dumps(doc), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--check", "--path", str(copy)],
            cwd=ROOT, capture_output=True, text=True,
        )
        assert result.returncode == 1, result.stdout + result.stderr


class TestTheAudioMap:
    @pytest.mark.parametrize("match_id", sorted(EXPECTED))
    def test_every_entry_is_a_file_that_exists(self, match_id):
        hero = heroes()[match_id]
        audio = hero.get("audio")
        assert isinstance(audio, dict), "hero.audio must be an object, empty for now"
        for key, path in audio.items():
            assert key in hero["voice_for"].values(), key
            assert path.startswith("assets/audio/"), path
            assert (WEB / path).is_file(), path


class TestTheMomentCard:
    def test_it_loads_the_player(self):
        assert '<script src="narration-player.js?v=__V__"></script>' in CARD.read_text(
            encoding="utf-8"
        )

    def test_the_mock_toggle_is_gone(self):
        assert "togglePlay" not in CARD.read_text(encoding="utf-8")

    def test_no_other_screen_loads_the_player(self):
        for page in sorted(WEB.glob("*.html")):
            if page == CARD:
                continue
            assert "narration-player.js" not in page.read_text(encoding="utf-8"), page.name


#: The renderer, which is where the narration reveal and so the button's
#: release are written.
RENDERER = WEB / "match-content.js"


def renderer():
    return RENDERER.read_text(encoding="utf-8")


def one_function(text, name):
    """The body of `function name(` in `text`, by matching its braces.

    A test that searched the whole file could not tell the one release of the
    button from a second one somewhere else, which is the thing these tests
    are about. The same two-helper shape is in
    `tests/test_frozen_narrations.py` and for the same reason.
    """
    start = text.index("function " + name + "(")
    opened = text.index("{", start)
    depth = 0
    for i in range(opened, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[opened:i + 1]
    raise AssertionError("function " + name + " has unbalanced braces")


class TestThePlayButtonWaitsForTheWords:
    """Shawn, 2026-11-12: the card and the voice are one piece of writing, so
    the button is not offered while the paragraph above it is blank.

    `hero.audio` lands with `matches.json` and the narration lands with a
    second fetch of `narrations.json`, so with the second one slow the card
    used to show no words and no label and an enabled play button. Nothing
    false was said, because the label is about the words and the words were
    absent, but half of one piece of writing was on screen. The button now
    waits for the other half.

    The reveal and the release are one step: `showNarration` sets the text,
    shows the paragraph, shows the label and fires `whenNarrationShown`, which
    is what the player subscribes to. Nothing else fires it, so a
    `narrations.json` that fails, that holds no entry for this match or that
    holds no text for this listener's slot leaves the button as the markup
    ships it.
    """

    def test_the_renderer_offers_the_subscription(self):
        assert "whenNarrationShown: whenNarrationShown" in renderer()

    def test_the_player_subscribes_to_it(self):
        assert "Prelude.whenNarrationShown(" in player()

    def test_the_player_releases_the_button_nowhere_else(self):
        """One release, inside the subscription. `playBtn.disabled = false`
        anywhere outside it would be the old behaviour under a new name."""
        text = player()
        assert text.count("playBtn.disabled = false") == 1
        subscription = text.index("Prelude.whenNarrationShown(")
        release = text.index("playBtn.disabled = false")
        assert release > subscription
        closing = text.index("});", release)
        assert closing > release

    def test_the_renderer_fires_it_from_the_reveal(self):
        """In `showNarration`, beside the two `removeProperty` calls that show
        the paragraph and the label, so the three arrive together."""
        body = one_function(renderer(), "showNarration")
        assert "announceNarration()" in body
        assert body.count("removeProperty") == 2

    def test_nothing_else_in_the_renderer_fires_it(self):
        """One call, the one in `showNarration`. The other occurrence of the
        name is its own definition, which is not a call."""
        text = renderer()
        calls = text.count("announceNarration()") - text.count(
            "function announceNarration()"
        )
        assert calls == 1

    def test_a_failing_fetch_leaves_the_button_disabled(self):
        """The catch arm reveals nothing, so it announces nothing."""
        body = one_function(renderer(), "renderNarration")
        catch = body[body.index(".catch("):]
        assert "announceNarration" not in catch
        assert "showNarration" not in catch

    def test_the_subscription_survives_either_order(self):
        """The two fetches can land in either order, so the subscription
        answers a late caller as well as an early one: it holds the callback
        while the narration has not been shown and calls it at once after."""
        body = one_function(renderer(), "whenNarrationShown")
        assert "narrationShown" in body
        assert "callback()" in body
        assert "narrationWaiting.push(callback)" in body


class TestThePlayer:
    def test_it_looks_up_the_fans_recording(self):
        """Which recording is `Prelude.slotFor`'s answer since Task 14: the
        side rule by default, and the narrator the fan chose when they have
        chosen one. The player no longer indexes `hero.voice_for` itself,
        because the moment card's words come from the same lookup and the two
        have to agree. `tests/test_narrator_picker.py` holds it."""
        text = player()
        assert "Prelude.slotFor(" in text
        assert "voice_for" not in text

    def test_it_reads_the_list_out_of_the_document(self):
        """`Prelude.whenMatches` passes the whole document, or null, not the
        list. Bob's Task 11 treated it as the list, so the loop never ran and
        the play button stayed disabled even with a recording; a browser run
        with a test file caught it."""
        text = player()
        found = re.search(r"whenMatches\(function \((\w+)\)", text)
        assert found, "whenMatches is not called with a named function argument"
        name = found.group(1)
        assert f"if (!{name})" in text
        assert f"{name}.matches" in text

    def test_it_disables_play_with_no_recording(self):
        assert "playBtn.disabled = true" in player()

    def test_it_follows_the_audio(self):
        text = player()
        for name in ("timeupdate", "ended", "currentTime", "duration"):
            assert name in text, name

    def test_replay_goes_back_ten_seconds(self):
        assert re.search(r"currentTime\s*-\s*10", player())

    def test_it_sends_nothing_and_parses_nothing(self):
        text = player()
        for call in ("fetch(", "XMLHttpRequest", "sendBeacon", "innerHTML"):
            assert call not in text, call
