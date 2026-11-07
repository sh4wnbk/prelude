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

from app.grounding import ACTION_CLAIMS, NOT_A_NAME, TEAM_DEMONYMS, check
from app.personas import THE_BUDDY, THE_STORYTELLER
from app.narration_grammar import (
    CLAUSE_BREAK,
    hyphens_allowed,
    DIRECTION_YARDS,
    RUN_YARDS,
    STRAIGHT_TOLERANCE_YARDS,
    Reader,
    carry_path,
    carry_yards,
    change_in_x,
    name_keys,
    player_spots,
    recorded_spellings,
    strays_from_straight,
    support,
    touched,
    why,
)
from app.narration_prompt import Beat, Spot, facts_from_buildup
from app.pitch_zones import zone_for
from app.recorded_names import recorded_nicknames, recorded_teams
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


class TestTheFinish:
    """The words a goal call lands on, which the check refused once.

    The live run of 2026-10-31 dropped nine of eighteen candidates and every
    one of the nine ended "and the ball went in". That is the plainest English
    for the thing the framework asks a narration to land on, and the moment is
    a goal, so refusing it was this module's mistake rather than the model's.
    """

    @pytest.mark.parametrize(
        "said",
        [
            "and the ball went in",
            "and it went in",
            "and went in",
            "and found the net",
        ],
    )
    def test_the_finish_can_be_said_without_a_verb_for_the_shot(
        self, said, facts_2022
    ):
        found = moves(facts_2022, "MacAllister set up Di María, {}.".format(said))
        shot = next(
            move
            for move in found
            if move.kind == "action" and "Shot" in (move.detail or ())
        )
        assert shot.actor == DI_MARIA
        assert support(shot, facts_2022)
        assert not ungrounded(facts_2022, found)

    def test_it_is_still_the_scorers_shot_and_nobody_elses(self, facts_2022):
        """So it is a claim about a record rather than a phrase waved through.

        MacAllister has four records in this passage and none is a `Shot`.
        """
        found = moves(facts_2022, "Molina passed to MacAllister, who went in.")
        shot = next(
            move
            for move in found
            if move.kind == "action" and "Shot" in (move.detail or ())
        )
        assert shot.actor == MAC_ALLISTER
        assert not support(shot, facts_2022)


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


def beat(action, start, end=None, player=MARADONA, team="Argentina"):
    """One hand-built record, for the measuring functions on their own.

    The two hero passages hold no pass or carry that takes the ball backwards
    by more than 0.8 yards, so a backward record is one this data cannot
    supply and `change_in_x` has to be shown both ways on records written
    here. Everything downstream of it is tested against `data/raw/`.
    """
    return Beat(
        index=0,
        minute=0,
        second=0,
        player=player,
        team=team,
        action=action,
        event_id="not-a-recorded-event",
        start=Spot(*start),
        end=Spot(*end) if end else None,
    )


class TestTheChangeInX:
    """How far up the pitch a record took the ball, which is a signed number.

    StatsBomb mirrors a defensive record's coordinates, so x rising is always
    the recorded player's own attacking direction and the sign reads the same
    way for either team.
    """

    def test_a_pass_up_the_pitch_is_positive(self):
        assert change_in_x(
            beat("Pass", (20.0, 40.0), (60.0, 40.0))
        ) == pytest.approx(40.0)

    def test_a_pass_the_other_way_is_negative(self):
        assert change_in_x(
            beat("Pass", (60.0, 40.0), (20.0, 40.0))
        ) == pytest.approx(-40.0)

    def test_a_record_with_no_end_cannot_be_measured(self):
        assert change_in_x(beat("Ball Receipt*", (60.0, 40.0))) is None

    def test_the_threshold_sits_in_the_gap_the_data_leaves(
        self, facts_1986, facts_2022
    ):
        """Nothing in either passage moves the ball between 0.8 and 9.0 yards
        of x, so `DIRECTION_YARDS` refuses a touch on the spot and holds every
        pass and carry either passage would call forward."""
        changes = [
            abs(change_in_x(one))
            for facts in (facts_1986, facts_2022)
            for one in facts.beats
            if one.action in ("Pass", "Carry")
            and change_in_x(one) is not None
        ]
        standing = sorted(one for one in changes if one < DIRECTION_YARDS)
        moving = sorted(one for one in changes if one >= DIRECTION_YARDS)
        assert max(standing) == pytest.approx(0.8, abs=0.05)
        assert min(moving) == pytest.approx(9.0, abs=0.05)


class TestWhichWayTheBallWent:
    """"Forward" and "back" are a claim, and they used to be prose.

    Alvarez's ball to MacAllister is 38.5 yards and 36.1 of them are up the
    pitch. The live run of 2026-10-31 called it a ball back to MacAllister
    four times over, in four of the six 2022 slots, and every one of them was
    grounded.
    """

    def test_forward_is_held_by_the_long_ball_up_the_pitch(self, facts_2022):
        found = moves(
            facts_2022,
            "Álvarez hit a long ball forward to MacAllister, who set up Di "
            "María to score.",
        )
        way = next(move for move in found if move.kind == "direction")
        assert (way.actor, way.detail) == (ALVAREZ, "forward")
        assert support(way, facts_2022)
        assert not ungrounded(facts_2022, found)

    def test_the_same_pass_called_back_is_refused(self, facts_2022):
        found = moves(
            facts_2022,
            "Álvarez sent a long ball back to MacAllister, who set up Di "
            "María to score.",
        )
        way = next(move for move in found if move.kind == "direction")
        assert way.detail == "back"
        assert not support(way, facts_2022)
        assert "the furthest any of them moves it is 36 forward" in why(
            way, facts_2022
        )

    def test_a_carry_up_the_pitch_is_forward(self, facts_1986):
        """Maradona's long carries run 32.7, 10.0 and 15.7 yards of x."""
        found = moves(
            facts_1986,
            "Maradona carried it forward past Beardsley and scored.",
        )
        way = next(move for move in found if move.kind == "direction")
        assert way.actor == MARADONA
        assert support(way, facts_1986)

    def test_the_same_carry_called_back_is_refused(self, facts_1986):
        found = moves(
            facts_1986, "Maradona carried it back past Beardsley and scored."
        )
        way = next(move for move in found if move.kind == "direction")
        assert not support(way, facts_1986)

    @pytest.mark.parametrize(
        "said, sense",
        [
            ("forward", "forward"),
            ("forwards", "forward"),
            ("upfield", "forward"),
            ("ahead", "forward"),
            ("back", "back"),
            ("backwards", "back"),
        ],
    )
    def test_each_word_reads_as_a_direction(self, said, sense, facts_1986):
        found = moves(facts_1986, f"Maradona carried it {said} and scored.")
        way = next(move for move in found if move.kind == "direction")
        assert way.detail == sense

    def test_the_longer_phrases_holding_back_still_win(self, facts_1986):
        """"Won it back" is a recovery and "came back at him" is pressure, so
        neither of them is read as a direction."""
        found = moves(
            facts_1986,
            "We won it back through Cuciuffo, and though Butcher came back at "
            "him Maradona scored.",
        )
        assert "direction" not in kinds(found)
        assert not ungrounded(facts_1986, found)


class TestARunHasYardsInIt:
    """"Drove", "ran" and "burst" are a claim about how long a carry was."""

    @pytest.mark.parametrize(
        "said", ["drove", "ran", "burst", "raced", "surged", "charged"]
    )
    def test_each_word_reads_as_a_run(self, said, facts_1986):
        found = moves(facts_1986, f"Maradona {said} past Beardsley and scored.")
        assert kinds(found).count("run") == 1

    def test_maradona_covered_the_ground(self, facts_1986):
        """His three long carries are 34.9, 16.8 and 16.7 yards."""
        found = moves(
            facts_1986, "Maradona drove forward past Beardsley and scored."
        )
        run = next(move for move in found if move.kind == "run")
        assert run.actor == MARADONA
        assert support(run, facts_1986)

    def test_a_carry_under_a_yard_is_not_a_run(self, facts_2022):
        """Álvarez's one carry is 0.7 yards, and the live run of 2026-10-31
        said he drove forward in four of the six 2022 slots."""
        found = moves(
            facts_2022,
            "Álvarez drove forward and set up Di María, who scored.",
        )
        run = next(move for move in found if move.kind == "run")
        assert run.actor == ALVAREZ
        assert not support(run, facts_2022)
        assert "the longest is 1" in why(run, facts_2022)

    def test_the_threshold_sits_in_the_gap_the_data_leaves(
        self, facts_1986, facts_2022
    ):
        """Three carries over ten yards and six under one and a half, with
        nothing in between, so `RUN_YARDS` is not a close call on this data."""
        carries = sorted(
            carry_yards(one)
            for facts in (facts_1986, facts_2022)
            for one in facts.beats
            if one.action == "Carry" and carry_yards(one) is not None
        )
        assert [round(one, 1) for one in carries if one < RUN_YARDS] == [
            0.2,
            0.6,
            0.7,
            1.0,
            1.1,
            1.1,
        ]
        assert [round(one, 1) for one in carries if one >= RUN_YARDS] == [
            16.7,
            16.8,
            34.9,
        ]


class TestACarryDoesNotDeliverTheBall:
    """A carry keeps the ball at the player's own feet; a pass gives it away.

    "Who carried it back to MacAllister" was in two of the eighteen
    candidates of 2026-10-31, over a 38 yard pass up the pitch.
    """

    def test_a_carry_asked_to_deliver_is_refused(self, facts_2022):
        found = moves(
            facts_2022,
            "Álvarez carried it to MacAllister, who set up Di María to score.",
        )
        delivery = next(
            move for move in found if move.kind == "carry_delivery"
        )
        assert (delivery.actor, delivery.target) == (ALVAREZ, MAC_ALLISTER)
        assert delivery.said == "carried it to MacAllister"
        assert not support(delivery, facts_2022)
        assert "only a pass does that" in why(delivery, facts_2022)

    def test_the_pass_itself_is_still_recorded(self, facts_2022):
        """So the refusal is about the words and not about the move: the same
        chain written as a pass passes."""
        found = moves(
            facts_2022,
            "Álvarez passed to MacAllister, who set up Di María to score.",
        )
        assert "carry_delivery" not in kinds(found)
        assert not ungrounded(facts_2022, found)

    @pytest.mark.parametrize(
        "said",
        [
            "carried and passed to MacAllister",
            "carried and played it to MacAllister",
            "carried it and found MacAllister",
            "carried and sent a long ball to MacAllister",
        ],
    )
    def test_a_second_verb_delivers_it_instead(self, said, facts_2022):
        """A conjunction, a marker with its own verb or a long ball between
        the carry and the name all say something else gave the ball away."""
        found = moves(
            facts_2022,
            f"Álvarez {said}, who set up Di María to score.",
        )
        assert "carry_delivery" not in kinds(found)

    def test_a_pass_that_delivers_is_not_touched_by_the_rule(self, facts_1986):
        """Enrique's pass to Maradona, which is the shape every reference
        opens with."""
        found = moves(
            facts_1986,
            "Cuciuffo passed to Enrique, who played it to Maradona, and he "
            "scored.",
        )
        assert "carry_delivery" not in kinds(found)
        assert not ungrounded(facts_1986, found)


class TestWhoTheMoveIsAttributedTo:
    """The attribution, which is who the sentence says did it.

    `support` has always checked a chain against `beat.player` and
    `beat.recipient`, so a pass only grounds between the two players the
    record names. What the run of 2026-11-05 showed is that the actor
    reaching it could be the wrong player: Shawn read "We won it back through
    Cuciuffo, who passed to Enrique and set up Maradona" aloud and heard
    Cuciuffo setting up Maradona, which the records put on Enrique, and the
    check passed it on twenty-one claims.

    The reader was following the ball. "And" joins a second verb to the same
    subject, so the subject is still Cuciuffo even though the ball has gone
    on to Enrique.
    """

    def test_the_candidate_that_got_away_with_it_is_refused(self, facts_1986):
        """Buddy for Argentina candidate 1 of 2026-11-05, as written."""
        text = (
            "We won it back through Cuciuffo, who passed to Enrique and set "
            "up Maradona; he slipped past Beardsley, ran forward thirty-five "
            "yards, dribbled past Butcher, ran forward seventeen, beat "
            "Fenwick, ran forward seventeen into the box, glided past "
            "Shilton and shot with his left foot! What a moment!"
        )
        result = check(text, facts_1986, THE_BUDDY, "Argentina")
        assert not result.grounded, result.summary
        assert "chain" in {failure.kind for failure in result.failures}
        assert any(
            "set up Maradona" in failure.value for failure in result.failures
        )

    def test_the_assist_has_to_be_the_recorded_assist(self, facts_1986):
        """Enrique carries `goal_assist`, so he set up Maradona and nobody
        else did."""
        assert check(
            "Enrique set up Maradona, who scored with his left foot.",
            facts_1986,
            THE_STORYTELLER,
            None,
        ).grounded
        wrong = check(
            "Cuciuffo set up Maradona, who scored with his left foot.",
            facts_1986,
            THE_STORYTELLER,
            None,
        )
        assert not wrong.grounded, wrong.summary
        assert "chain" in {failure.kind for failure in wrong.failures}

    def test_a_second_verb_on_the_same_subject_keeps_that_subject(
        self, facts_1986
    ):
        reader = Reader(
            facts=facts_1986,
            not_a_name=NOT_A_NAME,
            demonyms=TEAM_DEMONYMS,
            actions=ACTION_CLAIMS,
        )
        text = "Cuciuffo, who passed to Enrique and set up Maradona."
        chains = [
            move for move in reader.read(text) if move.kind == "chain"
        ]
        assert [move.actor for move in chains] == [
            "José Luis Cuciuffo",
            "José Luis Cuciuffo",
        ]
        assert [support(move, facts_1986) != () for move in chains] == [
            True,
            False,
        ]

    def test_a_pronoun_between_the_two_moves_the_subject_on(self, facts_1986):
        """"Played it to Enrique who found Maradona" is the same move told
        correctly: "who" follows Enrique, so the second chain is his."""
        reader = Reader(
            facts=facts_1986,
            not_a_name=NOT_A_NAME,
            demonyms=TEAM_DEMONYMS,
            actions=ACTION_CLAIMS,
        )
        text = "Cuciuffo played it to Enrique who found Maradona."
        chains = [
            move for move in reader.read(text) if move.kind == "chain"
        ]
        assert [move.actor for move in chains] == [
            "José Luis Cuciuffo",
            "Héctor Adolfo Enrique",
        ]
        assert all(support(move, facts_1986) for move in chains)

    def test_a_named_subject_between_the_two_does_as_well(self, facts_2022):
        """The 2022 counter, which names a subject before every chain."""
        reader = Reader(
            facts=facts_2022,
            not_a_name=NOT_A_NAME,
            demonyms=TEAM_DEMONYMS,
            actions=ACTION_CLAIMS,
        )
        text = (
            "Molina to MacAllister, MacAllister to Messi, Messi to Álvarez, "
            "Álvarez to MacAllister, MacAllister set up Di María."
        )
        chains = [
            move for move in reader.read(text) if move.kind == "chain"
        ]
        assert [move.actor for move in chains] == [
            "Nahuel Molina Lucero",
            "Alexis Mac Allister",
            "Lionel Andrés Messi Cuccittini",
            "Julián Álvarez",
            "Alexis Mac Allister",
        ]
        assert all(support(move, facts_2022) for move in chains)

    def test_a_bare_marker_still_follows_the_ball(self, facts_2022):
        """"On to" and "to" carry no verb of their own, so they are the ball
        continuing from whoever has it rather than a second verb on the same
        subject. Rule 14 offers "on to" as a join, so this one has to work."""
        reader = Reader(
            facts=facts_2022,
            not_a_name=NOT_A_NAME,
            demonyms=TEAM_DEMONYMS,
            actions=ACTION_CLAIMS,
        )
        text = "Molina to MacAllister on to Messi."
        chains = [
            move for move in reader.read(text) if move.kind == "chain"
        ]
        assert [move.actor for move in chains] == [
            "Nahuel Molina Lucero",
            "Alexis Mac Allister",
        ]
        assert all(support(move, facts_2022) for move in chains)

    def test_the_passer_and_the_receiver_are_both_checked(self, facts_2022):
        """Said plainly, because the module docstring used to say direction
        survived: it does in the cited reading and not in this one."""
        assert check(
            "Molina to MacAllister, who scored with his left foot.",
            facts_2022,
            THE_STORYTELLER,
            None,
        ).failures[0].kind != "chain"
        backwards = check(
            "MacAllister to Molina, and Di María scored with his left foot.",
            facts_2022,
            THE_STORYTELLER,
            None,
        )
        assert not backwards.grounded, backwards.summary
        assert "chain" in {failure.kind for failure in backwards.failures}



class TestWhoUnderPressureIsAbout:
    """"Under pressure" is the carrier's, and "from X" is a claim about X.

    The run of 2026-11-05 refused "under pressure from Beardsley and Reid"
    three times with `'under pressure': no record of Peter Beardsley is
    marked under pressure`, and the claim is true: Beardsley and Reid are the
    players who pressed. StatsBomb puts `under_pressure` on the record of the
    player being pressed and a `Pressure` on the record of the player
    pressing him, so reading the actor off the words asked the presser's
    record for the carrier's flag.
    """

    #: The refusal the run of 2026-11-05 printed, over a sentence the records
    #: hold. Three of that run's eight drops were this one line.
    REFUSAL = (
        "'under pressure': no record of Peter Beardsley is marked under "
        "pressure"
    )

    #: What the model wrote and the check refused, word for word, in the 1986
    #: `buddy_conceded` slot of that run.
    REFUSED = (
        "Cuciuffo recovered and passed to Enrique, who set up Maradona; "
        "under pressure from Beardsley and Reid, he dribbled past Beardsley, "
        "Butcher and Fenwick, carried it forward into the box, slipped past "
        "Shilton and shot with his left foot."
    )

    def test_the_carrier_owns_the_claim_and_not_the_name_beside_it(
        self, facts_1986
    ):
        found = moves(
            facts_1986,
            "Maradona, under pressure from Beardsley and Reid, dribbled "
            "past Butcher and scored with his left foot.",
        )
        pressed = next(move for move in found if move.kind == "pressured")
        assert pressed.actor == MARADONA
        assert support(pressed, facts_1986)
        assert not ungrounded(facts_1986, found)

    def test_each_name_after_from_has_to_have_pressed(self, facts_1986):
        found = moves(
            facts_1986,
            "Maradona, under pressure from Beardsley and Reid, dribbled "
            "past Butcher and scored with his left foot.",
        )
        pressers = [move for move in found if move.kind == "pressed_by"]
        assert [move.target for move in pressers] == [BEARDSLEY, "Peter Reid"]
        for move in pressers:
            assert move.actor == MARADONA
            assert support(move, facts_1986)

    def test_a_player_who_never_pressed_is_refused(self, facts_1986):
        """Terry Fenwick was dribbled past and pressed nobody, so the records
        hold the carrier's flag and not Fenwick's pressure."""
        found = moves(
            facts_1986,
            "Maradona, under pressure from Fenwick, dribbled past Butcher "
            "and scored with his left foot.",
        )
        pressed = next(move for move in found if move.kind == "pressured")
        assert support(pressed, facts_1986)
        refused = next(move for move in found if move.kind == "pressed_by")
        assert refused.target == "Terry Fenwick"
        assert not support(refused, facts_1986)
        assert why(refused, facts_1986) == (
            "'under pressure from Fenwick': the records hold no pressure by "
            "Terry Fenwick in this passage"
        )

    def test_the_refusal_of_2026_11_05_is_gone(self, facts_1986):
        """The whole narration the model wrote, through `check`, as the slot
        it was written for."""
        result = check(
            self.REFUSED, facts_1986, THE_BUDDY, "England"
        )
        assert result.grounded, result.summary
        assert self.REFUSAL not in result.summary

    def test_the_refusal_text_itself_is_no_longer_produced(self, facts_1986):
        """The words of the refusal, not just the verdict: no move of that
        sentence puts the claim on Beardsley any more."""
        found = moves(facts_1986, self.REFUSED)
        pressed = [move for move in found if move.kind == "pressured"]
        assert pressed and all(move.actor == MARADONA for move in pressed)
        assert self.REFUSAL not in [
            why(move, facts_1986) for move in found
        ]

    def test_pressed_by_them_still_passes_as_it_did(self, facts_1986):
        """Half the kept 1986 candidates routed around the refusal by
        writing it this way, and nothing here changes that reading."""
        found = moves(
            facts_1986,
            "Maradona, pressed by Beardsley and Reid, dribbled past "
            "Butcher and scored with his left foot.",
        )
        assert not ungrounded(facts_1986, found)

    def test_a_name_past_the_comma_is_not_read_as_a_presser(self, facts_1986):
        """The price of the clause rule, both ways round: a list that runs
        past a comma is checked as far as the comma, and a subject past one
        is not turned into a presser, which would refuse a true sentence."""
        found = moves(
            facts_1986,
            "Under pressure from Beardsley, Maradona dribbled past Butcher "
            "and scored with his left foot.",
        )
        pressers = [move for move in found if move.kind == "pressed_by"]
        assert [move.target for move in pressers] == [BEARDSLEY]
        assert MARADONA not in [move.target for move in pressers]
        assert not ungrounded(facts_1986, found)

    def test_a_verb_after_the_marker_ends_the_list(self, facts_1986):
        """"Under pressure from Beardsley and dribbled past Butcher" has a
        verb between the two, so Butcher is a defender beaten and not a
        presser."""
        found = moves(
            facts_1986,
            "Maradona, under pressure from Beardsley and dribbled past "
            "Butcher, scored with his left foot.",
        )
        assert [
            move.target for move in found if move.kind == "pressed_by"
        ] == [BEARDSLEY]
        assert "Terry Butcher" in [
            move.target for move in found if move.kind == "past"
        ]

    def test_the_presser_does_not_take_the_ball(self, facts_1986):
        """A player who pressed is spoken for, like a chain's target: he
        becomes nobody's actor and no pronoun after him means him."""
        found = moves(
            facts_1986,
            "Maradona, under pressure from Beardsley and Reid, dribbled "
            "past Butcher, and he scored with his left foot.",
        )
        shot = next(
            move
            for move in found
            if move.kind == "action" and "Shot" in (move.detail or ())
        )
        assert shot.actor == MARADONA


class TestAHyphenIsTheSameClaimAsASpace:
    """What the run of 2026-11-05 got past the reading with one character.

    Three of that run's four kept 2022 candidates wrote "first-time" or
    "left-foot", and `PHRASES` held both phrases as two words, so neither was
    read as a claim and neither was checked. Nothing false passed: the record
    is `first_time` and `Left Foot`, so the words were true and the check
    simply did not look. The two storyteller candidates said the foot that
    way and no other.
    """

    #: 2022 `storyteller_neutral` candidate 1 of that run, word for word.
    HYPHENATED = (
        "Molina to MacAllister, MacAllister to Messi, Messi to \u00c1lvarez, "
        "\u00c1lvarez sent a long ball to MacAllister, who set up Di Mar\u00eda. "
        "Di Mar\u00eda struck his first-time left-foot shot from inside the box "
        "and it went in. What a moment."
    )

    def test_the_hyphenated_finish_is_read_as_two_claims(self, facts_2022):
        found = moves(
            facts_2022,
            "Di Mar\u00eda struck his first-time left-foot shot from inside "
            "the box.",
        )
        assert "first_time" in kinds(found)
        assert "body_part" in kinds(found)
        assert not ungrounded(facts_2022, found)

    def test_the_candidate_of_2026_11_05_is_checked_on_more_claims(
        self, facts_2022
    ):
        """It passed on 15 claims when the hyphens were prose. The words are
        the same words; two more of them are now checked."""
        result = check(self.HYPHENATED, facts_2022, THE_STORYTELLER, None)
        assert result.grounded, result.summary
        assert result.checked == 17

    def test_the_same_words_over_the_1986_shot_are_refused(self, facts_1986):
        """The 1986 shot is not recorded as struck first time, so the
        hyphenated claim is refused there exactly as the spaced one is."""
        found = moves(
            facts_1986,
            "Maradona struck his first-time left-foot shot from inside the "
            "box.",
        )
        first = next(move for move in found if move.kind == "first_time")
        assert not support(first, facts_1986)
        assert why(first, facts_1986) == (
            "'first-time': the goal shot is not recorded as struck first "
            "time"
        )

    def test_the_wrong_foot_hyphenated_is_still_the_wrong_foot(
        self, facts_2022
    ):
        found = moves(facts_2022, "Di Mar\u00eda struck a right-foot shot.")
        part = next(move for move in found if move.kind == "body_part")
        assert not support(part, facts_2022)

    def test_footed_is_the_same_claim_as_foot(self, facts_2022):
        """"A left-footed shot" is the spelling the hyphen invites next."""
        found = moves(facts_2022, "Di Mar\u00eda struck a left-footed shot.")
        part = next(move for move in found if move.kind == "body_part")
        assert part.detail == "Left Foot"
        assert support(part, facts_2022)

    def test_every_phrase_takes_either_spelling(self, facts_1986):
        """Not the finish alone: the rule is in `hyphens_allowed`, so every
        phrase of two words or more reads the same with a hyphen in it."""
        assert hyphens_allowed("under pressure") == "under[ -]pressure"
        assert hyphens_allowed("first time") == "first[ -]time"
        assert hyphens_allowed("drove") == "drove"
        found = moves(
            facts_1986,
            "Maradona, under-pressure, dribbled past Shilton and scored.",
        )
        pressed = next(move for move in found if move.kind == "pressured")
        assert pressed.actor == MARADONA
        assert support(pressed, facts_1986)

    def test_a_hyphenated_long_ball_is_still_the_long_ball(self, facts_2022):
        """And still refused over a pass that is not long enough: the pass
        from MacAllister to Di Mar\u00eda is 26 yards."""
        held = moves(
            facts_2022,
            "\u00c1lvarez hit a long-ball forward to MacAllister.",
        )
        assert not ungrounded(facts_2022, held)
        refused = moves(
            facts_2022,
            "MacAllister hit a long-ball to Di Mar\u00eda.",
        )
        assert ungrounded(facts_2022, refused)

    def test_a_hyphenated_chain_marker_still_reads_as_the_pass(
        self, facts_2022
    ):
        """"Set-up" is the noun spelling of the marker, and "on-to" is the
        bare marker that the rule about a second verb exempts."""
        found = moves(
            facts_2022, "MacAllister set-up Di Mar\u00eda, who scored."
        )
        chain = next(move for move in found if move.kind == "chain")
        assert (chain.actor, chain.target) == (MAC_ALLISTER, DI_MARIA)
        assert support(chain, facts_2022)
        carried = moves(
            facts_2022, "Molina to MacAllister on-to Messi."
        )
        chains = [move for move in carried if move.kind == "chain"]
        assert [(one.actor, one.target) for one in chains] == [
            (MOLINA, MAC_ALLISTER),
            (MAC_ALLISTER, MESSI),
        ]
        assert not ungrounded(facts_2022, carried)

    def test_a_hyphen_cannot_make_a_claim_the_records_refuse(
        self, facts_2022
    ):
        """The point of the fix: the spelling changes what is read, never
        what the records hold."""
        for said in (
            "\u00c1lvarez passed it back to MacAllister.",
            "\u00c1lvarez passed it back-to MacAllister.",
        ):
            assert ungrounded(facts_2022, moves(facts_2022, said))


class TestAPlaceOnThePitchIsAClaim:
    """Where the move was is a claim about the location of one record.

    Shawn's reading of 2026-11-05: "dribbled past Butcher" places nothing, so
    the beats say where now and a narration may say it back. A place that is
    read out is a place that has to be checked, and this is where that
    happens: the band and the side are two moves, each one about the action
    they were said beside, each one refused when the records put that action
    somewhere else.

    The coordinates in these docstrings are in `data/raw/`.
    """

    def test_the_band_and_the_side_are_two_moves(self, facts_1986):
        found = moves(
            facts_1986,
            "Maradona dribbled past Butcher in the final third on the "
            "right.",
        )
        places = [move for move in found if move.kind == "zone"]
        assert [move.said for move in places] == [
            "in the final third",
            "on the right",
        ]
        for move in places:
            assert support(move, facts_1986)

    def test_a_wrong_side_is_refused_over_a_right_band(self, facts_1986):
        """Maradona went past Butcher in the final third and he did it at
        `y` 68.6, which is the right."""
        found = moves(
            facts_1986,
            "Maradona dribbled past Butcher in the final third on the left.",
        )
        wrong = next(
            move
            for move in found
            if move.kind == "zone" and move.said == "on the left"
        )
        assert not support(wrong, facts_1986)
        assert "on the left" in why(wrong, facts_1986)
        assert "on the right" in why(wrong, facts_1986)

    def test_beat_butcher_on_the_left_is_refused(self, facts_1986):
        """Shawn's test, in the words he wrote it in. "Beat" is nobody's
        claim about a record, so the place is about the Butcher beside it,
        and every record of Butcher's in this passage is England's: a place
        is read off the attacking side's own location and there is none."""
        found = moves(facts_1986, "He beat Butcher on the left.")
        place = next(move for move in found if move.kind == "zone")
        assert not support(place, facts_1986)
        assert "read off the attacking side's own location" in why(
            place, facts_1986
        )

    def test_the_mirrored_record_cannot_hold_a_place(self, facts_1986):
        """Beardsley's `Dribbled Past` is at (65.7, 23.7), which is just
        inside their half read as written, and the dribble that beat him
        happened at (54.4, 56.4), which is just inside his own. Both spots
        are between the sides of the box by width, so the band is what shows
        the mirroring and neither of them is on a side at all."""
        beardsley = next(
            beat
            for beat in facts_1986.beats
            if beat.action == "Dribbled Past" and beat.player == BEARDSLEY
        )
        assert zone_for(beardsley.start) == "just inside their half"
        for said in (
            "Maradona dribbled past Beardsley just inside their half.",
            "Maradona dribbled past Beardsley on the left.",
        ):
            found = moves(facts_1986, said)
            place = next(move for move in found if move.kind == "zone")
            assert not support(place, facts_1986)

    def test_the_true_places_of_the_1986_move_pass(self, facts_1986):
        """The beats' own phrasings, one claim at a time: the recovery deep
        in his own half, Beardsley just inside it, Butcher in the final
        third, Fenwick on the edge of the box and Shilton in the box."""
        said = (
            "Cuciuffo won it back deep in his own half, Maradona went past "
            "Beardsley just inside his own half, past Butcher in the final "
            "third on the right, past Fenwick on the edge of the box, and "
            "around Shilton in the box."
        )
        found = [
            move
            for move in moves(facts_1986, said)
            if move.kind == "zone"
        ]
        # Five places, and "in the box" is not one of them: the broad box
        # phrase is read as the position claim it already was.
        assert len(found) == 5
        for move in found:
            assert support(move, facts_1986), why(move, facts_1986)

    def test_the_true_places_of_the_2022_move_pass(self, facts_2022):
        said = (
            "Molina played it forward deep in his own half on the right, "
            "and Álvarez hit a long ball just inside France's half to "
            "MacAllister on the edge of the box, who set up Di María in "
            "the box."
        )
        found = [
            move for move in moves(facts_2022, said) if move.kind == "zone"
        ]
        assert len(found) == 4
        for move in found:
            assert support(move, facts_2022), why(move, facts_2022)

    def test_alvarez_deep_in_his_own_half_is_refused(self, facts_2022):
        """Shawn's other test. Álvarez's three records are at (62.5, 68.2),
        (63.2, 68.2) and the pass that lands at (99.3, 54.9), so nothing of
        his is under `x` 40."""
        found = moves(
            facts_2022, "Álvarez, deep in his own half, hit a long ball."
        )
        place = next(move for move in found if move.kind == "zone")
        assert place.detail["zone"] == "deep in his own half"
        assert not support(place, facts_2022)
        said = why(place, facts_2022)
        assert "just inside France's half on the right" in said
        assert "on the edge of the box" in said

    def test_a_place_said_before_the_action_is_about_it(self, facts_2022):
        """The appositive the beats are written in: "Álvarez, just inside
        France's half, hit a long ball". The move before it is the name, so
        the place is about the next one when there is nothing behind it."""
        found = moves(
            facts_2022,
            "Just inside France's half, Álvarez hit a long ball forward.",
        )
        place = next(move for move in found if move.kind == "zone")
        assert support(place, facts_2022)

    def test_a_long_ball_is_placed_at_either_end(self, facts_2022):
        """Struck at (63.2, 68.2) and down at (99.3, 54.9): one record, two
        locations, and a claim about either one holds."""
        for said in (
            "Álvarez hit a long ball to MacAllister just inside France's "
            "half.",
            "Álvarez hit a long ball to MacAllister on the edge of the box.",
        ):
            found = moves(facts_2022, said)
            place = next(move for move in found if move.kind == "zone")
            assert support(place, facts_2022), why(place, facts_2022)
        found = moves(
            facts_2022, "Álvarez hit a long ball to MacAllister in the final "
            "third."
        )
        place = next(move for move in found if move.kind == "zone")
        assert not support(place, facts_2022)

    def test_a_half_said_with_the_wrong_name_is_refused(self, facts_2022):
        """"Just inside Argentina's half" is a different place with the same
        words around it, and the side in possession is always known."""
        found = moves(
            facts_2022,
            "Álvarez hit a long ball just inside Argentina's half.",
        )
        place = next(move for move in found if move.kind == "zone")
        assert not support(place, facts_2022)
        assert "the side in possession here" in why(place, facts_2022)

    def test_a_half_said_with_a_third_teams_name_is_refused(self, facts_2022):
        found = moves(
            facts_2022, "Álvarez hit a long ball just inside Brazil's half."
        )
        place = next(move for move in found if move.kind == "zone")
        assert not support(place, facts_2022)
        assert "not the side being attacked here, which is France" in why(
            place, facts_2022
        )

    def test_a_hyphen_reads_as_the_space_it_stands_in_for(self, facts_1986):
        """The fix of Task 12, applied to a vocabulary written after it: a
        hyphen between two words is the same claim as a space."""
        found = moves(
            facts_1986,
            "Maradona went past Butcher in the final-third on the right.",
        )
        places = [move for move in found if move.kind == "zone"]
        assert [move.said for move in places] == [
            "in the final-third",
            "on the right",
        ]
        assert support(places[0], facts_1986)
        found = moves(
            facts_1986,
            "Cuciuffo won it back deep-in-his-own-half.",
        )
        place = next(move for move in found if move.kind == "zone")
        assert support(place, facts_1986)

    def test_the_broad_half_is_still_the_half_and_not_a_band(
        self, facts_1986
    ):
        """"In his own half" is read as the half it names, which is what
        three of the eight references say and what Maradona's first touch at
        `x` 55.2 is: the band for 55.2 is "just inside his own half", and
        refusing the broad phrase over it would refuse a true sentence and a
        reference with it."""
        found = moves(facts_1986, "Maradona picked it up in his own half.")
        kinds_said = [move.kind for move in found]
        assert "zone" not in kinds_said
        place = next(move for move in found if move.kind == "position")
        assert place.detail == "own half"
        assert support(place, facts_1986)

    def test_a_place_with_no_action_beside_it_places_nothing(
        self, facts_1986
    ):
        found = moves(facts_1986, "On the left.")
        place = next(move for move in found if move.kind == "zone")
        assert not support(place, facts_1986)
        assert "places nothing" in why(place, facts_1986)


class TestAHalfSaidWithAPossessive:
    """"Our half" and "their half": whose half, and which end of the pitch.

    A band of a team's own half is read in that team's frame, so the same
    words are two places depending on who the narration was written for.
    `_reads_from_the_other_end` in `app/narration_grammar.py` is the
    resolution and `from_the_other_end` in `app/pitch_zones.py` is the
    arithmetic. The coordinates behind these: Molina played the first pass
    at (25.9, 71.8) and Álvarez struck the long ball at (63.2, 68.2), which
    is 56.8 from France's end.
    """

    LONG_BALL = (
        "Álvarez, just inside our half on the right, hit a long ball "
        "forward to MacAllister."
    )
    MOLINA = "Molina, deep in {} own half, played it forward to MacAllister."

    def read(self, facts, text, side):
        one = Reader(
            facts=facts,
            not_a_name=NOT_A_NAME,
            demonyms=TEAM_DEMONYMS,
            actions=ACTION_CLAIMS,
            side=side,
        )
        return list(one.read(text))

    def places(self, facts, text, side):
        return [
            move for move in self.read(facts, text, side)
            if move.kind == "zone"
        ]

    def refusals(self, facts, text, persona, side):
        """What the check refuses in one line of play, less the ending.

        These lines are a clause of a telling rather than a whole narration,
        so every one of them is refused for not landing the finish. That is
        the rule about shape; what is being read here is the claims.
        """
        result = check(text, facts, persona, side)
        return [one for one in result.failures if one.kind != "ending"]

    def test_our_half_for_a_france_fan_is_the_half_france_defends(
        self, facts_2022
    ):
        """Shawn's first test. The long ball was struck 63.2 up the pitch
        from Argentina's goal, which is just inside France's half and is
        where a France fan's Buddy says "our half"."""
        said = self.places(facts_2022, self.LONG_BALL, "France")
        assert [move.said for move in said] == [
            "just inside our half",
            "on the right",
        ]
        assert said[0].detail["other_end"] is True
        for move in said:
            assert support(move, facts_2022), why(move, facts_2022)

    def test_the_same_line_is_held_for_that_fan(self, facts_2022):
        """And through the check, which is where the first person is read:
        every record in that clause is Argentina's, and "our" stands on the
        half claim rather than on the play."""
        assert self.refusals(
            facts_2022, self.LONG_BALL, THE_BUDDY, "France"
        ) == []

    def test_our_own_half_for_an_argentina_fan_is_where_molina_played_it(
        self, facts_2022
    ):
        said = self.places(facts_2022, self.MOLINA.format("our"), "Argentina")
        assert [move.said for move in said] == ["deep in our own half"]
        assert said[0].detail["other_end"] is False
        assert support(said[0], facts_2022)
        assert self.refusals(
            facts_2022, self.MOLINA.format("our"), THE_BUDDY, "Argentina"
        ) == []

    def test_their_own_half_for_an_argentina_fan_is_refused(self, facts_2022):
        """The other side of the resolution. For a fan of the side that
        scored, "their own half" is France's own half, which is ninety yards
        from where Molina played it."""
        said = self.places(
            facts_2022, self.MOLINA.format("their"), "Argentina"
        )
        assert said[0].detail["other_end"] is True
        assert not support(said[0], facts_2022)
        assert "read from the other end of the pitch" in why(
            said[0], facts_2022
        )
        refused = self.refusals(
            facts_2022, self.MOLINA.format("their"), THE_BUDDY, "Argentina"
        )
        assert [one.kind for one in refused] == ["zone"]

    def test_their_own_half_for_a_france_fan_is_where_molina_played_it(
        self, facts_2022
    ):
        """The 2022 Buddy telling for the side that conceded says it this
        way, and it is the same place "our own half" is for the other fan."""
        said = self.places(facts_2022, self.MOLINA.format("their"), "France")
        assert said[0].detail["other_end"] is False
        assert support(said[0], facts_2022)

    def test_with_no_side_a_possessive_half_reads_as_it_is_spelled(
        self, facts_2022
    ):
        """Nothing resolves "their" for a narration written for nobody, so
        "their own half" is the half the side on the ball defends, which is
        what "his own half" says, and a Storyteller cannot say "our" at
        all."""
        said = self.places(facts_2022, self.MOLINA.format("their"), None)
        assert said[0].detail["other_end"] is False
        assert support(said[0], facts_2022)
        # "Just inside their half" with no side is the opponent's half, which
        # is the band the vocabulary spells that way and is where the long
        # ball was struck.
        theirs = self.places(
            facts_2022,
            self.LONG_BALL.replace("our half", "their half"),
            None,
        )
        assert theirs[0].detail["other_end"] is True
        assert support(theirs[0], facts_2022)
        # And "our" from a voice that is not partisan is nobody's.
        refused = self.refusals(
            facts_2022, self.LONG_BALL, THE_STORYTELLER, None
        )
        assert [one.kind for one in refused] == ["first person"]

    def test_a_curly_apostrophe_reads_as_a_straight_one(self, facts_2022):
        """"France's half" is one claim however the ending is spelled: the
        run of 2026-11-05 wrote it with a RIGHT SINGLE QUOTATION MARK."""
        said = (
            "Álvarez hit a long ball just inside France{}s half on the "
            "right to MacAllister."
        )
        straight = self.places(facts_2022, said.format("'"), "Argentina")
        curly = self.places(facts_2022, said.format("’"), "Argentina")
        assert [move.said for move in curly] == [move.said for move in straight]
        assert curly[0].said == "just inside France's half"
        for move in curly:
            assert support(move, facts_2022), why(move, facts_2022)
        assert self.refusals(
            facts_2022, said.format("’"), THE_BUDDY, "Argentina"
        ) == []
