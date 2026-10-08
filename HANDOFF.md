# HANDOFF

State of the repo at the end of Phase 1. Every number below came from a command
that ran; see `docs/data_check.md` for the generated report.

## What was built

**Scaffold** (`d11f686`) — `app/`, `scripts/`, `tests/`, `docs/`, and
`data/raw/`. `data/raw/` is gitignored; raw StatsBomb data is never committed.

**`scripts/fetch_statsbomb.py`** (`17795e9`) — downloads from
`github.com/hudl/open-data` into `data/raw/`:

| File | Size |
| ---- | ---: |
| `competitions.json` | 34,887 bytes |
| `matches/43/54.json` (1986 World Cup) | 5,392 bytes |
| `events/3750191.json` (Argentina vs England) | 2,364,101 bytes |
| `matches/43/106.json` (2022 World Cup) | 119,132 bytes |
| `events/3869685.json` (2022 final) | 3,757,121 bytes |

The 2022 season id (`106`) and the final's match id (`3869685`, Argentina vs
France, 2022-12-18) are resolved at runtime — season by `season_name == "2022"`
in `competitions.json`, match by `competition_stage.name == "Final"`, failing
hard unless exactly one match matches. Nothing is hardcoded from memory.

**`scripts/data_check.py`** (`bdb83e7`) — reads `events/3750191.json`, lists
goals and shots per team, and generates `docs/data_check.md`.

**Docs** (this commit) — `CLAUDE.md`, `README.md` skeleton, this file.

## Data-check findings

Match `3750191`, Argentina 2-1 England, quarter-final, 1986-06-22. 2,748 events.

**Goals (3):**

| Player | Team | Minute | Second | Period |
| ------ | ---- | -----: | -----: | -----: |
| Diego Armando Maradona | Argentina | 50 | 27 | 2 |
| Diego Armando Maradona | Argentina | 54 | 18 | 2 |
| Gary Lineker | England | 80 | 37 | 2 |

StatsBomb's `minute` floors the match clock, so `50:27` is the 51st minute as a
broadcast would caption it. The three goals reconcile with the `2-1` scoreline
in the match index, which is an independent file.

**Shots: 27 total — Argentina 15, England 12.**

**The 13-of-15 claim does not hold.** Both halves are wrong: Argentina took 15
shots, not 13, and the match total is 27, not 15. Argentina's share is 15/27
(55.6%). The likely origin of the error is that 15 is Argentina's real count,
read as the match total.

This matters downstream: any narration line that leans on shot dominance has to
use 15-of-27, and a line built on "13 of 15" could not carry
"Verified from play data".

## Deviations

- **`.gitkeep` files.** Git cannot track empty directories, so `app/`,
  `scripts/`, `tests/`, and `docs/` each got a `.gitkeep`. `data/raw/`
  deliberately did not — it is ignored, so a placeholder there would be ignored
  too. A fresh clone has no `data/raw/`; `fetch_statsbomb.py` creates it.
- **`competitions.json` was also downloaded.** Not in the task list, but
  resolving the 2022 season id without it would have meant hardcoding the id.
- **`.gitignore` carried a pre-existing uncommitted line.** `voice_test/` was
  already modified in the working tree before Phase 1 and rode along in
  `d11f686`, with its missing trailing newline fixed.
- **`docs/data_check.md` triggers a CRLF normalization warning** on commit:
  Python writes CRLF on Windows and `.gitattributes` normalizes to LF. Harmless;
  passing `newline="\n"` to the write would silence it.
- **Untracked files left alone.** `george_expressive.wav`,
  `george_natural.wav`, and `line.json` predate Phase 1 and were out of scope.
  They are still untracked.

## Next first action (Phase 2)

Phase 2's scope was not specified to me, so treat this as a recommendation
rather than a decision already made.

**Recommended first action:** build the grounding layer that sits *downstream*
of the EventFeed — a function that takes a match id and an event index and
returns the set of facts that are verifiable from the play data for that moment
(player, team, clock, event type, and the related events around it). That is the
thing "Verified from play data" is a claim about, and it is the largest piece
that can be built without touching reserved work.

**Constraint to respect first:** the EventFeed and moment-detection module is
reserved for IBM Bob and must not be implemented here, not even as a stub that
grows. The grounding layer should be written against that interface and left
waiting for it, which means Phase 2 needs its input shape agreed before the
first line of it is written.

**Before starting:** run `scripts/fetch_statsbomb.py`, since `data/raw/` is not
in the repo.
