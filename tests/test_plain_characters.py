"""Tests for making a narration's characters plain.

Two candidate narrations of 2026-10-30 arrived carrying a character nobody
could see: a `NARROW NO-BREAK SPACE` (U+202F) inside "Terry Butcher" and a
`NON-BREAKING HYPHEN` (U+2011) inside "fifty-four". Both passed
`app/grounding.py` honestly and both would have been sent to the speech
service as written. The characters in these tests are those two and their
relatives, written as escapes so a test file nobody can read with their eyes
is not the thing holding the rule.

The other half of the rule matters as much: a dash is not a hyphen. The em
dash and the en dash are refused by `app/grounding.py` and banned from copy by
`CLAUDE.md`, so a rewrite that turned either into a hyphen would undo a ban in
the one place nobody would look. Several tests here exist only to say that
does not happen.
"""

import unicodedata

import pytest

from app.grounding import check
from app.narration_prompt import facts_from_buildup
from app.plain_characters import (
    DASHES,
    HYPHENS,
    REMOVED,
    is_space_to_plain,
    plain,
    unplain,
)
from app.recorded_names import recorded_nicknames
from app.statsbomb_event_feed import StatsBombEventFeed

MATCH_1986 = 3750191
MATCH_2022 = 3869685
GOAL_1986 = (54, 18)
HERO_2022 = (35, 22)

NARROW_NO_BREAK_SPACE = " "
NO_BREAK_SPACE = " "
NON_BREAKING_HYPHEN = "‑"
EM_DASH = "—"
EN_DASH = "–"
ZERO_WIDTH_SPACE = "​"


@pytest.fixture(scope="module")
def feed():
    return StatsBombEventFeed()


@pytest.fixture(scope="module")
def facts_1986(feed):
    moment = next(
        m for m in feed.defining_moments(MATCH_1986)
        if (m.minute, m.second) == GOAL_1986
    )
    return facts_from_buildup(
        feed.buildup(MATCH_1986, moment), recorded_nicknames(MATCH_1986)
    )


@pytest.fixture(scope="module")
def facts_hero_2022(feed):
    moment = next(
        m for m in feed.defining_moments(MATCH_2022)
        if (m.minute, m.second) == HERO_2022
    )
    return facts_from_buildup(
        feed.buildup(MATCH_2022, moment), recorded_nicknames(MATCH_2022)
    )


class TestTheTwoThatArrived:
    """The exact characters the live candidates carried."""

    def test_the_narrow_no_break_space_in_a_name(self):
        """Slot 5 of the 1986 rerun wrote "Terry Butcher" like this."""
        written = "Terry" + NARROW_NO_BREAK_SPACE + "Butcher"
        assert written != "Terry Butcher"
        assert plain(written) == "Terry Butcher"

    def test_the_non_breaking_hyphen_in_a_number(self):
        """The candidate before it wrote "fifty-four" like this."""
        written = "fifty" + NON_BREAKING_HYPHEN + "four"
        assert written != "fifty-four"
        assert plain(written) == "fifty-four"

    def test_the_no_break_space(self):
        assert plain("at" + NO_BREAK_SPACE + "54:18") == "at 54:18"


class TestWhatIsLeftAlone:
    def test_plain_text_comes_back_identical(self):
        text = (
            "[1] Nahuel Molina passed.\n"
            "[13] Angel Di Maria shot and scored for Argentina."
        )
        assert plain(text) is not None
        assert plain(text) == text

    def test_the_accents_survive(self):
        """A recorded name carries accents and they are how the data spells
        it. Nothing here is folding a name towards ASCII."""
        assert plain("Ángel Di María") == "Ángel Di María"
        assert plain("Héctor Enrique") == "Héctor Enrique"
        assert plain("Julián Álvarez") == "Julián Álvarez"

    def test_the_line_breaks_survive(self):
        """A narration is one sentence per line and `app/grounding.py` reads
        those lines, so a newline is not whitespace to be flattened."""
        assert plain("[1] One.\n[2] Two.\n") == "[1] One.\n[2] Two.\n"

    def test_an_em_dash_is_not_turned_into_a_hyphen(self):
        """It is banned copy, and it has to stay visible to be refused."""
        written = "he shot" + EM_DASH + "and scored"
        assert plain(written) == written
        assert EM_DASH in plain(written)

    def test_an_en_dash_is_not_turned_into_a_hyphen(self):
        written = "54" + EN_DASH + "18"
        assert plain(written) == written

    def test_every_dash_is_left_as_written(self):
        for character in DASHES:
            assert plain(character) == character

    def test_no_banned_word_can_be_assembled_by_normalising(self):
        """It fixes a character, never a word.

        A rewrite that joined two words would be a way past
        `BANNED_PATTERNS`, so the test is that the words either side of a
        rewritten character are the words that were there.
        """
        written = "the" + NARROW_NO_BREAK_SPACE + "greatest"
        assert plain(written).split() == ["the", "greatest"]


class TestTheZeroWidthCharacters:
    def test_a_zero_width_space_is_removed_not_replaced(self):
        """It sits inside a word, so a space in its place would split it."""
        assert plain("Maradona" + ZERO_WIDTH_SPACE + "shot") == "Maradonashot"

    def test_every_removed_character_leaves_nothing_behind(self):
        for character in REMOVED:
            assert plain("a" + character + "b") == "ab"


class TestTheCategoryRule:
    """The spaces are read off the Unicode category rather than listed, so a
    space form nobody has seen yet is covered."""

    @pytest.mark.parametrize(
        "codepoint",
        [
            0x00A0,  # NO-BREAK SPACE
            0x1680,  # OGHAM SPACE MARK
            0x2000,  # EN QUAD
            0x2001,  # EM QUAD
            0x2002,  # EN SPACE
            0x2003,  # EM SPACE
            0x2004,  # THREE-PER-EM SPACE
            0x2005,  # FOUR-PER-EM SPACE
            0x2006,  # SIX-PER-EM SPACE
            0x2007,  # FIGURE SPACE
            0x2008,  # PUNCTUATION SPACE
            0x2009,  # THIN SPACE
            0x200A,  # HAIR SPACE
            0x202F,  # NARROW NO-BREAK SPACE
            0x205F,  # MEDIUM MATHEMATICAL SPACE
            0x3000,  # IDEOGRAPHIC SPACE
        ],
    )
    def test_every_space_separator_becomes_a_plain_space(self, codepoint):
        character = chr(codepoint)
        assert unicodedata.category(character) == "Zs"
        assert is_space_to_plain(character)
        assert plain("a" + character + "b") == "a b"

    def test_the_plain_space_is_not_itself_rewritten(self):
        assert not is_space_to_plain(" ")
        assert plain("a b") == "a b"

    def test_a_dash_is_in_neither_mapping_twice_over(self):
        """`Pd` holds hyphens and dashes together, which is why the hyphens
        are listed by name instead of read off a category."""
        assert not set(HYPHENS) & set(DASHES)
        for character in DASHES:
            assert unicodedata.category(character) == "Pd"


class TestUnplain:
    def test_it_names_what_would_change(self):
        found = dict(
            unplain("Terry" + NARROW_NO_BREAK_SPACE + "Butcher at fifty"
                    + NON_BREAKING_HYPHEN + "four")
        )
        assert found[NARROW_NO_BREAK_SPACE] == "NARROW NO-BREAK SPACE"
        assert found[NON_BREAKING_HYPHEN] == "NON-BREAKING HYPHEN"

    def test_plain_text_has_nothing_to_report(self):
        assert unplain("[13] Ángel Di María shot and scored.") == ()

    def test_a_dash_is_not_reported_as_something_it_would_change(self):
        assert unplain("a" + EM_DASH + "b") == ()


class TestTheCheckReadsPlainText:
    """`check` makes the text plain first, so the words it reads are the words
    a voice would say."""

    def test_a_name_split_by_a_narrow_space_is_still_grounded(
        self, facts_1986
    ):
        """This is slot 5 of the live rerun, in miniature. It passed before
        the rewrite too, because a narrow space is whitespace; the point is
        that it still passes, so the rewrite costs no good narration."""
        result = check(
            "[14] Terry" + NARROW_NO_BREAK_SPACE + "Butcher was dribbled "
            "past.\n"
            "[24] Diego Armando Maradona shot and scored for Argentina.",
            facts_1986,
        )
        assert result.grounded, result.summary

    def test_a_name_joined_by_a_zero_width_space_is_read_as_one_word(
        self, facts_hero_2022
    ):
        """Without the rewrite this is "LionelMessi", which is a name nothing
        records, and the narration would be refused for a character nobody can
        see. With it the sentence is read as written aloud."""
        joined = "Lionel" + ZERO_WIDTH_SPACE + " Messi"
        result = check(
            "[6] " + joined + " passed.\n"
            "[13] Ángel Di María shot and scored for Argentina.",
            facts_hero_2022,
        )
        assert result.grounded, result.summary

    def test_an_em_dash_is_still_refused_after_the_rewrite(self, facts_1986):
        """The rewrite must not be a way past the ban."""
        result = check(
            "[24] Diego Armando Maradona shot" + EM_DASH
            + "and scored for Argentina.",
            facts_1986,
        )
        assert not result.grounded
        assert "em dash" in {failure.kind for failure in result.failures}

    def test_an_en_dash_is_still_refused_after_the_rewrite(self, facts_1986):
        result = check(
            "[24] Diego Armando Maradona shot" + EN_DASH
            + "and scored for Argentina.",
            facts_1986,
        )
        assert not result.grounded
        assert "en dash" in {failure.kind for failure in result.failures}


class TestTheSpeechRequestIsPlain:
    """`speech_text` is the last thing that touches the text before it is a
    paid request, so it is the other end of the same guard."""

    def test_the_narration_reaches_the_request_plain(self):
        from app.tts import speech_text

        text = speech_text(
            "Argentina lead England 2 to 1.",
            "Terry" + NARROW_NO_BREAK_SPACE + "Butcher was dribbled past at "
            "fifty" + NON_BREAKING_HYPHEN + "four.",
            "storyteller",
            "scored",
        )
        assert NARROW_NO_BREAK_SPACE not in text
        assert NON_BREAKING_HYPHEN not in text
        assert "Terry Butcher" in text
        assert "fifty-four" in text

    def test_the_header_reaches_the_request_plain(self):
        """"lead" is in the pronunciation table and arrives marked up, so the
        words either side of the rewritten space are what this reads."""
        from app.tts import speech_text

        text = speech_text(
            "England" + NO_BREAK_SPACE + "trail Argentina 2 to 1.",
            "Diego Armando Maradona shot and scored.",
            "storyteller",
            "scored",
        )
        assert NO_BREAK_SPACE not in text
        assert "England trail Argentina" in text

    def test_a_plain_narration_is_unchanged_by_it(self):
        """The counts a budget is set on do not move for text that was already
        plain, which every frozen narration is."""
        from app.tts import speech_text

        header = "Argentina lead England 2 to 1."
        narration = "Diego Armando Maradona shot and scored for Argentina."
        assert speech_text(header, narration, "storyteller", "scored") == (
            speech_text(
                plain(header), plain(narration), "storyteller", "scored"
            )
        )
