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

Grounding and coverage answer different questions, and both are needed. The
check refuses a narration that says something the data does not support; it has
nothing to say about a narration that supports everything it says and leaves
out the goal's whole story. A first live run on the 1986 54:18 goal passed the
check with four true sentences that skipped all four dribbles, which is the run
coverage exists to put a number on.

Run it:

    .\.venv-prelude\Scripts\python.exe -I scripts\narration_eval.py --help
    .\.venv-prelude\Scripts\python.exe -I scripts\narration_eval.py \
        --goals 3750191:54:18 --runs 1 --out out.md
    .\.venv-prelude\Scripts\python.exe -I scripts\narration_eval.py

The full default run is nine goals times three runs on a CPU, so it takes a
while. `--json` writes the records after every narration, so a run that dies at
goal eight keeps the first seven and the report can be rebuilt from the file
with `--from-json` instead of generating again.
"""

import argparse
import json
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.event_feed import Moment  # noqa: E402
from app.grounding import sentences  # noqa: E402
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
from app.statsbomb_event_feed import StatsBombEventFeed  # noqa: E402

#: The two demo matches, in the order the app lists them.
MATCHES = (3750191, 3869685)

#: Runs per goal. Three is enough to show that a model is not deterministic and
#: cheap enough to sit through; it is not enough for a confidence interval, and
#: the report says so rather than implying a precision this does not have.
DEFAULT_RUNS = 3

DEFAULT_REPORT = ROOT / "docs" / "narration_eval.md"

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


class Recorder:
    """A transport that passes requests through and keeps the token counts.

    `Transport` is the seam the provider already has for tests, so measuring
    tokens needs no change to `app/`. The counts come from Ollama's own
    `prompt_eval_count` and `eval_count` rather than from counting words, which
    would be a different number wearing the same name. A response without them
    reports zero rather than guessing.
    """

    def __init__(self, inner: Transport = post) -> None:
        self._inner = inner
        self.calls: list[Call] = []

    def __call__(
        self, url: str, body: bytes, headers: Mapping[str, str]
    ) -> Mapping[str, Any]:
        started = time.perf_counter()
        answer = self._inner(url, body, headers)
        self.calls.append(
            Call(
                prompt_tokens=int(answer.get("prompt_eval_count") or 0),
                completion_tokens=int(answer.get("eval_count") or 0),
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

    @property
    def clock(self) -> str:
        return f"{self.minute}:{self.second:02d}"

    @property
    def goal(self) -> str:
        """How the report names this goal, the same way in every table."""
        return f"{self.match_id} {self.clock} {surname(self.player)}"

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
) -> Record:
    """Narrate one goal once and record what it cost and what it reached.

    A narration that raises is recorded rather than allowed to end the run. A
    loop this long dying on goal eight and reporting nothing would be the worst
    of both: the time spent and no evidence.
    """
    facts = facts_from_buildup(feed.buildup(match_id, moment))
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
    )

    try:
        narrated = narrate(feed, match_id, moment, narration_provider=backend)
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
) -> tuple[Record, ...]:
    """Every goal, `runs` times each, in order, reporting as it goes."""
    backend, recorder = measuring_provider()

    records: list[Record] = []
    total = len(goals) * runs
    for index, (match_id, moment) in enumerate(goals, start=1):
        for run in range(1, runs + 1):
            done = (index - 1) * runs + run
            log(
                f"[{done}/{total}] match {match_id} "
                f"{moment.minute}:{moment.second:02d} {moment.player}, "
                f"run {run}"
            )
            record = measure(feed, match_id, moment, run, backend, recorder)
            records.append(record)
            log(
                "         first attempt "
                f"{'grounded' if record.first_attempt_grounded else 'refused'}"
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


def report(
    records: Sequence[Record],
    command: str,
    model: str,
    compare: Sequence[Record] = (),
    baseline_label: str = "",
    compare_label: str = "",
    compare_note: str = "",
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
        model = provider().model
        print(f"{len(goals)} goal(s), {args.runs} run(s) each, "
              f"{len(goals) * args.runs} narration(s)")
        print(f"model ollama {model}")
        print("a CPU-only generation takes a while\n")
        started = time.perf_counter()
        records = run_evaluation(feed, goals, args.runs, args.json)
        print(f"\ndone in {time.perf_counter() - started:.0f}s")

    if not records:
        raise SystemExit("nothing was measured")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    against = read_json(args.compare) if args.compare else ()
    args.out.write_text(
        report(
            records,
            command,
            model,
            compare=against,
            baseline_label=args.baseline_label,
            compare_label=args.compare_label,
            compare_note=args.compare_note,
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
