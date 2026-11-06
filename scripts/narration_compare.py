r"""Task 4b: the paid comparison. Two watsonx candidates, by persona.

`scripts/narration_eval.py` measures the development model and has no watsonx
path, deliberately: a loop of generations is the shape of accident that spends
money on a paid endpoint. This is the entry point that does spend it, and it
reuses that script's measuring code rather than copying it, so the numbers
mean the same thing in both reports.

**It says what it will cost before it costs it.** `--plan` prints the
narrations, the generation calls at three retry rates and the estimated tokens
for every arm, and makes no call at all. Nothing here runs without
`--confirm`, which has to name the arms being paid for.

**The arms**, which are Shawn's and are recorded in `HANDOFF.md`:

* **smoke**: one generation per candidate, to find out whether the endpoint
  serves the model at all before two hundred calls do.
* **b**: both candidates, no persona, three goals. The baseline the persona
  arms are read against.
* **a**: both candidates, every voice, the same three goals. The comparison
  Task 6c asked for on a model that might separate the registers.
* **c**: one candidate, no beats block, the five multi-beat goals.
* **c2**: the same candidate with the block on the two of those five that arm
  b does not cover, so the no-block comparison is paired on all five.
* **d**: the shipped candidate, every voice, on two of arm a's three goals,
  after each persona was given a worked example of its register. Task 4b
  found the three voices writing the same narration, so this is the same
  question asked again with the styles shown rather than described.

**The budget is a hard stop.** `--max-tokens` is checked after every narration
against the tokens the servers have reported so far, and the run stops between
narrations rather than mid-arm. What has been measured is already on disk:
records are written after every narration, like the local evaluation.

**One endpoint for the whole run.** If a candidate will not answer on
`/ml/v1/text/generation`, `--chat` sends every candidate to `/ml/v1/text/chat`
instead. A pass rate measured across two different APIs would be comparing
those as much as the models.

Run it:

    .\.venv-prelude\Scripts\python.exe -I scripts\narration_compare.py --plan
    .\.venv-prelude\Scripts\python.exe -I scripts\narration_compare.py \
        --arms smoke --confirm smoke
    .\.venv-prelude\Scripts\python.exe -I scripts\narration_compare.py \
        --arms b --confirm b --json docs/narration_runs/4b_watsonx.json
"""

import argparse
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.event_feed import Moment  # noqa: E402
from app.narration import narrate  # noqa: E402
from app.narration_config import (  # noqa: E402
    ACTIVE_CANDIDATE,
    CANDIDATES,
    COMPARISON_DECODING,
)
from app.narration_prompt import (  # noqa: E402
    build_prompt,
    facts_from_buildup,
    key_beats,
)
from app.narration_provider import (  # noqa: E402
    COMPARISON_MAX_NEW_TOKENS,
    WatsonxProvider,
)
from app.recorded_names import recorded_nicknames, recorded_teams  # noqa: E402
from app.statsbomb_event_feed import StatsBombEventFeed  # noqa: E402
from scripts.narration_eval import (  # noqa: E402
    NO_PERSONA,
    Record,
    Recorder,
    Voice,
    coverage,
    measure,
    read_personas,
    voices,
    write_json,
)

#: The three goals the persona arms run on, which are Task 6c's three, so the
#: paid numbers and the local ones are about the same passages.
GOALS_3 = ((3750191, (54, 18)), (3869685, (79, 24)), (3869685, (22, 24)))

#: The five goals with more than one key beat, which are the only ones the
#: beats block changes. Four of the nine have the shot as their only beat.
MULTI_BEAT = (
    (3750191, (50, 27)),
    (3750191, (54, 18)),
    (3869685, (22, 24)),
    (3869685, (79, 24)),
    (3869685, (117, 5)),
)

#: The two goals in `MULTI_BEAT` that arm b does not cover, which arm c2 runs
#: with the block so the no-block comparison is paired on all five.
C2_GOALS = ((3750191, (50, 27)), (3869685, (117, 5)))

DEFAULT_RUNS = 3

#: The run stops between narrations once the servers have reported this many
#: tokens. Shawn's figure.
DEFAULT_MAX_TOKENS = 500_000

#: What the project's usage meter read against what the servers reported, on
#: the smoke calls: 10,102 against about 9,000, so the reported counts run
#: roughly 12% low. The budget is about what the meter will say, so the
#: running total is raised by this before it is compared to the stop. It is a
#: measured correction rather than a safety margin; if the meter and the
#: responses are ever reconciled, this is the line that changes.
METER_UPLIFT = 1.12

#: The one setting the candidates do not share. `openai/gpt-oss-120b` writes
#: its reasoning into the same budget as its answer, and at the default effort
#: it spent 1,496 completion tokens on one narration against Granite's 60. A
#: fan waits through that on every attempt, so the comparison runs it the way
#: it would ship.
REASONING_EFFORT = {"openai/gpt-oss-120b": "low"}

#: The two goals the worked-example round reruns, which are two of the three
#: the persona arms used, so the before and the after are the same passages.
GOALS_2 = ((3750191, (54, 18)), (3869685, (79, 24)))

ARMS = ("smoke", "b", "a", "c", "c2", "d")


def read_arms(argument: str, default_runs: int) -> list[tuple[str, int]]:
    """"b,a:2,c" into [("b", 3), ("a", 2), ("c", 3)].

    An arm carries its own run count so that a budget which will not reach
    the whole plan is spent by asking one arm for fewer runs rather than by
    dropping a voice or a goal from it. Fewer runs weakens a rate; a missing
    voice removes a comparison.
    """
    chosen: list[tuple[str, int]] = []
    for item in (part.strip() for part in argument.split(",")):
        if not item:
            continue
        name, _, runs = item.partition(":")
        name = name.strip()
        if name not in ARMS:
            raise SystemExit(
                f"unknown arm {name!r}; the arms are {', '.join(ARMS)}"
            )
        if runs and (not runs.strip().isdigit() or int(runs) < 1):
            raise SystemExit(f"{item!r}: a run count is a whole number above 0")
        chosen.append((name, int(runs) if runs else default_runs))
    if not chosen:
        raise SystemExit("--arms selected nothing")
    return chosen


def moment_for(
    feed: StatsBombEventFeed, match_id: int, clock: tuple[int, int]
) -> Moment:
    found = [
        moment
        for moment in feed.defining_moments(match_id)
        if (moment.minute, moment.second) == clock
    ]
    if len(found) != 1:
        raise SystemExit(
            f"{len(found)} moments in match {match_id} at "
            f"{clock[0]}:{clock[1]:02d}; expected exactly one"
        )
    return found[0]


def arm_plan(
    feed: StatsBombEventFeed, arm: str, runs: int
) -> list[tuple[str, int, Moment, Voice, bool]]:
    """Every narration one arm will ask for, as (model, match, moment, voice).

    The boolean is whether the beats block is suppressed, which is arm c and
    nothing else.
    """
    both = [candidate.model_id for candidate in CANDIDATES]
    one = [CANDIDATES[0].model_id]
    # Arm d runs on whatever is shipping, which is the point of it.
    active = [ACTIVE_CANDIDATE.model_id]
    plan: list[tuple[str, int, Moment, Voice, bool]] = []

    def add(models, goals, chosen_voices, no_block=False, times=runs):
        for model in models:
            for match_id, clock in goals:
                moment = moment_for(feed, match_id, clock)
                for voice in chosen_voices(match_id):
                    for _ in range(times):
                        plan.append((model, match_id, moment, voice, no_block))

    plain = lambda _match_id: (Voice(persona=None, side=None),)
    every = lambda match_id: voices(feed, match_id, read_personas("all"))

    if arm == "smoke":
        add(both, GOALS_3[:1], plain, times=1)
    elif arm == "b":
        add(both, GOALS_3, plain)
    elif arm == "a":
        add(both, GOALS_3, every)
    elif arm == "c":
        add(one, MULTI_BEAT, plain, no_block=True)
    elif arm == "c2":
        add(one, C2_GOALS, plain)
    elif arm == "d":
        add(active, GOALS_2, every)
    else:
        raise SystemExit(f"unknown arm {arm!r}; the arms are {', '.join(ARMS)}")
    return plan


def estimated_prompt_tokens(
    feed: StatsBombEventFeed, plan: Sequence[tuple[str, int, Moment, Voice, bool]]
) -> int:
    """A rough token count for a plan, from the prompts it will send.

    Four characters to the token, which is an estimate and is labelled as one
    everywhere it is printed. The real counts come back from the servers and
    are what the report quotes; this exists so a plan can be read before any
    call is made.
    """
    total = 0
    for _model, match_id, moment, voice, no_block in plan:
        total += len(prompt_for(feed, match_id, moment, voice, no_block)) // 4
    return total


def prompt_for(
    feed: StatsBombEventFeed,
    match_id: int,
    moment: Moment,
    voice: Voice,
    no_block: bool,
) -> str:
    facts = facts_from_buildup(
        feed.buildup(match_id, moment),
        recorded_nicknames(match_id),
        recorded_teams(match_id),
    )
    # The prompt is the same in every voice, so `voice` changes nothing
    # here. It stays in the signature because an arm names one and the
    # estimate is per narration, which is per voice.
    return build_prompt(facts, beats=not no_block)


def describe_plan(
    feed: StatsBombEventFeed, arms: Sequence[tuple[str, int]]
) -> None:
    """What the run will cost, before anything is paid for."""
    print("Task 4b, the paid comparison. No call is made by --plan.\n")
    print(f"{'arm':8} {'narrations':>11} {'min calls':>10} {'likely':>8} "
          f"{'max calls':>10} {'est prompt tokens':>18}")
    totals = [0, 0, 0, 0, 0]
    for arm, runs in arms:
        plan = arm_plan(feed, arm, runs)
        narrations = len(plan)
        tokens = estimated_prompt_tokens(feed, plan)
        # One call if every first attempt passes, three if every narration
        # retries twice. "Likely" is what granite4:micro actually did.
        likely = round(narrations * (2.25 if arm == "a" else 1.4))
        print(f"{arm:8} {narrations:>11} {narrations:>10} {likely:>8} "
              f"{narrations * 3:>10} {tokens:>18,}")
        for index, value in enumerate(
            (narrations, narrations, likely, narrations * 3, tokens)
        ):
            totals[index] += value
    print(f"{'total':8} {totals[0]:>11} {totals[1]:>10} {totals[2]:>8} "
          f"{totals[3]:>10} {totals[4]:>18,}")
    print(
        "\nTokens are an estimate from the prompt text, four characters to "
        "the token.\nThe real counts come back from the servers. A template "
        "fallback costs no call."
    )


def backend(model: str, recorder: Recorder, chat: bool) -> WatsonxProvider:
    """One candidate, decoded the same way as the other.

    The credentials are read by `app/credentials.py` from outside the repo.
    Nothing here opens that file, names a variable's value or prints one.
    """
    return WatsonxProvider(
        model=model,
        transport=recorder,
        decoding=COMPARISON_DECODING,
        chat=chat,
        max_new_tokens=COMPARISON_MAX_NEW_TOKENS,
        reasoning_effort=REASONING_EFFORT.get(model),
    )


def run_smoke(feed: StatsBombEventFeed, chat: bool) -> int:
    """One generation per candidate, to learn whether the endpoint serves it.

    Prints what came back and returns non-zero if either candidate refused,
    so the staged run stops here rather than finding out two hundred calls in.
    """
    match_id, clock = GOALS_3[0]
    moment = moment_for(feed, match_id, clock)
    facts = facts_from_buildup(
        feed.buildup(match_id, moment),
        recorded_nicknames(match_id),
        recorded_teams(match_id),
    )
    prompt = build_prompt(facts)
    failures = 0

    for candidate in CANDIDATES:
        recorder = Recorder()
        feed_in = backend(candidate.model_id, recorder, chat)
        print(f"\n--- {candidate.label} ({candidate.model_id})")
        print(f"    endpoint {feed_in.url.split('?')[0]}")
        started = time.perf_counter()
        try:
            answer = feed_in.narrate(prompt, COMPARISON_MAX_NEW_TOKENS)
        except Exception as failure:  # noqa: BLE001 - reported, not swallowed
            failures += 1
            print(f"    REFUSED  {type(failure).__name__}: {failure}")
            body = getattr(failure, "read", None)
            if body is not None:
                try:
                    print(f"    body     {body()[:600].decode('utf-8')}")
                except Exception:  # noqa: BLE001
                    pass
            continue
        calls = recorder.take()
        tokens = sum(c.prompt_tokens + c.completion_tokens for c in calls)
        print(f"    answered in {time.perf_counter() - started:.1f}s, "
              f"{tokens} tokens reported, model id {answer.model!r}")
        print(f"    IAM exchanges {feed_in.iam_exchanges}")
        print("    first 300 characters of what it wrote:")
        print("      " + answer.text.strip()[:300].replace("\n", "\n      "))
    return failures


def run_arm(
    feed: StatsBombEventFeed,
    arm: str,
    runs: int,
    chat: bool,
    json_path: Path | None,
    records: list[Record],
    spent: list[int],
    max_tokens: int,
) -> bool:
    """One arm. Returns False if the budget stopped it.

    `records` and `spent` are carried across arms, so the budget is the run's
    and the records file holds everything measured so far whenever it stops.
    """
    plan = arm_plan(feed, arm, runs)
    print(f"\n=== arm {arm}: {len(plan)} narration(s)")

    backends: dict[str, tuple[WatsonxProvider, Recorder]] = {}
    run_number: dict[tuple, int] = {}

    for index, (model, match_id, moment, voice, no_block) in enumerate(plan, 1):
        if model not in backends:
            recorder = Recorder()
            backends[model] = (backend(model, recorder, chat), recorder)
        chosen, recorder = backends[model]

        key = (model, match_id, moment.minute, moment.second, voice.label, no_block)
        run_number[key] = run_number.get(key, 0) + 1

        print(f"[{arm} {index}/{len(plan)}] {model} {match_id} "
              f"{moment.minute}:{moment.second:02d} {voice.label} "
              f"run {run_number[key]}"
              + (" (no beats block)" if no_block else ""))

        record = measure(
            feed,
            match_id,
            moment,
            run_number[key],
            chosen,
            recorder,
            voice,
            beats=not no_block,
        )
        record = _tagged(record, model, arm, no_block)
        records.append(record)
        spent[0] += record.tokens

        print(f"         first attempt "
              f"{'grounded' if record.first_attempt_grounded else 'refused'}"
              f", {record.source}"
              f", coverage {record.covered}/{record.beats}"
              f", {record.tokens} tokens"
              f", {record.calls} call(s) in {record.generation_seconds:.1f}s"
              + (f", {record.error}" if record.error else ""))

        if json_path is not None:
            write_json(json_path, records)

        metered = spent[0] * METER_UPLIFT
        if metered >= max_tokens:
            print(f"\nSTOPPED: {spent[0]:,} tokens reported, {metered:,.0f} "
                  f"metered, at or over the {max_tokens:,} budget. "
                  f"{len(records)} narration(s) are on disk.")
            return False

    exchanges = sum(b.iam_exchanges for b, _ in backends.values())
    print(f"--- arm {arm} done. cumulative: {len(records)} narration(s), "
          f"{spent[0]:,} tokens reported, {spent[0] * METER_UPLIFT:,.0f} "
          f"metered of {max_tokens:,}, "
          f"{exchanges} IAM exchange(s) in this arm")
    return True


def _tagged(record: Record, model: str, arm: str, no_block: bool) -> Record:
    """The record, with what produced it that `Record` does not already hold."""
    return Record(
        **{
            **asdict(record),
            "missed": tuple(record.missed),
            "model": model,
            "arm": arm,
            "beats_block": not no_block,
        }
    )


def main(argv: Sequence[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="The paid watsonx comparison. Spends money; read --plan first.",
    )
    parser.add_argument(
        "--plan", action="store_true",
        help="print what the chosen arms would cost and make no call",
    )
    parser.add_argument(
        "--arms", default=",".join(ARMS),
        help=f"comma separated, in order. The arms are {', '.join(ARMS)}. An "
             "arm may carry its own run count as 'a:2', for a budget that "
             "reaches further by asking one arm for fewer runs rather than "
             "by dropping a voice from it.",
    )
    parser.add_argument(
        "--confirm", default="",
        help="the same arms again. Nothing runs unless this matches --arms, "
             "so a paid run cannot be started by an up arrow and a return.",
    )
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument(
        "--max-tokens", type=int, default=DEFAULT_MAX_TOKENS,
        help=f"stop between narrations at this many reported tokens "
             f"(default {DEFAULT_MAX_TOKENS:,})",
    )
    parser.add_argument(
        "--chat", action="store_true",
        help="send every candidate to the chat endpoint instead of the "
             "generation one, for a model the generation endpoint refuses",
    )
    parser.add_argument("--json", type=Path, help="write the records here")
    args = parser.parse_args(argv)

    arms = read_arms(args.arms, args.runs)

    feed = StatsBombEventFeed()

    if args.plan:
        describe_plan(feed, arms)
        return 0

    confirmed = read_arms(args.confirm, args.runs) if args.confirm else []
    if confirmed != arms:
        raise SystemExit(
            "--confirm has to name the same arms as --arms, in the same "
            f"order and with the same run counts. --arms said {arms} and "
            f"--confirm said {confirmed}. This run spends money."
        )

    named = ", ".join(f"{arm} x{runs}" for arm, runs in arms)
    print(f"watsonx, arms {named}")
    print(f"decoding {COMPARISON_DECODING}, max_new_tokens "
          f"{COMPARISON_MAX_NEW_TOKENS}")
    for named, effort in REASONING_EFFORT.items():
        print(f"reasoning_effort {effort} for {named}")
    print(f"endpoint {'chat' if args.chat else 'text generation'}")
    print(f"budget {args.max_tokens:,} reported tokens\n")

    records: list[Record] = []
    spent = [0]
    started = time.perf_counter()

    for arm, runs in arms:
        if arm == "smoke":
            failures = run_smoke(feed, args.chat)
            if failures:
                print(f"\n{failures} candidate(s) refused. Stopping before "
                      "any measured arm.")
                return 1
            print("\nboth candidates answered.")
            continue
        if not run_arm(feed, arm, runs, args.chat, args.json, records,
                       spent, args.max_tokens):
            break

    print(f"\ndone in {time.perf_counter() - started:.0f}s")
    print(f"narrations {len(records)}, tokens reported {spent[0]:,}")
    if args.json:
        print(f"records {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
