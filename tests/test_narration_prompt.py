"""Tests for the facts, the prompt and the fallback narration.

Nothing here calls a model. `tests/conftest.py` fails any test that opens a
connection, and these only read `data/raw/` and build strings.

The expected values are read out of the raw data the way the buildup tests do:
the 1986 numbers are written down, taken from a run over `data/raw/`, so a
regression shows up as a disagreement rather than as two derived values agreeing
with each other.
"""

import inspect
import json
from pathlib import Path

import pytest

from app.grounding import sentences
from app.narration_prompt import (
    Beat,
    Fact,
    Facts,
    NARRATION_STYLE,
    fact_text,
    style_block,
    EVENT_VERBS,
    cited_line,
    TEMPLATE_MAX_SENTENCES,
    key_beats,
    Facts,
    beats_block,
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

# Lineker's header: the buildup holds no dribble past a defender and no foul,
# so the shot is its only key beat and the beats block is empty for it.
LINEKER = {"clock": (80, 37)}

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
        """On a goal whose only key beat is the shot, nothing raises it."""
        facts = facts_for(feed, MATCH_1986, LINEKER["clock"])
        assert "Write 3 sentences" in build_prompt(facts, sentences=3)

    def test_the_count_rises_to_fit_the_beats_to_cover(self, feed):
        """A prompt cannot ask for four sentences and then name five.

        The 54:18 goal has four dribbles past a defender, so the beats block
        asks for four sentences before the goal sentence. A requested count
        below that would have the model drop one instruction to obey the
        other.
        """
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        assert len(key_beats(facts)) == 5
        assert "Write 5 sentences" in build_prompt(facts, sentences=3)
        assert "Write 5 sentences" in build_prompt(facts)

    def test_the_prompt_has_no_em_dashes(self, feed):
        """It tells the model not to use one, so it had better not model one."""
        for _, _, facts in every_goal(feed):
            assert "—" not in build_prompt(facts)


class TestBeatsBlock:
    """Task 4c: the key beats are named in the prompt, not left to be found.

    The measured run in `docs/narration_eval.md` found `granite4:micro`
    citing the shot and no other key beat in all fourteen narrations it wrote
    for the goals where coverage can move, while passing the grounding check
    every time. The facts were all there; the model took the first few in
    order and jumped to the goal.
    """

    def test_it_names_every_key_beat_but_the_shot(self, feed):
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        block = beats_block(facts)
        assert "THE BEATS TO COVER" in block
        for number, defender in (
            (10, "Peter Beardsley"),
            (14, "Terry Butcher"),
            (17, "Terry Fenwick"),
            (21, "Peter Shilton"),
        ):
            assert f"fact {number}: {defender}" in block

    def test_it_does_not_name_the_shot(self, feed):
        """The last line is the goal, which the rules already cover."""
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        assert f"fact {facts.goal_fact.number}:" not in beats_block(facts)

    def test_a_penalty_block_names_the_foul(self, feed):
        facts = facts_for(feed, MATCH_2022, PENALTY_2022["clock"])
        assert "won a foul" in beats_block(facts)

    def test_it_is_empty_when_the_shot_is_the_only_key_beat(self, feed):
        """Five of the nine goals, whose prompts this change leaves alone.

        That is what makes it sound to rerun the other four and compare them
        against the earlier numbers for these.
        """
        for match_id, clock in (
            (MATCH_1986, LINEKER["clock"]),
            (MATCH_2022, (35, 22)),
            (MATCH_2022, (80, 59)),
            (MATCH_2022, (107, 58)),
        ):
            facts = facts_for(feed, match_id, clock)
            assert [b.kind for b in key_beats(facts)] == ["shot"]
            assert beats_block(facts) == ""
            assert "THE BEATS TO COVER" not in build_prompt(facts)

    def test_every_number_it_cites_is_a_fact_in_the_passage(self, feed):
        """It names fact numbers for the model to cite, so a wrong one here
        would send every attempt to the grounding check with a bad tag."""
        for _, _, facts in every_goal(feed):
            numbers = {fact.number for fact in facts.facts}
            for line in beats_block(facts).splitlines():
                if line.strip().startswith("fact "):
                    cited = int(line.strip().split()[1].rstrip(":"))
                    assert cited in numbers

    def test_the_block_sits_in_the_prompt_after_the_facts(self, feed):
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        prompt = build_prompt(facts)
        assert prompt.index(facts.goal_fact.line) < prompt.index(
            "THE BEATS TO COVER"
        ) < prompt.index("WRITE IT LIKE THIS")

class TestTemplateNarration:
    def test_it_stays_within_its_sentence_budget_unless_a_beat_needs_room(
        self, feed
    ):
        """The budget is a target, and a key beat outranks it.

        `TEMPLATE_MAX_SENTENCES` used to be a ceiling, and reaching it was
        what dropped three of Maradona's four dribbles. The ceiling now is the
        minute line, every key beat but the shot, and the goal line.
        """
        for _, _, facts in every_goal(feed):
            said = sentences(template_narration(facts))
            ceiling = max(TEMPLATE_MAX_SENTENCES, 2 + len(key_beats(facts)) - 1)
            assert 0 < len(said) <= ceiling

    def test_it_cites_every_key_beat_of_the_passage(self, feed):
        """Grounded is not complete, and the fallback has to be both.

        It is built by code out of the facts, so it can see every beat and has
        no excuse for leaving one out. This is the property
        `tests/test_narration_eval.py` then measures as coverage.
        """
        for _, _, facts in every_goal(feed):
            cited = {n for s in sentences(template_narration(facts)) for n in s.cites}
            for beat in key_beats(facts):
                assert beat.covered_by(cited), f"{beat.label} is not in the fallback"

    def test_the_1986_fallback_names_all_four_defenders(self, feed):
        """The worked example, written out.

        The old fallback collapsed the run to one sentence and then trimmed
        it, so the goal everything else in this repo is tested against came
        out as a pass, a pass and a dribble.
        """
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        said = template_narration(facts)
        for defender in (
            "Peter Beardsley",
            "Terry Butcher",
            "Terry Fenwick",
            "Peter Shilton",
        ):
            assert f"{defender} was dribbled past." in said

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
        drops the foul, the set piece has no cause in the narration.

        It is said with the `Foul Won` record where there is one, naming the
        side the penalty was given to.
        """
        facts = facts_for(feed, MATCH_2022, PENALTY_2022["clock"])
        assert "won a foul" in template_narration(facts)

    def test_a_penalty_recorded_only_as_a_foul_committed_still_names_it(
        self, feed
    ):
        """The 117:05 penalty has no `Foul Won` record, only the other side.

        Preferring `Foul Won` without a fallback would have left that penalty
        with no foul in its narration at all.
        """
        facts = facts_for(feed, MATCH_2022, (117, 5))
        actions = {fact.beat.action for fact in facts.facts}
        assert "Foul Won" not in actions

        assert "committed a foul" in template_narration(facts)


class TestTheOneNarrationStyle:
    """Task 1 of Phase 5: one style, in every voice, with no persona in it.

    The prompt carried a persona's style text and a worked example of its
    register from Task 6b to Task 6d. Three measured runs found one register
    coming back whichever of the three was asked for
    (`docs/narration_eval.md`), so the narration text is one text now and the
    personas are separated in the audio. These tests hold the prompt to that:
    one style block, no persona input, and the first person refused in it.
    """

    def test_the_style_text_goes_in_whole(self, feed):
        """Verbatim, because the constant is where the style is argued about."""
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        prompt = build_prompt(facts)
        assert "THE STYLE" in prompt
        # Wrapped into the prompt's own column width, so the words are what is
        # compared rather than the line breaks.
        assert " ".join(NARRATION_STYLE.split()) in " ".join(prompt.split())

    def test_the_style_block_is_in_every_prompt(self, feed):
        """There is no prompt without it, which is what "one style" means.

        It was conditional while a persona carried the style: `persona=None`
        printed no block at all and was the arm the Task 4a and 4c runs in
        `docs/narration_eval.md` were measured on. Nothing is conditional now.
        """
        for _, _, facts in every_goal(feed):
            assert "THE STYLE" in build_prompt(facts)

    def test_the_prompt_takes_no_persona_and_no_side(self, feed):
        """The signature is the claim: the words do not depend on the voice.

        A persona argument that changed nothing would be worse than none: a
        caller would read it as a register reaching the model, which is the
        thing three runs measured and did not find.
        """
        taken = set(inspect.signature(build_prompt).parameters)
        assert taken == {"facts", "sentences", "beats"}

    def test_the_prompt_refuses_the_first_person_in_the_one_voice_it_has(
        self, feed
    ):
        """Including the Buddy's, which the prompt asked for until now.

        `app/grounding.py` still admits "we" from a partisan voice over that
        side's facts. A prompt asking for less than the check enforces sets
        the model up to fail; this asks for more, which costs nothing.
        """
        facts = facts_for(feed, MATCH_1986, GOAL_1986["clock"])
        prompt = " ".join(build_prompt(facts).split())
        assert '"you", "your", "we", "our" and "us" are all rejected' in prompt

    def test_the_block_is_the_constant_and_nothing_else(self):
        assert " ".join(style_block().split()) == "THE STYLE " + " ".join(
            NARRATION_STYLE.split()
        )

    def test_no_prompt_has_an_em_dash(self, feed):
        for _, _, facts in every_goal(feed):
            assert "—" not in build_prompt(facts)
