"""Tests for the goal-call prompt and the per-slot candidate run.

Two things are covered here, and both are about the shape of a run rather than
about what a model wrote: `app/goal_call_prompt.py`, which is the prompt a goal
call is written from, and `scripts/narrator_candidates.py`, which generates
three candidates for each of the six recorded slots.

Nothing here calls a model. `tests/conftest.py` fails any test that opens a
connection, so the run's own plan is exercised and its paid path is not.
"""

import json
from pathlib import Path

import pytest

from app.goal_call_prompt import (
    BUDDY_CONCEDED,
    BUDDY_SCORED,
    CALLER_NEUTRAL,
    GOAL_CALL_CHARACTERS_PER_WORD,
    GOAL_CALL_TARGET_CHARACTERS,
    INVENTED_MATCH,
    STORYTELLER_NEUTRAL,
    STYLES,
    build_goal_call_prompt,
    record_line,
    records_block,
    shared_name_parts,
    situation_for,
    slot_key,
    steps_block,
)
from app.grounding import check
from app.narration_grammar import WORD, fold
from app.narration_prompt import HERO_TARGET_CHARACTERS, facts_from_buildup
from app.personas import THE_BUDDY, THE_CALLER, THE_STORYTELLER
from app.recorded_names import recorded_nicknames
from app.statsbomb_event_feed import StatsBombEventFeed
from scripts.narrator_candidates import (
    DEFAULT_PER_SLOT,
    billed_for_slot,
    goals_to_run,
    main,
    narrator_for,
    review,
    slot_coverage,
    slots_for,
)
from scripts.tts_hero import DEFAULT_BUDGET
import tests.test_reference_narrations as references

ROOT = Path(__file__).resolve().parent.parent

MATCH_1986 = 3750191
MATCH_2022 = 3869685
HERO_1986 = (54, 18)
HERO_2022 = (35, 22)

#: The six recordings, and the reference narration each one is the standard
#: for. `tests/test_reference_narrations.py` is where the words live; this
#: file prices them.
RECORDED = (
    (MATCH_1986, STORYTELLER_NEUTRAL, references.STORYTELLER_1986),
    (MATCH_1986, BUDDY_SCORED, references.BUDDY_1986_ARGENTINA),
    (MATCH_1986, BUDDY_CONCEDED, references.BUDDY_1986_ENGLAND),
    (MATCH_2022, STORYTELLER_NEUTRAL, references.STORYTELLER_2022),
    (MATCH_2022, BUDDY_SCORED, references.BUDDY_2022_ARGENTINA),
    (MATCH_2022, BUDDY_CONCEDED, references.BUDDY_2022_FRANCE),
)


def flat(text: str) -> str:
    """The prompt as one line, for asserting on prose that is hard wrapped.

    The rules wrap at 76 columns, so a phrase a test looks for can sit across
    a line break. Flattening says what the rule says without pinning where it
    happens to wrap.
    """
    return " ".join(text.split())


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


class TestTheFourStyles:
    """One style per narrator and situation, and no fifth."""

    def test_there_are_four(self):
        assert set(STYLES) == {
            STORYTELLER_NEUTRAL,
            BUDDY_SCORED,
            BUDDY_CONCEDED,
            CALLER_NEUTRAL,
        }

    def test_the_buddy_is_the_one_split_by_situation(self):
        """Which is the one that needs a side: a fan whose team conceded is
        not told the same sentences as a fan whose team scored."""
        assert slot_key(THE_BUDDY.id, "scored") == BUDDY_SCORED
        assert slot_key(THE_BUDDY.id, "conceded") == BUDDY_CONCEDED
        for situation in ("scored", "conceded", "neutral"):
            assert slot_key(THE_STORYTELLER.id, situation) == (
                STORYTELLER_NEUTRAL
            )
            assert slot_key(THE_CALLER.id, situation) == CALLER_NEUTRAL

    def test_a_neutral_buddy_has_no_style_and_says_so(self):
        """The Buddy is `fans_only`, so there is nothing to write for it."""
        with pytest.raises(KeyError) as raised:
            slot_key(THE_BUDDY.id, "neutral")
        assert "no goal-call style" in str(raised.value)

    def test_the_situation_is_read_off_the_side_and_the_scorer(self):
        assert situation_for("Argentina", "Argentina") == "scored"
        assert situation_for("England", "Argentina") == "conceded"
        assert situation_for(None, "Argentina") == "neutral"
        assert situation_for("argentina", "Argentina") == "scored"

    def test_each_style_says_what_it_does_with_the_first_person(self):
        """The one rule the check reads differently per narrator, so the one
        the prompt has to say differently per narrator."""
        assert '"we"' in STYLES[BUDDY_SCORED].style
        for key in (STORYTELLER_NEUTRAL, BUDDY_CONCEDED, CALLER_NEUTRAL):
            assert 'no "we"' in STYLES[key].style.lower()

    def test_each_style_says_where_the_exclamation_mark_may_stand(self):
        assert "exclamation mark" in STYLES[BUDDY_SCORED].style
        assert "exclamation mark" in STYLES[BUDDY_CONCEDED].style
        assert "no exclamation mark" in STYLES[STORYTELLER_NEUTRAL].style
        assert STYLES[BUDDY_SCORED].example.endswith("!")
        assert STYLES[CALLER_NEUTRAL].example.endswith("!")
        assert STYLES[STORYTELLER_NEUTRAL].example.endswith(".")
        assert STYLES[BUDDY_CONCEDED].example.endswith(".")


class TestTheExampleIsInvented:
    """The style is shown through a match that does not exist.

    The eight references are the standard, not the material: a reference in the
    prompt for the goal it describes is dictation, and the check passing it
    back would measure nothing. These tests are what keeps that true as the
    prompt is edited.
    """

    @pytest.mark.parametrize("key", sorted(STYLES))
    def test_no_example_names_a_real_player_or_team(
        self, key, facts_1986, facts_2022
    ):
        said = {
            fold(word)
            for word in WORD.findall(
                STYLES[key].example + " " + INVENTED_MATCH
            )
        }
        for facts in (facts_1986, facts_2022):
            for player in facts.players:
                for part in WORD.findall(player):
                    assert fold(part) not in said, (key, part)
            for team in facts.teams:
                assert fold(team) not in said, (key, team)

    @pytest.mark.parametrize("key", sorted(STYLES))
    def test_no_example_is_a_reference_narration(self, key):
        example = STYLES[key].example
        for name, text in vars(references).items():
            if not name.isupper() or not isinstance(text, str):
                continue
            assert example != text

    @pytest.mark.parametrize("key", sorted(STYLES))
    def test_no_prompt_carries_a_reference_narration(
        self, key, facts_1986, facts_2022
    ):
        """The whole prompt, not only the example: the standard never goes in.

        A reference is one long sentence, so a shared opening clause is enough
        to show it leaked. Twenty-five characters is longer than any phrase the
        rules and the records share with one.
        """
        for facts in (facts_1986, facts_2022):
            prompt = flat(build_goal_call_prompt(facts, key))
            for name, text in vars(references).items():
                if not name.isupper() or not isinstance(text, str):
                    continue
                if len(text) < 60:
                    continue
                assert text[:25] not in prompt, (key, name)

    def test_the_invented_goal_is_a_different_shape_from_both_real_ones(self):
        """Right foot, one defender beaten, and a long ball, which is neither
        1986 (left foot, four beaten, no long ball) nor 2022 (left foot, none
        beaten, first time)."""
        assert "right foot" in INVENTED_MATCH
        assert "long ball" in INVENTED_MATCH
        assert "left foot" not in INVENTED_MATCH
        assert "first time" not in INVENTED_MATCH


class TestTheRecordsInThePrompt:
    """What the model is shown, which is read off the records."""

    def test_no_record_line_carries_a_clock(self, facts_1986, facts_2022):
        """The narration carries none, so the prompt shows none: a clock in
        front of a model is a clock in the narration."""
        for facts in (facts_1986, facts_2022):
            block = records_block(facts)
            assert ":" not in block
            assert not any(character.isdigit()
                           for line in block.splitlines()
                           for character in line.split(".", 1)[1])

    def test_a_pass_line_names_who_it_reached(self, facts_2022):
        block = records_block(facts_2022)
        assert "Nahuel Molina (Argentina) passed to Alexis MacAllister" in block
        assert "a long ball" in block
        assert "the assist" in block

    def test_the_shot_line_carries_the_body_part(self, facts_1986, facts_2022):
        assert "shot, with his left foot, in the box" in records_block(
            facts_1986
        )
        assert "shot, first time, with his left foot, in the box" in (
            records_block(facts_2022)
        )

    def test_a_defenders_line_carries_no_field_position(self, facts_1986):
        """StatsBomb mirrors a defensive record, so "his own half" on
        Beardsley's `Pressure` would mean the half England were attacking."""
        lines = [
            line
            for line in records_block(facts_1986).splitlines()
            if "(England)" in line
        ]
        assert lines
        for line in lines:
            assert "own half" not in line
            assert "in the box" not in line

    def test_the_pressure_records_are_there_for_the_conceding_buddy(
        self, facts_1986
    ):
        """"Beardsley and Reid closed him down" needs those records shown."""
        block = records_block(facts_1986)
        assert "Peter Beardsley (England) pressed" in block
        assert "Peter Reid (England) pressed" in block
        assert "Terry Butcher (England) pressed" in block

    def test_the_steps_say_a_dribble_past_once(self, facts_1986):
        block = steps_block(facts_1986)
        assert "Diego Armando Maradona dribbled past Peter Beardsley" in block
        assert "Diego Armando Maradona dribbled past Peter Shilton" in block
        assert "went dribbled" not in block
        assert block.rstrip().endswith("(the goal)")

    def test_the_steps_chain_the_2022_passes_in_order(self, facts_2022):
        lines = steps_block(facts_2022).splitlines()
        assert "passed to Alexis MacAllister" in lines[0]
        assert "passed to Lionel Messi" in lines[1]
        assert "passed to Julián Álvarez" in lines[2]
        assert "passed to Alexis MacAllister" in lines[3]
        assert "passed to Ángel Di María" in lines[4]

    def test_a_record_line_uses_the_recorded_nickname(self, facts_2022):
        beat = facts_2022.facts[10].beat
        assert record_line(facts_2022, beat) == (
            "Alexis MacAllister (Argentina) passed to Ángel Di María, "
            "the assist, in the box"
        )


class TestTheRulesMatchTheCheck:
    """The prompt asks for no less than `app/grounding.py` enforces."""

    def test_the_shared_name_parts_are_printed(self, facts_1986, facts_2022):
        """The grammar refuses them and a model cannot guess which they are."""
        assert shared_name_parts(facts_1986) == ("Peter", "Terry")
        assert shared_name_parts(facts_2022) == ()
        prompt = flat(build_goal_call_prompt(facts_1986, STORYTELLER_NEUTRAL))
        assert '"Peter", "Terry"' in prompt
        other = flat(build_goal_call_prompt(facts_2022, STORYTELLER_NEUTRAL))
        assert "every part of every name is unambiguous" in other

    @pytest.mark.parametrize("key", sorted(STYLES))
    def test_every_prompt_refuses_the_clock_and_the_digit(
        self, key, facts_1986
    ):
        prompt = flat(build_goal_call_prompt(facts_1986, key))
        assert "No clock and no digit anywhere" in prompt

    @pytest.mark.parametrize("key", sorted(STYLES))
    def test_every_prompt_asks_for_the_past_tense_and_the_finish(
        self, key, facts_2022
    ):
        prompt = flat(build_goal_call_prompt(facts_2022, key))
        assert "Write in the past tense" in prompt
        assert "the last thing you say" in prompt.lower()

    @pytest.mark.parametrize("key", sorted(STYLES))
    def test_every_prompt_names_its_narrator(self, key, facts_2022):
        prompt = flat(build_goal_call_prompt(facts_2022, key))
        assert STYLES[key].label in prompt
        assert STYLES[key].example in prompt

    def test_the_target_is_the_length_the_references_run_to(self):
        """230 characters and 42 words, measured off the eight references.

        They run 202 to 269 characters in 37 to 51 words. A goal call says the
        same move in fewer characters than the cited narration does, because
        it joins its clauses rather than giving each step a sentence, so the
        target is well under `HERO_TARGET_CHARACTERS`.
        """
        lengths = [len(text) for _, _, text in RECORDED]
        words = [len(text.split()) for _, _, text in RECORDED]
        assert min(lengths) <= GOAL_CALL_TARGET_CHARACTERS <= max(lengths)
        assert GOAL_CALL_TARGET_CHARACTERS < HERO_TARGET_CHARACTERS
        assert round(
            GOAL_CALL_TARGET_CHARACTERS / GOAL_CALL_CHARACTERS_PER_WORD
        ) == pytest.approx(sum(words) / len(words), abs=2)

    @pytest.mark.parametrize(
        "slot, text",
        [(slot, text) for _, slot, text in RECORDED],
        ids=[slot for _, slot, _ in RECORDED],
    )
    def test_a_reference_narration_meets_the_length_the_prompt_asks_for(
        self, slot, text
    ):
        """The prompt asks for about what the standard actually is.

        A target the references themselves miss would be a prompt asking for
        something nobody has written. Half again over the target is the room
        allowed, which every reference is inside.
        """
        assert len(text) <= GOAL_CALL_TARGET_CHARACTERS * 1.5


class TestTheSixRecordedSlots:
    """Which slots a run generates for, read off `hero.voice_for`."""

    def test_three_slots_per_match_and_six_in_all(self):
        for match_id in (MATCH_1986, MATCH_2022):
            slots = slots_for(match_id, "Argentina")
            assert [key for key, _ in slots] == [
                BUDDY_CONCEDED,
                BUDDY_SCORED,
                STORYTELLER_NEUTRAL,
            ]

    def test_the_conceding_side_is_the_other_team_in_the_fixture(self):
        assert dict(slots_for(MATCH_1986, "Argentina")) == {
            BUDDY_CONCEDED: "England",
            BUDDY_SCORED: "Argentina",
            STORYTELLER_NEUTRAL: None,
        }
        assert dict(slots_for(MATCH_2022, "Argentina")) == {
            BUDDY_CONCEDED: "France",
            BUDDY_SCORED: "Argentina",
            STORYTELLER_NEUTRAL: None,
        }

    def test_france_has_no_record_in_the_2022_passage(self, facts_2022):
        """Which is why the conceding Buddy there may not say "we", and why
        the side still has to come off the fixture rather than off the facts:
        `Facts.teams` holds Argentina alone."""
        assert facts_2022.teams == ("Argentina",)
        assert dict(slots_for(MATCH_2022, "Argentina"))[BUDDY_CONCEDED] == (
            "France"
        )

    def test_the_caller_is_not_a_recorded_slot(self):
        """It has a style and no recording: `hero.voice_for` sends no listener
        to it, so nothing generates for it."""
        for match_id in (MATCH_1986, MATCH_2022):
            assert CALLER_NEUTRAL not in dict(slots_for(match_id, "Argentina"))
        assert CALLER_NEUTRAL in STYLES

    def test_the_narrator_of_a_slot(self):
        assert narrator_for(BUDDY_SCORED) is THE_BUDDY
        assert narrator_for(BUDDY_CONCEDED) is THE_BUDDY
        assert narrator_for(STORYTELLER_NEUTRAL) is THE_STORYTELLER

    def test_a_slot_the_run_has_no_side_for_is_refused(self, tmp_path, monkeypatch):
        """A slot added to the app is a slot this run has to be taught, and
        the refusal says so rather than narrating it with no side."""
        doc = json.loads(
            (ROOT / "app" / "web" / "matches.json").read_text(encoding="utf-8")
        )
        for match in doc["matches"]:
            match["hero"]["voice_for"]["team_c"] = "caller_neutral"
        path = tmp_path / "matches.json"
        path.write_text(json.dumps(doc), encoding="utf-8")
        monkeypatch.setattr("scripts.narrator_candidates.MATCHES", path)
        with pytest.raises(SystemExit) as raised:
            slots_for(MATCH_1986, "Argentina")
        assert "no side for" in str(raised.value)


class TestTheSlotPrice:
    """One recording each, which is what the budget is divided by."""

    def test_a_slot_is_priced_as_one_recording(self):
        """`billed_for_match` priced one narration spoken by three voices.
        Each slot has its own narration now, so its price is its own request
        and is about a third of that."""
        from scripts.hero_candidates import billed_for_match

        text = references.STORYTELLER_2022
        one = billed_for_slot(MATCH_2022, STORYTELLER_NEUTRAL, text)
        assert one < billed_for_match(MATCH_2022, text)
        assert one * 3 == pytest.approx(
            billed_for_match(MATCH_2022, text), abs=60
        )

    def test_the_header_and_the_markup_are_billed(self):
        text = references.BUDDY_2022_ARGENTINA
        assert billed_for_slot(MATCH_2022, BUDDY_SCORED, text) > len(text)

    @pytest.mark.parametrize(
        "match_id, slot, text",
        RECORDED,
        ids=["{}-{}".format(match_id, slot) for match_id, slot, _ in RECORDED],
    )
    def test_every_reference_fits_the_allowance_for_one_recording(
        self, match_id, slot, text
    ):
        """583 a recording, which is 3,500 over the six."""
        assert billed_for_slot(match_id, slot, text) <= DEFAULT_BUDGET // 6

    def test_the_six_references_together_fit_the_budget(self):
        """1,873 of the 3,500, which is what the standard costs to record."""
        total = sum(
            billed_for_slot(match_id, slot, text)
            for match_id, slot, text in RECORDED
        )
        assert total == 1873
        assert total < DEFAULT_BUDGET


class TestWhatTheRunAsksFor:
    """The plan, which prints the call count and sends nothing."""

    def test_three_per_slot_is_eighteen(self):
        assert DEFAULT_PER_SLOT == 3
        assert DEFAULT_PER_SLOT * 6 == 18

    def test_the_plan_states_the_call_count_and_sends_nothing(self, capsys):
        assert main(["--plan"]) == 0
        printed = capsys.readouterr().out
        assert "at most 54 generations (6 slots x 3 candidates x 3 attempts)" in printed
        assert "nothing was sent" in printed
        assert "3500 billed for the 6 recordings together, so 583 a recording" in printed

    def test_no_confirm_also_sends_nothing(self, capsys):
        assert main([]) == 0
        assert "nothing was sent" in capsys.readouterr().out

    def test_the_review_file_may_not_be_written_into_the_repo(self):
        with pytest.raises(SystemExit) as raised:
            main(["--plan", "--out", str(ROOT / "docs")])
        assert "inside the repo" in str(raised.value)

    def test_one_goal_can_be_rerun_on_its_own(self):
        assert [hero[1] for hero in goals_to_run([MATCH_2022])] == [MATCH_2022]
        assert len(goals_to_run([])) == 2

    def test_a_match_that_is_not_a_hero_is_refused(self):
        with pytest.raises(SystemExit) as raised:
            goals_to_run([1])
        assert "not one of the hero goals" in str(raised.value)


class TestWhatACandidateIsMeasuredOn:
    """The coverage numbers a choice is made on, read off the words."""

    def test_a_reference_names_every_player_it_should(self, facts_2022):
        cover = slot_coverage(references.STORYTELLER_2022, facts_2022)
        assert len(cover["named_players"]) == 5
        assert cover["touched_not_named"] == ()
        assert cover["key_beats_reached"] == cover["key_beats"]

    def test_the_1986_reference_reaches_every_dribble_beat(self, facts_1986):
        cover = slot_coverage(references.STORYTELLER_1986, facts_1986)
        assert cover["key_beats"] == 5
        assert cover["key_beats_reached"] == 5
        assert cover["beats_missed"] == ()
        assert "Peter Reid" in cover["missing_players"]

    def test_a_narration_that_leaves_a_defender_out_is_measured_short(
        self, facts_1986
    ):
        thin = (
            "Maradona carried it forward past Beardsley and scored with his "
            "left foot."
        )
        cover = slot_coverage(thin, facts_1986)
        assert cover["key_beats_reached"] < cover["key_beats"]
        assert any("Butcher" in beat for beat in cover["beats_missed"])

    def test_no_reference_carries_a_digit(self, facts_1986):
        """The digit count reads the text, so one buildup answers for all
        six: what is being counted is not in the records."""
        for _, _, text in RECORDED:
            assert slot_coverage(text, facts_1986)["digits"] == 0

    def test_the_cheer_is_counted(self, facts_1986, facts_2022):
        assert slot_coverage(
            references.BUDDY_1986_ARGENTINA, facts_1986
        )["cheers"] == 1
        assert slot_coverage(
            references.BUDDY_1986_ENGLAND, facts_1986
        )["cheers"] == 0
        assert slot_coverage(
            references.STORYTELLER_2022, facts_2022
        )["cheers"] == 0


class TestTheReviewFile:
    """What Shawn reads aloud, built from a run's own records."""

    def test_it_groups_the_candidates_by_slot(self, facts_1986):
        goals = [
            {
                "year": 1986,
                "match_id": MATCH_1986,
                "minute": 54,
                "second": 18,
                "player": "Diego Armando Maradona",
                "team": "Argentina",
                "records": 24,
                "recorded_players": ("Diego Armando Maradona",),
                "players_who_touched_the_ball": ("Diego Armando Maradona",),
                "shared_name_parts": ("Peter", "Terry"),
                "slots": [
                    {
                        "slot": BUDDY_SCORED,
                        "label": STYLES[BUDDY_SCORED].label,
                        "narrator": "buddy",
                        "side": "Argentina",
                        "candidates": [
                            {
                                "candidate": 1,
                                "text": references.BUDDY_1986_ARGENTINA,
                                "attempt": 1,
                                "first_attempt_grounded": True,
                                "claims_checked": 20,
                                "billed_characters": 280,
                                "characters": len(
                                    references.BUDDY_1986_ARGENTINA
                                ),
                                "words": 41,
                                "coverage": slot_coverage(
                                    references.BUDDY_1986_ARGENTINA,
                                    facts_1986,
                                ),
                            }
                        ],
                        "dropped": [],
                    }
                ],
            }
        ]
        text = review(goals, "openai/gpt-oss-120b", "watsonx")
        assert "## 1986 (54:18, Diego Armando Maradona)" in text
        assert "### buddy_scored" in text
        assert "Written for a fan of Argentina." in text
        assert references.BUDDY_1986_ARGENTINA in text
        assert "280 characters for this recording" in text
        assert "Peter, Terry" in text
        assert "—" not in text

    def test_a_slot_with_nothing_kept_says_so(self):
        goals = [
            {
                "year": 2022,
                "match_id": MATCH_2022,
                "minute": 35,
                "second": 22,
                "player": "Ángel Fabián Di María Hernández",
                "team": "Argentina",
                "records": 13,
                "recorded_players": (),
                "players_who_touched_the_ball": (),
                "shared_name_parts": (),
                "slots": [
                    {
                        "slot": BUDDY_CONCEDED,
                        "label": STYLES[BUDDY_CONCEDED].label,
                        "narrator": "buddy",
                        "side": "France",
                        "candidates": [],
                        "dropped": [{"candidate": 1}],
                    }
                ],
            }
        ]
        text = review(goals, "m", "p")
        assert "No candidate for this slot passed." in text
        assert "none" in text


class TestTheReferencesPassTheCheckAsTheSlotTheyAreFor:
    """One more time, through the slot's own narrator and side.

    `tests/test_reference_narrations.py` checks all eight. This checks the six
    that get recorded, with the narrator and side the run will use, so the
    slot table above and the standard cannot drift apart.
    """

    @pytest.mark.parametrize(
        "match_id, slot, text",
        RECORDED,
        ids=["{}-{}".format(match_id, slot) for match_id, slot, _ in RECORDED],
    )
    def test_the_slot_passes_the_check(
        self, match_id, slot, text, facts_1986, facts_2022
    ):
        facts = facts_1986 if match_id == MATCH_1986 else facts_2022
        side = dict(slots_for(match_id, facts.moment.team))[slot]
        result = check(text, facts, narrator_for(slot), side)
        assert result.grounded, result.summary
