"""Tests for the delivery table: its shape, its bounds and its one rule.

The table is placeholders, so there are no numbers here to check. What there
is to check is everything that will be true of the numbers once Shawn sets
them, which is the whole point of writing the rules down before the values:
filling the table in is then an edit to one file and a run of the suite, and a
value the speech service would ignore fails rather than ships.

Each bound traces back to something measured or published, not to taste:

| Rule | Where it comes from |
| ---- | ------------------- |
| pitch may not go below zero | `scripts/tts_probe.py`: a lowered pitch came back byte for byte identical |
| only the Caller may carry a pause | the same probe: `<break>` moves one voice of the three |
| rate runs -50 to 100 | IBM's published guidance on `rate_percentage` |
| the goal pause is the longer one | `docs/VOICE.md`: the pause before the goal lets it land |
| the Buddy is never cheerful when the other side scored | the brief, and it is the one rule here that is about taste |

Nothing here calls the speech service or a model. The situation is read off a
moment and a listener, which is the other thing worth holding: a delivery
chosen from the narration text would be a model deciding how a fan should feel
about a goal.
"""

import pytest

from app.delivery import (
    CALLER_RATE_CEILING,
    DELIVERY,
    PITCH_CEILING,
    PITCH_FLOOR,
    RATE_CEILING,
    RATE_FLOOR,
    SITUATIONS,
    Delivery,
    DeliveryError,
    delivery,
    rows_that_should_exist,
    situation,
    validate,
)
from app.orchestrator_contract import (
    BUDDY,
    CALLER,
    CONCEDED,
    NEUTRAL,
    SCORED,
    STORYTELLER,
    TEAM_A,
    TEAM_B,
    Listener,
    ScoringMoment,
)
from app.personas import PERSONAS


def moment(scoring_side=TEAM_A):
    """The 1986 goal at 54:18, which is the hero moment of the demo."""
    return ScoringMoment(
        scoring_side=scoring_side,
        minute=54,
        second=18,
        score_before_a=1 if scoring_side == TEAM_A else 0,
        score_before_b=0,
        score_a=2 if scoring_side == TEAM_A else 1,
        score_b=0 if scoring_side == TEAM_A else 1,
        regulation_minutes=90,
    )


def changed(rows):
    """`DELIVERY` with these rows replaced or added.

    The tests that check a rule have to hand `validate` a table that breaks
    it, and the shipped table is every value `None`, so every one of them is
    the real table with one or two rows written over.
    """
    return {**DELIVERY, **rows}


class TestTheSituations:
    """Three, and they are the orchestrator's own words."""

    def test_there_are_three(self):
        assert SITUATIONS == (SCORED, CONCEDED, NEUTRAL)

    def test_a_fan_whose_side_scored_is_the_scored_situation(self):
        assert situation(moment(TEAM_A), Listener(allegiance=TEAM_A)) == SCORED

    def test_a_fan_of_the_other_side_is_the_conceded_situation(self):
        assert (
            situation(moment(TEAM_A), Listener(allegiance=TEAM_B)) == CONCEDED
        )

    def test_a_listener_with_no_side_is_the_neutral_situation(self):
        """`outcome` in `app/orchestrator.py` raises for a neutral listener,
        correctly: they neither scored nor conceded. The neutral situation is
        answered here instead of asking it.
        """
        assert (
            situation(moment(TEAM_A), Listener(allegiance=NEUTRAL)) == NEUTRAL
        )

    def test_the_same_moment_is_two_situations_for_two_listeners(self):
        """Which is the reason the table is keyed by situation at all."""
        one = moment(TEAM_A)
        assert situation(one, Listener(allegiance=TEAM_A)) != situation(
            one, Listener(allegiance=TEAM_B)
        )


class TestTheTableHasEveryRowAndNoOthers:
    def test_eight_rows(self):
        """Three personas by three situations is nine, less the Buddy's neutral
        row, which cannot exist: a partisan voice told to a listener with no
        side would be telling them they support a team they did not choose.
        """
        assert len(DELIVERY) == 8

    def test_the_rows_are_the_rows_that_should_exist(self):
        assert set(DELIVERY) == set(rows_that_should_exist())

    def test_the_buddy_has_no_neutral_row(self):
        assert (BUDDY, NEUTRAL) not in DELIVERY

    def test_every_other_persona_has_all_three(self):
        for persona_id in (CALLER, STORYTELLER):
            for where in SITUATIONS:
                assert (persona_id, where) in DELIVERY

    def test_the_shipped_table_validates(self):
        validate(DELIVERY)

    def test_a_missing_row_is_refused(self):
        short = {key: row for key, row in DELIVERY.items() if key != (CALLER, SCORED)}
        with pytest.raises(DeliveryError) as failure:
            validate(short)
        assert "missing" in str(failure.value)

    def test_a_row_that_cannot_exist_is_refused(self):
        with pytest.raises(DeliveryError) as failure:
            validate(changed({(BUDDY, NEUTRAL): Delivery()}))
        assert "cannot exist" in str(failure.value)


class TestTheValuesAreShawnsAndTheTableSaysSo:
    """The table is filled in, by ear, and every row carries a decision.

    These assert the values themselves, which is unusual for a config test
    and is the point: the numbers are a judgement nothing in this repo can
    re-derive, so the only thing that can hold them is a test saying what was
    decided. A row that drifts fails here rather than in somebody's ear six
    weeks later.
    """

    def test_every_row_is_set(self):
        assert [key for key, row in DELIVERY.items() if not row.is_set] == []

    def test_every_persona_claims_its_delivery_is_confirmed(self):
        assert [p.id for p in PERSONAS if not p.prosody_confirmed] == []

    def test_the_caller_is_quicker_except_when_the_other_side_scored(self):
        """Hurrying a fan through a goal against them is the Caller's version
        of being cheerful about it, so that row drops to the voice's own rate.
        """
        assert delivery(CALLER, SCORED).rate == 10
        assert delivery(CALLER, NEUTRAL).rate == 10
        assert delivery(CALLER, CONCEDED).rate == 0

    def test_the_caller_pauses_the_same_way_in_every_situation(self):
        """The pauses are about letting a sentence land, which does not change
        with who scored. What changes with who scored is the rate.
        """
        for where in SITUATIONS:
            row = delivery(CALLER, where)
            assert (row.sentence_break, row.goal_break) == (200, 400)

    def test_only_the_caller_carries_pauses(self):
        assert [
            key
            for key, row in DELIVERY.items()
            if key[0] != CALLER
            and (row.sentence_break is not None or row.goal_break is not None)
        ] == []

    def test_the_storyteller_is_even_in_every_situation(self):
        """It is the one the other two are set against, so it is the voice's
        own rate throughout and nothing else is set.
        """
        for where in SITUATIONS:
            row = delivery(STORYTELLER, where)
            assert (row.rate, row.pitch) == (0, None)

    def test_the_buddy_lifts_for_your_goal_and_not_for_theirs(self):
        assert (delivery(BUDDY, SCORED).rate, delivery(BUDDY, SCORED).pitch) == (
            10, 10,
        )
        assert (
            delivery(BUDDY, CONCEDED).rate, delivery(BUDDY, CONCEDED).pitch
        ) == (-10, 0)

    def test_the_buddy_is_the_only_persona_that_moves_its_pitch(self):
        """Pitch is what cheerful is mostly made of, and the Buddy is the only
        voice with a side to be cheerful about.
        """
        assert {
            key[0] for key, row in DELIVERY.items() if row.pitch
        } == {BUDDY}

    def test_the_shipped_table_satisfies_the_buddy_rule(self):
        """The rule that was written while the table was empty, now that it is
        not. The conceded row is slower and no brighter, so it passes for the
        reason it was meant to rather than for want of values to compare.
        """
        validate(DELIVERY)
        assert delivery(BUDDY, CONCEDED).rate < delivery(BUDDY, SCORED).rate
        assert delivery(BUDDY, CONCEDED).pitch < delivery(BUDDY, SCORED).pitch

    def test_the_callers_rate_ceiling_is_not_measured_yet(self):
        """It is words per minute off real audio, and nothing has measured it.

        A plausible ceiling written down now would be a guess with the look of
        a decision, and `validate` skips the check while it is `None` rather
        than enforcing an invented number. The Caller's rate being set does
        not settle this: +10 is a value somebody chose, and the ceiling is the
        number that says how high anybody may choose.
        """
        assert CALLER_RATE_CEILING is None


class TestTheBounds:
    """A value the service would ignore is refused where it is written."""

    def test_a_lowered_pitch_is_refused(self):
        """The probe's finding, enforced. `pitch_percentage` of -20 came back
        byte for byte identical on all three voices, so a negative pitch here
        would read as a decision and do nothing.
        """
        with pytest.raises(DeliveryError) as failure:
            Delivery(pitch=-20)
        assert "ignored" in str(failure.value)

    def test_pitch_at_the_floor_is_allowed(self):
        assert Delivery(pitch=PITCH_FLOOR).pitch == PITCH_FLOOR

    def test_pitch_above_the_ceiling_is_refused(self):
        with pytest.raises(DeliveryError):
            Delivery(pitch=PITCH_CEILING + 1)

    def test_a_rate_below_the_floor_is_refused(self):
        """IBM's guidance: below -50 begins to cost pronunciation."""
        with pytest.raises(DeliveryError):
            Delivery(rate=RATE_FLOOR - 1)

    def test_a_rate_above_the_ceiling_is_refused(self):
        with pytest.raises(DeliveryError):
            Delivery(rate=RATE_CEILING + 1)

    def test_a_rate_at_either_bound_is_allowed(self):
        assert Delivery(rate=RATE_FLOOR).rate == RATE_FLOOR
        assert Delivery(rate=RATE_CEILING).rate == RATE_CEILING

    def test_a_slower_rate_is_allowed_because_rate_works_both_ways(self):
        """Unlike pitch. The probe moved all three voices in both directions
        with `rate_percentage`, so the floor here is the service's guidance
        rather than a direction that does nothing.
        """
        assert Delivery(rate=-20).rate == -20

    def test_a_pause_of_zero_or_less_is_refused(self):
        for pause in (0, -1):
            with pytest.raises(DeliveryError):
                Delivery(sentence_break=pause)
            with pytest.raises(DeliveryError):
                Delivery(goal_break=pause)

    def test_the_goal_pause_may_not_be_shorter_than_the_sentence_pause(self):
        with pytest.raises(DeliveryError) as failure:
            Delivery(sentence_break=400, goal_break=200)
        assert "longer" in str(failure.value)

    def test_the_two_pauses_may_be_equal(self):
        assert Delivery(sentence_break=400, goal_break=400).goal_break == 400

    def test_none_is_not_zero(self):
        """`None` is the parameter not being sent; zero is sending it at its
        neutral value. They are different requests, so they are different
        values here.
        """
        assert Delivery().rate is None
        assert Delivery(rate=0).rate == 0
        assert Delivery().is_set is False
        assert Delivery(rate=0).is_set is True


class TestOnlyTheCallerMayPause:
    """`<break>` moves one voice of the three, so it is one persona's control."""

    def test_a_pause_on_the_storyteller_is_refused(self):
        with pytest.raises(DeliveryError) as failure:
            validate(
                changed({(STORYTELLER, SCORED): Delivery(sentence_break=400)},
                )
            )
        assert "identical" in str(failure.value)

    def test_a_pause_on_the_buddy_is_refused(self):
        with pytest.raises(DeliveryError):
            validate(
                changed({(BUDDY, SCORED): Delivery(goal_break=600)})
            )

    def test_a_pause_on_the_caller_is_allowed(self):
        validate(
            changed({
                    (CALLER, SCORED): Delivery(
                        sentence_break=300, goal_break=600
                    )
                },
            )
        )


class TestTheBuddyIsNeverCheerfulWhenTheOtherSideScored:
    """The one rule here that is about taste rather than measurement.

    A voice that brightens over a goal against your team is a voice that was
    not listening with you. Brighter and quicker is what cheerful is made of
    in the only two controls there are, so the rule is a comparison between
    the Buddy's two rows rather than a fixed number: with the table unset there
    is no number to compare against, and the relation is the only thing that
    can be stated now.
    """

    def test_a_brighter_pitch_when_the_other_side_scored_is_refused(self):
        with pytest.raises(DeliveryError) as failure:
            validate(
                changed({
                        (BUDDY, SCORED): Delivery(pitch=10),
                        (BUDDY, CONCEDED): Delivery(pitch=20),
                    },
                )
            )
        assert "brighter" in str(failure.value)

    def test_a_quicker_rate_when_the_other_side_scored_is_refused(self):
        with pytest.raises(DeliveryError) as failure:
            validate(
                changed({
                        (BUDDY, SCORED): Delivery(rate=5),
                        (BUDDY, CONCEDED): Delivery(rate=15),
                    },
                )
            )
        assert "quicker" in str(failure.value)

    def test_the_same_delivery_in_both_is_allowed(self):
        """The rule is "never brighter", not "always duller". A Buddy that
        sounds the same either way is not cheerful about a goal against the
        listener's team; it is just even.
        """
        validate(
            changed({
                    (BUDDY, SCORED): Delivery(rate=5, pitch=10),
                    (BUDDY, CONCEDED): Delivery(rate=5, pitch=10),
                },
            )
        )

    def test_a_duller_and_slower_conceded_row_is_allowed(self):
        validate(
            changed({
                    (BUDDY, SCORED): Delivery(rate=5, pitch=10),
                    (BUDDY, CONCEDED): Delivery(rate=-5, pitch=0),
                },
            )
        )

    def test_the_rule_does_not_fire_on_the_other_personas(self):
        """The Caller and the Storyteller are not partisan, so a brighter
        conceded row is not a voice celebrating against its listener. It may
        still be wrong by ear; it is not wrong by rule.
        """
        validate(
            changed({
                    (CALLER, SCORED): Delivery(pitch=0),
                    (CALLER, CONCEDED): Delivery(pitch=20),
                },
            )
        )


class TestLookup:
    def test_every_row_is_reachable(self):
        for persona_id, where in rows_that_should_exist():
            assert delivery(persona_id, where) is DELIVERY[(persona_id, where)]

    def test_an_unknown_persona_names_the_three_that_exist(self):
        with pytest.raises(KeyError) as failure:
            delivery("commentator", SCORED)
        assert "commentator" in str(failure.value)

    def test_an_unknown_situation_names_the_three_that_exist(self):
        with pytest.raises(KeyError) as failure:
            delivery(CALLER, "delighted")
        for known in SITUATIONS:
            assert known in str(failure.value)

    def test_the_buddys_neutral_row_says_why_it_does_not_exist(self):
        with pytest.raises(KeyError) as failure:
            delivery(BUDDY, NEUTRAL)
        assert "fans only" in str(failure.value)


class TestNothingHereReadsTheNarration:
    """The situation comes from the orchestrator, never from a model.

    `situation` takes a moment and a listener and nothing else. There is no
    parameter for the narration text, which is what makes "never from the
    model" a property of the signature rather than a promise in a comment.
    """

    def test_situation_takes_a_moment_and_a_listener_only(self):
        import inspect

        assert list(
            inspect.signature(situation).parameters
        ) == ["moment", "listener"]

    def test_the_situation_is_the_same_whatever_was_written(self):
        """Two listeners, one moment, and no text anywhere in the call."""
        one = moment(TEAM_A)
        assert situation(one, Listener(allegiance=TEAM_A, name="Olivia")) == (
            situation(one, Listener(allegiance=TEAM_A))
        )
