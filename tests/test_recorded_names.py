"""Tests for the recorded nicknames read out of the lineups files.

Nothing here is a judgement about what a player should be called. Every
assertion is a value in `data/raw/lineups/`, which
`scripts/fetch_statsbomb.py` downloads, so a test that fails here says either
the file changed or the reader did.

The two matches in the repo give both cases on purpose. The 2022 final records
a nickname for most of its players, including one whose nickname is spelled
differently from the full name rather than merely shorter. The 1986
quarter-final records almost none, and in particular records none for the
scorer of the goal this project is built around.
"""

import json

import pytest

from app.recorded_names import lineups_path, recorded_nicknames

MATCH_1986 = 3750191
MATCH_2022 = 3869685


@pytest.fixture(scope="module")
def nicknames_1986():
    return recorded_nicknames(MATCH_1986)


@pytest.fixture(scope="module")
def nicknames_2022():
    return recorded_nicknames(MATCH_2022)


class TestWhatTheFilesRecord:
    def test_the_2022_final_records_these_four(self, nicknames_2022):
        """The four players in the 35:22 buildup who have one.

        Written out rather than derived, so the test says which names it
        means. They are the names the hero narration for that goal uses.
        """
        assert nicknames_2022["Nahuel Molina Lucero"] == "Nahuel Molina"
        assert nicknames_2022["Alexis Mac Allister"] == "Alexis MacAllister"
        assert (
            nicknames_2022["Lionel Andrés Messi Cuccittini"] == "Lionel Messi"
        )
        assert (
            nicknames_2022["Ángel Fabián Di María Hernández"]
            == "Ángel Di María"
        )

    def test_alvarez_has_none(self, nicknames_2022):
        """The fifth player in that buildup, and the reason the mapping is
        read rather than assumed: four of five is not five of five."""
        assert "Julián Álvarez" not in nicknames_2022

    def test_maradona_has_none(self, nicknames_1986):
        """The 1986 file records no nickname for the scorer.

        So the 1986 narration says "Diego Armando Maradona" in full, however
        well known the short form is, because `CLAUDE.md` allows what the data
        records and nothing else. This is the fact behind that, and it is
        worth a test of its own: it is the one most likely to be assumed away.
        """
        assert "Diego Armando Maradona" not in nicknames_1986

    def test_the_1986_file_does_record_enrique(self, nicknames_1986):
        """It is not that the 1986 file has no nicknames at all.

        Enrique, who passed Maradona the ball, has one. So does the Argentina
        goalkeeper. The file is sparse rather than empty, which is why the
        reader reads it per player.
        """
        assert nicknames_1986["Héctor Adolfo Enrique"] == "Héctor Enrique"
        assert (
            nicknames_1986["Neri Alberto Pumpido Barrinat"] == "Nery Pumpido"
        )


class TestTheReader:
    def test_a_nickname_equal_to_the_full_name_is_left_out(self, tmp_path):
        """Mapping a name to itself would say there is a shorter name when
        there is not, and the absence is what callers read."""
        path = tmp_path / "lineups" / "99.json"
        path.parent.mkdir(parents=True)
        path.write_text(
            json.dumps(
                [
                    {
                        "team_name": "Somewhere",
                        "lineup": [
                            {
                                "player_name": "Alice Example",
                                "player_nickname": "Alice Example",
                            },
                            {
                                "player_name": "Bob Example",
                                "player_nickname": None,
                            },
                            {
                                "player_name": "Carol Example",
                                "player_nickname": "",
                            },
                            {
                                "player_name": "Dan Example",
                                "player_nickname": "Dan",
                            },
                        ],
                    }
                ]
            ),
            encoding="utf-8",
        )
        import app.recorded_names as module

        before = module._RAW
        module._RAW = tmp_path
        try:
            assert dict(recorded_nicknames(99)) == {"Dan Example": "Dan"}
        finally:
            module._RAW = before

    def test_a_missing_file_raises(self, tmp_path):
        """A match with no lineups file is not a match whose players all
        happen to have no nickname, and an empty mapping would read as the
        second. The two want different answers, so this one says so."""
        import app.recorded_names as module

        before = module._RAW
        module._RAW = tmp_path
        try:
            with pytest.raises(FileNotFoundError) as caught:
                recorded_nicknames(12345)
        finally:
            module._RAW = before
        assert "fetch_statsbomb" in str(caught.value)

    def test_the_path_is_under_data_raw(self):
        """Gitignored like the rest of it, and written by the fetch script."""
        path = lineups_path(MATCH_2022)
        assert path.name == "3869685.json"
        assert path.parent.name == "lineups"
        assert path.parent.parent.name == "raw"
