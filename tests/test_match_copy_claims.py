"""The copy gate's hold on lines that describe the play.

`scripts/check_match_copy.py` has always read the values in
`app/web/matches.json` against `data/raw/`: the names, the minutes, the
scores, the counts. Task 33 asked a different question, which is what the
*words* claim. The moment card's caption said Maradona's goal was a solo run
from his own half past four England players, the share sheet said "solo goal",
and both 1986 moments described the play in a sentence each. None of that was
read against anything: the check verified the clock in front of the caption
and let the rest of the line stand.

Three rules now hold them, and this is what proves each one bites. The data
is the real feed, and the copy is the committed copy with one value moved, so
a rule that stopped working would show up here as a mutation that no longer
fails.

1. **Every grounding key is checked against the feed.** `tests/` had no cover
   for the keys before this file: `check_match_copy.py` was its own test.
2. **Every key is said in the words beside it**, so a block of keys cannot be
   a grounding score attached to a line that says something else.
3. **Every claim in the words has a key**, so a new adjective about the play
   cannot be written into `matches.json` without something reading it against
   the feed.

The committed copy passing is the fourth claim, and `scripts/check_match_copy.py`
makes it on every run; `test_the_committed_copy_passes_every_rule` is it inside
the suite.
"""

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from check_match_copy import (  # noqa: E402
    CLAIMS,
    HELD_PROSE,
    SAYS,
    check_grounding,
    check_match,
    check_names,
    check_prose,
    goals_of,
    load,
)

RAW = ROOT / "data" / "raw"
MATCHES = ROOT / "app" / "web" / "matches.json"

#: The 1986 match, whose hero is the goal every one of the new keys was
#: written for, and the 2022 match, which carries the older three.
ARG_ENG = 3750191
ARG_FRA = 3869685


@pytest.fixture(scope="module")
def doc():
    return json.loads(MATCHES.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def entries(doc):
    return {entry["match_id"]: entry for entry in doc["matches"]}


@pytest.fixture(scope="module")
def events():
    return {mid: load(RAW / "events" / f"{mid}.json") for mid in (ARG_ENG, ARG_FRA)}


def run(entry, events_of_match):
    """One match entry through the whole gate. Returns the failures."""
    failures = []
    check_match(entry, lambda where, why: failures.append(f"{where}: {why}"),
                lambda line: None)
    return failures


def hero_of(entries, events, mid):
    """The hero block, its goal and that match's events."""
    entry = entries[mid]
    these = events[mid]
    goal = next(g for g in goals_of(these)
                if (g["period"], g["minute"], g["second"])
                == (entry["hero"]["event"]["period"],
                    entry["hero"]["event"]["minute"],
                    entry["hero"]["event"]["second"]))
    return entry["hero"], goal, these


class TestTheCommittedCopyPasses:
    def test_the_committed_copy_passes_every_rule(self, entries, events):
        for mid in (ARG_ENG, ARG_FRA):
            assert run(copy.deepcopy(entries[mid]), events[mid]) == [], mid


class TestEveryKeyIsReadAgainstTheFeed:
    """Rule 1. Each key moved off what the feed says, one at a time."""

    @pytest.mark.parametrize("key, wrong", [
        ("solo_run", False),
        ("own_half", "the final third"),
        ("dribbled_past", 5),
    ])
    def test_the_1986_hero_keys(self, entries, events, key, wrong):
        """`own_half` takes one of two readings and is refused anything else.
        Both of its readings are true of this goal, which is why the wrong
        value here is a third one: Maradona's first touch and the start of
        the possession are both short of the halfway line. The reading that
        matters is held by `test_the_2022_hero_keys`, where they differ."""
        entry = copy.deepcopy(entries[ARG_ENG])
        entry["hero"]["grounding"][key] = wrong
        assert any(key in one for one in run(entry, events[ARG_ENG])), key

    @pytest.mark.parametrize("key, wrong", [
        ("match_goal_number", 2),
        ("recovers_error", "Peter Shilton"),
        ("yards_from_goal", 20),
    ])
    def test_the_1986_opener_keys(self, entries, events, key, wrong):
        entry = copy.deepcopy(entries[ARG_ENG])
        entry["moments"][0]["grounding"][key] = wrong
        assert any(key in one for one in run(entry, events[ARG_ENG])), key

    @pytest.mark.parametrize("key, wrong", [
        ("play_pattern", "Regular Play"),
        ("own_half", "first touch"),
    ])
    def test_the_2022_hero_keys(self, entries, events, key, wrong):
        entry = copy.deepcopy(entries[ARG_FRA])
        entry["hero"]["grounding"][key] = wrong
        assert any(key in one for one in run(entry, events[ARG_FRA])), key

    @pytest.mark.parametrize("key, wrong", [
        ("body_part", "Right Foot"),
        ("assist", "Lionel Andrés Messi Cuccittini"),
    ])
    def test_the_2022_moment_keys(self, entries, events, key, wrong):
        entry = copy.deepcopy(entries[ARG_FRA])
        entry["moments"][1]["grounding"][key] = wrong
        assert any(key in one for one in run(entry, events[ARG_FRA])), key

    def test_solo_run_is_a_run_and_not_a_one_touch_finish(
            self, entries, events):
        """The 2022 hero is a five-pass move finished first time by the man
        who received it. Nobody else is on the ball between his first touch
        and his shot, so "nobody else touched it" is satisfied by a tap-in;
        the reading also asks the feed for a carry or a dribble of his own,
        and there is none."""
        entry = copy.deepcopy(entries[ARG_FRA])
        entry["hero"]["grounding"]["solo_run"] = True
        entry["hero"]["caption"] += " A solo run."
        assert any("solo_run" in one for one in run(entry, events[ARG_FRA]))

    def test_dribbled_past_counts_only_that_possession(self, entries, events):
        """Four England players were dribbled past in the goal's possession.
        The match holds more than four Dribbled Past events in all."""
        these = events[ARG_ENG]
        hero, goal, _ = hero_of(entries, events, ARG_ENG)
        whole_match = [e for e in these if e["type"]["name"] == "Dribbled Past"]
        in_the_move = [e for e in whole_match if e["possession"] == goal["possession"]]
        assert len(in_the_move) == 4
        assert len(whole_match) > len(in_the_move)


class TestEveryKeyIsSaidInTheWords:
    """Rule 2. The key still checks out; the words stop saying it."""

    def test_a_key_the_line_does_not_say(self, entries, events):
        entry = copy.deepcopy(entries[ARG_ENG])
        entry["hero"]["caption"] = "2H · 55' · Maradona scores"
        entry["hero"]["share_text"] = "Maradona's goal as it happened."
        said = run(entry, events[ARG_ENG])
        assert any("the words do not" in one for one in said), said

    def test_every_key_the_copy_uses_has_a_reading(self, entries):
        for entry in entries.values():
            blocks = [entry["hero"]] + list(entry["moments"])
            for block in blocks:
                for key in block.get("grounding", {}):
                    assert key in SAYS, key

    def test_a_key_with_no_reading_is_reported_rather_than_skipped(
            self, entries, events):
        hero, goal, these = hero_of(entries, events, ARG_ENG)
        block = copy.deepcopy(hero)
        block["grounding"] = {"invented_key": True}
        failures = []
        check_prose("test", "some words", block, goal, these,
                    lambda where, why: failures.append(why), lambda line: None)
        assert any("no reading in SAYS" in one for one in failures), failures


class TestEveryClaimHasAKey:
    """Rule 3. The words make a claim the block has nothing behind."""

    @pytest.mark.parametrize("line, key", [
        ("Maradona's solo goal", "solo_run"),
        ("Maradona scores from his own half", "own_half"),
        ("Maradona finishes a counter", "play_pattern"),
        ("Maradona goes past Fenwick", "dribbled_past"),
        ("Maradona scores from nine yards", "yards_from_goal"),
        ("Maradona punishes an error", "recovers_error"),
        ("Maradona scores with his left foot", "body_part"),
        ("Maradona scores, set up by Valdano", "assist"),
        ("Maradona's opener", "match_goal_number"),
    ])
    def test_a_claim_with_nothing_behind_it(self, entries, events, line, key):
        hero, goal, these = hero_of(entries, events, ARG_ENG)
        block = {"grounding": {}, "event": dict(hero["event"])}
        failures = []
        check_prose("test", line, block, goal, these,
                    lambda where, why: failures.append(why), lambda line_: None)
        assert any(key in one for one in failures), (line, failures)

    def test_the_penalty_claim_is_backed_by_the_shot_type(self, entries, events):
        """"from the spot" needs no grounding key: the moment's own event
        carries the shot type, which `check_match` reads against the feed."""
        hero, goal, these = hero_of(entries, events, ARG_FRA)
        failures = []
        check_prose("test", "Messi from the spot",
                    {"grounding": {}, "event": {"shot_type": "Penalty"}},
                    goal, these,
                    lambda where, why: failures.append(why), lambda line_: None)
        assert failures == []

        failures = []
        check_prose("test", "Messi from the spot",
                    {"grounding": {}, "event": {"shot_type": "Open Play"}},
                    goal, these,
                    lambda where, why: failures.append(why), lambda line_: None)
        assert any("shot type Penalty" in one for one in failures), failures

    def test_a_claim_written_into_a_line_no_block_stands_behind(
            self, entries, events):
        """The other direction: a description moved out of the two blocks the
        gate reads and into a line it does not. The list card's status is the
        nearest free line to the copy that was removed."""
        entry = copy.deepcopy(entries[ARG_ENG])
        entry["picker"]["status"] = "A solo run from his own half"
        said = run(entry, events[ARG_ENG])
        assert any("no grounding block stands behind" in one for one in said), said

    def test_the_held_lines_are_the_ones_with_blocks(self):
        assert "hero.caption" in HELD_PROSE
        assert "hero.share_text" in HELD_PROSE
        assert "moments[0].title" in HELD_PROSE
        assert "moments[1].body" in HELD_PROSE
        assert "picker.status" not in HELD_PROSE

    def test_every_claim_phrase_names_a_key_something_can_check(self):
        """A phrase pointing at a key with no reading and no event fact would
        be a rule nothing could satisfy."""
        for _, key in CLAIMS:
            assert key in SAYS or key == "shot type Penalty", key


class TestAPlayerNamedIsAPlayerThere:
    """What held the removed broadcast quote, kept for every line."""

    def test_a_name_is_read_part_by_part_rather_than_by_its_last_word(
            self, entries):
        """StatsBomb records both surnames: Valdano is "Jorge Alberto
        Francisco Valdano Castellano" and Messi is "Lionel Andrés Messi
        Cuccittini". Reading the last word would have looked for Castellano
        in a line saying Valdano, which is a check that never fires."""
        from check_match_copy import name_parts

        assert "Valdano" in name_parts("Jorge Alberto Francisco Valdano Castellano")
        assert "Messi" in name_parts("Lionel Andrés Messi Cuccittini")
        assert "Allister" in name_parts("Alexis Mac Allister")
        assert "Mac" not in name_parts("Alexis Mac Allister")

    def test_a_player_from_another_moment(self, entries, events):
        hero, goal, these = hero_of(entries, events, ARG_ENG)
        players = {e["player"]["name"] for e in these if "player" in e}
        failures = []
        check_names("test", "Maradona rounds Shilton and finishes", goal, these,
                    players, lambda where, why: failures.append(why))
        assert failures == [], "Shilton is in that possession"

        failures = []
        check_names("test", "Valdano squares it", goal, these,
                    players, lambda where, why: failures.append(why))
        assert any("Valdano" in one for one in failures), failures

    def test_the_committed_lines_name_only_players_who_were_there(
            self, entries, events):
        for mid in (ARG_ENG, ARG_FRA):
            assert run(copy.deepcopy(entries[mid]), events[mid]) == []
