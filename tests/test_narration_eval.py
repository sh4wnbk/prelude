"""Tests for the measuring code in `scripts/narration_eval.py`.

No model is called and no connection is opened: every test here reads the
event data off disk, builds the facts, and measures narration written in the
test. `tests/conftest.py` fails the suite if anything reaches the network.

`key_beats` is `app/narration_prompt.py`'s, not this script's: the fallback
narration is built to reach every key beat and the evaluation measures what
share of them a narration reached, so the two read one list. The measuring
code here is `coverage`, `Recorder` and the goal selection.

**The test that matters most is the thin narration.** A live run on the 1986
54:18 goal came back with four true sentences that take the first three facts
in order and then jump to the shot. It passes `app/grounding.py`, because
every word of it is grounded, and it skips all four dribbles, which is the
whole reason the goal is remembered. If coverage does not score that narration
low, coverage is measuring nothing and the report built on it is worthless. So
it is pinned here, with its real citations, rather than left to a live run to
notice.

The fact numbers in this file are read out of `data/raw/` and written down as
literals, the way `tests/test_grounding.py` does it, so a test says what it
expects rather than deriving it from the thing under test.
"""

import json
from pathlib import Path

import pytest

from app.narration_prompt import (
    DRIBBLE,
    FOUL,
    SHOT,
    facts_from_buildup,
    key_beats,
    template_narration,
)
from app.statsbomb_event_feed import StatsBombEventFeed
from app.personas import MATE, THE_CALLER, THE_MATE
from scripts.narration_eval import (
    MODEL,
    NO_PERSONA,
    TEMPLATE,
    Record,
    Recorder,
    Voice,
    call_tokens,
    coverage,
    is_generation,
    goal_moments,
    match_sides,
    model_coverage,
    pass_rate,
    per_call,
    persona_section,
    read_json,
    read_personas,
    sentence_length,
    surname,
    voices,
    watsonx_section,
)

MATCH_1986 = 3750191
MATCH_2022 = 3869685

#: The goals these tests use, by clock.
MARADONA_RUN = (54, 18)       # four dribbles past, open play
MARADONA_FIRST = (50, 27)     # one dribble past, open play
LINEKER = (80, 37)            # a header, nothing but the shot
MESSI_PENALTY = (22, 24)      # a penalty, one dribble past, Foul Won and Committed
DI_MARIA = (35, 22)           # open play, nothing but the shot
MBAPPE_PENALTY_79 = (79, 24)  # a penalty, Foul Won and Foul Committed
MBAPPE_PENALTY_117 = (117, 5)  # a penalty recorded only as a Foul Committed

#: The 54:18 facts, read from the data. The four defenders who were dribbled
#: past, each with the `Dribble` on Maradona's record at the same clock.
DRIBBLE_BEATS_54_18 = ((10, 11), (14, 15), (17, 18), (21, 22))
SHOT_54_18 = 24

#: A live first attempt from `granite4:micro`, quoted exactly, citations and
#: all. It is grounded and it misses every dribble.
THIN = (
    "[1] Jose Luis Cuciuffo recovered the ball.\n"
    "[2] Jose Luis Cuciuffo carried the ball.\n"
    "[3] Jose Luis Cuciuffo passed.\n"
    "[24] Diego Armando Maradona shot."
)

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = Path(__file__).resolve().parent / "golden" / "ollama_development_model.json"


@pytest.fixture(scope="module")
def feed():
    return StatsBombEventFeed()


def facts_for(feed, match_id, clock):
    """The facts for one goal, found by its clock."""
    found = [
        moment
        for moment in feed.defining_moments(match_id)
        if (moment.minute, moment.second) == clock
    ]
    assert len(found) == 1, f"{len(found)} moments at {clock} in {match_id}"
    return facts_from_buildup(feed.buildup(match_id, found[0]))


class TestKeyBeats:
    """What a narration of a goal is expected to reach."""

    def test_the_1986_run_is_the_shot_and_four_dribbles(self, feed):
        beats = key_beats(facts_for(feed, MATCH_1986, MARADONA_RUN))
        assert len(beats) == 5
        assert [beat.kind for beat in beats] == [DRIBBLE] * 4 + [SHOT]
        assert beats[-1].numbers == (SHOT_54_18,)

    def test_a_dribble_beat_holds_both_sides_of_the_record(self, feed):
        """One beat of play, two records: the dribble and the player beaten.

        Citing either one says the beat happened, so both numbers are in it.
        """
        beats = key_beats(facts_for(feed, MATCH_1986, MARADONA_RUN))
        dribbles = tuple(b.numbers for b in beats if b.kind == DRIBBLE)
        assert dribbles == DRIBBLE_BEATS_54_18

    def test_a_dribble_beat_is_named_after_the_player_who_was_beaten(self, feed):
        beats = key_beats(facts_for(feed, MATCH_1986, MARADONA_RUN))
        assert beats[0].label == "dribbled past Peter Beardsley"

    def test_a_goal_with_no_dribbles_or_fouls_has_only_the_shot(self, feed):
        for clock in (LINEKER, DI_MARIA):
            beats = key_beats(facts_for(feed, MATCH_1986 if clock == LINEKER
                                        else MATCH_2022, clock))
            assert [beat.kind for beat in beats] == [SHOT]

    def test_a_penalty_adds_the_foul_that_won_it(self, feed):
        beats = key_beats(facts_for(feed, MATCH_2022, MBAPPE_PENALTY_79))
        assert [beat.kind for beat in beats] == [FOUL, SHOT]
        assert beats[0].label == "the foul that won the penalty"

    def test_a_penalty_with_only_a_foul_committed_still_has_the_foul(self, feed):
        """The 117:05 penalty has no `Foul Won` record, only the other side.

        Keying the beat on `Foul Won` alone would have left that penalty with
        the shot as its only key beat and said nothing was missing.
        """
        facts = facts_for(feed, MATCH_2022, MBAPPE_PENALTY_117)
        actions = {fact.beat.action for fact in facts.facts}
        assert "Foul Won" not in actions and "Foul Committed" in actions

        beats = key_beats(facts)
        assert [beat.kind for beat in beats] == [FOUL, SHOT]

    def test_only_a_penalty_gets_a_foul_beat(self, feed):
        """A foul in open play is not a key beat, because the task said so.

        Checked across all nine goals rather than argued: every foul beat
        belongs to a goal whose shot is recorded as a penalty.
        """
        for match_id in (MATCH_1986, MATCH_2022):
            for moment in feed.defining_moments(match_id):
                facts = facts_from_buildup(feed.buildup(match_id, moment))
                fouls = [b for b in key_beats(facts) if b.kind == FOUL]
                assert bool(fouls) == (facts.set_piece == "Penalty")

    def test_every_goal_has_exactly_one_shot_beat(self, feed):
        for match_id in (MATCH_1986, MATCH_2022):
            for moment in feed.defining_moments(match_id):
                facts = facts_from_buildup(feed.buildup(match_id, moment))
                shots = [b for b in key_beats(facts) if b.kind == SHOT]
                assert len(shots) == 1
                assert shots[0].numbers == (facts.goal_fact.number,)

    def test_the_beats_are_in_the_order_they_happened(self, feed):
        beats = key_beats(facts_for(feed, MATCH_2022, MESSI_PENALTY))
        starts = [min(beat.numbers) for beat in beats]
        assert starts == sorted(starts)
        assert [beat.kind for beat in beats] == [DRIBBLE, FOUL, SHOT]


class TestCoverage:
    """How much of the passage a narration reached."""

    def test_the_thin_narration_covers_only_the_shot(self, feed):
        """The run this metric exists for.

        Four true sentences, grounded, and every dribble missing. One beat of
        five is 20%, and anything near the top of the scale here would mean
        coverage is not measuring what it claims to.
        """
        facts = facts_for(feed, MATCH_1986, MARADONA_RUN)
        reached = coverage(THIN, facts)

        assert reached.beats == 5
        assert len(reached.covered) == 1
        assert reached.covered[0].kind == SHOT
        assert reached.share == pytest.approx(0.2)
        assert [beat.label for beat in reached.missed] == [
            "dribbled past Peter Beardsley",
            "dribbled past Terry Butcher",
            "dribbled past Terry Fenwick",
            "dribbled past Peter Shilton",
        ]

    def test_the_thin_narration_is_grounded_all_the_same(self, feed):
        """Coverage is a second question, not a stricter grounding check.

        If the check refused this narration there would be nothing for
        coverage to add. It passes, which is the point.
        """
        from app.grounding import check

        facts = facts_for(feed, MATCH_1986, MARADONA_RUN)
        assert check(THIN, facts).grounded

    def test_a_narration_that_names_every_dribble_covers_everything(self, feed):
        facts = facts_for(feed, MATCH_1986, MARADONA_RUN)
        full = (
            "[10] Peter Beardsley was dribbled past.\n"
            "[14] Terry Butcher was dribbled past.\n"
            "[17] Terry Fenwick was dribbled past.\n"
            "[21] Peter Shilton was dribbled past.\n"
            "[24] Diego Armando Maradona shot."
        )
        reached = coverage(full, facts)
        assert reached.missed == ()
        assert reached.share == 1.0

    def test_citing_either_side_of_a_dribble_covers_it(self, feed):
        """The `Dribble` and the `Dribbled Past` are one beat of play."""
        facts = facts_for(feed, MATCH_1986, MARADONA_RUN)
        beaten = coverage("[10] Peter Beardsley was dribbled past.", facts)
        dribbled = coverage("[11] Diego Armando Maradona dribbled.", facts)
        assert len(beaten.covered) == len(dribbled.covered) == 1
        assert beaten.covered[0].numbers == dribbled.covered[0].numbers

    def test_a_dribble_that_went_past_nobody_is_not_a_beat(self, feed):
        """Every `Dribble` here has a `Dribbled Past` beside it.

        The rule is that the beat comes from the `Dribbled Past` record, so a
        lone `Dribble` would not create one. This records what the data holds,
        so a later data set that breaks the assumption shows up here.
        """
        facts = facts_for(feed, MATCH_1986, MARADONA_RUN)
        dribbles = [f for f in facts.facts if f.beat.action == "Dribble"]
        beaten = [f for f in facts.facts if f.beat.action == "Dribbled Past"]
        assert len(dribbles) == len(beaten) == 4
        assert len([b for b in key_beats(facts) if b.kind == DRIBBLE]) == 4

    def test_a_narration_citing_nothing_covers_nothing(self, feed):
        facts = facts_for(feed, MATCH_1986, MARADONA_RUN)
        reached = coverage("He turned away and went again.", facts)
        assert reached.covered == ()
        assert reached.share == 0.0

    def test_the_fallback_scores_full_coverage_on_every_goal(self, feed):
        """The fallback is complete as well as grounded, on all nine goals.

        It used to score 2 of 5 on the 54:18 goal: grounded in every word and
        missing three of the four dribbles, because it collapsed the run and
        then trimmed it to a sentence budget. Code assembling a narration out
        of the facts can see every beat, so there was no reason for it to drop
        one. This is the end-to-end form of
        `tests/test_narration_prompt.py::TestTemplateNarration::test_it_cites_every_key_beat_of_the_passage`:
        the fallback and the measure have to agree, and a template row in
        `docs/narration_eval.md` below 100% means one of them has drifted.
        """
        for match_id in (MATCH_1986, MATCH_2022):
            for moment in feed.defining_moments(match_id):
                facts = facts_from_buildup(feed.buildup(match_id, moment))
                reached = coverage(template_narration(facts), facts)
                assert reached.missed == (), (
                    f"{match_id} {moment.minute}:{moment.second:02d} "
                    f"misses {[b.label for b in reached.missed]}"
                )
                assert reached.share == 1.0

    def test_coverage_of_a_single_beat_goal_is_all_or_nothing(self, feed):
        """Five of the nine goals have one key beat, so the number is thin.

        Recorded as a test because the report has to say so: a goal whose only
        key beat is the shot reads 100% for any narration the ending rule
        would let through, and that is not evidence about the model.
        """
        facts = facts_for(feed, MATCH_2022, DI_MARIA)
        goal = facts.goal_fact.number
        assert coverage(f"[{goal}] Di Maria shot.", facts).share == 1.0
        assert coverage("[1] Someone passed.", facts).share == 0.0


class TestRecorder:
    """Tokens come from the server's counters, not from counting words."""

    def test_it_reads_ollamas_own_counters(self):
        golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
        response = golden["response"]
        recorder = Recorder(inner=lambda url, body, headers: response)

        recorder("http://127.0.0.1:11434/api/generate", b"{}", {})

        assert len(recorder.calls) == 1
        call = recorder.calls[0]
        assert call.prompt_tokens == response["prompt_eval_count"]
        assert call.completion_tokens == response["eval_count"]
        assert call.seconds >= 0.0

    def test_a_response_without_counters_reports_zero(self):
        recorder = Recorder(inner=lambda url, body, headers: {"response": "hi"})
        recorder("http://127.0.0.1:11434/api/generate", b"{}", {})
        assert recorder.calls[0].prompt_tokens == 0
        assert recorder.calls[0].completion_tokens == 0

    def test_take_hands_over_the_calls_and_starts_again(self):
        recorder = Recorder(inner=lambda url, body, headers: {"eval_count": 7})
        recorder("u", b"", {})
        recorder("u", b"", {})
        assert len(recorder.take()) == 2
        assert recorder.take() == ()

    def test_it_passes_the_response_through_unchanged(self):
        answer = {"response": "text", "eval_count": 3}
        recorder = Recorder(inner=lambda url, body, headers: answer)
        assert recorder("u", b"", {}) is answer


class TestGoalSelection:
    """`--goals`, so a run can be one goal rather than all nine."""

    def test_no_argument_is_every_goal_in_both_matches(self, feed):
        chosen = goal_moments(feed, None)
        assert len(chosen) == 9
        assert {match_id for match_id, _ in chosen} == {MATCH_1986, MATCH_2022}

    def test_a_match_id_is_every_goal_in_that_match(self, feed):
        chosen = goal_moments(feed, str(MATCH_1986))
        assert len(chosen) == 3
        assert all(match_id == MATCH_1986 for match_id, _ in chosen)

    def test_a_match_and_clock_is_one_goal(self, feed):
        chosen = goal_moments(feed, f"{MATCH_1986}:54:18")
        assert len(chosen) == 1
        match_id, moment = chosen[0]
        assert (match_id, moment.minute, moment.second) == (MATCH_1986, 54, 18)

    def test_several_goals_are_comma_separated(self, feed):
        chosen = goal_moments(feed, f"{MATCH_1986}:54:18, {MATCH_2022}:22:24")
        assert [(m, o.minute) for m, o in chosen] == [
            (MATCH_1986, 54),
            (MATCH_2022, 22),
        ]

    def test_a_clock_with_no_goal_is_refused(self, feed):
        with pytest.raises(SystemExit):
            goal_moments(feed, f"{MATCH_1986}:12:34")

    def test_something_that_is_not_a_goal_reference_is_refused(self, feed):
        with pytest.raises(SystemExit):
            goal_moments(feed, "54:18")


class TestReportHelpers:
    def test_a_surname_is_the_last_word_of_a_recorded_name(self):
        assert surname("Diego Armando Maradona") == "Maradona"
        assert surname("Lionel Andrés Messi Cuccittini") == "Cuccittini"


def a_record(**fields) -> Record:
    """One measured narration, with the fields a test does not care about
    filled in. The report code reads a lot of them and a test naming all
    eighteen would say less, not more."""
    base = dict(
        match_id=MATCH_1986,
        minute=54,
        second=18,
        team="Argentina",
        player="Diego Armando Maradona",
        set_piece="Open Play",
        run=1,
        first_attempt_grounded=True,
        attempts=1,
        source=MODEL,
        covered=5,
        beats=5,
        missed=(),
        prompt_tokens=100,
        completion_tokens=10,
        seconds=1.0,
        text="[24] Maradona shot and scored for Argentina.",
        tagged_text="[24] Maradona shot and scored for Argentina.",
    )
    return Record(**{**base, **fields})


class TestTheVoices:
    """Task 6c: a persona is a voice, and the Mate is two of them."""

    def test_the_two_sides_are_read_off_the_records(self, feed):
        assert match_sides(feed, MATCH_1986) == ("Argentina", "England")
        assert match_sides(feed, MATCH_2022) == ("Argentina", "France")

    def test_a_fans_only_persona_is_one_voice_per_side(self, feed):
        built = voices(feed, MATCH_1986, [MATE])
        assert [v.side for v in built] == ["Argentina", "England"]
        assert {v.persona for v in built} == {THE_MATE}

    def test_a_persona_with_no_side_is_one_voice(self, feed):
        built = voices(feed, MATCH_1986, [THE_CALLER.id])
        assert len(built) == 1
        assert built[0].side is None

    def test_all_is_every_persona(self):
        assert read_personas("all") == ("caller", "storyteller", "mate")

    def test_none_is_the_prompt_with_no_style_block(self, feed):
        assert read_personas(NO_PERSONA) == ()
        assert read_personas("") == ()

    def test_an_unknown_persona_is_refused(self):
        with pytest.raises(KeyError):
            read_personas("commentator")

    def test_a_voice_is_labelled_by_its_persona_and_side(self, feed):
        assert Voice(persona=THE_CALLER, side=None).label == "caller"
        assert Voice(persona=THE_MATE, side="England").label == "mate (England)"
        assert Voice(persona=None, side=None).label == NO_PERSONA

    def test_four_voices_over_a_match(self, feed):
        built = voices(feed, MATCH_2022, read_personas("all"))
        assert [v.label for v in built] == [
            "caller",
            "storyteller",
            "mate (Argentina)",
            "mate (France)",
        ]


class TestARecordCarriesItsVoice:
    """And a records file written before personas existed still reads."""

    def test_a_record_defaults_to_no_persona(self):
        assert a_record().persona == NO_PERSONA
        assert a_record().voice == NO_PERSONA

    def test_a_partisan_record_names_its_side(self):
        record = a_record(persona=MATE, side="England")
        assert record.voice == "mate (England)"

    def test_the_task_4a_records_still_read(self):
        """`--from-json` rebuilds the committed report from them."""
        path = ROOT / "docs" / "narration_runs" / "4a_granite4_micro.json"
        rows = read_json(path)
        assert len(rows) == 27
        assert {r.persona for r in rows} == {NO_PERSONA}


class TestOnlyTheModelCanPass:
    """A template fallback is a failure, however complete it is."""

    def test_a_model_narration_is_a_pass(self):
        assert a_record(source=MODEL).model_wrote_it

    def test_a_template_fallback_is_not(self):
        assert not a_record(source=TEMPLATE, first_attempt_grounded=False).model_wrote_it

    def test_the_section_counts_a_fallback_as_a_failure(self):
        """Three runs of one voice: one first attempt, one retry, one
        fallback. The first-attempt rate is 1/3 and the after-retry rate is
        2/3, because the fallback is neither."""
        rows = [
            a_record(persona="caller", run=1),
            a_record(persona="caller", run=2, first_attempt_grounded=False,
                     attempts=2),
            a_record(persona="caller", run=3, first_attempt_grounded=False,
                     attempts=3, source=TEMPLATE),
        ]
        section = "\n".join(persona_section(rows))
        assert "| caller | 3 | 1/3 | 2/3 | 1 |" in section

    def test_coverage_leaves_the_fallback_out(self):
        """A fallback cites every key beat by construction, so averaging it
        in would report the fallback's completeness as the persona's."""
        rows = [
            a_record(persona="caller", covered=1, beats=5),
            a_record(persona="caller", run=2, source=TEMPLATE, covered=5,
                     beats=5, first_attempt_grounded=False),
        ]
        section = "\n".join(persona_section(rows))
        assert "| caller | 2 | 1/2 | 1/2 | 1 | 20% |" in section


class TestThePersonaSection:
    def test_it_is_empty_when_no_record_carries_a_persona(self):
        assert persona_section([a_record()]) == []

    def test_it_names_every_voice_that_ran(self):
        rows = [
            a_record(persona="caller"),
            a_record(persona="storyteller"),
            a_record(persona=MATE, side="Argentina"),
            a_record(persona=MATE, side="England"),
        ]
        section = "\n".join(persona_section(rows))
        for voice in ("caller", "storyteller", "mate (Argentina)",
                      "mate (England)"):
            assert f"| {voice} |" in section

    def test_it_counts_the_partisan_narrations_that_said_we(self):
        rows = [
            a_record(persona=MATE, side="Argentina",
                     text="[24] We scored through Maradona."),
            a_record(persona=MATE, side="Argentina", run=2,
                     text="[24] Maradona shot and scored for Argentina."),
        ]
        section = "\n".join(persona_section(rows))
        assert "2 narrations" in section
        assert "**1** used" in section


class TestSentenceLength:
    """The crudest measure of a register, and the only one without a judgement."""

    def test_it_averages_words_per_sentence(self):
        row = a_record(
            tagged_text="[1] He passed.\n[24] Maradona shot and scored for Argentina."
        )
        # Two sentences, two and six words.
        assert sentence_length([row]) == "4.0"

    def test_a_template_fallback_is_left_out(self):
        """The fallback writes one fact a sentence in every voice, so folding
        it in would report its shape as the persona's."""
        model = a_record(tagged_text="[1] He passed.")
        template = a_record(
            source=TEMPLATE,
            first_attempt_grounded=False,
            tagged_text="[1] A much longer sentence than the other one here.",
        )
        assert sentence_length([model, template]) == sentence_length([model])

    def test_no_model_narration_reads_n_a(self):
        template = a_record(source=TEMPLATE, first_attempt_grounded=False)
        assert sentence_length([template]) == "n/a"


class TestTheRecorderReadsEveryApi:
    """Task 4b: three APIs count the same thing under different names."""

    def test_ollamas_own_counters(self):
        assert call_tokens({"prompt_eval_count": 1883, "eval_count": 59}) == (
            1883,
            59,
        )

    def test_watsonx_text_generation_counts_them_inside_results(self):
        answer = {
            "results": [
                {
                    "generated_text": "narration",
                    "input_token_count": 1640,
                    "generated_token_count": 74,
                }
            ]
        }
        assert call_tokens(answer) == (1640, 74)

    def test_watsonx_chat_counts_them_in_a_usage_object(self):
        answer = {
            "choices": [{"message": {"content": "narration"}}],
            "usage": {"prompt_tokens": 1640, "completion_tokens": 74},
        }
        assert call_tokens(answer) == (1640, 74)

    def test_a_response_with_no_counters_reports_zero(self):
        """An invented count would be indistinguishable in the report from
        one the server actually sent."""
        assert call_tokens({"results": [{"generated_text": "narration"}]}) == (
            0,
            0,
        )
        assert call_tokens({}) == (0, 0)

    def test_an_iam_exchange_is_not_a_generation(self):
        assert not is_generation({"access_token": "a-token", "expires_in": 3600})
        assert is_generation({"results": [{"generated_text": "x"}]})
        assert is_generation({"response": "x"})

    def test_the_recorder_skips_the_iam_exchange(self):
        """Counting it would report every watsonx narration as having tried
        twice as often as it did."""
        answers = iter(
            [
                {"access_token": "a-token", "expires_in": 3600},
                {
                    "results": [
                        {
                            "generated_text": "narration",
                            "input_token_count": 1640,
                            "generated_token_count": 74,
                        }
                    ]
                },
            ]
        )
        recorder = Recorder(inner=lambda url, body, headers: next(answers))

        recorder("https://iam.cloud.ibm.com/identity/token", b"", {})
        recorder("https://eu-gb.ml.cloud.ibm.com/ml/v1/text/generation", b"", {})

        calls = recorder.take()
        assert len(calls) == 1
        assert calls[0].prompt_tokens == 1640
        assert calls[0].completion_tokens == 74


class TestTheModelComparison:
    """Task 4b: the report section for the two paid candidates."""

    GRANITE = "ibm/granite-4-h-small"
    GPT_OSS = "openai/gpt-oss-120b"

    def _baseline(self):
        """Three narrations per model on arm b: one clean, one retried, one
        fallback for Granite; all three clean for the other."""
        rows = []
        for run, (source, first) in enumerate(
            ((MODEL, True), (MODEL, False), (TEMPLATE, False)), start=1
        ):
            rows.append(
                a_record(
                    arm="b",
                    model=self.GRANITE,
                    run=run,
                    source=source,
                    first_attempt_grounded=first,
                    calls=1 if first else 3,
                    generation_seconds=1.0 if first else 3.0,
                )
            )
        for run in range(1, 4):
            rows.append(
                a_record(
                    arm="b",
                    model=self.GPT_OSS,
                    run=run,
                    calls=1,
                    generation_seconds=2.0,
                )
            )
        return rows

    def test_a_fallback_fails_both_rates(self):
        rows = [r for r in self._baseline() if r.model == self.GRANITE]
        assert pass_rate(rows, first_only=True) == "1/3"
        assert pass_rate(rows, first_only=False) == "2/3"

    def test_a_model_that_never_falls_back_passes_everything(self):
        rows = [r for r in self._baseline() if r.model == self.GPT_OSS]
        assert pass_rate(rows, first_only=True) == "3/3"
        assert pass_rate(rows, first_only=False) == "3/3"

    def test_coverage_leaves_the_fallback_out(self):
        rows = [
            a_record(model=self.GRANITE, covered=1, beats=5),
            a_record(
                model=self.GRANITE,
                run=2,
                source=TEMPLATE,
                first_attempt_grounded=False,
                covered=5,
                beats=5,
            ),
        ]
        assert model_coverage(rows) == "20%"

    def test_per_call_divides_by_calls_not_by_narrations(self):
        """A narration that retried twice cost three calls, and a reader
        comparing two models wants the price of one answer."""
        rows = [
            a_record(
                prompt_tokens=900,
                completion_tokens=100,
                calls=1,
                generation_seconds=2.0,
            ),
            a_record(
                run=2,
                prompt_tokens=2700,
                completion_tokens=300,
                calls=3,
                generation_seconds=6.0,
            ),
        ]
        assert per_call(rows) == ("1,000", "2.0s")

    def test_per_call_with_no_calls_reads_n_a(self):
        assert per_call([a_record(calls=0)]) == ("n/a", "n/a")

    def test_the_section_names_both_models(self):
        section = "\n".join(watsonx_section(self._baseline()))
        assert f"`{self.GRANITE}`" in section
        assert f"`{self.GPT_OSS}`" in section
        assert "Task 4b" in section

    def test_the_section_is_empty_without_records(self):
        assert watsonx_section([]) == []

    def test_the_register_spread_is_reported_per_model(self):
        """A model writing the same sentence length in every voice was given
        three styles and wrote one."""
        rows = [
            a_record(
                arm="a",
                model=self.GRANITE,
                persona="caller",
                tagged_text="[1] He passed.",
            ),
            a_record(
                arm="a",
                model=self.GRANITE,
                persona="storyteller",
                tagged_text="[1] He passed the ball to a teammate nearby.",
            ),
        ]
        section = "\n".join(watsonx_section(rows))
        assert "Spread" in section
        # Two words against eight, so the spread is six.
        assert "| 2.0 | 8.0 | 6.0 |" in section

    def test_the_beats_block_arm_is_compared_against_the_block_on(self):
        rows = [
            a_record(arm="c2", model=self.GRANITE, beats_block=True),
            a_record(
                arm="c",
                model=self.GRANITE,
                beats_block=False,
                run=2,
                covered=1,
                beats=5,
            ),
        ]
        section = "\n".join(watsonx_section(rows))
        assert "What the beats block costs" in section
        assert "with the beats block" in section
        assert "without it" in section

    def test_the_mate_first_person_count_is_per_model(self):
        rows = [
            a_record(
                arm="a",
                model=self.GRANITE,
                persona="mate",
                side="Argentina",
                text="[24] We scored through Maradona.",
            ),
            a_record(
                arm="a",
                model=self.GPT_OSS,
                persona="mate",
                side="Argentina",
                text="[24] Maradona scored for Argentina.",
            ),
        ]
        section = "\n".join(watsonx_section(rows))
        assert "Mate narrations" in section
        assert f"| `{self.GRANITE}` | 1 | 1 |" in section
        assert f"| `{self.GPT_OSS}` | 1 | 0 |" in section


class TestTheBeatsBlockComparison:
    """One candidate ran the no-block arm, so the with-block side is that one."""

    GRANITE = "ibm/granite-4-h-small"
    GPT_OSS = "openai/gpt-oss-120b"

    def test_the_other_model_is_left_out_of_both_sides(self):
        """Reading the no-block arm against both models would put the better
        grounder on one side of a comparison about the prompt."""
        rows = [
            # The candidate that ran both prompts.
            a_record(arm="c2", model=self.GRANITE, beats_block=True),
            a_record(
                arm="c",
                model=self.GRANITE,
                beats_block=False,
                run=2,
                first_attempt_grounded=False,
                source=TEMPLATE,
            ),
            # The one that only ever ran with the block.
            a_record(arm="b", model=self.GPT_OSS, beats_block=True),
            a_record(arm="b", model=self.GPT_OSS, beats_block=True, run=2),
        ]
        section = "\n".join(watsonx_section(rows))
        block = section.split("What the beats block costs")[1].split("###")[0]
        assert f"`{self.GRANITE}`" in block
        assert f"`{self.GPT_OSS}`" not in block
        # One narration a side, not three on the with-block side.
        assert "| with the beats block | 1 |" in block
        assert "| without it | 1 |" in block
