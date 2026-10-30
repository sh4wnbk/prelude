"""Tests for the vocabulary check: no word reaches a voice unreviewed.

The pronunciation table's first two entries both arrived after the audio was
paid for, because somebody listened and heard a word come out wrong. Both were
heteronyms and both were predictable from a dictionary beforehand, which is
what `scripts/check_vocabulary.py` does: it collects every word the app can
speak and flags any spelling the CMU Pronouncing Dictionary lists more than
one pronunciation for.

**The test here is the half that runs every time.** The script prints a report
somebody reads; this fails the suite when a flagged word is on neither list,
which is what makes new vocabulary a decision rather than an oversight. Change
a header wording, add an event verb, add a match with a new team name, and
either the word is already reviewed or this goes red naming it.

**No network, and no dictionary download.** `cmudict` is a dev dependency and
ships the data inside the package. `tests/conftest.py` blocks the network for
every test, so a check that fetched a dictionary at test time would fail here
rather than quietly working on one machine.

`tests/test_pronunciation.py` covers the table itself and the markup it
builds. This covers what goes into the table's inbox.
"""

import re
import sys
from pathlib import Path

import pytest

from app.narration_prompt import EVENT_VERBS
from app.orchestrator_contract import (
    CLOSE_GAP,
    HEADER_TAIL,
    HEADER_WORDING,
    SCORE_LINE,
)
from app.pronunciation import CHECKED_NO_ENTRY_NEEDED, PRONUNCIATIONS

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from check_vocabulary import (  # noqa: E402
    TEMPLATE_WORDS,
    pronunciations,
    speakable,
    variants,
)


@pytest.fixture(scope="module")
def vocabulary():
    return speakable()


@pytest.fixture(scope="module")
def dictionary():
    return pronunciations()


@pytest.fixture(scope="module")
def flagged(vocabulary, dictionary):
    """Every word the app can speak that has more than one pronunciation."""
    return {
        word: variants(word, dictionary)
        for word in sorted(vocabulary)
        if len(variants(word, dictionary)) > 1
    }


class TestEveryFlaggedWordHasBeenReviewed:
    """The one test that fails when new vocabulary arrives unreviewed."""

    def test_no_flagged_word_is_unreviewed(self, flagged, vocabulary):
        unreviewed = {
            word: said
            for word, said in flagged.items()
            if word not in PRONUNCIATIONS
            and word not in CHECKED_NO_ENTRY_NEEDED
        }
        assert unreviewed == {}, (
            "these words have more than one pronunciation in the CMU "
            "dictionary and have not been reviewed: "
            + "; ".join(
                "{} ({}) spoken in {}".format(
                    word, " / ".join(said), ", ".join(sorted(vocabulary[word]))
                )
                for word, said in sorted(unreviewed.items())
            )
            + ". Add an entry to PRONUNCIATIONS in app/pronunciation.py, or "
            "put the word on CHECKED_NO_ENTRY_NEEDED there with the reason "
            "it needs none."
        )

    def test_the_check_finds_something_to_check(self, flagged):
        """A check that flags nothing is a check that has stopped working.

        If the dictionary failed to load, or the collector stopped finding
        text, every assertion above would pass on an empty set. This is what
        says the thing ran.
        """
        assert len(flagged) > 10

    def test_the_vocabulary_is_collected_from_every_source(self, vocabulary):
        sources = {source for found in vocabulary.values() for source in found}
        assert {
            "the header",
            "the event verbs",
            "the narration template",
            "the team names",
        } <= sources
        assert any(source.startswith("tests/golden/") for source in sources)


class TestTheTwoListsDoNotOverlap:
    """A word is either given a pronunciation or recorded as not needing one."""

    def test_no_word_is_on_both_lists(self):
        assert set(PRONUNCIATIONS) & set(CHECKED_NO_ENTRY_NEEDED) == set()

    def test_every_reviewed_word_carries_a_reason(self):
        assert [
            word for word, why in CHECKED_NO_ENTRY_NEEDED.items()
            if not why.strip()
        ] == []

    def test_every_reviewed_word_is_lower_case(self):
        """The collector lower cases, so an upper case key would never match."""
        assert [
            word for word in CHECKED_NO_ENTRY_NEEDED if word != word.lower()
        ] == []

    def test_neither_list_holds_a_word_the_app_cannot_speak(self, vocabulary):
        """A stale entry is a review of something that is no longer said.

        Harmless in the audio and misleading in the file: it reads as a
        decision about this app. The table and the reviewed list are both held
        to the vocabulary, so a word that leaves the app leaves these too.
        """
        stale = sorted(
            (set(PRONUNCIATIONS) | set(CHECKED_NO_ENTRY_NEEDED))
            - set(vocabulary)
        )
        assert stale == []


class TestTheHeteronymsAreTheOnesInTheTable:
    """Four entries, and each is a word whose two readings are two words."""

    def test_the_table_holds_exactly_the_four(self):
        """`di` is the fourth, from the frozen 2022 narration: the dictionary
        lists `D IY1` beside `D AY1`, and the second is the English "die"
        rather than an accent on the Spanish name.
        """
        assert set(PRONUNCIATIONS) == {"lead", "minute", "close", "di"}

    def test_every_entry_is_a_word_the_dictionary_flags(self, flagged):
        """An entry for a word with one listed pronunciation would be a
        pronunciation nobody needed to override.
        """
        assert [word for word in PRONUNCIATIONS if word not in flagged] == []

    def test_close_is_spoken_by_the_header(self):
        """It is in the table because of one transition's wording, so that
        wording is what holds the entry in place: if the header stops saying
        "close the gap", the entry stops being needed.
        """
        assert "close" in HEADER_WORDING[CLOSE_GAP]

    def test_minute_is_spoken_by_the_narration_template(self):
        assert any("Minute" in text for text in TEMPLATE_WORDS)

    def test_lead_is_spoken_by_more_than_one_transition(self):
        saying_it = [
            key for key, wording in HEADER_WORDING.items()
            if "lead" in wording
        ]
        assert len(saying_it) > 1


class TestWhatTheCollectorCollects:
    """The vocabulary is read off the app, not typed out in the checker."""

    def test_the_header_words_are_in_it(self, vocabulary):
        for word in ("extend", "gap", "level", "here's", "happened"):
            assert word in vocabulary, word

    def test_the_event_verbs_are_in_it(self, vocabulary):
        for verb in EVENT_VERBS.values():
            for word in re.findall(r"[A-Za-z']+", verb):
                assert word.lower() in vocabulary, word

    def test_the_team_names_are_in_it(self, vocabulary):
        for team in ("argentina", "england", "france"):
            assert team in vocabulary, team

    def test_the_score_line_contributes_no_placeholder(self, vocabulary):
        """`{team_a}` is filled with a team name, which is collected from
        `app/web/matches.json`; the brace name itself is not a word.
        """
        assert "team_a" in SCORE_LINE
        assert "team_a" not in vocabulary
        assert "scorer" not in vocabulary

    def test_the_tail_is_in_it(self, vocabulary):
        assert "happened" in HEADER_TAIL.lower()
        assert vocabulary["happened"]

    def test_no_digit_is_collected(self, vocabulary):
        """"54" is a number the voice reads as a number, and no dictionary
        entry governs it. The clock is checked by `app/grounding.py`.
        """
        assert [word for word in vocabulary if any(c.isdigit() for c in word)] == []

    def test_the_markup_in_a_recorded_request_is_not_collected(self, vocabulary):
        """`tests/golden/tts_synthesize.json` holds a real speech request, so
        its text carries a `<phoneme>` element. The words it says are
        vocabulary; the element around them is not.
        """
        for word in ("phoneme", "alphabet", "ipa", "ph"):
            assert word not in vocabulary, word

    def test_the_schema_fixture_is_not_collected(self, vocabulary):
        """`tests/golden/watsonx_text_generation.json` says in its own
        provenance block that it is not a recording, and its placeholder text
        is not something this app would speak.
        """
        for word in ("placeholder", "fixture"):
            assert word not in vocabulary, word

    def test_no_source_enumerates_player_names(self, vocabulary):
        """A dictionary has nothing useful to say about a player's name, so no
        source here walks the squads. What a name needs is a listener.

        A name still arrives when something the app actually speaks says it,
        which is the rule rather than an exception to it: "beardsley" and
        "shilton" are here because the frozen 1986 narration names them, and
        the test below is the same point from the other side. "cuccittini" is
        the one that shows the squads are not being walked: Messi is in both
        matches and in the 2022 quote, and the 2022 narration does not name
        him, so his name is not vocabulary.
        """
        assert "cuccittini" not in vocabulary
        assert vocabulary["beardsley"] == {"the frozen narrations"}

    def test_a_name_inside_a_recorded_narration_is_collected(self, vocabulary):
        """The rule is the words in a recorded narration, whatever kind of
        word they are, so the one name in the recorded speech request is in.

        It is not flagged: the dictionary lists one pronunciation for it. A
        name that was flagged would be a review for a listener rather than a
        table entry, and `allister` is the first that has come up.

        Two sources now, because the hero recordings stopped speaking the
        template and started speaking the frozen narration, and both say his
        name.
        """
        assert vocabulary["maradona"] == {
            "tests/golden/tts_synthesize.json",
            "the frozen narrations",
        }
