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
MOMENTS = WEB / "prelude_04_moments.html"
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

    def test_only_the_two_screens_that_play_audio_load_the_player(self):
        """The moment card and the Moments list, and no others.

        It was the moment card alone until Task 30. The Moments cards carried
        play buttons that did nothing, and the hero goal's card now plays the
        recording this fan would hear on the moment card. A second player
        would be a second answer to which recording that is, so the Moments
        screen loads this one.
        """
        plays = {CARD.name, MOMENTS.name}
        for page in sorted(WEB.glob("*.html")):
            loads = "narration-player.js" in page.read_text(encoding="utf-8")
            assert loads == (page.name in plays), page.name

    def test_the_moments_screen_loads_it_after_the_renderer(self):
        """The player registers for the Moments cards as the head is read, and
        the thing it registers with is defined by `match-content.js`."""
        markup = MOMENTS.read_text(encoding="utf-8")
        assert markup.index("match-content.js") < markup.index("narration-player.js")


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

    def test_the_button_ships_disabled_in_the_markup(self):
        """Not only disabled by the player. `tests/browser/` caught this: the
        card's first frame, before `start()` has run, had an enabled button
        over a blank paragraph, and a button a fan can press before its
        handler is attached does nothing when they do.
        """
        found = re.search(
            r'<button[^>]*id="playBtn"[^>]*>', CARD.read_text(encoding="utf-8")
        )
        assert found, "the card has no play button"
        assert " disabled " in found.group(0), found.group(0)
        assert "disabled:opacity-40" in found.group(0), found.group(0)

    def test_the_renderer_offers_the_subscription(self):
        assert "whenNarrationShown: whenNarrationShown" in renderer()

    def test_the_player_subscribes_to_it(self):
        """The card hands `whenNarrationShown` to the player as the thing
        that says when the button may be pressed. Task 32 made that an
        argument, because the Moments cards answer the same question
        differently: their words are the card's own title and body, which are
        already on screen."""
        text = player()
        assert "whenReady: Prelude.whenNarrationShown" in text

    def test_the_player_releases_the_button_nowhere_else(self):
        """One release, inside the callback the caller subscribes with.
        `playBtn.disabled = false` anywhere outside it would be the old
        behaviour under a new name."""
        text = player()
        assert text.count("playBtn.disabled = false") == 1
        subscription = text.index("opts.whenReady(")
        release = text.index("playBtn.disabled = false")
        assert release > subscription
        closing = text.index("});", release)
        assert closing > release

    def test_the_moments_cards_do_not_wait_for_a_narration(self):
        """The one screen that does not have the moment card's second fetch.
        Its answer is to release at once, written out rather than left as a
        missing argument, so the two are read side by side."""
        body = one_function(player(), "playOnly")
        assert "whenReady: function (release) { release(); }" in body
        assert "whenNarrationShown" not in body

    def test_the_renderer_fires_it_from_the_reveal(self):
        """In `showNarration`, beside the three `removeProperty` calls that
        show the paragraph, the label and the claim count, so the four arrive
        together. Task 32 added the count and the third call with it."""
        body = one_function(renderer(), "showNarration")
        assert "announceNarration()" in body
        assert body.count("removeProperty") == 3

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


class TestTheMomentsHeroCardPlays:
    """Shawn, 2026-11-12: the Moments play buttons were plain buttons that did
    nothing.

    One moment per match has a recording, the hero goal, and the fan has
    already been told which voice is theirs. So the hero goal's card plays the
    file the moment card would play them, by the one lookup both screens
    share, and every other card's button is disabled rather than offering
    audio that was never recorded.

    `app/web/match-content.js` builds those cards and holds the lookup, so it
    decides which button has a file; `app/web/narration-player.js` is handed
    that button and does the playing. The division is the one the two screens
    already have: markup and copy in the renderer, audio in the player.
    """

    @staticmethod
    def matches():
        return json.loads(MATCHES.read_text(encoding="utf-8"))["matches"]

    def test_both_buttons_ship_disabled(self):
        """A button that can promise audio before the fetch lands is a button
        that can promise the wrong thing, or nothing. Neither is offered until
        something hands it a file."""
        markup = MOMENTS.read_text(encoding="utf-8")
        buttons = re.findall(r"<button[^>]*data-field=\"moment_play\"[^>]*>", markup)
        assert len(buttons) == 2, buttons
        for button in buttons:
            assert " disabled " in button or button.endswith("disabled>"), button

    def test_the_shipped_labels_promise_nothing(self):
        """Both buttons ship disabled, so in the state where the fetch fails
        and the inline copy stands, neither of them can be pressed and neither
        says it can be."""
        markup = MOMENTS.read_text(encoding="utf-8")
        labels = re.findall(r'<button[^>]*data-field="moment_play"[^>]*>', markup)
        for button in labels:
            found = re.search(r'aria-label="([^"]*)"', button)
            assert found, button
            assert found.group(1).endswith(": no narration recorded"), found.group(1)

    def test_the_renderer_names_each_card_in_its_own_label(self):
        """The cards are clones of the two inline templates, so without this
        the 2022 screen's buttons name Maradona over Messi and Di Maria."""
        body = one_function(renderer(), "wireMomentPlay")
        assert 'setAttribute(' in body
        assert '"aria-label"' in body
        assert "moment.title" in body

    def test_the_renderer_finds_the_file_by_the_one_lookup(self):
        body = one_function(renderer(), "renderMoments")
        assert "slotFor(match)" in body
        assert "match.hero && match.hero.audio" in body

    def test_the_renderer_hands_over_only_the_hero_card(self):
        body = one_function(renderer(), "wireMomentPlay")
        assert "isHeroMoment(match, moment)" in body
        assert "button.disabled = true" in body
        assert "if (!file) return;" in body

    def test_the_player_takes_the_button_and_enables_it(self):
        """It takes the button, the icon, the file, the bars and the clock,
        and hands them to the one player. The recording is built inside
        `wirePlayer`, which is why `new Audio(` is there and not here: there
        is one of them in the file and both screens reach it."""
        text = player()
        assert "Prelude.onMomentPlay(playOnly)" in text
        body = one_function(text, "playOnly")
        assert "function playOnly(button, icon, file, track, clock)" in text
        assert "wirePlayer({" in body
        assert "file: file" in body
        assert "playBtn: button" in body
        assert text.count("new Audio(") == 1

    def test_the_player_registers_outside_start(self):
        """`start()` returns at once on the Moments screen, which has none of
        the moment card's five elements, so the registration cannot be inside
        it."""
        text = player()
        assert "Prelude.onMomentPlay(playOnly)" in text
        assert "Prelude.onMomentPlay(playOnly)" not in one_function(text, "start")

    def test_the_player_holds_no_second_copy_of_the_slot_rule(self):
        assert "voice_for" not in player()

    def test_exactly_one_moment_per_match_is_the_hero(self):
        """What `isHeroMoment` rests on: the hero event is written twice in
        `app/web/matches.json`, as `hero.event` and once in the moments list,
        and the clock tells it from the other moments."""
        for entry in self.matches():
            hero = entry["hero"]["event"]
            same = [
                moment for moment in entry["moments"]
                if (moment["event"]["period"], moment["event"]["minute"],
                    moment["event"]["second"])
                == (hero["period"], hero["minute"], hero["second"])
            ]
            assert len(same) == 1, (entry["match_id"], len(same))

    def test_the_other_moments_have_no_recording(self):
        """`hero.audio` holds files for the hero goal's slots and for nothing
        else, which is why every other card's button is disabled rather than
        waiting on a file that might arrive."""
        for entry in self.matches():
            keys = set(entry["hero"]["audio"])
            assert keys == set(entry["hero"]["voice_for"].values()), entry["match_id"]
            assert len(entry["moments"]) > 1, entry["match_id"]

    @pytest.mark.parametrize("match_id", sorted(EXPECTED))
    def test_the_hero_card_plays_the_moment_cards_file(self, match_id):
        """The same file for the same fan, because both screens reach it
        through `Prelude.slotFor` and `hero.audio`. The rows of the slot rule
        are in `tests/slot_rows.json`; this holds the three side answers with
        no narrator chosen."""
        hero = heroes()[match_id]
        for side, slot in EXPECTED[match_id].items():
            assert hero["voice_for"][side] == slot
            assert hero["audio"][slot].startswith("assets/audio/")
            assert (WEB / hero["audio"][slot]).is_file()


class TestTheMomentsWaveformFollowsTheVoice:
    """The hero card's bars move with the recording and scrub, and the rest
    do not move at all.

    Task 30 wired the hero card's button and left this as "Found, not fixed":
    the card played and nothing on it followed the voice, so a fan who had
    seen the moment card could expect the bars to move and be wrong. There is
    one player in `app/web/narration-player.js` now, `wirePlayer`, and both
    screens hand it their own markup, so the Moments bars follow the voice by
    the same analyser and scrub by the same pointer and key handlers.

    **A card with no recording is left exactly as it ships.** Nothing is
    handed over for it, so its bars keep the heights the markup gives them,
    its track is not a slider and there is nothing on it to focus. A disabled
    control that a keyboard can still reach is a control that says it does
    something.
    """

    def templates(self):
        """The two inline cards the renderer clones, as raw markup."""
        markup = MOMENTS.read_text(encoding="utf-8")
        found = re.findall(
            r'<div class="h-6 w-full flex items-end[^>]*>', markup
        )
        assert len(found) == 2, found
        return found

    def test_both_templates_carry_a_track(self):
        for tag in self.templates():
            assert 'data-field="moment_track"' in tag, tag

    def test_both_templates_carry_a_clock(self):
        markup = MOMENTS.read_text(encoding="utf-8")
        assert markup.count('data-field="moment_time"') == 2

    def test_the_clock_ships_empty(self):
        """It is one of the empty placeholders Phase 2 left. The player fills
        it, and a card with no recording still shows nothing rather than a
        time it does not have."""
        markup = MOMENTS.read_text(encoding="utf-8")
        assert markup.count('data-field="moment_time"></span>') == 2

    def test_no_template_ships_as_a_slider(self):
        """The markup is the state a card with no recording stays in, so the
        slider is added by the player and only to the card it takes."""
        for tag in self.templates():
            for attribute in ("role=", "tabindex=", "aria-value", "touch-action"):
                assert attribute not in tag, (attribute, tag)

    def test_the_renderer_hands_the_track_and_the_clock_over(self):
        body = one_function(renderer(), "wireMomentPlay")
        assert 'field("moment_track", card)' in body
        assert 'field("moment_time", card)' in body

    def test_the_renderer_hands_nothing_over_without_a_file(self):
        """The same refusal the button rests on: `if (!file) return;` comes
        before the hand over, so a card with no recording reaches no handler
        at all."""
        body = one_function(renderer(), "wireMomentPlay")
        assert body.index("if (!file) return;") < body.index("momentPlayHandlers[h](")

    def test_the_player_makes_the_track_a_slider(self):
        body = one_function(player(), "playOnly")
        for attribute in ("'role', 'slider'", "'tabindex', '0'", "'aria-valuemin'",
                          "'aria-valuemax'", "'aria-valuenow'"):
            assert attribute in body, attribute

    def test_the_slider_says_what_it_is(self):
        """The same accessible name the moment card's scrubber carries, so
        the two read alike to a screen reader."""
        body = one_function(player(), "playOnly")
        assert "'aria-label', 'Narration position in seconds'" in body
        card = CARD.read_text(encoding="utf-8")
        assert 'aria-label="Narration position in seconds"' in card

    def test_the_track_takes_the_touch_itself(self):
        body = one_function(player(), "playOnly")
        assert "track.style.touchAction = 'none'" in body

    def test_the_player_refuses_a_card_with_no_track(self):
        """`wireMomentPlay` hands over whatever the card has, and a card
        without the markup is not one to wire: the button stays disabled
        rather than being offered with nothing behind it."""
        body = one_function(player(), "playOnly")
        assert "button.disabled = true;" in body
        at = body.index("if (!track) {")
        assert body.index("return;", at) < body.index("wirePlayer({")

    def test_the_bars_it_hands_over_are_the_ones_in_the_markup(self):
        """`w-1` on the Moments cards and `w-[3px]` on the moment card, each
        read off its own track rather than off the document."""
        body = one_function(player(), "playOnly")
        assert "track.querySelectorAll('div.w-1')" in body
        markup = MOMENTS.read_text(encoding="utf-8")
        assert 'class="w-1 bg-primary-container rounded-full' in markup

    def test_the_rest_colour_is_the_one_in_the_markup(self):
        """The Moments bars rest on `bg-secondary-container` and the moment
        card's on the same at 70%, so the two are arguments rather than
        literals inside the player."""
        body = one_function(player(), "playOnly")
        assert "restClass: 'bg-secondary-container'" in body
        assert "playedClass: 'bg-primary-container'" in body
        card_half = player()[player().index("function start("):]
        assert "restClass: 'bg-secondary-container/70'" in card_half

    def test_there_is_one_player_and_both_screens_use_it(self):
        text = player()
        assert text.count("function wirePlayer(") == 1
        assert text.count("wirePlayer({") == 2
        # One capture of one element. The other mention of the name is the
        # comment saying why a second one would take the sound with it.
        assert text.count("createMediaElementSource(audio)") == 1
