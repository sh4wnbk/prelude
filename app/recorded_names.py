"""The name a player is recorded under, and the shorter one recorded beside it.

StatsBomb records two names per player, in two different files. The event feed
carries `player.name`, the full legal name: `Diego Armando Maradona`,
`Lionel Andrés Messi Cuccittini`. The lineups file carries `player_nickname`
beside it, which is the name the same source writes that player under in
short: `Lionel Messi`, `Ángel Di María`.

**Why the short one matters.** The narration is read aloud. A hero narration
tells a whole move, so it names the scorer once per step, and the frozen 1986
narration says `Diego Armando Maradona` six times over. Nothing about that is
ungrounded, and all of it is how nobody says it.

**It is read, not chosen.** The nickname used here is the one in
`data/raw/lineups/<match_id>.json`, and there is no fallback that shortens a
name this file does not shorten: a surname picked out of a full name would be
this repo's judgement about what a player is called, and `CLAUDE.md` allows
only what the data records. So a player with no recorded nickname keeps their
full recorded name, however well known the short form is. **Maradona is one of
those**: the 1986 lineups file records no nickname for him, so the 1986
narration still says the full name.

It is also not a fourth input. The lineups file is the same StatsBomb open data
as the event feed, for the same match, fetched by the same script.

Standard library only, like the rest of `app/`.
"""

import json
from pathlib import Path
from typing import Mapping

_RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


def lineups_path(match_id: int) -> Path:
    """Where `scripts/fetch_statsbomb.py` puts a match's lineups file."""
    return _RAW / "lineups" / f"{match_id}.json"


def recorded_nicknames(match_id: int) -> Mapping[str, str]:
    """Full recorded name to recorded nickname, for every player who has one.

    A player with no `player_nickname`, or one recorded as the full name
    again, is left out rather than mapped to itself: the absence is what tells
    a caller there is no shorter name to use.

    Raises if the lineups file is missing, rather than quietly returning
    nothing. A silent empty mapping would look exactly like a match whose
    players all happen to have no nickname, and the two want different
    answers: re-run `scripts/fetch_statsbomb.py` for the first.
    """
    path = lineups_path(match_id)
    if not path.is_file():
        raise FileNotFoundError(
            f"{path} is missing, so no recorded nickname can be read for "
            f"match {match_id}: run scripts/fetch_statsbomb.py"
        )
    teams = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for team in teams:
        for player in team["lineup"]:
            full = player["player_name"]
            short = player.get("player_nickname")
            if not short or short == full:
                continue
            out[full] = short
    return out
