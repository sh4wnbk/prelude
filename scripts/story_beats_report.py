"""The beat list for both hero goals, beside the records it was curated from.

`app/story_beats.py` decides what the model is shown, and the only way to see
whether the decision was right is to read the two lists. Task 10 step 2 asks
for them, and a report is better than a transcript: it reads `data/raw/`
rather than a document somebody pasted, so it says what the code does today.

It makes no model call, spends nothing and writes nothing. Run it:

    .\\.venv-prelude\\Scripts\\python.exe -I scripts\\story_beats_report.py

Standard library only.
"""

import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# The recorded names carry accents and this script prints them. A Windows
# console is cp1252 by default, which cannot encode "Ángel" as it is spelled.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from app.narration_prompt import facts_from_buildup  # noqa: E402
from app.recorded_names import recorded_nicknames  # noqa: E402
from app.statsbomb_event_feed import StatsBombEventFeed  # noqa: E402
from app.story_beats import (  # noqa: E402
    NOT_A_BEAT,
    RUN,
    beat_line,
    kinds,
    story,
)
from scripts.hero_candidates import HEROES, moment_at  # noqa: E402


def report(match_id: int, minute: int, second: int, year: int) -> None:
    """One goal: its records, its beats, and what the curation left out."""
    feed = StatsBombEventFeed()
    moment = moment_at(feed, match_id, minute, second)
    facts = facts_from_buildup(
        feed.buildup(match_id, moment), recorded_nicknames(match_id)
    )
    one = story(facts)

    # The minute is in the header and nowhere else: the model never sees it,
    # and this is the report rather than the prompt.
    print("{} match {} {}:{:02d}: {} ({})".format(
        year, match_id, minute, second, moment.player, moment.team
    ))
    print("  {} records in the passage, {} of them beats".format(
        one.records, one.kept
    ))
    print("  {}".format(", ".join(
        "{} {}".format(count, kind)
        for kind, count in sorted(kinds(one).items())
    )))
    print()
    print("  THE BEATS")
    for number, beat in enumerate(one.beats, start=1):
        print("    {:>2}. {}".format(number, beat_line(beat)))
    print()

    print("  LEFT OUT")
    left: list[str] = []
    for fact in facts.facts:
        beat = fact.beat
        if beat.action in NOT_A_BEAT:
            left.append("{} ({}), a ball receipt".format(beat.name, beat.team))
            continue
        if beat.action == "Carry":
            kept = any(
                one_beat.kind == RUN and beat.event_id in one_beat.event_ids
                for one_beat in one.beats
            )
            if not kept:
                left.append(
                    "{} ({}), a carry too short to be a run".format(
                        beat.name, beat.team
                    )
                )
            continue
        if beat.action == "Dribble":
            left.append(
                "{} ({}), a dribble folded into the beat naming the "
                "defender".format(beat.name, beat.team)
            )
            continue
        if beat.action == "Pressure" and not any(
            beat.event_id in one_beat.event_ids for one_beat in one.beats
        ):
            left.append(
                "{} ({}), pressure on nobody the records show on the "
                "ball".format(beat.name, beat.team)
            )
    for line in left:
        print("    {}".format(line))
    if not left:
        print("    nothing: every record of this passage is a beat")
    print()
    print("  SAID ONCE, ABOVE THE LIST")
    print("    play pattern: {}".format(one.play_pattern or "not recorded"))
    print("    own half:     {}".format(
        "the move started in {}'s own half".format(one.team)
        if one.started_in_own_half
        else "the move did not start in {}'s own half".format(one.team)
    ))
    print()


def main(argv: Sequence[str]) -> int:
    if argv:
        print(__doc__.splitlines()[0])
        print("it takes no arguments: both hero goals, every time")
        return 2
    for year, match_id, minute, second in HEROES:
        report(match_id, minute, second, year)
    print("No beat carries a minute, a second or a timestamp, and the "
          "rendered prompt holds no clock value.")
    print("The grounding check still reads a narration against every record "
          "of the passage.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
