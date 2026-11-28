"""The six frozen narrations, cut into spans and pointed at their records.

`app/play_segments.py` says which words of a narration the check passed stand
on which events. These tests read `data/raw/` and build the facts the way
`slot_facts` in `tests/test_frozen_narrations.py` does, so every span is held
to the events on disk and not to a fixture.

Every expected value here is a literal, read once off the data and written
down, so a change underneath shows up as a failure rather than being checked
against itself.
"""

import json
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from app.grounding import goal_call_reader, sentences
from app.narration_grammar import SPAN_KEYS, support
from app.play_segments import (
    NotGrounded,
    _fold_pressure_into_presser,
    move_span,
    segments,
)
from scripts.narrator_candidates import narrator_for

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
NARRATIONS = ROOT / "app" / "web" / "narrations.json"
SEGMENTS_FILE = ROOT / "app" / "web" / "play_segments.json"
WRITER = ROOT / "scripts" / "write_play_segments.py"

#: The two hero goals, by match and clock, as `tests/test_frozen_narrations.py`
#: has them.
HEROES = {
    "3750191": (54, 18),
    "3869685": (35, 22),
}

SLOTS = ("buddy_conceded", "buddy_scored", "storyteller_neutral")

#: Each match's goal shot, the record the finish has to stand on.
GOAL_SHOT = {
    "3750191": "f7c68c94-1db5-477f-aabe-f97733605571",
    "3869685": "ef86f4d9-7acd-4ed0-a5ec-9129079e8fbe",
}

#: Where each slot says the finish: its start and its words.
FINISH = {
    ("3750191", "buddy_conceded"): (244, "scored"),
    ("3750191", "buddy_scored"): (257, "scored"),
    ("3750191", "storyteller_neutral"): (289, "scored"),
    ("3869685", "buddy_conceded"): (256, "hit"),
    ("3869685", "buddy_scored"): (262, "hit"),
    ("3869685", "storyteller_neutral"): (316, "finished"),
}

#: The 2022 long ball, merged with its chain by `Reader._merge_long`, and the
#: one long pass that holds it.
LONG_BALL_SAID = "long ball forward to MacAllister"
LONG_PASS = "5a800227-911a-4490-b828-14ece1f81d76"
LONG_BALL_START = {
    "buddy_conceded": 155,
    "buddy_scored": 165,
    "storyteller_neutral": 209,
}


def make_feed():
    if not RAW.is_dir():
        pytest.fail(
            "data/raw/ is absent, so the segments cannot be checked against "
            "the events. Run scripts/fetch_statsbomb.py."
        )
    from app.statsbomb_event_feed import StatsBombEventFeed

    return StatsBombEventFeed()


_FACTS: dict = {}


def slot_facts(match_id: str):
    """The facts for one hero goal, with the names and teams on them."""
    if match_id in _FACTS:
        return _FACTS[match_id]
    from app.narration_prompt import facts_from_buildup
    from app.recorded_names import recorded_nicknames, recorded_teams

    feed = make_feed()
    clock = HEROES[match_id]
    found = [
        moment
        for moment in feed.defining_moments(int(match_id))
        if (moment.minute, moment.second) == clock
    ]
    assert len(found) == 1
    _FACTS[match_id] = facts_from_buildup(
        feed.buildup(int(match_id), found[0]),
        recorded_nicknames(int(match_id)),
        recorded_teams(int(match_id)),
    )
    return _FACTS[match_id]


def slot(match_id: str, key: str) -> dict:
    document = json.loads(NARRATIONS.read_text(encoding="utf-8"))
    return document["narrations"][match_id]["slots"][key]


def cut(match_id: str, key: str) -> tuple[str, list[dict]]:
    one = slot(match_id, key)
    return one["text"], segments(
        one["text"],
        slot_facts(match_id),
        narrator_for(key),
        one["listener_side"],
    )


EVERY_SLOT = [(match_id, key) for match_id in HEROES for key in SLOTS]


@pytest.mark.parametrize("match_id,key", EVERY_SLOT)
class TestEverySlot:
    def test_it_gives_at_least_one_segment(self, match_id, key):
        _text, found = cut(match_id, key)
        assert len(found) >= 1

    def test_segments_are_in_order_and_do_not_overlap(self, match_id, key):
        _text, found = cut(match_id, key)
        for before, after in zip(found, found[1:]):
            assert before["start_char"] < after["start_char"]
            assert before["end_char"] <= after["start_char"]

    def test_every_event_id_is_in_the_raw_events(self, match_id, key):
        events = json.loads(
            (RAW / "events" / f"{match_id}.json").read_text(encoding="utf-8")
        )
        ids = {event["id"] for event in events}
        _text, found = cut(match_id, key)
        for segment in found:
            assert segment["event_ids"]
            for event_id in segment["event_ids"]:
                assert event_id in ids, (segment["said"], event_id)

    def test_every_span_reads_as_its_said(self, match_id, key):
        text, found = cut(match_id, key)
        for segment in found:
            span = text[segment["start_char"]:segment["end_char"]]
            assert span == segment["said"]

    def test_the_finish_stands_on_the_goal_shot(self, match_id, key):
        _text, found = cut(match_id, key)
        start, said = FINISH[(match_id, key)]
        finish = [one for one in found if one["start_char"] == start]
        assert len(finish) == 1
        assert finish[0]["said"] == said
        assert GOAL_SHOT[match_id] in finish[0]["event_ids"]


class TestTheMergedClaims:
    def test_pressed_carries_both_pressers(self):
        _text, found = cut("3750191", "buddy_conceded")
        pressed = [one for one in found if one["said"] == "pressed"]
        assert pressed == [
            {
                "start_char": 78,
                "end_char": 85,
                "said": "pressed",
                "kind": "action",
                "event_ids": [
                    "3fa18492-7ff8-46ec-8fce-c045726a8d36",
                    "9acad196-80b8-47ce-8353-1c6cf38563cb",
                ],
            }
        ]

    @pytest.mark.parametrize("key", SLOTS)
    def test_the_2022_long_ball_is_one_span_on_one_pass(self, key):
        _text, found = cut("3869685", key)
        long_ball = [
            one for one in found if one["start_char"] == LONG_BALL_START[key]
        ]
        assert len(long_ball) == 1
        assert long_ball[0]["said"] == LONG_BALL_SAID
        assert long_ball[0]["event_ids"] == [LONG_PASS]

    def test_a_chain_opens_on_its_marker_not_its_name(self):
        _text, found = cut("3750191", "buddy_scored")
        chain = [one for one in found if one["kind"] == "chain"]
        assert chain == [
            {
                "start_char": 51,
                "end_char": 65,
                "said": "found Maradona",
                "kind": "chain",
                "event_ids": ["3c9db676-5edd-49af-8508-ab7d462ce25d"],
            }
        ]


class TestTheReader:
    def test_under_pressure_from_a_1986_presser_spans_its_said(self):
        sentence = "Maradona carried it on under pressure from Beardsley."
        moves = goal_call_reader(slot_facts("3750191"), None).read(sentence)
        pressed_by = [move for move in moves if move.kind == "pressed_by"]
        assert len(pressed_by) == 1
        start, end = move_span(sentence, pressed_by[0], moves)
        assert (start, end) == (23, 52)
        assert sentence[start:end] == pressed_by[0].said
        assert pressed_by[0].said == "under pressure from Beardsley"

    def test_the_span_keys_change_no_record_a_move_stands_on(self):
        """`SPAN_KEYS` are position data only: a move with them taken out of
        its detail is held by exactly the records it was held by, in every
        slot."""
        seen = 0
        for match_id, key in EVERY_SLOT:
            one = slot(match_id, key)
            facts = slot_facts(match_id)
            reader = goal_call_reader(facts, one["listener_side"])
            for move in (
                move
                for sentence in sentences(one["text"])
                for move in reader.read(sentence.text)
            ):
                if not isinstance(move.detail, dict):
                    continue
                if not SPAN_KEYS & set(move.detail):
                    continue
                seen += 1
                bare = replace(
                    move,
                    detail={
                        name: value
                        for name, value in move.detail.items()
                        if name not in SPAN_KEYS
                    },
                )
                assert support(bare, facts) == support(move, facts)
        assert seen == 17


class TestUnderPressureFrom:
    """The carrier's flag and the presser's record, said over nested words,
    are one segment over the longer span."""

    def test_it_is_one_segment_with_both_claims_records(self):
        sentence = (
            "Maradona carried it on under pressure from Beardsley, went past "
            "Butcher and scored with his left foot."
        )
        found = segments(sentence, slot_facts("3750191"), None, None)
        pressure = [one for one in found if "pressed_by" in one["kind"]]
        assert pressure == [
            {
                "start_char": 23,
                "end_char": 52,
                "said": "under pressure from Beardsley",
                "kind": "pressured+pressed_by",
                "event_ids": [
                    "cf1088ae-4ec8-4a43-b154-f53c3eb90388",
                    "1aca4e20-faca-4edf-bd2b-926c8d47c8e1",
                    "d8caa5f4-88e5-4840-87bb-95dc1645cb57",
                    "8452a2e7-343a-4b7a-9602-42450ee4742e",
                    "c8798a94-3bc5-4bb7-aa5c-a7c2c393d0ee",
                    "b16e026b-f9cf-4ec4-a160-5a1df11afaed",
                    "b29fa2f1-ab67-4650-8300-4c7864ca6790",
                    "5573383d-bddb-4785-8a21-39ccc8421f03",
                    "abbf4118-3967-4455-8fea-7710c1b322ef",
                    "3fa18492-7ff8-46ec-8fce-c045726a8d36",
                ],
            }
        ]
        assert not [one for one in found if one["kind"] == "pressured"]

    def test_a_pressured_span_not_inside_a_presser_is_left_alone(self):
        """Only containment is folded, so an overlap that is not one is still
        there for `segments` to refuse."""
        spans = {
            (10, 29): {
                "start_char": 10, "end_char": 29, "said": "x" * 19,
                "kind": "pressured", "event_ids": ["a"],
            },
            (20, 40): {
                "start_char": 20, "end_char": 40, "said": "y" * 20,
                "kind": "pressed_by", "event_ids": ["b"],
            },
        }
        _fold_pressure_into_presser(spans)
        assert sorted(spans) == [(10, 29), (20, 40)]


class TestWhatItRefuses:
    def test_a_narration_the_check_refuses_raises(self):
        refused = "Fenwick scored with his right foot."
        with pytest.raises(NotGrounded):
            segments(refused, slot_facts("3750191"), None, None)

    def test_a_curly_apostrophe_raises(self):
        """The check passes it, because it reads the straightened text, but
        an offset into what it read is not an offset into this one."""
        one = slot("3869685", "buddy_scored")
        curly = one["text"].replace("France's", "France’s")
        assert curly != one["text"]
        with pytest.raises(NotGrounded):
            segments(
                curly,
                slot_facts("3869685"),
                narrator_for("buddy_scored"),
                one["listener_side"],
            )


def write_segments(*arguments):
    return subprocess.run(
        [sys.executable, str(WRITER), *arguments],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    )


class TestTheSegmentsFile:
    """`scripts/write_play_segments.py` and the file it writes. `--check` is
    run against a copy in pytest's own directory, so the suite leaves the
    tree as it found it."""

    def test_check_passes_on_a_copy_of_the_committed_file(self, tmp_path):
        copy = tmp_path / "play_segments.json"
        shutil.copy(SEGMENTS_FILE, copy)
        before = copy.read_bytes()
        result = write_segments("--check", "--path", str(copy))
        assert result.returncode == 0, result.stdout + result.stderr
        assert copy.read_bytes() == before
        assert "1986 match 3750191 buddy_conceded: 8 segment(s)" in result.stdout
        assert "2022 match 3869685 buddy_scored: 10 segment(s)" in result.stdout

    def test_check_fails_on_a_copy_that_drifted(self, tmp_path):
        copy = tmp_path / "play_segments.json"
        document = json.loads(SEGMENTS_FILE.read_text(encoding="utf-8"))
        document["matches"]["3750191"]["slots"]["buddy_scored"][
            "segments"
        ].pop()
        copy.write_text(json.dumps(document), encoding="utf-8")
        result = write_segments("--check", "--path", str(copy))
        assert result.returncode == 1, result.stdout + result.stderr

    def test_check_fails_on_a_missing_file(self, tmp_path):
        result = write_segments(
            "--check", "--path", str(tmp_path / "absent.json")
        )
        assert result.returncode == 1, result.stdout + result.stderr

    def test_the_file_holds_the_segments(self):
        document = json.loads(SEGMENTS_FILE.read_text(encoding="utf-8"))
        for match_id, key in EVERY_SLOT:
            _text, found = cut(match_id, key)
            slot_doc = document["matches"][match_id]["slots"][key]
            assert slot_doc["segments"] == found

    def test_every_event_id_is_in_that_goals_buildup(self):
        document = json.loads(SEGMENTS_FILE.read_text(encoding="utf-8"))
        for match_id, entry in document["matches"].items():
            buildup = {beat.event_id for beat in slot_facts(match_id).beats}
            assert set(entry["records"]) <= buildup
            for slot_doc in entry["slots"].values():
                for segment in slot_doc["segments"]:
                    assert set(segment["event_ids"]) <= buildup

    def test_draw_from_is_non_decreasing_in_clock_order(self):
        document = json.loads(SEGMENTS_FILE.read_text(encoding="utf-8"))
        for match_id, entry in document["matches"].items():
            records = entry["records"]
            for key, slot_doc in entry["slots"].items():
                drawn = slot_doc["draw_from"]
                named = {
                    event_id
                    for segment in slot_doc["segments"]
                    for event_id in segment["event_ids"]
                }
                assert set(drawn) == named, (match_id, key)
                in_clock_order = sorted(
                    drawn, key=lambda one: records[one]["index"]
                )
                steps = [drawn[event_id] for event_id in in_clock_order]
                assert steps == sorted(steps), (match_id, key)

    def test_the_1986_shot_is_drawn_at_scored_not_picked_it_up(self):
        slot_doc = json.loads(SEGMENTS_FILE.read_text(encoding="utf-8"))[
            "matches"
        ]["3750191"]["slots"]["buddy_conceded"]
        found = slot_doc["segments"]
        assert found[0]["said"] == "picked it up"
        assert GOAL_SHOT["3750191"] in found[0]["event_ids"]
        at = slot_doc["draw_from"][GOAL_SHOT["3750191"]]
        assert at == 6
        assert found[at]["said"] == "scored"

    def test_the_1986_carry_1970_is_drawn_no_earlier_than_shilton(self):
        slot_doc = json.loads(SEGMENTS_FILE.read_text(encoding="utf-8"))[
            "matches"
        ]["3750191"]["slots"]["storyteller_neutral"]
        found = slot_doc["segments"]
        carry = "abbf4118-3967-4455-8fea-7710c1b322ef"
        shilton = [n for n, one in enumerate(found) if one["said"] == "Shilton"]
        assert shilton == [6]
        assert slot_doc["draw_from"][carry] >= 6

    def test_three_records_as_the_raw_events_hold_them(self):
        records = json.loads(SEGMENTS_FILE.read_text(encoding="utf-8"))[
            "matches"
        ]
        assert records["3869685"]["records"][LONG_PASS] == {
            "index": 1174,
            "type": "Pass",
            "team": "Argentina",
            "player": "Julián Álvarez",
            "location": [63.2, 68.2],
            "end_location": [99.3, 54.9],
        }
        assert records["3750191"]["records"][GOAL_SHOT["3750191"]] == {
            "index": 1971,
            "type": "Shot",
            "team": "Argentina",
            "player": "Diego Armando Maradona",
            "location": [113.4, 49.5],
            "end_location": [120.0, 41.7, 0.2],
        }
        assert records["3750191"]["records"][
            "3fa18492-7ff8-46ec-8fce-c045726a8d36"
        ] == {
            "index": 1956,
            "type": "Pressure",
            "team": "England",
            "player": "Peter Beardsley",
            "location": [64.9, 20.9],
            "end_location": None,
        }

    def test_records_are_exactly_the_events_the_segments_name(self):
        document = json.loads(SEGMENTS_FILE.read_text(encoding="utf-8"))
        for match_id, entry in document["matches"].items():
            named = {
                event_id
                for slot_doc in entry["slots"].values()
                for segment in slot_doc["segments"]
                for event_id in segment["event_ids"]
            }
            assert set(entry["records"]) == named

    def test_every_record_is_its_raw_event_unchanged(self):
        document = json.loads(SEGMENTS_FILE.read_text(encoding="utf-8"))
        for match_id, entry in document["matches"].items():
            events = {
                event["id"]: event
                for event in json.loads(
                    (RAW / "events" / f"{match_id}.json").read_text(
                        encoding="utf-8"
                    )
                )
            }
            for event_id, record in entry["records"].items():
                event = events[event_id]
                assert record["index"] == event["index"]
                assert record["type"] == event["type"]["name"]
                assert record["team"] == event["team"]["name"]
                assert record["player"] == event["player"]["name"]
                assert record["location"] == event["location"]
                block = next(
                    (event[f] for f in ("pass", "carry", "shot") if f in event),
                    {},
                )
                assert record["end_location"] == block.get("end_location")
