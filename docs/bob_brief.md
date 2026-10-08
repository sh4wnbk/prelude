# Bob's brief: the EventFeed module

This is the contract for the EventFeed and moment-detection module. The module
is reserved for you; nobody else in this repo implements it, and the rest of the
codebase is written to wait for it.

Everything you need is already in the repo: the interface, the acceptance tests,
and a script that fetches the data. Nothing is implemented.

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

`tests/test_event_feed.py`, 14 tests. Run them with:

```
.\.venv-prelude\Scripts\python.exe -m pytest
```

Right now all 14 fail with the same message:

```
Failed: No EventFeed implementation yet: app.statsbomb_event_feed does not
exist. This is the expected failure until Bob builds the module; see
docs/bob_brief.md.
```

That is the only reason they fail. Nothing else in the suite is broken.

Two other messages exist and mean different things. `app.statsbomb_event_feed
exists but does not provide StatsBombEventFeed` means the module is there but
the class is missing or misnamed. A raw `ModuleNotFoundError` naming some other
module means your module imports something that is not installed; that one is
re-raised with a full traceback rather than reported as the module being
absent.

| Group | Covers |
| ----- | ------ |
| `TestContract` | satisfies the protocol; `load_match` returns the whole feed |
| `Test1986` | three goals, their exact values, order, floored clock, index reconciliation |
| `Test2022` | goals match the raw feed, index reconciliation, shootout excluded |
| `TestEventWindow` | window ends at the moment, is in feed order, is within the span, reports the requested span, returns untouched source records |

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
- **Never open, print, or edit `.env`.** `.env.example` lists the variable
  names.
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
export, starting with `.env`.

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
