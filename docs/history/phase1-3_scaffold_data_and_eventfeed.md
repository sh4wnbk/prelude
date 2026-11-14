# Phases 1 to 3: the scaffold, the data and Bob's EventFeed

Moved out of `HANDOFF.md` unchanged, when that file was restructured as a
running snapshot plus the latest record. **This is the record as it was written
when each task closed, not a description of the repo today**: present tense in
it means the day of the task. `HANDOFF.md` carries the current state, and
`docs/history/README.md` says where each decision from here now lives.

Phases 1, 2 and 3 of the What was built section.

---

### Phase 1

**Scaffold** (`d11f686`): `app/`, `scripts/`, `tests/`, `docs/`, and
`data/raw/`. `data/raw/` is gitignored; raw StatsBomb data is never committed.

**`scripts/fetch_statsbomb.py`** (`17795e9`): downloads from
`github.com/hudl/open-data` into `data/raw/`:

| File | Size |
| ---- | ---: |
| `competitions.json` | 34,887 bytes |
| `matches/43/54.json` (1986 World Cup) | 5,392 bytes |
| `events/3750191.json` (Argentina vs England) | 2,364,101 bytes |
| `matches/43/106.json` (2022 World Cup) | 119,132 bytes |
| `events/3869685.json` (2022 final) | 3,757,121 bytes |

The 2022 season id (`106`) and the final's match id (`3869685`, Argentina vs
France, 2022-12-18) are resolved at runtime: season by `season_name == "2022"`
in `competitions.json`, match by `competition_stage.name == "Final"`, failing
hard unless exactly one match matches. Nothing is hardcoded from memory.

**`scripts/data_check.py`** (`bdb83e7`): reads `events/3750191.json`, lists
goals and shots per team, and generates `docs/data_check.md`.

**Docs** (`ae582d2`, `f59e135`): `CLAUDE.md`, `README.md` skeleton, this file.

### Phase 2

**Housekeeping** (`c52358c`): `data_check.py` writes with `newline="\n"`, so
the generated report stays LF and no longer trips git's CRLF normalization
warning. `fetch_statsbomb.py` creates `data/raw/` explicitly at startup, which
was verified by deleting the directory and re-running. The voice test leftovers
moved into the already-ignored `voice_test/`. 20 em dashes removed from the
docs and the no-em-dash rule recorded in `CLAUDE.md`.

**Screens** (`ee7ba82`): four screens into `app/web/`, 750 lines in total.
Sizes as committed at `ee7ba82`; later copy fixes changed three of them.

| Screen | Size |
| ------ | ---: |
| `prelude_01_picker.html` | 17,815 bytes |
| `prelude_02_live_seated.html` | 14,554 bytes |
| `prelude_03_moment_card.html` | 17,522 bytes |
| `prelude_04_moments.html` | 24,548 bytes |

Copy-only fixes: the buildup headline and share title replace the 60-second
framing, the narration quote ends at "and finishes.", the 60S and 45S BUILDUP
meta values and the three player timers are gone (spans left in place and
empty, for Phase 5 to fill from real fixtures), and the nicknamed accessibility
labels are now descriptive. The reversed Hudl StatsBomb logo sits beside both
text credits, copied unrenamed and byte-identical from the supplied set.

**`scripts/scan_copy.py`** (`ee7ba82`): gates the banned strings across the
screens and exits non-zero on any hit.

**`docs/DESIGN.md`** (`1b56a62`): the design system as the screens define it,
derived from the inline `tailwind.config` and the markup that uses it, with a
file and line citation on every value. 291 lines.

### Phase 3

**Bob built the EventFeed module**, in two sessions, against `docs/bob_brief.md`.
The exports and the task-summary screenshots are in `bob_sessions/`, and
`bob_sessions/README.md` lists them.

| Task | Commit | Bobcoins |
| ---- | ------ | -------: |
| Build `StatsBombEventFeed` | `3ce6bca` | 0.463 |
| End event windows at the goal shot | `343c712` | 0.508 |

**`app/statsbomb_event_feed.py`** (`3ce6bca`): `StatsBombEventFeed`, satisfying
the `EventFeed` protocol in `app/event_feed.py`. Standard library only. It reads
`data/raw/events/<match_id>.json`, returns Goal-outcome shots from periods 1 to
4 as moments, and returns the run-up to a moment as untouched source records.
The contract was not changed, so `Moment` still carries no period field and the
shootout exclusion stays a rule the module applies.

**The window fix** (`343c712`): `event_window` filtered by clock time alone, so
where StatsBomb records the goalkeeper's event in the same second as the shot,
the window ran one event past the goal. It affected 6 of the 9 goals across the
two matches. The fix also excludes any event whose `index` is above the goal
shot's, and the second session tightened
`test_window_ends_at_the_moment` so the last event in a window has to be the
goal shot itself. That is the one test change Bob made; the other 13 are as
written in Phase 2.

**Penalties come back as a window holding only the kick.** Three of the nine
goals are penalties, and each one is alone in its own possession, with the foul
that won it 71 to 93 seconds earlier in the possession before. A 30 second
window around an open-play goal holds 22 to 36 events; around each of the three
penalties it holds 1. This is correct under the contract, which does not cross a
period boundary or pad a window, but it means **Phase 4 cannot narrate a set
piece from the window alone: it needs the prior possession.** Run
`defining_moments` and `event_window` over both matches to see it.
