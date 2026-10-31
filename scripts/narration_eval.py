r"""Narrate every goal several times and measure what came back.

`app/narration.py` can narrate one moment. Nothing until now ran it over the
nine goals and wrote down how it did, so the only evidence about the prompt was
a handful of runs quoted in `docs/VOICE.md`. This produces the numbers:
`docs/narration_eval.md`.

**Development model only.** Every call here goes to the local Ollama server
running the model in `app/narration_config.py`. There is no watsonx path in
this script and no flag that adds one, because a loop of twenty-seven
generations is exactly the shape of accident that spends money on a paid
endpoint. Task 4b writes the paid comparison, states its call count before
running, and reuses the measuring code below rather than this entry point.

Four things are recorded per narration:

* **First-attempt grounding.** `Narrated.first_attempt_grounded`, never the
  attempt that eventually passed. A rate counting retries would say the prompt
  is doing better than it is.
* **Coverage**, the share of the key beats of the passage that the narration
  cited. See `key_beats` for what counts as one and what that measure cannot
  do.
* **Tokens**, read off Ollama's own `prompt_eval_count` and `eval_count`
  rather than estimated from the text, which is what `Recorder` is for.
* **Time**, wall clock around the generation call.
* **The voice**, which persona was asked for and which side the listener was
  on. It reaches `app/grounding.py` and no longer reaches the prompt: the
  narration text is one style in every voice (`NARRATION_STYLE` in
  `app/narration_prompt.py`). The persona columns in the saved runs were
  measured while it did reach the prompt, and each of those sections says so.

Grounding and coverage answer different questions, and both are needed. The
check refuses a narration that says something the data does not support; it has
nothing to say about a narration that supports everything it says and leaves
out the goal's whole story. A first live run on the 1986 54:18 goal passed the
check with four true sentences that skipped all four dribbles, which is the run
coverage exists to put a number on.

**The personas are opt in, and they now change only the check.**
`--personas` picks the voices to run and defaults to `none`. It changed the
prompt from Task 6b to Task 6d, which is what the saved persona runs measured;
the prompt takes no persona now, so a voice changes which first-person rule
`app/grounding.py` applies and nothing else. A `fans_only` persona is still
two runs, one per side, because that is what the check reads it against.
`--persona-runs` takes a records file and adds its per-persona results to the
report as a section of their own, which is how one document holds three runs.

**Only the model can pass.** A template fallback is counted as a failure in
the persona section: it is assembled by code out of the facts, so it is not
the model's narration, and a column treating it as a pass would report the
fallback's reliability as the model's.

Run it:

    .\.venv-prelude\Scripts\python.exe -I scripts\narration_eval.py --help
    .\.venv-prelude\Scripts\python.exe -I scripts\narration_eval.py \
        --goals 3750191:54:18 --runs 1 --out out.md
    .\.venv-prelude\Scripts\python.exe -I scripts\narration_eval.py \
        --goals 3750191:54:18 --runs 3 --personas all --json records.json
    .\.venv-prelude\Scripts\python.exe -I scripts\narration_eval.py

The full default run is nine goals times three runs on a CPU, so it takes a
while. `--json` writes the records after every narration, so a run that dies at
goal eight keeps the first seven and the report can be rebuilt from the file
with `--from-json` instead of generating again.
"""

import argparse
import json
import statistics
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.event_feed import Moment  # noqa: E402
from app.grounding import FIRST_PERSON, sentences  # noqa: E402
from app.narration import MODEL, TEMPLATE, narrate  # noqa: E402
from app.narration_config import DEVELOPMENT_MODEL  # noqa: E402
from app.narration_prompt import (  # noqa: E402
    DRIBBLE,
    FOUL,
    SHOT,
    Facts,
    KeyBeat,
    facts_from_buildup,
    key_beats,
)
from app.narration_provider import Transport, post, provider  # noqa: E402
from app.personas import PERSONAS, Persona, persona as persona_by_id  # noqa: E402
from app.recorded_names import recorded_nicknames  # noqa: E402
from app.statsbomb_event_feed import StatsBombEventFeed  # noqa: E402

#: The two demo matches, in the order the app lists them.
MATCHES = (3750191, 3869685)

#: Runs per goal. Three is enough to show that a model is not deterministic and
#: cheap enough to sit through; it is not enough for a confidence interval, and
#: the report says so rather than implying a precision this does not have.
DEFAULT_RUNS = 3

DEFAULT_REPORT = ROOT / "docs" / "narration_eval.md"

#: What a narration with no persona is called in a report. It was a real arm
#: of the comparison rather than a missing value: while a persona carried a
#: style, `none` was the prompt without one, and it is the prompt the Task 4a
#: and 4c numbers were measured with.
NO_PERSONA = "none"

#: The label every persona section carries, because the code those runs
#: measured is gone. Doc copy, so `CLAUDE.md` governs it, and it names the
#: commits rather than describing them: a reader can check out any of the
#: three and build the prompt the numbers came from.
REMOVED_SINCE = (
    "**Measured on code since removed.** Each persona carried a `style` "
    "that `build_prompt` printed under \"THE VOICE\", and from Task 6d a "
    "worked `example` of its register as well. Three runs asked three models "
    "for three registers and got one back each time, so both fields were "
    "removed: the narration text is now one style for every persona, "
    "`NARRATION_STYLE` in `app/narration_prompt.py`, and Phase 5 separates "
    "the voices in the audio instead. The runs are at `8f784cf` (Task 6c), "
    "`abf5702` (Task 4b) and `128833a` (Task 6d). The numbers below are what "
    "they reported; nothing in them has been recomputed."
)


@dataclass(frozen=True)
class Voice:
    """One persona, and the side it is being written for.

    A voice rather than a persona, because the Mate is two runs and not one:
    it writes as the listener's side, so the same persona over the same goal
    is a different request for each team. The other two have no side and are
    one voice each.
    """

    persona: Persona | None
    side: str | None

    @property
    def id(self) -> str:
        if self.persona is None:
            return NO_PERSONA
        return self.persona.id

    @property
    def label(self) -> str:
        """How a report names this voice, the same way in every table."""
        if self.side:
            return f"{self.id} ({self.side})"
        return self.id


def match_sides(feed: StatsBombEventFeed, match_id: int) -> tuple[str, ...]:
    """The two teams of a match, in the order the events first name them.

    Read off the records rather than written down, like everything else here.
    A match with anything but two teams in it is a match this script has
    misread, so it raises rather than narrating for a side it invented.
    """
    sides: list[str] = []
    for event in feed.load_match(match_id):
        team = (event.get("team") or {}).get("name")
        if team and team not in sides:
            sides.append(team)
    if len(sides) != 2:
        raise SystemExit(
            f"match {match_id} names {len(sides)} teams, expected two"
        )
    return tuple(sides)


def voices(
    feed: StatsBombEventFeed, match_id: int, chosen: Sequence[str]
) -> tuple[Voice, ...]:
    """The voices to run for one match, from a list of persona ids.

    A `fans_only` persona becomes one voice per side, because it writes as the
    listener's team and there are two of them. `NO_PERSONA` is the prompt with
    no style block, which is what the earlier runs in `docs/narration_eval.md`
    measured and what makes them comparable with these.
    """
    built: list[Voice] = []
    for persona_id in chosen:
        if persona_id == NO_PERSONA:
            built.append(Voice(persona=None, side=None))
            continue
        persona = persona_by_id(persona_id)
        if persona.fans_only:
            built += [
                Voice(persona=persona, side=side)
                for side in match_sides(feed, match_id)
            ]
        else:
            built.append(Voice(persona=persona, side=None))
    return tuple(built)


def read_personas(argument: str) -> tuple[str, ...]:
    """The `--personas` argument: "all", "none", or a comma separated list."""
    if argument in ("", NO_PERSONA):
        return ()
    if argument == "all":
        return tuple(persona.id for persona in PERSONAS)
    chosen = tuple(part.strip() for part in argument.split(",") if part.strip())
    for persona_id in chosen:
        if persona_id == NO_PERSONA:
            continue
        persona_by_id(persona_id)
    return chosen

@dataclass(frozen=True)
class Coverage:
    """How much of the passage one narration reached."""

    cited: tuple[int, ...]
    covered: tuple[KeyBeat, ...]
    missed: tuple[KeyBeat, ...]

    @property
    def beats(self) -> int:
        return len(self.covered) + len(self.missed)

    @property
    def share(self) -> float:
        return len(self.covered) / self.beats if self.beats else 0.0


def coverage(text: str, facts: Facts) -> Coverage:
    """Which key beats a narration cited.

    Read off the citations, not the prose. A sentence citing the fact is taken
    to be about it, which is the same assumption `app/grounding.py` makes when
    it reads a sentence against the facts that sentence named; there the
    assumption is conservative, and here it is generous, because a sentence can
    cite a dribble and then say nothing much about it. Coverage is a measure of
    what the narration reached, not of how well it said it.
    """
    cited = sorted({number for s in sentences(text) for number in s.cites})
    beats = key_beats(facts)
    return Coverage(
        cited=tuple(cited),
        covered=tuple(b for b in beats if b.covered_by(cited)),
        missed=tuple(b for b in beats if not b.covered_by(cited)),
    )


@dataclass(frozen=True)
class Call:
    """One generation request, as the server reported it."""

    prompt_tokens: int
    completion_tokens: int
    seconds: float


def call_tokens(answer: Mapping[str, Any]) -> tuple[int, int]:
    """(prompt, completion) tokens from one response, whichever API sent it.

    Three shapes, because three APIs count the same thing under different
    names, and none of them is guessed at: Ollama reports `prompt_eval_count`
    and `eval_count` at the top level, watsonx text generation reports
    `input_token_count` and `generated_token_count` inside `results[0]`, and
    watsonx chat reports a `usage` object. A response carrying none of them
    reports zero rather than an estimate, because a token count invented here
    would be indistinguishable in the report from one the server sent.
    """
    if "prompt_eval_count" in answer or "eval_count" in answer:
        return (
            int(answer.get("prompt_eval_count") or 0),
            int(answer.get("eval_count") or 0),
        )

    results = answer.get("results") or []
    if results:
        first = results[0] or {}
        return (
            int(first.get("input_token_count") or 0),
            int(first.get("generated_token_count") or 0),
        )

    usage = answer.get("usage") or {}
    if usage:
        return (
            int(usage.get("prompt_tokens") or 0),
            int(usage.get("completion_tokens") or 0),
        )

    return (0, 0)


def is_generation(answer: Mapping[str, Any]) -> bool:
    """Whether a response is a generation rather than an IAM exchange.

    The paid run authorises before it generates, and both go through this
    transport. Counting the IAM exchange as an attempt would report every
    watsonx narration as having tried twice as often as it did, so it is told
    apart by what it answered with: an access token and nothing else.
    """
    return "access_token" not in answer


class Recorder:
    """A transport that passes requests through and keeps the token counts.

    `Transport` is the seam the provider already has for tests, so measuring
    tokens needs no change to `app/`. The counts come from whichever server
    answered, through `call_tokens`, rather than from counting words, which
    would be a different number wearing the same name.

    **An IAM exchange is not a call.** The watsonx provider authorises before
    it generates, and both pass through here. Only generations are recorded,
    so an attempt count means attempts at narrating; `iam_exchanges` on the
    provider is what says how often it authorised.
    """

    def __init__(self, inner: Transport = post) -> None:
        self._inner = inner
        self.calls: list[Call] = []

    def __call__(
        self, url: str, body: bytes, headers: Mapping[str, str]
    ) -> Mapping[str, Any]:
        started = time.perf_counter()
        answer = self._inner(url, body, headers)
        if is_generation(answer):
            prompt_tokens, completion_tokens = call_tokens(answer)
            self.calls.append(
                Call(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    seconds=time.perf_counter() - started,
                )
            )
        return answer

    def take(self) -> tuple[Call, ...]:
        """Hand back the calls since the last `take`, and start again."""
        calls = tuple(self.calls)
        self.calls = []
        return calls


@dataclass(frozen=True)
class Record:
    """One narration, measured. The row behind every number in the report."""

    match_id: int
    minute: int
    second: int
    team: str
    player: str
    set_piece: str
    run: int
    first_attempt_grounded: bool
    attempts: int
    source: str
    covered: int
    beats: int
    missed: tuple[str, ...]
    prompt_tokens: int
    completion_tokens: int
    seconds: float
    text: str
    tagged_text: str
    error: str = ""
    # The voice, with defaults so a records file written before personas
    # existed still reads: the Task 4a and 4c runs in docs/narration_runs/
    # are rebuilt by --from-json and --compare, and an absent field there
    # means the prompt had no style block, which is what NO_PERSONA says.
    persona: str = NO_PERSONA
    side: str = ""
    # What produced it, for a report holding more than one model. The local
    # runs have no model field because they were all the development model,
    # which is what the default says.
    model: str = ""
    arm: str = ""
    beats_block: bool = True
    # Latency, separated from `seconds`. `seconds` is the whole narration,
    # every attempt and both checks; these two are the generation calls
    # alone, which is what a fan waits through and what a model is compared
    # on. The local records have neither, and a mean over zero calls is
    # reported as n/a rather than as zero.
    calls: int = 0
    generation_seconds: float = 0.0

    @property
    def seconds_per_call(self) -> float | None:
        return self.generation_seconds / self.calls if self.calls else None

    @property
    def clock(self) -> str:
        return f"{self.minute}:{self.second:02d}"

    @property
    def goal(self) -> str:
        """How the report names this goal, the same way in every table."""
        return f"{self.match_id} {self.clock} {surname(self.player)}"

    @property
    def voice(self) -> str:
        """How the report names the voice it was written in."""
        return f"{self.persona} ({self.side})" if self.side else self.persona

    @property
    def model_wrote_it(self) -> bool:
        """A pass. The template fallback is not one.

        A fallback is assembled by code out of the facts, in one plain
        register, so it is neither the model's narration nor the voice that
        was asked for. Counting it as a pass would report the fallback's
        reliability as the model's.
        """
        return self.source == MODEL

    @property
    def share(self) -> float:
        return self.covered / self.beats if self.beats else 0.0

    @property
    def tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


def surname(player: str) -> str:
    """The last word of a recorded name, for a table that has to stay narrow.

    Report copy only. Narration never shortens a name this way: `app/` uses the
    recorded name, and the grounding check decides what a sentence may call
    someone by reading the fact it cited.
    """
    return player.split()[-1]


def goal_moments(
    feed: StatsBombEventFeed, specification: str | None
) -> tuple[tuple[int, Moment], ...]:
    """The goals to run, from a `--goals` string.

    Each comma-separated item is either a match id, meaning every defining
    moment in it, or `match:minute:second`, meaning one. No argument means
    every goal in both demo matches, which is the nine the report is about.
    """
    if specification is None:
        return tuple(
            (match_id, moment)
            for match_id in MATCHES
            for moment in feed.defining_moments(match_id)
        )

    chosen: list[tuple[int, Moment]] = []
    for item in (part.strip() for part in specification.split(",")):
        if not item:
            continue
        fields = item.split(":")
        if len(fields) == 1:
            match_id = int(fields[0])
            chosen.extend(
                (match_id, moment) for moment in feed.defining_moments(match_id)
            )
        elif len(fields) == 3:
            match_id, minute, second = (int(field) for field in fields)
            found = [
                moment
                for moment in feed.defining_moments(match_id)
                if (moment.minute, moment.second) == (minute, second)
            ]
            if len(found) != 1:
                raise SystemExit(
                    f"{len(found)} moments in match {match_id} at "
                    f"{minute}:{second:02d}; expected exactly one"
                )
            chosen.append((match_id, found[0]))
        else:
            raise SystemExit(
                f"cannot read {item!r} as a goal: write a match id, or "
                "match:minute:second"
            )
    if not chosen:
        raise SystemExit("--goals selected nothing")
    return tuple(chosen)


def measure(
    feed: StatsBombEventFeed,
    match_id: int,
    moment: Moment,
    run: int,
    backend,
    recorder: Recorder,
    voice: Voice = Voice(persona=None, side=None),
    beats: bool = True,
) -> Record:
    """Narrate one goal once and record what it cost and what it reached.

    A narration that raises is recorded rather than allowed to end the run. A
    loop this long dying on goal eight and reporting nothing would be the worst
    of both: the time spent and no evidence.
    """
    facts = facts_from_buildup(
        feed.buildup(match_id, moment), recorded_nicknames(match_id)
    )
    beats = key_beats(facts)
    started = time.perf_counter()
    recorder.take()

    shared = dict(
        match_id=match_id,
        minute=moment.minute,
        second=moment.second,
        team=moment.team,
        player=moment.player,
        set_piece=facts.set_piece or "Open Play",
        run=run,
        beats=len(beats),
        persona=voice.id,
        side=voice.side or "",
    )

    try:
        narrated = narrate(
            feed,
            match_id,
            moment,
            narration_provider=backend,
            persona=voice.persona,
            side=voice.side,
            beats=beats,
        )
    except Exception as failure:  # noqa: BLE001 - recorded, not swallowed
        calls = recorder.take()
        return Record(
            **shared,
            first_attempt_grounded=False,
            attempts=len(calls),
            source="error",
            covered=0,
            missed=tuple(beat.label for beat in beats),
            prompt_tokens=sum(call.prompt_tokens for call in calls),
            completion_tokens=sum(call.completion_tokens for call in calls),
            seconds=time.perf_counter() - started,
            text="",
            tagged_text="",
            error=f"{type(failure).__name__}: {failure}",
            calls=len(calls),
            generation_seconds=sum(call.seconds for call in calls),
        )

    calls = recorder.take()
    reached = coverage(narrated.tagged_text, facts)
    return Record(
        **shared,
        first_attempt_grounded=narrated.first_attempt_grounded,
        attempts=len(narrated.attempts),
        source=narrated.source,
        covered=len(reached.covered),
        missed=tuple(beat.label for beat in reached.missed),
        prompt_tokens=sum(call.prompt_tokens for call in calls),
        completion_tokens=sum(call.completion_tokens for call in calls),
        seconds=time.perf_counter() - started,
        text=narrated.text,
        tagged_text=narrated.tagged_text,
        calls=len(calls),
        generation_seconds=sum(call.seconds for call in calls),
    )


def measuring_provider() -> tuple[Any, Recorder]:
    """A provider whose every call is counted, and the counter.

    The transport goes in through the constructor, which is the seam
    `app/narration_provider.py` documents and the tests already use, rather
    than being attached afterwards. `provider()` with no name is Ollama, which
    is the only backend this script reaches.
    """
    recorder = Recorder()
    return provider(transport=recorder), recorder


def run_evaluation(
    feed: StatsBombEventFeed,
    goals: Sequence[tuple[int, Moment]],
    runs: int,
    json_path: Path | None = None,
    log=print,
    personas: Sequence[str] = (),
) -> tuple[Record, ...]:
    """Every goal in every voice, `runs` times each, reporting as it goes.

    `personas` is a list of persona ids, empty for the prompt with no style
    block. A `fans_only` persona is two voices, one per side, because it
    writes as the listener's team; `voices` is what expands it.

    The order is goal, then voice, then run, so a run that is stopped early
    has whole voices measured rather than one run of each.
    """
    backend, recorder = measuring_provider()

    plan = [
        (match_id, moment, voice)
        for match_id, moment in goals
        for voice in (
            voices(feed, match_id, personas)
            if personas
            else (Voice(persona=None, side=None),)
        )
    ]

    records: list[Record] = []
    total = len(plan) * runs
    done = 0
    for match_id, moment, voice in plan:
        for run in range(1, runs + 1):
            done += 1
            log(
                f"[{done}/{total}] match {match_id} "
                f"{moment.minute}:{moment.second:02d} {moment.player}, "
                f"{voice.label}, run {run}"
            )
            record = measure(
                feed, match_id, moment, run, backend, recorder, voice
            )
            records.append(record)
            log(
                "         first attempt "
                f"{'grounded' if record.first_attempt_grounded else 'refused'}"
                f", {record.source}"
                f", coverage {record.covered}/{record.beats}"
                f", {record.tokens} tokens, {record.seconds:.1f}s"
                + (f", {record.error}" if record.error else "")
            )
            if json_path is not None:
                write_json(json_path, records)
    return tuple(records)


def write_json(path: Path, records: Sequence[Record]) -> None:
    """Save the records, overwriting, after every narration.

    The run is long and a crash near the end would otherwise cost all of it.
    """
    path.write_text(
        json.dumps([asdict(record) for record in records], indent=2),
        encoding="utf-8",
        newline="\n",
    )


def read_json(path: Path) -> tuple[Record, ...]:
    """Records from a saved file, including one written before personas.

    The Task 4a and 4c files in `docs/narration_runs/` have no `persona` or
    `side` field. The defaults on `Record` fill them in as `NO_PERSONA`, which
    is what those runs were: the prompt with no style block.
    """
    rows = json.loads(path.read_text(encoding="utf-8"))
    return tuple(
        Record(**{**row, "missed": tuple(row["missed"])}) for row in rows
    )


def mean(values: Sequence[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def percent(part: int, whole: int) -> str:
    return f"{100 * part / whole:.0f}%" if whole else "n/a"


def plural(count: int, noun: str) -> str:
    """"1 goal", "4 goals". Report copy reads badly without it."""
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"


def first_attempt(rows: Sequence[Record]) -> list[Record]:
    """The model's own narrations that were grounded with no retry."""
    return [r for r in rows if r.source == MODEL and r.first_attempt_grounded]


def retried(rows: Sequence[Record]) -> list[Record]:
    """The model's own narrations that needed a second or third attempt."""
    return [r for r in rows if r.source == MODEL and not r.first_attempt_grounded]


def fell_back(rows: Sequence[Record]) -> list[Record]:
    """The ones no model attempt got through, which the template wrote."""
    return [r for r in rows if r.source == TEMPLATE]


def cell(rows: Sequence[Record], counted: bool = True) -> str:
    """A coverage cell: the mean, and how many narrations are behind it.

    An empty class reads `n/a` rather than 0%, because no narrations is not
    the same measurement as narrations that covered nothing.
    """
    if not rows:
        return "n/a"
    share = f"{mean([r.share for r in rows]) * 100:.0f}%"
    return f"{share} ({len(rows)})" if counted else share


def reproduction_command(args) -> str:
    """The command the report prints as the one that produced it.

    Only the flags that change the numbers are in it. `--out` and `--json` say
    where output went rather than what was measured, and the full run writes
    its records to a temporary path on one machine, which has no business
    being quoted in a committed document as if a reader could use it.
    """
    parts = [r".\.venv-prelude\Scripts\python.exe -I scripts\narration_eval.py"]
    if args.from_json:
        parts.append(f"--from-json {_repo_path(args.from_json)}")
    else:
        if args.goals:
            parts.append(f"--goals {args.goals}")
        if args.runs != DEFAULT_RUNS:
            parts.append(f"--runs {args.runs}")
    if args.compare:
        parts.append(f"--compare {_repo_path(args.compare)}")
        parts.append(f'--baseline-label "{args.baseline_label}"')
        parts.append(f'--compare-label "{args.compare_label}"')
        # The note is a paragraph of the report, so a command without it
        # rebuilds a document one paragraph short of this one.
        if args.compare_note:
            parts.append(f'--compare-note "{args.compare_note}"')
    if args.persona_runs:
        parts.append(f"--persona-runs {_repo_path(args.persona_runs)}")
    if args.watsonx_runs:
        parts.append(f"--watsonx-runs {_repo_path(args.watsonx_runs)}")
    if args.example_runs:
        parts.append(f"--example-runs {_repo_path(args.example_runs)}")
    if not args.from_json and args.personas:
        parts.append(f"--personas {args.personas}")
    return " ".join(parts)


def _repo_path(path: Path) -> str:
    """A path as a reader could type it, or a placeholder if it was temporary.

    The records a committed report is built from live in the repo, so the
    command quoted in it is one that runs. A path outside the repo belongs to
    one machine and is printed as a placeholder instead.
    """
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return "<records>"


def comparison(
    before: Sequence[Record],
    after: Sequence[Record],
    before_label: str,
    after_label: str,
    note: str = "",
) -> list[str]:
    """Two runs of the same goals, side by side, pass rate beside coverage.

    Only the goals in both runs are compared, because the second run covers
    the goals whose prompt changed and nothing else.

    Pass rate and coverage are printed together on purpose. Naming the beats
    in the prompt asks the model for more sentences, and more sentences is
    more chances to cite the wrong fact, so a gain in coverage bought with a
    fall in grounding is the outcome worth seeing rather than the one worth
    hiding. Nothing here is enforced: `app/grounding.py` is unchanged and
    coverage is still only reported.
    """
    # In the order the goals were narrated, which is the order the feed lists
    # them. Sorting the labels instead puts 117:05 before 22:24.
    was = {r.goal for r in before}
    shared: list[str] = []
    for record in after:
        if record.goal in was and record.goal not in shared:
            shared.append(record.goal)
    if not shared:
        return []

    def rows(records, goal):
        return [r for r in records if r.goal == goal]

    def rate(records):
        passed = sum(1 for r in records if r.first_attempt_grounded)
        return f"{passed}/{len(records)}"

    def model_coverage(records):
        """Coverage of the model's own narrations, template runs left out."""
        rows = [r for r in records if r.source == MODEL]
        return f"{mean([r.share for r in rows]) * 100:.0f}%" if rows else "n/a"

    lines = [f"## {after_label} compared with {before_label}", ""]
    add = lines.append

    if note:
        add(note)
        add("")
    add(f"The same {plural(len(shared), 'goal')} under both prompts, three "
        f"runs each. Coverage is of the model's own narrations; a template "
        "fallback reaches every beat by construction and would report its "
        "completeness as the model's.")
    add("")
    add(f"| Goal | Beats | Grounded, {before_label} | Grounded, {after_label} "
        f"| Coverage, {before_label} | Coverage, {after_label} |")
    add("| ---- | ----: | ---------------------: | ---------------------: "
        "| ----------------------: | ----------------------: |")
    for goal in shared:
        was, now = rows(before, goal), rows(after, goal)
        add(f"| {goal} | {now[0].beats} | {rate(was)} | {rate(now)} | "
            f"{model_coverage(was)} | {model_coverage(now)} |")

    was_all = [r for r in before if r.goal in shared]
    now_all = [r for r in after if r.goal in shared]
    add(f"| **all {len(shared)}** | | **{rate(was_all)}** | "
        f"**{rate(now_all)}** | **{model_coverage(was_all)}** | "
        f"**{model_coverage(now_all)}** |")
    add("")

    was_model = [r for r in was_all if r.source == MODEL]
    now_model = [r for r in now_all if r.source == MODEL]
    was_only_shot = [r for r in was_model if r.covered == 1]
    now_only_shot = [r for r in now_model if r.covered == 1]
    add(f"Narrations that cited the shot and no other key beat: "
        f"**{len(was_only_shot)} of {len(was_model)}** before, "
        f"**{len(now_only_shot)} of {len(now_model)}** after.")
    add("")
    return lines


def persona_section(records: Sequence[Record]) -> list[str]:
    """Task 6c: the same goals in every voice, pass rate beside coverage.

    Two pass rates are printed, and they answer different questions. **First
    attempt** is the model's first answer passing the check, which is what a
    prompt change moves. **After a retry** is whether any of the three
    attempts passed, which is what a listener would actually get.

    Only model-written narration counts as a pass in either. A template
    fallback is assembled by code out of the facts in one plain register, so
    it is neither the model's work nor the voice that was asked for, and a
    column counting it as a pass would report the fallback's reliability as
    the persona's. It has a column of its own instead.
    """
    if not any(r.persona != NO_PERSONA for r in records):
        return []

    goals: list[str] = []
    for record in records:
        if record.goal not in goals:
            goals.append(record.goal)
    voices_run: list[str] = []
    for record in records:
        if record.voice not in voices_run:
            voices_run.append(record.voice)

    def rate(rows: Sequence[Record], first_only: bool) -> str:
        if not rows:
            return "n/a"
        if first_only:
            passed = sum(
                1 for r in rows if r.model_wrote_it and r.first_attempt_grounded
            )
        else:
            passed = sum(1 for r in rows if r.model_wrote_it)
        return f"{passed}/{len(rows)}"

    def model_coverage(rows: Sequence[Record]) -> str:
        written = [r for r in rows if r.model_wrote_it]
        if not written:
            return "n/a"
        return f"{mean([r.share for r in written]) * 100:.0f}%"

    lines = ["## Task 6c: the three personas", ""]
    add = lines.append
    add(REMOVED_SINCE)
    add("")
    add("Every voice over the same goals, on the same development model. A "
        "persona changed the register and one rule then: the Mate was "
        "written as the listener's side and could say \"we\" over that "
        "side's facts, which is why it was run once for each team and is "
        "reported as two rows.")
    add("")
    add("A pass is narration the model wrote and the check accepted. A "
        "template fallback is a failure here, however complete it is: it is "
        "assembled by code out of the facts, so it is not what the model "
        "wrote.")
    add("")
    add("| | |")
    add("| --- | --- |")
    add(f"| command | `{_persona_command(records)}` |")
    # Per goal and in total, because they differ: the Mate runs once per
    # side, and two matches with a team in common have three sides between
    # them, so five voices appear over four per goal.
    per_goal = sorted(
        {len({r.voice for r in records if r.goal == goal}) for goal in goals}
    )
    add(f"| goals | {len(goals)} |")
    add("| voices per goal | "
        + (str(per_goal[0]) if len(per_goal) == 1
           else f"{per_goal[0]} to {per_goal[-1]}")
        + " |")
    add(f"| voices in all | {len(voices_run)}, because a fans-only persona "
        "runs once per side |")
    add(f"| runs per voice | {max(r.run for r in records)} |")
    add(f"| narrations | {len(records)} |")
    add("")

    add("### Per persona")
    add("")
    add("| Voice | Narrations | First attempt | After a retry | Fell back | "
        "Coverage | Words per sentence | Tokens | Seconds |")
    add("| ----- | ---------: | ------------: | ------------: | --------: | "
        "-------: | -----------------: | -----: | ------: |")
    for voice in voices_run:
        rows = [r for r in records if r.voice == voice]
        add(f"| {voice} | {len(rows)} | {rate(rows, True)} | "
            f"{rate(rows, False)} | {len(fell_back(rows))} | "
            f"{model_coverage(rows)} | {sentence_length(rows)} | "
            f"{mean([float(r.tokens) for r in rows]):.0f} | "
            f"{mean([r.seconds for r in rows]):.0f} |")
    add("")
    add("**Words per sentence is the one thing a register can be measured "
        "by here,** and it is in the table because the Caller's style asks "
        "for short lines and the Storyteller's for measured ones. It counts "
        "the model's own narrations only, since the fallback writes one fact "
        "a sentence whatever voice was asked for.")
    add("")

    add("### Per goal and voice")
    add("")
    add("| Goal | Voice | Key beats | First attempt | After a retry | "
        "Fell back | Coverage |")
    add("| ---- | ----- | --------: | ------------: | ------------: | "
        "--------: | -------: |")
    for goal in goals:
        for voice in voices_run:
            rows = [
                r for r in records if r.goal == goal and r.voice == voice
            ]
            if not rows:
                continue
            add(f"| {goal} | {voice} | {rows[0].beats} | "
                f"{rate(rows, True)} | {rate(rows, False)} | "
                f"{len(fell_back(rows))} | {model_coverage(rows)} |")
    add("")

    add("### Per goal, every voice together")
    add("")
    add("| Goal | Key beats | First attempt | After a retry | Fell back | "
        "Coverage |")
    add("| ---- | --------: | ------------: | ------------: | --------: | "
        "-------: |")
    for goal in goals:
        rows = [r for r in records if r.goal == goal]
        add(f"| {goal} | {rows[0].beats} | {rate(rows, True)} | "
            f"{rate(rows, False)} | {len(fell_back(rows))} | "
            f"{model_coverage(rows)} |")
    add("")

    partisan = [r for r in records if r.side]
    if partisan:
        said_as_us = [r for r in partisan if _first_person(r.text)]
        add(f"**The Mate is allowed the first person.** Of the "
            f"{plural(len(partisan), 'narration')} written in that voice, "
            f"**{len(said_as_us)}** used \"we\", \"our\" or \"us\" at "
            "all. The permission is in the prompt and in the check, and "
            "nothing makes a model take it: `app/grounding.py` has no "
            "opinion about a partisan voice that narrates plainly, and a "
            "narration that never says \"we\" is refused by nothing here.")
        add("")

    add("### One narration per voice")
    add("")
    add("The first run of each voice on each goal, as it would be shown and "
        "voiced.")
    add("")
    for goal in goals:
        for voice in voices_run:
            rows = [r for r in records if r.goal == goal and r.voice == voice]
            if not rows:
                continue
            first = rows[0]
            add(f"**{goal}**, {voice} ({first.source}, "
                f"{first.covered}/{first.beats} beats)")
            add("")
            add(f"> {first.text if first.text else '(raised: ' + first.error + ')'}")
            add("")
    return lines


def sentence_length(rows: Sequence[Record]) -> str:
    """Mean words per sentence across the model's narrations in `rows`.

    The crudest possible measure of a register, and the only one available
    without a judgement: a style that asks for short lines and gets the same
    sentence length as one that does not has not reached the model. It reads
    `tagged_text` through `app/grounding.py`'s own sentence splitter, so a
    sentence here is the same thing the check counted, and it leaves the
    template fallback out because the fallback writes one fact per sentence
    in every voice.
    """
    lengths = [
        len(sentence.text.split())
        for row in rows
        if row.model_wrote_it
        for sentence in sentences(row.tagged_text)
    ]
    return f"{mean([float(n) for n in lengths]):.1f}" if lengths else "n/a"


def _persona_command(records: Sequence[Record]) -> str:
    """The command that produced these records, read back out of them.

    Not the command that rebuilt the report, which is the one in the table at
    the top: this section is a different run over different goals, and a
    reader who wants these numbers again needs the one that generated them.
    Built from the records rather than passed in, so it cannot describe a run
    other than the one it is printed beside.
    """
    goals: list[str] = []
    for record in records:
        goal = f"{record.match_id}:{record.minute}:{record.second:02d}"
        if goal not in goals:
            goals.append(goal)
    personas: list[str] = []
    for record in records:
        if record.persona not in personas:
            personas.append(record.persona)
    chosen = (
        "all"
        if personas == [p.id for p in PERSONAS]
        else ",".join(personas)
    )
    return (
        r".\.venv-prelude\Scripts\python.exe -I scripts\narration_eval.py"
        f" --goals {','.join(goals)}"
        f" --runs {max(r.run for r in records)}"
        f" --personas {chosen}"
    )


def _first_person(text: str) -> bool:
    """Whether a narration used "we", "our" or "us" at all.

    `FIRST_PERSON` is `app/grounding.py`'s own list rather than a second one
    written here. The check is what decides whether a partisan narration may
    say these words, so counting how often a model took the permission has to
    count the same words the permission is about.
    """
    return any(
        re.search(pattern, text, re.IGNORECASE) for pattern in FIRST_PERSON
    )


def model_label(record: Record) -> str:
    """How a report names the model behind a record."""
    return record.model or "the development model"


def pass_rate(rows: Sequence[Record], first_only: bool) -> str:
    """Narrations the model wrote and the check accepted, over all of them.

    A template fallback is a failure in both columns. It is assembled by code
    out of the facts in one plain register, so it is neither the model's
    narration nor the voice that was asked for.
    """
    if not rows:
        return "n/a"
    if first_only:
        passed = sum(
            1 for r in rows if r.model_wrote_it and r.first_attempt_grounded
        )
    else:
        passed = sum(1 for r in rows if r.model_wrote_it)
    return f"{passed}/{len(rows)}"


def model_coverage(rows: Sequence[Record]) -> str:
    written = [r for r in rows if r.model_wrote_it]
    if not written:
        return "n/a"
    return f"{mean([r.share for r in written]) * 100:.0f}%"


def per_call(rows: Sequence[Record]) -> tuple[str, str]:
    """(tokens, seconds) per generation call, which is what a fan waits for.

    Per call rather than per narration, because a narration that retried
    twice cost three calls and a reader comparing two models wants the price
    of one answer. The narration-level figures are the rates beside them.
    """
    calls = sum(r.calls for r in rows)
    if not calls:
        return ("n/a", "n/a")
    tokens = sum(r.tokens for r in rows) / calls
    seconds = sum(r.generation_seconds for r in rows) / calls
    return (f"{tokens:,.0f}", f"{seconds:.1f}s")


def watsonx_section(records: Sequence[Record]) -> list[str]:
    """Task 4b: the two paid candidates, read against each other.

    Four questions, in the order they matter for picking a model: which one
    stays inside the data, whether the personas are distinguishable on it,
    what the beats block costs a model that may not need it, and what each
    answer costs in tokens and in seconds.
    """
    if not records:
        return []

    models: list[str] = []
    for record in records:
        if record.model and record.model not in models:
            models.append(record.model)

    lines = ["## Task 4b: the two watsonx candidates", ""]
    add = lines.append

    add("The paid comparison, run once. Both candidates answered the same "
        "prompts through the same endpoint with the same decoding, and a "
        "pass is narration the model wrote that `app/grounding.py` accepted: "
        "a template fallback is a failure here, as it is in the Task 6c "
        "numbers above.")
    add("")
    add(REMOVED_SINCE)
    add("")

    baseline = [r for r in records if r.arm == "b"]
    if baseline:
        add("### Grounding, with no persona")
        add("")
        add("Arm b: the same three goals as Task 6c, with no persona and "
            "so no style block, which is the prompt the local numbers were "
            "measured with.")
        add("")
        add("| Model | Narrations | First attempt | After a retry | Fell back "
            "| Coverage | Words per sentence | Tokens per call | Seconds per call |")
        add("| ----- | ---------: | ------------: | ------------: | --------: "
            "| -------: | -----------------: | --------------: | ---------------: |")
        for model in models:
            rows = [r for r in baseline if r.model == model]
            if not rows:
                continue
            tokens, seconds = per_call(rows)
            add(f"| `{model}` | {len(rows)} | {pass_rate(rows, True)} | "
                f"{pass_rate(rows, False)} | {len(fell_back(rows))} | "
                f"{model_coverage(rows)} | {sentence_length(rows)} | "
                f"{tokens} | {seconds} |")
        add("")

    personas = [r for r in records if r.arm == "a"]
    if personas:
        voices_run: list[str] = []
        for record in personas:
            if record.voice not in voices_run:
                voices_run.append(record.voice)

        add("### The personas, by model")
        add("")
        add("Arm a. Task 6c found the three registers indistinguishable on "
            "the development model, by the one measure available without a "
            "judgement: words per sentence. The same measure is in the last "
            "column here, for a model with room to tell them apart.")
        add("")
        add("| Model | Voice | Narrations | First attempt | After a retry | "
            "Fell back | Coverage | Words per sentence |")
        add("| ----- | ----- | ---------: | ------------: | ------------: | "
            "--------: | -------: | -----------------: |")
        for model in models:
            for voice in voices_run:
                rows = [
                    r for r in personas
                    if r.model == model and r.voice == voice
                ]
                if not rows:
                    continue
                add(f"| `{model}` | {voice} | {len(rows)} | "
                    f"{pass_rate(rows, True)} | {pass_rate(rows, False)} | "
                    f"{len(fell_back(rows))} | {model_coverage(rows)} | "
                    f"{sentence_length(rows)} |")
        add("")

        add("**Whether a register reached a model** is the spread of that "
            "last column across its voices. A model writing the same "
            "sentence length in every voice was given three styles and wrote "
            "one.")
        add("")
        add("| Model | Narrowest voice | Widest voice | Spread |")
        add("| ----- | --------------: | -----------: | -----: |")
        for model in models:
            lengths = []
            for voice in voices_run:
                rows = [
                    r for r in personas
                    if r.model == model and r.voice == voice
                ]
                value = sentence_length(rows)
                if value != "n/a":
                    lengths.append(float(value))
            if not lengths:
                continue
            add(f"| `{model}` | {min(lengths):.1f} | {max(lengths):.1f} | "
                f"{max(lengths) - min(lengths):.1f} |")
        add("")

        partisan = [r for r in personas if r.side]
        if partisan:
            add("**The Mate is the one voice allowed the first person**, and "
                "whether it takes it is a thing to count rather than to "
                "judge. On the development model it was none of eighteen.")
            add("")
            add("| Model | Mate narrations | Used \"we\", \"our\" or \"us\" |")
            add("| ----- | --------------: | ------------------------: |")
            for model in models:
                rows = [r for r in partisan if r.model == model]
                if not rows:
                    continue
                said = [r for r in rows if _first_person(r.text)]
                add(f"| `{model}` | {len(rows)} | {len(said)} |")
            add("")

    block_off = [r for r in records if not r.beats_block]
    if block_off:
        # One candidate ran the no-block arm, so the with-block side is that
        # candidate too. Reading it against both models would put the better
        # grounder on one side of a comparison about the prompt.
        ran_it = {r.model for r in block_off}
        block_on = [
            r
            for r in records
            if r.arm in ("b", "c2") and r.beats_block and r.model in ran_it
        ]
        shared = {r.goal for r in block_off} & {r.goal for r in block_on}
        on = [r for r in block_on if r.goal in shared]
        off = [r for r in block_off if r.goal in shared]
        add("### What the beats block costs")
        add("")
        add("Arms c and c2. Task 4c added the block because "
            "`granite4:micro` would not reach the key beats without it, and "
            "that is a statement about a three billion parameter model "
            "rather than about every model. The block asks for a sentence "
            "per beat, and more sentences is more chances to cite the wrong "
            "fact, so it buys coverage with grounding. A model that covers "
            "the beats unprompted does not need to pay that.")
        add("")
        add(f"The {plural(len(shared), 'goal')} with more than one key beat, "
            "under both prompts, on "
            + ", ".join(f"`{model}`" for model in sorted(ran_it))
            + ".")
        add("")
        add("| Prompt | Narrations | First attempt | After a retry | "
            "Fell back | Coverage | Tokens per call |")
        add("| ------ | ---------: | ------------: | ------------: | "
            "--------: | -------: | --------------: |")
        for label, rows in (("with the beats block", on),
                            ("without it", off)):
            if not rows:
                continue
            tokens, _ = per_call(rows)
            add(f"| {label} | {len(rows)} | {pass_rate(rows, True)} | "
                f"{pass_rate(rows, False)} | {len(fell_back(rows))} | "
                f"{model_coverage(rows)} | {tokens} |")
        add("")

    add("### What it cost")
    add("")
    add("| Model | Narrations | Generation calls | Tokens reported | "
        "Tokens per call | Seconds per call |")
    add("| ----- | ---------: | ---------------: | --------------: | "
        "--------------: | ---------------: |")
    for model in models:
        rows = [r for r in records if r.model == model]
        tokens, seconds = per_call(rows)
        add(f"| `{model}` | {len(rows)} | {sum(r.calls for r in rows)} | "
            f"{sum(r.tokens for r in rows):,} | {tokens} | {seconds} |")
    add(f"| **both** | {len(records)} | {sum(r.calls for r in records)} | "
        f"**{sum(r.tokens for r in records):,}** | | |")
    add("")

    add("### One narration per model and voice")
    add("")
    add("The first run of each, as it would be shown and voiced.")
    add("")
    seen: set[tuple[str, str]] = set()
    for record in records:
        key = (record.model, record.voice)
        if key in seen:
            continue
        seen.add(key)
        add(f"**`{record.model}`**, {record.voice}, {record.goal} "
            f"({record.source}, {record.covered}/{record.beats} beats)")
        add("")
        shown = record.text or f"(raised: {record.error})"
        add(f"> {shown}")
        add("")
    return lines


def example_section(
    before: Sequence[Record], after: Sequence[Record]
) -> list[str]:
    """Task 6d: the same voices, after each persona was shown its register.

    Task 4b described each register in a paragraph and got one narration in
    three voices from a model that obeyed every other rule exactly. So each
    persona was given a worked example to copy instead. This is the same
    question asked again, on the same goals and the same model, with the one
    thing changed.

    Only the goals and voices both runs covered are compared, which is what
    makes the two columns about the examples rather than about the sample.
    """
    if not before or not after:
        return []

    model = after[0].model
    goals = sorted({r.goal for r in after} & {r.goal for r in before})
    was = [r for r in before if r.model == model and r.goal in goals]
    now = [r for r in after if r.model == model and r.goal in goals]
    if not was or not now:
        return []

    voices_run: list[str] = []
    for record in list(was) + list(now):
        if record.voice not in voices_run:
            voices_run.append(record.voice)

    lines = ["## Task 6d: one worked example per persona", ""]
    add = lines.append

    add(REMOVED_SINCE)
    add("")
    add(f"`{model}` over the same {plural(len(goals), 'goal')} as the "
        "persona arm above, before and after each persona was given a short "
        "narration in its own register to copy. The example was of an "
        "invented passage, so nothing in it could be lifted into a real "
        "narration without `app/grounding.py` refusing it.")
    add("")
    add("**Words per sentence is the measure, and the spread across the "
        "voices is the answer.** A model writing the same sentence length in "
        "every voice was given three styles and wrote one.")
    add("")
    add("| Voice | Narrations | First attempt, described | First attempt, "
        "shown | Words per sentence, described | Words per sentence, shown |")
    add("| ----- | ---------: | -----------------------: | "
        "--------------------: | ----------------------------: | "
        "------------------------: |")

    def rate(rows):
        if not rows:
            return "n/a"
        passed = sum(
            1 for r in rows if r.model_wrote_it and r.first_attempt_grounded
        )
        return f"{passed}/{len(rows)}"

    spreads: dict[str, list[float]] = {"described": [], "shown": []}
    for voice in voices_run:
        old = [r for r in was if r.voice == voice]
        new = [r for r in now if r.voice == voice]
        if not old or not new:
            continue
        old_words, new_words = sentence_length(old), sentence_length(new)
        for key, value in (("described", old_words), ("shown", new_words)):
            if value != "n/a":
                spreads[key].append(float(value))
        add(f"| {voice} | {len(new)} | {rate(old)} | {rate(new)} | "
            f"{old_words} | {new_words} |")
    add("")

    if spreads["described"] and spreads["shown"]:
        add("| | Described | Shown |")
        add("| --- | ---: | ---: |")
        for label, key in (("narrowest voice", min), ("widest voice", max)):
            add(f"| {label} | {key(spreads['described']):.1f} | "
                f"{key(spreads['shown']):.1f} |")
        add(f"| **spread** | **{max(spreads['described']) - min(spreads['described']):.1f}** "
            f"| **{max(spreads['shown']) - min(spreads['shown']):.1f}** |")
        add("")

    old_mate = [r for r in was if r.side]
    new_mate = [r for r in now if r.side]
    if old_mate and new_mate:
        old_said = [r for r in old_mate if _first_person(r.text)]
        new_said = [r for r in new_mate if _first_person(r.text)]
        add(f"**The Mate's first person**: {len(old_said)} of "
            f"{len(old_mate)} narrations used \"we\", \"our\" or \"us\" when "
            f"the register was described, {len(new_said)} of "
            f"{len(new_mate)} when it was shown.")
        add("")

    first_goal = goals[0]
    add(f"### Every voice on {first_goal}, side by side")
    add("")
    add("The first run of each, after the examples. This is the comparison "
        "the decision was made on: the personas are separated by sound now, "
        "not by text.")
    add("")
    for voice in voices_run:
        rows = [r for r in now if r.voice == voice and r.goal == first_goal]
        if not rows:
            continue
        add(f"**{voice}**")
        add("")
        add(f"> {rows[0].text}")
        add("")
    return lines


def report(
    records: Sequence[Record],
    command: str,
    model: str,
    compare: Sequence[Record] = (),
    baseline_label: str = "",
    compare_label: str = "",
    compare_note: str = "",
    personas: Sequence[Record] = (),
    watsonx: Sequence[Record] = (),
    examples: Sequence[Record] = (),
) -> str:
    """The generated report.

    Doc copy, so `CLAUDE.md` governs it: no em dashes, nothing claimed that the
    numbers do not show, and the development model named at the top so no
    reader mistakes this for the model comparison.
    """
    goals: dict[str, list[Record]] = {}
    for record in records:
        goals.setdefault(record.goal, []).append(record)

    grounded = sum(1 for r in records if r.first_attempt_grounded)
    errors = [r for r in records if r.error]
    multi = [key for key, rows in goals.items() if rows[0].beats > 1]
    single = [key for key, rows in goals.items() if rows[0].beats == 1]

    lines: list[str] = []
    add = lines.append

    add("# Narration evaluation: the development model")
    add("")
    add(f"Generated by `scripts/narration_eval.py` on "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC.")
    add("")
    add("**These are development-model results and they are not a model "
        "choice.** Every narration below came from `" + model + "` running "
        "locally under Ollama, which is what this repo develops against "
        "because it is free, local and small. The watsonx candidates in "
        "`app/narration_config.py` have not been run. Task 4b runs them, says "
        "how many paid calls it will make before making them, and that is the "
        "comparison a model is chosen from.")
    add("")
    if compare:
        add(f"This report holds two runs. The body below is **{baseline_label}"
            "**, the first full measurement. The section headed "
            f"**{compare_label}** compares it against a later run of the "
            "goals whose prompt changed, so the before and the after sit in "
            "one document.")
        add("")
    if personas:
        add("A third run is at the end, under **Task 6c**: the same model "
            "over three goals in every persona, which is a different "
            "question from the two above and is reported separately rather "
            "than averaged into them.")
        add("")
    add("## How it was run")
    add("")
    add("| | |")
    add("| --- | --- |")
    add(f"| command | `{command}` |")
    add(f"| model | `{model}`, local Ollama |")
    add(f"| goals | {len(goals)} |")
    add(f"| runs per goal | {len(records) // len(goals) if goals else 0} |")
    add(f"| narrations | {len(records)} |")
    add("")
    per_goal = len(records) // len(goals) if goals else 0
    if per_goal > 1:
        add(f"{plural(per_goal, 'run')} per goal shows that the model is not "
            "deterministic. It is not enough to put an interval on any of "
            "these numbers, and none is quoted.")
    else:
        add("One run per goal, so nothing here says anything about how much "
            "the model varies between runs.")
    add("")

    add("## Per goal")
    add("")
    add("Coverage is split by what produced the narration. A template "
        "fallback reaches every key beat by construction, so folding it in "
        "with the model's own narrations would report the fallback's "
        "completeness as the model's.")
    add("")
    add("| Goal | Set piece | Key beats | First attempt grounded | "
        "Coverage, first attempt | Coverage, after a retry | "
        "Coverage, template | Tokens | Seconds |")
    add("| ---- | --------- | --------: | ---------------------: | "
        "----------------------: | ----------------------: | "
        "-----------------: | -----: | ------: |")
    for key, rows in goals.items():
        passed = sum(1 for r in rows if r.first_attempt_grounded)
        add(
            f"| {key} | {rows[0].set_piece} | {rows[0].beats} | "
            f"{passed}/{len(rows)} | "
            f"{cell(first_attempt(rows))} | "
            f"{cell(retried(rows))} | "
            f"{cell(fell_back(rows))} | "
            f"{mean([float(r.tokens) for r in rows]):.0f} | "
            f"{mean([r.seconds for r in rows]):.0f} |"
        )
    add("")

    add("## Overall")
    add("")
    add(f"- First-attempt grounding: **{grounded} of {len(records)}** "
        f"({percent(grounded, len(records))}).")
    add("")
    if multi:
        speaking = [r for r in records if r.goal in multi]
        add(f"Coverage below is averaged over the "
            f"{plural(len(multi), 'goal')} that can show a difference, which "
            "are the ones with more than one key beat: "
            + ", ".join(f"`{key}`" for key in multi) + ". The other "
            f"{plural(len(single), 'goal')} are reported under them, on "
            "their own, because their only key beat is the shot and they "
            "cannot come out as anything but 100%.")
        add("")
        add("| Narrations | Count | Coverage |")
        add("| ---------- | ----: | -------: |")
        add(f"| grounded on the first attempt | {len(first_attempt(speaking))} "
            f"| {cell(first_attempt(speaking), counted=False)} |")
        add(f"| grounded after a retry | {len(retried(speaking))} "
            f"| {cell(retried(speaking), counted=False)} |")
        add(f"| template fallback | {len(fell_back(speaking))} "
            f"| {cell(fell_back(speaking), counted=False)} |")
        add("")
        # Every grounded narration cites the shot, because the ending rule in
        # app/grounding.py requires it. So one beat covered means the shot and
        # nothing else, and counting those says what the mean hides.
        model_rows = [r for r in speaking if r.source == MODEL]
        only_shot = [r for r in model_rows if r.covered == 1]
        if model_rows:
            add(f"Of the {plural(len(model_rows), 'narration')} the model "
                f"wrote for those goals, **{len(only_shot)}** cited the shot "
                "and no other key beat. Every grounded narration cites the "
                "shot, because the ending rule requires the last sentence to, "
                "so one beat covered means the model reached nothing else. "
                "The percentages above move with how many beats a goal has "
                "rather than with how much the model found, and that is worth "
                "reading before the means are.")
            add("")

        quiet = [r for r in records if r.goal in single]
        if quiet:
            add(f"The {plural(len(single), 'goal')} with the shot as their "
                f"only key beat: {len(quiet)} narrations, coverage "
                f"{mean([r.share for r in quiet]) * 100:.0f}%.")
            add("")
    else:
        add(f"- Mean coverage: "
            f"**{mean([r.share for r in records]) * 100:.0f}%**.")
    add(f"- Narrations that fell back to the template: "
        f"**{len(fell_back(records))}**.")
    add(f"- Mean tokens per narration: "
        f"**{mean([float(r.tokens) for r in records]):.0f}** "
        f"(prompt {mean([float(r.prompt_tokens) for r in records]):.0f}, "
        f"completion {mean([float(r.completion_tokens) for r in records]):.0f}).")
    add(f"- Mean wall clock per narration: "
        f"**{mean([r.seconds for r in records]):.0f}s**, on CPU.")
    if errors:
        add(f"- Narrations that raised: **{len(errors)}**. Listed at the end.")
    add("")

    add("## What the two numbers mean")
    add("")
    add("**First attempt grounded** is `Narrated.first_attempt_grounded`: the "
        "model's first answer passed `app/grounding.py` with no retry. A "
        "narration that failed twice and passed on the third attempt counts "
        "as a failure here, because the rate is about the prompt and the "
        "model, not about how many times the pipeline is willing to ask.")
    add("")
    add("**Coverage** is the share of the key beats of the passage that the "
        "narration cited: the shot, every dribble past an opponent, and the "
        "foul for a penalty. `key_beats` in `app/narration_prompt.py` "
        "builds them, one per `Dribbled Past` record, with the `Dribble` on "
        "the other player's record joining the same beat so that citing "
        "either one counts. It lives in `app/` rather than in the measuring "
        "script because the fallback narration is built to reach every one "
        "of those beats, so the two have to be reading the same list.")
    add("")
    add("**The template rows are not a model result.** The fallback is "
        "assembled by code out of the facts and cites every key beat by "
        "construction, so it scores 100% on all nine goals and a row below "
        "that would mean the fallback and the measure have drifted apart. "
        "It is in its own column for that reason: averaged in with the "
        "model's narrations it would lift the number by being a different "
        "thing, not by the model doing better.")
    add("")
    add("The two measure different failures. The check refuses a narration "
        "that says what the data does not support. It has nothing to say "
        "about a narration that is true in every word and leaves out the "
        "whole run: on the 1986 54:18 goal the model has returned four true "
        "sentences that take facts 1 to 3 in order and then jump to the shot, "
        "passing the check and skipping all four dribbles. That narration is "
        "what coverage is for.")
    add("")
    if single:
        add(f"**Coverage says nothing on {len(single)} of these "
            f"{plural(len(goals), 'goal')}.** They have no dribble past an "
            "opponent and no penalty, so their only key beat is the shot, and "
            "`app/grounding.py` already refuses any narration whose last "
            "sentence does not cite it. Those goals read 100% whenever they "
            "pass at all, which is not evidence about the model. The key "
            "beats column is in the table so the two cases are told apart by "
            "looking. The ones with something to say are: "
            + ", ".join(f"`{key}`" for key in multi) + ".")
    else:
        add("Every goal in this run has more than one key beat, so every "
            "coverage figure below is about something. Over the full nine, "
            "five goals have the shot as their only key beat and read 100% "
            "for any narration that passed at all.")
    add("")

    if compare:
        lines.extend(
            comparison(
                records, compare, baseline_label, compare_label, compare_note
            )
        )

    if personas:
        lines.extend(persona_section(personas))

    if watsonx:
        lines.extend(watsonx_section(watsonx))

    if watsonx and examples:
        lines.extend(example_section(watsonx, examples))

    missed_rows = [r for r in records if r.missed and not r.error]
    add("## What was missed")
    add("")
    if not missed_rows:
        add("Nothing: every narration cited every key beat of its goal.")
    else:
        add("| Goal | Run | Covered | Missed |")
        add("| ---- | --: | ------: | ------ |")
        for record in missed_rows:
            add(f"| {record.goal} | {record.run} | "
                f"{record.covered}/{record.beats} | "
                f"{', '.join(record.missed)} |")
    add("")

    add("## One narration per goal")
    add("")
    add("The first run of each goal, as it would be shown and voiced. Every "
        "one of these passed the grounding check; that is the only way "
        "`narrate` returns.")
    add("")
    for key, rows in goals.items():
        first = rows[0]
        add(f"**{key}** ({first.set_piece}, {first.source}, "
            f"{first.covered}/{first.beats} beats)")
        add("")
        add(f"> {first.text if first.text else '(raised: ' + first.error + ')'}")
        add("")

    if errors:
        add("## Narrations that raised")
        add("")
        add("| Goal | Run | Error |")
        add("| ---- | --: | ----- |")
        for record in errors:
            add(f"| {record.goal} | {record.run} | {record.error} |")
        add("")

    return "\n".join(lines) + "\n"


def main(argv: Sequence[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Narrate the goals several times and measure the result.",
        epilog="Ollama only. Task 4b adds the paid comparison.",
    )
    parser.add_argument(
        "--goals",
        help="comma separated: a match id for every goal in it, or "
             "match:minute:second for one. Default: all nine.",
    )
    parser.add_argument(
        "--runs", type=int, default=DEFAULT_RUNS,
        help=f"runs per goal (default {DEFAULT_RUNS})",
    )
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_REPORT,
        help=f"where to write the report (default {DEFAULT_REPORT.name})",
    )
    parser.add_argument(
        "--json", type=Path,
        help="also save the records here, rewritten after every narration",
    )
    parser.add_argument(
        "--from-json", type=Path,
        help="rebuild the report from a saved records file, generating nothing",
    )
    parser.add_argument(
        "--compare", type=Path,
        help="a second records file to compare the report against, goal by "
             "goal, with the pass rate beside the coverage",
    )
    parser.add_argument(
        "--baseline-label", default="the first run",
        help="what to call the report's own run in the comparison",
    )
    parser.add_argument(
        "--compare-label", default="the second run",
        help="what to call the --compare run in the comparison",
    )
    parser.add_argument(
        "--compare-note", default="",
        help="one sentence saying what differs between the two runs",
    )
    parser.add_argument(
        "--personas", default=NO_PERSONA,
        help="which voices to run: 'all', 'none' (the default, the prompt "
             "with no style block), or a comma separated list of persona "
             "ids. A fans-only persona runs once per side.",
    )
    parser.add_argument(
        "--persona-runs", type=Path,
        help="a records file whose per-persona results are added to the "
             "report as its own section",
    )
    parser.add_argument(
        "--example-runs", type=Path,
        help="a records file from the worked-example round, compared against "
             "the persona arm of --watsonx-runs",
    )
    parser.add_argument(
        "--watsonx-runs", type=Path,
        help="a records file from scripts/narration_compare.py, whose paid "
             "comparison is added to the report as its own section",
    )
    args = parser.parse_args(argv)

    if args.runs < 1:
        raise SystemExit("--runs has to be at least 1")

    command = reproduction_command(args)

    if args.from_json:
        records = read_json(args.from_json)
        model = DEVELOPMENT_MODEL.model
    else:
        feed = StatsBombEventFeed()
        goals = goal_moments(feed, args.goals)
        personas = read_personas(args.personas)
        model = provider().model
        pairs = (
            sum(len(voices(feed, match_id, personas)) for match_id, _ in goals)
            if personas
            else len(goals)
        )
        print(f"{len(goals)} goal(s), {pairs} goal-voice pair(s), "
              f"{args.runs} run(s) each, {pairs * args.runs} narration(s)")
        if personas:
            print(f"personas {', '.join(personas)}")
        print(f"model ollama {model}")
        print("a CPU-only generation takes a while\n")
        started = time.perf_counter()
        records = run_evaluation(
            feed, goals, args.runs, args.json, personas=personas
        )
        print(f"\ndone in {time.perf_counter() - started:.0f}s")

    if not records:
        raise SystemExit("nothing was measured")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    against = read_json(args.compare) if args.compare else ()
    by_persona = read_json(args.persona_runs) if args.persona_runs else ()
    paid = read_json(args.watsonx_runs) if args.watsonx_runs else ()
    shown = read_json(args.example_runs) if args.example_runs else ()
    args.out.write_text(
        report(
            records,
            command,
            model,
            compare=against,
            baseline_label=args.baseline_label,
            compare_label=args.compare_label,
            compare_note=args.compare_note,
            personas=by_persona,
            watsonx=paid,
            examples=shown,
        ),
        encoding="utf-8",
        newline="\n",
    )

    grounded = sum(1 for r in records if r.first_attempt_grounded)
    print(f"first attempt grounded {grounded}/{len(records)}")
    print(f"mean coverage          "
          f"{mean([r.share for r in records]) * 100:.0f}%")
    print(f"report                 {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
