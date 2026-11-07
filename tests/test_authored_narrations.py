"""The six hero narrations the team wrote, read against `data/raw/`.

`scripts/authored_narrations.py` holds them verbatim and re-checks them with
the three rules a candidate meets: `app/grounding.py` as a goal call, the
places rule and the opener rule. These tests are the same three answers held
in the suite, so a check change that would cost a hero narration fails here
rather than in a run nobody made.

**All six pass all three.** Two of the 1986 tellings were written again to
get there, and the wordings they replaced are kept below with the refusal
each one met: "on into the final third" put a place beside a dribble thirty
yards short of it, and "beat Butcher" left Butcher a bare name because "beat"
is not one of `PAST_MARKERS`. Neither reading was widened to accept them, so
both refusals still stand and are held here, beside the lines that are
recorded now.

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

#: The two 1986 wordings these six replaced, and the claim each was refused
#: for. Kept because the refusals are the reason the lines were written
#: again: neither reading was widened to let them through, so both still
#: refuse, and a change to either one fails here.
REPLACED = {
    (MATCH_1986, "buddy_scored"): (
        "the final third",
        "Cuciuffo won it back deep in our own half, Enrique found Maradona "
        "just inside his own half, and from there it was all him: past "
        "Beardsley, on into the final third, past Butcher on the right, past "
        "Fenwick on the edge of the box, into the box, past Shilton, and he "
        "scored with his left foot! What a finish!",
    ),
    (MATCH_1986, "storyteller_neutral"): (
        "on the right",
        "Cuciuffo won it back deep in his own half, and Enrique played it to "
        "Maradona just inside his own half. He went past Beardsley there, "
        "carried it on into the final third, beat Butcher on the right and "
        "Fenwick on the edge of the box, then took it into the box, slipped "
        "past Shilton and scored with his left foot. What a moment.",
    ),
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
            "drafted with an AI assistant, edited by Shawn, verified by the "
            "grounding check"
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
        assert "No watsonx call wrote these" in text
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


class TestWhatTheCheckSays:
    """All six are grounded, and the two wordings they replaced are not.

    Both of those refusals are `_about` in `app/narration_grammar.py`
    pointing a place at the move beside it: "on into the final third" follows
    "past Beardsley", whose dribble is thirty yards short of the final third,
    and "beat Butcher on the right" leaves Butcher a bare name because "beat"
    is not one of `PAST_MARKERS`, so the place is read off England's record.
    The lines recorded now say "past Butcher in the final third on the
    right", which is the same claim about the same dribble in words the
    reading can pair.
    """

    def result(self, heroes, slot, text=None):
        match_id, key = slot
        return check(
            authored.AUTHORED[slot] if text is None else text,
            facts_for(heroes, match_id),
            persona=narrator_for(key),
            side=side_for(heroes, match_id, key),
        )

    @pytest.mark.parametrize("slot", SLOTS)
    def test_every_one_of_the_six_is_grounded(self, slot, heroes):
        answer = self.result(heroes, slot)
        assert answer.grounded, answer.summary
        assert answer.checked >= 17

    @pytest.mark.parametrize("slot", sorted(REPLACED))
    def test_the_wording_it_replaced_is_still_refused(self, slot, heroes):
        refused, text = REPLACED[slot]
        answer = self.result(heroes, slot, text)
        assert not answer.grounded
        assert {one.kind for one in answer.failures} == {"zone"}
        assert refused in answer.summary

    @pytest.mark.parametrize("slot", sorted(REPLACED))
    def test_the_line_recorded_now_is_not_the_one_it_replaced(self, slot):
        _refused, text = REPLACED[slot]
        assert authored.AUTHORED[slot] != text

    def test_the_script_says_so_and_exits_zero(self, capsys):
        """The whole script, which is what a reader runs."""
        assert authored.main([]) == 0
        said = capsys.readouterr().out
        assert "does not pass all three" not in said
        assert authored.AUTHORSHIP in said

    def test_it_takes_no_arguments(self):
        with pytest.raises(SystemExit):
            authored.main(["--confirm"])
