"""Tests for the pronunciation table and where it is allowed to reach.

Two halves. The first is the function: it marks up the listed words, it leaves
everything else exactly as it found it, and it says the same words it was
given. The second is the constraint that made the module worth writing
separately, which is that nothing but the speech request may see its output.
A `<phoneme>` element in the text the screen shows is a fan reading markup,
and the same element in the text `app/grounding.py` reads is a name the check
cannot match and a narration refused for being pronounceable.

Nothing here calls the speech service. The markup is text and is checked as
text; whether IBM honours it is `scripts/tts_probe.py`'s question, and
`docs/VOICE.md` records that `<phoneme>` is the one element it supports on all
three voices.
"""

import re
from datetime import datetime
from pathlib import Path

import pytest

from app.orchestrator import header
from app.orchestrator_contract import Event, ScoringMoment, TEAM_A
from app.pronunciation import (
    PHONEME,
    PRONUNCIATIONS,
    AlreadyMarkedUp,
    escape,
    for_speech,
    spoken_text,
    unescape,
)

APP = Path(__file__).resolve().parent.parent / "app"

#: The modules that must not reach the pronunciation table. The screen's text
#: and the checked text come through these, and markup in either is a bug the
#: rest of the suite would not catch: the narration would still be grounded
#: and the header would still read correctly to anything that strips tags.
MUST_NOT_IMPORT = (
    "grounding.py",
    "narration.py",
    "narration_prompt.py",
    "narration_provider.py",
    "orchestrator.py",
    "orchestrator_contract.py",
    "personas.py",
)


class TestTheTable:
    """One entry, and the shape the next one has to fit."""

    def test_lead_is_in_the_table(self):
        assert PRONUNCIATIONS["lead"] == "liːd"

    def test_every_key_is_lower_case(self):
        """The match is case insensitive and looks the key up in lower case,
        so a capitalised key would be an entry that never fires.
        """
        assert [word for word in PRONUNCIATIONS if word != word.lower()] == []

    def test_no_key_is_empty_or_padded(self):
        assert [
            word for word in PRONUNCIATIONS if not word or word != word.strip()
        ] == []

    def test_every_value_is_a_non_empty_pronunciation(self):
        assert [
            word for word, ipa in PRONUNCIATIONS.items() if not ipa.strip()
        ] == []

    def test_no_value_carries_a_quote(self):
        """The IPA goes into a double quoted attribute, so a quote in it would
        end the attribute early and the service would answer 400.
        """
        assert [
            word for word, ipa in PRONUNCIATIONS.items() if '"' in ipa
        ] == []


class TestItMarksTheListedWords:
    def test_lead_is_marked_up(self):
        assert for_speech("Argentina take the lead.") == (
            'Argentina take the '
            '<phoneme alphabet="ipa" ph="liːd">lead</phoneme>.'
        )

    def test_the_word_keeps_its_own_case(self):
        """The text inside the element is what a client that cannot speak the
        IPA falls back on, so it stays the word as it was written.
        """
        assert ">Lead</phoneme>" in for_speech("Lead changed hands.")

    def test_every_occurrence_is_marked(self):
        marked = for_speech("The lead, and then the lead again.")
        assert marked.count("<phoneme") == 2

    def test_a_longer_word_containing_one_is_left_alone(self):
        """"leader" and "misleading" are not "lead" and are said correctly."""
        for word in ("leader", "leaders", "misleading", "pleaded"):
            assert for_speech(word) == word

    def test_the_tag_is_the_documented_element(self):
        assert PHONEME.format(ipa="x", word="y") == (
            '<phoneme alphabet="ipa" ph="x">y</phoneme>'
        )


class TestItTouchesNothingElse:
    def test_text_with_no_listed_word_is_returned_identically(self):
        text = "Maradona shot. Shilton was beaten at 54:18."
        assert for_speech(text) is text

    def test_an_ampersand_is_left_alone_when_there_is_no_markup(self):
        """Escaping is only needed once the body is SSML, and it costs
        characters. Nothing is escaped on the path that sends plain text.
        """
        assert for_speech("Hearts & Hibs drew.") == "Hearts & Hibs drew."

    def test_an_ampersand_is_escaped_once_there_is_markup(self):
        marked = for_speech("Hearts & Hibs take the lead.")
        assert "&amp;" in marked
        assert "<phoneme" in marked

    def test_applying_it_twice_is_refused(self):
        with pytest.raises(AlreadyMarkedUp):
            for_speech(for_speech("Argentina take the lead."))


class TestItSaysTheSameWords:
    """A pronunciation changes how a word sounds and never what it says."""

    CASES = (
        "Argentina take the lead.",
        "Lead changed hands twice.",
        "The lead, and then the lead again.",
        "Maradona shot at 54:18.",
        "Hearts & Hibs take the lead.",
        "A literal &amp; survives.",
        "Nothing listed here at all.",
        "",
    )

    @pytest.mark.parametrize("text", CASES)
    def test_a_round_trip_returns_the_input(self, text):
        assert spoken_text(for_speech(text)) == text

    def test_escaping_round_trips(self):
        for text in ("a & b", "a < b", "a > b", "&amp;", "&lt;", "a &amp;lt; b"):
            assert unescape(escape(text)) == text


class TestNothingElseAppliesIt:
    """The one constraint: the markup reaches the speech request and no other.

    This is a structural test rather than a behavioural one because the bug it
    guards against is invisible behaviourally. Markup in the header still
    reads correctly to anything that strips tags, and a narration marked up
    before the check would be refused with a message about an ungrounded name,
    which is the wrong thing to go looking at.
    """

    def test_no_text_producing_module_imports_it(self):
        offenders = []
        for name in MUST_NOT_IMPORT:
            source = (APP / name).read_text(encoding="utf-8")
            if re.search(r"^\s*(from|import)\s+app\.pronunciation", source,
                         re.MULTILINE):
                offenders.append(name)
        assert offenders == []

    def test_the_header_the_screen_shows_carries_no_markup(self):
        """The real header for a real transition, and it says "lead"."""
        line = header(
            Event(
                kickoff=datetime(1986, 6, 22, 12, 0),
                team_a="Argentina",
                team_b="England",
                sport="football",
            ),
            ScoringMoment(
                scoring_side=TEAM_A,
                minute=54,
                second=18,
                score_before_a=1,
                score_before_b=0,
                score_a=2,
                score_b=0,
                regulation_minutes=90,
            ),
        )
        assert "lead" in line
        assert "<phoneme" not in line

    def test_the_speech_text_is_not_the_written_text(self):
        """The two forms are different strings, so neither can pass for the
        other by accident. Which module may hold which is the test above; this
        is why it matters that they are not the same value.
        """
        narration = "Argentina take the lead. [1]"
        assert for_speech(narration) != narration
        assert spoken_text(for_speech(narration)) == narration
