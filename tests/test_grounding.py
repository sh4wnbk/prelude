"""Tests for the grounding check.

Each test is one way a narration can be wrong, or one way it can look wrong and
be fine. The second kind matters as much as the first: the check fails a
narration whole and the pipeline throws it away, so a false positive costs a
good narration and makes a model look worse than it is. Three of the tests here
exist because the first live run produced exactly that, and the words it tripped
on ("Finally", "Argentina's", a clock the prompt itself had printed) are named
in the tests so they cannot come back.

Nothing here calls a model. The narrations are written in the test.
"""

import pytest

from app.grounding import (
    BANNED_PATTERNS,
    TEAM_DEMONYMS,
    GroundingResult,
    bare,
    check,
    fold,
    name_parts,
)
from app.narration_prompt import facts_from_buildup, template_narration
from app.statsbomb_event_feed import StatsBombEventFeed

MATCH_1986 = 3750191
MATCH_2022 = 3869685

GOAL_1986 = (54, 18)
PENALTY_2022 = (22, 24)


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
            "Maradona dribbles and shoots, and scores for Argentina.", facts_1986
        )
        assert result.grounded, result.summary

    def test_a_possessive_names_the_same_team(self, facts_1986):
        """The word pattern keeps apostrophes so O'Brien survives, which meant
        "Argentina's" arrived with its ending attached and matched nothing. Two
        model attempts died on this before the ending came off."""
        result = check(
            "Argentina's Maradona shoots. Maradona's effort scores.", facts_1986
        )
        assert result.grounded, result.summary

    def test_a_sentence_can_start_with_an_ordinary_word(self, facts_1986):
        """Three model attempts in a row failed on "Finally", which was this
        module's bug and not the model's."""
        result = check(
            "Finally, Maradona shoots for Argentina. However, it is close.",
            facts_1986,
        )
        assert result.grounded, result.summary

    def test_a_demonym_grounds_against_its_team(self, facts_1986):
        result = check(
            "Maradona dribbles past the English defenders for Argentina.",
            facts_1986,
        )
        assert result.grounded, result.summary

    def test_an_accented_name_spelled_plainly(self, facts_1986):
        """Hector for Héctor is a spelling variant of a player who is really
        there, not an invented one."""
        result = check("Hector Enrique passes to Maradona.", facts_1986)
        assert result.grounded, result.summary

    def test_the_goal_minute_and_second(self, facts_1986):
        result = check("Maradona scores in minute 54, second 18.", facts_1986)
        assert result.grounded, result.summary

    def test_a_penalty_narration_may_say_penalty(self, facts_penalty):
        result = check(
            "Messi scores from the penalty spot for Argentina.", facts_penalty
        )
        assert result.grounded, result.summary

    def test_a_penalty_narration_may_say_a_foul_was_won(self, facts_penalty):
        """"wins a foul" is a recorded Foul Won event, which is why the
        outcome-claim patterns leave "win" and "won" alone."""
        result = check(
            "Di Maria wins a foul and Messi scores for Argentina.", facts_penalty
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
        result = check("Maradona passes to Valdano, who scores.", facts_1986)
        assert not result.grounded
        assert kinds(result) == {"name"}
        assert "Valdano" in result.summary

    def test_a_real_player_who_is_not_in_this_passage(self, facts_1986):
        """Rule 1 of the prompt says so explicitly: a real player who is not in
        the buildup is still not something this narration can point at."""
        result = check("Burruchaga squares it for Maradona.", facts_1986)
        assert not result.grounded
        assert kinds(result) == {"name"}

    def test_a_demonym_for_a_team_that_is_not_playing(self, facts_1986):
        result = check(
            "The Brazilian defender cannot stop Maradona.", facts_1986
        )
        assert not result.grounded
        assert kinds(result) == {"name"}
        assert "Brazil" in result.summary

    def test_the_wrong_body_part(self, facts_1986):
        result = check("Maradona heads it in for Argentina.", facts_1986)
        assert not result.grounded
        assert kinds(result) == {"body_part"}
        assert "Left Foot" in result.summary

    def test_a_goal_turned_into_a_set_piece(self, facts_1986):
        """The highest-value check here: the run of play does not reveal the
        shot type, so a model can invent a penalty without contradicting
        anything it was shown."""
        result = check("Maradona scores the penalty for Argentina.", facts_1986)
        assert not result.grounded
        assert kinds(result) == {"shot_type"}
        assert "Open Play" in result.summary

    def test_a_set_piece_turned_into_the_wrong_one(self, facts_penalty):
        result = check("Messi scores from the corner for Argentina.", facts_penalty)
        assert not result.grounded
        assert kinds(result) == {"shot_type"}

    def test_an_action_that_is_not_in_the_buildup(self, facts_1986):
        result = check("Shilton saves, then Maradona scores.", facts_1986)
        assert not result.grounded
        assert kinds(result) == {"action"}
        assert "Goal Keeper" in result.summary

    def test_a_number_that_is_not_a_minute(self, facts_1986):
        """7 is a second several events happened at, which is why seconds are
        not groundable numbers: it would let almost any count through."""
        result = check("Maradona beats 7 defenders in minute 54.", facts_1986)
        assert not result.grounded
        assert kinds(result) == {"number"}

    def test_a_clock_from_the_middle_of_the_passage(self, facts_1986):
        result = check("Maradona receives it at 54:07 for Argentina.", facts_1986)
        assert not result.grounded
        assert kinds(result) == {"number"}

    def test_a_verdict_nickname(self, facts_1986):
        result = check("Maradona scores the Goal of the Century.", facts_1986)
        assert not result.grounded
        assert "verdict nickname" in kinds(result)

    def test_an_editorial_epithet(self, facts_1986):
        """The first run that got past the name checks still called it "this
        decisive moment" and "a significant moment"."""
        result = check(
            "Maradona scores a decisive goal for Argentina.", facts_1986
        )
        assert not result.grounded
        assert kinds(result) == {"editorial epithet"}

    def test_an_outcome_claim(self, facts_1986):
        """A buildup is one passage of play and carries no scoreline, so the
        result is outside the facts the narration was written from."""
        for line in (
            "Maradona scores for Argentina, securing the victory.",
            "Maradona scores the winner for Argentina.",
            "Maradona's goal seals the trophy for Argentina.",
        ):
            result = check(line, facts_1986)
            assert not result.grounded, line
            assert "outcome claim" in kinds(result), line

    def test_an_em_dash(self, facts_1986):
        result = check(
            "Maradona turns away — and scores for Argentina.", facts_1986
        )
        assert not result.grounded
        assert "em dash" in kinds(result)

    def test_narration_that_asserts_nothing_checkable(self, facts_1986):
        """Prose that names nobody and quotes no clock has nothing tracing back
        to the data, so there is nothing for the label to be true about. A pass
        here would mean "found no problem", which is not the same as grounded.
        """
        result = check(
            "Just inside his own half, he turns away from two. "
            "Past one, past another, still going.",
            facts_1986,
        )
        assert not result.grounded
        assert kinds(result) == {"unverifiable"}

    def test_every_failing_claim_is_reported_not_just_the_first(self, facts_1986):
        """A retry and a log both need the whole list."""
        result = check(
            "Valdano passes to Burruchaga, who heads it in for Brazil.",
            facts_1986,
        )
        assert len(result.failures) >= 3
        assert {"name", "body_part"} <= kinds(result)

    def test_a_failure_says_where_it_was(self, facts_1986):
        result = check("Maradona passes.\nValdano scores.", facts_1986)
        assert not result.grounded
        assert result.failures[0].line_number == 2
        assert "Valdano" in result.failures[0].line


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


class TestResult:
    def test_a_grounded_result_says_how_much_it_checked(self, facts_1986):
        result = check("Maradona shoots and scores for Argentina.", facts_1986)
        assert result.grounded
        assert result.checked > 0
        assert "grounded" in result.summary

    def test_an_ungrounded_result_lists_its_claims(self, facts_1986):
        result = check("Valdano scores.", facts_1986)
        assert not result.grounded
        assert "Valdano" in result.summary
        assert result.failures
