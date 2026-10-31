# Bob's brief: the EventFeed module

This is the contract for the EventFeed and moment-detection module. The module
is reserved for you; nobody else in this repo implements it.

**Status: built, including `buildup`.**

- `app/statsbomb_event_feed.py` is in the repo and satisfies the `EventFeed`
  protocol in full. It took three sessions: the build, a fix to where the event
  window ends, then `buildup`.
- `tests/test_event_feed.py` holds 28 tests and they all pass. The 28th,
  `test_goal_possession_does_not_cross_period_boundary`, came with the period
  gap fix in the Task 4 session.
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

`tests/test_event_feed.py`, 28 tests. Run them with:

```
.\.venv-prelude\Scripts\python.exe -m pytest
```

`pytest -q` reports:

```
905 passed
```

The total covers far more than this module now. Phase 4 added the narration
provider, the prompt, the grounding check and the evaluation, each with its
own tests; run `pytest tests/test_event_feed.py` to see this module's tests
alone.

**The suite is green, so any failure means something is actually wrong.**

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

`tests/test_event_feed.py::TestBuildup`, 14 tests. All 14 pass. The fourteenth,
`test_goal_possession_does_not_cross_period_boundary`, was added with the period
gap fix in the Task 4 session.

While the method was unbuilt, 12 of them failed with
`No buildup implementation yet: StatsBombEventFeed has no buildup method.`
That guard is still in the test file, so the same message returns if the method
is ever removed.

Of the first thirteen, `test_the_expected_values_are_what_the_raw_data_says`, passed
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

## Task 4: the orchestrator

**Status: built, in `1c4063a`.** `app/orchestrator.py` implements the six
functions and `PreludeOrchestrator`, whose `opening` puts their answers
together. The contract is unchanged and its functions still raise; callers
import from `app/orchestrator.py`.

**The header part of it is being replaced, which is Task 5 below.** The
greeting, the phase, the score state, the outcome and the default persona are
untouched and still pass. The header tests that were handed over with this
task are gone: `tests/test_orchestrator.py` is 72 tests now, 46 of them green
and 26 of them Task 5's.

The tests as first written imported the six functions from the contract, which
could only raise, so they could not pass without the contract changing. Bob
was told not to edit it, and worked around it by overwriting the contract's
functions from `app/orchestrator.py` at import time, with an import added to
`tests/conftest.py` to make that run first. The fault was in the tests, so the
fix went there: they now import the functions from `app/orchestrator.py`, and
the overwrite and the extra import were removed. Three tests on `opening`
itself were added at the same time, since none of the 44 called it.

Build the module that decides what is said **before** the narration starts.

### Why it exists

The narration says only what the play data proves. That rule is what makes
"Verified from play data" mean anything, and it leaves the narration unable to
do three ordinary things: greet the listener, know which side they are on, and
say anything at all after the goal, because it stops dead there on purpose
(`docs/VOICE.md`).

So everything addressed to the fan happens in one line before the narration,
and that line is this module's whole output. Today the app has a placeholder,
"Here's the buildup.", written in no code at all. You replace it.

Nothing here is generated by a model and nothing here is grounded. The header
is built from what the app already knows: when kickoff was, who scored, how
far into the match it happened, and which side the listener picked on the card
in Task 7. It must never carry the grounding label, and `app/grounding.py`
never sees it. If it did it would refuse it, because a line spoken to the fan
is exactly what the ending rule keeps out of narration.

### What you build

`app/orchestrator.py`, satisfying `Orchestrator` in
`app/orchestrator_contract.py`. The contract declares every shape, the wording
table and six functions, and every function raises `NotImplementedError`. You
implement them and the `opening` method that puts their answers together.

Do not change `app/orchestrator_contract.py`. If something in it is wrong or
missing, **stop and report it** rather than editing the contract to fit the
implementation.

### The rules

**The greeting word.** `TONIGHT` when kickoff is at or after `EVENING_CUTOFF`,
which is 17:00, and `TODAY` otherwise. At the cutoff counts as evening. Only
the time of day decides it; the date never does.

**The phase.** A share of regulation time, never a count of minutes. Early is
the first third, late is the final quarter, and the middle is what is left.
`EARLY_UNTIL` and `LATE_FROM` are in the contract. A moment exactly on a
boundary belongs to the later phase. A moment past regulation, which both 2022
extra time goals are, gives a ratio above 1 and is late.

This is the rule that makes the module sport agnostic, and it is the one most
likely to get a 90 written into it. The seconds count: 29:59 and 30:00 are
different phases of a 90 minute game.

**The score state.** `AHEAD`, `LEVEL` or `BEHIND` for the listener's side,
using the score **after** the moment, which is what they are looking at while
they listen. Conceding does not mean behind: Argentina conceded at 80:37 in
1986 and were still 2 to 1 up.

**The outcome.** `SCORED` or `CONCEDED` from the listener's point of view. A
neutral listener did neither, and `score_state` and `outcome` both raise
`ValueError` for one rather than inventing an answer.

**The header.** A prefix looked up by outcome and phase, then a single space,
then a fan tail; a neutral listener got a tail and no prefix. **That header is
gone.** Task 5 below replaced it with the game focused one, and the follow-up
after that task removed its table and both tails from the contract. The rules
it was built to are kept here only as the record of what this task built.

**The default persona.** `MATE` for a fan, `STORYTELLER` for a neutral
listener. The personas themselves are Task 6; the contract declares their ids
and nothing else about them. A partisan voice is for somebody who has a side:
telling a neutral listener "late one for your side" would be telling them they
support a team they did not pick.

### The tests to pass

`tests/test_orchestrator.py` is 72 tests now and held 48 at the end of this
task, all of them passing then. 44 of those 48 were handed over with the brief,
and 38 failed with `NotImplementedError` until the module was built. Four were
added afterwards: the 3 in `TestTheOpening`, and one holding the late scored
wording to England's only goal in 1986 when that wording changed.

**Those are this task's numbers and not the file's now.** The header tests
handed over here were replaced when the header became game focused, and the one
covering the late scored wording went with them. Task 5 below has the current
split.

`TestTheContractItself` reads the wording table and the cutoff. It passed
before the module existed and must keep passing: it is what makes a change to
the wording a deliberate edit rather than something that slips through.

`TestAnotherSport` is a sixty minute game in a sport that does not exist. It is
the proof that nothing counts in football: if a 90 is ever written into the
phase rule, those tests fail and no test about the two demo matches does.

The expected values are literals written beside each test, including ones that
could be derived from the contract's table. A test that computed its
expectation the way the implementation will would agree with any implementation
that made the same mistake.

### Stop conditions

The usual rules apply, and these two are the ones this task will meet.

**Do not touch the narration or the grounding check.** The header is not
narration and must not pass through `app/grounding.py`. If the header seems to
need something from the event data, **stop and report it**: the three real
inputs in `CLAUDE.md` have not changed.

**Do not invent the personas.** The contract names three ids. Their
descriptions, writing styles and voices are Task 6, and a persona given a
personality here is one that has to be unpicked later.

### One known gap, fixed in the same session

The gap as described here was in the set-piece reach back a possession. That
reach already filtered by the goal's period. The unguarded path was the goal's
own possession: a possession that straddled a period boundary would have
carried events from the earlier period into the buildup. The goal possession
now filters by period too, and
`tests/test_event_feed.py::TestBuildup::test_goal_possession_does_not_cross_period_boundary`
builds a feed with that shape and checks only the goal's period is returned.
No goal in either demo match triggers it.


## Task 5: the game-focused header

**Status: built, in `7f1b21e`.** `transition` and `header` are in
`app/orchestrator.py` and `PreludeOrchestrator.opening` says the new line. The
brief below is the record of what the task asked for.

Build the header that says what the goal did to the score.

### Why it exists

The header is the one line in the app addressed to the fan, and it was built
from how the fan should feel: a prefix by whether their side scored or
conceded and how far into the match it was ("Great start.", "Still early.").
Shawn's decision after Phase 4 is that it should say what happened to the game
instead, in the same words for everybody. A fan with a side and a listener
with none are looking at the same scoreboard, and the app guessing at a mood
is the part of that line that was not earned.

So allegiance no longer reaches the header at all. What it picks is the
persona, which `default_persona` already does and which Phase 5 turns into a
voice.

Nothing here is generated by a model and nothing here is grounded. The header
is built from the fixture, the score before the moment and the score after it.
It must never carry the "Verified from play data" label, and
`app/grounding.py` never sees it.

### What you build

Two functions in `app/orchestrator.py`, both declared in
`app/orchestrator_contract.py` and both raising there:

```
def transition(moment: ScoringMoment) -> str
def header(event: Event, moment: ScoringMoment) -> str
```

`PreludeOrchestrator.opening` then uses the new `header`. Its signature does
not change: it still takes the event, the moment and the listener, and the
listener still decides the persona.

Do not change `app/orchestrator_contract.py`. If something in it is wrong or
missing, **stop and report it** rather than editing the contract to fit the
implementation.

### The rules

**The score before the moment is given, never derived.** `ScoringMoment`
carries `score_before_a` and `score_before_b` as well as `score_a` and
`score_b`. Do not subtract one from the scoring side to get the before: a
score can move by any number of points, and `tests/test_orchestrator.py`
holds a sport whose scores move three at a time. The shape refuses a score
that one side scoring cannot explain, so you can rely on exactly one side
having risen.

**The transition is one of five, from the scoring side's point of view**, and
`TRANSITIONS` in the contract names them:

| Transition | The scoring side went |
| ---------- | --------------------- |
| `TAKE_LEAD` | level to ahead |
| `OVERTAKE` | behind to ahead |
| `EXTEND` | ahead to further ahead |
| `CLOSE_GAP` | behind to still behind |
| `DRAW_LEVEL` | behind to level |

The five are exhaustive over a score that rose for one side only, which is the
only score the shape accepts.

**No transition may depend on anything earlier in the match.** There is no
"again" and no "back in front". The two scores do not record whether this side
has led before, and a header claiming a goal that nothing it was built from
holds is the mistake the old wording made: a cell reading "Your side again."
was false for England's only goal in 1986.

**The header is the wording, then the score, then the tail**, joined by single
spaces:

`HEADER_WORDING[transition(moment)]`, with `{scorer}` filled in from the team
that scored, then `SCORE_LINE` with both team names and the score after the
moment, then `HEADER_TAIL`. Read every one of them out of the contract rather
than writing any of them into your code: the wording is the starting wording,
Shawn writes the final wording, and changing a word should be a one line edit
to that file.

**`TAKE_LEAD` and `OVERTAKE` share a sentence** in the table as it stands.
They are still two transitions, so do not collapse them: a later wording that
tells them apart should not need the classification rewritten.

**The header takes no listener and must not differ by one.** Three listeners
over one moment get one line.

### The tests to pass

`tests/test_orchestrator.py`, 72 tests, all passing. They cover every goal in
both demo matches, with the clock and both scores read out of `data/raw/`
rather than written down, and the header each one has to produce written out
beside it.

Two of them were built with the wrong scoring side and Bob found it:
`test_three_points_from_far_behind_closes_the_gap` and
`test_three_points_can_draw_it_level` in `TestAnotherSport` both used the
default `side=TEAM_A` for a scenario that needs `side=TEAM_B`. The defect was
in the tests, not the implementation. Shawn approved the fix in the session,
only `side=TEAM_B` was added, and no expected value changed.

`TestAnotherSport` is the sixty minute game whose scores move three at a time.
It holds the `OVERTAKE` transition, which neither demo match contains: a goal
is worth one, so a side that was behind is level or still behind afterwards. A
rule that recovered the before by subtracting one would call that overtake a
draw level, and that is the test which says so.

`TestTheContractItself` reads the wording table. It is what makes a change to
the wording a deliberate edit rather than something that slips through.

The expected values are literals written beside each test. A test that
computed its expectation the way the implementation does would agree with any
implementation that made the same mistake.

### Stop conditions

The usual rules apply, and these are the ones this task will meet.

**Do not touch the narration or the grounding check.** The header is not
narration and must not pass through `app/grounding.py`.

**Do not reach for the event data.** The header is built from the fixture and
the two scores it is given. If it seems to need a player, a shot or anything
else out of `data/raw/`, **stop and report it**: the three real inputs in
`CLAUDE.md` have not changed, and the header is not one of them.

**Do not keep the old header alive beside the new one.** `header` is one
function and the new rules replace the old ones. There is no fallback to the
prefixes, no flag that picks between the two headers, and no second function
that still builds the old line.

**Do not invent the personas.** The contract names three ids and
`app/personas.py` holds the three. They are separated by voice in Phase 5, and
nothing about that belongs in this task.

### When you are done

**Print this reminder at the end of the session**, so the export is not
forgotten:

> Export this session to `bob_sessions/phase4_task5_header.md`, scrub it
> against the list in `bob_sessions/README.md` before committing, and check
> the diff rather than the commit.

## Task 6: the header on the moment card

**Status: built, in `aab7093`.** `scripts/write_headers.py` writes
`hero.opening` into `app/web/matches.json` and the moment card shows it.

Put the orchestrator's header on the moment card, in place of the heading the
card carries today. That is the whole task.

### Why it exists

The moment card opens on "You stepped away. Here’s the buildup you missed."
That line tells the fan they were absent, which the opener rule in
`docs/VOICE.md` keeps out, and the orchestrator now has the line that replaces
it: what the goal did to the score, the same for every listener.

The app is a static site, so nothing in the browser can run
`app/orchestrator.py`. It does not need to. The header does not depend on the
listener, so it can be computed once per match ahead of time and stored in
`app/web/matches.json`, which the screens already read.

### What you build

Three changes, and nothing else.

1. **`scripts/write_headers.py`, new.** For each match in
   `app/web/matches.json`, it finds the hero goal (`hero.event`) among
   `StatsBombEventFeed().defining_moments(match_id)`, works out the score
   before and after it by counting the goals before it in that list, and
   builds the `Event` and `ScoringMoment` the orchestrator takes: teams are
   `home_team` as team A and `away_team` as team B, the kickoff is
   `picker.kickoff`, the sport is `"football"`, regulation is 90 minutes. It
   calls `greeting_word` and `header` from `app/orchestrator.py` and writes
   `hero.opening = {"greeting": ..., "header": ...}` into the file.
   - It exposes `openings()`, returning `{match_id: {"greeting", "header"}}`
     computed from the data without writing anything.
   - `--check` writes nothing and exits 1 if the file's `hero.opening`
     differs from `openings()` for any match, 0 if they agree.
   - `--path PATH` points it at another copy of `matches.json`; the default is
     `app/web/matches.json`.
   - When writing, it changes `hero.opening` and nothing else in the file, and
     keeps the file's existing formatting. The file round-trips exactly through
     `json.dumps(doc, indent=2, ensure_ascii=False) + "\n"` written as UTF-8,
     so write it that way. Do not touch `_note`.
2. **`app/web/prelude_03_moment_card.html`.** The `<h1>` that holds "You
   stepped away. Here’s the buildup you missed." gets `data-field="hero_header"`,
   and its inline text becomes the 1986 header exactly as the script writes it.
   Keep the element, its classes and everything around it. The eyebrow above
   it is out of scope; leave it as it is.
3. **`app/web/match-content.js`.** In `renderHero`, set `hero_header` from
   `match.hero.opening.header`, the same way `hero_caption` is set. If
   `opening` is missing, leave the inline text alone.

Run the script once to write the two openings, and commit the result.

### The tests to pass

`tests/test_moment_card_header.py`, 10 tests, all failing until this is
built. The expected headers are literals, produced by running the
orchestrator over `data/raw/`; if the script disagrees with one, the script is
wrong. Run them with:

```
.\.venv-prelude\Scripts\python.exe -m pytest tests/test_moment_card_header.py -q
```

Then run the full suite and the four gates (`scripts/data_check.py`,
`scripts/scan_copy.py`, `scripts/check_match_copy.py`,
`scripts/check_docs.py`). `check_docs.py` will fail on this brief naming
`scripts/write_headers.py` as unbuilt and on test counts; that is expected and
is Claude Code's follow-up. Any other gate failure is yours to report.

### Stop conditions

**Do not change `app/orchestrator.py`, `app/orchestrator_contract.py`,
`app/statsbomb_event_feed.py` or any test.** If the script cannot produce an
expected header, stop and report what it produced.

**Do not edit any other screen, any other field, or any doc.** No restyling,
no new elements, no Profile tab, no "Who are you with" card, no name. Those
are later tasks.

**Do not write the header by hand into `matches.json`.** It comes from the
script, so that `--check` can prove it.

**Do not add the "Verified from play data" label near the header.** The header
is not narration.

### When you are done

**Print this reminder at the end of the session**, so the export is not
forgotten:

> Export this session to `bob_sessions/phase4_task6_card_header.md` and
> `.png`, scrub it against the list in `bob_sessions/README.md` before
> committing, and check the diff rather than the commit.

## Task 7: the screen copy

**Status: built, in `8215108`.** The six copy changes are in, and the script
was rerun so both headers end "Here's how it happened."

Change six pieces of copy to the wording Shawn settled on 2026-10-29, and run
`scripts/write_headers.py` once. That is the whole task.

### Why it exists

Some copy still tells the fan they were away after they came back, which the
opener rule in `docs/VOICE.md` keeps out, and some repeats "buildup" on screens
that already say it. The header's last sentence has already been changed in
the contract, from "Here's the buildup." to "Here's how it happened.", and its
tests updated, so the header is handled by rerunning the script.

### What you change

Every new line is given exactly. Copy it character for character.

1. **`app/web/prelude_03_moment_card.html`, the label above the heading.**
   Remove the separator dot and the "YOU STEPPED AWAY" span after "THE
   BUILDUP": the two elements
   `<span class="w-1 h-1 rounded-full bg-surface-variant"></span>` and the
   `<span ...>YOU STEPPED AWAY</span>` that follows it. Leave "THE BUILDUP"
   and its wrapper as they are.
2. **The same file, the share sheet title.** In the script near the end,
   `title: 'PRELUDE: The buildup you missed.',` becomes
   `title: 'Listen on Prelude.',`.
3. **`app/web/matches.json`, `hero.share_text`.** For 3750191:
   `Maradona's solo goal as it happened.` For 3869685:
   `Di María's counter goal as it happened.`
4. **The moment card's inline share text.** The `data-share-text` attribute on
   `#shareAction` becomes the 1986 line from item 3.
5. **`app/web/matches.json`, `live_seated.after.help`, both matches.**
   `Ready when you are.`
6. **`app/web/matches.json`, `_note`.** It says the values are not generated
   and that nothing in `app/web` reads the file, and both are now false.
   Replace the two sentences "These values are fixed content, not generated:
   scripts/check_match_copy.py verifies every name, minute, score and count
   against data/raw and exits 1 on a mismatch." and "Nothing in app/web reads
   this yet; the screens still carry their copy inline, and wiring them to it
   is Phase 5." with these two, and leave the rest of `_note` as it is:
   "These values are fixed content, except hero.opening, which
   scripts/write_headers.py generates from the orchestrator: run it again
   rather than editing it by hand. scripts/check_match_copy.py verifies every
   name, minute, score and count against data/raw and exits 1 on a mismatch."
   and "app/web/match-content.js renders the screens from this file; the
   screens also carry the default match's copy inline, for when it cannot be
   fetched."

Then run `scripts/write_headers.py` (no flags) to rewrite both
`hero.opening` headers, and change the moment card's inline `<h1>` text to the
new 1986 header exactly as the script wrote it.

Write `matches.json` the way the script does:
`json.dumps(doc, indent=2, ensure_ascii=False) + "\n"` as UTF-8, so the diff
shows only the lines that changed.

### The tests to pass

`tests/test_screen_copy.py`, 10 tests, all passing now. Nine failed until
this was built; the tenth checks that "THE BUILDUP" stays.

Four in `tests/test_moment_card_header.py` also failed until the script was
rerun and the inline heading updated.

Then the full suite, target 0 failed, and the four
gates. `check_docs.py` failing on the quoted pytest result in this brief is
expected and is Claude Code's follow-up; report any other gate failure.

### Stop conditions

**Change only the six items above, the rerun, and the inline heading.** No
other copy, no restyling, no new elements, no Python other than running the
script, no tests, no docs.

**Keep these exactly as they are**, even though they mention being away:
"Tap as you leave your seat. Prelude keeps track while you’re away.", the
"STEPPED AWAY · TAP TO RETURN" label on the Live screen, "Step away" on the
ticket screen, and "The moment you missed deserves an encore!" in the Moments
footer. Shawn chose to keep them.

**If a gate refuses one of the new lines, stop and report the gate's
message.** Do not reword a line to get past a check.

### When you are done

**Print this reminder at the end of the session**, so the export is not
forgotten:

> Export this session to `bob_sessions/phase4_task7_screen_copy.md` and
> `.png`, scrub it against the list in `bob_sessions/README.md` before
> committing, and check the diff rather than the commit.

## Task 8: where the 1986 fan steps away

**Status: built, in `30116a2`.** The 1986 fan leaves at 52' with the score
1 to 0, and `scripts/check_match_copy.py` passes.

Move the 1986 step-away to after the first goal. That is the whole task.

### Why it exists

The 1986 fan leaves at 48' with the score 0 to 0 and comes back at 55' to
2 to 0. Two goals fall in that window, at 50:27 and 54:18, and the moment card
tells one buildup, so the fan returns to a score the card does not explain.
Shawn's decision on 2026-10-29: the fan sees the 50:27 goal from their seat
and leaves at 52' with the score 1 to 0. One goal is missed, the 54:18, and the
card tells it. 2022 already works this way and does not change.

`scripts/check_match_copy.py` now refuses any match whose window holds more or
fewer than one goal, so it fails on 1986 until this is built.

### What you change

1. **`app/web/matches.json`, match 3750191, `live_seated.before`.** Set
   `display_minute` to `52` and `home_goals` to `1`. Leave `away_goals` at `0`,
   `period` at `2`, `period_label` at `"2H"`, and every other key as it is.
2. **`app/web/prelude_02_live_seated.html`, the inline 1986 copy.** The
   `state_badge` text becomes `2H · 52'`, the `half_line` text becomes
   `SECOND HALF · 52'`, and the `home_goals` text becomes `1`. Change only
   those three text values.

Write `matches.json` as before: `json.dumps(doc, indent=2,
ensure_ascii=False) + "\n"` as UTF-8.

### The tests to pass

`tests/test_live_before.py`, 7 tests, all passing now. Six failed until this
was built; the seventh checks the period stays the second half.

Then the full suite, target 0 failed, and the four gates, with
`scripts/check_match_copy.py` now passing. `check_docs.py` failing on the
quoted pytest result in this brief is expected and is the follow-up's; report
any other gate failure.

### Stop conditions

**Change only the five values above.** Not the `after` state, not the hero,
not the Moments list, not 2022, not any script, test or doc.

**If `scripts/check_match_copy.py` still fails after the change, stop and
report its message.** Do not edit the checker.

### When you are done

**Print this reminder at the end of the session**, so the export is not
forgotten:

> Export this session to `bob_sessions/phase4_task8_step_away.md` and `.png`,
> scrub it against the list in `bob_sessions/README.md` before committing, and
> check the diff rather than the commit.

## Task 9: the "Who are you with" card

**Status: built, in `c6fc1ad`.** Two things were corrected after it, in the
follow-up. `headerWithName` passed the name to `replace()` as the replacement
string, which reads `$&` as the matched text, so a name like "Jo $& Smith" came
out "Jo . Smith"; the name is now joined as a plain string, and
`tests/test_listener_card.py::TestTheNameInTheHeader::test_the_name_is_never_a_replacement_string`
holds it. And four classes in `app/web/listener-card.js` were not ones the app
already used; `rounded-2xl` became `rounded-xl`, `gap-4` became
`gap-space-md`, and `max-w-sm` went, since the phone frame already sets the
width.

Ask the fan, once per match, who they are with and what to call them, keep the
answer on the phone, and put the name at the end of the moment card's header.
Also stop the Live screen's clock badge wrapping. That is the whole task.

### Why it exists

The orchestrator already knows what to do with a listener's side: it picks the
persona. Nothing in the app asks for it yet. Shawn settled the wording on
2026-10-26 and the name's place on 2026-10-29: the name goes on the header's
last sentence, "Argentina extend the lead. Argentina 2, England 0. Here's how
it happened, Olivia." The name is the fan's own, typed by them; it never leaves
the phone.

### What you build

1. **`app/web/match-content.js`, storage and the name join.** Beside the
   existing `sessionStorage` helpers, and in their style (every read and write
   in `try`/`catch`, a failure degrading quietly):
   - `listenerFor(matchId)` and `setListener(matchId, allegiance)`, under the
     key `"prelude.listener." + matchId`. The value is exactly `"team_a"`,
     `"team_b"` or `"neutral"`; anything else reads as `null`.
   - `nameFor()` and `setName(name)`, under the one key `"prelude.name"`.
     `setName` trims the name and collapses inner whitespace to single spaces,
     cuts it to 40 characters, and removes the key when the result is empty.
   - `headerWithName(header, name)`: with no name, the header unchanged. With
     a name, the header with its final `.` replaced by `, ` + name + `.`.
   - In `renderHero`, set `hero_header` to
     `headerWithName(match.hero.opening.header, nameFor())`, as
     `setText("hero_header", headerWithName(...))`.
   - Add all five to `window.Prelude`.
2. **`app/web/listener-card.js`, new.** It waits for the match with
   `Prelude.whenMatches`, finds the one whose `match_id` is `Prelude.matchId`,
   and does nothing if there is none or the fetch failed. If
   `Prelude.listenerFor(Prelude.matchId)` is `null`, it shows a full-screen
   overlay holding one card:
   - the question `"Who are you with " + match.hero.opening.greeting + "?"`;
   - three choice buttons, in this order: `match.home_team` (value
     `"team_a"`), `match.away_team` (value `"team_b"`), and `Just here for the
     game` (value `"neutral"`). Choosing one marks it with
     `aria-pressed="true"` and clears the others;
   - a text field labelled `What should we call you?`, with
     `placeholder="Optional"`, prefilled with `.value = Prelude.nameFor() ||
     ""`;
   - a `Continue` button, disabled until a choice is made. It calls
     `setListener` and `setName` with the field's value, then removes the
     overlay.
   Build the markup the way `app/web/manual-entry.js` does: a string assigned
   once with `innerHTML`, using its `FIELD` and `LABEL` class strings for the
   field and its Continue button classes for Continue. Use only classes already
   used in `app/web/`. The choice buttons use the existing
   `bg-surface-container` and `bg-primary-container` pair for unselected and
   selected. The fan's name never goes into an `innerHTML` string: it is set
   with `.value` and read with `.value`. Keep every line that assigns
   `innerHTML` free of the word "name" in any form, including ids and
   variables, because `tests/test_listener_card.py` checks exactly that: call
   the field `listener-call` or similar, and assign with a single
   `container.innerHTML = markup(match);`.
3. **`app/web/prelude_02_live_seated.html`.** Load the card after
   `match-content.js`, exactly as
   `<script src="listener-card.js?v=__V__"></script>`. On the `state_badge`
   span, add the class `whitespace-nowrap` and change nothing else.

### The tests to pass

`tests/test_listener_card.py`, 17 tests, all passing now. Fifteen of the
first sixteen failed until this was built; the seventeenth was added in the
follow-up.

Then the full suite, target 0 failed, and the four gates.
`check_docs.py` failing on the quoted pytest result in this brief is expected
and is the follow-up's; report any other gate failure.

### Stop conditions

**Build only the three changes above.** No persona choice, no Profile tab, no
change to the moment card's markup, no change to any other screen, no tests,
no docs, no Python.

**The card sends nothing anywhere.** No `fetch`, no `XMLHttpRequest`, no
analytics, nothing in the URL. The answer lives in `sessionStorage` only.

**Do not change any copy.** The question, the three choices, the label, the
placeholder and the button are given above exactly.

**If the overlay cannot be made to work with the existing classes, stop and
report what is missing.** Do not add a stylesheet or new Tailwind config.

### When you are done

**Print this reminder at the end of the session**, so the export is not
forgotten:

> Export this session to `bob_sessions/phase4_task9_listener_card.md` and
> `.png`, scrub it against the list in `bob_sessions/README.md` before
> committing, and check the diff rather than the commit.

## Task 10: the Profile screen

**Status: built, in `4ef3aa0`.** Two corrections in the follow-ups. The new
screen did not keep the head of `prelude_04_moments.html` as the brief said:
it carried its own Tailwind config, with `primary-container` at `#5c3d00` in
place of `#ffb703` and an older label scale, so every amber element on it read
as disabled. Shawn noticed the Change button looked greyed out on his phone.
The head was restored and
`tests/test_profile.py::TestTheProfileScreen::test_it_uses_the_same_design_tokens_as_every_other_screen`
now requires every screen to carry the same config. And `asked()`
matched the letters "ask" anywhere in the query, so `?task=1` would also have
reopened the card; it now reads `ask=1` as a whole parameter.

Add a Profile screen that shows the fan's name and side for the match, with a
Change button that reopens the "Who are you with" card, and make the person
icon and the Profile tab lead to it. That is the whole task.

### Why it exists

Shawn found on 2026-10-29 that once the card is answered nothing lets the fan
change it: the answer lasts the tab's session and a refresh keeps it. The
person icon in every header is decorative and the Profile tab is disabled, so
both now lead here.

The persona cards are not part of this task. A persona is a voice, no voice is
chosen until Phase 5, and a picker today would offer a choice that changes
nothing.

### What you build

1. **`app/web/prelude_07_profile.html`, new.** Take `prelude_04_moments.html`.
   Keep everything before its `<main` unchanged. Replace its whole `<main>`
   element with exactly this:

   ```
   <main class="flex flex-col relative w-full pt-16 pb-24 bg-surface min-h-screen"><div class="flex flex-col w-full px-screen-edge-mobile py-space-sm gap-space-md">
   <span class="font-label-sm text-label-sm tracking-[0.22em] text-primary-container font-semibold uppercase">PROFILE</span>
   <div class="w-full rounded-xl bg-surface-container p-card-padding-md flex flex-col gap-space-md border border-surface-container-highest/30">
   <div class="flex flex-col gap-space-2xs"><span class="font-label-sm text-label-sm text-outline uppercase">Name</span><span class="font-body-lg text-body-lg text-on-surface" data-field="profile_name">Not set</span></div>
   <div class="flex flex-col gap-space-2xs"><span class="font-label-sm text-label-sm text-outline uppercase">With</span><span class="font-body-lg text-body-lg text-on-surface" data-field="profile_with">Not set</span></div>
   <button class="mt-1 w-full h-touch-target-min rounded-full bg-primary-container text-on-primary-container font-label-lg text-label-lg font-bold tracking-wider uppercase flex items-center justify-center" id="profileChange" type="button">Change</button>
   </div>
   </div>
   <script>
     document.getElementById('profileChange').addEventListener('click', function () {
       window.location.href = Prelude.url('prelude_02_live_seated.html') + '&ask=1';
     });
   </script>
   </main>
   ```

   Keep the bottom nav after it, with two changes: the Moments item loses
   `aria-current="page"` and takes the inactive classes the Live item has
   (`text-on-surface-variant hover:text-on-surface transition-colors` in place
   of `transition-colors text-primary-container`), and the Profile item becomes
   the current one: `aria-current="page"`, the active classes the Moments item
   had, and `href="prelude_07_profile.html?v=__V__"`.
2. **The Profile tab on screens 01 to 04.** On the nav's `data-path="profile"`
   item, remove `aria-disabled="true"`, `tabindex="-1"`, and the classes
   `opacity-40` and `pointer-events-none`, and add
   `href="prelude_07_profile.html?v=__V__"`. Nothing else in the nav changes.
3. **The person icon on screens 01 to 06 and on the new screen.** Replace
   `<div class="w-8 h-8 rounded-full bg-primary flex items-center justify-center"><span class="material-symbols-outlined text-on-primary text-[18px]">person</span></div>`
   with
   `<a aria-label="Profile" class="w-8 h-8 rounded-full bg-primary flex items-center justify-center" href="prelude_07_profile.html?v=__V__"><span class="material-symbols-outlined text-on-primary text-[18px]">person</span></a>`.
4. **`app/web/match-content.js`, `renderProfile(match)`.** If there is no
   `profile_name` field, return. Otherwise set `profile_name` to `nameFor()`
   or `"Not set"`, and `profile_with` to `match.home_team` for `"team_a"`,
   `match.away_team` for `"team_b"`, `"Just here for the game"` for
   `"neutral"`, and `"Not set"` when `listenerFor(match.match_id)` is `null`.
   Use `setText` for both. Call it from `render`, after `renderMoments`.
5. **`app/web/listener-card.js`, reopening.** Add `function asked()`, true when
   the URL's query has `ask=1`; it must contain the string `"ask"`. When the
   matches arrive, show the card if `Prelude.listenerFor(Prelude.matchId)` is
   `null` **or** `asked()` is true. When it is reopened with an answer stored,
   press that answer's button (so Continue is enabled) and keep the name in the
   field. After Continue, if `asked()`, call
   `window.history.replaceState(null, "", Prelude.url("prelude_02_live_seated.html"))`
   so a reload does not reopen it.

### The tests to pass

`tests/test_profile.py`, 25 tests, all passing now. The 24 written with the
brief failed until this was built; the 25th was added in the follow-up. Then the
full suite, target 0 failed, and the four gates. `check_docs.py` failing on the
quoted pytest result in this brief, and on `app/web/prelude_07_profile.html`
being listed as absent, is expected and is the follow-up's; report any other
gate failure.

### Stop conditions

**Build only the five changes above.** No persona cards, no other copy, no new
classes, no tests, no docs, no Python.

**Do not load `listener-card.js` on the Profile screen.** Change sends the fan
to Live, where the card already lives.

**The name is set with `setText` only**, never with `innerHTML`.

### When you are done

**Print this reminder at the end of the session**, so the export is not
forgotten:

> Export this session to `bob_sessions/phase4_task10_profile.md` and `.png`,
> scrub it against the list in `bob_sessions/README.md` before committing, and
> check the diff rather than the commit.

## Task 11: audio playback on the moment card

**Status: built, in `35708cd`, with one fix in the follow-up.** The player
took `Prelude.whenMatches`'s argument for the list of matches, but it is the
whole document, or null on a failed fetch. The loop over it never ran, so the
play button stayed disabled even with a recording. A browser run with a silent
test file under one key caught it; the player now reads `doc.matches`, returns
on null, and
`tests/test_narration_player.py::TestThePlayer::test_it_reads_the_list_out_of_the_document`
fails on the original.

Make the moment card's player play the recording the fan should hear, and
nothing else. That is the whole task.

### Why it exists

The player is a mock: the play button swaps its icon and plays nothing, and the
waveform shows a fixed progress. The speech backend now exists
(`app/tts.py`), and the hero recordings are generated after the November 1
TTS reset, so the player is built now against a map that is empty until then.

Which recording a fan hears is the orchestrator's decision, made in Python
ahead of time like the header: `default_persona` picks the voice from the
listener's side, and `situation` in `app/delivery.py` picks the delivery. The
browser only looks up its answer.

### What you build

1. **`scripts/write_headers.py`.** Add `voice_keys(path=...)`, returning
   `{match_id: {"team_a": key, "team_b": key, "neutral": key}}`, where each key
   is `default_persona(listener) + "_" + situation(moment, listener)` for a
   `Listener` with that allegiance and the same hero `ScoringMoment` the header
   is built from. Import `default_persona` from `app/orchestrator.py`,
   `situation` from `app/delivery.py`, and `NEUTRAL` and `Listener` from
   `app/orchestrator_contract.py`. Build the moment once, in one place, for
   both the opening and the keys. When writing, set `hero.voice_for` to the
   keys and set `hero.audio` to `{}` only if it is not already present. `--check`
   exits 1 if `hero.voice_for` differs, as it already does for `hero.opening`.
   Run the script once.
2. **`app/web/narration-player.js`, new.** Everything below runs only after
   the document has loaded: `match-content.js` is loaded in the `<head>`, so
   wrap the work in a `start()` function and call it on `DOMContentLoaded`, or
   at once if `document.readyState` is no longer `"loading"`, exactly as
   `match-content.js` does.
   - Find `#playBtn`, `#playIcon`, `#timerReadout`, `#scrubTrack` and
     `#replayAction`. The waveform bars are the `div`s inside `#scrubTrack`
     with the class `w-[3px]`, and the playhead is the `.absolute` element
     inside it.
   - Show zero progress at once: every bar takes `bg-secondary-container/70`
     and loses `bg-primary-container`, the playhead's `style.left` is `"0%"`,
     and `playBtn.disabled = true`.
   - With `Prelude.whenMatches`, find the match for `Prelude.matchId`. The key
     is `match.hero.voice_for[Prelude.listenerFor(Prelude.matchId) ||
     "neutral"]`, and the file is `match.hero.audio[key]`. With no file, leave
     `playBtn.disabled = true` and stop. With one, create `new Audio(file)` and
     enable the button.
   - The play button plays or pauses, with `#playIcon` reading `pause` or
     `play_arrow`. On `timeupdate`, the first `round(bars × currentTime /
     duration)` bars take `bg-primary-container` and the rest
     `bg-secondary-container/70`, the playhead's `style.left` is the same
     fraction as a percentage, and `#timerReadout` shows the elapsed time as
     `m:ss`. On `ended`, the icon returns to `play_arrow`.
   - `#replayAction` sets `currentTime` to `Math.max(0, currentTime - 10)` and
     plays. A click on `#scrubTrack` seeks to the clicked fraction.
3. **`app/web/prelude_03_moment_card.html`.** Load the player right after
   `match-content.js`, exactly as
   `<script src="narration-player.js?v=__V__"></script>`. In the inline script,
   delete `let isPlaying = false;`, `togglePlay` and the play and replay
   listeners. Keep the sync and share listeners. Change no markup.

### The tests to pass

`tests/test_narration_player.py`, 15 tests, all passing now. Thirteen of the
first fourteen failed until this was built; the fifteenth was added in the
follow-up.

Then the full suite, target 0 failed, and the five gates
(`scripts/data_check.py`, `scripts/scan_copy.py`,
`scripts/check_match_copy.py`, `scripts/check_docs.py`,
`scripts/check_vocabulary.py`). `check_docs.py` failing on the quoted pytest
result in this brief, and on `app/web/narration-player.js` being listed as
absent, is expected and is the follow-up's; report any other gate failure.

### Stop conditions

**Do not add audio files or entries to `hero.audio`.** The recordings come
after the TTS reset; with none, the play button is simply disabled.

**Do not touch `app/tts.py`, `app/delivery.py`, `app/personas.py`, any test or
any doc**, and make no TTS calls.

**No `innerHTML` and no network calls in the player.** The audio element loads
its file; nothing else is fetched.

**Do not change the moment card's markup**, including the waveform and the
playhead's classes: `docs/DESIGN.md` quotes them. The player changes classes
and styles at run time only.

### When you are done

**Print this reminder at the end of the session**, so the export is not
forgotten:

> Export this session to `bob_sessions/phase5_task11_player.md` and `.png`,
> scrub it against the list in `bob_sessions/README.md` before committing, and
> check the diff rather than the commit.

## Task 12: "Your narrator" on Profile

**Status: built, in `35c91b6`.** Checked in Chromium: The Buddy marked for an
England fan, The Storyteller for a neutral listener, the note on tapping The
Caller, and Change as an outline.

Show the three narrators on Profile, mark the one the fan's answer picked,
say "coming soon" when another is tapped, rename the partisan one to "The
Buddy", and make Change an outline. That is the whole task.

### Why it exists

The personas are now voices, and a fan should see who is narrating. Choosing
one is not live: the recordings exist only for the narrator each answer picks,
and recording every narrator in every situation would spend about half a
month's Text to Speech characters. Shawn's decisions on 2026-10-30: the heading
is "Your narrator", the partisan persona is shown as "The Buddy" because "Mate"
reads British in a North American market, and tapping another narrator shows
that it is coming soon. With the current narrator shown as an amber card,
Change becomes an outline so the two do not compete.

### What you build

1. **`app/personas.py`.** Change `name="The Mate"` to `name="The Buddy"`.
   Change nothing else: the id stays `mate`, and so do the contract constant,
   the delivery table and the recordings' keys.
2. **`scripts/write_narrators.py`, new.** Writes `app/web/narrators.json` as
   `{"narrators": [{"id", "name", "profile"} for each persona in PERSONAS]}`,
   in `PERSONAS` order, with `json.dumps(doc, indent=2, ensure_ascii=False) +
   "\n"` as UTF-8. `--check` writes nothing and exits 1 if the file is
   missing or differs, 0 if it matches. `--path PATH` points it at another
   file. Run it once.
3. **`app/web/prelude_07_profile.html`.** After the card that holds Name, With
   and Change, and before the closing `</div>` of the column, add exactly:

   ```
   <span class="font-label-sm text-label-sm tracking-[0.22em] text-primary-container font-semibold uppercase">Your narrator</span>
   <div class="flex flex-col gap-space-xs" data-field="narrator_list"></div>
   <p class="font-body-md text-body-md text-on-surface-variant" data-field="narrator_note" hidden></p>
   ```

   On the Change button, replace `bg-primary-container text-on-primary` with
   `bg-transparent border border-primary-container text-primary-container`,
   and remove `shadow-lg shadow-primary-container/20`. Keep its other classes.
4. **`app/web/match-content.js`, `renderNarrators(match)`.** Call it from
   `render`, after `renderProfile`. If `narrator_list` or `narrator_note` is
   missing, return. Fetch `narrators.json` (with `?v=` + `VERSION` when there
   is one, as `matches.json` is fetched); on failure leave the list empty. The
   current narrator's id is the part before the first `_` of
   `match.hero.voice_for[listenerFor(match.match_id) || "neutral"]`. For each
   narrator, append a `button` (type `button`) built with `createElement`,
   holding two `span`s set with `textContent`: the name
   (`font-label-lg text-label-lg font-bold`) and the profile line
   (`font-body-md text-body-md`). The button's classes are
   `w-full text-left rounded-xl p-card-padding-sm flex flex-col gap-space-2xs`
   plus `bg-primary-container text-on-primary` for the current narrator, with
   `aria-current="true"`, or `bg-surface-container-highest text-on-surface`
   for the others. Tapping a narrator that is not current sets
   `narrator_note`'s text to its name followed by
   ` is coming soon. For now, Prelude picks your narrator from who you're with.`
   and un-hides it. Tapping the current one does nothing.

### The tests to pass

`tests/test_narrators.py`, 14 tests, all passing now. Thirteen failed until
this was built; the fourteenth checks the persona ids are unchanged.

Then the full suite, target 0 failed, and the five gates. `check_docs.py`
failing on the quoted pytest result in this brief, and on
`scripts/write_narrators.py` being listed as absent, is expected and is the
follow-up's; report any other gate failure.

### Stop conditions

**Do not make choosing a narrator work.** Nothing is stored and nothing else
changes when a narrator is tapped; only the note appears.

**No `innerHTML` in `renderNarrators`.** Names and descriptions come from a
file and are set as text.

**Change only the four things above.** No other screen, no other copy, no
tests, no docs, no TTS or watsonx calls. "The Mate" appearing in docstrings
and docs elsewhere is the follow-up's.

### When you are done

**Print this reminder at the end of the session**, so the export is not
forgotten:

> Export this session to `bob_sessions/phase5_task12_narrators.md` and `.png`,
> scrub it against the list in `bob_sessions/README.md` before committing, and
> check the diff rather than the commit.

## Task 13: rename the persona id from mate to buddy

**Status: built, in `4e61a10`.** Test names that spelled the old id were
renamed with it, so the docs that cite them were updated in the follow-up.

Rename the partisan persona's id, constant and every live use from "mate" to
"buddy", so the code says what the screen says. That is the whole task.

### Why it exists

Task 12 changed the name fans see to "The Buddy" and kept the id `mate`.
Shawn's call on 2026-10-30 is to rename the id too, now, before the hero
recordings exist: their filenames are built from the id, and once
`3750191_mate_scored.mp3` is committed, renaming means regenerating audio
against a monthly character cap.

### What you change

1. **`app/orchestrator_contract.py`.** `MATE = "mate"` becomes
   `BUDDY = "buddy"`. No alias: `MATE` must no longer exist.
2. **Every live use of the constant, the id and the word**, in `app/*.py`,
   `app/web/*.js`, `app/web/*.json`, `app/web/*.html`, `scripts/*.py` except
   `scripts/narration_eval.py`, and `tests/test_*.py` except
   `tests/test_buddy_rename.py`: `MATE` becomes `BUDDY`, `THE_MATE` becomes
   `THE_BUDDY`, the string `"mate"` becomes `"buddy"`, and "Mate" or "mate"
   in comments and docstrings becomes "Buddy" or "buddy". Keys built from the
   id change with it: `mate_scored` becomes `buddy_scored`, `mate_conceded`
   becomes `buddy_conceded`. Change expected values in tests only where they
   spell the old id; change nothing else a test asserts.
3. **Regenerate the two written files**, never by hand:
   `scripts/write_headers.py` (for `hero.voice_for`) and
   `scripts/write_narrators.py` (for `app/web/narrators.json`).

### Do not rename the past

`scripts/narration_eval.py` writes the report of runs made while the persona
was the Mate, and `docs/narration_eval.md`, `HANDOFF.md`, every other doc and
everything in `bob_sessions/` describe those runs. Leave all of them exactly
as they are. The docs are the follow-up's.

### The tests to pass

`tests/test_buddy_rename.py`, 4 tests, all passing now; all 4 failed until
this was built. The
last one lists every live line that still says "mate", which is the to-do list.

Then the full suite, target 0 failed, and the five gates. `check_docs.py`
failing on the quoted pytest result in this brief, or on a doc that names
the old constant, is expected and is the follow-up's; report any other gate
failure.

### Stop conditions

**A rename and nothing else.** No logic, no copy shown to fans, no file
moves, no TTS or watsonx calls.

**If a test fails for any reason other than a spelling of the old id, stop
and report it.** Do not change what a test asserts to make it pass.

### When you are done

**Print this reminder at the end of the session**, so the export is not
forgotten:

> Export this session to `bob_sessions/phase5_task13_buddy_rename.md` and
> `.png`, scrub it against the list in `bob_sessions/README.md` before
> committing, and check the diff rather than the commit.

