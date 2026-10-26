"""Tests for the grounding check.

Each test is one way a narration can be wrong, or one way it can look wrong and
be fine. The second kind matters as much as the first: the check fails a
narration whole and the pipeline throws it away, so a false positive costs a
good narration and makes a model look worse than it is. Three of the tests here
exist because the first live run produced exactly that, and the words it tripped
on ("Finally", "Argentina's", a clock the prompt itself had printed) are named in
the tests so they cannot come back.

Every narration here carries citation tags, because the check reads a sentence
against the facts that sentence cited. The numbers are the real fact numbers for
these two buildups, read out of `data/raw/` and written down, so a test says
which record it means rather than deriving it from the thing under test. The 54
facts worth knowing for the 1986 goal are in `FACTS_1986` below.

Nothing here calls a model. The narrations are written in the test.
"""

import pytest

from app.grounding import (
    ACTION_CLAIMS,
    BANNED_PATTERNS,
    TEAM_DEMONYMS,
    GroundingResult,
    bare,
    check,
    fold,
    name_parts,
    sentences,
    strip_citations,
)
from app.narration_prompt import EVENT_VERBS, facts_from_buildup, template_narration
from app.statsbomb_event_feed import StatsBombEventFeed

MATCH_1986 = 3750191
MATCH_2022 = 3869685

GOAL_1986 = (54, 18)
PENALTY_2022 = (22, 24)

# The facts of the 54:18 buildup this file cites, read out of data/raw/. The
# whole list is 24 facts, one per recorded event; these are the ones the tests
# point at.
FACTS_1986 = """
   3. José Luis Cuciuffo (Argentina) passes, 54:03
   6. Héctor Adolfo Enrique (Argentina) passes, 54:06
   7. Diego Armando Maradona (Argentina) receives the ball, 54:07
   8. Diego Armando Maradona (Argentina) carries the ball, 54:07
  10. Peter Beardsley (England) is dribbled past, 54:08
  11. Diego Armando Maradona (Argentina) dribbles, 54:08
  13. Peter Reid (England) presses, 54:08
  14. Terry Butcher (England) is dribbled past, 54:13
  15. Diego Armando Maradona (Argentina) dribbles, 54:13
  17. Terry Fenwick (England) is dribbled past, 54:15
  18. Diego Armando Maradona (Argentina) dribbles, 54:15
  21. Peter Shilton (England) is dribbled past, 54:18
  22. Diego Armando Maradona (Argentina) dribbles, 54:18
  24. Diego Armando Maradona (Argentina) shoots, 54:18
"""

# The 2022 penalty buildup reaches back a possession, so the foul that won it is
# in the list: 98 is Dembélé's Foul Committed, 99 is Di María's Foul Won, and
# 100 is Messi's shot.
FACTS_2022 = """
  98. Ousmane Dembélé (France) commits a foul, 20:53
  99. Ángel Fabián Di María Hernández (Argentina) wins a foul, 20:53
 100. Lionel Andrés Messi Cuccittini (Argentina) shoots, 22:24
"""


@pytest.fixture(scope="module")
def feed():
    return StatsBombEventFeed()


@pytest.fixture(scope="module")
def facts_1986(feed):
    """Maradona's second: open play, left foot, eight players, minute 54."""
    moment = next(
        m for m in feed.defining_moments(MATCH_1986)
        if (m.minute, m.second) == GOAL_1986
    )
    return facts_from_buildup(feed.buildup(MATCH_1986, moment))


@pytest.fixture(scope="module")
def facts_penalty(feed):
    moment = next(
        m for m in feed.defining_moments(MATCH_2022)
        if (m.minute, m.second) == PENALTY_2022
    )
    return facts_from_buildup(feed.buildup(MATCH_2022, moment))


def kinds(result: GroundingResult) -> set[str]:
    return {failure.kind for failure in result.failures}


class TestGrounded:
    """Narration the check has to accept."""

    def test_a_plain_grounded_line(self, facts_1986):
        result = check(
            "Maradona dribbles and shoots, and scores for Argentina. [22, 24]",
            facts_1986,
        )
        assert result.grounded, result.summary

    def test_a_possessive_names_the_same_team(self, facts_1986):
        """The word pattern keeps apostrophes so O'Brien survives, which meant
        "Argentina's" arrived with its ending attached and matched nothing. Two
        model attempts died on this before the ending came off."""
        result = check(
            "Argentina's Maradona shoots. [24]\nMaradona's effort scores. [24]",
            facts_1986,
        )
        assert result.grounded, result.summary

    def test_a_sentence_can_start_with_an_ordinary_word(self, facts_1986):
        """Three model attempts in a row failed on "Finally", which was this
        module's bug and not the model's."""
        result = check(
            "Finally, Maradona shoots for Argentina. [24]\n"
            "However, it is close. [24]",
            facts_1986,
        )
        assert result.grounded, result.summary

    def test_a_demonym_grounds_against_its_team(self, facts_1986):
        """Fact 14 is recorded against England, which is what the demonym has
        to sit in; a demonym is checked in the cited facts like any name."""
        result = check(
            "Maradona dribbles past the English defenders for Argentina. "
            "[14, 15]",
            facts_1986,
        )
        assert result.grounded, result.summary

    def test_an_accented_name_spelled_plainly(self, facts_1986):
        """Hector for Héctor is a spelling variant of a player who is really
        there, not an invented one. Fact 6 is Enrique's pass and fact 7 is
        Maradona receiving it, so naming both ends of the pass needs both."""
        result = check("Hector Enrique passes to Maradona. [6, 7]", facts_1986)
        assert result.grounded, result.summary

    def test_the_goal_minute_and_second(self, facts_1986):
        result = check(
            "Maradona scores in minute 54, second 18. [24]", facts_1986
        )
        assert result.grounded, result.summary

    def test_a_clock_quoted_from_the_fact_it_cites(self, facts_1986):
        """A per-second clock is groundable now, which it was not before the
        facts were numbered: 54:07 is fact 7's clock, and citing fact 7 is what
        makes it something a reader can be pointed at."""
        result = check("Maradona receives it at 54:07. [7]", facts_1986)
        assert result.grounded, result.summary

    def test_one_sentence_may_span_several_facts(self, facts_1986):
        """Two defenders beaten is two `Dribbled Past` records and two
        `Dribble` records, and the sentence that says so cites all four."""
        result = check(
            "Maradona dribbles past Terry Butcher and Terry Fenwick. "
            "[14, 15, 17, 18]",
            facts_1986,
        )
        assert result.grounded, result.summary

    def test_a_penalty_narration_may_say_penalty(self, facts_penalty):
        result = check(
            "Messi scores from the penalty spot for Argentina. [100]",
            facts_penalty,
        )
        assert result.grounded, result.summary

    def test_a_penalty_narration_may_say_a_foul_was_won(self, facts_penalty):
        """"wins a foul" is a recorded Foul Won event, which is why the
        outcome-claim patterns leave "win" and "won" alone. One action per
        sentence, so the foul and the goal are two sentences."""
        result = check(
            "Di Maria wins a foul. [99]\n"
            "Messi scores from the penalty spot for Argentina. [100]",
            facts_penalty,
        )
        assert result.grounded, result.summary

    def test_tags_written_after_the_full_stops(self, facts_1986):
        """`granite4:micro` put every tag just after the full stop and ran the
        sentences together on one line, and the splitter read each tag as part
        of the sentence it started, shifting every citation by one. The layout
        is not what was wrong with that narration, so narration written this way
        and citing correctly has to pass: fact 15 is a Dribble, 16 the Carry
        beside it, 24 the shot."""
        result = check(
            "Diego Armando Maradona dribbles past a defender. [15] "
            "He carries the ball. [16] "
            "He shoots and scores for Argentina. [24]",
            facts_1986,
        )
        assert result.grounded, result.summary

    def test_every_fallback_narration_is_grounded(self, feed):
        """The fallback is grounded by construction, which is a claim worth
        testing rather than trusting. All nine goals, both matches."""
        for match_id in (MATCH_1986, MATCH_2022):
            for moment in feed.defining_moments(match_id):
                facts = facts_from_buildup(feed.buildup(match_id, moment))
                result = check(template_narration(facts), facts)
                assert result.grounded, f"{moment}: {result.summary}"


class TestNotGrounded:
    """Narration the check has to refuse."""

    def test_an_invented_player(self, facts_1986):
        result = check(
            "Maradona passes to Valdano, who scores. [6, 7]", facts_1986
        )
        assert not result.grounded
        assert kinds(result) == {"name"}
        assert "Valdano" in result.summary

    def test_a_real_player_who_is_not_in_this_passage(self, facts_1986):
        """Rule 2 of the prompt says so explicitly: a real player who is not in
        the buildup is still not something this narration can point at."""
        result = check("Burruchaga squares it for Maradona. [7]", facts_1986)
        assert not result.grounded
        assert kinds(result) == {"name"}

    def test_a_demonym_for_a_team_that_is_not_playing(self, facts_1986):
        result = check(
            "The Brazilian defender cannot stop Maradona. [22]", facts_1986
        )
        assert not result.grounded
        assert kinds(result) == {"name"}
        assert "Brazil" in result.summary

    def test_the_wrong_body_part(self, facts_1986):
        result = check("Maradona heads it in for Argentina. [24]", facts_1986)
        assert not result.grounded
        assert kinds(result) == {"body_part"}
        assert "Left Foot" in result.summary

    def test_a_goal_turned_into_a_set_piece(self, facts_1986):
        """The highest-value check here: the facts do not reveal the shot type,
        so a model can invent a penalty without contradicting anything it was
        shown."""
        result = check(
            "Maradona scores the penalty for Argentina. [24]", facts_1986
        )
        assert not result.grounded
        assert kinds(result) == {"shot_type"}
        assert "Open Play" in result.summary

    def test_a_set_piece_turned_into_the_wrong_one(self, facts_penalty):
        result = check(
            "Messi scores from the corner for Argentina. [100]", facts_penalty
        )
        assert not result.grounded
        assert kinds(result) == {"shot_type"}

    def test_an_action_that_is_not_in_the_buildup(self, facts_1986):
        result = check("Shilton saves, then Maradona scores. [21, 24]", facts_1986)
        assert not result.grounded
        assert kinds(result) == {"action"}
        assert "Goal Keeper" in result.summary

    def test_an_action_that_is_in_the_buildup_but_not_in_the_cited_facts(
        self, facts_1986
    ):
        """A miscitation, not an invention, and the report says which it is: a
        retry that reads "not in the buildup" for a dribble that is in the
        buildup would be told to drop a true sentence."""
        result = check("Maradona dribbles past a defender. [7, 8]", facts_1986)
        assert not result.grounded
        assert kinds(result) == {"action"}
        assert "not in the facts this sentence cites" in result.summary

    def test_a_number_that_is_not_a_minute(self, facts_1986):
        """7 is a second several events happened at, which is why a bare digit
        is grounded only by a minute or the goal's own second: a count would
        otherwise land on whatever second an event happened at."""
        result = check(
            "Maradona beats 7 defenders in minute 54. [22]", facts_1986
        )
        assert not result.grounded
        assert kinds(result) == {"number"}

    def test_a_clock_from_a_fact_the_sentence_did_not_cite(self, facts_1986):
        """54:07 is a real clock in this buildup: it is fact 7's. Cited against
        fact 22, which is 54:18, it is a claim about the wrong event."""
        result = check("Maradona dribbles at 54:07. [22]", facts_1986)
        assert not result.grounded
        assert kinds(result) == {"clock"}
        assert "54:07" in result.summary

    def test_a_name_in_the_buildup_but_not_in_the_cited_facts(self, facts_1986):
        """Fenwick is in the passage and fact 14 is Butcher, so this is the
        right action attached to the wrong player."""
        result = check("Terry Fenwick is dribbled past. [14]", facts_1986)
        assert not result.grounded
        assert kinds(result) == {"name"}
        assert "Fenwick" in result.summary

    def test_the_miscitation_the_first_live_run_produced(self, facts_1986):
        """The first attempt of the first live run, verbatim. Fact 17 is Terry
        Fenwick being dribbled past; Maradona carrying the ball at the same
        second is fact 19. Every word of the sentence is in the passage and the
        clock is real, and it still cites the wrong record: the wrong player and
        the wrong action, both reported against the fact it named."""
        result = check(
            "Diego Armando Maradona dribbles the ball (54:13). [15] "
            "Maradona carries the ball as he approaches the goal (54:15). [17] "
            "He shoots and scores the goal (54:18). [24]",
            facts_1986,
        )
        assert not result.grounded
        assert kinds(result) == {"name", "action"}
        assert all(f.sentence_number == 2 for f in result.failures)
        assert all("[17]" in f.value for f in result.failures)

    def test_a_sentence_that_cites_nothing(self, facts_1986):
        """Every sentence names the facts it used. One that does not cannot be
        read against anything, however true it reads."""
        result = check("Maradona shoots and scores for Argentina.", facts_1986)
        assert not result.grounded
        assert kinds(result) == {"untagged"}

    def test_a_citation_that_is_not_one_of_the_facts(self, facts_1986):
        result = check(
            "Maradona shoots and scores for Argentina. [99]", facts_1986
        )
        assert not result.grounded
        assert kinds(result) == {"citation"}
        assert "24 facts" in result.summary

    def test_a_verdict_nickname(self, facts_1986):
        result = check(
            "Maradona scores the Goal of the Century. [24]", facts_1986
        )
        assert not result.grounded
        assert "verdict nickname" in kinds(result)

    def test_an_editorial_epithet(self, facts_1986):
        """The first run that got past the name checks still called it "this
        decisive moment" and "a significant moment"."""
        result = check(
            "Maradona scores a decisive goal for Argentina. [24]", facts_1986
        )
        assert not result.grounded
        assert kinds(result) == {"editorial epithet"}

    def test_an_outcome_claim(self, facts_1986):
        """A buildup is one passage of play and carries no scoreline, so the
        result is outside the facts the narration was written from."""
        for line in (
            "Maradona scores for Argentina, securing the victory. [24]",
            "Maradona scores the winner for Argentina. [24]",
            "Maradona's goal seals the trophy for Argentina. [24]",
        ):
            result = check(line, facts_1986)
            assert not result.grounded, line
            assert "outcome claim" in kinds(result), line

    def test_an_em_dash(self, facts_1986):
        result = check(
            "Maradona turns away — and scores for Argentina. [22]", facts_1986
        )
        assert not result.grounded
        assert "em dash" in kinds(result)

    def test_narration_that_asserts_nothing_checkable(self, facts_1986):
        """Prose that names nobody and quotes no clock has nothing tracing back
        to the data, so there is nothing for the label to be true about. A pass
        here would mean "found no problem", which is not the same as grounded.
        It cites its facts, so the tags are not what refuses it.
        """
        result = check(
            "Just inside his own half, he turns away from two. [8]\n"
            "Past one, past another, still going. [11]",
            facts_1986,
        )
        assert not result.grounded
        assert kinds(result) == {"unverifiable"}

    def test_every_failing_claim_is_reported_not_just_the_first(self, facts_1986):
        """A retry and a log both need the whole list."""
        result = check(
            "Valdano passes to Burruchaga, who heads it in for Brazil. [6, 7]",
            facts_1986,
        )
        assert len(result.failures) >= 3
        assert {"name", "body_part"} <= kinds(result)

    def test_a_failure_says_which_sentence_it_was_in(self, facts_1986):
        result = check(
            "Maradona dribbles. [22]\nValdano scores. [24]", facts_1986
        )
        assert not result.grounded
        assert result.failures[0].sentence_number == 2
        assert "Valdano" in result.failures[0].sentence


class TestMisdescription:
    """The failure the old check could not see.

    Everything in a sentence can be in the passage and the sentence can still
    describe something that did not happen. This is the case `docs/VOICE.md`
    worked through as the check's limit, and it is the case the numbered facts
    and the pairing rule exist to catch.
    """

    # Beardsley, Reid and Butcher. The records show Beardsley, Butcher, Fenwick
    # and Shilton dribbled past (facts 10, 14, 17, 21) and Beardsley, Reid and
    # Butcher applying pressure (9, 13, 20). Reid pressured and was never
    # dribbled past, so this names three defenders beaten and one of them was
    # not.
    BEARDSLEY_REID_BUTCHER = (
        "Maradona dribbles past Peter Beardsley, Peter Reid and Terry Butcher, "
        "and scores for Argentina. [10, 11, 13, 14]"
    )

    # The same sentence with Reid taken out, which is true and has to pass. The
    # two together are what show the refusal is about the pairing and not about
    # the shape of the sentence.
    BEARDSLEY_AND_BUTCHER = (
        "Maradona dribbles past Peter Beardsley and Terry Butcher, "
        "and scores for Argentina. [10, 11, 14]"
    )

    def test_a_defender_who_pressured_was_not_dribbled_past(self, facts_1986):
        result = check(self.BEARDSLEY_REID_BUTCHER, facts_1986)
        assert not result.grounded, result.summary
        assert kinds(result) == {"pairing"}
        assert "Reid" in result.summary

    def test_only_the_misdescribed_name_is_reported(self, facts_1986):
        """Beardsley and Butcher were dribbled past, so the sentence is wrong
        about one defender and right about two. A report that failed all three
        would send a retry to rewrite the true part."""
        result = check(self.BEARDSLEY_REID_BUTCHER, facts_1986)
        assert len(result.failures) == 1
        assert "Beardsley" not in result.failures[0].value
        assert "Butcher" not in result.failures[0].value

    def test_the_same_sentence_without_the_wrong_name_passes(self, facts_1986):
        result = check(self.BEARDSLEY_AND_BUTCHER, facts_1986)
        assert result.grounded, result.summary

    def test_every_word_of_it_is_in_the_passage(self, facts_1986):
        """Why the old check passed it: Reid is a recorded player, a Dribble is
        a recorded action, and nothing in the sentence is invented. Membership
        was never the thing that was wrong with it."""
        assert "reid" in name_parts(facts_1986)
        assert "Dribble" in facts_1986.actions
        assert "Pressure" in facts_1986.actions

    def test_a_citation_cannot_be_chosen_to_make_it_pass(self, facts_1986):
        """Reid has one record in this passage, a `Pressure`, so no set of
        citations pairs him with a dribble. The failure is not a tagging
        mistake a model can tag its way out of."""
        every_fact = ", ".join(str(n) for n in range(1, len(facts_1986.facts) + 1))
        result = check(
            f"Maradona dribbles past Peter Reid. [{every_fact}]", facts_1986
        )
        assert not result.grounded
        assert kinds(result) == {"pairing"}


class TestPairingRefusesSomeTrueSentences:
    """The cost of pairing, named rather than left to be discovered.

    Nothing in a sentence says which name goes with which action, so a sentence
    holding one action and a name outside that action is refused even when it is
    true. The prompt asks for one action per sentence because of this, and the
    same words in two sentences pass; `docs/VOICE.md` records the trade.
    """

    def test_two_clauses_in_one_sentence_are_refused(self, facts_penalty):
        result = check(
            "Di Maria wins a foul and Messi scores for Argentina. [99, 100]",
            facts_penalty,
        )
        assert not result.grounded
        assert kinds(result) == {"pairing"}
        assert "Messi" in result.summary

    def test_the_same_words_in_two_sentences_pass(self, facts_penalty):
        result = check(
            "Di Maria wins a foul. [99]\nMessi scores for Argentina. [100]",
            facts_penalty,
        )
        assert result.grounded, result.summary


class TestSentences:
    """Reading a narration into sentences and citations."""

    def test_a_sentence_carries_the_numbers_it_cites(self):
        read = sentences("Maradona dribbles past Terry Butcher. [14, 15]")
        assert len(read) == 1
        assert read[0].cites == (14, 15)
        assert read[0].text == "Maradona dribbles past Terry Butcher."
        assert read[0].number == 1

    def test_several_sentences_are_numbered_in_order(self):
        read = sentences("First one. [1]\nThen another. [2]")
        assert [s.number for s in read] == [1, 2]
        assert [s.cites for s in read] == [(1,), (2,)]

    def test_a_tag_after_the_full_stop_belongs_to_the_sentence_before(self):
        """The prompt asks for the tag inside the sentence. A model that puts it
        just outside has still said which facts it used, and refusing that would
        throw away good copy over punctuation."""
        read = sentences("Maradona shoots. [24]")
        assert len(read) == 1
        assert read[0].cites == (24,)

    def test_the_layout_the_first_live_run_wrote(self):
        """`granite4:micro` put every tag just after the full stop and ran the
        sentences together on one line. Reading a tag as part of the chunk it
        starts shifted every citation by one and failed the narration for it,
        which was this module's bug and not the model's.
        """
        read = sentences(
            "Diego Armando Maradona dribbles past a defender. [15] "
            "He carries the ball. [17] "
            "He shoots and scores for Argentina. [24]"
        )
        assert [s.cites for s in read] == [(15,), (17,), (24,)]
        assert [s.text for s in read] == [
            "Diego Armando Maradona dribbles past a defender.",
            "He carries the ball.",
            "He shoots and scores for Argentina.",
        ]

    def test_tags_written_in_front_of_their_sentences(self):
        """The other layout a model reaches for. A leading tag goes to the
        sentence before it only while that sentence has no tag of its own, so
        this one is read the way it was meant too."""
        read = sentences("[15] Maradona dribbles. [19] Maradona carries it.")
        assert [s.cites for s in read] == [(15,), (19,)]

    def test_a_fact_number_is_not_read_as_a_clock_or_a_count(self):
        """The tag comes out of the text before any claim is read, or every
        citation would be a number claim about the match clock."""
        assert "24" not in sentences("Maradona shoots. [24]")[0].text

    def test_strip_citations_leaves_no_tag_and_one_paragraph(self):
        stripped = strip_citations(
            "Maradona dribbles past Terry Butcher. [14, 15]\n"
            "Maradona shoots and scores. [24]"
        )
        assert "[" not in stripped
        assert "\n" not in stripped
        assert stripped == (
            "Maradona dribbles past Terry Butcher. "
            "Maradona shoots and scores."
        )

    def test_strip_citations_leaves_no_space_before_the_full_stop(self):
        assert strip_citations("Maradona shoots [24].") == "Maradona shoots."


class TestHelpers:
    def test_fold_strips_accents_and_case(self):
        assert fold("Héctor") == "hector"
        assert fold("MARADONA") == "maradona"

    def test_bare_strips_a_possessive(self):
        assert bare("argentina's") == "argentina"
        assert bare("argentina’s") == "argentina"
        assert bare("butchers'") == "butchers"
        assert bare("maradona") == "maradona"

    def test_name_parts_splits_full_names(self, facts_1986):
        parts = name_parts(facts_1986)
        assert {"maradona", "diego", "argentina", "england", "shilton"} <= parts

    def test_the_demonym_table_names_only_teams_in_the_data(self):
        """The table does not generalise, and a third match needs its own
        entries. This fails if one is added without a team to back it."""
        assert set(TEAM_DEMONYMS.values()) == {"Argentina", "England", "France"}

    def test_no_banned_pattern_is_blank(self):
        """A blank pattern would match every line and fail everything."""
        for label, pattern in BANNED_PATTERNS:
            assert label and pattern

    def test_every_action_claim_names_event_types_a_fact_can_say(self):
        """A claim whose event type no fact can be phrased from could never be
        matched, so it would refuse the word wherever it appeared."""
        for word, types in ACTION_CLAIMS.items():
            assert types, word
            assert types <= set(EVENT_VERBS), (word, types - set(EVENT_VERBS))

    def test_the_two_sided_action_words_name_both_records(self):
        """"X dribbles past Y" is a `Dribble` on X's record and a `Dribbled
        Past` on Y's. Without both in the set, naming the beaten defender would
        be reported as an invented action."""
        assert ACTION_CLAIMS["dribbles"] == {"Dribble", "Dribbled Past"}
        assert ACTION_CLAIMS["passes"] == {"Pass", "Ball Receipt*"}
        assert ACTION_CLAIMS["foul"] == {"Foul Committed", "Foul Won"}


class TestResult:
    def test_a_grounded_result_says_how_much_it_checked(self, facts_1986):
        result = check(
            "Maradona shoots and scores for Argentina. [24]", facts_1986
        )
        assert result.grounded
        assert result.checked > 0
        assert "grounded" in result.summary

    def test_an_ungrounded_result_lists_its_claims(self, facts_1986):
        result = check("Valdano scores. [24]", facts_1986)
        assert not result.grounded
        assert "Valdano" in result.summary
        assert result.failures
