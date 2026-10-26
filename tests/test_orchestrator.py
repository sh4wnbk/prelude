"""Acceptance tests for the orchestrator.

`app/orchestrator_contract.py` declares the shapes, the wording table and the
functions, and every function in it raises. IBM Bob built
`app/orchestrator.py` against it (Task 4 in `docs/bob_brief.md`), and these
tests call that module. The constants and shapes are still read from the
contract, because the contract is what the wording is edited in.

**Both demo matches are covered, and one sport that does not exist.** The
phase of a game is a share of regulation time rather than a count of minutes,
so the rules have to hold for a 60 minute game with no changes. `TestAnother
Sport` is that proof: if a number in this module ever grows a 90 in it, that
class is what fails.

The expected values are written out as literals next to each test, including
the ones that could be derived from the table in the contract. A test that
computed its expectation the way the implementation will would pass whatever
the implementation did.
"""

from datetime import datetime

import pytest

from app.orchestrator_contract import (
    AHEAD,
    BEHIND,
    CONCEDED,
    EARLY,
    EVENING_CUTOFF,
    FAN_TAIL,
    HEADER_PREFIXES,
    LATE,
    LEVEL,
    MATE,
    MIDDLE,
    NEUTRAL,
    NEUTRAL_TAIL,
    SCORED,
    STORYTELLER,
    TEAM_A,
    TEAM_B,
    TODAY,
    TONIGHT,
    Event,
    Listener,
    Opening,
    Orchestrator,
    ScoringMoment,
)
from app.orchestrator import (
    PreludeOrchestrator,
    default_persona,
    greeting_word,
    header,
    outcome,
    phase,
    score_state,
)

#: 1986, Argentina vs England. A 16:00 kickoff in Mexico City, so it is a
#: "today" match: the one of the two demo matches that is.
MEXICO_86 = Event(
    kickoff=datetime(1986, 6, 22, 16, 0),
    team_a="Argentina",
    team_b="England",
    sport="football",
)

#: 2022, Argentina vs France. An 18:00 kickoff in Lusail, so "tonight".
QATAR_22 = Event(
    kickoff=datetime(2022, 12, 18, 18, 0),
    team_a="Argentina",
    team_b="France",
    sport="football",
)

REGULATION = 90

#: Maradona's second, 54:18, Argentina 2 England 0. Just past the first third
#: of 90 minutes, so the middle.
GOAL_54_18 = ScoringMoment(
    scoring_side=TEAM_A, minute=54, second=18,
    score_a=2, score_b=0, regulation_minutes=REGULATION,
)

#: Lineker's header, 80:37, Argentina 2 England 1. Past three quarters, late.
GOAL_80_37 = ScoringMoment(
    scoring_side=TEAM_B, minute=80, second=37,
    score_a=2, score_b=1, regulation_minutes=REGULATION,
)

#: Messi's penalty, 22:24, Argentina 1 France 0. Inside the first third.
GOAL_22_24 = ScoringMoment(
    scoring_side=TEAM_A, minute=22, second=24,
    score_a=1, score_b=0, regulation_minutes=REGULATION,
)

#: Mbappe's second, 80:59, Argentina 2 France 2. Late, and it levelled it.
GOAL_80_59 = ScoringMoment(
    scoring_side=TEAM_B, minute=80, second=59,
    score_a=2, score_b=2, regulation_minutes=REGULATION,
)

#: Messi in extra time, 107:58, Argentina 3 France 2. Past regulation, so the
#: ratio is above 1 and the phase is late.
GOAL_107_58 = ScoringMoment(
    scoring_side=TEAM_A, minute=107, second=58,
    score_a=3, score_b=2, regulation_minutes=REGULATION,
)

ARGENTINA = Listener(allegiance=TEAM_A)
ENGLAND = Listener(allegiance=TEAM_B)
FRANCE = Listener(allegiance=TEAM_B)
ANYONE = Listener(allegiance=NEUTRAL)


class TestTheGreetingWord:
    """"today" or "tonight", from the kickoff and a configured cutoff."""

    def test_an_afternoon_kickoff_is_today(self):
        assert greeting_word(MEXICO_86) == TODAY

    def test_an_evening_kickoff_is_tonight(self):
        assert greeting_word(QATAR_22) == TONIGHT

    def test_the_cutoff_itself_is_tonight(self):
        """At the cutoff counts as evening, so 17:00 is tonight."""
        at_cutoff = Event(
            kickoff=datetime(2022, 12, 18, EVENING_CUTOFF.hour,
                             EVENING_CUTOFF.minute),
            team_a="Argentina", team_b="France", sport="football",
        )
        assert greeting_word(at_cutoff) == TONIGHT

    def test_a_minute_before_the_cutoff_is_today(self):
        just_before = Event(
            kickoff=datetime(2022, 12, 18, 16, 59),
            team_a="Argentina", team_b="France", sport="football",
        )
        assert greeting_word(just_before) == TODAY

    def test_the_date_does_not_decide_it(self):
        """Only the time of day does, so the same clock gives the same word."""
        for year in (1986, 2022):
            evening = Event(
                kickoff=datetime(year, 6, 1, 20, 30),
                team_a="A", team_b="B", sport="football",
            )
            assert greeting_word(evening) == TONIGHT


class TestThePhase:
    """A share of regulation time, so it holds for any sport."""

    def test_the_first_third_is_early(self):
        assert phase(GOAL_22_24) == EARLY

    def test_between_the_thirds_and_the_three_quarters_is_the_middle(self):
        assert phase(GOAL_54_18) == MIDDLE

    def test_the_final_quarter_is_late(self):
        assert phase(GOAL_80_37) == LATE

    def test_past_regulation_is_late(self):
        """Both 2022 extra time goals are past 90, so the ratio exceeds 1."""
        assert phase(GOAL_107_58) == LATE

    def test_the_boundaries_belong_to_the_later_phase(self):
        """Exactly a third in is no longer early, so the first third is the
        first third and not a hair more."""
        third = ScoringMoment(
            scoring_side=TEAM_A, minute=30, second=0,
            score_a=1, score_b=0, regulation_minutes=90,
        )
        three_quarters = ScoringMoment(
            scoring_side=TEAM_A, minute=67, second=30,
            score_a=1, score_b=0, regulation_minutes=90,
        )
        assert phase(third) == MIDDLE
        assert phase(three_quarters) == LATE

    def test_the_second_counts_towards_the_phase(self):
        """29:59 and 30:00 are different phases, so the clock is not the
        minute alone."""
        before = ScoringMoment(
            scoring_side=TEAM_A, minute=29, second=59,
            score_a=1, score_b=0, regulation_minutes=90,
        )
        assert phase(before) == EARLY


class TestTheScoreState:
    """Ahead, level or behind, for the listener's side, after the moment."""

    def test_the_side_that_just_scored_can_be_ahead(self):
        assert score_state(GOAL_54_18, ARGENTINA) == AHEAD

    def test_the_other_side_is_behind_by_the_same_moment(self):
        assert score_state(GOAL_54_18, ENGLAND) == BEHIND

    def test_a_goal_can_level_it(self):
        assert score_state(GOAL_80_59, FRANCE) == LEVEL
        assert score_state(GOAL_80_59, ARGENTINA) == LEVEL

    def test_conceding_does_not_always_mean_behind(self):
        """Argentina conceded at 80:37 and were still 2 to 1 up."""
        assert score_state(GOAL_80_37, ARGENTINA) == AHEAD

    def test_a_neutral_listener_has_no_side_to_report(self):
        with pytest.raises(ValueError):
            score_state(GOAL_54_18, ANYONE)


class TestTheOutcome:
    """Scored or conceded, from where the listener is sitting."""

    def test_the_listeners_side_scored(self):
        assert outcome(GOAL_54_18, ARGENTINA) == SCORED

    def test_the_listeners_side_conceded(self):
        assert outcome(GOAL_54_18, ENGLAND) == CONCEDED

    def test_a_neutral_listener_did_neither(self):
        with pytest.raises(ValueError):
            outcome(GOAL_54_18, ANYONE)


class TestTheHeader:
    """A prefix from the fixed table, then the tail. Nothing generated."""

    def test_a_fan_whose_side_scored_early(self):
        assert header(GOAL_22_24, ARGENTINA) == "Great start. Here's how it happened."

    def test_a_fan_whose_side_scored_in_the_middle(self):
        assert header(GOAL_54_18, ARGENTINA) == "Good news. Here's how it happened."

    def test_a_fan_whose_side_scored_late(self):
        assert header(GOAL_107_58, ARGENTINA) == "Late one for your side. Here's how it happened."

    def test_a_late_first_goal_gets_no_again(self):
        # England's only goal of the 1986 match. The cell once read "Your side
        # again.", which was false here: the header must not claim a goal
        # before this one, because nothing it is built from records one.
        assert header(GOAL_80_37, ENGLAND) == "Late one for your side. Here's how it happened."

    def test_a_fan_whose_side_conceded_early(self):
        assert header(GOAL_22_24, FRANCE) == "Still early. Here's how it happened."

    def test_a_fan_whose_side_conceded_late_gets_no_prefix(self):
        """The late conceded cell is empty, so the tail stands alone with no
        leading space."""
        assert header(GOAL_80_37, ARGENTINA) == FAN_TAIL

    def test_a_neutral_listener_gets_the_buildup_line_and_no_prefix(self):
        assert header(GOAL_54_18, ANYONE) == NEUTRAL_TAIL
        assert header(GOAL_80_37, ANYONE) == NEUTRAL_TAIL

    def test_there_is_still_time_never_appears_late(self):
        """The one cell that would be a lie. A phone telling somebody there is
        still time when there is not is worse than a phone saying nothing."""
        for moment in (GOAL_80_37, GOAL_80_59, GOAL_107_58):
            for listener in (ARGENTINA, ENGLAND, FRANCE, ANYONE):
                assert "There's still time" not in header(moment, listener)

    def test_every_fan_header_ends_on_the_tail(self):
        for moment in (GOAL_22_24, GOAL_54_18, GOAL_80_37, GOAL_107_58):
            for listener in (ARGENTINA, ENGLAND):
                assert header(moment, listener).endswith(FAN_TAIL)

    def test_a_header_never_runs_two_spaces_together(self):
        """What an empty prefix joined carelessly produces."""
        for moment in (GOAL_22_24, GOAL_54_18, GOAL_80_37, GOAL_107_58):
            for listener in (ARGENTINA, ENGLAND, ANYONE):
                line = header(moment, listener)
                assert "  " not in line
                assert line == line.strip()

    def test_the_wording_comes_from_the_table(self):
        """Every prefix the header uses is one the contract declares, so the
        wording can be changed in one place."""
        for moment in (GOAL_22_24, GOAL_54_18, GOAL_80_37, GOAL_107_58):
            for listener in (ARGENTINA, ENGLAND):
                line = header(moment, listener)
                prefix = line[: -len(FAN_TAIL)].strip()
                assert prefix in set(HEADER_PREFIXES.values())


class TestTheDefaultPersona:
    def test_a_fan_gets_the_mate(self):
        assert default_persona(ARGENTINA) == MATE
        assert default_persona(ENGLAND) == MATE

    def test_a_neutral_listener_gets_the_storyteller(self):
        assert default_persona(ANYONE) == STORYTELLER


class TestTheOpening:
    """`opening` is what the app calls, so it is checked as a whole too."""

    def test_satisfies_the_protocol(self):
        assert isinstance(PreludeOrchestrator(), Orchestrator)

    def test_argentina_fan_on_the_1986_54_18_goal(self):
        assert PreludeOrchestrator().opening(MEXICO_86, GOAL_54_18, ARGENTINA) == Opening(
            greeting="today",
            header="Good news. Here's how it happened.",
            persona="mate",
        )

    def test_neutral_listener_on_the_2022_22_24_penalty(self):
        assert PreludeOrchestrator().opening(QATAR_22, GOAL_22_24, ANYONE) == Opening(
            greeting="tonight",
            header="Here's the buildup.",
            persona="storyteller",
        )


class TestAnotherSport:
    """A sport that does not exist, to prove nothing counts in football.

    Sixty minutes of regulation, three periods of twenty. If a 90 ever gets
    written into the phase rule, every test in this class fails and no test
    about the two demo matches does.
    """

    GAME = Event(
        kickoff=datetime(2026, 2, 14, 19, 30),
        team_a="Tharsis Reds",
        team_b="Elysium Blue",
        sport="gravityball",
    )
    REGULATION = 60

    def moment(self, minute, second=0, side=TEAM_A, score_a=1, score_b=0):
        return ScoringMoment(
            scoring_side=side, minute=minute, second=second,
            score_a=score_a, score_b=score_b,
            regulation_minutes=self.REGULATION,
        )

    def test_the_first_third_of_sixty_minutes_is_early(self):
        """Twenty minutes in, which is late in a 90 minute game and early
        here."""
        assert phase(self.moment(19)) == EARLY

    def test_a_minute_that_is_early_in_football_is_the_middle_here(self):
        assert phase(self.moment(25)) == MIDDLE

    def test_the_final_quarter_of_sixty_minutes_is_late(self):
        assert phase(self.moment(45)) == LATE

    def test_an_evening_kickoff_is_tonight_whatever_the_sport(self):
        assert greeting_word(self.GAME) == TONIGHT

    def test_the_header_table_is_the_same_table(self):
        home = Listener(allegiance=TEAM_A)
        assert header(self.moment(10), home) == "Great start. Here's how it happened."
        assert header(self.moment(50), home) == "Late one for your side. Here's how it happened."

    def test_a_neutral_listener_gets_the_same_line(self):
        assert header(self.moment(10), Listener(allegiance=NEUTRAL)) == NEUTRAL_TAIL

    def test_the_default_persona_does_not_depend_on_the_sport(self):
        assert default_persona(Listener(allegiance=TEAM_B)) == MATE
        assert default_persona(Listener(allegiance=NEUTRAL)) == STORYTELLER


class TestTheContractItself:
    """The parts that are declared rather than implemented.

    These pass now. They are here so that a change to the wording table or the
    cutoff is a deliberate edit to a value the tests name, rather than
    something that slips through because every test that would have noticed is
    failing for another reason.
    """

    def test_the_cutoff_is_five_in_the_afternoon(self):
        assert (EVENING_CUTOFF.hour, EVENING_CUTOFF.minute) == (17, 0)

    def test_the_table_covers_every_outcome_and_phase(self):
        for what in (SCORED, CONCEDED):
            for when in (EARLY, MIDDLE, LATE):
                assert (what, when) in HEADER_PREFIXES

    def test_the_late_conceded_cell_is_empty(self):
        assert HEADER_PREFIXES[(CONCEDED, LATE)] == ""

    def test_there_is_still_time_is_not_in_the_late_row(self):
        assert "There's still time" not in HEADER_PREFIXES[(CONCEDED, LATE)]
        assert HEADER_PREFIXES[(CONCEDED, MIDDLE)] == "There's still time."

    def test_the_two_tails_differ(self):
        """A neutral listener is not told "how it happened" to their side."""
        assert FAN_TAIL != NEUTRAL_TAIL

    def test_no_wording_in_the_table_carries_an_em_dash(self):
        for value in (*HEADER_PREFIXES.values(), FAN_TAIL, NEUTRAL_TAIL):
            assert "—" not in value and "--" not in value
