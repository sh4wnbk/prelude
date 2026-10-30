"""Write or check the orchestrator's opening into each match's hero field.

For each match in app/web/matches.json, finds the hero goal among
StatsBombEventFeed().defining_moments(match_id), counts goals before it to
derive the score before and after, then calls greeting_word and header from
app/orchestrator.py and writes hero.opening = {"greeting": ..., "header": ...}.
Also writes hero.voice_for = {"team_a": key, "team_b": key, "neutral": key},
where each key is default_persona(listener) + "_" + situation(moment, listener).
Sets hero.audio = {} only if it is not already present.

Usage:
    python scripts/write_headers.py              # write openings to the file
    python scripts/write_headers.py --check      # exit 1 if any opening or voice_for drifts
    python scripts/write_headers.py --path PATH  # use a different matches.json
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.delivery import situation
from app.orchestrator import default_persona, greeting_word, header
from app.orchestrator_contract import (
    NEUTRAL,
    TEAM_A,
    TEAM_B,
    Event,
    Listener,
    ScoringMoment,
)
from app.statsbomb_event_feed import StatsBombEventFeed

_DEFAULT_PATH = ROOT / "app" / "web" / "matches.json"


def _build_moment(match: dict, feed: StatsBombEventFeed) -> tuple[Event, ScoringMoment]:
    """Compute the Event and ScoringMoment for one match's hero goal."""
    match_id = match["match_id"]
    home_team = match["home_team"]
    away_team = match["away_team"]
    kickoff_str = match["picker"]["kickoff"]  # e.g. "19:00"
    hero_event = match["hero"]["event"]

    # Parse kickoff as a datetime (date is arbitrary; only time matters for greeting).
    kickoff_dt = datetime.strptime(kickoff_str, "%H:%M").replace(
        year=2000, month=1, day=1
    )

    event = Event(
        kickoff=kickoff_dt,
        team_a=home_team,
        team_b=away_team,
        sport="football",
    )

    # Find the hero moment and count goals before it to determine the scores.
    moments = feed.defining_moments(match_id)

    # Locate the hero moment by minute, second, player, and team.
    hero_minute = hero_event["minute"]
    hero_second = hero_event["second"]
    hero_player = hero_event["player"]
    hero_team = hero_event["team"]

    hero_index = None
    for i, m in enumerate(moments):
        if (
            m.minute == hero_minute
            and m.second == hero_second
            and m.player == hero_player
            and m.team == hero_team
        ):
            hero_index = i
            break

    if hero_index is None:
        raise ValueError(
            f"Hero event not found in defining_moments for match {match_id}: "
            f"{hero_player} at {hero_minute}:{hero_second:02d}"
        )

    # Count goals for each team before the hero moment.
    score_before_a = sum(
        1 for m in moments[:hero_index] if m.team == home_team
    )
    score_before_b = sum(
        1 for m in moments[:hero_index] if m.team == away_team
    )

    scoring_side = TEAM_A if hero_team == home_team else TEAM_B
    score_a = score_before_a + (1 if scoring_side == TEAM_A else 0)
    score_b = score_before_b + (1 if scoring_side == TEAM_B else 0)

    moment = ScoringMoment(
        scoring_side=scoring_side,
        minute=hero_minute,
        second=hero_second,
        score_before_a=score_before_a,
        score_before_b=score_before_b,
        score_a=score_a,
        score_b=score_b,
        regulation_minutes=90,
    )

    return event, moment


def _build_opening(event: Event, moment: ScoringMoment) -> dict:
    """Compute {"greeting": ..., "header": ...} from an already-built moment."""
    return {
        "greeting": greeting_word(event),
        "header": header(event, moment),
    }


def _build_voice_keys(moment: ScoringMoment) -> dict:
    """Compute {"team_a": key, "team_b": key, "neutral": key} for one match."""
    result = {}
    for allegiance in (TEAM_A, TEAM_B, NEUTRAL):
        listener = Listener(allegiance=allegiance)
        persona_id = default_persona(listener)
        sit = situation(moment, listener)
        result[allegiance] = persona_id + "_" + sit
    return result


def openings(path: Path = _DEFAULT_PATH) -> dict:
    """Return {match_id: {"greeting": ..., "header": ...}} without writing."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    feed = StatsBombEventFeed()
    result = {}
    for entry in doc["matches"]:
        event, moment = _build_moment(entry, feed)
        result[entry["match_id"]] = _build_opening(event, moment)
    return result


def voice_keys(path: Path = _DEFAULT_PATH) -> dict:
    """Return {match_id: {"team_a": key, "team_b": key, "neutral": key}} without writing."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    feed = StatsBombEventFeed()
    result = {}
    for entry in doc["matches"]:
        _event, moment = _build_moment(entry, feed)
        result[entry["match_id"]] = _build_voice_keys(moment)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if hero.opening or hero.voice_for differs from computed values; write nothing.",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=_DEFAULT_PATH,
        help="Path to matches.json (default: app/web/matches.json).",
    )
    args = parser.parse_args()

    path: Path = args.path
    doc = json.loads(path.read_text(encoding="utf-8"))
    feed = StatsBombEventFeed()

    computed_openings = {}
    computed_voice_keys = {}
    for entry in doc["matches"]:
        event, moment = _build_moment(entry, feed)
        computed_openings[entry["match_id"]] = _build_opening(event, moment)
        computed_voice_keys[entry["match_id"]] = _build_voice_keys(moment)

    if args.check:
        drift = False
        for entry in doc["matches"]:
            mid = entry["match_id"]
            existing_opening = entry.get("hero", {}).get("opening")
            if existing_opening != computed_openings[mid]:
                drift = True
                break
            existing_voice_for = entry.get("hero", {}).get("voice_for")
            if existing_voice_for != computed_voice_keys[mid]:
                drift = True
                break
        sys.exit(1 if drift else 0)

    # Write: update hero.opening and hero.voice_for for each match, nothing else.
    # Set hero.audio = {} only if it is not already present.
    for entry in doc["matches"]:
        mid = entry["match_id"]
        entry["hero"]["opening"] = computed_openings[mid]
        entry["hero"]["voice_for"] = computed_voice_keys[mid]
        if "audio" not in entry["hero"]:
            entry["hero"]["audio"] = {}

    path.write_text(
        json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
