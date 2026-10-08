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

## Never touch `.env`

Do not open, read, print, echo, copy, edit, or commit `.env`. Not to check a
key's format, not to debug, not to confirm a variable exists. `.env.example`
lists the variable names; use that. If a credential appears to be missing or
wrong, report the symptom and let the user inspect `.env` themselves.

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
