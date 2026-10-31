"""Tests for the goal-call grammar: the pieces behind the eight references.

`tests/test_reference_narrations.py` holds the standard end to end: eight
narrations that have to pass the check word for word. This file is the other
half of the same work, one mechanism at a time, because a reference that passes
says the whole chain worked and not which link did.

Nothing here calls a model, and nothing here calls `check`. These are the
grammar's own functions in `app/narration_grammar.py`, read against the two
hero buildups in `data/raw/`.
"""

import pytest

from app.grounding import ACTION_CLAIMS, NOT_A_NAME, TEAM_DEMONYMS
from app.narration_grammar import (
    CLAUSE_BREAK,
    STRAIGHT_TOLERANCE_YARDS,
    Reader,
    carry_path,
    name_keys,
    player_spots,
    recorded_spellings,
    strays_from_straight,
    support,
    touched,
    why,
)
from app.narration_prompt import Spot, facts_from_buildup
from app.recorded_names import recorded_nicknames
from app.statsbomb_event_feed import StatsBombEventFeed

MATCH_1986 = 3750191
MATCH_2022 = 3869685
HERO_1986 = (54, 18)
HERO_2022 = (35, 22)

MARADONA = "Diego Armando Maradona"
CUCIUFFO = "José Luis Cuciuffo"
ENRIQUE = "Héctor Adolfo Enrique"
BEARDSLEY = "Peter Beardsley"
SHILTON = "Peter Shilton"
MOLINA = "Nahuel Molina Lucero"
MAC_ALLISTER = "Alexis Mac Allister"
MESSI = "Lionel Andrés Messi Cuccittini"
ALVAREZ = "Julián Álvarez"
DI_MARIA = "Ángel Fabián Di María Hernández"


@pytest.fixture(scope="module")
def feed():
    return StatsBombEventFeed()


def hero(feed, match_id, clock):
    moment = next(
        m
        for m in feed.defining_moments(match_id)
        if (m.minute, m.second) == clock
    )
    return facts_from_buildup(
        feed.buildup(match_id, moment), recorded_nicknames(match_id)
    )


@pytest.fixture(scope="module")
def facts_1986(feed):
    return hero(feed, MATCH_1986, HERO_1986)


@pytest.fixture(scope="module")
def facts_2022(feed):
    return hero(feed, MATCH_2022, HERO_2022)


def reader(facts):
    return Reader(
        facts=facts,
        not_a_name=NOT_A_NAME,
        demonyms=TEAM_DEMONYMS,
        actions=ACTION_CLAIMS,
    )


def moves(facts, *sentences):
    """Every move a run of sentences makes, read by one reader in order."""
    one = reader(facts)
    found = []
    for sentence in sentences:
        found += list(one.read(sentence))
    return found


def kinds(found):
    return [move.kind for move in found]


def ungrounded(facts, found):
    return [move for move in found if not support(move, facts)]


class TestTheNamesAGoalCallMaySay:
    """Any run of words of a recorded name, where it picks out one player."""

    def test_both_recorded_spellings_are_name_keys(self, facts_2022):
        """The event feed's full name and the lineups file's nickname."""
        assert recorded_spellings(facts_2022)[MAC_ALLISTER] == (
            "Alexis Mac Allister",
            "Alexis MacAllister",
        )
        keys = name_keys(facts_2022)
        assert keys["macallister"] == (MAC_ALLISTER,)
        assert keys["allister"] == (MAC_ALLISTER,)
        assert keys["mac allister"] == (MAC_ALLISTER,)
        assert keys["cuccittini"] == (MESSI,)
        assert keys["di maria"] == (DI_MARIA,)

    def test_an_accent_is_folded_away(self, facts_2022):
        """"Alvarez" is a spelling of a player who is really there."""
        keys = name_keys(facts_2022)
        assert keys["alvarez"] == (ALVAREZ,)
        assert keys["julian"] == (ALVAREZ,)

    def test_a_forename_two_players_share_fits_neither(self, facts_1986):
        """Which is what makes "Terry" and "Peter" refusable."""
        keys = name_keys(facts_1986)
        assert keys["terry"] == ("Terry Butcher", "Terry Fenwick")
        assert keys["peter"] == (BEARDSLEY, "Peter Reid", SHILTON)
        assert keys["peter shilton"] == (SHILTON,)
        assert keys["shilton"] == (SHILTON,)

    def test_a_name_the_match_does_not_record_is_no_key(self, facts_1986):
        """"Leo" and "Diego Maradona" are not spellings this data holds."""
        keys = name_keys(facts_1986)
        assert "leo" not in keys
        assert "diego maradona" not in keys
        assert keys["diego armando"] == (MARADONA,)

    def test_an_invented_name_is_reported_rather_than_skipped(self, facts_1986):
        found = moves(facts_1986, "Burruchaga shot and scored.")
        assert kinds(found)[0] == "unknown_name"
        assert "nobody this passage records" in why(found[0], facts_1986)

    def test_an_ordinary_capitalised_word_is_not_a_name(self, facts_1986):
        """The sentence openers a goal call uses, and nothing reported."""
        for opener in ("It", "He", "In", "We", "Then", "Finally"):
            found = moves(facts_1986, f"{opener} started the counter.")
            assert "unknown_name" not in kinds(found), opener


class TestThePlayerAPronounMeans:
    """"He" is the player with the ball, which is a recorded touch."""

    def test_only_players_with_a_touch_are_followed(self, facts_1986):
        """The four defenders beaten have no touch in the passage.

        Beardsley, Butcher, Fenwick and Shilton are recorded with a `Pressure`
        or a `Dribbled Past` and nothing else, and being beaten is not having
        the ball. Reid only pressed.
        """
        assert touched(facts_1986) == frozenset({CUCIUFFO, ENRIQUE, MARADONA})

    def test_everyone_in_the_2022_counter_touched_it(self, facts_2022):
        assert touched(facts_2022) == frozenset(
            {MOLINA, MAC_ALLISTER, MESSI, ALVAREZ, DI_MARIA}
        )

    def test_three_defenders_named_in_between_do_not_steal_the_pronoun(
        self, facts_1986
    ):
        """The Storyteller's line is why the rule is a touch and not recency.

        "past Beardsley, Butcher and Fenwick and took it into the box, where he
        went around Peter Shilton": the plainest reading of "the most recently
        named player" makes that "he" mean Fenwick.
        """
        found = moves(
            facts_1986,
            "Maradona carried it past Beardsley, Butcher and Fenwick and took "
            "it into the box, where he went around Peter Shilton and scored.",
        )
        around = [move for move in found if move.kind == "past"]
        assert [move.target for move in around] == [
            BEARDSLEY,
            "Terry Butcher",
            "Terry Fenwick",
            SHILTON,
        ]
        assert {move.actor for move in around} == {MARADONA}
        assert not ungrounded(facts_1986, found)

    def test_the_pronoun_carries_across_a_full_stop(self, facts_2022):
        """The 2022 Storyteller's second sentence opens on it.

        "whose long ball forward found MacAllister again. He set it up for Di
        María": one reader per narration, so the "He" is still MacAllister.
        """
        found = moves(
            facts_2022,
            "Álvarez found MacAllister again.",
            "He set it up for Di María, who finished it.",
        )
        chains = [move for move in found if move.kind == "chain"]
        assert [(move.actor, move.target) for move in chains] == [
            (ALVAREZ, MAC_ALLISTER),
            (MAC_ALLISTER, DI_MARIA),
        ]
        assert not ungrounded(facts_2022, found)

    def test_a_possessive_resolves_the_same_way(self, facts_1986):
        found = moves(
            facts_1986,
            "Enrique played it to Maradona in his own half, and he scored "
            "with his left foot.",
        )
        positions = [move for move in found if move.kind == "position"]
        assert [move.actor for move in positions] == [MARADONA]
        assert not ungrounded(facts_1986, found)


class TestTheChain:
    """"X to Y" is a recorded pass from X to Y, in any of its forms."""

    @pytest.mark.parametrize(
        "said",
        [
            "Molina to MacAllister",
            "Molina played it to MacAllister",
            "Molina gave it to MacAllister",
            "Molina found MacAllister",
            "Molina moved it on to MacAllister",
        ],
    )
    def test_every_form_reads_as_the_same_pass(self, said, facts_2022):
        found = moves(facts_2022, f"{said}, who shot and scored.")
        chains = [move for move in found if move.kind == "chain"]
        assert [(move.actor, move.target) for move in chains] == [
            (MOLINA, MAC_ALLISTER)
        ]
        assert support(chains[0], facts_2022)

    def test_a_pass_the_records_do_not_hold_is_refused(self, facts_2022):
        found = moves(facts_2022, "Molina to Messi, who shot and scored.")
        chain = next(move for move in found if move.kind == "chain")
        assert not support(chain, facts_2022)
        assert "no pass from" in why(chain, facts_2022)

    def test_set_up_has_to_be_the_recorded_assist(self, facts_2022):
        """"He set up Di María" is a claim about `goal_assist`.

        MacAllister's pass carries the flag. Molina's pass to MacAllister is a
        recorded pass and is not the assist, so the same words about it are
        refused.
        """
        held = moves(facts_2022, "MacAllister set up Di María, who scored.")
        assert not ungrounded(facts_2022, held)
        wrong = moves(facts_2022, "Molina set up MacAllister, who scored.")
        chain = next(move for move in wrong if move.kind == "chain")
        assert not support(chain, facts_2022)
        assert "recorded as the assist" in why(chain, facts_2022)

    def test_a_long_ball_and_the_chain_beside_it_are_one_pass(self, facts_2022):
        """So that one record has to be both, rather than two records each
        being one of the two."""
        found = moves(
            facts_2022,
            "Álvarez hit a long ball forward to MacAllister, who set up Di "
            "María to score.",
        )
        chains = [move for move in found if move.kind == "chain"]
        assert chains[0].detail["long"] is True
        assert chains[0].actor == ALVAREZ
        assert support(chains[0], facts_2022)
        assert not ungrounded(facts_2022, found)

    def test_a_pass_that_is_not_long_enough_is_refused_as_a_long_ball(
        self, facts_2022
    ):
        """Messi's ball to Álvarez is 11.5 yards."""
        found = moves(
            facts_2022,
            "Messi hit a long ball forward to Álvarez, who shot and scored.",
        )
        chain = next(move for move in found if move.kind == "chain")
        assert not support(chain, facts_2022)
        assert "long pass" in why(chain, facts_2022)

    def test_a_marker_with_no_name_after_it_claims_nothing(self, facts_2022):
        """"In the box to score" has the bare marker in it and no chain.

        A "to" that is not followed by a player is ordinary English, and
        reading it as a chain would refuse the reference it is taken from.
        """
        found = moves(
            facts_2022, "MacAllister set up Di María in the box to score."
        )
        assert kinds(found).count("chain") == 1
        assert not ungrounded(facts_2022, found)


class TestTheActorOfAClaim:
    """Which player a claim is about, read from the words around it."""

    def test_a_name_before_the_claim_owns_it(self, facts_1986):
        found = moves(facts_1986, "Cuciuffo's recovery started it, and he shot.")
        action = next(move for move in found if move.kind == "action")
        assert action.actor == CUCIUFFO

    def test_two_names_before_one_claim_both_own_it(self, facts_1986):
        """"Beardsley and Reid closed him down" is two `Pressure` records."""
        found = moves(
            facts_1986,
            "Beardsley and Reid closed him down, and Maradona scored.",
        )
        pressure = [
            move
            for move in found
            if move.kind == "action" and "Pressure" in (move.detail or ())
        ]
        assert {move.actor for move in pressure} == {BEARDSLEY, "Peter Reid"}
        assert not ungrounded(facts_1986, found)

    def test_the_action_can_come_before_the_name(self, facts_1986):
        """Which is the framework's rule, and "We won it back through
        Cuciuffo" is the reference that needs it."""
        found = moves(
            facts_1986, "We won it back through Cuciuffo, and Maradona scored."
        )
        recovery = next(
            move
            for move in found
            if move.kind == "action" and "Ball Recovery" in (move.detail or ())
        )
        assert recovery.actor == CUCIUFFO
        assert not ungrounded(facts_1986, found)

    def test_a_name_past_a_comma_is_not_the_actor(self, facts_1986):
        """The 1986 Buddy's England line is why the look-ahead stops at one.

        "picked it up in his own half, and though Beardsley and Reid closed him
        down": without the clause boundary, the half the ball was in belongs to
        Beardsley, who is never in his own half in this passage.
        """
        assert CLAUSE_BREAK.search("half, and though")
        found = moves(
            facts_1986,
            "Maradona picked it up in his own half, and though Beardsley and "
            "Reid closed him down, he scored.",
        )
        position = next(move for move in found if move.kind == "position")
        assert position.actor == MARADONA
        assert not ungrounded(facts_1986, found)

    def test_with_no_name_either_side_it_is_the_player_with_the_ball(
        self, facts_1986
    ):
        """"Around Peter Shilton, and finished with his left": the defender
        beaten is spoken for, so the finish belongs to Maradona."""
        found = moves(
            facts_1986,
            "Maradona carried it into the box, around Peter Shilton, and "
            "finished with his left.",
        )
        shot = next(
            move
            for move in found
            if move.kind == "action" and "Shot" in (move.detail or ())
        )
        assert shot.actor == MARADONA
        assert not ungrounded(facts_1986, found)


class TestPastAndAround:
    """"Past X" is a `Dribbled Past` on X and a `Dribble` at the same clock."""

    @pytest.mark.parametrize("said", ["past", "around", "round"])
    def test_each_preposition_reads_as_a_dribble(self, said, facts_1986):
        found = moves(
            facts_1986, f"Maradona went {said} Peter Shilton and scored."
        )
        beaten = next(move for move in found if move.kind == "past")
        assert beaten.target == SHILTON
        assert beaten.actor == MARADONA
        held = support(beaten, facts_1986)
        assert {beat.action for beat in held} == {"Dribble", "Dribbled Past"}

    def test_a_player_who_was_only_pressed_past_is_refused(self, facts_1986):
        """Reid's one record in this passage is a `Pressure`.

        This is the misdescription the cited reading already refuses, said in
        the goal call's own words: every name is in the buildup and a dribble
        is in it, and Reid was never dribbled past.
        """
        found = moves(facts_1986, "Maradona went past Peter Reid and scored.")
        beaten = next(move for move in found if move.kind == "past")
        assert not support(beaten, facts_1986)
        assert "no dribble past Peter Reid" in why(beaten, facts_1986)

    def test_the_dribble_has_to_be_at_the_defenders_clock(self, facts_1986):
        """Which is what pairs the two records of one beat.

        Cuciuffo has no `Dribble` at all, so no clock of his can meet
        Beardsley's `Dribbled Past`.
        """
        found = moves(facts_1986, "Cuciuffo went past Beardsley and scored.")
        beaten = next(move for move in found if move.kind == "past")
        assert not support(beaten, facts_1986)


class TestWhereOnThePitch:
    """A position claim is one coordinate against one of the pitch's lines."""

    def test_a_pass_the_player_did_not_follow_is_not_his_position(
        self, facts_2022
    ):
        """MacAllister's assist ends inside the box and he does not.

        He played it from x 99.3, four yards outside, and a pass end is where
        the ball arrived rather than where the passer went. Counting it would
        put him in the box.
        """
        spots = player_spots(facts_2022, MAC_ALLISTER)
        assert not any(place.in_the_box for place in spots)
        found = moves(facts_2022, "MacAllister in the box set up Di María.")
        position = next(move for move in found if move.kind == "position")
        assert not support(position, facts_2022)

    def test_a_carry_takes_the_player_with_it(self, facts_1986):
        """Which is how "took it into the box" is true of Maradona: the carry
        that ends the run ends at x 112.8."""
        spots = player_spots(facts_1986, MARADONA)
        assert any(place.in_the_box for place in spots)
        assert any(place.in_own_half for place in spots)

    def test_the_run_up_never_leaves_its_own_half(self, facts_1986):
        for player in (CUCIUFFO, ENRIQUE):
            spots = player_spots(facts_1986, player)
            assert all(place.in_own_half for place in spots)
            assert not any(place.in_the_box for place in spots)

    def test_the_scorer_is_not_in_his_own_half_in_2022(self, facts_2022):
        """Di María's two records are both inside the box, so "in his own
        half" about him is refused."""
        spots = player_spots(facts_2022, DI_MARIA)
        assert all(place.in_the_box for place in spots)
        found = moves(facts_2022, "Di María in his own half shot and scored.")
        position = next(move for move in found if move.kind == "position")
        assert not support(position, facts_2022)


class TestTheShapeOfTheRun:
    """"Straight" is a claim the start and end of every carry can refuse."""

    def test_the_1986_run_is_not_straight(self, facts_1986):
        """It goes out towards the touchline and back in again."""
        path = carry_path(facts_1986, MARADONA)
        assert path[0] == Spot(55.2, 55.6)
        assert path[-1] == Spot(113.4, 49.5)
        strays = strays_from_straight(path)
        assert strays == pytest.approx(16.3, abs=0.1)
        assert strays > STRAIGHT_TOLERANCE_YARDS

    def test_a_straight_line_strays_nothing(self):
        path = (Spot(20.0, 40.0), Spot(60.0, 40.0), Spot(100.0, 40.0))
        assert strays_from_straight(path) == pytest.approx(0.0)

    def test_a_path_with_nothing_to_measure_is_not_called_straight(self):
        assert strays_from_straight(()) is None
        assert strays_from_straight((Spot(1.0, 1.0), Spot(2.0, 2.0))) is None

    def test_the_claim_is_refused_over_the_1986_carries(self, facts_1986):
        found = moves(
            facts_1986, "Maradona took it straight into the box and scored."
        )
        straight = next(move for move in found if move.kind == "straight")
        assert not support(straight, facts_1986)
        assert "stray 16 yards" in why(straight, facts_1986)


class TestTheRecordedFieldsSaidOutLoud:
    """The fields step 1 put on the facts, now said in a sentence."""

    def test_the_counter(self, facts_2022):
        found = moves(facts_2022, "Argentina were on the counter and scored.")
        pattern = next(move for move in found if move.kind == "pattern")
        assert pattern.actor == "Argentina"
        assert support(pattern, facts_2022)

    def test_no_pattern_claim_can_be_refused_with_this_data(
        self, facts_1986, facts_2022
    ):
        """Recorded rather than left to be discovered: the rule is untested.

        `play_pattern` belongs to the possession, so every record of a passage
        carries the same one, and both hero passages are "From Counter"
        throughout. There is no player and no team in either of them that a
        false pattern claim could be made about, so the refusal branch is
        specified and unexercised, exactly like the free kick and corner
        branches in `app/event_feed.py`.

        What is refused instead is the team: France has no record in the 2022
        counter, so a sentence putting France on it names nobody the passage
        holds.
        """
        for facts in (facts_1986, facts_2022):
            assert facts.play_patterns == frozenset({"From Counter"})
        found = moves(facts_2022, "France were on the counter and scored.")
        assert "unknown_name" in kinds(found)
        assert "France" not in facts_2022.teams

    def test_under_pressure_is_refused_where_nothing_records_it(
        self, facts_1986, facts_2022
    ):
        held = moves(facts_1986, "Maradona carried it under pressure and scored.")
        assert not ungrounded(facts_1986, held)
        for player in ("Cuciuffo", "Enrique"):
            found = moves(
                facts_1986, f"{player} carried it under pressure, and Maradona scored."
            )
            pressed = next(move for move in found if move.kind == "pressured")
            assert not support(pressed, facts_1986)
        found = moves(facts_2022, "Messi carried it under pressure to Álvarez, who scored.")
        pressed = next(move for move in found if move.kind == "pressured")
        assert not support(pressed, facts_2022)

    def test_first_time_is_the_2022_shot_and_not_the_1986_one(
        self, facts_1986, facts_2022
    ):
        held = moves(facts_2022, "Di María finished it first time.")
        assert not ungrounded(facts_2022, held)
        found = moves(facts_1986, "Maradona finished it first time.")
        struck = next(move for move in found if move.kind == "first_time")
        assert not support(struck, facts_1986)
        assert "not recorded as struck first time" in why(struck, facts_1986)

    def test_with_one_touch_says_the_same_thing(self, facts_2022):
        found = moves(facts_2022, "Di María, with one touch, finished it.")
        assert [move.kind for move in found].count("first_time") == 1
        assert not ungrounded(facts_2022, found)

    def test_the_body_part_is_the_goals(self, facts_2022):
        held = moves(facts_2022, "Di María finished it with his left foot.")
        assert not ungrounded(facts_2022, held)
        for said in ("with his right foot", "with a header"):
            found = moves(facts_2022, f"Di María finished it {said}.")
            part = next(move for move in found if move.kind == "body_part")
            assert not support(part, facts_2022)

    def test_his_left_on_its_own_is_the_same_claim(self, facts_2022):
        found = moves(facts_2022, "Di María finished it with his left.")
        part = next(move for move in found if move.kind == "body_part")
        assert part.detail == "Left Foot"
        assert support(part, facts_2022)

    def test_the_duration_is_the_span_of_the_passage(self, facts_2022):
        found = moves(facts_2022, "In under ten seconds Di María scored.")
        span = next(move for move in found if move.kind == "duration")
        assert span.detail == ("under", 10)
        assert support(span, facts_2022)

    def test_a_duration_the_passage_did_not_take(self, facts_1986, facts_2022):
        """The 1986 run is 15.7 seconds, so "under ten" is false of it."""
        found = moves(facts_1986, "In under ten seconds Maradona scored.")
        span = next(move for move in found if move.kind == "duration")
        assert not support(span, facts_1986)
        assert "15.7 seconds" in why(span, facts_1986)
        found = moves(facts_2022, "In over ten seconds Di María scored.")
        span = next(move for move in found if move.kind == "duration")
        assert not support(span, facts_2022)

    def test_picked_it_up_is_any_recorded_touch(self, facts_2022, facts_1986):
        """Molina's only record in the 2022 passage is the pass he played.

        A pass is a touch, so "Molina picked it up" is held by it. The
        defenders beaten in 1986 have no touch at all, so the same words about
        one of them are refused.
        """
        found = moves(facts_2022, "Molina picked it up and found MacAllister, who scored.")
        touch = next(move for move in found if move.kind == "touch")
        assert support(touch, facts_2022)
        found = moves(facts_1986, "Shilton picked it up, and Maradona scored.")
        touch = next(move for move in found if move.kind == "touch")
        assert not support(touch, facts_1986)
        assert "puts the ball at" in why(touch, facts_1986)
