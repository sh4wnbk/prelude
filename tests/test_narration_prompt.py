"""Tests for the facts, the prompt and the fallback narration.

Nothing here calls a model. `tests/conftest.py` fails any test that opens a
connection, and these only read `data/raw/` and build strings.

The expected values are read out of the raw data the way the buildup tests do:
the 1986 numbers are written down, taken from a run over `data/raw/`, so a
regression shows up as a disagreement rather than as two derived values
agreeing with each other.
"""

import json
from pathlib import Path

import pytest

from app.narration_prompt import (
    TEMPLATE_MAX_SENTENCES,
    TEMPLATE_VERBS,
    Facts,
    build_prompt,
    facts_from_buildup,
    template_narration,
)
from app.statsbomb_event_feed import StatsBombEventFeed

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

MATCH_1986 = 3750191
MATCH_2022 = 3869685

# Maradona's second, read out of data/raw/. The buildup is one possession of 24
# events, every one of which carries a player, so there are 24 beats.
GOAL_1986 = {
    "clock": (54, 18),
    "beats": 24,
    "players": 8,
    "teams": ("Argentina", "England"),
    "numbers": {18, 54},
    "set_piece": None,
    "body_part": "Left Foot",
    "scorer": "Diego Armando Maradona",
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
        assert len(facts.beats) == GOAL_1986["beats"]
        assert len(facts.players) == GOAL_1986["players"]
        assert facts.teams == GOAL_1986["teams"]
        assert facts.numbers == frozenset(GOAL_1986["numbers"])
        assert facts.set_piece is GOAL_1986["set_piece"]
        assert facts.body_part == GOAL_1986["body_part"]
        assert facts.moment.player == GOAL_1986["scorer"]

    def test_a_set_piece_carries_its_recorded_type(self, feed):
        facts = facts_for(feed, MATCH_2022, PENALTY_2022["clock"])
        assert facts.set_piece == PENALTY_2022["set_piece"]
        assert len(facts.beats) == PENALTY_2022["beats"]

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

    def test_numbers_leave_out_the_other_seconds(self, feed):
        """Every second a possession passes through is a number from 0 to 59,
        so admitting them would ground almost any small number a model
        invented. Only the minutes and the goal's own second are in."""
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        seconds = {beat.second for beat in facts.beats}
        assert {2, 3, 4, 7, 13, 15} <= seconds
        assert facts.numbers == {54, 18}

    def test_the_goal_beat_is_the_shot(self, feed):
        for _, moment, facts in every_goal(feed):
            goal = facts.goal_beat
            assert goal.action == "Shot"
            assert (goal.minute, goal.second) == (moment.minute, moment.second)
            assert goal.player == moment.player


class TestPrompt:
    def test_the_prompt_carries_the_goal_and_the_run_of_play(self, feed):
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        prompt = build_prompt(facts)
        assert GOAL_1986["scorer"] in prompt
        assert "Left Foot" in prompt
        assert "Open Play" in prompt
        for beat in facts.beats:
            assert beat.player in prompt
            assert beat.action in prompt

    def test_the_prompt_shows_minutes_and_not_seconds(self, feed):
        """It used to print 54:04 and then forbid every digit but the minute
        and the goal's second, so a model that quoted the prompt was failed for
        it. The run of play now shows the minute only."""
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        run_of_play = build_prompt(facts).split("THE RUN OF PLAY")[1].split("RULES")[0]
        assert "min 54" in run_of_play
        assert "54:04" not in run_of_play
        assert "54:08" not in run_of_play

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
            sentences = [s for s in template_narration(facts).split(". ") if s]
            assert 0 < len(sentences) <= TEMPLATE_MAX_SENTENCES

    def test_it_ends_on_the_goal(self, feed):
        for _, moment, facts in every_goal(feed):
            text = template_narration(facts)
            assert text.rstrip().endswith(f"shoots and scores for {moment.team}.")
            assert moment.player in text

    def test_it_opens_on_the_recorded_minute(self, feed):
        for _, moment, facts in every_goal(feed):
            assert template_narration(facts).startswith(f"Minute {moment.minute}.")

    def test_it_says_only_names_actions_and_minutes_from_the_events(self, feed):
        """Grounded by construction: every sentence is built from one beat."""
        for _, _, facts in every_goal(feed):
            text = template_narration(facts)
            said = text.replace(f"Minute {facts.goal_beat.minute}.", "")
            for fragment in said.split(". "):
                fragment = fragment.strip().rstrip(".")
                if not fragment:
                    continue
                assert any(
                    fragment.startswith(beat.player) for beat in facts.beats
                ), fragment

    def test_it_does_not_repeat_the_same_player_and_action(self, feed):
        """Maradona's run is four Dribble events, which read as the same
        sentence four times before the runs were collapsed."""
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        sentences = template_narration(facts).split(". ")
        assert len(sentences) == len(set(sentences))

    def test_a_penalty_fallback_names_the_foul(self, feed):
        """The whole reason buildup reaches back a possession. If the fallback
        drops the foul, the set piece has no cause in the narration."""
        facts = facts_for(feed, MATCH_2022, PENALTY_2022["clock"])
        assert "commits a foul" in template_narration(facts)

    def test_every_action_it_can_say_has_a_verb(self, feed):
        """A type with no entry in TEMPLATE_VERBS is skipped rather than
        guessed at, so this checks the table covers the data."""
        seen = set()
        for _, _, facts in every_goal(feed):
            seen |= facts.actions
        assert seen <= set(TEMPLATE_VERBS), seen - set(TEMPLATE_VERBS)
