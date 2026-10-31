"""Tests for `scripts/freeze_narrations.py --pick`, which freezes a choice.

No model is called and no connection is opened: the pick path exists precisely
because the words already exist. `tests/conftest.py` fails the suite if
anything reaches the network, and nothing here writes
`app/web/narrations.json` either. Every test builds its own candidates
document in a temporary directory.

**What this path is for.** `freeze_narrations.py --confirm` generates a
narration and keeps the first that passes. Task 7 generated several per goal
instead, for Shawn to choose from, so there has to be a way to freeze the one
he chose rather than a fresh one the model happens to write next. The chosen
words are committed as what a judge hears under "Verified from play data", so
this path re-reads them against `data/raw/` rather than trusting the verdict
recorded in the candidates file.

The fact numbers and the narration text here are real: the 2022 text is one of
the candidates the run of 2026-10-30 produced, which keeps the test honest
about the shape this path actually receives.
"""

import json
from pathlib import Path

import pytest

from app.grounding import strip_citations
from scripts.freeze_narrations import (
    chosen,
    freeze_picked,
    main,
    newest_candidates,
    parse_pick,
    read_candidates,
)

ROOT = Path(__file__).resolve().parent.parent

MATCH_1986 = 3750191
MATCH_2022 = 3869685

# One of the candidates the live run kept for each goal, tagged as the check
# passed it. The 1986 one is candidate 3 and the 2022 one is candidate 4.
TAGGED_1986 = (
    "[1, 2, 3] José Luis Cuciuffo recovered the ball, carried the ball "
    "and passed at 54:02.\n"
    "[4, 5, 6] Héctor Adolfo Enrique received the ball, carried the "
    "ball and passed.\n"
    "[7, 8] Diego Armando Maradona received the ball and carried the ball.\n"
    "[10, 11, 12] Diego Armando Maradona dribbled past Peter Beardsley.\n"
    "[14, 15, 16] Diego Armando Maradona dribbled past Terry Butcher.\n"
    "[17, 18, 19] Diego Armando Maradona dribbled past Terry Fenwick.\n"
    "[21, 22, 23] Diego Armando Maradona dribbled past Peter Shilton.\n"
    "[24] Diego Armando Maradona shot and scored."
)

TAGGED_2022 = (
    "[1] Nahuel Molina Lucero passed at 35:12.\n"
    "[2, 3] Alexis Mac Allister received the ball and passed.\n"
    "[4, 5, 6] Lionel Andrés Messi Cuccittini received the ball, "
    "carried it and passed.\n"
    "[7, 8, 9] Julián Álvarez received the ball, carried it and "
    "passed.\n"
    "[10, 11] Alexis Mac Allister received the ball and passed.\n"
    "[12] Ángel Fabián Di María Hernández received the "
    "ball.\n"
    "[13] Ángel Fabián Di María Hernández shot and "
    "scored."
)


def candidate(slot: int, tagged: str) -> dict:
    return {
        "slot": slot,
        "text": strip_citations(tagged),
        "tagged_text": tagged,
        "attempt": 1,
        "first_attempt_grounded": True,
        "claims_checked": 97,
        "billed_characters": 1491,
        "coverage": {},
    }


def document(**overrides) -> dict:
    doc = {
        "_note": "candidates",
        "generated_on": "2026-10-30",
        "model": "openai/gpt-oss-120b",
        "provider": "watsonx",
        "chat": True,
        "reasoning_effort": "low",
        "max_new_tokens": 2000,
        "decoding": {"temperature": 0.8, "top_p": 0.9, "top_k": 40},
        "goals": [
            {
                "year": 1986,
                "match_id": MATCH_1986,
                "minute": 54,
                "second": 18,
                "player": "Diego Armando Maradona",
                "team": "Argentina",
                "facts": 24,
                "candidates": [
                    candidate(3, TAGGED_1986),
                    candidate(5, TAGGED_1986),
                ],
                "dropped": [],
            },
            {
                "year": 2022,
                "match_id": MATCH_2022,
                "minute": 35,
                "second": 22,
                "player": "Ángel Fabián Di María Hernández",
                "team": "Argentina",
                "facts": 13,
                "candidates": [candidate(4, TAGGED_2022)],
                "dropped": [],
            },
        ],
    }
    doc.update(overrides)
    return doc


@pytest.fixture
def written(tmp_path):
    """A candidates document on disk, the way a run leaves one."""
    def write(doc=None, name="hero_candidates_2026-10-30.json"):
        path = tmp_path / name
        path.write_text(
            json.dumps(doc if doc is not None else document(), indent=2),
            encoding="utf-8",
        )
        return path
    return write


class TestParsingAPick:
    def test_a_match_and_a_slot(self):
        assert parse_pick("3750191=3") == (3750191, 3)

    @pytest.mark.parametrize(
        "value", ["3750191", "3750191=3=1", "", "x=3", "3750191=x"]
    )
    def test_anything_else_is_refused(self, value):
        with pytest.raises(SystemExit):
            parse_pick(value)


class TestReadingTheCandidatesFile:
    def test_a_missing_file_is_refused(self, tmp_path):
        with pytest.raises(SystemExit) as raised:
            read_candidates(tmp_path / "nothing.json")
        assert "does not exist" in str(raised.value)

    def test_a_bare_list_of_goals_is_refused(self, written):
        """The shape the first run wrote. A freeze records which model wrote
        the words, and a bare list does not say."""
        path = written(doc=[{"match_id": MATCH_1986}])
        with pytest.raises(SystemExit) as raised:
            read_candidates(path)
        assert "not a candidates document" in str(raised.value)

    @pytest.mark.parametrize("field", ["model", "provider", "generated_on"])
    def test_a_document_missing_its_provenance_is_refused(
        self, written, field
    ):
        doc = document()
        del doc[field]
        with pytest.raises(SystemExit) as raised:
            read_candidates(written(doc=doc))
        assert field in str(raised.value)

    def test_the_newest_file_in_a_directory_is_the_one_picked_from(
        self, tmp_path, written
    ):
        written(name="hero_candidates_2026-10-28.json")
        newest = written(name="hero_candidates_2026-10-30.json")
        assert newest_candidates(tmp_path) == newest

    def test_a_directory_with_no_candidates_is_refused(self, tmp_path):
        with pytest.raises(SystemExit) as raised:
            newest_candidates(tmp_path)
        assert "nothing to pick from" in str(raised.value)


class TestChoosing:
    """Four ways a pick can be wrong, all refused before anything is written."""

    def test_both_goals_picked_is_accepted(self):
        picked = chosen(document(), ["3750191=3", "3869685=4"])
        assert [goal["match_id"] for goal, _ in picked] == [
            MATCH_1986,
            MATCH_2022,
        ]
        assert [one["slot"] for _, one in picked] == [3, 4]

    def test_the_order_is_the_hero_order_not_the_argument_order(self):
        picked = chosen(document(), ["3869685=4", "3750191=3"])
        assert [goal["match_id"] for goal, _ in picked] == [
            MATCH_1986,
            MATCH_2022,
        ]

    def test_one_goal_left_unpicked_is_refused(self):
        """Both are frozen together, so one card does not end up speaking a
        narration chosen before the other."""
        with pytest.raises(SystemExit) as raised:
            chosen(document(), ["3750191=3"])
        assert "no pick for match 3869685" in str(raised.value)

    def test_a_goal_picked_twice_is_refused(self):
        with pytest.raises(SystemExit) as raised:
            chosen(document(), ["3750191=3", "3750191=5", "3869685=4"])
        assert "picked twice" in str(raised.value)

    def test_a_goal_that_is_not_a_hero_is_refused(self):
        with pytest.raises(SystemExit) as raised:
            chosen(document(), ["999=1", "3750191=3", "3869685=4"])
        assert "not one of the hero goals" in str(raised.value)

    def test_a_slot_that_is_not_in_the_file_is_refused(self):
        """And it says which slots are there: the kept candidates are not
        numbered one to five, because a dropped slot leaves a gap."""
        with pytest.raises(SystemExit) as raised:
            chosen(document(), ["3750191=9", "3869685=4"])
        message = str(raised.value)
        assert "has no candidate 9" in message
        assert "it has 3, 5" in message


class TestFreezingThePick:
    """The document written, and the two things re-checked before it is."""

    def test_it_writes_both_narrations_with_their_provenance(self, written):
        path = written()
        doc = read_candidates(path)
        out = freeze_picked(doc, path, ["3750191=3", "3869685=4"])
        assert set(out["narrations"]) == {str(MATCH_1986), str(MATCH_2022)}
        for match_id in (MATCH_1986, MATCH_2022):
            entry = out["narrations"][str(match_id)]
            assert entry["source"] == "model"
            assert entry["model"] == "openai/gpt-oss-120b"
            assert entry["provider"] == "watsonx"
            assert entry["labelled"] is True
            assert entry["check"]["grounded"] is True
            assert entry["check"]["failures"] == []

    def test_it_records_which_candidate_was_picked(self, written):
        """A narration chosen from several is a different claim from one
        accepted because it was the first that passed."""
        path = written()
        out = freeze_picked(
            read_candidates(path), path, ["3750191=3", "3869685=4"]
        )
        picked = out["narrations"][str(MATCH_1986)]["picked"]
        assert picked["slot"] == 3
        assert picked["kept_for_this_goal"] == 2
        assert picked["from"] == path.name
        assert picked["generated_on"] == "2026-10-30"

    def test_the_text_it_writes_is_the_tagged_text_without_citations(
        self, written
    ):
        path = written()
        out = freeze_picked(
            read_candidates(path), path, ["3750191=3", "3869685=4"]
        )
        for match_id in (MATCH_1986, MATCH_2022):
            entry = out["narrations"][str(match_id)]
            assert entry["text"] == strip_citations(entry["tagged_text"])
            assert "[" not in entry["text"]

    def test_every_cited_fact_leads_back_to_an_event_id(self, written):
        path = written()
        out = freeze_picked(
            read_candidates(path), path, ["3750191=3", "3869685=4"]
        )
        for match_id in (MATCH_1986, MATCH_2022):
            cited = out["narrations"][str(match_id)]["cited_facts"]
            assert cited
            for record in cited:
                assert record["event_id"]
                assert record["player"]
                assert record["action"]

    def test_a_candidate_that_does_not_pass_the_check_stops_the_freeze(
        self, written
    ):
        """The verdict in the candidates file is not the verdict: these words
        are about to be committed as grounded, so they are re-read against
        data/raw/. Here the last sentence cites a fact that is not the shot."""
        doc = document()
        broken = TAGGED_1986.replace(
            "[24] Diego Armando Maradona shot and scored.",
            "[1] Diego Armando Maradona shot and scored.",
        )
        doc["goals"][0]["candidates"] = [candidate(3, broken)]
        path = written(doc=doc)
        with pytest.raises(SystemExit) as raised:
            freeze_picked(read_candidates(path), path, ["3750191=3", "3869685=4"])
        assert "does not pass the check against data/raw/" in str(raised.value)

    def test_a_text_that_is_not_its_own_tagged_text_is_refused(self, written):
        """The words checked and the words spoken have to be one text. A
        candidate whose `text` has drifted from its `tagged_text` would get the
        grounding label over something the check never read."""
        doc = document()
        one = candidate(3, TAGGED_1986)
        one["text"] = "Maradona scored."
        doc["goals"][0]["candidates"] = [one]
        path = written(doc=doc)
        with pytest.raises(SystemExit) as raised:
            freeze_picked(read_candidates(path), path, ["3750191=3", "3869685=4"])
        assert "two different texts" in str(raised.value)


class TestThePickPathWritesNothingWithoutConfirm:
    def test_a_pick_without_confirm_writes_nothing(self, written, capsys):
        path = written()
        before = (ROOT / "app" / "web" / "narrations.json").read_text(
            encoding="utf-8"
        )
        assert main(
            ["--pick", "3750191=3", "--pick", "3869685=4",
             "--candidates", str(path)]
        ) == 0
        printed = capsys.readouterr().out
        assert "nothing was written" in printed
        assert "calls    none" in printed
        assert (ROOT / "app" / "web" / "narrations.json").read_text(
            encoding="utf-8"
        ) == before

    def test_it_prints_which_model_wrote_the_words(self, written, capsys):
        path = written()
        main(["--pick", "3750191=3", "--pick", "3869685=4",
              "--candidates", str(path)])
        printed = capsys.readouterr().out
        assert "openai/gpt-oss-120b" in printed
        assert "2026-10-30" in printed

    def test_a_bad_pick_writes_nothing_and_exits(self, written):
        path = written()
        before = (ROOT / "app" / "web" / "narrations.json").read_text(
            encoding="utf-8"
        )
        with pytest.raises(SystemExit):
            main(["--pick", "3750191=9", "--pick", "3869685=4",
                  "--candidates", str(path), "--confirm"])
        assert (ROOT / "app" / "web" / "narrations.json").read_text(
            encoding="utf-8"
        ) == before

    def test_the_generating_path_still_sends_nothing_without_confirm(
        self, capsys
    ):
        """The pick path is an addition and does not change the other one."""
        assert main(["--plan"]) == 0
        printed = capsys.readouterr().out
        assert "nothing was sent" in printed
        assert "at most 6 generations" in printed
