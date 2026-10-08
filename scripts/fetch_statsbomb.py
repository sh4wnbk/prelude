"""Download the StatsBomb open-data files this project needs into data/raw/.

Fetches two matches and their event feeds:

  * 1986 World Cup, Argentina vs England (quarter-final). The match id is
    pinned, since that is the game the project is built around.
  * 2022 World Cup final, resolved at runtime by reading the competition
    and match indexes, so no remembered id is baked in here.

Raw data is gitignored; re-run this script instead of committing it.
"""

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

RAW_BASE = "https://raw.githubusercontent.com/hudl/open-data/master/data"
DATA_RAW = Path(__file__).resolve().parent.parent / "data" / "raw"

WORLD_CUP_COMPETITION_ID = 43
SEASON_1986 = 54
ARGENTINA_ENGLAND_1986 = 3750191


def fetch(rel_path):
    """Download `rel_path` from the open-data repo into data/raw/, return parsed JSON."""
    dest = DATA_RAW / rel_path
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = f"{RAW_BASE}/{rel_path}"

    try:
        with urllib.request.urlopen(url, timeout=120) as response:
            payload = response.read()
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"{url} -> HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"{url} -> {exc.reason}") from exc

    parsed = json.loads(payload)
    dest.write_bytes(payload)
    print(f"{rel_path}  {len(payload):,} bytes")
    return parsed


def find_season_id(competitions, competition_id, season_name):
    for entry in competitions:
        if entry["competition_id"] == competition_id and entry["season_name"] == season_name:
            return entry["season_id"]
    raise SystemExit(f"no season {season_name!r} for competition {competition_id} in competitions.json")


def find_final(matches):
    finals = [m for m in matches if m["competition_stage"]["name"] == "Final"]
    if len(finals) != 1:
        raise SystemExit(f"expected exactly 1 Final, found {len(finals)}")
    return finals[0]


def main():
    # Create the destination up front so the directory exists even if the first
    # download fails; a fresh clone has no data/raw/, since it is gitignored.
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    print(f"data dir  {DATA_RAW}")

    competitions = fetch("competitions.json")

    # 1986: Argentina vs England, pinned.
    matches_1986 = fetch(f"matches/{WORLD_CUP_COMPETITION_ID}/{SEASON_1986}.json")
    pinned = next(
        (m for m in matches_1986 if m["match_id"] == ARGENTINA_ENGLAND_1986),
        None,
    )
    if pinned is None:
        raise SystemExit(f"match {ARGENTINA_ENGLAND_1986} not in matches/{WORLD_CUP_COMPETITION_ID}/{SEASON_1986}.json")
    print(
        f"  1986: {pinned['home_team']['home_team_name']} vs "
        f"{pinned['away_team']['away_team_name']} ({pinned['competition_stage']['name']}, {pinned['match_date']})"
    )
    fetch(f"events/{ARGENTINA_ENGLAND_1986}.json")

    # 2022 final: season and match id both read from the data.
    season_2022 = find_season_id(competitions, WORLD_CUP_COMPETITION_ID, "2022")
    print(f"  2022 season_id resolved to {season_2022}")
    matches_2022 = fetch(f"matches/{WORLD_CUP_COMPETITION_ID}/{season_2022}.json")
    final = find_final(matches_2022)
    print(
        f"  2022 final: {final['home_team']['home_team_name']} vs "
        f"{final['away_team']['away_team_name']} (match_id {final['match_id']}, {final['match_date']})"
    )
    fetch(f"events/{final['match_id']}.json")

    print(f"\ndone -> {DATA_RAW}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
