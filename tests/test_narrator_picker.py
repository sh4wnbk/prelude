"""Acceptance tests for the narrator picker, written before it exists.

Today the side decides the recording: a fan gets the Buddy, a listener with no
side gets the Storyteller, and Profile's narrator cards only say "coming soon".
Shawn's decision on 2026-11-07 is that a fan may now choose, and that the side
rule stays the default until they do. `docs/bob_brief.md` carries the brief as
Task 14.

**One lookup.** `Prelude.slotFor(match)` becomes the only place that reads
`hero.voice_for`. The words the moment card shows and the recording its player
plays both come from it, so the text under the grounding label and the voice
reading it stay one piece of writing however the narrator was picked. Profile
marks the card that lookup names, so the marked narrator is the one the fan
will actually hear. Three readers indexing `voice_for` separately is how those
three answers would drift apart.

**What the lookup answers**, for a hero whose `voice_for` is
`{"team_a": "buddy_scored", "team_b": "buddy_conceded",
"neutral": "storyteller_neutral"}`, which is what both heroes carry:

| Chosen | Listener with a side | Listener with no side |
| ------ | -------------------- | --------------------- |
| nothing | the side's key, today's behaviour | `storyteller_neutral` |
| the Storyteller | `storyteller_neutral` | `storyteller_neutral` |
| the Buddy | the side's key | the default, `storyteller_neutral` |
| the Caller | the default | the default |

**That table is checked in a browser and not here.** The suite has no
JavaScript runtime, so these tests read the files and hold the contract: where
the one lookup lives, who calls it, what is stored, and the copy a fan reads.
The table itself is run in a headless browser and recorded in the brief and in
`HANDOFF.md`, which is how Task 10's reopened card and Task 11's player were
checked. Task 11 is why the browser run is not optional: a player that read
`whenMatches`'s document as if it were the list passed every file-reading test
and played nothing.

**Nothing moves in Python.** `default_persona` in `app/orchestrator.py` is
still the side rule and still writes `hero.voice_for` through
`scripts/write_headers.py`. The choice is a preference held on the phone, like
the fan's name, and it selects among the recordings that rule produced.
"""

import json
import re
from pathlib import Path

import pytest

from app.orchestrator import default_persona
from app.orchestrator_contract import BUDDY, NEUTRAL, STORYTELLER, TEAM_A, TEAM_B, Listener
from app.personas import PERSONAS

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
RENDERER = WEB / "match-content.js"
PLAYER = WEB / "narration-player.js"
PROFILE = WEB / "prelude_07_profile.html"
MATCHES = WEB / "matches.json"
NARRATORS = WEB / "narrators.json"

#: The storage key, alongside `prelude.name`: one choice for the session, not
#: one per match, because a narrator is a voice and not an answer about a game.
NARRATOR_KEY = '"prelude.narrator"'

#: The note under a narrator that is recorded but cannot be chosen yet, because
#: the fan has not said who they are with. Shawn's copy, 2026-11-07.
BUDDY_NOTE = "The Buddy needs a team. Choose a team under 'Who are you with.'"

#: The note under a narrator with no recordings at all.
CALLER_NOTE = "The Caller is coming soon."

#: What Task 12 showed when a narrator was tapped. Choosing one works now, so
#: the half of that sentence about Prelude picking goes.
OLD_MESSAGE = "For now, Prelude picks your narrator from who you're with."

#: `hero.voice_for` for both heroes, which the picker does not touch. Argentina
#: scored in both, so a fan of theirs hears the Buddy on a goal for their side,
#: a fan of the other team hears the Buddy on one against it, and a listener
#: with no side hears the Storyteller.
VOICE_FOR = {
    3750191: {"team_a": "buddy_scored", "team_b": "buddy_conceded",
              "neutral": "storyteller_neutral"},
    3869685: {"team_a": "buddy_scored", "team_b": "buddy_conceded",
              "neutral": "storyteller_neutral"},
}

BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)
LINE_COMMENT = re.compile(r"(?:^|  )//.*$", re.M)


def without_comments(source):
    """`source` with its comments removed, so a rule about code is read off the
    code. A trailing comment in these files is set off by at least two spaces,
    which is what keeps a `//` inside a string or a regular expression."""
    return LINE_COMMENT.sub("", BLOCK_COMMENT.sub("", source))


def renderer():
    return RENDERER.read_text(encoding="utf-8")


def player():
    return PLAYER.read_text(encoding="utf-8")


FUNCTION = re.compile(r"^  function ([A-Za-z0-9_]+)\(", re.M)


def functions(source):
    """Every top-level function in `match-content.js`, by name, with comments
    stripped. They sit at one indent inside the file's one closure, which is
    what `tests/test_narrators.py` splits on to read `renderNarrators`."""
    found = {}
    marks = list(FUNCTION.finditer(source))
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(source)
        found[mark.group(1)] = without_comments(source[mark.end():end])
    return found


def body(name):
    """One function of `match-content.js`, or a failure naming the task."""
    found = functions(renderer())
    if name not in found:
        pytest.fail(
            f"app/web/match-content.js has no {name}() yet. It is Task 14 in "
            "docs/bob_brief.md."
        )
    return found[name]


def published():
    """The `window.Prelude` object literal, which is what a screen can reach."""
    found = re.search(r"window\.Prelude = \{(.*?)\n  \};", renderer(), re.S)
    assert found, "no window.Prelude object literal in match-content.js"
    return found.group(1)


def heroes():
    doc = json.loads(MATCHES.read_text(encoding="utf-8"))
    return {entry["match_id"]: entry["hero"] for entry in doc["matches"]}


class TestOneLookup:
    """`slotFor` is the lookup, and it is the only reader of `voice_for`."""

    def test_the_lookup_exists(self):
        assert "slotFor" in functions(renderer())

    def test_the_renderer_publishes_it(self):
        assert "slotFor" in published()

    def test_it_reads_who_the_fan_is_with(self):
        assert "listenerFor(" in body("slotFor")

    def test_it_reads_the_chosen_narrator(self):
        assert "narratorFor(" in body("slotFor")

    def test_voice_for_is_read_nowhere_else(self):
        """The rule this task is built on: one reader of `hero.voice_for`.

        Task 15 put the words and the recording on the same key so the text
        under the grounding label is the one the voice reads. A second reader
        that handled the choice differently would break that silently, with
        one narrator's words and another's voice.
        """
        readers = sorted(name for name, text in functions(renderer()).items()
                         if "voice_for" in text or "voiceFor" in text)
        assert readers == ["slotFor"]

    def test_the_cards_words_come_from_the_lookup(self):
        assert "slotFor(" in body("renderNarration")

    def test_the_marked_card_comes_from_the_lookup(self):
        """Profile marks the narrator the fan will actually hear, which is the
        one `slotFor` names: the chosen one, or the default when nothing is
        chosen, or the default when the Buddy is stored and the side is gone."""
        assert "slotFor(" in body("renderNarrators")


class TestThePlayer:
    def test_it_calls_the_lookup(self):
        assert "Prelude.slotFor(" in player()

    def test_it_does_not_index_voice_for(self):
        text = without_comments(player())
        assert "voice_for" not in text
        assert "voiceFor" not in text

    def test_it_still_disables_play_with_no_recording(self):
        """Task 11's behaviour, kept: a slot with no file leaves the button
        disabled rather than throwing."""
        assert "playBtn.disabled = true" in player()


class TestTheChoice:
    def test_the_reader_is_published(self):
        assert "narratorFor" in published()

    def test_the_writer_is_published(self):
        assert "setNarrator" in published()

    def test_it_is_stored_the_way_the_name_is(self):
        """`prelude.name` is one value for the session, read and written inside
        a try, so blocked storage costs the preference and not the screen. The
        narrator is the same kind of value and is held the same way."""
        text = renderer()
        assert NARRATOR_KEY in text
        read = body("narratorFor")
        assert "sessionStorage.getItem" in read
        assert "catch" in read
        write = body("setNarrator")
        assert "sessionStorage.setItem" in write
        assert "catch" in write

    def test_the_id_stored_is_the_narrators_own(self):
        """The ids are the persona ids, and they arrive in `narrators.json`
        rather than being spelled again in the browser."""
        cards = body("renderNarrators")
        assert "setNarrator(" in cards
        assert re.search(r"setNarrator\((?:[A-Za-z0-9_]+)\.id\)", cards)


class TestTheProfileCards:
    def cards(self):
        return body("renderNarrators")

    def test_the_cards_are_buttons(self):
        cards = self.cards()
        assert 'createElement("button")' in cards
        assert 'btn.type = "button"' in cards

    def test_the_chosen_card_is_current(self):
        assert '"aria-current", "true"' in self.cards()

    def test_a_card_that_cannot_be_chosen_says_so(self):
        assert '"aria-disabled", "true"' in self.cards()

    def test_the_buddy_needs_a_team(self):
        assert BUDDY_NOTE in self.cards()

    def test_the_caller_is_coming_soon(self):
        assert CALLER_NOTE in self.cards()

    def test_the_old_message_is_gone(self):
        assert OLD_MESSAGE not in renderer()

    def test_the_notes_are_set_as_text(self):
        assert "note.textContent" in self.cards()

    def test_no_markup_from_data(self):
        """Task 12's rule, kept: names, descriptions and notes are text."""
        assert "innerHTML" not in self.cards()

    def test_the_note_starts_hidden_in_the_markup(self):
        assert re.search(r'data-field="narrator_note"[^>]*hidden',
                         PROFILE.read_text(encoding="utf-8"))


class TestWhatDoesNotChange:
    """The choice selects among the recordings the side rule produced. It does
    not change the rule, the keys, the list or the audio."""

    def test_the_side_rule_in_python_is_the_same(self):
        assert default_persona(Listener(allegiance=TEAM_A)) == BUDDY
        assert default_persona(Listener(allegiance=TEAM_B)) == BUDDY
        assert default_persona(Listener(allegiance=NEUTRAL)) == STORYTELLER

    @pytest.mark.parametrize("match_id", sorted(VOICE_FOR))
    def test_the_voice_keys_are_the_same(self, match_id):
        assert heroes()[match_id]["voice_for"] == VOICE_FOR[match_id]

    @pytest.mark.parametrize("match_id", sorted(VOICE_FOR))
    def test_every_key_still_has_its_recording(self, match_id):
        hero = heroes()[match_id]
        audio = hero["audio"]
        for key in sorted(set(VOICE_FOR[match_id].values())):
            assert key in audio, key
            assert (WEB / audio[key]).is_file(), audio[key]

    def test_the_narrator_list_is_the_same(self):
        doc = json.loads(NARRATORS.read_text(encoding="utf-8"))
        assert doc == {"narrators": [
            {"id": p.id, "name": p.name, "profile": p.profile} for p in PERSONAS
        ]}

    def test_the_caller_has_no_recording_to_choose(self):
        """Why the Caller stays coming soon, read off the data rather than
        asserted: no slot in either hero is the Caller's, so there is nothing
        for a fan who picks it to hear."""
        for hero in heroes().values():
            assert not [key for key in hero["voice_for"].values()
                        if key.startswith("caller_")]
            assert not [key for key in hero["audio"] if key.startswith("caller_")]
