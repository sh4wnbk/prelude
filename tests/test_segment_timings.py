"""The segment timings, held to the segments and to the recordings on disk.

`app/web/segment_timings.json` is written offline by
`scripts/align_segments.py`, which needs a speech model CI does not have. So
nothing here transcribes anything: it reads the committed file and asks that
it still describes the committed segments and the committed recordings. A
re-cut narration or a re-recorded MP3 leaves the timings describing something
else, and that is what fails here.
"""

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
TIMINGS = WEB / "segment_timings.json"
SEGMENTS = WEB / "play_segments.json"
MATCHES = WEB / "matches.json"

MATCH_IDS = ("3750191", "3869685")
SLOTS = ("buddy_conceded", "buddy_scored", "storyteller_neutral")
EVERY_SLOT = [(match_id, key) for match_id in MATCH_IDS for key in SLOTS]


def timings() -> dict:
    return json.loads(TIMINGS.read_text(encoding="utf-8"))["matches"]


def play() -> dict:
    return json.loads(SEGMENTS.read_text(encoding="utf-8"))["matches"]


def audio_for(match_id: str, key: str) -> str:
    document = json.loads(MATCHES.read_text(encoding="utf-8"))
    match = next(
        one for one in document["matches"] if str(one["match_id"]) == match_id
    )
    return match["hero"]["audio"][key]


def test_every_slot_is_timed_and_nothing_else():
    assert sorted(timings()) == list(MATCH_IDS)
    for match_id in MATCH_IDS:
        assert sorted(timings()[match_id]) == list(SLOTS)


@pytest.mark.parametrize("match_id,key", EVERY_SLOT)
class TestEverySlot:
    def test_the_segments_are_the_play_segments_in_order(self, match_id, key):
        timed = timings()[match_id][key]["segments"]
        cut = play()[match_id]["slots"][key]["segments"]
        assert len(timed) == len(cut)
        assert [one["said"] for one in timed] == [one["said"] for one in cut]

    def test_start_ms_rises_strictly_and_ends_inside_the_file(
        self, match_id, key
    ):
        slot = timings()[match_id][key]
        starts = [one["start_ms"] for one in slot["segments"]]
        assert all(isinstance(ms, int) for ms in starts)
        assert starts[0] >= 0
        for before, after in zip(starts, starts[1:]):
            assert before < after
        assert starts[-1] < slot["duration_ms"]

    def test_it_is_the_committed_recording(self, match_id, key):
        slot = timings()[match_id][key]
        assert slot["audio"] == audio_for(match_id, key)
        recording = WEB / slot["audio"]
        assert slot["sha256"] == hashlib.sha256(
            recording.read_bytes()
        ).hexdigest()
