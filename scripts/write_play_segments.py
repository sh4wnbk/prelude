"""Write or check app/web/play_segments.json: each frozen narration's claims, pointed at their records.

For each hero match and each of its frozen slots in `app/web/narrations.json`,
the segments `app/play_segments.py` cuts from the slot's text: which words
stand on which events. Beside them, per match, a `records` map from every
event id a segment names to fields copied unchanged out of
`data/raw/events/<match_id>.json`:

    index         event["index"]
    type          event["type"]["name"]
    team          event["team"]["name"]
    player        event["player"]["name"], or null where the record has none
    location      event["location"], or null where the record has none
    end_location  event["pass" | "carry" | "shot"]["end_location"], or null
                  where the record is none of the three

Nothing is derived: every value is a field of one raw record.

Each slot is `{"segments": [...], "draw_from": {event_id: n}}`. `draw_from`
says, for every record the slot's segments name, the index of the segment at
which that record is first drawn, listed in clock order (the record's own
`index`). The rule, record by record in clock order: the earliest segment that
claims the record and is not earlier than the segment the record before it was
drawn at; where no segment from there on claims it, that floor itself. So the
draw never goes back in time: `draw_from` is non-decreasing in clock order,
and a record a broad early claim also holds ("picked it up" holds the shot)
is still drawn where the play has reached it ("scored").

The facts are built the way `freeze_authored` in `scripts/freeze_narrations.py`
builds them, from its `HEROES`, and each slot is cut in the narrator
`narrator_for(key)` names and for the slot's own `listener_side`, which is
how the check passed it.

Usage:
    .\\.venv-prelude\\Scripts\\python.exe scripts/write_play_segments.py
    .\\.venv-prelude\\Scripts\\python.exe scripts/write_play_segments.py --check
    .\\.venv-prelude\\Scripts\\python.exe scripts/write_play_segments.py --path PATH

`--check` writes nothing and exits 1 if the file is missing or differs from
what would be written, 0 if it matches. Reaches nothing outside the repo.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.narration_prompt import facts_from_buildup  # noqa: E402
from app.play_segments import segments  # noqa: E402
from app.recorded_names import recorded_nicknames, recorded_teams  # noqa: E402
from app.statsbomb_event_feed import StatsBombEventFeed  # noqa: E402
from scripts.freeze_narrations import HEROES, moment_at  # noqa: E402
from scripts.narrator_candidates import narrator_for  # noqa: E402

RAW = ROOT / "data" / "raw"
NARRATIONS = ROOT / "app" / "web" / "narrations.json"
_DEFAULT_PATH = ROOT / "app" / "web" / "play_segments.json"

#: The three record types whose own block carries an `end_location`.
_ENDS_IN = ("pass", "carry", "shot")

_NOTE = (
    "Written by scripts/write_play_segments.py. For each frozen narration, "
    "the words that say an event happened and the events that hold them; "
    "records are fields copied unchanged from data/raw/events/."
)


def _name(event: dict, field: str):
    block = event.get(field)
    return block["name"] if block else None


def _record(event: dict) -> dict:
    end = None
    for field in _ENDS_IN:
        if field in event:
            end = event[field].get("end_location")
            break
    return {
        "index": event["index"],
        "type": _name(event, "type"),
        "team": _name(event, "team"),
        "player": _name(event, "player"),
        "location": event.get("location"),
        "end_location": end,
    }


def draw_from(found: list[dict], records: dict) -> dict:
    """Each record's first segment, in clock order. See the module docstring."""
    named = {event_id for segment in found for event_id in segment["event_ids"]}
    drawn: dict = {}
    floor = 0
    for event_id in sorted(named, key=lambda one: records[one]["index"]):
        claiming = [
            number
            for number, segment in enumerate(found)
            if number >= floor and event_id in segment["event_ids"]
        ]
        floor = claiming[0] if claiming else floor
        drawn[event_id] = floor
    return drawn


def build() -> tuple[dict, list[str]]:
    """The document, and one line per slot saying how many segments it has."""
    frozen = json.loads(NARRATIONS.read_text(encoding="utf-8"))["narrations"]
    feed = StatsBombEventFeed()
    matches: dict = {}
    lines: list[str] = []
    for year, match_id, minute, second in HEROES:
        moment = moment_at(feed, match_id, minute, second)
        facts = facts_from_buildup(
            feed.buildup(match_id, moment),
            recorded_nicknames(match_id),
            recorded_teams(match_id),
        )
        slots = frozen[str(match_id)]["slots"]
        cut: dict = {}
        wanted: set[str] = set()
        for key in sorted(slots):
            slot = slots[key]
            found = segments(
                slot["text"], facts, narrator_for(key), slot["listener_side"]
            )
            cut[key] = found
            for segment in found:
                wanted.update(segment["event_ids"])

        events = json.loads(
            (RAW / "events" / f"{match_id}.json").read_text(encoding="utf-8")
        )
        by_id = {event["id"]: event for event in events}
        missing = sorted(wanted - set(by_id))
        if missing:
            raise SystemExit(
                f"match {match_id}: segments name events not in data/raw/: "
                + ", ".join(missing)
            )
        records = {
            event_id: _record(by_id[event_id])
            for event_id in sorted(wanted, key=lambda one: by_id[one]["index"])
        }
        matches[str(match_id)] = {
            "slots": {
                key: {"segments": found, "draw_from": draw_from(found, records)}
                for key, found in cut.items()
            },
            "records": records,
        }
        for key, slot in matches[str(match_id)]["slots"].items():
            found = slot["segments"]
            lines.append(
                f"{year} match {match_id} {key}: {len(found)} segment(s)"
            )
            for number, segment in enumerate(found):
                drawn = [
                    f"{records[event_id]['index']} {records[event_id]['type']}"
                    for event_id, at in slot["draw_from"].items()
                    if at == number
                ]
                lines.append(
                    f"  [{number}] {segment['said']!r}: "
                    + (", ".join(drawn) if drawn else "no record drawn here")
                )
    return {"_note": _NOTE, "matches": matches}, lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="write nothing; exit 1 if the file is missing or differs",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=_DEFAULT_PATH,
        help="the file to write or check (default: app/web/play_segments.json)",
    )
    args = parser.parse_args()

    document, lines = build()
    for line in lines:
        print(line)
    text = json.dumps(document, indent=2, ensure_ascii=False) + "\n"

    path: Path = args.path
    if args.check:
        if not path.is_file():
            print(f"{path} does not exist")
            return 1
        if path.read_text(encoding="utf-8") != text:
            print(f"{path} differs from what the segments give")
            return 1
        print(f"{path} matches")
        return 0

    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
