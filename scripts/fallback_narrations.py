r"""The six fallback narrations, in the repo, re-checked against `data/raw/`.

**The six candidates of the first run of 2026-11-05 were overwritten.** The
review file outside the repo is named for the day, both runs of that day wrote
it, and `merged` in `scripts/narrator_candidates.py` carries across only the
slots a run did not produce: the zones run produced all six, so all six were
replaced. Nothing in the repo held them, so there was no second copy to read
them back from. Shawn had read them aloud and still had them; they are below,
verbatim, in his spelling and punctuation.

**So a run is never the only copy again.** The six texts are in this module
and the two review files this script writes are committed beside the
generated run reports in `docs/narration_runs/`. A file in the repo survives
a rerun of anything outside it.

**Nothing here calls a model and nothing here is frozen.** The texts are not
generated: they are the ones Shawn kept. What this script does is read them
against the current `app/grounding.py` and say, for each, whether the check
still grounds it, how many claims it looked at, and where the narration puts
the move on the pitch. That answer moves when the check or the zone
vocabulary moves, which is the reason to be able to ask it again.

Run it:

    .\.venv-prelude\Scripts\python.exe -I scripts\fallback_narrations.py

Standard library only. It writes `docs/narration_runs/fallback_2026-11-05.md`
and `docs/narration_runs/fallback_2026-11-05.json`, and exits 1 if any of the
six is refused, so a check change that would cost a fallback is visible
rather than quiet.
"""

import json
import sys
from datetime import date
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# The recorded names carry accents and this script prints them. A Windows
# console is cp1252 by default, which cannot encode "Ángel" as it is spelled.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from app.grounding import check  # noqa: E402
from app.narration_prompt import Facts, facts_from_buildup  # noqa: E402
from app.recorded_names import (  # noqa: E402
    recorded_nicknames,
    recorded_teams,
)
from app.statsbomb_event_feed import StatsBombEventFeed  # noqa: E402
from scripts.hero_candidates import HEROES, moment_at  # noqa: E402
from scripts.narrator_candidates import (  # noqa: E402
    billed_for_slot,
    narrator_for,
    said_who,
    slots_for,
    zones_said,
)

#: Where the two review files go. Not `data/raw/`, which is gitignored and
#: reproducible, and not the review directory outside the repo, which is what
#: a rerun overwrites. Beside the generated run reports, which is where a
#: reader of this repo already looks for what a run produced.
OUT_DIR = ROOT / "docs" / "narration_runs"

#: The day the six were written, which is what names the files. Both runs of
#: 2026-11-05 are that day and these are the first run's.
WRITTEN_ON = "2026-11-05"

#: The six, verbatim as Shawn kept them, by match and slot. One per slot of
#: the two hero goals, which is every slot `hero.voice_for` sends a listener
#: to.
#:
#: **Verbatim means verbatim.** No spacing, hyphen or punctuation of these is
#: tidied here, because what is being preserved is the telling Shawn read
#: aloud and may still pick. "first-time" in the 2022 `buddy_conceded` line
#: and "first time" in the other two are both his.
FALLBACK: dict[tuple[int, str], str] = {
    (3750191, "buddy_scored"): (
        "We won it back through Cuciuffo, who found Enrique and he set up "
        "Maradona; Maradona dribbled past Beardsley, Butcher and Fenwick, "
        "carried it forward into the box, dribbled past Shilton and shot "
        "with his left foot! What a finish!"
    ),
    (3750191, "buddy_conceded"): (
        "Cuciuffo recovered and played it to Enrique, who set up Maradona; "
        "pressed by Beardsley and Reid, Maradona dribbled past Beardsley, "
        "Butcher and Fenwick, carried it forward into the box, slipped past "
        "Shilton and struck with his left foot. Ah, no."
    ),
    (3750191, "storyteller_neutral"): (
        "Cuciuffo recovered and passed to Enrique, who set up Maradona, "
        "pressed by Beardsley and Reid; Maradona dribbled past Beardsley, "
        "Butcher and Fenwick, carried it forward into the box, faced another "
        "press from Butcher, slipped past Shilton and shot with his left "
        "foot. What a moment."
    ),
    (3869685, "buddy_scored"): (
        "We started from our own half, Molina to MacAllister, who fed Messi, "
        "Messi to Álvarez, Álvarez sent a long ball to MacAllister, "
        "MacAllister set up Di María, and he struck with his left foot first "
        "time and it went in! Pure magic!"
    ),
    (3869685, "buddy_conceded"): (
        "Molina to MacAllister, MacAllister to Messi, Messi to Álvarez, "
        "Álvarez sent a long ball to MacAllister, MacAllister set up Di "
        "María in the box and he struck first-time with his left foot. Ah, "
        "no."
    ),
    (3869685, "storyteller_neutral"): (
        "Molina passed forward to MacAllister, who found Messi, who gave it "
        "to Álvarez; Álvarez sent a long ball forward to MacAllister, who "
        "set up Di María, and Di María shot first time with his left foot "
        "and scored. What a moment."
    ),
}

_NOTE = (
    "The six narrations of the first run of 2026-11-05, kept in the repo in "
    "scripts/fallback_narrations.py and re-checked against data/raw/ by that "
    "script. Not generated here and not frozen: app/web/narrations.json is "
    "not written by it."
)


def facts_for(feed: StatsBombEventFeed, match_id: int, minute: int,
              second: int) -> tuple[Facts, object]:
    """The buildup facts for one hero goal, with the names and teams on them.

    The same three arguments `scripts/narrator_candidates.py` builds its
    facts from, so a re-check here reads the passage the run read: the
    recorded nicknames are what four of the 2022 players are called, and the
    fixture's two teams are what lets a zone phrase say "France's half".
    """
    moment = moment_at(feed, match_id, minute, second)
    facts = facts_from_buildup(
        feed.buildup(match_id, moment),
        recorded_nicknames(match_id),
        recorded_teams(match_id),
    )
    return facts, moment


def rechecked() -> list[dict]:
    """Every fallback narration, read against the records, goal by goal."""
    feed = StatsBombEventFeed()
    goals: list[dict] = []
    for year, match_id, minute, second in HEROES:
        facts, moment = facts_for(feed, match_id, minute, second)
        slots: list[dict] = []
        for key, side in slots_for(match_id, moment.team):
            text = FALLBACK[(match_id, key)]
            persona = narrator_for(key)
            result = check(text, facts, persona=persona, side=side)
            slots.append(
                {
                    "slot": key,
                    "narrator": persona.id,
                    "side": side,
                    "text": text,
                    "grounded": result.grounded,
                    "claims_checked": result.checked,
                    "summary": result.summary,
                    "refusals": [
                        str(failure) for failure in result.failures
                    ],
                    "billed_characters": billed_for_slot(
                        match_id, key, text
                    ),
                    "characters": len(text),
                    "words": len(text.split()),
                    "who": said_who(text),
                    "zones": list(zones_said(text, facts)),
                }
            )
        goals.append(
            {
                "year": year,
                "match_id": match_id,
                "minute": minute,
                "second": second,
                "player": moment.player,
                "team": moment.team,
                "opponent": facts.opponent,
                "records": len(facts.facts),
                "slots": slots,
            }
        )
    return goals


def review(goals: Sequence[dict]) -> str:
    """The review file: the six, with what the check says about each.

    Markdown, because a person reads it aloud and picks between these and a
    run's. No em dashes, which `CLAUDE.md` requires of every doc in the repo
    and this one is now in the repo.
    """
    out: list[str] = []
    out.append("# The six fallback narrations, re-checked")
    out.append("")
    out.append("Written by Shawn's reading of the first run of {}, kept "
               "verbatim in scripts/fallback_narrations.py, and re-checked "
               "by that script on {}.".format(WRITTEN_ON,
                                              date.today().isoformat()))
    out.append("")
    out.append("The zones run of {} overwrote these six in the review file "
               "outside the repo, and nothing in the repo held them. They "
               "are here so that a run is never the only copy of a "
               "narration.".format(WRITTEN_ON))
    out.append("")
    out.append("No model was called for this file. Each line was read "
               "against data/raw/ by app/grounding.py as a goal call, in the "
               "persona and for the listening side its slot is written for.")
    out.append("")
    out.append("The billed count is what that one recording would cost, "
               "markup counted and whitespace not, which is the figure IBM "
               "charges.")
    out.append("")
    grounded = sum(
        1 for goal in goals for slot in goal["slots"] if slot["grounded"]
    )
    total = sum(len(goal["slots"]) for goal in goals)
    out.append("**{} of the {} are grounded today.**".format(grounded, total))
    out.append("")
    for goal in goals:
        out.append("## {} ({}:{:02d}, {})".format(
            goal["year"], goal["minute"], goal["second"], goal["player"]
        ))
        out.append("")
        out.append("Match {}, {} records, {} attacking and {} "
                   "defending.".format(
                       goal["match_id"], goal["records"],
                       goal["team"], goal["opponent"],
                   ))
        out.append("")
        out.append("| Slot | Check | Claims | Billed | Places |")
        out.append("| ---- | ----- | -----: | -----: | -----: |")
        for slot in goal["slots"]:
            out.append("| {} | {} | {} | {} | {} |".format(
                slot["slot"],
                "grounded" if slot["grounded"] else "refused",
                slot["claims_checked"],
                slot["billed_characters"],
                len(slot["zones"]),
            ))
        out.append("")
        for slot in goal["slots"]:
            out.append("### {}".format(slot["slot"]))
            out.append("")
            out.append("Written for {}.".format(
                "a fan of {}".format(slot["side"]) if slot["side"]
                else "a listener with no side"
            ))
            out.append("")
            out.append("> {}".format(slot["text"]))
            out.append("")
            out.append("- {}".format(slot["summary"]))
            out.append("- Billed: {} characters for this recording".format(
                slot["billed_characters"]
            ))
            out.append("- Length: {} characters, {} words".format(
                slot["characters"], slot["words"]
            ))
            out.append("- Says \"who\" {}".format(
                "not at all" if not slot["who"]
                else "once" if slot["who"] == 1
                else "{} times".format(slot["who"])
            ))
            out.append("- Places the move {}".format(
                "not at all, which rule 17 asks for two or three of"
                if not slot["zones"]
                else "{} time(s): {}".format(
                    len(slot["zones"]), "; ".join(slot["zones"])
                )
            ))
            for refusal in slot["refusals"]:
                out.append("- **Refused:** {}".format(refusal))
            out.append("")
    return "\n".join(out) + "\n"


def document(goals: Sequence[dict]) -> dict:
    """The same answers as data, for anything that would rather read JSON."""
    return {
        "_note": _NOTE,
        "written_on": WRITTEN_ON,
        "rechecked_on": date.today().isoformat(),
        "goals": list(goals),
    }


def main(argv: Sequence[str]) -> int:
    if argv:
        raise SystemExit(
            "fallback_narrations.py takes no arguments; it reads the six "
            "narrations in the module and the records in data/raw/"
        )
    goals = rechecked()
    refused = 0
    for goal in goals:
        print("{} match {} {}:{:02d} ({} against {})".format(
            goal["year"], goal["match_id"], goal["minute"], goal["second"],
            goal["team"], goal["opponent"],
        ))
        for slot in goal["slots"]:
            print("  {}: {}".format(slot["slot"], slot["summary"]))
            print("    billed {}, {} characters, \"who\" x{}, {} "
                  "place(s){}".format(
                      slot["billed_characters"], slot["characters"],
                      slot["who"], len(slot["zones"]),
                      ": " + "; ".join(slot["zones"]) if slot["zones"]
                      else "",
                  ))
            print("    | {}".format(slot["text"]))
            if not slot["grounded"]:
                refused += 1
        print()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "fallback_{}.md".format(WRITTEN_ON)
    data = OUT_DIR / "fallback_{}.json".format(WRITTEN_ON)
    path.write_text(review(goals), encoding="utf-8", newline="\n")
    data.write_text(
        json.dumps(document(goals), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print("wrote {}".format(path))
    print("wrote {}".format(data))
    print("Nothing is frozen. These six are what a run is picked against.")
    if refused:
        print()
        print("{} of the six is refused by the check as it stands "
              "today.".format(refused))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
