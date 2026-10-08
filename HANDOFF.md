# HANDOFF

State of the repo at the end of Phase 2. Every number below came from a command
that ran; see `docs/data_check.md` and `docs/DESIGN.md` for the generated and
derived reports.

## What was built

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

## Data-check findings

Match `3750191`, Argentina 2-1 England, quarter-final, 1986-06-22. 2,748 events.

**Goals (3):**

| Player | Team | Minute | Second | Period | `shot.body_part.name` |
| ------ | ---- | -----: | -----: | -----: | --------------------- |
| Diego Armando Maradona | Argentina | 50 | 27 | 2 | `Other` |
| Diego Armando Maradona | Argentina | 54 | 18 | 2 | `Left Foot` |
| Gary Lineker | England | 80 | 37 | 2 | `Head` |

StatsBomb's `minute` floors the match clock, so `50:27` is the 51st minute as a
broadcast would caption it. The three goals reconcile with the `2-1` scoreline
in the match index, which is an independent file.

**Shots: 27 total. Argentina 15, England 12.**

**The 13-of-15 claim does not hold.** Both halves are wrong: Argentina took 15
shots, not 13, and the match total is 27, not 15. Argentina's share is 15/27
(55.6%). The likely origin of the error is that 15 is Argentina's real count,
read as the match total.

This matters downstream: any narration line that leans on shot dominance has to
use 15-of-27, and a line built on "13 of 15" could not carry
"Verified from play data".

## Screen scan results

`scripts/scan_copy.py` checks all four screens for basketball terms, verdict
nicknames, "official", the 60-second framing, invented hardware, and em dashes.

**Baseline, 4 hits:**

| File | Line | Category | String |
| ---- | ---: | -------- | ------ |
| `prelude_03_moment_card.html` | 26 | 60-second framing | `60 seconds` |
| `prelude_03_moment_card.html` | 165 | 60-second framing | `60-Second` |
| `prelude_04_moments.html` | 76 | verdict nickname | `Goal of the Century` |
| `prelude_04_moments.html` | 151 | verdict nickname | `Hand of God` |

**Current, 0 hits**, exit code 0. Screens 01 and 02 were clean at baseline: no
basketball terms, no "official", no UWB, haptic or dB, no "Controversy"
anywhere in the set. A separate census of every non-ASCII character found no em
or en dashes, only middle dots, one bullet, one curly apostrophe, and the quote
guillemets.

### Card bodies checked against the data

Two card bodies were tested against `shot.body_part.name`:

- **50:27 Maradona** records `Other`, with `technique: Normal`, `type: Open
  Play`, `xg: 0.379`, location `[110.8, 40.1]`. Nothing in the feed records an
  aerial duel, so "Maradona rises with Shilton and the ball is in" (`removed`)
  was not supported and was rewritten. The surrounding events do support a replacement:
  Peter Reid has both a `Clearance` and an `Error` at 50:26, then Maradona has
  `Ball Recovery`, `Carry` and `Shot` at 50:27. The body now reads "Maradona
  recovers Reid's error and scores from nine yards." (`04`) Nine yards is
  `120 - 110.8` on StatsBomb's 120-yard pitch. A trailing "the body part is
  recorded as Other" was cut in review as a data note rather than card copy.
- **80:37 Lineker** records `Head` at minute 80, so "England's late header sets
  up a tense finish" (`04`) is supported on both counts and was left alone.

### Hero copy checked against possession 117

The solo goal line appeared on two screens and the narration quote on one. All
three were re-derived from `events/3750191.json` before editing (`10eb5a5`).

Possession 117 is the 54:18 goal. It holds four `Dribble` events, every one
with outcome `Complete`, each paired with a `Dribbled Past` event naming the
defender:

| Clock | Dribble location | Dribbled Past |
| ----- | ---------------- | ------------- |
| 54:08 | `[54.4, 56.4]` | Peter Beardsley |
| 54:13 | `[87.1, 68.6]` | Terry Butcher |
| 54:15 | `[97.1, 55.1]` | Terry Fenwick |
| 54:18 | `[112.8, 49.4]` | Peter Shilton |

Maradona's first touch of the move is a `Ball Receipt*` at `x = 55.2`. Halfway
is 60 on a 120-yard pitch, so the run starts inside his own half. The shot is at
`x = 113.4`, giving a span of 58.2 yards.

Three claims did not survive that:

- **"past five England players" (`removed`) was one too many.** Four are
  recorded as dribbled past. The likely fifth is Peter Reid, who has a
  `Pressure` event at 54:08 but no `Dribbled Past`, so the feed does not record
  him as beaten.
- **"60-yard" was a rounded figure.** The run spans 58.2 yards. The copy now
  says "from his own half", which is what `x = 55.2` supports.
- **"turns away from two, still going" (`removed`) has nothing behind it** in
  the feed and was cut.

The hero line on both screens now reads "Maradona's solo run from his own half,
past four England players" (`03`, `04`), and the quote names all four in
feed order: "«...Maradona, inside his own half, past Beardsley, past Butcher,
past Fenwick, rounds Shilton, and finishes.»" (`03`)

### Design tokens worth carrying forward

From `docs/DESIGN.md`, all verified against the markup:

- 29 of 47 colour tokens are declared but never referenced. The whole tertiary
  ramp and the whole error ramp are unused, so the screens define no error state.
- No responsive design exists: zero `sm:`, `md:`, `lg:`, `xl:` or `2xl:`
  utilities, and `screen-edge-tablet` is defined but never applied.
- Focus is defined only on the picker's text inputs. Every button has no focus
  style, and the toggle sets `focus:outline-none` with no replacement.

## Deviations

### Phase 1

- **`.gitkeep` files.** Git cannot track empty directories, so `app/`,
  `scripts/`, `tests/`, and `docs/` each got a `.gitkeep`. `data/raw/`
  deliberately did not, since it is ignored and a placeholder there would be
  ignored too. A fresh clone has no `data/raw/`; `fetch_statsbomb.py` creates it.
- **`competitions.json` was also downloaded.** Not in the task list, but
  resolving the 2022 season id without it would have meant hardcoding the id.
- **`.gitignore` carried a pre-existing uncommitted line.** `voice_test/` was
  already modified in the working tree before Phase 1 and rode along in
  `d11f686`, with its missing trailing newline fixed.
- **The CRLF normalization warning on `docs/data_check.md`** is resolved in
  `c52358c` and no longer occurs.

### Phase 2

- **The em dash removal covered already-committed docs.** The constraint arrived
  in Phase 2 and says "any doc", so the 20 existing em dashes in `CLAUDE.md`,
  `README.md` and `HANDOFF.md` were treated as violations and fixed, along with
  the prose `--` in the scripts and the generated report. This went beyond the
  four listed housekeeping items.
- **`scripts/scan_copy.py` was not requested.** The exit condition was a scan
  result, and a one-off grep is not evidence anyone else can reproduce, so the
  scan is a committed script that exits non-zero on a hit.
- **The screens were rendered during review, in Edge rather than Chrome.**
  Chrome is not installed on this machine; Edge is the same Blink engine, driven
  headless with `--screenshot`. Both credit rows were confirmed by eye: the
  reversed logo reads correctly as orange and white on the dark surface, beside
  "Powered by StatsBomb play-by-play data" on the picker and "Data: StatsBomb"
  on Moments. That render is what surfaced the credit truncation.
- **The moment-card timer was cleared in review** (`c7934d6`). The display and
  the 60-second cap in the script are both gone, and `#timerReadout` stays in
  place and empty for Phase 5. The moment card's play button was renamed from
  the generic `Play Narration` to `Play buildup narration` in `df6ca25`, so all
  four play buttons now say what they play.
- **A reported 390 px overflow was a measurement artifact, not a defect**
  (no code change). The first review screenshots used Edge headless with
  `--window-size=390`, which does not drive the layout viewport in this build:
  the page laid out at 492 CSS px and the screenshot captured a 390 px crop of
  it, so unclipped elements appeared clipped. Re-measured inside a 390 px
  iframe, every screen reports
  `clientWidth=390 scrollWidth=390 overflow=0px count=0`, and screenshots at a
  true 390 px viewport show the header pill, both primary buttons and the
  `PROFILE` nav label all intact on all four screens. The screens were never
  broken; the earlier handoff entry claiming they were has been removed.
- **`truncate` was dropped from the picker credit** (`c7934d6`). Rendering
  showed the logo squeezing the attribution to "play-by-play da...", which is
  not an intact credit. The text now wraps to two lines and reads in full. This
  changed an existing class rather than only copy.
- **Three claims in `DESIGN.md` were wrong on the first pass** and were
  corrected before commit by verification rather than shipped: the Material
  Symbol count, an omission in the unused spacing list, and a claim that
  `focus:outline-none` was the only focus utility. That last error also
  surfaced two components that had been missed entirely, the text input and the
  toggle switch, both now documented.
- **The four screens arrived mid-session as untracked files** that this session
  did not author. They were left untracked until the task that called for them.

## Next first action (Phase 3)

**Bob builds the EventFeed module against `docs/bob_brief.md`.**

The EventFeed and moment-detection module is reserved for IBM Bob. Per
`CLAUDE.md` it must not be implemented in this repo by anyone else, not even as
a stub that grows or a helper that does the same job under another name.

Everything Bob needs is in the repo:

| What | Where |
| ---- | ----- |
| The brief | `docs/bob_brief.md` |
| The contract | `app/event_feed.py`, shapes and protocol, no implementation |
| The tests | `tests/test_event_feed.py`, 14 tests, all failing |
| What to build | `app/statsbomb_event_feed.py`, class `StatsBombEventFeed` |

All 14 tests fail with one message, that
`app/statsbomb_event_feed.py` does not exist. Nothing else in the suite is
broken. Run them with
`.\.venv-prelude\Scripts\python.exe -m pytest`.

**Session exports go in `bob_sessions/`,** one per task, committed rather than
ignored, and scrubbed of credentials before each commit. See
`bob_sessions/README.md` and `.bobignore`.

**Before starting:** run `scripts/fetch_statsbomb.py`, since `data/raw/` is
gitignored and absent from a fresh clone.

### Settled during the Phase 2 review

- **2022 defining moments are periods 1 to 4 only.** A shootout has no buildup
  to narrate, so excluding it is the right default.
- **`Moment` carries no period field.** Accepted as it stands. Bob can add one
  later, with the tests, if the module needs it.

## Phase 5 backlog

Items found during Phase 2 that belong with the wiring, not before it:

- **Keyboard focus states.** `docs/DESIGN.md` records that focus is defined only
  on the picker's text inputs. Every button in the system has no focus style,
  and the toggle at `prelude_04_moments.html:263` sets `focus:outline-none` with
  no replacement, so it has no visible keyboard focus. This is a real
  accessibility gap and a cheap win on the design and usability axis.
- **The empty placeholders.** The Moments meta badges, the three Moments player
  timers, and the moment card's `#timerReadout` are all present and empty,
  waiting for real values from the fixture.
