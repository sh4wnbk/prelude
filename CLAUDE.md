# CLAUDE.md

Working rules for this repo. These are constraints, not suggestions. Prefer
stopping and asking over working around one.

## Environment

- Repo root: `C:\Users\shawn\Documents\src\prelude`. Windows, PowerShell.
- Virtualenv: `.venv-prelude`, managed with `uv`. Run Python as
  `.\.venv-prelude\Scripts\python.exe`.
- Raw StatsBomb data lives in `data/raw/`, which is gitignored. Never commit it.
  It is reproducible: run `scripts/fetch_statsbomb.py`.

## The three real inputs

The system has exactly three real inputs:

1. **Play data**: StatsBomb open event data.
2. **GPS presence**: whether GPS tracking exists for a given match.
3. **Audio narration.**

Do not invent a fourth. If something seems to need another input, say so and
stop; do not quietly add a data source, a scraped feed, or a synthetic
substitute.

## Grounding: "Verified from play data"

The phrase **"Verified from play data"** may appear only over narration whose
claims trace back to the event data: a specific event, player, team, or clock
value that can be pointed at in `data/raw/`. If any part of a line is inferred,
embellished, or recalled rather than read, that line does not get the label.
There is no partial credit and no softened variant of the phrase.

## No verdict nicknames in app output

App output describes what the data shows, in neutral language. It does not use
verdict nicknames or editorial epithets for moments, goals, or players, however
well known they are. Nicknames are broadcast and marketing language; they are
not findings, and attaching one to a data-grounded line misrepresents the line
as a judgement the data did not make.

## Never touch the credentials file

The live credentials live **outside this repo**, at `~/.prelude/.env` by
default, or wherever `PRELUDE_ENV_FILE` points. They were moved out after a
recursive search over the working directory swept the old repo-root `.env` into
a transcript without ever naming it: a rule about one filename cannot stop a
command that searches everything, so the file is out of reach instead.

Do not open, read, print, echo, copy, edit, or commit that file. Not to check a
key's format, not to debug, not to confirm a variable exists. `.env.example` in
the repo lists the variable names and holds no secrets; use that. If a credential
appears to be missing or wrong, report the symptom and let the user inspect the
file themselves. `app/credentials.py` can report which variable names a file
defines without reading a single value.

The repo keeps a `.env` entry in `.gitignore` and a `Read(./.env)` deny rule in
`.claude/settings.json` as a second layer, in case a file is ever created there
by habit. Neither is the live location.

## Reserved: EventFeed and moment detection

The **EventFeed and moment-detection module is reserved for IBM Bob. Do not
implement it.** That includes no partial version, no stub that grows, no
"temporary" local substitute, and no helper that quietly does the same job under
another name. Code that needs moments should be written against the interface
and left waiting for it. If a task appears to require moment detection, flag the
collision instead of building it.

## Docs describe only code that exists

Every document in this repo (`README.md`, `HANDOFF.md`, anything in `docs/`)
describes only code that is present and runnable at that commit. No aspirational
features in the present tense, no capabilities that a reader could not exercise.
Planned work is labelled as planned, or left out. When code is removed, the docs
that describe it are updated in the same commit.

## No em dashes

No em dashes in any doc or UI copy. Use a colon, a semicolon, parentheses, or
two sentences instead. This covers generated copy too: text assembled in a
script and written to `docs/` is doc copy and follows the same rule. A literal
`--` standing in for a dash is the same construction and is also out; `--` is
fine only inside a command-line flag.

## Reporting

Report executed evidence, meaning the command run and its real output, not a
claim that something works. Values in docs come from program output, not from memory
or hand-editing. Don't guess IDs, counts, or names; read them from the data.

## Before you report: definition of done

A task is not done when its own tests pass, and it is not done until CI is
green on its last commit. Before writing the report, run this audit and fix
what it finds, or list it under "Found, not fixed" with the reason.

**CI runs items 1, 2, 3, 4 and 8 on every push**, and most of 6: the unit
suite, the five gates, the browser suite in `tests/browser/` and a step that
fails when the run changed a tracked file. So those items are not a thing to
remember any more; they are a thing to read the result of. What is still read
by hand is item 5 beyond the smoke subset, item 7, and the part of item 6 that
is a judgement about copy rather than a banned string. Green CI is necessary
and is not sufficient: a check nobody wrote still passes.

Each item below says which it is.

1. Baseline and finish (CI: the suite and the five gates, every push): the
   full suite and all five gates, at the start and at the end, with the real
   output quoted. The browser suite is run by naming it,
   `pytest tests/browser`, and the unit run leaves it out.
2. Every match, every listener (CI: `tests/browser/`): anything that touches
   the app is checked on both matches, for team_a, team_b and neutral, and
   with the narrator unset, Storyteller and Buddy, in headless Chromium at
   390 x 844. A new screen or a new state belongs in that suite, not in a
   script that is thrown away.
3. Every state, not just the happy one (CI: `tests/browser/`): first load
   with cleared storage; a slow network (delay matches.json and
   narrations.json by two seconds); a failed fetch; a refresh; a closed and
   reopened tab. Nothing a fan can see may be wrong at any moment, even
   briefly: the frames before any script has run are a state a fan can
   see.
4. The label (CI: `tests/browser/test_the_label_waits.py`): "Verified from
   play data" is never visible over words other than the frozen narration for
   the match and slot on screen, in any state above. The rule is asked of
   every frame a `MutationObserver` recorded, not only of the state the card
   settled in.
5. The deployed site (CI: the smoke workflow runs a short subset): after the
   Pages job succeeds, `.github/workflows/smoke.yml` checks both matches with
   one listener each, the label rule and the play button against
   https://sh4wnbk.github.io/prelude/ at the new version, and calls /health,
   /moments and /buildup on https://prelude-api.onrender.com. Anything the
   change touched that the subset does not cover is still checked by hand.
6. Copy (CI: the gates catch the banned strings; the judgement is yours):
   every line a fan can read is true at the moment it is shown: no promise
   wider than the code (one narrated goal per match), no verdict or nickname,
   no "you missed" framing, no em dash or "--". An accessible name is a line a
   fan can read.
7. Docs (CI: `scripts/check_docs.py` checks paths, counts, citations and
   dashes; prose is yours): grep the docs for every name, count, file and
   behaviour the change touched; fix each stale present-tense claim in the
   same commit.
8. Side effects (CI: the last step fails on a dirty tree): running tests
   must not change a tracked file; git status is clean after the suite. A
   script a test runs writes into pytest's temporary directory, not into the
   repo.
9. Report (yours): what changed, the evidence, and a section "Found, not
   fixed". Anything a reviewer would flag that you did not fix goes there,
   never left for the reviewer to find. The evidence includes the CI run that
   is green on the last commit.
