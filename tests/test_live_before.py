"""Acceptance tests for where the 1986 fan steps away, written before the fix.

The fan used to leave at 48' with the score 0 to 0 and come back at 55' to
2 to 0, so two goals fell in the window and the moment card told only one.
Shawn's decision on 2026-10-29: the fan sees the 50:27 goal from their seat and
leaves at 52' with the score 1 to 0, so one goal is missed and the card tells
it. `scripts/check_match_copy.py` now refuses any window holding more or
fewer than one goal. `docs/bob_brief.md` carries the brief as Task 8.

2022 already had one goal in its window and is not changed.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "app" / "web"
LIVE = WEB / "prelude_02_live_seated.html"


def before_1986():
    doc = json.loads((WEB / "matches.json").read_text(encoding="utf-8"))
    entry = next(e for e in doc["matches"] if e["match_id"] == 3750191)
    return entry["live_seated"]["before"]


class TestTheStepAwayIn1986:
    def test_the_fan_leaves_at_52(self):
        assert before_1986()["display_minute"] == 52

    def test_the_score_when_they_leave_is_1_0(self):
        before = before_1986()
        assert (before["home_goals"], before["away_goals"]) == (1, 0)

    def test_it_is_still_the_second_half(self):
        before = before_1986()
        assert (before["period"], before["period_label"]) == (2, "2H")


class TestTheLiveScreenInlineCopy:
    """The Live screen carries the 1986 before state inline, for when
    `matches.json` cannot be fetched, so it has to move with the data."""

    def test_the_state_badge(self):
        assert 'data-field="state_badge">2H · 52\'' in LIVE.read_text(encoding="utf-8")

    def test_the_half_line(self):
        assert 'data-field="half_line">SECOND HALF · 52\'' in LIVE.read_text(encoding="utf-8")

    def test_the_home_score(self):
        assert 'data-field="home_goals">1<' in LIVE.read_text(encoding="utf-8")

    def test_the_old_clock_is_gone(self):
        assert "48'" not in LIVE.read_text(encoding="utf-8")
