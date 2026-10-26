"""Tests for the facts, the prompt and the fallback narration.

Nothing here calls a model. `tests/conftest.py` fails any test that opens a
connection, and these only read `data/raw/` and build strings.

The expected values are read out of the raw data the way the buildup tests do:
the 1986 numbers are written down, taken from a run over `data/raw/`, so a
regression shows up as a disagreement rather than as two derived values agreeing
with each other.
"""

import json
from pathlib import Path

import pytest

from app.grounding import sentences
from app.narration_prompt import (
    EVENT_VERBS,
    cited_line,
    TEMPLATE_MAX_SENTENCES,
    Facts,
    build_prompt,
    fact_list,
    facts_from_buildup,
    template_narration,
)
from app.statsbomb_event_feed import StatsBombEventFeed

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

MATCH_1986 = 3750191
MATCH_2022 = 3869685

# Maradona's second, read out of data/raw/. The buildup is one possession of 24
# events, every one of which carries a player, so there are 24 beats and 24
# numbered facts.
GOAL_1986 = {
    "clock": (54, 18),
    "beats": 24,
    "players": 8,
    "teams": ("Argentina", "England"),
    "set_piece": None,
    "body_part": "Left Foot",
    "scorer": "Diego Armando Maradona",
    # Fact 14, written out as the prompt prints it. Past tense: a buildup is
    # playback of a passage that already happened.
    "fact_14": "Terry Butcher (England) was dribbled past, 54:13",
}

# The first of the three 2022 penalties, which reaches back a possession.
PENALTY_2022 = {
    "clock": (22, 24),
    "beats": 100,
    "set_piece": "Penalty",
}


@pytest.fixture(scope="module")
def feed():
    return StatsBombEventFeed()


def facts_for(feed, match_id, clock) -> Facts:
    moment = next(
        m
        for m in feed.defining_moments(match_id)
        if (m.minute, m.second) == clock
    )
    return facts_from_buildup(feed.buildup(match_id, moment))


def every_goal(feed):
    for match_id in (MATCH_1986, MATCH_2022):
        for moment in feed.defining_moments(match_id):
            yield match_id, moment, facts_from_buildup(
                feed.buildup(match_id, moment)
            )


class TestFacts:
    def test_facts_match_the_raw_data(self, feed):
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        assert len(facts.facts) == GOAL_1986["beats"]
        assert len(facts.beats) == GOAL_1986["beats"]
        assert len(facts.players) == GOAL_1986["players"]
        assert facts.teams == GOAL_1986["teams"]
        assert facts.set_piece is GOAL_1986["set_piece"]
        assert facts.body_part == GOAL_1986["body_part"]
        assert facts.moment.player == GOAL_1986["scorer"]

    def test_a_set_piece_carries_its_recorded_type(self, feed):
        facts = facts_for(feed, MATCH_2022, PENALTY_2022["clock"])
        assert facts.set_piece == PENALTY_2022["set_piece"]
        assert len(facts.facts) == PENALTY_2022["beats"]

    def test_every_beat_is_a_real_event(self, feed):
        """A beat is a reduction of a record, not a new fact. Each one has to
        be findable by id in the source file, with the same values."""
        with (RAW / "events" / f"{MATCH_1986}.json").open(encoding="utf-8") as fh:
            raw_by_id = {e["id"]: e for e in json.load(fh)}
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        for beat in facts.beats:
            source = raw_by_id[beat.event_id]
            assert beat.minute == source["minute"]
            assert beat.second == source["second"]
            assert beat.player == source["player"]["name"]
            assert beat.team == source["team"]["name"]
            assert beat.action == source["type"]["name"]

    def test_the_goal_fact_is_the_shot_and_comes_last(self, feed):
        for _, moment, facts in every_goal(feed):
            goal = facts.goal_fact
            assert goal.number == len(facts.facts)
            assert goal.beat.action == "Shot"
            assert (goal.beat.minute, goal.beat.second) == (
                moment.minute,
                moment.second,
            )
            assert goal.beat.player == moment.player


class TestFactList:
    """The numbered facts: one per event, built by code from the record."""

    def test_one_fact_per_event_numbered_from_one(self, feed):
        for _, _, facts in every_goal(feed):
            assert [fact.number for fact in facts.facts] == list(
                range(1, len(facts.beats) + 1)
            )
            assert [fact.beat for fact in facts.facts] == list(facts.beats)

    def test_a_fact_says_who_which_team_what_and_when(self, feed):
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        assert facts.facts[13].text == GOAL_1986["fact_14"]
        assert facts.facts[13].line == f"14. {GOAL_1986['fact_14']}"

    def test_every_fact_leads_back_to_one_record(self, feed):
        """A citation is worth nothing if the fact it names cannot be found in
        the source file."""
        with (RAW / "events" / f"{MATCH_1986}.json").open(encoding="utf-8") as fh:
            raw_by_id = {e["id"]: e for e in json.load(fh)}
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        for fact in facts.facts:
            source = raw_by_id[fact.beat.event_id]
            assert source["player"]["name"] in fact.text
            assert source["team"]["name"] in fact.text

    def test_the_list_prints_every_fact_once(self, feed):
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        printed = fact_list(facts).splitlines()
        assert len(printed) == len(facts.facts)
        for fact, line in zip(facts.facts, printed):
            assert line.strip() == fact.line

    def test_a_fact_names_one_player(self, feed):
        """One record names one player, so a fact does too. Pairing two
        records into "Maradona dribbles past Butcher" would mean inferring
        which dribble went past whom."""
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        for fact in facts.facts:
            named = [
                player for player in facts.players if player in fact.text
            ]
            assert named == [fact.beat.player], fact.text

    def test_every_action_in_the_data_has_a_verb(self, feed):
        """A type with no entry in EVENT_VERBS falls back to naming the type,
        which is honest but reads badly, so this checks the table covers the
        data and the fallback stays unreachable."""
        seen = set()
        for _, _, facts in every_goal(feed):
            seen |= facts.actions
        assert seen <= set(EVENT_VERBS), seen - set(EVENT_VERBS)


class TestPrompt:
    def test_the_prompt_carries_the_goal_and_the_facts(self, feed):
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        prompt = build_prompt(facts)
        assert GOAL_1986["scorer"] in prompt
        assert "Left Foot" in prompt
        assert "Open Play" in prompt
        for fact in facts.facts:
            assert fact.line in prompt

    def test_the_prompt_asks_for_a_citation_on_every_sentence(self, feed):
        """The check reads a sentence against the facts it cited, so a prompt
        that did not ask for them would fail every attempt."""
        prompt = build_prompt(facts_for(feed, MATCH_1986, GOAL_1986["clock"]))
        assert "square brackets" in prompt
        assert "[1]" in prompt

    def test_the_citation_comes_first_on_the_line(self, feed):
        """What three live layouts settled. Asked for the tag at the end of the
        sentence, `granite4:micro` wrote sentences with no tag at all: a model
        that has finished the sentence has nothing left to look up. Asked for
        the number first, it tagged every line."""
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        for fact in (facts.facts[0], facts.goal_fact):
            line = cited_line(fact)
            assert line.startswith(f"[{fact.number}] ")
            assert line in build_prompt(facts)

    def test_the_worked_example_shows_two_different_numbers(self, feed):
        """It showed one, the goal's, and the model ended all four sentences
        with that number, having read the example as the answer rather than the
        shape."""
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        prompt = build_prompt(facts)
        first, goal = facts.facts[0], facts.goal_fact
        assert first.number != goal.number
        assert f"[{first.number}]" in prompt
        assert f"[{goal.number}]" in prompt
        assert "not put the same number on every line" in prompt

    def test_the_worked_example_is_a_fact_said_as_a_sentence(self, feed):
        """It has to show the step from a numbered line to a cited sentence,
        and invent nothing doing it."""
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        first = facts.facts[0]
        example = cited_line(first)
        assert example.startswith(f"[{first.number}] {first.beat.player}")
        assert EVENT_VERBS[first.beat.action] in example

    def test_the_prompt_says_how_to_find_a_number(self, feed):
        """The attempt that came back grounded was written under this block."""
        prompt = build_prompt(facts_for(feed, MATCH_1986, GOAL_1986["clock"]))
        assert "WRITE IT LIKE THIS" in prompt
        assert "read the number at the start of its line" in prompt

    def test_the_prompt_asks_for_one_action_per_sentence(self, feed):
        """The check pairs every name in a sentence with every action in it, so
        a sentence about one action is one it can read exactly."""
        prompt = build_prompt(facts_for(feed, MATCH_1986, GOAL_1986["clock"]))
        assert "one action" in prompt

    def test_the_prompt_states_the_rules_the_check_enforces(self, feed):
        """A prompt that asked for less than the check requires would set the
        model up to fail, and a retry would not help it."""
        prompt = build_prompt(facts_for(feed, MATCH_1986, GOAL_1986["clock"]))
        for rule in ("nickname", "em dash", "digit", "penalty", "score"):
            assert rule in prompt.lower(), rule

    def test_the_prompt_asks_for_the_requested_sentence_count(self, feed):
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        assert "Write 3 sentences" in build_prompt(facts, sentences=3)

    def test_the_prompt_has_no_em_dashes(self, feed):
        """It tells the model not to use one, so it had better not model one."""
        for _, _, facts in every_goal(feed):
            assert "—" not in build_prompt(facts)


class TestTemplateNarration:
    def test_it_stays_within_its_sentence_budget(self, feed):
        for _, _, facts in every_goal(feed):
            assert 0 < len(sentences(template_narration(facts))) <= (
                TEMPLATE_MAX_SENTENCES
            )

    def test_every_sentence_cites_the_fact_it_was_built_from(self, feed):
        """Grounded by construction means each sentence names its record, not
        just that the words came from somewhere in the passage."""
        for _, _, facts in every_goal(feed):
            numbers = {fact.number for fact in facts.facts}
            for sentence in sentences(template_narration(facts)):
                assert len(sentence.cites) == 1, sentence
                assert sentence.cites[0] in numbers, sentence

    def test_it_ends_on_the_goal(self, feed):
        for _, moment, facts in every_goal(feed):
            last = sentences(template_narration(facts))[-1]
            assert last.text == (
                f"{moment.player} shot and scored for {moment.team}."
            )
            assert last.cites == (facts.goal_fact.number,)

    def test_it_opens_on_the_recorded_minute(self, feed):
        for _, moment, facts in every_goal(feed):
            first = sentences(template_narration(facts))[0]
            assert first.text == f"Minute {moment.minute}."

    def test_it_says_only_names_actions_and_minutes_from_the_facts(self, feed):
        """Every sentence between the first and the last is built from one
        fact, and names the player that fact names."""
        for _, _, facts in every_goal(feed):
            by_number = {fact.number: fact for fact in facts.facts}
            for sentence in sentences(template_narration(facts))[1:-1]:
                fact = by_number[sentence.cites[0]]
                assert sentence.text.startswith(fact.beat.player), sentence
                assert EVENT_VERBS[fact.beat.action] in sentence.text, sentence

    def test_it_does_not_repeat_the_same_player_and_action(self, feed):
        """Maradona's run is four Dribble events, which read as the same
        sentence four times before the runs were collapsed."""
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        said = [s.text for s in sentences(template_narration(facts))]
        assert len(said) == len(set(said))

    def test_a_penalty_fallback_names_the_foul(self, feed):
        """The whole reason buildup reaches back a possession. If the fallback
        drops the foul, the set piece has no cause in the narration."""
        facts = facts_for(feed, MATCH_2022, PENALTY_2022["clock"])
        assert "committed a foul" in template_narration(facts)
