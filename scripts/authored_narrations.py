r"""The six hero narrations the team wrote, re-checked against `data/raw/`.

**These six were written by the team and not by a model.** At
`reasoning_effort` low the model would not place the move on the pitch: the
run of 2026-11-05 produced nine grounded 1986 tellings and not one of them
said a band or a side, so `places_missing` refused eleven of the fourteen
candidates it reached. The answer Shawn settled on is that the writing is the
team's and the verifying is Prelude's: each of these six goes through
`app/grounding.py` as a goal call, in the persona and for the listening side
its slot is written for, exactly as a model's candidate does.

**"Verified from play data" still means what it says.** The label is about
the claims and not about the author: every claim in a line here traces to a
record in `data/raw/`, and the check is what proves it. What changes is who
wrote the words, and that is disclosed rather than implied: `AUTHORSHIP` is
carried beside every one of them, `README.md` says it in the present tense,
and the model runs stay in `docs/narration_runs/` as the evidence of the
pipeline.

**Two things are asked of a telling beyond grounding**, and they are the
run's acceptance rules rather than the check's: `places_missing`, which wants
at least `PLACES_WANTED` places and, in a passage holding a long ball, one
saying where it was struck; and `opener_missing`, which wants the first word
to name a player, a team or a country the records hold. All three answers are
reported per slot here.

This script calls no model and freezes nothing. Run it:

    .\.venv-prelude\Scripts\python.exe -I scripts\authored_narrations.py

Standard library only. It writes `docs/narration_runs/authored_2026-11-07.md`
and the same answers as JSON beside it, and exits 1 if any of the six is
refused by any of the three, so a check change that would cost a hero
narration is visible rather than quiet.
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
from app.narration_prompt import Facts  # noqa: E402
from app.statsbomb_event_feed import StatsBombEventFeed  # noqa: E402
from scripts.fallback_narrations import facts_for  # noqa: E402
from scripts.hero_candidates import HEROES  # noqa: E402
from scripts.narrator_candidates import (  # noqa: E402
    billed_for_slot,
    narrator_for,
    opener_missing,
    places_missing,
    said_who,
    slots_for,
    zones_said,
)

#: Where the two review files go. Beside the generated run reports, which is
#: where a reader of this repo already looks for what a run produced.
OUT_DIR = ROOT / "docs" / "narration_runs"

#: The day the six were written into the repo, which is what names the files.
WRITTEN_ON = "2026-11-07"

#: Who wrote them. One string, used everywhere the authorship is stated, so a
#: reader of the frozen file, the review file and the JSON sees one answer.
AUTHOR = "the team"

#: The authorship, as a sentence a reader cannot take for model output. It is
#: carried beside every frozen narration and
#: `tests/test_authored_narrations.py` fails if one loses it.
AUTHORSHIP = "written by the team, verified by the grounding check"

#: The six, verbatim as Shawn wrote them, by match and slot. One per slot of
#: the two hero goals, which is every slot `hero.voice_for` sends a listener
#: to.
#:
#: **Verbatim means verbatim**, with one thing settled before they arrived:
#: the apostrophes are straight. A curly one would reach the speech service as
#: written, and `app/plain_characters.py` rewrites it for the reading rather
#: than for the recording.
AUTHORED: dict[tuple[int, str], str] = {
    (3750191, "storyteller_neutral"): (
        "Cuciuffo won it back deep in his own half, and Enrique played it to "
        "Maradona just inside his own half. He went past Beardsley there, "
        "carried it on into the final third, beat Butcher on the right and "
        "Fenwick on the edge of the box, then took it into the box, slipped "
        "past Shilton and scored with his left foot. What a moment."
    ),
    (3750191, "buddy_scored"): (
        "Cuciuffo won it back deep in our own half, Enrique found Maradona "
        "just inside his own half, and from there it was all him: past "
        "Beardsley, on into the final third, past Butcher on the right, past "
        "Fenwick on the edge of the box, into the box, past Shilton, and he "
        "scored with his left foot! What a finish!"
    ),
    (3750191, "buddy_conceded"): (
        "Maradona picked it up just inside his own half, and though "
        "Beardsley and Reid pressed him, he went past Beardsley there, past "
        "Butcher in the final third on the right and past Fenwick on the "
        "edge of the box, then got past Shilton in the box and scored with "
        "his left foot."
    ),
    (3869685, "storyteller_neutral"): (
        "Argentina were on the counter when Molina, deep in his own half on "
        "the right, found MacAllister. He played it to Messi, Messi moved it "
        "on to Álvarez, and Álvarez, just inside France's half on "
        "the right, hit a long ball forward to MacAllister again on the edge "
        "of the box. He set up Di María in the box, and Di María "
        "finished first time with his left foot. What a finish."
    ),
    (3869685, "buddy_scored"): (
        "Molina started it deep in our own half, on to MacAllister, "
        "MacAllister to Messi, Messi on to Álvarez, and from just "
        "inside France's half on the right, Álvarez hit a long ball "
        "forward to MacAllister on the edge of the box. He set up Di "
        "María in the box, Di María hit it first time with his "
        "left foot, and it went in! Oh, lovely!"
    ),
    (3869685, "buddy_conceded"): (
        "Molina started it deep in their own half, on to MacAllister, "
        "MacAllister to Messi, Messi to Álvarez, and Álvarez, just "
        "inside our half on the right, hit a long ball forward to "
        "MacAllister on the edge of the box. He set up Di María in the "
        "box, and Di María hit it first time with his left foot. Ah, "
        "no."
    ),
}

_NOTE = (
    "The six hero narrations, written by the team and kept verbatim in "
    "scripts/authored_narrations.py, re-checked against data/raw/ by that "
    "script. No model wrote them and no model was called for this file. The "
    "model runs are in docs/narration_runs/ beside it."
)


def answers(facts: Facts, match_id: int, key: str, side: str | None) -> dict:
    """What the three rules say about one narration, as data.

    Grounding first, because it is the one that decides whether the line may
    carry the label, and then the two acceptance rules the run applies to a
    candidate: the places and the opener.
    """
    text = AUTHORED[(match_id, key)]
    persona = narrator_for(key)
    result = check(text, facts, persona=persona, side=side)
    return {
        "slot": key,
        "narrator": persona.id,
        "side": side,
        "author": AUTHOR,
        "authorship": AUTHORSHIP,
        "text": text,
        "grounded": result.grounded,
        "claims_checked": result.checked,
        "summary": result.summary,
        "refusals": [str(failure) for failure in result.failures],
        "missing_places": places_missing(text, facts),
        "missing_opener": opener_missing(text, facts),
        "billed_characters": billed_for_slot(match_id, key, text),
        "characters": len(text),
        "words": len(text.split()),
        "who": said_who(text),
        "zones": list(zones_said(text, facts)),
    }


def rechecked() -> list[dict]:
    """Every authored narration, read against the records, goal by goal."""
    feed = StatsBombEventFeed()
    goals: list[dict] = []
    for year, match_id, minute, second in HEROES:
        facts, moment = facts_for(feed, match_id, minute, second)
        slots = [
            answers(facts, match_id, key, side)
            for key, side in slots_for(match_id, moment.team)
        ]
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


def held(slot: dict) -> bool:
    """Whether one narration passed all three."""
    return (
        slot["grounded"]
        and not slot["missing_places"]
        and not slot["missing_opener"]
    )


def review(goals: Sequence[dict]) -> str:
    """The review file: the six, with what each of the three rules says.

    Markdown, because a person reads it. No em dashes, which `CLAUDE.md`
    requires of every doc in the repo.
    """
    out: list[str] = []
    out.append("# The six hero narrations, written by the team and checked")
    out.append("")
    out.append("Written by {} and kept verbatim in "
               "scripts/authored_narrations.py. Re-checked by that script on "
               "{}.".format(AUTHOR, date.today().isoformat()))
    out.append("")
    out.append("No model wrote these and no model was called for this file. "
               "Each line was read against data/raw/ by app/grounding.py as "
               "a goal call, in the persona and for the listening side its "
               "slot is written for, and then by the two acceptance rules a "
               "candidate meets: the places and the opener.")
    out.append("")
    out.append("Every one of them is {}. The model runs are in "
               "docs/narration_runs/ beside this file, which is where the "
               "pipeline's own output stays.".format(AUTHORSHIP))
    out.append("")
    out.append("The billed count is what that one recording would cost, "
               "markup counted and whitespace not, which is the figure IBM "
               "charges.")
    out.append("")
    passed = sum(1 for goal in goals for slot in goal["slots"] if held(slot))
    total = sum(len(goal["slots"]) for goal in goals)
    out.append("**{} of the {} pass all three today.**".format(passed, total))
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
        out.append("| Slot | Check | Places | Opener | Claims | Billed |")
        out.append("| ---- | ----- | ------ | ------ | -----: | -----: |")
        for slot in goal["slots"]:
            out.append("| {} | {} | {} | {} | {} | {} |".format(
                slot["slot"],
                "grounded" if slot["grounded"] else "refused",
                "{} said".format(len(slot["zones"]))
                if not slot["missing_places"] else "refused",
                "ok" if not slot["missing_opener"] else "refused",
                slot["claims_checked"],
                slot["billed_characters"],
            ))
        out.append("")
        for slot in goal["slots"]:
            out.append("### {}".format(slot["slot"]))
            out.append("")
            out.append("Written for {}, by {}.".format(
                "a fan of {}".format(slot["side"]) if slot["side"]
                else "a listener with no side",
                slot["author"],
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
                "not at all"
                if not slot["zones"]
                else "{} time(s): {}".format(
                    len(slot["zones"]), "; ".join(slot["zones"])
                )
            ))
            out.append("- Opens on \"{}\"".format(slot["text"].split()[0]))
            for refusal in slot["refusals"]:
                out.append("- **Refused by the check:** {}".format(refusal))
            if slot["missing_places"]:
                out.append("- **Refused for places:** it {}".format(
                    slot["missing_places"]
                ))
            if slot["missing_opener"]:
                out.append("- **Refused for the opener:** it {}".format(
                    slot["missing_opener"]
                ))
            out.append("")
    return "\n".join(out) + "\n"


def document(goals: Sequence[dict]) -> dict:
    """The same answers as data, for anything that would rather read JSON."""
    return {
        "_note": _NOTE,
        "author": AUTHOR,
        "authorship": AUTHORSHIP,
        "written_on": WRITTEN_ON,
        "rechecked_on": date.today().isoformat(),
        "goals": list(goals),
    }


def main(argv: Sequence[str]) -> int:
    if argv:
        raise SystemExit(
            "authored_narrations.py takes no arguments; it reads the six "
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
            print("    opener: {}".format(
                slot["missing_opener"] or "opens on \"{}\"".format(
                    slot["text"].split()[0]
                )
            ))
            if slot["missing_places"]:
                print("    places: {}".format(slot["missing_places"]))
            for refusal in slot["refusals"]:
                print("    REFUSED: {}".format(refusal))
            print("    | {}".format(slot["text"]))
            if not held(slot):
                refused += 1
        print()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "authored_{}.md".format(WRITTEN_ON)
    data = OUT_DIR / "authored_{}.json".format(WRITTEN_ON)
    path.write_text(review(goals), encoding="utf-8", newline="\n")
    data.write_text(
        json.dumps(document(goals), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print("wrote {}".format(path))
    print("wrote {}".format(data))
    print("{}. Nothing is frozen by this script.".format(AUTHORSHIP))
    if refused:
        print()
        print("{} of the six does not pass all three today.".format(refused))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
