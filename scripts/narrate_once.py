r"""Narrate one goal with a real model, and print every attempt.

This is the live run behind the narration pipeline: it calls the local Ollama
server, checks what came back, retries, falls back, and prints what happened at
each step. Nothing in the test suite does this, and nothing should:
`tests/conftest.py` fails any test that opens a connection.

It needs a local Ollama server with the development model pulled:

    ollama pull granite4:micro
    .\.venv-prelude\Scripts\python.exe -I scripts\narrate_once.py

With no arguments it narrates the 1986 Argentina vs England goal at 54:18.
Another goal is named by its match id and clock:

    .\.venv-prelude\Scripts\python.exe -I scripts\narrate_once.py 3869685 22:24

What it prints is the model's own text, the claims the check refused, and
whether the first attempt was grounded, which is the number a pass rate is
measured on. It writes nothing and changes nothing.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.narration import narrate  # noqa: E402
from app.narration_prompt import facts_from_buildup  # noqa: E402
from app.narration_provider import provider  # noqa: E402
from app.statsbomb_event_feed import StatsBombEventFeed  # noqa: E402

DEFAULT_MATCH = 3750191
DEFAULT_CLOCK = (54, 18)


def parse(argv):
    """(match_id, (minute, second)) from the command line."""
    if not argv:
        return DEFAULT_MATCH, DEFAULT_CLOCK
    if len(argv) != 2 or ":" not in argv[1]:
        raise SystemExit(
            "usage: narrate_once.py [match_id minute:second]\n"
            f"  default: {DEFAULT_MATCH} "
            f"{DEFAULT_CLOCK[0]}:{DEFAULT_CLOCK[1]:02d}"
        )
    minute, second = argv[1].split(":", 1)
    return int(argv[0]), (int(minute), int(second))


def main(argv) -> int:
    # The recorded names carry accents, and a Windows console is not UTF-8 by
    # default, so the player this is about would not print.
    sys.stdout.reconfigure(encoding="utf-8")

    match_id, clock = parse(argv)
    feed = StatsBombEventFeed()
    moments = [
        moment
        for moment in feed.defining_moments(match_id)
        if (moment.minute, moment.second) == clock
    ]
    if len(moments) != 1:
        raise SystemExit(
            f"{len(moments)} moments in match {match_id} at "
            f"{clock[0]}:{clock[1]:02d}; expected exactly one"
        )
    moment = moments[0]
    facts = facts_from_buildup(feed.buildup(match_id, moment))
    backend = provider()

    print(f"match     {match_id}")
    print(f"moment    {moment.player} ({moment.team}), {moment.minute}:"
          f"{moment.second:02d}, {facts.set_piece or 'Open Play'}, "
          f"{facts.body_part or 'body part not recorded'}")
    print(f"facts     {len(facts.facts)}")
    print(f"model     {backend.name} {backend.model}")
    print("a CPU-only generation takes a while; waiting\n")

    narrated = narrate(feed, match_id, moment, narration_provider=backend)

    for attempt in narrated.attempts:
        print(f"attempt {attempt.number} ({attempt.source}): "
              f"{'grounded' if attempt.grounded else 'not grounded'}")
        for line in attempt.text.splitlines():
            print(f"  | {line}")
        for failure in attempt.failures:
            print(f"  x {failure}")
        print()

    print(f"source                 {narrated.source}")
    print(f"first attempt grounded {narrated.first_attempt_grounded}")
    print(f"label                  {narrated.label!r}")
    print("\nnarration as it would be shown and voiced:")
    print(f"  {narrated.text}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
