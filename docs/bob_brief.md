# Bob's brief: the EventFeed module

This is the contract for the EventFeed and moment-detection module. The module
is reserved for you; nobody else in this repo implements it.

**Status: built, including `buildup`.**

- `app/statsbomb_event_feed.py` is in the repo and satisfies the `EventFeed`
  protocol in full. It took three sessions: the build, a fix to where the event
  window ends, then `buildup`.
- `tests/test_event_feed.py` holds 27 tests and they all pass.
- `buildup` landed in `24e1a8d`, and that session merged `BuildupFeed` into
  `EventFeed`, which is what the Task 3 brief below asked for. `BuildupFeed`
  survives in `app/event_feed.py` as an alias of `EventFeed`, so the tests'
  existing imports and `isinstance` checks keep working unchanged.

The contract is what any further change to the module is measured against.

## What you build

One file: **`app/statsbomb_event_feed.py`**, exporting a class
**`StatsBombEventFeed`** that satisfies the `EventFeed` protocol in
`app/event_feed.py`.

The tests construct it with no arguments:

```python
from app.statsbomb_event_feed import StatsBombEventFeed
feed = StatsBombEventFeed()
```

If it needs constructor arguments, they all need defaults.

## The interface

`app/event_feed.py` holds the contract and nothing else. It declares two frozen
dataclasses and one `Protocol`, with no behaviour anywhere in it:

```python
@dataclass(frozen=True)
class Moment:
    type: str       # the kind of moment; the tests only cover "Goal"
    team: str       # full StatsBomb team name
    player: str     # full StatsBomb player name
    minute: int     # raw, floored match clock
    second: int

@dataclass(frozen=True)
class EventWindow:
    moment: Moment
    events: Sequence[RawEvent]   # raw feed records, oldest first
    seconds_before: float        # the span requested, not the span covered

class EventFeed(Protocol):
    def load_match(self, match_id: int) -> Sequence[RawEvent]: ...
    def defining_moments(self, match_id: int) -> Sequence[Moment]: ...
    def event_window(self, match_id: int, moment: Moment,
                     seconds_before: float) -> EventWindow: ...
```

`RawEvent` is `Mapping[str, Any]`: a StatsBomb event exactly as it appears in the
JSON. `event_window` hands back untouched source records, because
"Verified from play data" has to be able to point at something in `data/raw/`.
One test asserts each returned event is identical to the record with the same
`id` in the source file, so do not reshape, trim, or normalize them.

The contract is yours to change if it is wrong, but change it deliberately and
update `tests/test_event_feed.py` in the same commit. Do not work around it.

### What counts as a defining moment

For the acceptance tests, a defining moment is a **goal**: an event with
`type.name == "Shot"` and `shot.outcome.name == "Goal"`, with `Moment.type` set
to `"Goal"`.

**Periods 1 to 4 only.** Period 5 is the penalty shootout. Its penalties are
goals in the feed but not goals in the match, and must not be returned. In the
2022 final this is the difference between 6 moments and 12.

`Moment` carries no period field, so a caller cannot filter the shootout out
afterwards. That makes the exclusion a rule you apply, not a decision you can
defer. If you would rather expose `period` and let callers decide, that is a
reasonable change: make it in `app/event_feed.py` and update the tests.

Moments come back earliest first, ordered by period, then minute, then second.

`minute` is the raw StatsBomb value, which floors the match clock. Minute 50
second 27 is in the 51st minute as a broadcast would caption it. Do not add one;
the display layer decides how to caption it.

## Input files

Everything is read from `data/raw/`, which is gitignored and absent from a fresh
clone. Rebuild it with:

```
.\.venv-prelude\Scripts\python.exe -I scripts\fetch_statsbomb.py
```

| File | What it is |
| ---- | ---------- |
| `events/3750191.json` | 1986 Argentina vs England, 2,748 events |
| `events/3869685.json` | 2022 Argentina vs France, 4,407 events |
| `matches/43/54.json` | 1986 World Cup match index |
| `matches/43/106.json` | 2022 World Cup match index |
| `competitions.json` | competition and season index |

The match index files are a second, independent source for the scoreline, and
two tests use them to cross-check your goal counts. Keep them in mind: if your
goal detection disagrees with the recorded score, one of the two is wrong.

## The tests to pass

`tests/test_event_feed.py`, 27 tests. Run them with:

```
.\.venv-prelude\Scripts\python.exe -m pytest
```

`pytest -q` reports:

```
212 passed
```

The total covers far more than this module now. Phase 4 added the narration
provider, the prompt and the grounding check, each with its own tests; run
`pytest tests/test_event_feed.py` to see this module's tests alone.

The suite still guards the import, and three messages mean three different
things if that changes. In `tests/test_event_feed.py`, every test that builds
the feed failing with
`No EventFeed implementation yet: app.statsbomb_event_feed does not exist`
means the module file has gone.
`app.statsbomb_event_feed exists but does not provide StatsBombEventFeed` means
the module is there but the class is missing or misnamed. A raw
`ModuleNotFoundError` naming some other module means the module imports
something that is not installed; that one is re-raised with a full traceback
rather than reported as the module being absent.

| Group | Covers |
| ----- | ------ |
| `TestContract` | satisfies the protocol; `load_match` returns the whole feed |
| `Test1986` | three goals, their exact values, order, floored clock, index reconciliation |
| `Test2022` | goals match the raw feed, index reconciliation, shootout excluded |
| `TestEventWindow` | window ends at the moment, is in feed order, is within the span, reports the requested span, returns untouched source records |
| `TestBuildup` | the buildup contract: one possession for open play, the previous possession too for a set piece, the foul that won each penalty, feed order, period containment, untouched source records |

### Where the expected values come from

The two matches are checked differently on purpose.

**1986 values are written out literally** in the test file, taken from
`docs/data_check.md`, which `scripts/data_check.py` generated:

| Team | Player | Minute | Second |
| ---- | ------ | -----: | -----: |
| Argentina | Diego Armando Maradona | 50 | 27 |
| Argentina | Diego Armando Maradona | 54 | 18 |
| England | Gary Lineker | 80 | 37 |

They are hardcoded so that a regression shows up as a disagreement with a report
that was produced independently of your module.

**2022 values are read out of the raw JSON at test time**, not written down. The
test derives the expected goals from `events/3869685.json` and cross-checks the
count against the score in `matches/43/106.json`. Nothing about that match is
recalled from memory, by anyone.

A note on the data, because it has already caught one error: a claim that
Argentina took 13 of 15 shots in the 1986 match is wrong. The feed has 27 shots,
Argentina 15 and England 12. Read values out of the data rather than trusting a
remembered figure, including remembered figures about famous matches.

## Rules

These come from `CLAUDE.md`, which applies to the whole repo.

- **Do not guess IDs or values.** Read them from the data.
- **Never open, print, or edit the credentials file.** It lives outside the
  repo, at `~/.prelude/.env` by default. `.env.example` in the repo lists the
  variable names and holds no values.
- **Never commit raw StatsBomb data.** `data/raw/` is gitignored; keep it that
  way.
- **The three real inputs are play data, GPS presence, and audio narration.**
  Do not add a fourth. If the module seems to need another source, say so and
  stop.
- **No verdict nicknames in app output.** Describe what the data records.
- **"Verified from play data" only over narration grounded in the data**, which
  is what the raw-record rule on `event_window` exists to support.
- **Docs describe only code that exists**, and carry no em dashes.
- **Report executed evidence**, meaning the command and its real output, not a
  claim that something works.

## Session exports

**Export each task to `bob_sessions/`.** One export per task, so the work is
reviewable afterwards and the reasoning behind a detection rule is not lost with
the session.

`bob_sessions/` is in the repo and the policy is settled: **exports are
committed, not ignored**, and each one is scrubbed of credentials before it is
committed. `bob_sessions/README.md` carries the scrub list and the file naming.
`.bobignore` lists what must never be read into a session or appear in an
export. The live credentials are not in the repo at all.

## Defaults and stop conditions

The interface leaves some things open. Each one below has a default. Apply the
default rather than guessing, and do not invent an alternative. Where a task
cannot be done under the default, stop and report the collision instead of
deciding unilaterally.

**`Moment` carries no `period` field.** Default: leave it that way. Excluding
the shootout is therefore a rule the implementation applies, not something a
caller filters afterwards. Adding `period` is allowed if the module genuinely
needs it, but change `app/event_feed.py` and `tests/test_event_feed.py` in the
same commit, so the contract and its tests never disagree.

**Goals are the only defining moments.** Default: `defining_moments` returns
Goal-outcome shots from periods 1 to 4 and nothing else. Red cards, penalties
awarded and near misses are plausible kinds, but they are unspecified and
`Moment.type` has no agreed vocabulary beyond `"Goal"`. **Stop and report** if a
task requires a kind other than a goal. Do not invent type names: downstream
copy keys off them.

**A short window at the start of a period is correct.** Default: when
`seconds_before` reaches back past the first event of the period, return what
exists and truncate there. Do not pad the window, and do not cross a period
boundary to fill it. `EventWindow.seconds_before` still reports the span that
was requested rather than the span covered, which is what the contract says.

**GPS presence does not enter this interface.** Default: `EventFeed` reads play
data only. Do not add a GPS parameter, a fourth input, or a stand-in for one.
**Stop and report** if a task appears to require GPS presence inside this
module.

## Task 3: the buildup

**Built, in `24e1a8d`.** The brief below is kept as written, because it is what
the method was built to and what any further change to it is measured against.
What changed since: `buildup` is implemented in `app/statsbomb_event_feed.py`,
all 13 of its tests pass, and the protocol merge the brief asked for was done
in the same commit.

### Why it exists

Task 2 of the last session found this, and `HANDOFF.md` records it: a penalty is
alone in its own possession. A 30 second `event_window` around one of the 2022
final's three penalties holds exactly one event, the kick. The foul that won the
penalty is in the possession before, 71 to 91 seconds earlier.

Narration needs that foul. Padding the window to reach it would break the
window's own truncation rule, which is deliberate, so reaching back is a
separate method rather than a change to `event_window`.

### What you build

`buildup(match_id, moment)` on `StatsBombEventFeed`, returning a `Buildup`.
The shapes are already in `app/event_feed.py`:

```python
SET_PIECE_SHOT_TYPES = frozenset({"Penalty", "Free Kick", "Corner"})

@dataclass(frozen=True)
class Buildup:
    moment: Moment
    events: Sequence[RawEvent]   # raw records, feed order, ending on the shot
    possessions: Sequence[int]   # possession numbers included, in order
    set_piece: str | None        # the shot's recorded type, or None
```

`buildup` is declared on `EventFeed` in `app/event_feed.py`. It was declared
on a separate `BuildupFeed` protocol while it was pending, so that the tests
proving `EventFeed` was satisfied kept passing; the build merged the two, which
is what the brief asked for. `BuildupFeed` remains in the file as an alias of
`EventFeed`, which is why the tests' imports and `isinstance` checks needed no
change.

### The rules

Each one has a test. The full statement is the docstring on
`EventFeed.buildup`; this is the summary.

1. **The goal's possession, truncated at the shot.** Every event of the
   possession the goal shot belongs to, up to and including the shot. What
   StatsBomb records after the shot in that possession, usually the
   goalkeeper's event, is excluded. Same truncation as `event_window`, for the
   same reason.
2. **The previous possession, in full, only for a set piece.** A goal is a set
   piece when its `shot.type.name` is in `SET_PIECE_SHOT_TYPES`, read off the
   goal event itself. Then the possession numbered one below the goal's comes
   first, in full, followed by the goal's possession. An open play goal gets one
   possession and nothing reaches back.
3. **Raw source records, feed order, oldest first.** Untouched, exactly as
   `event_window` returns them. A test compares each returned event to the
   record with the same `id` in the source file.
4. **Do not cross a period boundary.** Every event is in the goal's own period.
   This is not hypothetical: possession 99 of the 1986 match spans half time,
   and four possessions of the 2022 final span a period boundary. If the
   previous possession began in an earlier period, only its events in the goal's
   period belong.
5. **Do not pad.** If the previous possession does not exist, or lies entirely
   in an earlier period, return what exists and no more. A short buildup is
   correct, the same way a short window is correct.

### Read the type off the shot, not off `play_pattern`

`shot.type.name` is where the set piece is recorded. On all three 2022
penalties, `play_pattern.name` is `"Other"`, which says nothing useful. There is
a test for this.

### What the data actually holds

Read out of `data/raw/`. The four goals the tests cover:

| Match | Goal | `shot.type.name` | Possessions | Events |
| ----- | ---- | ---------------- | ----------- | -----: |
| 1986 | 54:18 Maradona | `Open Play` | 117 | 24 |
| 2022 | 22:24 Messi | `Penalty` | 31, 32 | 100 |
| 2022 | 79:24 Mbappé | `Penalty` | 162, 163 | 10 |
| 2022 | 117:05 Mbappé | `Penalty` | 237, 238 | 11 |

Each penalty's goal possession contributes exactly one event, the kick.
Everything else comes from the possession before.

The foul in each penalty's previous possession:

| Goal | Foul event | Player | Clock |
| ---- | ---------- | ------ | ----- |
| 22:24 | `Foul Committed` | Ousmane Dembélé (France) | 20:53 |
| 79:24 | `Foul Committed` | Nicolás Hernán Otamendi (Argentina) | 78:13 |
| 117:05 | `Foul Committed` | Gonzalo Ariel Montiel (Argentina) | 115:39 |

**Two of the three also have a `Foul Won` record; the 117:05 one does not.**
The tests assert on `Foul Committed`, which all three have. If you key anything
on `Foul Won` it will work twice and fail once.

### Two of the three set piece types have no goal to test against

Among the goals in these two matches, `shot.type.name` is only ever
`"Open Play"` or `"Penalty"`. `"Free Kick"` appears on six 1986 shots, none of
which scored, and `"Corner"` appears in neither match. So rule 2 is specified
for all three set piece types and exercised by tests for penalties only. Build
all three branches from the recorded type; do not add a fourth type, and do not
narrow the set to `"Penalty"` because that is what the tests reach.

### The tests to pass

`tests/test_event_feed.py::TestBuildup`, 13 tests. All 13 pass.

While the method was unbuilt, 12 of them failed with
`No buildup implementation yet: StatsBombEventFeed has no buildup method.`
That guard is still in the test file, so the same message returns if the method
is ever removed.

The thirteenth, `test_the_expected_values_are_what_the_raw_data_says`, passed
throughout and must keep passing. It checks the expected values in the test
file against `data/raw/` without going near the implementation, so a wrong
expectation fails on its own line instead of looking like a bug in the code.
If it ever fails, the test file is wrong.

The expected values are written out literally in the test file, read out of
`data/raw/`. They are written down rather than derived, on purpose: a helper
that derived them would reimplement the rule under test and then agree with any
implementation that made the same mistake.

### Stop conditions

The same rules as before apply, and these are the ones this task is most likely
to run into.

**Do not change what counts as a defining moment.** `buildup` takes a `Moment`
that `defining_moments` already returned. If a buildup seems to need a kind of
moment that does not exist yet, **stop and report it**.

**Do not add a GPS parameter or a fourth input.** `buildup` reads play data
from `data/raw/` and nothing else.

**Do not reach for a shot type that is not in the data.** If a goal turns up
whose `shot.type.name` is none of the five StatsBomb values you can see in
these two files, **stop and report it** rather than adding a branch for a value
you have not read.

**If a rule above is wrong, say so and change the contract deliberately.** The
contract is yours to change, in `app/event_feed.py`, with
`tests/test_event_feed.py` updated in the same commit. Do not work around it,
and do not leave the two disagreeing.
