"""The six hero narrations the team wrote, read against `data/raw/`.

`scripts/authored_narrations.py` holds them verbatim and re-checks them with
the three rules a candidate meets: `app/grounding.py` as a goal call, the
places rule and the opener rule. These tests are the same three answers held
in the suite, so a check change that would cost a hero narration fails here
rather than in a run nobody made.

**Four of the six pass all three today and two do not**, and the two that do
not are refused for the way the reading pairs a place with an action rather
than for anything the words claim. The tests below say which two and why, in
the words the check uses, because that refusal is the finding of this task
and not a thing to tidy away. When the pairing changes, these two tests fail
and are rewritten; nothing here rewords a narration.

Nothing in this file calls a model.
"""

import json

import pytest

from app.grounding import check
from app.narration_prompt import facts_from_buildup
from app.recorded_names import recorded_nicknames, recorded_teams
from app.statsbomb_event_feed import StatsBombEventFeed

import scripts.authored_narrations as authored
from scripts.narrator_candidates import (
    PLACES_WANTED,
    narrator_for,
    opener_missing,
    places_missing,
    slots_for,
    zones_said,
)

MATCH_1986 = 3750191
MATCH_2022 = 3869685

#: The six slots, as (match, slot), in the order the two goals run.
SLOTS = tuple(sorted(authored.AUTHORED))

#: The four that pass all three today, read off
#: `scripts/authored_narrations.py` on 2026-11-07.
GROUNDED_TODAY = (
    (MATCH_1986, "buddy_conceded"),
    (MATCH_2022, "buddy_conceded"),
    (MATCH_2022, "buddy_scored"),
    (MATCH_2022, "storyteller_neutral"),
)

#: The two that are not, and the claim each is refused for.
REFUSED_TODAY = {
    (MATCH_1986, "buddy_scored"): "the final third",
    (MATCH_1986, "storyteller_neutral"): "on the right",
}


@pytest.fixture(scope="module")
def feed():
    return StatsBombEventFeed()


def hero(feed, match_id, clock):
    moment = next(
        one
        for one in feed.defining_moments(match_id)
        if (one.minute, one.second) == clock
    )
    return (
        facts_from_buildup(
            feed.buildup(match_id, moment),
            recorded_nicknames(match_id),
            recorded_teams(match_id),
        ),
        moment,
    )


@pytest.fixture(scope="module")
def heroes(feed):
    return {
        MATCH_1986: hero(feed, MATCH_1986, (54, 18)),
        MATCH_2022: hero(feed, MATCH_2022, (35, 22)),
    }


def facts_for(heroes, match_id):
    return heroes[match_id][0]


def side_for(heroes, match_id, key):
    moment = heroes[match_id][1]
    return dict(slots_for(match_id, moment.team))[key]


class TestTheSixAreTheSixSlots:
    def test_there_is_one_narration_per_recorded_slot(self, heroes):
        for match_id in (MATCH_1986, MATCH_2022):
            moment = heroes[match_id][1]
            keys = [key for key, _side in slots_for(match_id, moment.team)]
            for key in keys:
                assert (match_id, key) in authored.AUTHORED
            assert len(keys) == 3
        assert len(authored.AUTHORED) == 6

    def test_no_two_slots_share_a_telling(self):
        texts = list(authored.AUTHORED.values())
        assert len(set(texts)) == len(texts)

    def test_every_apostrophe_is_a_straight_one(self):
        """A curly one would reach the speech service as written."""
        for text in authored.AUTHORED.values():
            assert "’" not in text


class TestTheAuthorshipIsCarried:
    """No reader can take these for model output.

    `AUTHOR` and `AUTHORSHIP` are one string each, used everywhere the
    authorship is stated, so the review file, the JSON and anything that
    freezes them say one thing.
    """

    def test_the_author_is_the_team(self):
        assert authored.AUTHOR == "the team"

    def test_the_authorship_says_both_halves(self):
        assert authored.AUTHORSHIP == (
            "written by the team, verified by the grounding check"
        )

    def test_every_slot_carries_it(self, heroes):
        for match_id, key in SLOTS:
            said = authored.answers(
                facts_for(heroes, match_id),
                match_id,
                key,
                side_for(heroes, match_id, key),
            )
            assert said["author"] == authored.AUTHOR
            assert said["authorship"] == authored.AUTHORSHIP

    def test_the_review_file_says_who_wrote_them(self, heroes):
        goals = [
            {
                "year": 2022,
                "match_id": MATCH_2022,
                "minute": 35,
                "second": 22,
                "player": "Ángel Fabián Di María Hernández",
                "team": "Argentina",
                "opponent": "France",
                "records": 13,
                "slots": [
                    authored.answers(
                        facts_for(heroes, MATCH_2022),
                        MATCH_2022,
                        "buddy_scored",
                        "Argentina",
                    )
                ],
            }
        ]
        text = authored.review(goals)
        assert authored.AUTHORSHIP in text
        assert "No model wrote these" in text
        assert "—" not in text
        document = authored.document(goals)
        assert document["author"] == authored.AUTHOR
        assert json.dumps(document)


class TestTheOpenerRuleOnTheSix:
    """Shawn's test: each of the six opens on a name."""

    @pytest.mark.parametrize("slot", SLOTS)
    def test_each_one_opens_on_a_name(self, slot, heroes):
        match_id, key = slot
        text = authored.AUTHORED[slot]
        assert opener_missing(text, facts_for(heroes, match_id)) == ""

    def test_the_openers_are_the_four_names(self):
        openers = sorted(
            {text.split()[0] for text in authored.AUTHORED.values()}
        )
        assert openers == ["Argentina", "Cuciuffo", "Maradona", "Molina"]


class TestThePlacesRuleOnTheSix:
    @pytest.mark.parametrize("slot", SLOTS)
    def test_each_one_places_the_move(self, slot, heroes):
        match_id, key = slot
        facts = facts_for(heroes, match_id)
        text = authored.AUTHORED[slot]
        assert places_missing(text, facts) == ""
        assert len(zones_said(text, facts)) >= PLACES_WANTED


class TestWhatTheCheckSaysToday:
    """Four ground, and two are refused by the pairing rather than by a
    claim.

    Both refusals are `_about` in `app/narration_grammar.py` pointing a place
    at the move beside it: "on into the final third" follows "past
    Beardsley", whose dribble is thirty yards short of the final third, and
    "beat Butcher on the right" leaves Butcher a bare name because "beat" is
    not one of `PAST_MARKERS`, so the place is read off England's record.
    """

    @pytest.mark.parametrize("slot", GROUNDED_TODAY)
    def test_the_four_are_grounded(self, slot, heroes):
        match_id, key = slot
        result = check(
            authored.AUTHORED[slot],
            facts_for(heroes, match_id),
            persona=narrator_for(key),
            side=side_for(heroes, match_id, key),
        )
        assert result.grounded, result.summary
        assert result.checked >= 17

    @pytest.mark.parametrize("slot", sorted(REFUSED_TODAY))
    def test_the_two_are_refused_for_a_place_and_nothing_else(
        self, slot, heroes
    ):
        match_id, key = slot
        result = check(
            authored.AUTHORED[slot],
            facts_for(heroes, match_id),
            persona=narrator_for(key),
            side=side_for(heroes, match_id, key),
        )
        assert not result.grounded
        assert {one.kind for one in result.failures} == {"zone"}
        assert REFUSED_TODAY[slot] in result.summary

    def test_the_script_says_so_and_exits_one(self, capsys):
        """The whole script, which is what a reader runs."""
        assert authored.main([]) == 1
        said = capsys.readouterr().out
        assert "2 of the six does not pass all three today." in said
        assert authored.AUTHORSHIP in said

    def test_it_takes_no_arguments(self):
        with pytest.raises(SystemExit):
            authored.main(["--confirm"])
