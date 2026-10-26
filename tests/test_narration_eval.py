"""Tests for the measuring code in `scripts/narration_eval.py`.

No model is called and no connection is opened: every test here reads the
event data off disk, builds the facts, and measures narration written in the
test. `tests/conftest.py` fails the suite if anything reaches the network.

`key_beats` is `app/narration_prompt.py`'s, not this script's: the fallback
narration is built to reach every key beat and the evaluation measures what
share of them a narration reached, so the two read one list. The measuring
code here is `coverage`, `Recorder` and the goal selection.

**The test that matters most is the thin narration.** A live run on the 1986
54:18 goal came back with four true sentences that take the first three facts
in order and then jump to the shot. It passes `app/grounding.py`, because
every word of it is grounded, and it skips all four dribbles, which is the
whole reason the goal is remembered. If coverage does not score that narration
low, coverage is measuring nothing and the report built on it is worthless. So
it is pinned here, with its real citations, rather than left to a live run to
notice.

The fact numbers in this file are read out of `data/raw/` and written down as
literals, the way `tests/test_grounding.py` does it, so a test says what it
expects rather than deriving it from the thing under test.
"""

import json
from pathlib import Path

import pytest

from app.narration_prompt import (
    DRIBBLE,
    FOUL,
    SHOT,
    facts_from_buildup,
    key_beats,
    template_narration,
)
from app.statsbomb_event_feed import StatsBombEventFeed
from scripts.narration_eval import Recorder, coverage, goal_moments, surname

MATCH_1986 = 3750191
MATCH_2022 = 3869685

#: The goals these tests use, by clock.
MARADONA_RUN = (54, 18)       # four dribbles past, open play
MARADONA_FIRST = (50, 27)     # one dribble past, open play
LINEKER = (80, 37)            # a header, nothing but the shot
MESSI_PENALTY = (22, 24)      # a penalty, one dribble past, Foul Won and Committed
DI_MARIA = (35, 22)           # open play, nothing but the shot
MBAPPE_PENALTY_79 = (79, 24)  # a penalty, Foul Won and Foul Committed
MBAPPE_PENALTY_117 = (117, 5)  # a penalty recorded only as a Foul Committed

#: The 54:18 facts, read from the data. The four defenders who were dribbled
#: past, each with the `Dribble` on Maradona's record at the same clock.
DRIBBLE_BEATS_54_18 = ((10, 11), (14, 15), (17, 18), (21, 22))
SHOT_54_18 = 24

#: A live first attempt from `granite4:micro`, quoted exactly, citations and
#: all. It is grounded and it misses every dribble.
THIN = (
    "[1] Jose Luis Cuciuffo recovered the ball.\n"
    "[2] Jose Luis Cuciuffo carried the ball.\n"
    "[3] Jose Luis Cuciuffo passed.\n"
    "[24] Diego Armando Maradona shot."
)

GOLDEN = Path(__file__).resolve().parent / "golden" / "ollama_development_model.json"


@pytest.fixture(scope="module")
def feed():
    return StatsBombEventFeed()


def facts_for(feed, match_id, clock):
    """The facts for one goal, found by its clock."""
    found = [
        moment
        for moment in feed.defining_moments(match_id)
        if (moment.minute, moment.second) == clock
    ]
    assert len(found) == 1, f"{len(found)} moments at {clock} in {match_id}"
    return facts_from_buildup(feed.buildup(match_id, found[0]))


class TestKeyBeats:
    """What a narration of a goal is expected to reach."""

    def test_the_1986_run_is_the_shot_and_four_dribbles(self, feed):
        beats = key_beats(facts_for(feed, MATCH_1986, MARADONA_RUN))
        assert len(beats) == 5
        assert [beat.kind for beat in beats] == [DRIBBLE] * 4 + [SHOT]
        assert beats[-1].numbers == (SHOT_54_18,)

    def test_a_dribble_beat_holds_both_sides_of_the_record(self, feed):
        """One beat of play, two records: the dribble and the player beaten.

        Citing either one says the beat happened, so both numbers are in it.
        """
        beats = key_beats(facts_for(feed, MATCH_1986, MARADONA_RUN))
        dribbles = tuple(b.numbers for b in beats if b.kind == DRIBBLE)
        assert dribbles == DRIBBLE_BEATS_54_18

    def test_a_dribble_beat_is_named_after_the_player_who_was_beaten(self, feed):
        beats = key_beats(facts_for(feed, MATCH_1986, MARADONA_RUN))
        assert beats[0].label == "dribbled past Peter Beardsley"

    def test_a_goal_with_no_dribbles_or_fouls_has_only_the_shot(self, feed):
        for clock in (LINEKER, DI_MARIA):
            beats = key_beats(facts_for(feed, MATCH_1986 if clock == LINEKER
                                        else MATCH_2022, clock))
            assert [beat.kind for beat in beats] == [SHOT]

    def test_a_penalty_adds_the_foul_that_won_it(self, feed):
        beats = key_beats(facts_for(feed, MATCH_2022, MBAPPE_PENALTY_79))
        assert [beat.kind for beat in beats] == [FOUL, SHOT]
        assert beats[0].label == "the foul that won the penalty"

    def test_a_penalty_with_only_a_foul_committed_still_has_the_foul(self, feed):
        """The 117:05 penalty has no `Foul Won` record, only the other side.

        Keying the beat on `Foul Won` alone would have left that penalty with
        the shot as its only key beat and said nothing was missing.
        """
        facts = facts_for(feed, MATCH_2022, MBAPPE_PENALTY_117)
        actions = {fact.beat.action for fact in facts.facts}
        assert "Foul Won" not in actions and "Foul Committed" in actions

        beats = key_beats(facts)
        assert [beat.kind for beat in beats] == [FOUL, SHOT]

    def test_only_a_penalty_gets_a_foul_beat(self, feed):
        """A foul in open play is not a key beat, because the task said so.

        Checked across all nine goals rather than argued: every foul beat
        belongs to a goal whose shot is recorded as a penalty.
        """
        for match_id in (MATCH_1986, MATCH_2022):
            for moment in feed.defining_moments(match_id):
                facts = facts_from_buildup(feed.buildup(match_id, moment))
                fouls = [b for b in key_beats(facts) if b.kind == FOUL]
                assert bool(fouls) == (facts.set_piece == "Penalty")

    def test_every_goal_has_exactly_one_shot_beat(self, feed):
        for match_id in (MATCH_1986, MATCH_2022):
            for moment in feed.defining_moments(match_id):
                facts = facts_from_buildup(feed.buildup(match_id, moment))
                shots = [b for b in key_beats(facts) if b.kind == SHOT]
                assert len(shots) == 1
                assert shots[0].numbers == (facts.goal_fact.number,)

    def test_the_beats_are_in_the_order_they_happened(self, feed):
        beats = key_beats(facts_for(feed, MATCH_2022, MESSI_PENALTY))
        starts = [min(beat.numbers) for beat in beats]
        assert starts == sorted(starts)
        assert [beat.kind for beat in beats] == [DRIBBLE, FOUL, SHOT]


class TestCoverage:
    """How much of the passage a narration reached."""

    def test_the_thin_narration_covers_only_the_shot(self, feed):
        """The run this metric exists for.

        Four true sentences, grounded, and every dribble missing. One beat of
        five is 20%, and anything near the top of the scale here would mean
        coverage is not measuring what it claims to.
        """
        facts = facts_for(feed, MATCH_1986, MARADONA_RUN)
        reached = coverage(THIN, facts)

        assert reached.beats == 5
        assert len(reached.covered) == 1
        assert reached.covered[0].kind == SHOT
        assert reached.share == pytest.approx(0.2)
        assert [beat.label for beat in reached.missed] == [
            "dribbled past Peter Beardsley",
            "dribbled past Terry Butcher",
            "dribbled past Terry Fenwick",
            "dribbled past Peter Shilton",
        ]

    def test_the_thin_narration_is_grounded_all_the_same(self, feed):
        """Coverage is a second question, not a stricter grounding check.

        If the check refused this narration there would be nothing for
        coverage to add. It passes, which is the point.
        """
        from app.grounding import check

        facts = facts_for(feed, MATCH_1986, MARADONA_RUN)
        assert check(THIN, facts).grounded

    def test_a_narration_that_names_every_dribble_covers_everything(self, feed):
        facts = facts_for(feed, MATCH_1986, MARADONA_RUN)
        full = (
            "[10] Peter Beardsley was dribbled past.\n"
            "[14] Terry Butcher was dribbled past.\n"
            "[17] Terry Fenwick was dribbled past.\n"
            "[21] Peter Shilton was dribbled past.\n"
            "[24] Diego Armando Maradona shot."
        )
        reached = coverage(full, facts)
        assert reached.missed == ()
        assert reached.share == 1.0

    def test_citing_either_side_of_a_dribble_covers_it(self, feed):
        """The `Dribble` and the `Dribbled Past` are one beat of play."""
        facts = facts_for(feed, MATCH_1986, MARADONA_RUN)
        beaten = coverage("[10] Peter Beardsley was dribbled past.", facts)
        dribbled = coverage("[11] Diego Armando Maradona dribbled.", facts)
        assert len(beaten.covered) == len(dribbled.covered) == 1
        assert beaten.covered[0].numbers == dribbled.covered[0].numbers

    def test_a_dribble_that_went_past_nobody_is_not_a_beat(self, feed):
        """Every `Dribble` here has a `Dribbled Past` beside it.

        The rule is that the beat comes from the `Dribbled Past` record, so a
        lone `Dribble` would not create one. This records what the data holds,
        so a later data set that breaks the assumption shows up here.
        """
        facts = facts_for(feed, MATCH_1986, MARADONA_RUN)
        dribbles = [f for f in facts.facts if f.beat.action == "Dribble"]
        beaten = [f for f in facts.facts if f.beat.action == "Dribbled Past"]
        assert len(dribbles) == len(beaten) == 4
        assert len([b for b in key_beats(facts) if b.kind == DRIBBLE]) == 4

    def test_a_narration_citing_nothing_covers_nothing(self, feed):
        facts = facts_for(feed, MATCH_1986, MARADONA_RUN)
        reached = coverage("He turned away and went again.", facts)
        assert reached.covered == ()
        assert reached.share == 0.0

    def test_the_fallback_scores_full_coverage_on_every_goal(self, feed):
        """The fallback is complete as well as grounded, on all nine goals.

        It used to score 2 of 5 on the 54:18 goal: grounded in every word and
        missing three of the four dribbles, because it collapsed the run and
        then trimmed it to a sentence budget. Code assembling a narration out
        of the facts can see every beat, so there was no reason for it to drop
        one. This is the end-to-end form of
        `tests/test_narration_prompt.py::TestTemplateNarration::test_it_cites_every_key_beat_of_the_passage`:
        the fallback and the measure have to agree, and a template row in
        `docs/narration_eval.md` below 100% means one of them has drifted.
        """
        for match_id in (MATCH_1986, MATCH_2022):
            for moment in feed.defining_moments(match_id):
                facts = facts_from_buildup(feed.buildup(match_id, moment))
                reached = coverage(template_narration(facts), facts)
                assert reached.missed == (), (
                    f"{match_id} {moment.minute}:{moment.second:02d} "
                    f"misses {[b.label for b in reached.missed]}"
                )
                assert reached.share == 1.0

    def test_coverage_of_a_single_beat_goal_is_all_or_nothing(self, feed):
        """Five of the nine goals have one key beat, so the number is thin.

        Recorded as a test because the report has to say so: a goal whose only
        key beat is the shot reads 100% for any narration the ending rule
        would let through, and that is not evidence about the model.
        """
        facts = facts_for(feed, MATCH_2022, DI_MARIA)
        goal = facts.goal_fact.number
        assert coverage(f"[{goal}] Di Maria shot.", facts).share == 1.0
        assert coverage("[1] Someone passed.", facts).share == 0.0


class TestRecorder:
    """Tokens come from the server's counters, not from counting words."""

    def test_it_reads_ollamas_own_counters(self):
        golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
        response = golden["response"]
        recorder = Recorder(inner=lambda url, body, headers: response)

        recorder("http://127.0.0.1:11434/api/generate", b"{}", {})

        assert len(recorder.calls) == 1
        call = recorder.calls[0]
        assert call.prompt_tokens == response["prompt_eval_count"]
        assert call.completion_tokens == response["eval_count"]
        assert call.seconds >= 0.0

    def test_a_response_without_counters_reports_zero(self):
        recorder = Recorder(inner=lambda url, body, headers: {"response": "hi"})
        recorder("http://127.0.0.1:11434/api/generate", b"{}", {})
        assert recorder.calls[0].prompt_tokens == 0
        assert recorder.calls[0].completion_tokens == 0

    def test_take_hands_over_the_calls_and_starts_again(self):
        recorder = Recorder(inner=lambda url, body, headers: {"eval_count": 7})
        recorder("u", b"", {})
        recorder("u", b"", {})
        assert len(recorder.take()) == 2
        assert recorder.take() == ()

    def test_it_passes_the_response_through_unchanged(self):
        answer = {"response": "text", "eval_count": 3}
        recorder = Recorder(inner=lambda url, body, headers: answer)
        assert recorder("u", b"", {}) is answer


class TestGoalSelection:
    """`--goals`, so a run can be one goal rather than all nine."""

    def test_no_argument_is_every_goal_in_both_matches(self, feed):
        chosen = goal_moments(feed, None)
        assert len(chosen) == 9
        assert {match_id for match_id, _ in chosen} == {MATCH_1986, MATCH_2022}

    def test_a_match_id_is_every_goal_in_that_match(self, feed):
        chosen = goal_moments(feed, str(MATCH_1986))
        assert len(chosen) == 3
        assert all(match_id == MATCH_1986 for match_id, _ in chosen)

    def test_a_match_and_clock_is_one_goal(self, feed):
        chosen = goal_moments(feed, f"{MATCH_1986}:54:18")
        assert len(chosen) == 1
        match_id, moment = chosen[0]
        assert (match_id, moment.minute, moment.second) == (MATCH_1986, 54, 18)

    def test_several_goals_are_comma_separated(self, feed):
        chosen = goal_moments(feed, f"{MATCH_1986}:54:18, {MATCH_2022}:22:24")
        assert [(m, o.minute) for m, o in chosen] == [
            (MATCH_1986, 54),
            (MATCH_2022, 22),
        ]

    def test_a_clock_with_no_goal_is_refused(self, feed):
        with pytest.raises(SystemExit):
            goal_moments(feed, f"{MATCH_1986}:12:34")

    def test_something_that_is_not_a_goal_reference_is_refused(self, feed):
        with pytest.raises(SystemExit):
            goal_moments(feed, "54:18")


class TestReportHelpers:
    def test_a_surname_is_the_last_word_of_a_recorded_name(self):
        assert surname("Diego Armando Maradona") == "Maradona"
        assert surname("Lionel Andrés Messi Cuccittini") == "Cuccittini"
