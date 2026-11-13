"""The label never stands over the wrong words, an empty paragraph or nothing.

The states Task 29 found by hand and Task 30 added the play button to, now read
in a browser on every push. Three of them are about `narrations.json`, which is
the one fetch on the moment card with no fallback: the words it carries arrive
under "Verified from play data", so another match's words or no words at all
would be a false claim rather than a stale screen.

- **Slow.** The server holds `narrations.json` for two seconds. The delay is
  the server's, for the reason `tests/browser/server.py` records: a sleep in
  the driver reports a state the page has already left.
- **Refused.** The server answers `503`.
- **Never answered.** The server holds the connection and says nothing.

In every one of them three rules are asked of every frame the card passed
through, not only of the state it settled in, and a `MutationObserver`
installed before the page's own scripts gives the frames:

1. the paragraph holds nothing, or exactly the served slot's text for the
   match and the slot on screen,
2. the paragraph and the label are both hidden or both shown,
3. the play button is disabled in every frame where the words are hidden.

The third is this task's. The first two are Task 29's, with the frames read the
same way.

`matches.json` is checked too, because the card's other fields do take a
fallback: with that fetch refused the inline 1986 copy is a correct screen, and
the narration and the label still have to stay hidden, because the fallback
copy is the default match's and the narration is not.
"""

import pytest

from tests.browser.conftest import (
    CARD_STATE, LISTENERS, MOMENT_CARD, PLAY_OFFERED, WATCH_THE_CARD,
)
from tests.browser.test_the_fan_hears_their_own import BLOCK_PX

#: Long enough to read the card while the fetch is still in the air.
SLOW_SECONDS = 2.0

ALL_SLOT_TEXT = None   # filled by `every_frozen_line`


@pytest.fixture(scope="session")
def every_frozen_line(narrations):
    """Every frozen narration in the file, for rule 1's other half.

    Rule 1 is two claims: the paragraph holds the right words, and it holds
    nothing else. A paragraph holding another match's or another slot's words
    is the failure Task 29 was about, so the frames are checked against the
    whole set and not only against the one that is correct here.
    """
    lines = set()
    for match in narrations.values():
        for slot in match["slots"].values():
            lines.add(slot["text"])
    return lines


def obeys(frames, wanted_text, every_line):
    """The three rules, over every frame. Returns the offending frame or None."""
    for frame in frames:
        text = frame["text"]
        if text and text != wanted_text:
            return ("other words", frame)
        if text and text in every_line and text != wanted_text:
            return ("another slot's words", frame)
        if frame["wordsShown"] != frame["labelShown"]:
            return ("one shown without the other", frame)
        if frame["labelShown"] and not text.strip():
            return ("the label over an empty paragraph", frame)
        if not frame["wordsShown"] and frame["playDisabled"] is False:
            return ("play offered with the words hidden", frame)
    return None


def watched(fan, screen, **query):
    fan.page.add_init_script(WATCH_THE_CARD)
    return fan.visit(screen, **query)


def frames(fan):
    return fan.page.evaluate("() => window.__preludeFrames")


@pytest.mark.parametrize("listener", LISTENERS)
def test_a_slow_narrations_file(
    fan, plan, match_ids, expected, every_frozen_line, listener
):
    plan.delay["narrations.json"] = SLOW_SECONDS
    for match_id in match_ids:
        want = expected(match_id, listener)
        fan.remember(match_id=match_id, listener=listener)
        watched(fan, MOMENT_CARD, match=match_id)

        # Read while the fetch is still in the air.
        mid = fan.page.evaluate(CARD_STATE)
        assert mid["text"] == "", (match_id, mid)
        assert mid["wordsShown"] is False
        assert mid["labelShown"] is False
        assert mid["playDisabled"] is True
        assert mid["blockHeight"] == BLOCK_PX, mid
        # The header is this match's, so the fan is not looking at the other
        # one while they wait.
        assert str(want["slot"])
        assert mid["header"]

        fan.page.wait_for_function(
            PLAY_OFFERED, timeout=(SLOW_SECONDS + 8) * 1000
        )
        end = fan.page.evaluate(CARD_STATE)
        assert end["text"] == want["text"], (match_id, listener)
        assert end["labelShown"] is True
        assert end["blockHeight"] == BLOCK_PX, end

        broken = obeys(frames(fan), want["text"], every_frozen_line)
        assert broken is None, (match_id, listener, broken)


@pytest.mark.parametrize("status", [500, 503])
def test_a_refused_narrations_file(
    fan, plan, match_ids, expected, every_frozen_line, status
):
    plan.status["narrations.json"] = status
    for match_id in match_ids:
        want = expected(match_id, "team_b")
        fan.remember(match_id=match_id, listener="team_b")
        watched(fan, MOMENT_CARD, match=match_id)
        fan.page.wait_for_timeout(600)
        state = fan.page.evaluate(CARD_STATE)
        assert state["text"] == "", (match_id, status, state)
        assert state["wordsShown"] is False
        assert state["labelShown"] is False
        assert state["playDisabled"] is True, (match_id, status)
        assert state["blockHeight"] == BLOCK_PX, state
        broken = obeys(frames(fan), want["text"], every_frozen_line)
        assert broken is None, (match_id, status, broken)


def test_a_narrations_file_that_never_answers(
    fan, plan, match_ids, expected, every_frozen_line
):
    plan.hang.add("narrations.json")
    for match_id in match_ids:
        want = expected(match_id, "team_a")
        fan.remember(match_id=match_id, listener="team_a")
        watched(fan, MOMENT_CARD, match=match_id)
        fan.page.wait_for_timeout(1500)
        state = fan.page.evaluate(CARD_STATE)
        assert state["text"] == ""
        assert state["labelShown"] is False
        assert state["playDisabled"] is True, (match_id, state)
        broken = obeys(frames(fan), want["text"], every_frozen_line)
        assert broken is None, (match_id, broken)


def test_a_slow_matches_file_leaves_the_card_quiet(fan, plan, match_ids, expected):
    """Both fetches late. The card paints its inline copy, which is the 1986
    match, and the narration and the label and the button all wait."""
    plan.delay["matches.json"] = SLOW_SECONDS
    plan.delay["narrations.json"] = SLOW_SECONDS
    for match_id in match_ids:
        fan.remember(match_id=match_id, listener="neutral")
        fan.page.add_init_script(WATCH_THE_CARD)
        fan.goto(MOMENT_CARD, match=match_id)
        fan.page.wait_for_load_state("domcontentloaded")
        state = fan.page.evaluate(CARD_STATE)
        assert state["text"] == ""
        assert state["labelShown"] is False
        assert state["playDisabled"] is True
        assert state["blockHeight"] == BLOCK_PX, state


def test_a_refused_matches_file_leaves_the_card_quiet(
    fan, plan, match_ids, expected, every_frozen_line
):
    plan.status["matches.json"] = 503
    for match_id in match_ids:
        want = expected(match_id, "neutral")
        fan.page.add_init_script(WATCH_THE_CARD)
        fan.goto(MOMENT_CARD, match=match_id)
        fan.page.wait_for_timeout(600)
        state = fan.page.evaluate(CARD_STATE)
        assert state["text"] == "", state
        assert state["labelShown"] is False
        assert state["playDisabled"] is True
        broken = obeys(frames(fan), want["text"], every_frozen_line)
        assert broken is None, (match_id, broken)


def test_a_refresh_and_a_reopened_tab_keep_the_rules(
    fan, plan, match_ids, expected, every_frozen_line
):
    """A reload and a new tab are two more first loads, and the second one has
    no `sessionStorage`, so the listener answer is gone and the fan is the
    neutral one. Both still obey the three rules."""
    match_id = match_ids[0]
    fan.remember(match_id=match_id, listener="team_b")
    watched(fan, MOMENT_CARD, match=match_id)
    fan.page.wait_for_function(PLAY_OFFERED)
    want = expected(match_id, "team_b")
    assert fan.page.evaluate(CARD_STATE)["text"] == want["text"]

    fan.page.reload()
    fan.page.wait_for_function(PLAY_OFFERED)
    assert fan.page.evaluate(CARD_STATE)["text"] == want["text"]
    broken = obeys(frames(fan), want["text"], every_frozen_line)
    assert broken is None, broken

    page = fan.reopen()
    page.add_init_script(WATCH_THE_CARD)
    fan.visit(MOMENT_CARD, match=match_id)
    page.wait_for_function(PLAY_OFFERED)
    neutral = expected(match_id, "neutral")
    assert page.evaluate(CARD_STATE)["text"] == neutral["text"]
    broken = obeys(frames(fan), neutral["text"], every_frozen_line)
    assert broken is None, broken


def test_the_label_is_never_over_another_matchs_words(
    fan, plan, match_ids, expected, every_frozen_line
):
    """The 2022 card read one second into a slow load, which is the exact
    reading Task 29 was opened by: the 1986 words under a 2022 header and
    under the label."""
    plan.delay["narrations.json"] = SLOW_SECONDS
    other = expected(match_ids[0], "neutral")["text"]
    fan.remember(match_id=match_ids[1], listener="neutral")
    watched(fan, MOMENT_CARD, match=match_ids[1])
    fan.page.wait_for_timeout(1000)
    state = fan.page.evaluate(CARD_STATE)
    assert other not in (state["text"] or ""), state
    assert state["labelShown"] is False
    fan.page.wait_for_function(
        PLAY_OFFERED, timeout=(SLOW_SECONDS + 8) * 1000
    )
    want = expected(match_ids[1], "neutral")
    for frame in frames(fan):
        assert other not in (frame["text"] or ""), frame
    broken = obeys(frames(fan), want["text"], every_frozen_line)
    assert broken is None, broken
