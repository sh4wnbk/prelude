"""Tests for the zone vocabulary: a coordinate against a number, and a phrase.

`app/pitch_zones.py` is arithmetic and a word list, so these are read against
its own thresholds and then against the two hero passages in `data/raw/`. The
coordinates quoted in the docstrings came off `scripts/story_beats_report.py`
and the event files, not off memory.
"""

import pytest

from app.narration_prompt import BOX_X, HALFWAY_X, Spot, facts_from_buildup
from app.pitch_zones import (
    BOX_BOTTOM_Y,
    BOX_TOP_Y,
    DEEP_IN_OWN_HALF,
    DEEP_X,
    EDGE_OF_THE_BOX,
    EDGE_X,
    FINAL_THIRD,
    FINAL_THIRD_X,
    IN_OWN_HALF,
    IN_THEIR_HALF,
    JUST_INSIDE_OWN_HALF,
    JUST_INSIDE_THEIR_HALF,
    JUST_INSIDE_X,
    LEFT_Y,
    ON_THE_LEFT,
    ON_THE_RIGHT,
    OWN_HALF_X,
    RIGHT_Y,
    SIDES,
    THE_BOX,
    ZONES,
    holds,
    in_the_box_width,
    said_as,
    side_of,
    zone_for,
    zone_of,
)
from app.recorded_names import recorded_nicknames, recorded_teams
from app.statsbomb_event_feed import StatsBombEventFeed

MATCH_1986 = 3750191
MATCH_2022 = 3869685
HERO_1986 = (54, 18)
HERO_2022 = (35, 22)


@pytest.fixture(scope="module")
def feed():
    return StatsBombEventFeed()


def hero(feed, match_id, clock):
    moment = next(
        one
        for one in feed.defining_moments(match_id)
        if (one.minute, one.second) == clock
    )
    return facts_from_buildup(
        feed.buildup(match_id, moment),
        recorded_nicknames(match_id),
        recorded_teams(match_id),
    )


@pytest.fixture(scope="module")
def facts_1986(feed):
    return hero(feed, MATCH_1986, HERO_1986)


@pytest.fixture(scope="module")
def facts_2022(feed):
    return hero(feed, MATCH_2022, HERO_2022)


def at(x, y):
    return Spot(x=x, y=y)


class TestTheBandsUpThePitch:
    """Eight of them, each a phrase, on the thresholds the module declares."""

    def test_the_thresholds_are_the_ones_shawn_gave(self):
        assert (DEEP_X, OWN_HALF_X, HALFWAY_X) == (40.0, 50.0, 60.0)
        assert (JUST_INSIDE_X, FINAL_THIRD_X) == (70.0, 80.0)
        assert (EDGE_X, BOX_X) == (96.0, 102.0)
        assert (BOX_TOP_Y, BOX_BOTTOM_Y) == (18.0, 62.0)
        assert (LEFT_Y, RIGHT_Y) == (26.7, 53.3)

    @pytest.mark.parametrize(
        "x, zone",
        [
            (0.0, DEEP_IN_OWN_HALF),
            (39.9, DEEP_IN_OWN_HALF),
            (40.0, IN_OWN_HALF),
            (49.9, IN_OWN_HALF),
            (50.0, JUST_INSIDE_OWN_HALF),
            (59.9, JUST_INSIDE_OWN_HALF),
            (60.0, JUST_INSIDE_THEIR_HALF),
            (69.9, JUST_INSIDE_THEIR_HALF),
            (70.0, IN_THEIR_HALF),
            (79.9, IN_THEIR_HALF),
            (80.0, FINAL_THIRD),
            (95.9, FINAL_THIRD),
            (96.0, EDGE_OF_THE_BOX),
            (101.9, EDGE_OF_THE_BOX),
            (102.0, THE_BOX),
            (120.0, THE_BOX),
        ],
    )
    def test_every_band_in_the_middle_of_the_pitch(self, x, zone):
        """Down the middle by width, so only `x` decides."""
        assert zone_of(at(x, 40.0)) == zone

    def test_the_bands_are_a_partition(self):
        """Every yard of the pitch is in exactly one of them, and the eight
        are all reachable: a vocabulary with a gap in it is a coordinate
        nothing can be said about."""
        said = {zone_of(at(x / 2, 40.0)) for x in range(0, 241)}
        assert said == set(ZONES)

    def test_the_box_needs_its_width(self):
        """A ball at `x` 110 and `y` 10 is past the eighteen yard line and by
        the byline, with the goal frame between it and the posts."""
        assert zone_of(at(110.0, 10.0)) == FINAL_THIRD
        assert zone_of(at(110.0, 70.0)) == FINAL_THIRD
        assert zone_of(at(110.0, 40.0)) == THE_BOX
        assert in_the_box_width(at(110.0, 40.0))
        assert not in_the_box_width(at(110.0, 10.0))

    def test_the_edge_of_the_box_needs_it_too(self):
        assert zone_of(at(99.0, 40.0)) == EDGE_OF_THE_BOX
        assert zone_of(at(99.0, 10.0)) == FINAL_THIRD

    def test_the_box_width_is_inclusive_at_both_lines(self):
        assert zone_of(at(110.0, BOX_TOP_Y)) == THE_BOX
        assert zone_of(at(110.0, BOX_BOTTOM_Y)) == THE_BOX
        assert zone_of(at(110.0, BOX_TOP_Y - 0.1)) == FINAL_THIRD
        assert zone_of(at(110.0, BOX_BOTTOM_Y + 0.1)) == FINAL_THIRD


class TestTheSidesAcrossIt:
    """Two lines across an eighty yard pitch, and a middle third with no
    word for it."""

    @pytest.mark.parametrize(
        "y, side",
        [
            (0.0, ON_THE_LEFT),
            (26.6, ON_THE_LEFT),
            (26.7, ""),
            (40.0, ""),
            (53.3, ""),
            (53.4, ON_THE_RIGHT),
            (80.0, ON_THE_RIGHT),
        ],
    )
    def test_the_side_is_read_off_y_alone(self, y, side):
        assert side_of(at(60.0, y)) == side

    def test_the_middle_third_is_said_with_no_side(self):
        assert zone_for(at(35.2, 50.4)) == DEEP_IN_OWN_HALF
        assert side_of(at(35.2, 50.4)) == ""

    def test_a_phrase_is_the_band_and_then_the_side(self):
        assert zone_for(at(87.1, 68.6)) == "in the final third on the right"
        assert zone_for(at(25.9, 71.8)) == "deep in his own half on the right"
        assert zone_for(at(23.0, 10.0)) == "deep in his own half on the left"


class TestTheirHalfIsSaidWithTheirName:
    """"Just inside France's half", which is what a listener needs to place
    the 2022 long ball."""

    def test_the_opponent_replaces_their(self):
        assert said_as(JUST_INSIDE_THEIR_HALF, "France") == (
            "just inside France's half"
        )
        assert said_as(IN_THEIR_HALF, "England") == "in England's half"

    def test_no_opponent_leaves_the_phrase_alone(self):
        assert said_as(JUST_INSIDE_THEIR_HALF, None) == (
            JUST_INSIDE_THEIR_HALF
        )

    def test_only_the_two_bands_that_say_their_are_touched(self):
        for zone in ZONES:
            if zone in (JUST_INSIDE_THEIR_HALF, IN_THEIR_HALF):
                continue
            assert said_as(zone, "France") == zone
        for side in SIDES:
            assert said_as(side, "France") == side

    def test_the_whole_phrase_carries_the_name_and_keeps_the_side(self):
        assert zone_for(at(63.2, 68.2), "France") == (
            "just inside France's half on the right"
        )


class TestWhatAPhraseIsHeldBy:
    """`holds` is what `app/narration_grammar.py` refuses a wrong zone on."""

    def test_the_right_band_holds_and_the_others_do_not(self):
        place = at(63.2, 68.2)
        assert holds(JUST_INSIDE_THEIR_HALF, place)
        for zone in ZONES:
            if zone == JUST_INSIDE_THEIR_HALF:
                continue
            assert not holds(zone, place)

    def test_a_band_is_exclusive_inside_the_same_half(self):
        """`x` 35 is in its own half and the phrase for it is "deep"."""
        assert holds(DEEP_IN_OWN_HALF, at(35.0, 40.0))
        assert not holds(JUST_INSIDE_OWN_HALF, at(35.0, 40.0))
        assert not holds(IN_OWN_HALF, at(35.0, 40.0))

    def test_a_side_is_held_by_the_side_it_names(self):
        assert holds(ON_THE_RIGHT, at(87.1, 68.6))
        assert not holds(ON_THE_LEFT, at(87.1, 68.6))


class TestTheTwoHeroPassages:
    """The zones the records put the beats in, read off `data/raw/`."""

    def spot(self, facts, number):
        return facts.facts[number - 1].beat.start

    def test_the_1986_beats(self, facts_1986):
        """Cuciuffo's recovery, and the four `Dribble` records, which are
        the attacking side's own half of each dribble past."""
        assert zone_for(self.spot(facts_1986, 1)) == DEEP_IN_OWN_HALF
        assert zone_for(self.spot(facts_1986, 11)) == (
            "just inside his own half on the right"
        )
        assert zone_for(self.spot(facts_1986, 15)) == (
            "in the final third on the right"
        )
        assert zone_for(self.spot(facts_1986, 18)) == (
            "on the edge of the box on the right"
        )
        assert zone_for(self.spot(facts_1986, 22)) == THE_BOX
        assert zone_for(self.spot(facts_1986, 24)) == THE_BOX

    def test_the_mirrored_defending_record_is_the_other_end_of_the_pitch(
        self, facts_1986
    ):
        """Butcher's `Dribbled Past` is at `x` 33.0 and the `Dribble` that
        beat him is at 87.1, which is why a zone may only be read off the
        attacking side's own record."""
        assert round(self.spot(facts_1986, 14).x, 1) == 33.0
        assert zone_of(self.spot(facts_1986, 14)) == DEEP_IN_OWN_HALF
        assert round(self.spot(facts_1986, 15).x, 1) == 87.1
        assert zone_of(self.spot(facts_1986, 15)) == FINAL_THIRD

    def test_the_2022_beats(self, facts_2022):
        """Molina's pass, the long ball at both ends, the assist and the
        shot."""
        opponent = facts_2022.opponent
        assert opponent == "France"
        assert zone_for(self.spot(facts_2022, 1), opponent) == (
            "deep in his own half on the right"
        )
        long_ball = facts_2022.facts[8].beat
        assert zone_for(long_ball.start, opponent) == (
            "just inside France's half on the right"
        )
        assert zone_for(long_ball.end, opponent) == (
            "on the edge of the box on the right"
        )
        assert zone_for(self.spot(facts_2022, 11), opponent) == (
            "on the edge of the box on the right"
        )
        assert zone_for(self.spot(facts_2022, 13), opponent) == THE_BOX

    def test_every_recorded_location_past_the_eighteen_yard_line_is_in_the_box(
        self, facts_1986, facts_2022
    ):
        """Which is why this module and `Spot.in_the_box` agree on all of the
        real data although they read the width differently."""
        for facts in (facts_1986, facts_2022):
            for fact in facts.facts:
                for place in (fact.beat.start, fact.beat.end):
                    if place is None or place.x < BOX_X:
                        continue
                    assert in_the_box_width(place), place
                    assert place.in_the_box
