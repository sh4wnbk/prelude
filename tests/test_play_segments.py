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
from dataclasses import replace
from pathlib import Path

import pytest

from app.grounding import goal_call_reader, sentences
from app.narration_grammar import SPAN_KEYS, support
from app.play_segments import NotGrounded, move_span, segments
from scripts.narrator_candidates import narrator_for

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
NARRATIONS = ROOT / "app" / "web" / "narrations.json"

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
