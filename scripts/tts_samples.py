r"""The hero samples: both demo goals, in every voice, for Shawn to listen to.

Eight samples. Two goals, the 1986 Maradona goal at 54:18 and the 2022 Di
Maria goal at 35:22, each in the Caller, the Storyteller and the Mate, with
the Mate heard from both sides: once as a fan of the side that scored and once
as a fan of the side that conceded.

**The words are built by code, not by a model.** The header comes from the
orchestrator through `openings` in `scripts/write_headers.py`, and the
narration is `template_narration` in `app/narration_prompt.py`, the fallback
that assembles a plain narration out of the numbered facts. Nothing here calls
a model, so a sample is reproducible, costs nothing but the speech, and is
grounded by construction. These are for judging the voices; the model's
narration is `scripts/narrate_once.py`.

**Six calls for eight samples, and that is a finding rather than a saving.**
The delivery table in `app/delivery.py` is all placeholders, so the Mate's
scored row and its conceded row are the same empty delivery and build the
identical request. The two files are written anyway, under both names, from
the one response: what matters is that **there is nothing to hear between the
two sides yet**, and writing two separately paid-for identical files would
hide that. The plan says which names share a request and why.

**The character count is printed before anything is sent**, two ways, because
IBM does not publish whether SSML markup is billable: the submitted length of
every request and the spoken text alone. Nothing is sent without `--confirm`.

**The audio is written outside the repo.** It is not the repo's to hold, and
`data/raw/` and the credentials are out there for the same reason.

Run it:

    .\.venv-prelude\Scripts\python.exe -I scripts\tts_samples.py --plan
    .\.venv-prelude\Scripts\python.exe -I scripts\tts_samples.py --confirm

Standard library only.
"""

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
# `scripts/write_headers.py` already builds the hero moment and calls the
# orchestrator for its header, and doing it a second time here would be a
# second place for that construction to be wrong. The scripts directory is not
# on the path under `-I`, so it is added explicitly rather than by accident.
sys.path.insert(0, str(Path(__file__).resolve().parent))

# The pronunciation table holds IPA and this script prints the text it built.
# A Windows console is cp1252 by default, which cannot encode "liːd".
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.grounding import strip_citations  # noqa: E402
from app.narration_prompt import (  # noqa: E402
    facts_from_buildup,
    template_narration,
)
from app.orchestrator_contract import (  # noqa: E402
    CALLER,
    CONCEDED,
    MATE,
    NEUTRAL,
    SCORED,
    STORYTELLER,
)
from app.statsbomb_event_feed import StatsBombEventFeed  # noqa: E402
from app.tts import SpeechRequest, WatsonTextToSpeech, without_markup  # noqa: E402
from write_headers import openings  # noqa: E402

#: Where the samples go: outside the repo, beside the probe's audio.
DEFAULT_OUT = Path.home() / "prelude_voice" / "samples"

#: The two hero goals, by the match they are in and the clock they are at.
#: Both are read out of `app/web/matches.json` by `scripts/write_headers.py`,
#: so the minute and second here are a label rather than a second source: the
#: script fails if the clock does not match the hero in that file.
HEROES = (
    ("1986", 3750191, 54, 18),
    ("2022", 3869685, 35, 22),
)

#: Which persona in which situation, and what the sample is called. The Caller
#: and the Storyteller are heard in the neutral situation, which is what a
#: listener with no side gets; the Mate is heard from both sides, because it is
#: the only persona that has a side at all.
VOICES = (
    (CALLER, NEUTRAL),
    (STORYTELLER, NEUTRAL),
    (MATE, SCORED),
    (MATE, CONCEDED),
)


@dataclass(frozen=True)
class Sample:
    """One file to write, and the request that would produce it."""

    name: str
    persona_id: str
    situation: str
    header: str
    narration: str
    request: SpeechRequest
    side: str

    @property
    def filename(self) -> str:
        return "{}.wav".format(self.name)


def narration_for(feed: StatsBombEventFeed, match_id: int, minute: int,
                  second: int) -> str:
    """The code-built narration for the goal at this clock.

    `strip_citations` takes the fact numbers off, which is what
    `Narrated.text` holds and what `app/tts.py` will speak: the tagged form is
    for the audit trail and the backend refuses it.
    """
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
    facts = facts_from_buildup(feed.buildup(match_id, found[0]))
    return strip_citations(template_narration(facts))


def samples(backend: WatsonTextToSpeech) -> tuple[Sample, ...]:
    """Every sample, with the request each one would send."""
    feed = StatsBombEventFeed()
    heroes = openings()
    built = []
    for year, match_id, minute, second in HEROES:
        header = heroes[match_id]["header"]
        narration = narration_for(feed, match_id, minute, second)
        # Which team a Mate listener supports, for the plan to print. The
        # header names the scoring side first, which is how the two sides are
        # told apart in a sentence rather than in a key.
        scorer = header.split(" ")[0]
        for persona_id, situation in VOICES:
            if situation == SCORED:
                side = "supporting {}".format(scorer)
            elif situation == CONCEDED:
                side = "supporting the other side"
            else:
                side = "no side"
            built.append(
                Sample(
                    name="{}_{}_{}".format(year, persona_id, situation),
                    persona_id=persona_id,
                    situation=situation,
                    header=header,
                    narration=narration,
                    request=backend.request_for(
                        header, narration, persona_id, situation
                    ),
                    side=side,
                )
            )
    return tuple(built)


def distinct(all_samples: Sequence[Sample]) -> dict[tuple[str, str], list[Sample]]:
    """The samples grouped by the request they send, in order.

    Two samples sharing a request share a response: one call, two files. With
    the delivery table unset that is the Mate's two sides, and it is the thing
    the plan should say out loud rather than hide.
    """
    groups: dict[tuple[str, str], list[Sample]] = {}
    for sample in all_samples:
        groups.setdefault((sample.request.query, sample.request.text), []).append(
            sample
        )
    return groups


def plan(all_samples: Sequence[Sample]) -> tuple[int, int, int]:
    """Print every sample and what the run costs. Returns the three totals."""
    groups = distinct(all_samples)
    print("{} samples, {} distinct request(s)".format(
        len(all_samples), len(groups)
    ))
    print()
    for sample in all_samples:
        print("  {}: {}, {}".format(sample.name, sample.persona_id, sample.side))
    print()
    for index, (_, shared) in enumerate(groups.items(), start=1):
        first = shared[0]
        print("  call {}: {}".format(index, first.request.query))
        print("    {}".format(first.request.text))
        print("    {} submitted, {} spoken".format(
            first.request.billable_characters,
            len(without_markup(first.request.text)),
        ))
        if len(shared) > 1:
            print("    writes {} files: {}".format(
                len(shared), ", ".join(one.filename for one in shared)
            ))
            print("    they share one request, so they will be identical "
                  "audio: the delivery table is placeholders, and there is "
                  "nothing to tell the two sides apart yet")
    submitted = sum(
        shared[0].request.billable_characters for shared in groups.values()
    )
    spoken = sum(
        len(without_markup(shared[0].request.text))
        for shared in groups.values()
    )
    print()
    print("  {} calls".format(len(groups)))
    print("  {} characters submitted, markup counted".format(submitted))
    print("  {} characters spoken, markup not counted".format(spoken))
    return len(groups), submitted, spoken


def run(backend: WatsonTextToSpeech, all_samples: Sequence[Sample],
        out: Path) -> list[Path]:
    """Send one request per distinct sample and write every file."""
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for shared in distinct(all_samples).values():
        audio = backend.send(shared[0].request)
        for one in shared:
            path = out / one.filename
            path.write_bytes(audio)
            written.append(path)
            print("  {}: {} bytes".format(one.filename, len(audio)), flush=True)
    return written


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--plan",
        action="store_true",
        help="print the samples and the character count, and make no call",
    )
    parser.add_argument(
        "--confirm", action="store_true", help="send them; this is the paid path"
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=2500,
        help="refuse to send if the submitted count is above this",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    backend = WatsonTextToSpeech()
    all_samples = samples(backend)
    calls, submitted, _ = plan(all_samples)
    if args.plan or not args.confirm:
        print()
        print("nothing was sent. --confirm is what sends it.")
        return 0
    if submitted > args.budget:
        print()
        print("{} characters is over the budget of {}; nothing was sent".format(
            submitted, args.budget
        ), file=sys.stderr)
        return 1

    print()
    print("sending {} calls, {} characters:".format(calls, submitted))
    written = run(backend, all_samples, args.out)
    print()
    print("{} files in {}".format(len(written), args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
