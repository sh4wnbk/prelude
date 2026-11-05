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
    catalyst_and_finish,
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
from app.grounding import (
    ACTION_CLAIMS,
    NOT_A_NAME,
    REACTION_WORDS,
    TEAM_DEMONYMS,
    is_a_reaction,
    check,
    sentences,
)
from app.narration_grammar import WORD, Reader, fold
from app.narration_prompt import HERO_TARGET_CHARACTERS, facts_from_buildup
from app.personas import THE_BUDDY, THE_CALLER, THE_STORYTELLER
from app.recorded_names import recorded_nicknames
from app.statsbomb_event_feed import StatsBombEventFeed
from app.narration_config import ACTIVE_CANDIDATE
from app.narration_provider import IAM_TOKEN_URL, WatsonxProvider
from scripts.hero_candidates import HEROES
from scripts.narrator_candidates import (
    DEFAULT_PER_SLOT,
    gather,
    merged,
    billed_for_slot,
    goals_to_run,
    main,
    narrator_for,
    play_shape,
    prompt_characters,
    review,
    slot_coverage,
    slots_for,
    token_estimate,
)
from scripts.tts_hero import DEFAULT_BUDGET
import tests.test_reference_narrations as references

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "tests" / "golden"


def read_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


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
            "the assist, forward, in the box"
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


class TestWhatTheLiveRunOfTheThirtyFirstChanged:
    """Two prompt fixes, each one a thing the model got wrong three times.

    Nine of eighteen candidates were dropped on 2026-10-31. Two of the nine
    were the check and are fixed in `app/narration_grammar.py`; these two are
    the prompt.
    """

    def test_the_prompt_says_where_the_narration_starts(
        self, facts_1986, facts_2022
    ):
        """The worked example opens on a recovery and the 2022 counter does
        not, and the model opened it "we won it back through Molina" three
        times over. Molina's first record in that passage is a pass.
        """
        assert "Cuciuffo recovered the ball" in catalyst_and_finish(facts_1986)
        anchor = catalyst_and_finish(facts_2022)
        assert "Nahuel Molina passed" in anchor
        assert "recovered" not in anchor
        assert "Ángel Di María scored" in anchor

    def test_the_prompt_names_the_one_pass_that_is_the_assist(
        self, facts_1986, facts_2022
    ):
        """Rule 6 said "the pass marked the assist", and the model called
        three other passes a set-up. It now says which pass that is."""
        rule = flat(build_goal_call_prompt(facts_1986, BUDDY_SCORED))
        assert '"Set up" is for one pass and no other: Héctor Enrique to ' \
               "Diego Armando Maradona" in rule
        other = flat(build_goal_call_prompt(facts_2022, BUDDY_SCORED))
        assert '"Set up" is for one pass and no other: Alexis MacAllister ' \
               "to Ángel Di María" in other


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


class TestMergingASlotRerunIntoTheDocument:
    """A rerun of one slot keeps the other five.

    `--slot` exists so that a slot can be rerun after a check or a prompt fix
    without spending calls on five that are already good, and that is only
    worth having if the document survives it. `scripts/hero_candidates.py`
    lost a goal that way once, on 2026-10-30.
    """

    def goal(self, slots, **extra):
        one = {
            "year": 1986,
            "match_id": MATCH_1986,
            "minute": 54,
            "second": 18,
            "player": "Diego Armando Maradona",
            "team": "Argentina",
            "records": 24,
            "recorded_players": (),
            "players_who_touched_the_ball": (),
            "shared_name_parts": (),
            "generated_on": "2026-10-31",
            "slots": slots,
        }
        one.update(extra)
        return one

    def slot(self, key, texts):
        return {
            "slot": key,
            "label": STYLES[key].label,
            "narrator": "buddy" if key.startswith("buddy") else "storyteller",
            "side": "Argentina" if key == BUDDY_SCORED else None,
            "candidates": [{"candidate": n, "text": text}
                           for n, text in enumerate(texts, start=1)],
            "dropped": [],
        }

    def write(self, tmp_path, goals):
        path = tmp_path / "narrator_candidates_2026-10-31.json"
        path.write_text(
            json.dumps({"goals": goals}, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def test_a_slot_this_run_did_not_touch_is_carried_over(self, tmp_path):
        path = self.write(tmp_path, [self.goal([
            self.slot(BUDDY_SCORED, ["old scored"]),
            self.slot(STORYTELLER_NEUTRAL, ["old neutral"]),
        ])])
        fresh = [self.goal([self.slot(BUDDY_SCORED, ["new scored"])])]
        out = merged(fresh, path)
        assert len(out) == 1
        keys = [slot["slot"] for slot in out[0]["slots"]]
        assert keys == [BUDDY_SCORED, STORYTELLER_NEUTRAL]
        texts = {
            slot["slot"]: slot["candidates"][0]["text"]
            for slot in out[0]["slots"]
        }
        assert texts[BUDDY_SCORED] == "new scored"
        assert texts[STORYTELLER_NEUTRAL] == "old neutral"

    def test_a_goal_this_run_did_not_touch_is_carried_over_whole(
        self, tmp_path
    ):
        older = self.goal([self.slot(BUDDY_SCORED, ["old"])])
        other = dict(older, match_id=MATCH_2022, year=2022)
        path = self.write(tmp_path, [older, other])
        out = merged(
            [self.goal([self.slot(BUDDY_SCORED, ["new"])])], path
        )
        assert [goal["match_id"] for goal in out] == [MATCH_1986, MATCH_2022]
        assert out[1]["slots"][0]["candidates"][0]["text"] == "old"

    def test_with_no_earlier_document_the_run_stands_alone(self, tmp_path):
        fresh = [self.goal([self.slot(BUDDY_SCORED, ["new"])])]
        assert merged(fresh, tmp_path / "absent.json") == fresh


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
        text = review(goals, "openai/gpt-oss-120b", "watsonx", "high", 2000)
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
        text = review(goals, "m", "p", "high", 2000)
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


def last_sentence(text):
    return sentences(text)[-1]


def reads_as_a_reaction(text, facts):
    """Whether the check would read this sentence as a reaction.

    The reader is given real facts because that is what `is_a_reaction`
    takes. None of the four reactions names anybody, which is the point of
    them, so which passage it is read against makes no difference.
    """
    one = Reader(
        facts=facts,
        not_a_name=NOT_A_NAME,
        demonyms=TEAM_DEMONYMS,
        actions=ACTION_CLAIMS,
    )
    sentence = last_sentence(text)
    return is_a_reaction(sentence.text, one.read(sentence.text))


class TestEachWorkedExampleCarriesAReaction:
    """The two layers, shown rather than only described.

    The example is the one thing in the prompt a model copies the shape of,
    so a layer the examples do not have is a layer the candidates will not
    have either.
    """

    @pytest.mark.parametrize("key", sorted(STYLES))
    def test_the_example_ends_on_a_reaction(self, key, facts_2022):
        assert reads_as_a_reaction(STYLES[key].example, facts_2022), key

    @pytest.mark.parametrize("key", sorted(STYLES))
    def test_the_reaction_is_within_the_word_count(self, key, facts_2022):
        said = last_sentence(STYLES[key].example).text
        assert len(WORD.findall(said)) <= REACTION_WORDS, (key, said)

    def test_the_two_voices_that_cheer_cheer_in_the_reaction_too(self):
        for key in (BUDDY_SCORED, CALLER_NEUTRAL):
            assert STYLES[key].example.endswith("!")

    def test_the_two_voices_that_do_not_are_restrained(self):
        """The Storyteller notices the goal and the conceding Buddy is
        subdued, which is the cheer rule each of them already had."""
        for key in (STORYTELLER_NEUTRAL, BUDDY_CONCEDED):
            assert STYLES[key].example.endswith(".")
            assert "!" not in STYLES[key].example

    @pytest.mark.parametrize("key", sorted(STYLES))
    def test_every_style_says_how_its_reaction_ends(self, key):
        assert "reaction" in STYLES[key].style

    @pytest.mark.parametrize("key", sorted(STYLES))
    def test_every_prompt_states_both_layers(self, key, facts_1986):
        prompt = flat(build_goal_call_prompt(facts_1986, key))
        assert "THE PLAY" in prompt
        assert "THE REACTION" in prompt
        assert "at most eight words" in prompt.lower()
        assert "it is the last thing you write" in prompt


class TestTheRecordsSayWhichWayAndHowFar:
    """Rule 5 asks for a claim the model has to be able to read off the page.

    A coordinate is not something a model can be asked to compare, so the
    records say "forward" and "a run" in the words the narration would use,
    computed by `app/narration_grammar.py` from the two ends of the record.
    """

    def test_a_pass_up_the_pitch_is_marked_forward(self, facts_2022):
        """Álvarez's ball to MacAllister, 36.1 yards of x."""
        line = record_line(facts_2022, facts_2022.facts[8].beat)
        assert "a long ball, forward" in line

    def test_a_touch_on_the_spot_is_marked_as_no_run(self, facts_2022):
        """Álvarez's carry, 0.7 yards, which four candidates called a drive
        forward on 2026-10-31."""
        line = record_line(facts_2022, facts_2022.facts[7].beat)
        assert "a touch on the spot, not a run" in line
        assert "forward" not in line

    def test_a_long_carry_is_marked_a_run(self, facts_1986):
        """Maradona's 34.9 yard carry."""
        line = record_line(facts_1986, facts_1986.facts[11].beat)
        assert "a run, far enough to be called one" in line
        assert "forward" in line

    def test_a_defenders_record_says_neither(self, facts_1986):
        """StatsBomb mirrors a defensive record's coordinates, so "forward"
        on one would mean the half the words do not say."""
        for fact in facts_1986.facts:
            if fact.beat.team == facts_1986.moment.team:
                continue
            line = record_line(facts_1986, fact.beat)
            assert "forward" not in line
            assert "back" not in line
            assert "run" not in line


class TestAskingForDifferentTellings:
    """Rule 13, and the one mechanism that can make it bite.

    Three independent calls at temperature 0.8 wrote three near copies for
    each slot on 2026-10-31. A model writing one candidate per call cannot
    know what the others said unless the prompt tells it.
    """

    @pytest.mark.parametrize("key", sorted(STYLES))
    def test_every_prompt_asks_for_a_different_structure(
        self, key, facts_2022
    ):
        prompt = flat(build_goal_call_prompt(facts_2022, key))
        assert "differ in structure" in prompt.lower()
        assert "not one telling with the words swapped" in prompt

    def test_the_first_candidate_has_nothing_to_avoid(self, facts_2022):
        prompt = build_goal_call_prompt(facts_2022, BUDDY_SCORED)
        assert "ALREADY WRITTEN FOR THIS SLOT" not in prompt

    def test_what_was_kept_is_shown_back(self, facts_2022):
        earlier = [
            "We went on the counter, Molina to MacAllister, and he scored!",
            "Molina to MacAllister and on it went, and we scored!",
        ]
        prompt = flat(
            build_goal_call_prompt(facts_2022, BUDDY_SCORED, avoid=earlier)
        )
        assert "ALREADY WRITTEN FOR THIS SLOT" in prompt
        for one in earlier:
            assert one in prompt

    def test_what_is_shown_back_is_never_a_reference(
        self, facts_1986, facts_2022
    ):
        """`avoid` is the model's own earlier answers. The eight references
        are the standard and go into no prompt for the goal they describe,
        which `TestTheExampleIsInvented` holds for the rest of the prompt."""
        for facts in (facts_1986, facts_2022):
            prompt = flat(build_goal_call_prompt(facts, BUDDY_SCORED))
            for name, text in vars(references).items():
                if not name.isupper() or not isinstance(text, str):
                    continue
                if len(text) < 60:
                    continue
                assert text[:25] not in prompt, name


class TestTheReasoningEffortIsThisRunsChoice:
    """How much the model thinks is a setting of the run, not of the module.

    `app/narration_config.py` ships `low` on the active candidate, which is
    what the pipeline a fan waits on uses: at its default effort
    `openai/gpt-oss-120b` spent most of its budget reasoning before writing
    anything. A candidate run is not a fan waiting, so Task 9d asked for
    `high`, and the run that chose it is what records it.
    """

    def test_the_default_is_still_what_the_active_candidate_ships(self, capsys):
        main(["--plan"])
        printed = capsys.readouterr().out
        assert "effort    {} (this run; app/narration_config.py ships {})".format(
            ACTIVE_CANDIDATE.reasoning_effort, ACTIVE_CANDIDATE.reasoning_effort
        ) in printed

    def test_the_plan_prints_the_effort_it_would_send(self, capsys):
        main(["--plan", "--reasoning-effort", "high"])
        printed = capsys.readouterr().out
        assert "effort    high (this run" in printed
        assert "ships low" in printed

    def test_an_effort_the_service_has_no_name_for_is_refused(self):
        with pytest.raises(SystemExit):
            main(["--plan", "--reasoning-effort", "maximum"])

    def test_the_review_file_records_what_the_run_used(self):
        """Not what the module ships: the two differ on a run like this one,
        and the file is the provenance of the words in it."""
        goals = [
            {
                "year": 2022,
                "match_id": 3869685,
                "minute": 35,
                "second": 22,
                "player": "Ángel Di María",
                "records": 13,
                "players_who_touched_the_ball": ("Ángel Di María",),
                "shared_name_parts": (),
                "slots": [],
            }
        ]
        text = review(goals, "m", "p", "high", 2000)
        assert "reasoning effort high for this run" in text
        assert "2000 max new tokens" in text


class TestWhatTheRunIsExpectedToSpend:
    """The call count and the tokens, printed before anything is sent.

    Two figures and only one of them is a prediction, because they are far
    apart: a run where every candidate is grounded first time sends a third of
    the calls of one where every candidate fails until its last attempt.
    """

    def test_the_prompt_grows_with_what_is_already_kept(self, facts_2022):
        sizes = prompt_characters(facts_2022, BUDDY_SCORED, 3)
        assert len(sizes) == 3
        assert sizes[0] < sizes[1] < sizes[2]

    def test_the_first_prompt_of_a_slot_carries_no_avoid_block(
        self, facts_2022
    ):
        assert prompt_characters(facts_2022, BUDDY_SCORED, 1) == (
            len(build_goal_call_prompt(facts_2022, BUDDY_SCORED)),
        )

    def test_the_ceiling_is_the_attempts_times_the_first_pass(self):
        characters = {(1, "a"): (4000, 4400), (2, "b"): (4000, 4400)}
        spend = token_estimate(
            [(1, "a"), (2, "b")], characters, attempts=3, max_new_tokens=2000
        )
        assert spend["calls_if_first_attempt"] == 4
        assert spend["calls_at_most"] == 12
        assert spend["input_if_first_attempt"] == 4200
        assert spend["output_if_first_attempt"] == 8000
        assert spend["if_first_attempt"] == 12200
        assert spend["at_most"] == 36600

    def test_the_plan_states_the_call_count_and_the_tokens(self, capsys):
        main(["--plan", "--reasoning-effort", "high"])
        printed = capsys.readouterr().out
        assert "calls     at most 54 generations" in printed
        assert "tokens    about" in printed
        assert "expected (18 calls" in printed
        assert "at most (54 calls" in printed
        assert "4 characters a token" in printed
        assert "nothing was sent" in printed


class TestTheRecordsSayWhatIsNotThereToo:
    """One absence is worth printing, because the example teaches it.

    The worked example opens on "won it back", which is a `Ball Recovery`.
    The 2022 counter holds none: Molina's first record in it is a pass. The
    model opened that passage with "we won it back through Molina" three
    times in the run of 2026-10-31 and twice more in the run at effort high,
    and the check refused every one of them.
    """

    def test_the_2022_passage_says_nothing_was_won_back(self, facts_2022):
        assert not any(
            fact.beat.action == "Ball Recovery" for fact in facts_2022.facts
        )
        said = flat(catalyst_and_finish(facts_2022))
        assert "nothing in it was won back" in said

    def test_the_1986_passage_does_not_say_it(self, facts_1986):
        """Cuciuffo's recovery is fact 1, so the words are true there and the
        prompt has no reason to say anything."""
        assert any(
            fact.beat.action == "Ball Recovery" for fact in facts_1986.facts
        )
        assert "won back" not in flat(catalyst_and_finish(facts_1986))

    @pytest.mark.parametrize("key", sorted(STYLES))
    def test_every_2022_prompt_carries_it(self, key, facts_2022):
        assert "nothing in it was won back" in flat(
            build_goal_call_prompt(facts_2022, key)
        )


class TestTwoTellingsOrOneWithOtherWordsInIt:
    """`play_shape` is what rule 13 is measured by.

    The run at effort high wrote two pairs that differ only in a synonym and
    in the reaction they end on, which is one telling and not two. The shape
    is the moves the play makes, by kind, so a chain written as "found Y" and
    a chain written as "played it to Y" are the same move and a sentence
    break is not.
    """

    def test_a_synonym_leaves_the_shape_alone(self, facts_2022):
        assert play_shape(
            "Molina found MacAllister, who set up Di María, who scored.",
            facts_2022,
        ) == play_shape(
            "Molina played it to MacAllister, who set up Di María, who "
            "scored.",
            facts_2022,
        )

    def test_a_sentence_break_changes_it(self, facts_2022):
        assert play_shape(
            "Molina found MacAllister, who set up Di María, who scored.",
            facts_2022,
        ) != play_shape(
            "Molina found MacAllister. He set up Di María, who scored.",
            facts_2022,
        )

    def test_a_claim_the_other_does_not_make_changes_it(self, facts_2022):
        assert play_shape(
            "Molina found MacAllister, who set up Di María, who scored.",
            facts_2022,
        ) != play_shape(
            "Molina found MacAllister, who set up Di María in the box, who "
            "scored.",
            facts_2022,
        )

    def test_the_reaction_is_not_part_of_the_shape(self, facts_2022):
        """A slot whose candidates differ only in ending on "What a finish!"
        or "What a strike!" holds one telling."""
        play = "Molina found MacAllister, who set up Di María, who scored"
        assert play_shape(
            play + "! What a finish!", facts_2022
        ) == play_shape(play + "! Oh, lovely!", facts_2022)
        assert play_shape(play + "!", facts_2022) == play_shape(
            play + "! What a strike!", facts_2022
        )

    @pytest.mark.parametrize(
        "goal, names",
        [
            (
                "1986",
                [
                    "STORYTELLER_1986",
                    "BUDDY_1986_ARGENTINA",
                    "BUDDY_1986_ENGLAND",
                    "CALLER_1986",
                ],
            ),
            (
                "2022",
                [
                    "STORYTELLER_2022",
                    "BUDDY_2022_ARGENTINA",
                    "BUDDY_2022_FRANCE",
                    "CALLER_2022",
                ],
            ),
        ],
    )
    def test_the_four_references_for_a_goal_are_four_tellings(
        self, goal, names, facts_1986, facts_2022
    ):
        """So the measure is not over-eager: Shawn's four narrations of one
        goal are four shapes, not one shape four times."""
        facts = facts_1986 if goal == "1986" else facts_2022
        shapes = {
            play_shape(getattr(references, name), facts) for name in names
        }
        assert len(shapes) == len(names)


class TestTheRunIsCappedInTokens:
    """`--max-total-tokens`, which has no default on purpose.

    Task 9d printed an estimate before it sent anything, ran at effort high
    and cost about 817,000 tokens. The plan is still printed; what is new is
    that the run stops at a number rather than reporting one afterwards.
    """

    def test_confirm_refuses_to_start_without_a_cap(self):
        with pytest.raises(SystemExit) as raised:
            main(["--confirm"])
        said = str(raised.value)
        assert "--max-total-tokens" in said
        assert "no default" in said
        assert "817,000" in said

    def test_a_cap_of_nothing_is_refused(self):
        with pytest.raises(SystemExit) as raised:
            main(["--plan", "--max-total-tokens", "0"])
        assert "count of tokens" in str(raised.value)

    def test_the_plan_prints_the_cap_it_was_given(self, capsys):
        assert main(["--plan", "--max-total-tokens", "80000"]) == 0
        printed = capsys.readouterr().out
        assert "80,000 tokens for the whole run" in printed
        assert "stops before a call that could pass it" in printed

    def test_the_plan_says_when_no_cap_was_given(self, capsys):
        assert main(["--plan"]) == 0
        assert "--confirm refuses to start without one" in (
            capsys.readouterr().out
        )

    def test_the_review_file_states_the_cap_and_a_run_cut_short(self):
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
                "slots": [],
            }
        ]
        text = review(
            goals,
            "m",
            "p",
            "low",
            2000,
            token_cap=80_000,
            stopped="watsonx has billed this run 79,000 tokens",
        )
        assert "allowed 80,000 tokens in all" in text
        assert "stopped on its token cap" in text
        assert "79,000" in text
        assert "—" not in text

    def test_the_review_file_says_nothing_about_a_run_that_was_not_cut(self):
        text = review([], "m", "p", "low", 2000, token_cap=80_000)
        assert "allowed 80,000 tokens in all" in text
        assert "stopped on its token cap" not in text


class TestTheCapStopsTheRunAndKeepsWhatWasWritten:
    """The cap driven through `gather`, against a recorded response.

    The answer replayed here is one of the reference narrations, so it passes
    the grounding check and the run really does keep a candidate before the
    cap stops it. Nothing opens a connection: `tests/conftest.py` would fail
    the test if it did.
    """

    def backend(self, billed, **kwargs):
        golden = read_json(GOLDEN / "watsonx_text_generation.json")
        body = {
            "usage": {
                "prompt_tokens": billed - 200,
                "completion_tokens": 200,
                "total_tokens": billed,
            },
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": references.BUDDY_2022_ARGENTINA,
                    },
                }
            ],
        }
        urls = {
            IAM_TOKEN_URL: golden["iam"]["response"],
            WatsonxProvider(env=golden["env"], chat=True).url: body,
        }

        def transport(url, sent, headers):
            return urls[url]

        return WatsonxProvider(
            env=golden["env"],
            chat=True,
            transport=transport,
            max_new_tokens=2000,
            **kwargs,
        )

    def test_the_run_stops_mid_slot_and_the_first_candidate_survives(self):
        hero = next(one for one in HEROES if one[1] == MATCH_2022)
        # 6,000 billed for the first answer, a prompt of about 1,700 tokens
        # and a 2,000 length cap: the second call's worst case passes 9,000.
        backend = self.backend(6_000, token_cap=9_000)
        goals, stopped = gather(
            backend, 3, heroes=(hero,), only=[BUDDY_SCORED]
        )
        assert stopped
        assert "9,000" in stopped
        assert backend.total_tokens == 6_000
        assert len(goals) == 1
        assert [slot["slot"] for slot in goals[0]["slots"]] == [BUDDY_SCORED]
        kept = goals[0]["slots"][0]["candidates"]
        assert len(kept) == 1
        assert kept[0]["text"] == references.BUDDY_2022_ARGENTINA
        # The cap is not a failed candidate: nothing was sent, so there is
        # nothing to record as refused.
        assert goals[0]["slots"][0]["dropped"] == []

    def test_a_cap_with_room_lets_the_slot_finish(self):
        """The same recorded answer three times, so candidates two and three
        are dropped as near copies rather than as a cap."""
        hero = next(one for one in HEROES if one[1] == MATCH_2022)
        backend = self.backend(6_000, token_cap=400_000)
        goals, stopped = gather(
            backend, 3, heroes=(hero,), only=[BUDDY_SCORED]
        )
        assert stopped is None
        assert backend.total_tokens == 18_000
        slot = goals[0]["slots"][0]
        assert len(slot["candidates"]) == 1
        assert [one.get("near_copy_of") for one in slot["dropped"]] == [1, 1]
