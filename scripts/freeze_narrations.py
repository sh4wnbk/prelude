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

from app.grounding import check, sentences  # noqa: E402
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
    args = parser.parse_args(argv)

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
