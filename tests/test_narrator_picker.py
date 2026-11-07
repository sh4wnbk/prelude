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

**The two notes are composed, so a fan reads the name and this suite reads
the join.** A narrator with no recording in either hero is coming soon, and a
narrator that is recorded but not for this listener's answer needs a team. The
names come from `narrators.json`, which is where Task 12 put them, so what is
checked here is the tail and the `.name +` in front of it; the sentences a fan
reads are "The Caller is coming soon." and "The Buddy needs a team. Choose a
team under 'Who are you with.'".

**The table is seven rows now, and it is a file.** Phase 6 wrote the rule a
second time, in Python, for the hosted API in `app/api.py`, so the rows moved
out of this docstring and into `tests/slot_rows.json`. The `slot_rows` fixture
in `tests/conftest.py` hands them to this file and to `tests/test_api.py`:
`TestTheSevenRows` below reads each row against `hero.voice_for` and
`hero.audio`, which is what the browser's copy indexes, and
`tests/test_api.py::TestTheSevenRows` runs the same rows through the Python
copy and through `GET /buildup`. One rule, one table, two suites.

**That table and those two sentences are checked in a browser and not here.** The suite has no
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
#: the fan has not said who they are with. Shawn's copy, 2026-11-07. A fan
#: reads "The Buddy needs a team. Choose a team under 'Who are you with.'": the
#: name comes from `narrators.json`, as Task 12's note did, so the copy here is
#: the tail and the join.
NEEDS_A_TEAM = '''.name + " needs a team. Choose a team under 'Who are you with.'"'''

#: The note under a narrator with no recordings at all. A fan reads "The Caller
#: is coming soon.". The closing quote is part of this: Task 12's note carried
#: a second sentence after the period, and that sentence is what Task 14 drops.
COMING_SOON = '.name + " is coming soon."'

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

    def test_a_recorded_narrator_waiting_on_a_side_needs_a_team(self):
        assert NEEDS_A_TEAM in self.cards()

    def test_a_narrator_with_no_recording_is_coming_soon(self):
        assert COMING_SOON in self.cards()

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


class TestTheSevenRows:
    """The rule's own table, read against the data the browser's copy indexes.

    This file cannot run `Prelude.slotFor`, so what it can hold is that every
    row names a real match, a key that match actually carries, and a recording
    that is in the repo, and that each row is the branch of the rule it claims
    to be. The branches are the three in the lookup: no choice, a chosen
    narrator whose slot is in reach, and a chosen narrator whose slot is not.
    `tests/test_api.py` holds the Python copy to the same seven rows, and the
    browser run is recorded in `HANDOFF.md`.
    """

    def test_there_are_seven(self, slot_rows):
        assert len(slot_rows) == 7

    def test_every_row_names_a_match_the_app_serves(self, slot_rows):
        assert {row["match_id"] for row in slot_rows} <= set(heroes())

    def test_every_row_names_one_of_the_three_answers(self, slot_rows):
        for row in slot_rows:
            assert row["listener"] in ("team_a", "team_b", "neutral"), row["reads"]

    def test_every_rows_slot_is_one_the_match_carries(self, slot_rows):
        for row in slot_rows:
            voice_for = heroes()[row["match_id"]]["voice_for"]
            assert row["slot"] in voice_for.values(), row["reads"]

    def test_every_rows_slot_has_its_recording(self, slot_rows):
        for row in slot_rows:
            audio = heroes()[row["match_id"]]["audio"]
            assert row["slot"] in audio, row["reads"]
            assert (WEB / audio[row["slot"]]).is_file(), row["reads"]

    def test_a_row_with_no_choice_is_the_side_rule(self, slot_rows):
        """Today's behaviour, which the choice did not change: with nothing
        chosen the answer to "Who are you with" decides."""
        rows = [row for row in slot_rows if not row["narrator"]]
        assert rows, "no row covers a fan who has chosen nothing"
        for row in rows:
            voice_for = heroes()[row["match_id"]]["voice_for"]
            assert row["slot"] == voice_for[row["listener"]], row["reads"]

    def test_a_chosen_narrator_in_reach_is_heard(self, slot_rows):
        """The two slots in reach are the side's own and the neutral one, and
        a slot belongs to the narrator whose id starts it."""
        covered = 0
        for row in slot_rows:
            if not row["narrator"]:
                continue
            voice_for = heroes()[row["match_id"]]["voice_for"]
            reach = [voice_for.get(row["listener"]), voice_for.get("neutral")]
            theirs = [
                key for key in reach
                if key and key.startswith(row["narrator"] + "_")
            ]
            if not theirs:
                continue
            assert row["slot"] == theirs[0], row["reads"]
            covered += 1
        assert covered >= 3, "the chosen-narrator branch is barely covered"

    def test_a_chosen_narrator_out_of_reach_falls_back(self, slot_rows):
        """A fan who picks a narrator with no slot for their answer hears the
        telling their side was written, rather than nothing."""
        covered = 0
        for row in slot_rows:
            if not row["narrator"]:
                continue
            voice_for = heroes()[row["match_id"]]["voice_for"]
            reach = [voice_for.get(row["listener"]), voice_for.get("neutral")]
            if any(key and key.startswith(row["narrator"] + "_") for key in reach):
                continue
            assert row["slot"] == voice_for[row["listener"]], row["reads"]
            covered += 1
        assert covered >= 1, "no row covers the fallback"

    def test_the_rows_cover_both_matches(self, slot_rows):
        assert {row["match_id"] for row in slot_rows} == set(heroes())


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
