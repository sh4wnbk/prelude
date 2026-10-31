r"""Narrate both hero goals with the active model, and freeze what passes.

The recordings judges hear speak a narration a model wrote, not the fallback
the code assembles. A model writes a different narration every time it is
asked, so the words have to be settled once and committed: this script is the
run that settles them, and `app/web/narrations.json` is what it writes.

**Only a model's narration is kept.** `app/narration.py` falls back to
`template_narration` when three attempts all drift, and that fallback is not
what this is for: a run that reaches it writes nothing and exits 1, so a
frozen narration is always one the model wrote and the grounding check passed.

**The check runs with no persona.** One narration is spoken by all three
voices, and `app/grounding.py` admits the first person only for a partisan
voice over its own side. Checking as nobody in particular is the strict
reading, and it is the only one that is true for every listener who hears
these words.

**The call count is printed before anything is sent.** Two goals, at most
three attempts each, so at most six generations plus one IAM exchange. Nothing
is sent without `--confirm`.

What is written beside each narration is the text as it is shown and voiced,
the tagged text the check actually passed, the facts the narration cited with
the `event_id` each one was read from, and the check's own verdict.
`tests/test_frozen_narrations.py` re-runs the check against `data/raw/` and
fails if a frozen narration stops passing.

Run it:

    .\.venv-prelude\Scripts\python.exe -I scripts\freeze_narrations.py --plan
    .\.venv-prelude\Scripts\python.exe -I scripts\freeze_narrations.py --confirm

Standard library only.
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# The recorded names carry accents and this script prints them. A Windows
# console is cp1252 by default, which cannot encode "Angel" as it is spelled.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from app.grounding import check, sentences, strip_citations  # noqa: E402
from app.narration import MAX_RETRIES, MODEL, narrate  # noqa: E402
from app.narration_config import ACTIVE_CANDIDATE  # noqa: E402
from app.narration_prompt import facts_from_buildup  # noqa: E402
from app.narration_provider import (  # noqa: E402
    COMPARISON_MAX_NEW_TOKENS,
    WatsonxProvider,
)
from app.statsbomb_event_feed import StatsBombEventFeed  # noqa: E402

#: Where the frozen narrations go. Beside `matches.json`, because the browser
#: fetches it from `app/web/` like the rest of the site's copy.
NARRATIONS = ROOT / "app" / "web" / "narrations.json"

#: The two hero goals, by the match they are in and the clock they are at.
#: The same pair `scripts/tts_samples.py` records.
HEROES: tuple[tuple[int, int, int, int], ...] = (
    (1986, 3750191, 54, 18),
    (2022, 3869685, 35, 22),
)

_NOTE = (
    "The narration each hero moment shows and speaks, written by the model in "
    "app/narration_config.py and frozen after it passed the grounding check in "
    "app/grounding.py. Regenerate with scripts/freeze_narrations.py --confirm; "
    "do not edit the text by hand, because the check's verdict recorded here "
    "was reached on these exact words. text is what the card shows and the "
    "voice reads, tagged_text is what the check passed, and cited_facts names "
    "the event_id in data/raw/ behind every fact the narration used. "
    "tests/test_frozen_narrations.py re-runs the check against data/raw/ and "
    "fails if a narration here stops passing."
)


def moment_at(feed: StatsBombEventFeed, match_id: int, minute: int, second: int):
    """The one defining moment at this clock, or a refusal."""
    found = [
        moment
        for moment in feed.defining_moments(match_id)
        if (moment.minute, moment.second) == (minute, second)
    ]
    if len(found) != 1:
        raise SystemExit(
            "match {} has {} goals at {}:{:02d}; the hero is one".format(
                match_id, len(found), minute, second
            )
        )
    return found[0]


def cited_facts(tagged_text: str, facts) -> tuple[list[dict], dict[int, list[int]]]:
    """The facts the narration cited, and which sentence cited which.

    A fact is recorded once however many sentences cite it, with the
    `event_id` it was read from, so a reader can follow any claim in the
    narration back to a record in `data/raw/`.
    """
    by_number = {fact.number: fact for fact in facts.facts}
    per_sentence: dict[int, list[int]] = {}
    used: list[int] = []
    for sentence in sentences(tagged_text):
        per_sentence[sentence.number] = list(sentence.cites)
        for number in sentence.cites:
            if number not in used:
                used.append(number)
    records = []
    for number in sorted(used):
        fact = by_number[number]
        records.append(
            {
                "number": fact.number,
                "text": fact.text,
                "event_id": fact.beat.event_id,
                "clock": fact.beat.clock,
                "player": fact.beat.player,
                "team": fact.beat.team,
                "action": fact.beat.action,
            }
        )
    return records, per_sentence


def freeze(backend: WatsonxProvider) -> dict:
    """Narrate both goals and build the document, or exit on a fallback."""
    feed = StatsBombEventFeed()
    frozen: dict[str, dict] = {}
    for year, match_id, minute, second in HEROES:
        moment = moment_at(feed, match_id, minute, second)
        facts = facts_from_buildup(feed.buildup(match_id, moment))
        print("{} match {} {}:{:02d}: {} ({}), {} facts".format(
            year, match_id, minute, second, moment.player, moment.team,
            len(facts.facts),
        ))
        narrated = narrate(
            feed,
            match_id,
            moment,
            narration_provider=backend,
            max_retries=MAX_RETRIES,
        )
        for attempt in narrated.attempts:
            print("  attempt {} ({}): {}".format(
                attempt.number,
                attempt.source,
                "grounded" if attempt.grounded else "not grounded",
            ))
            print("    | {}".format(attempt.text))
            for failure in attempt.failures:
                print("    x {}".format(failure))
        if narrated.source != MODEL:
            raise SystemExit(
                "match {} reached the template fallback after {} model "
                "attempt(s), so there is no model narration to freeze; "
                "nothing was written".format(match_id, len(narrated.attempts) - 1)
            )
        # Re-checked here rather than trusting the pipeline's verdict, because
        # the verdict is what gets committed beside the words.
        result = check(narrated.tagged_text, facts)
        if not result.grounded:
            raise SystemExit(
                "the narration the pipeline passed does not pass a second "
                "check: " + result.summary
            )
        records, per_sentence = cited_facts(narrated.tagged_text, facts)
        frozen[str(match_id)] = {
            "match_id": match_id,
            "minute": minute,
            "second": second,
            "player": moment.player,
            "team": moment.team,
            "text": narrated.text,
            "tagged_text": narrated.tagged_text,
            "source": narrated.source,
            "model": backend.model,
            "provider": backend.name,
            "attempt": len(narrated.attempts),
            "first_attempt_grounded": narrated.first_attempt_grounded,
            # The permission, not the words. `scripts/scan_copy.py` refuses
            # the grounding label in a copy file, because a data file carries
            # no markup that could place it over anything, and it is right:
            # the label is spelled once in `app/narration.py` and once in the
            # markup that puts it beside this narration.
            "labelled": narrated.labelled,
            "check": {
                "grounded": result.grounded,
                "claims_checked": result.checked,
                "failures": [str(failure) for failure in result.failures],
                "summary": result.summary,
            },
            "cited_facts": records,
            "citations_by_sentence": {
                str(number): cites for number, cites in sorted(per_sentence.items())
            },
            "frozen_on": date.today().isoformat(),
        }
        print("  kept: {}".format(result.summary))
        print()
    return {"_note": _NOTE, "narrations": frozen}


#: Where `scripts/hero_candidates.py` writes the candidates a pick comes from.
#: Outside the repo, because a candidate is not a narration the app may speak
#: until it has been picked.
CANDIDATES_DIR = Path.home() / "prelude-review"


def newest_candidates(directory: Path) -> Path:
    """The most recent candidates document in `directory`, or a refusal."""
    found = sorted(directory.glob("hero_candidates_*.json"))
    if not found:
        raise SystemExit(
            "no hero_candidates_*.json in {}, so there is nothing to pick "
            "from. Run scripts/hero_candidates.py --confirm, which is a paid "
            "watsonx run.".format(directory)
        )
    return found[-1]


def read_candidates(path: Path) -> dict:
    """The candidates document, checked for the provenance a freeze records."""
    if not path.is_file():
        raise SystemExit("{} does not exist".format(path))
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or "goals" not in doc:
        raise SystemExit(
            "{} is not a candidates document: it carries no goals, and a "
            "freeze records which model wrote the words it writes".format(path)
        )
    for field in ("model", "provider", "generated_on"):
        if not doc.get(field):
            raise SystemExit(
                "{} records no {}, and a frozen narration says which model "
                "wrote it".format(path, field)
            )
    return doc


def parse_pick(value: str) -> tuple[int, int]:
    """One `--pick` argument, as `match_id=slot`."""
    if value.count("=") != 1:
        raise SystemExit(
            "--pick takes match_id=slot, as in --pick 3750191=3; got "
            "{!r}".format(value)
        )
    left, right = value.split("=")
    try:
        return int(left), int(right)
    except ValueError:
        raise SystemExit(
            "--pick takes two whole numbers, match_id=slot; got "
            "{!r}".format(value)
        )


def chosen(doc: dict, picks: Sequence[str]) -> list[tuple[dict, dict]]:
    """Each picked candidate with the goal it belongs to, in `HEROES` order.

    Refuses a pick naming a goal that is not a hero, a goal picked twice, a
    slot that is not in the file, and any hero left unpicked. A half-frozen
    pair would leave one moment card speaking a narration chosen on the
    evidence and the other speaking one chosen before it.
    """
    wanted: dict[int, int] = {}
    for value in picks:
        match_id, slot = parse_pick(value)
        if match_id in wanted:
            raise SystemExit(
                "match {} is picked twice; one narration is frozen per "
                "goal".format(match_id)
            )
        wanted[match_id] = slot

    heroes = [match_id for _, match_id, _, _ in HEROES]
    for match_id in wanted:
        if match_id not in heroes:
            raise SystemExit(
                "match {} is not one of the hero goals ({})".format(
                    match_id, ", ".join(str(one) for one in heroes)
                )
            )
    missing = [one for one in heroes if one not in wanted]
    if missing:
        raise SystemExit(
            "no pick for match {}; both hero goals are frozen together, so "
            "one card does not end up speaking a narration chosen before the "
            "other".format(", ".join(str(one) for one in missing))
        )

    by_match = {goal["match_id"]: goal for goal in doc["goals"]}
    out = []
    for match_id in heroes:
        goal = by_match.get(match_id)
        if goal is None:
            raise SystemExit(
                "the candidates file holds nothing for match {}".format(
                    match_id
                )
            )
        slot = wanted[match_id]
        candidate = next(
            (one for one in goal["candidates"] if one["slot"] == slot), None
        )
        if candidate is None:
            available = ", ".join(
                str(one["slot"]) for one in goal["candidates"]
            )
            raise SystemExit(
                "match {} has no candidate {}; it has {}".format(
                    match_id, slot, available or "none"
                )
            )
        out.append((goal, candidate))
    return out


def freeze_picked(doc: dict, path: Path, picks: Sequence[str]) -> dict:
    """Build the frozen document from picked candidates, with no model call.

    **The check is run again here, against `data/raw/`.** The candidate file
    records a verdict, and a verdict read out of a file is not a verdict: the
    words are about to be committed as the ones a judge hears under "Verified
    from play data", so they are re-read against the events rather than
    trusted. A candidate that no longer passes stops the freeze.
    """
    feed = StatsBombEventFeed()
    frozen: dict[str, dict] = {}
    for year, match_id, minute, second in HEROES:
        goal, candidate = next(
            (g, c)
            for g, c in chosen(doc, picks)
            if g["match_id"] == match_id
        )
        moment = moment_at(feed, match_id, minute, second)
        facts = facts_from_buildup(feed.buildup(match_id, moment))
        print("{} match {} {}:{:02d}: candidate {}".format(
            year, match_id, minute, second, candidate["slot"]
        ))
        print("  | {}".format(candidate["text"]))
        result = check(candidate["tagged_text"], facts)
        if not result.grounded:
            raise SystemExit(
                "candidate {} for match {} does not pass the check against "
                "data/raw/, so it is not what gets committed: {}".format(
                    candidate["slot"], match_id, result.summary
                )
            )
        if strip_citations(candidate["tagged_text"]) != candidate["text"]:
            raise SystemExit(
                "candidate {} for match {} has a text that is not its tagged "
                "text with the citations taken off, so the words checked and "
                "the words spoken are two different texts".format(
                    candidate["slot"], match_id
                )
            )
        records, per_sentence = cited_facts(candidate["tagged_text"], facts)
        frozen[str(match_id)] = {
            "match_id": match_id,
            "minute": minute,
            "second": second,
            "player": moment.player,
            "team": moment.team,
            "text": candidate["text"],
            "tagged_text": candidate["tagged_text"],
            "source": MODEL,
            # A merged candidates document holds goals from more than one
            # run, so the model that wrote these words is the goal's own
            # where it is recorded, and the document's only as a fallback.
            "model": goal.get("model") or doc["model"],
            "provider": goal.get("provider") or doc["provider"],
            "attempt": candidate["attempt"],
            "first_attempt_grounded": candidate["first_attempt_grounded"],
            "labelled": True,
            # Which candidate this was, and out of what. A frozen narration
            # chosen from several is a different claim from one accepted
            # because it was the first that passed, and the file says which.
            "picked": {
                "from": path.name,
                "generated_on": goal.get("generated_on")
                or doc["generated_on"],
                "slot": candidate["slot"],
                # How many of the asked-for slots came back grounded for this
                # goal, which is not the slot number: a slot that reached the
                # template fallback yields no candidate, so the kept ones are
                # not numbered one to five.
                "kept_for_this_goal": len(goal["candidates"]),
            },
            "check": {
                "grounded": result.grounded,
                "claims_checked": result.checked,
                "failures": [str(failure) for failure in result.failures],
                "summary": result.summary,
            },
            "cited_facts": records,
            "citations_by_sentence": {
                str(number): cites for number, cites in sorted(per_sentence.items())
            },
            "frozen_on": date.today().isoformat(),
        }
        print("  kept: {}".format(result.summary))
        print()
    return {"_note": _NOTE, "narrations": frozen}


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--plan",
        action="store_true",
        help="print the call count and the goals, and make no call",
    )
    parser.add_argument(
        "--confirm", action="store_true", help="send them; this is the paid path"
    )
    parser.add_argument(
        "--pick",
        action="append",
        default=[],
        metavar="MATCH_ID=SLOT",
        help="freeze a candidate from a hero_candidates file instead of "
             "generating, as --pick 3750191=3; one per hero goal, and no "
             "model is called",
    )
    parser.add_argument(
        "--candidates",
        type=Path,
        default=None,
        help="the candidates document to pick from (default: the newest in "
             "{})".format(CANDIDATES_DIR),
    )
    args = parser.parse_args(argv)

    # The pick path calls no model: the words already exist and were already
    # checked once. It still takes --confirm, because it overwrites a file the
    # repo commits and the app reads.
    if args.pick:
        path = args.candidates or newest_candidates(CANDIDATES_DIR)
        doc = read_candidates(path)
        print("picking  from {}".format(path))
        print("written  {} on {}, {}".format(
            doc["model"], doc["generated_on"], doc["provider"]
        ))
        print("calls    none: the narrations are already written and are "
              "re-checked against data/raw/ here")
        print("goals    {}".format(len(HEROES)))
        print()
        picked = chosen(doc, args.pick)
        for goal, candidate in picked:
            print("  match {}: candidate {}, one of the {} kept for this "
                  "goal, {} billed".format(
                      goal["match_id"],
                      candidate["slot"],
                      len(goal["candidates"]),
                      candidate["billed_characters"],
                  ))
            print("    | {}".format(candidate["text"]))
        print()
        if args.plan or not args.confirm:
            print("nothing was written. --confirm is what writes it.")
            return 0
        document = freeze_picked(doc, path, args.pick)
        NARRATIONS.write_text(
            json.dumps(document, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print("wrote {}".format(NARRATIONS.relative_to(ROOT)))
        return 0
    attempts = MAX_RETRIES + 1
    print("model     {} ({})".format(
        ACTIVE_CANDIDATE.model_id, ACTIVE_CANDIDATE.label
    ))
    print("endpoint  {}".format("chat" if ACTIVE_CANDIDATE.chat else "generation"))
    print("effort    {}".format(ACTIVE_CANDIDATE.reasoning_effort or "not set"))
    print("tokens    {} max new".format(COMPARISON_MAX_NEW_TOKENS))
    print("goals     {}".format(len(HEROES)))
    print("calls     at most {} generations ({} goals x {} attempts), "
          "plus 1 IAM exchange".format(
              len(HEROES) * attempts, len(HEROES), attempts
          ))
    print()
    if args.plan or not args.confirm:
        print("nothing was sent. --confirm is what sends it.")
        return 0

    backend = WatsonxProvider(max_new_tokens=COMPARISON_MAX_NEW_TOKENS)
    document = freeze(backend)
    NARRATIONS.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print("wrote {}".format(NARRATIONS.relative_to(ROOT)))
    print("IAM exchanges: {}".format(backend.iam_exchanges))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
