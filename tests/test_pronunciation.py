"""Tests for the pronunciation table and where it is allowed to reach.

Two halves. The first is the function: it marks up the listed words, it leaves
everything else exactly as it found it, and it says the same words it was
given. The second is the constraint that made the module worth writing
separately, which is that nothing but the speech request may see its output.
A `<phoneme>` element in the text the screen shows is a fan reading markup.
The same element in the text `app/grounding.py` reads was once markup carried
into the label and into the audio with nothing raising; the check refuses it
now, which `TestTheClockInARealNarration` measures rather than assumes, and
the structural test stays as the second layer.

Nothing here calls the speech service. The markup is text and is checked as
text; whether IBM honours it is `scripts/tts_probe.py`'s question, and
`docs/VOICE.md` records that `<phoneme>` is the one element it supports on all
three voices.
"""

import re
from datetime import datetime
from pathlib import Path

import pytest

from app.grounding import check, strip_citations
from app.narration_prompt import facts_from_buildup, template_narration
from app.orchestrator import header
from app.orchestrator_contract import (
    NEUTRAL,
    STORYTELLER,
    TEAM_A,
    Event,
    ScoringMoment,
)
from app.statsbomb_event_feed import StatsBombEventFeed
from app.tts import WatsonTextToSpeech, without_markup
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

#: The 1986 hero goal, which is the one whose narration opens on the clock.
MATCH_1986 = 3750191
GOAL_1986 = (54, 18)

#: The header the orchestrator writes for it, which is where "lead" is spoken.
HEADER_1986 = (
    "Argentina extend the lead. Argentina 2, England 0. "
    "Here's how it happened."
)

#: Credentials that are not credentials, so no test reads a file. The backend
#: is built only to have it construct a request; nothing here sends one, and
#: `tests/conftest.py` blocks the network for the whole suite anyway.
FAKE_ENV = {
    "TTS_API_KEY": "not-a-key",
    "TTS_URL": "https://example.invalid/instances/not-an-instance",
}


def speech_backend():
    return WatsonTextToSpeech(
        env=FAKE_ENV, transport=lambda url, body, headers: b""
    )


@pytest.fixture(scope="module")
def feed():
    return StatsBombEventFeed()


@pytest.fixture(scope="module")
def facts_1986(feed):
    """The facts behind Maradona's second, which the narration is built from."""
    moment = next(
        one for one in feed.defining_moments(MATCH_1986)
        if (one.minute, one.second) == GOAL_1986
    )
    return facts_from_buildup(feed.buildup(MATCH_1986, moment))


@pytest.fixture(scope="module")
def tagged_1986(facts_1986):
    """The narration as it is checked: citation tags still on it.

    `Narrated.tagged_text` in `app/narration.py`. This is what
    `app/grounding.py` reads, and it is the only form it can read: a sentence
    with no citation has nothing to be read against, so the stripped text does
    not pass the check and is not meant to.
    """
    return template_narration(facts_1986)


@pytest.fixture(scope="module")
def spoken_1986(tagged_1986):
    """The narration as it is shown and spoken: the tags taken off.

    `Narrated.text`. The two forms exist because the check needs the
    citations and a listener must never hear them, which is also why
    `app/tts.py` refuses the tagged one.
    """
    return strip_citations(tagged_1986)

#: The modules that must not reach the pronunciation table. The screen's text
#: and the checked text come through these, and markup in either is a bug the
#: rest of the suite would not catch: the narration would still be grounded
#: and the header would still read correctly to anything that strips tags.
def _imports_pronunciation(name: str) -> bool:
    """Whether `app/<name>` imports the pronunciation table."""
    source = (APP / name).read_text(encoding="utf-8")
    return bool(
        re.search(r"^\s*(from|import)\s+app\.pronunciation", source, re.MULTILINE)
    )


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
    """Two entries, and the shape the next one has to fit."""

    def test_lead_is_in_the_table(self):
        assert PRONUNCIATIONS["lead"] == "liːd"

    def test_minute_is_in_the_table(self):
        """All three voices read "Minute 54." as "my-NEWT", the adjective.

        In this app the word only ever means the unit of time: it reaches
        speech from `template_narration` in `app/narration_prompt.py`, which
        writes the clock. The CMU Pronouncing Dictionary lists `M AY0 N UW1 T`
        beside `M IH1 N AH0 T`, so the voices were choosing a real
        pronunciation of the written word rather than misreading it, and no
        amount of context would have settled it for them.
        """
        assert PRONUNCIATIONS["minute"] == "ˈmɪnɪt"

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


class TestTheClockInARealNarration:
    """The one entry added for a word the narration writes, end to end.

    `template_narration` opens on "Minute 54." for the 1986 hero goal, so this
    is the shipped path rather than a sentence invented for a test: the real
    narration, through the real backend, with the real table.
    """

    def test_the_real_narration_says_minute(self, spoken_1986):
        assert spoken_1986.startswith("Minute 54.")

    def test_the_request_carries_the_element(self, spoken_1986):
        request = speech_backend().request_for(
            HEADER_1986, spoken_1986, STORYTELLER, NEUTRAL
        )
        assert (
            '<phoneme alphabet="ipa" ph="ˈmɪnɪt">Minute</phoneme>'
            in request.text
        )

    def test_the_request_says_the_same_words(self, spoken_1986):
        request = speech_backend().request_for(
            HEADER_1986, spoken_1986, STORYTELLER, NEUTRAL
        )
        assert without_markup(request.text) == HEADER_1986 + " " + spoken_1986

    def test_the_displayed_narration_is_unchanged(self, spoken_1986):
        """What a screen shows, after the request has been built from it."""
        before = spoken_1986
        speech_backend().request_for(
            HEADER_1986, spoken_1986, STORYTELLER, NEUTRAL
        )
        assert spoken_1986 == before
        assert "<phoneme" not in spoken_1986

    def test_the_displayed_header_is_unchanged(self):
        assert "<phoneme" not in HEADER_1986
        assert "Minute" not in HEADER_1986

    def test_the_checked_narration_is_grounded_and_unchanged(
        self, tagged_1986, facts_1986
    ):
        """The text the check reads carries no markup and still passes.

        It is the tagged form, which is the only form the check can read, and
        it says the clock in the same sentence the request marks up. Building
        the request leaves it exactly as it was.
        """
        before = tagged_1986
        speech_backend().request_for(
            HEADER_1986, strip_citations(tagged_1986), STORYTELLER, NEUTRAL
        )
        assert tagged_1986 == before
        assert "<phoneme" not in tagged_1986
        assert check(tagged_1986, facts_1986).grounded

    def test_the_check_refuses_markup_in_the_text_it_reads(
        self, tagged_1986, facts_1986
    ):
        """The grounding check refuses the markup, and the plain narration it
        was made from still passes on the same claims.

        It did not always, and that is why the rule is the characters rather
        than an element. Both forms came back grounded on all 35 claims when
        this was first measured: the check reads names, actions, clocks and
        numbers against the facts a sentence cited, and `phoneme`, `alphabet`
        and `ipa` are none of those, so they passed through as words it had no
        claim about. A narration marked up a step early was accepted, labelled
        "Verified from play data", and read out with the markup in it.

        `BANNED_PATTERNS` now refuses any narration holding an angle bracket.
        `TestNothingElseAppliesIt` stays as the second layer: this one catches
        marked-up text arriving at the check, and that one catches a module
        that could produce it.
        """
        marked = for_speech(tagged_1986)
        assert marked != tagged_1986
        plain_result = check(tagged_1986, facts_1986)
        marked_result = check(marked, facts_1986)
        assert plain_result.grounded
        assert plain_result.checked == 35
        assert not marked_result.grounded
        assert {failure.kind for failure in marked_result.failures} == {"markup"}


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

    This is a structural test rather than a behavioural one, and it is the
    second layer rather than the only one. The grounding check refuses an
    angle bracket outright, so marked-up narration arriving there is caught;
    what no behaviour can catch is markup in the header, which still reads
    correctly to anything that strips tags and never passes through the
    check. A module that imported the table is what produces either, and that
    is what this reads for.
    """

    def test_no_text_producing_module_imports_it(self):
        offenders = [
            name for name in MUST_NOT_IMPORT if _imports_pronunciation(name)
        ]
        assert offenders == []

    def test_the_speech_backend_is_the_one_module_that_does(self):
        """The constraint has two halves and this is the second one.

        A table nothing imports is a table that does nothing, so the test
        above would pass just as well if the markup never reached the service
        at all. `app/tts.py` is where it is applied, and it is the only place.
        """
        applies = [
            path.name
            for path in sorted(APP.glob("*.py"))
            if _imports_pronunciation(path.name)
        ]
        assert applies == ["tts.py"]

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
