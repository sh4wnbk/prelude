"""Acceptance tests for the orchestrator, including the game focused header.

`app/orchestrator_contract.py` declares the shapes, the wording tables and the
functions, and every function in it raises. IBM Bob built
`app/orchestrator.py` against it (Task 4 in `docs/bob_brief.md`), and these
tests call that module. The constants and shapes are still read from the
contract, because the contract is what the wording is edited in.

**The header tests in here are red on purpose.** The header is game focused
now: it says what the goal did to the score rather than how the fan should
feel, it is the same line for every listener, and allegiance picks the persona
instead. `transition` and the new `header` are declared in the contract and
are Task 5 in `docs/bob_brief.md`. The old outcome-by-phase header tests were
removed in the same commit that added these, along with the contract tests
about `HEADER_PREFIXES`: two header tables, both tested, would have left it
unclear which one the app is meant to say.

**Nothing new is imported from `app/orchestrator.py` at the top of this
file.** A missing function imported there would be an ImportError that
collected none of these tests, and a red suite has to say which thing is not
built. `built` looks the function up by name at call time, so an absent
`transition` is one failing test with a message naming it.

**Both demo matches are covered, and one sport that does not exist.** Every
goal in `data/raw/` is read out of the feed, with the score before and after
it counted from the goals themselves, and the header each one has to produce
is written down. `TestAnotherSport` is a sixty minute game whose scores move
three at a time, which is the proof that nothing here counts in goals or in
ninety minutes, and it holds the one transition neither demo match contains.

The expected values are written out as literals next to each test, including
the ones that could be derived from the tables in the contract. A test that
computed its expectation the way the implementation will would pass whatever
the implementation did.
"""

import inspect
import json
from datetime import datetime
from pathlib import Path

import pytest

import app.orchestrator as orchestrator
from app.orchestrator_contract import (
    AHEAD,
    BEHIND,
    CLOSE_GAP,
    CONCEDED,
    DRAW_LEVEL,
    EARLY,
    EVENING_CUTOFF,
    EXTEND,
    HEADER_TAIL,
    HEADER_WORDING,
    LATE,
    LEVEL,
    MATE,
    MIDDLE,
    NEUTRAL,
    OVERTAKE,
    SCORE_LINE,
    SCORED,
    STORYTELLER,
    TAKE_LEAD,
    TEAM_A,
    TEAM_B,
    TODAY,
    TONIGHT,
    TRANSITIONS,
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
    outcome,
    phase,
    score_state,
)
from app.statsbomb_event_feed import StatsBombEventFeed

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

MATCH_1986 = 3750191
MATCH_2022 = 3869685

#: The match index files, which are a second and independent source for the
#: scoreline. `tests/test_event_feed.py` reconciles its goal counts against
#: them and the running score below is reconciled the same way: if counting
#: the goals disagrees with the recorded score, one of the two is wrong.
INDEX = {
    MATCH_1986: RAW / "matches" / "43" / "54.json",
    MATCH_2022: RAW / "matches" / "43" / "106.json",
}


def built(name: str, **arguments):
    """Call `app/orchestrator.py`'s `name`, or fail saying what is not built.

    The game focused header is Task 5 and `app/orchestrator.py` is Bob's
    module, so these tests are written against functions that are not there
    yet. The lookup happens here, by name and at call time, which is what
    keeps an unbuilt function to one failing test with a message naming it.

    The signature is checked before the call so that a function taking the old
    arguments fails saying so, rather than raising something obscure from
    inside a body that was given an `Event` where it wanted a `Listener`.
    """
    function = getattr(orchestrator, name, None)
    if function is None:
        pytest.fail(
            f"app/orchestrator.py does not define {name}() yet. It is "
            "Task 5 in docs/bob_brief.md."
        )
    try:
        inspect.signature(function).bind(**arguments)
    except TypeError as mismatch:
        pytest.fail(
            f"app/orchestrator.py's {name}() does not take "
            f"({', '.join(sorted(arguments))}): {mismatch}. It is Task 5 in "
            "docs/bob_brief.md."
        )
    return function(**arguments)


#: 1986, Argentina vs England. A 16:00 kickoff in Mexico City, so it is a
#: "today" match: the one of the two demo matches that is. The team names are
#: checked against `data/raw/` by `TestTheMomentsComeFromTheData`, and the
#: kickoff is written here because the greeting is about the listener's
#: evening rather than about anything in the event data.
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

MATCHES = {MATCH_1986: MEXICO_86, MATCH_2022: QATAR_22}

REGULATION = 90

#: Every goal in both demo matches, by match and clock, with the transition it
#: is and the header it has to produce.
#:
#: The clock and the score come out of `data/raw/`; these are written down.
#: Neither demo match holds an `OVERTAKE`: nobody in either came from behind
#: to ahead with one score, so that one is `TestAnotherSport`'s.
EXPECTED = {
    (MATCH_1986, 50, 27): (
        TAKE_LEAD,
        "Argentina take the lead. Argentina 1, England 0. Here's the buildup.",
    ),
    (MATCH_1986, 54, 18): (
        EXTEND,
        "Argentina extend the lead. Argentina 2, England 0. Here's the buildup.",
    ),
    (MATCH_1986, 80, 37): (
        CLOSE_GAP,
        "England close the gap. Argentina 2, England 1. Here's the buildup.",
    ),
    (MATCH_2022, 22, 24): (
        TAKE_LEAD,
        "Argentina take the lead. Argentina 1, France 0. Here's the buildup.",
    ),
    (MATCH_2022, 35, 22): (
        EXTEND,
        "Argentina extend the lead. Argentina 2, France 0. Here's the buildup.",
    ),
    (MATCH_2022, 79, 24): (
        CLOSE_GAP,
        "France close the gap. Argentina 2, France 1. Here's the buildup.",
    ),
    (MATCH_2022, 80, 59): (
        DRAW_LEVEL,
        "France draw level. Argentina 2, France 2. Here's the buildup.",
    ),
    (MATCH_2022, 107, 58): (
        TAKE_LEAD,
        "Argentina take the lead. Argentina 3, France 2. Here's the buildup.",
    ),
    (MATCH_2022, 117, 5): (
        DRAW_LEVEL,
        "France draw level. Argentina 3, France 3. Here's the buildup.",
    ),
}


@pytest.fixture(scope="module")
def feed():
    return StatsBombEventFeed()


def read_index(match_id: int) -> dict:
    entries = json.loads(INDEX[match_id].read_text(encoding="utf-8"))
    return next(e for e in entries if e["match_id"] == match_id)


def moments(feed, match_id: int) -> list[ScoringMoment]:
    """Every goal in one match as a `ScoringMoment`, read out of `data/raw/`.

    The score before and after is counted from the goals themselves, because a
    StatsBomb shot record carries no scoreline: each side's score at a moment
    is how many goals it has scored up to and including that one, and the
    feed returns them in clock order.
    `TestTheMomentsComeFromTheData::test_the_running_score_ends_on_the_recorded_scoreline`
    reconciles the count against the match index, which is a separate file.
    """
    event = MATCHES[match_id]
    built_moments = []
    score_a = score_b = 0
    for moment in feed.defining_moments(match_id):
        before_a, before_b = score_a, score_b
        if moment.team == event.team_a:
            side, score_a = TEAM_A, score_a + 1
        elif moment.team == event.team_b:
            side, score_b = TEAM_B, score_b + 1
        else:
            raise AssertionError(
                f"{moment.team!r} scored in {match_id} and is neither "
                f"{event.team_a!r} nor {event.team_b!r}"
            )
        built_moments.append(
            ScoringMoment(
                scoring_side=side,
                minute=moment.minute,
                second=moment.second,
                score_before_a=before_a,
                score_before_b=before_b,
                score_a=score_a,
                score_b=score_b,
                regulation_minutes=REGULATION,
            )
        )
    return built_moments


def every_goal(feed):
    """(match id, event, moment) for all nine goals in the two matches."""
    for match_id in (MATCH_1986, MATCH_2022):
        for moment in moments(feed, match_id):
            yield match_id, MATCHES[match_id], moment


def expected_for(match_id: int, moment: ScoringMoment) -> tuple[str, str]:
    key = (match_id, moment.minute, moment.second)
    assert key in EXPECTED, f"{key} is a goal nothing in this file expects"
    return EXPECTED[key]


def goals_that_are(feed, transition: str):
    """Every goal of one transition, so a failure names the transition."""
    for match_id, event, moment in every_goal(feed):
        if expected_for(match_id, moment)[0] == transition:
            yield match_id, event, moment


#: Maradona's second, 54:18, Argentina 2 England 0, from 1 England 0. Just
#: past the first third of 90 minutes, so the middle.
GOAL_54_18 = ScoringMoment(
    scoring_side=TEAM_A, minute=54, second=18,
    score_before_a=1, score_before_b=0,
    score_a=2, score_b=0, regulation_minutes=REGULATION,
)

#: Lineker's header, 80:37, Argentina 2 England 1. Past three quarters, late.
GOAL_80_37 = ScoringMoment(
    scoring_side=TEAM_B, minute=80, second=37,
    score_before_a=2, score_before_b=0,
    score_a=2, score_b=1, regulation_minutes=REGULATION,
)

#: Messi's penalty, 22:24, Argentina 1 France 0. Inside the first third.
GOAL_22_24 = ScoringMoment(
    scoring_side=TEAM_A, minute=22, second=24,
    score_before_a=0, score_before_b=0,
    score_a=1, score_b=0, regulation_minutes=REGULATION,
)

#: Mbappe's second, 80:59, Argentina 2 France 2. Late, and it levelled it.
GOAL_80_59 = ScoringMoment(
    scoring_side=TEAM_B, minute=80, second=59,
    score_before_a=2, score_before_b=1,
    score_a=2, score_b=2, regulation_minutes=REGULATION,
)

#: Messi in extra time, 107:58, Argentina 3 France 2. Past regulation, so the
#: ratio is above 1 and the phase is late.
GOAL_107_58 = ScoringMoment(
    scoring_side=TEAM_A, minute=107, second=58,
    score_before_a=2, score_before_b=2,
    score_a=3, score_b=2, regulation_minutes=REGULATION,
)

#: The five written out above, for the one test that holds them to the data.
WRITTEN_DOWN = (
    (MATCH_1986, GOAL_54_18),
    (MATCH_1986, GOAL_80_37),
    (MATCH_2022, GOAL_22_24),
    (MATCH_2022, GOAL_80_59),
    (MATCH_2022, GOAL_107_58),
)

ARGENTINA = Listener(allegiance=TEAM_A)
ENGLAND = Listener(allegiance=TEAM_B)
FRANCE = Listener(allegiance=TEAM_B)
ANYONE = Listener(allegiance=NEUTRAL)


class TestTheMomentsComeFromTheData:
    """The inputs are read out of `data/raw/`, not remembered.

    Everything the header tests are given, the clock, the teams and both
    scores, comes from the feed and the match index. Only the headers
    themselves are written down.
    """

    def test_the_fixture_teams_are_the_ones_the_data_names(self):
        for match_id in (MATCH_1986, MATCH_2022):
            entry = read_index(match_id)
            event = MATCHES[match_id]
            assert event.team_a == entry["home_team"]["home_team_name"]
            assert event.team_b == entry["away_team"]["away_team_name"]

    def test_every_goal_in_the_data_has_a_header_written_down(self, feed):
        found = {
            (match_id, moment.minute, moment.second)
            for match_id, _, moment in every_goal(feed)
        }
        assert found == set(EXPECTED)

    def test_the_running_score_ends_on_the_recorded_scoreline(self, feed):
        """The goals counted against the match index, which is another file.

        A goal missed or counted twice would move every score before and
        after it, so this is what says the inputs are the match and not an
        arithmetic of this file's own.
        """
        for match_id in (MATCH_1986, MATCH_2022):
            entry = read_index(match_id)
            last = moments(feed, match_id)[-1]
            assert (last.score_a, last.score_b) == (
                entry["home_score"],
                entry["away_score"],
            )

    def test_the_moments_written_out_here_are_ones_the_data_records(self, feed):
        """The five literal moments the phase and score tests use.

        They are written out so a phase test reads as one value and one
        answer. This is what keeps them honest, field for field, against the
        same goal read from the feed.
        """
        for match_id, written in WRITTEN_DOWN:
            clock = (written.minute, written.second)
            read = next(
                m
                for m in moments(feed, match_id)
                if (m.minute, m.second) == clock
            )
            assert read == written, f"{match_id} {clock}"


class TestTheScoringMomentRefusesAnImpossibleScore:
    """The shape holds its own invariant, which is the one bit of code here.

    A score before and a score after that no single side scoring could
    produce is a caller bug, and the two mistakes the pair invites are a
    before and an after swapped and a before copied from another moment. Both
    are caught where they are made.
    """

    def test_a_real_goal_is_accepted(self):
        assert GOAL_54_18.score_before_a == 1
        assert GOAL_54_18.score_a == 2

    def test_a_score_that_did_not_rise_is_refused(self):
        with pytest.raises(ValueError):
            ScoringMoment(
                scoring_side=TEAM_A, minute=10, second=0,
                score_before_a=1, score_before_b=0,
                score_a=1, score_b=0, regulation_minutes=REGULATION,
            )

    def test_a_score_that_fell_is_refused(self):
        """A before and an after swapped, which is what this looks like."""
        with pytest.raises(ValueError):
            ScoringMoment(
                scoring_side=TEAM_A, minute=10, second=0,
                score_before_a=2, score_before_b=0,
                score_a=1, score_b=0, regulation_minutes=REGULATION,
            )

    def test_the_other_side_moving_too_is_refused(self):
        with pytest.raises(ValueError):
            ScoringMoment(
                scoring_side=TEAM_A, minute=10, second=0,
                score_before_a=0, score_before_b=0,
                score_a=1, score_b=1, regulation_minutes=REGULATION,
            )

    def test_a_neutral_scorer_is_refused(self):
        """Somebody scored, so there is a side that did it."""
        with pytest.raises(ValueError):
            ScoringMoment(
                scoring_side=NEUTRAL, minute=10, second=0,
                score_before_a=0, score_before_b=0,
                score_a=1, score_b=0, regulation_minutes=REGULATION,
            )

    def test_a_score_may_rise_by_more_than_one(self):
        """Nothing here is counting goals: three points is a score too."""
        three = ScoringMoment(
            scoring_side=TEAM_B, minute=10, second=0,
            score_before_a=0, score_before_b=0,
            score_a=0, score_b=3, regulation_minutes=60,
        )
        assert three.score_b - three.score_before_b == 3


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
            score_before_a=0, score_before_b=0,
            score_a=1, score_b=0, regulation_minutes=90,
        )
        three_quarters = ScoringMoment(
            scoring_side=TEAM_A, minute=67, second=30,
            score_before_a=0, score_before_b=0,
            score_a=1, score_b=0, regulation_minutes=90,
        )
        assert phase(third) == MIDDLE
        assert phase(three_quarters) == LATE

    def test_the_second_counts_towards_the_phase(self):
        """29:59 and 30:00 are different phases, so the clock is not the
        minute alone."""
        before = ScoringMoment(
            scoring_side=TEAM_A, minute=29, second=59,
            score_before_a=0, score_before_b=0,
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


class TestTheTransition:
    """What the moment did to the score, from the scoring side's view.

    Read out of the score before it and the score after it, and out of
    nothing else: no transition may depend on what happened earlier in the
    match, because the two scores do not record it.
    """

    def test_level_to_ahead_takes_the_lead(self, feed):
        found = list(goals_that_are(feed, TAKE_LEAD))
        assert len(found) == 3
        for match_id, _, moment in found:
            assert built("transition", moment=moment) == TAKE_LEAD, (
                f"{match_id} {moment.minute}:{moment.second:02d}"
            )

    def test_ahead_to_further_ahead_extends(self, feed):
        found = list(goals_that_are(feed, EXTEND))
        assert len(found) == 2
        for match_id, _, moment in found:
            assert built("transition", moment=moment) == EXTEND, (
                f"{match_id} {moment.minute}:{moment.second:02d}"
            )

    def test_behind_to_still_behind_closes_the_gap(self, feed):
        found = list(goals_that_are(feed, CLOSE_GAP))
        assert len(found) == 2
        for match_id, _, moment in found:
            assert built("transition", moment=moment) == CLOSE_GAP, (
                f"{match_id} {moment.minute}:{moment.second:02d}"
            )

    def test_behind_to_level_draws_level(self, feed):
        found = list(goals_that_are(feed, DRAW_LEVEL))
        assert len(found) == 2
        for match_id, _, moment in found:
            assert built("transition", moment=moment) == DRAW_LEVEL, (
                f"{match_id} {moment.minute}:{moment.second:02d}"
            )

    def test_every_goal_gets_one_of_the_five(self, feed):
        for match_id, _, moment in every_goal(feed):
            assert built("transition", moment=moment) in TRANSITIONS, (
                f"{match_id} {moment.minute}:{moment.second:02d}"
            )

    def test_the_same_scores_give_the_same_transition_whenever_they_happen(
        self, feed
    ):
        """A transition is the two scores and not the clock.

        Argentina's first in 1986 at 50:27 and their extra time goal in 2022
        at 107:58 are both level to ahead, one of them in regulation and one
        of them past it.
        """
        early_lead = next(
            m for _, _, m in every_goal(feed)
            if (m.minute, m.second) == (50, 27)
        )
        late_lead = next(
            m for _, _, m in every_goal(feed)
            if (m.minute, m.second) == (107, 58)
        )
        assert built("transition", moment=early_lead) == built(
            "transition", moment=late_lead
        )


class TestTheHeader:
    """The transition's wording, the score, then the tail. Nothing generated.

    The whole line is written out beside each goal, including the parts that
    could be assembled from the contract's tables.
    """

    def test_the_1986_goals(self, feed):
        for match_id, event, moment in every_goal(feed):
            if match_id != MATCH_1986:
                continue
            _, expected = expected_for(match_id, moment)
            assert built("header", event=event, moment=moment) == expected, (
                f"{moment.minute}:{moment.second:02d}"
            )

    def test_the_2022_goals(self, feed):
        for match_id, event, moment in every_goal(feed):
            if match_id != MATCH_2022:
                continue
            _, expected = expected_for(match_id, moment)
            assert built("header", event=event, moment=moment) == expected, (
                f"{moment.minute}:{moment.second:02d}"
            )

    def test_it_takes_no_listener(self):
        """The header is the same line for everybody.

        Allegiance picks the persona and nothing else now, so a listener
        argument here would be a way back to a header that differs by who is
        listening.
        """
        function = getattr(orchestrator, "header", None)
        if function is None:
            pytest.fail(
                "app/orchestrator.py does not define header() yet. It is "
                "Task 5 in docs/bob_brief.md."
            )
        taken = set(inspect.signature(function).parameters)
        assert taken == {"event", "moment"}

    def test_every_header_ends_on_the_tail(self, feed):
        for match_id, event, moment in every_goal(feed):
            line = built("header", event=event, moment=moment)
            assert line.endswith(HEADER_TAIL), (
                f"{match_id} {moment.minute}:{moment.second:02d}: {line}"
            )

    def test_the_first_sentence_comes_from_the_wording_table(self, feed):
        """Every opening sentence is one the contract declares, filled in.

        Changing a word has to be a one line edit to `HEADER_WORDING`, which
        it is not if the implementation writes any of them down.
        """
        allowed = {
            wording.format(scorer=team)
            for wording in HEADER_WORDING.values()
            for team in ("Argentina", "England", "France")
        }
        for match_id, event, moment in every_goal(feed):
            line = built("header", event=event, moment=moment)
            assert line.split(". ")[0] + "." in allowed, line

    def test_the_score_sentence_is_the_score_after_the_moment(self, feed):
        for match_id, event, moment in every_goal(feed):
            line = built("header", event=event, moment=moment)
            assert SCORE_LINE.format(
                team_a=event.team_a,
                score_a=moment.score_a,
                team_b=event.team_b,
                score_b=moment.score_b,
            ) in line, line

    def test_the_scoring_side_is_the_side_the_wording_names(self, feed):
        for match_id, event, moment in every_goal(feed):
            line = built("header", event=event, moment=moment)
            scorer = (
                event.team_a if moment.scoring_side == TEAM_A else event.team_b
            )
            assert line.startswith(scorer), line

    def test_no_header_claims_a_goal_before_this_one(self, feed):
        """No "again", and no "back in front".

        Nothing the header is built from records an earlier goal, so nothing
        in it may imply one. England's only goal of 1986 is the case that
        caught the old wording: a cell reading "Your side again." was false
        for it.
        """
        for match_id, event, moment in every_goal(feed):
            line = built("header", event=event, moment=moment).lower()
            for claim in ("again", "back in front", "another", "second"):
                assert claim not in line, (
                    f"{match_id} {moment.minute}:{moment.second:02d}: {line}"
                )

    def test_a_header_never_runs_two_spaces_together(self, feed):
        for _, event, moment in every_goal(feed):
            line = built("header", event=event, moment=moment)
            assert "  " not in line
            assert line == line.strip()

    def test_no_header_carries_an_em_dash(self, feed):
        for _, event, moment in every_goal(feed):
            line = built("header", event=event, moment=moment)
            assert "—" not in line and "--" not in line


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
            header="Argentina extend the lead. Argentina 2, England 0. Here's the buildup.",
            persona="mate",
        )

    def test_neutral_listener_on_the_2022_22_24_penalty(self):
        assert PreludeOrchestrator().opening(QATAR_22, GOAL_22_24, ANYONE) == Opening(
            greeting="tonight",
            header="Argentina take the lead. Argentina 1, France 0. Here's the buildup.",
            persona="storyteller",
        )

    def test_the_header_is_the_same_line_for_every_listener(self):
        """Three listeners, one header, and only the persona differs."""
        openings = [
            PreludeOrchestrator().opening(MEXICO_86, GOAL_80_37, listener)
            for listener in (ARGENTINA, ENGLAND, ANYONE)
        ]
        assert len({o.header for o in openings}) == 1
        assert openings[0].header == (
            "England close the gap. Argentina 2, England 1. Here's the buildup."
        )
        assert {o.persona for o in openings} == {"mate", "storyteller"}


class TestAnotherSport:
    """A sport that does not exist, to prove nothing counts in football.

    Sixty minutes of regulation, three periods of twenty, and a score worth
    three points. If a 90 ever gets written into the phase rule, or a 1 into
    the transition rule, every test in this class fails and no test about the
    two demo matches does.

    It also holds the one transition neither demo match contains: behind to
    ahead, which is what a score of three over a one point lead does.
    """

    GAME = Event(
        kickoff=datetime(2026, 2, 14, 19, 30),
        team_a="Tharsis Reds",
        team_b="Elysium Blue",
        sport="gravityball",
    )
    REGULATION = 60
    STEP = 3

    def moment(self, minute, second=0, side=TEAM_A, before=(0, 0)):
        """One score of three points, by `side`, at that clock."""
        after = list(before)
        after[0 if side == TEAM_A else 1] += self.STEP
        return ScoringMoment(
            scoring_side=side, minute=minute, second=second,
            score_before_a=before[0], score_before_b=before[1],
            score_a=after[0], score_b=after[1],
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

    def test_three_points_from_level_takes_the_lead(self):
        assert built(
            "transition", moment=self.moment(10, before=(6, 6))
        ) == TAKE_LEAD

    def test_three_points_from_behind_can_overtake(self):
        """Behind by one, then ahead by two, in one score.

        Neither demo match holds this: a goal is worth one, so a side that
        was behind is level or still behind afterwards. A sport that scores
        three at a time is how the transition is reached at all, and a rule
        that read the before by subtracting one from the after would call
        this a draw level.
        """
        assert built(
            "transition", moment=self.moment(30, before=(4, 5))
        ) == OVERTAKE

    def test_three_points_from_ahead_extends(self):
        assert built(
            "transition", moment=self.moment(40, before=(9, 3))
        ) == EXTEND

    def test_three_points_from_far_behind_closes_the_gap(self):
        assert built(
            "transition", moment=self.moment(50, before=(12, 3), side=TEAM_B)
        ) == CLOSE_GAP

    def test_three_points_can_draw_it_level(self):
        assert built(
            "transition", moment=self.moment(55, before=(9, 6), side=TEAM_B)
        ) == DRAW_LEVEL

    def test_the_header_says_the_overtake_and_the_points(self):
        overtake = self.moment(30, before=(4, 5))
        assert built("header", event=self.GAME, moment=overtake) == (
            "Tharsis Reds take the lead. Tharsis Reds 7, Elysium Blue 5. "
            "Here's the buildup."
        )

    def test_the_header_reads_the_same_table_whatever_the_sport(self):
        drew = self.moment(55, before=(9, 6), side=TEAM_B)
        assert built("header", event=self.GAME, moment=drew) == (
            "Elysium Blue draw level. Tharsis Reds 9, Elysium Blue 9. "
            "Here's the buildup."
        )

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

    def test_the_wording_table_covers_every_transition(self):
        assert set(HEADER_WORDING) == set(TRANSITIONS)

    def test_the_five_transitions_are_the_five(self):
        assert TRANSITIONS == (
            TAKE_LEAD, OVERTAKE, EXTEND, CLOSE_GAP, DRAW_LEVEL
        )

    def test_every_wording_names_the_scorer_and_nothing_else(self):
        for transition, wording in HEADER_WORDING.items():
            assert "{scorer}" in wording, transition
            assert wording.format(scorer="X") == wording.replace(
                "{scorer}", "X"
            )

    def test_taking_the_lead_and_overtaking_share_their_wording(self):
        """"Take the lead" is true of both, and the difference between them
        is history the listener already has."""
        assert HEADER_WORDING[TAKE_LEAD] == HEADER_WORDING[OVERTAKE]

    def test_the_score_line_names_both_teams_and_both_scores(self):
        assert SCORE_LINE.format(
            team_a="A", score_a=1, team_b="B", score_b=2
        ) == "A 1, B 2."

    def test_the_tail_is_one_sentence_for_everybody(self):
        assert HEADER_TAIL == "Here's the buildup."

    def test_no_wording_claims_a_goal_before_this_one(self):
        """The rule the transitions are built to: no history in the header."""
        for wording in HEADER_WORDING.values():
            lowered = wording.lower()
            for claim in ("again", "back in front", "another", "second"):
                assert claim not in lowered

    def test_no_wording_carries_an_em_dash(self):
        for value in (*HEADER_WORDING.values(), SCORE_LINE, HEADER_TAIL):
            assert "—" not in value and "--" not in value
