"""Write or check the served-match list inside docs/orchestrate_agent.md.

The agent's pasteable instructions carry the matches the API serves. They did
not until 2026-11-07, and the first live test of the agent showed what that
costs: asked about a match, it asked the fan for a StatsBomb match id, because
nothing in its context said which matches exist. A fan in a stadium does not
know that number. The list is what the agent reads instead.

Every value on the list is read off a source rather than typed here.

`app/web/matches.json` is the service's own list, and `app/api.py` answers for
exactly its `match_id` values, so the id and the two team names come from
there. The competition, the season, the stage and the date are not in that
file. They are in the StatsBomb match files under `data/raw/matches/`, which
`scripts/fetch_statsbomb.py` downloads and which is where the two match ids
were resolved from in the first place, so they are read from the play data.

The list lives inside the one fenced block in the doc, because the agent needs
the ids and that block is the whole of what it is given.
`tests/test_orchestrate_agent.py::TestTheMatchesItServes` holds the list in the
doc to what this script builds, so the file cannot drift from the two sources
without the suite saying so.

Usage:
    python scripts/write_served_matches.py              # rewrite the list
    python scripts/write_served_matches.py --check      # exit 1 if it differs
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MATCHES_FILE = ROOT / "app" / "web" / "matches.json"
RAW_MATCHES = ROOT / "data" / "raw" / "matches"
DOC = ROOT / "docs" / "orchestrate_agent.md"

#: The line the list sits under, inside the fenced block. The script keys on
#: this rather than on a comment marker: a comment would be pasted into the
#: agent along with everything else in the block, and the block is instruction
#: text, not a file.
ANCHOR = "The matches you serve, with the id both tools take:"

#: What a generated line starts with. The run of them under the anchor is the
#: region this script owns.
BULLET = "- "


class NoPlayData(RuntimeError):
    """`data/raw/` is absent or does not hold one of the two matches."""


def raw_matches() -> dict[int, dict]:
    """Every StatsBomb match record under `data/raw/matches/`, by match id."""
    if not RAW_MATCHES.is_dir():
        raise NoPlayData(
            f"{RAW_MATCHES.relative_to(ROOT).as_posix()} is not there. "
            "Run scripts/fetch_statsbomb.py first; data/raw is gitignored and "
            "reproducible."
        )
    found = {}
    for path in sorted(RAW_MATCHES.glob("*/*.json")):
        with path.open(encoding="utf-8") as handle:
            for record in json.load(handle):
                found[record["match_id"]] = record
    return found


def rows() -> list[str]:
    """One line per match the service serves, in `matches.json` order."""
    with MATCHES_FILE.open(encoding="utf-8") as handle:
        served = json.load(handle)["matches"]
    raw = raw_matches()

    lines = []
    for entry in served:
        match_id = entry["match_id"]
        record = raw.get(match_id)
        if record is None:
            raise NoPlayData(
                f"match {match_id} is served by app/web/matches.json and is "
                "in no match file under data/raw/matches/. Run "
                "scripts/fetch_statsbomb.py."
            )
        lines.append(
            "{}{}: {} vs {}, {} {}, {}, {}".format(
                BULLET,
                match_id,
                entry["home_team"],
                entry["away_team"],
                record["competition"]["competition_name"],
                record["season"]["season_name"],
                record["competition_stage"]["name"],
                record["match_date"],
            )
        )
    return lines


def rewrite(text: str, lines: list[str]) -> str:
    """`text` with the run of bullets under the anchor replaced by `lines`."""
    source = text.split("\n")
    try:
        at = next(i for i, line in enumerate(source) if line.strip() == ANCHOR)
    except StopIteration:
        raise RuntimeError(
            f"{DOC.relative_to(ROOT).as_posix()} has no line reading "
            f"{ANCHOR!r}, so there is nowhere to write the list."
        ) from None

    start = at + 1
    while start < len(source) and not source[start].strip():
        start += 1
    end = start
    while end < len(source) and source[end].startswith(BULLET):
        end += 1
    if end == start:
        raise RuntimeError(
            f"{DOC.relative_to(ROOT).as_posix()} has no list under "
            f"{ANCHOR!r}. Leave one line starting {BULLET!r} there for this "
            "script to replace."
        )
    return "\n".join(source[:start] + lines + source[end:])


def current(text: str) -> list[str]:
    """The lines the doc holds now, for `--check` and for the suite."""
    source = text.split("\n")
    at = next(
        (i for i, line in enumerate(source) if line.strip() == ANCHOR), None
    )
    if at is None:
        return []
    start = at + 1
    while start < len(source) and not source[start].strip():
        start += 1
    end = start
    while end < len(source) and source[end].startswith(BULLET):
        end += 1
    return source[start:end]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if the list in the doc differs from the sources.",
    )
    args = parser.parse_args()

    try:
        lines = rows()
    except NoPlayData as problem:
        print(f"no play data: {problem}")
        return 1

    text = DOC.read_text(encoding="utf-8")
    if args.check:
        held = current(text)
        if held == lines:
            print(f"{len(lines)} match(es) listed, and the list is the sources'")
            return 0
        print("the list in the doc is not what the sources say:")
        for line in lines:
            print(f"  want {line}")
        for line in held:
            print(f"  have {line}")
        return 1

    DOC.write_text(rewrite(text, lines), encoding="utf-8", newline="\n")
    print(f"{DOC.relative_to(ROOT).as_posix()}: {len(lines)} match(es) written")
    for line in lines:
        print(f"  {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
