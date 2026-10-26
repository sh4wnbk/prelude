# Governance

The rules this repo is built under, and what enforces each one. Every statement
below names the file that enforces the rule and a test that holds it, or says
that nothing does and the rule rests on a person reading it.

The rules themselves are in `CLAUDE.md`, which calls them constraints and not
suggestions, and says to prefer stopping and asking over working around one.
This document is the map from each rule to its enforcement.
`docs/VERIFICATION.md` is what the checkers decide; this is why they exist.

## The rules, and what holds them

| Rule in `CLAUDE.md` | What enforces it | Where it is tested |
| ------------------- | ---------------- | ------------------ |
| Three real inputs, and no fourth | nothing automatic; see below | nothing |
| "Verified from play data" only over traceable narration | `app/grounding.py`, `app/narration.py`, `scripts/scan_copy.py` | `tests/test_grounding.py`, `tests/test_narration.py` |
| No verdict nicknames in app output | `app/grounding.py` and `scripts/scan_copy.py` | `tests/test_grounding.py::TestNotGrounded::test_a_verdict_nickname` |
| Never touch the credentials file | `app/credentials.py`, four repo-level layers | `tests/test_credentials.py`, `tests/conftest.py` |
| EventFeed and moment detection reserved for IBM Bob | `app/event_feed.py` holds a contract and no behaviour | `tests/test_event_feed.py::TestContract::test_satisfies_the_event_feed_protocol` |
| Docs describe only code that exists | `scripts/check_docs.py` | nothing; it is a gate |
| No em dashes | `scripts/check_docs.py`, `scripts/scan_copy.py`, `app/grounding.py` | `tests/test_grounding.py::TestNotGrounded::test_an_em_dash` |
| Report executed evidence | `scripts/data_check.py`, `scripts/check_docs.py` | nothing; they are generators and gates |

The rest of this document takes them in turn.

## The three real inputs

`CLAUDE.md` names exactly three: StatsBomb play data, GPS presence, and audio
narration. It says not to invent a fourth, and to stop rather than quietly add a
data source, a scraped feed or a synthetic substitute.

**Nothing enforces this automatically, and that is worth saying plainly.** What
the repo has instead is a shape that makes a fourth input visible:

- One script fetches data, `scripts/fetch_statsbomb.py`, and it reads one host.
- `app/` imports nothing outside the standard library, so a new dependency on a
  feed would show up in `pyproject.toml`.
- Nothing in the suite can open a socket at all, which the `no_network` guard in
  `tests/conftest.py` makes true for every test, including tests nobody has
  written yet
  (`tests/test_narration_provider.py::TestNoNetwork::test_the_real_transport_is_blocked_inside_a_test`).
- The seat and section on the ticket screens are demo fixture data rather than a
  fourth input, and `scripts/make_tickets.py` says so where they are used: a
  seat is the fan's own ticket, not a claim about the match.

GPS presence is whether tracking exists for a match, and no code in this repo
reads or decides it yet.

## The grounding label

`CLAUDE.md` allows "Verified from play data" only over narration whose claims
trace back to a specific event, player, team or clock value in `data/raw/`, and
says there is no partial credit and no softened variant of the phrase.

Three things hold it:

| Layer | What it does | Test |
| ----- | ------------ | ---- |
| `app/grounding.py` | refuses narration whose claims cannot be pointed at | the tables in `docs/VERIFICATION.md` |
| `app/narration.py` | writes the phrase once, as `GROUNDING_LABEL`, and returns nothing ungrounded | `tests/test_narration.py::TestFirstAttemptPasses::test_it_is_labelled` |
| `scripts/scan_copy.py` | refuses the label on a screen card that holds no narration | nothing; it is a gate |

The no-partial-credit rule is why the pipeline fails a narration whole rather
than dropping a line: a narration with a hole in it tells a different story.
`app/narration.py` records the reasoning, and
`tests/test_narration.py::TestRetries::test_no_part_of_a_failing_narration_survives`
holds it.

## No verdict nicknames

`CLAUDE.md`: app output describes what the data shows, in neutral language, and
does not use verdict nicknames or editorial epithets, however well known they
are. They are broadcast and marketing language, not findings.

Two surfaces, because generated text and static markup are different problems:

| Surface | Enforced by | Test |
| ------- | ----------- | ---- |
| generated narration | `BANNED_PATTERNS` in `app/grounding.py` | `tests/test_grounding.py::TestNotGrounded::test_a_verdict_nickname`, `tests/test_grounding.py::TestNotGrounded::test_an_editorial_epithet` |
| the screens | `BANNED` in `scripts/scan_copy.py` | nothing; it is a gate |

The epithet list exists because of a real line rather than a worry. The first
live run that got past every other check still ended "This decisive moment
marked a significant moment in the match's narrative", which `docs/VOICE.md`
quotes. Claims about the score or the result are refused for the same reason
(`tests/test_grounding.py::TestNotGrounded::test_an_outcome_claim`). "Win" and
"won" are not refused as words, because "won a foul" is a recorded `Foul Won`
event (`tests/test_grounding.py::TestTense::test_won_a_foul_is_allowed`). What
is refused is winning the thing no buildup carries, so the pattern reaches past
the verb to its object and "won the match" fails
(`tests/test_grounding.py::TestTense::test_won_the_match_is_refused`).

A blank pattern would match every line and fail everything, so
`tests/test_grounding.py::TestHelpers::test_no_banned_pattern_is_blank` holds the
table itself.

## The credentials file

`CLAUDE.md` is absolute here: do not open, read, print, echo, copy, edit or
commit the live credentials file, not to check a key's format, not to debug, not
to confirm a variable exists.

**The rule is enforced by the file not being here.** It lives outside the
working directory, at `~/.prelude/.env` by default or wherever
`PRELUDE_ENV_FILE` points, and `app/credentials.py` is what finds it:

| Layer | What it closes | Test |
| ----- | -------------- | ---- |
| the file is outside the repo | every tool and every command, because no search over the repo can reach it | `tests/test_credentials.py::TestWhereTheFileLives::test_the_default_is_outside_the_repo` |
| a path inside the repo is refused | pointing the override back into the working directory | `tests/test_credentials.py::TestRefusingAPathInsideTheRepo::test_a_subdirectory_of_the_repo_is_refused` |
| `describe` reports names and never values | diagnosing a missing credential without one reaching a terminal | `tests/test_credentials.py::TestDescribe::test_it_reports_names_and_no_values` |
| the `no_real_credentials` guard in `tests/conftest.py` | the one test path that would have opened the real file | `tests/test_credentials.py::TestTheProviderUsesIt::test_watsonx_reports_the_file_it_looked_in` |
| `.gitignore`, `.bobignore` and the `Read(./.env)` deny rule in `.claude/settings.json` | a `.env` created at the repo root by habit | nothing; they are configuration |

**Why the layers are ordered this way, and where the weak one is blind.** The
deny rule in `.claude/settings.json` covers the file tools and not the shell: a
`Read(...)` deny stops Read, Grep and Glob, and does not stop a `grep -r` from
sweeping the file up by searching everything. One did, which is what prompted
all of this; `HANDOFF.md` records that two lines reached a transcript at a time
when the file was still at the repo root. A `PreToolUse` hook on `Bash` reading
the command string was the first idea and is the wrong one, because the command
that leaked never named the file. Moving the file out closes the path itself.

**No test reads the real file**, and the guard that makes that true is not
decoration: the missing-credential report asks `describe` which file it looked
in, and the default is the real one. `app/narration_provider.py` names the
missing variables and stops there, which
`tests/test_narration_provider.py::TestWatsonxBackend::test_missing_credentials_are_named_and_nothing_is_sent`
holds, and
`tests/test_credentials.py::TestTheProviderUsesIt::test_watsonx_never_puts_a_credential_in_its_repr`
holds the other end of it.

`.env.example` is in the repo on purpose. It lists the variable names and holds
no values, which is what makes it safe to read and safe to commit, and it is
what anything needing a variable name should use.

## The reserved module

`CLAUDE.md` reserves the EventFeed and moment-detection module for IBM Bob: no
partial version, no stub that grows, no temporary local substitute, and no
helper that quietly does the same job under another name. Code that needs
moments is written against the interface.

| What | Where | How the rule shows |
| ---- | ----- | ------------------ |
| the contract | `app/event_feed.py` | its docstring says it is a contract and not a component, with no file access, no parsing and no detection rules |
| the implementation | `app/statsbomb_event_feed.py` | built by Bob, to `docs/bob_brief.md` |
| the brief | `docs/bob_brief.md` | what to build, which files to read, which tests must pass |
| the exports | `bob_sessions/` | one per task, committed rather than ignored |

The contract is held by a test rather than by discipline:
`tests/test_event_feed.py::TestContract::test_satisfies_the_event_feed_protocol`
asserts the implementation satisfies the protocol, and
`tests/test_event_feed.py::TestBuildup::test_the_implementation_satisfies_the_buildup_protocol`
does the same for `buildup`. `HANDOFF.md` notes that those two now assert the
same thing, since Bob merged the two protocols as the brief asked, and that this
is harmless duplication rather than a defect.

**Phase 4 calls the module rather than reaching around it.** Narration reads
moments and buildups through it: `app/narration.py` takes an `EventFeed` and
calls `buildup`, and `app/narration_prompt.py` reads its facts off the `Buildup`
that comes back
(`tests/test_narration_prompt.py::TestFacts::test_a_set_piece_carries_its_recorded_type`).

**A latent gap was found and left to Bob rather than patched from outside.** A
goal whose possession began in the period before would carry events across the
boundary. `HANDOFF.md` records that this is unreachable with the data in the
repo and that it was checked rather than assumed, and the fix belongs to Bob
under this rule.

`bob_sessions/README.md` governs the exports: they are transcripts, they are
scrubbed of anything secret before every commit, the diff is checked before
committing rather than after, and a key that reaches a public repo has to be
rotated rather than deleted because it stays in history. Nothing scrubs them
automatically. The Task 3 export was scanned and nothing needed scrubbing, which
`bob_sessions/README.md` and `HANDOFF.md` both record.

The exports keep the dashes Bob typed. The no-em-dash rule covers copy written
here and not a record of what another tool said, so `scripts/check_docs.py`
checks `bob_sessions/README.md` and leaves the exports alone.

## Docs describe only code that exists

`CLAUDE.md`: every document describes only code that is present and runnable at
that commit, with no aspirational features in the present tense; planned work is
labelled as planned or left out, and when code is removed the docs that describe
it are updated in the same commit.

`scripts/check_docs.py` is what makes this more than an intention. It checks
paths, test citations, test counts, quoted pytest output, quoted screen copy and
quoted class strings, and exits non-zero on any drift.
`docs/VERIFICATION.md` lists each check and what it decides.

Two things it cannot do, and both matter:

- **It does not check prose.** A sentence that is simply wrong about why
  something was built passes every gate here.
- **It does not know what is missing.** A doc that fails to mention a module is
  not stale by any check in this repo. The `README.md` "Capability honesty"
  section and `HANDOFF.md` are maintained by hand for that reason, and
  `README.md` says outright that no claim in it is intended to run ahead of the
  code.

The one place planned work is described is `docs/IBM_STACK.md`, which keeps it
under a heading that says so.

## No em dashes

Three enforcement points, because the rule covers three kinds of text:

| Text | Enforced by | Test |
| ---- | ----------- | ---- |
| docs | `check_no_em_dashes` in `scripts/check_docs.py`, over every doc in its `DOCS` list | nothing; it is a gate |
| screen copy | the em dash entry in `BANNED` in `scripts/scan_copy.py` | nothing; it is a gate |
| generated narration | `BANNED_PATTERNS` in `app/grounding.py` | `tests/test_grounding.py::TestNotGrounded::test_an_em_dash` |

The prompt tells the model not to use one, so it had better not model one:
`tests/test_narration_prompt.py::TestPrompt::test_the_prompt_has_no_em_dashes`
checks the prompt for all nine goals. Scripts are exempt and may hold one as a
search pattern, which `check_no_em_dashes` says in its own docstring.

## Reporting executed evidence

`CLAUDE.md`: report the command run and its real output; values in docs come
from program output rather than from memory or hand-editing; do not guess ids,
counts or names.

| What | How it is held to that |
| ---- | ---------------------- |
| `docs/data_check.md` | generated by `scripts/data_check.py`, which says every number in the report comes from the data and nothing is written by hand |
| test counts in the docs | `check_test_count` in `scripts/check_docs.py` reads them back from a live collection run |
| the `pytest -q` output in `docs/bob_brief.md` | `check_quoted_pytest_result` compares it with live output |
| test names cited in the docs | `check_cited_tests` in `scripts/check_docs.py` |
| the ticket QR codes | `scripts/make_tickets.py` decodes each PNG back and compares byte for byte |
| the 2022 match and season ids | `scripts/fetch_statsbomb.py` resolves them at runtime and fails unless exactly one match matches, so no remembered id is baked in |
| the live narration runs | `scripts/narrate_once.py` prints every attempt; `docs/VOICE.md` and `HANDOFF.md` quote what it produced |

## What governance does not cover

- **Nothing runs the gates for you.** No workflow in the repo runs the suite or
  the three gate scripts; the only one is `.github/workflows/pages.yml`, which
  deploys `app/web/`. See `docs/HARNESS.md`.
- **Nothing enforces the three-input rule,** as above. It rests on a person
  reading `CLAUDE.md`.
- **Nothing scrubs a session export.** `bob_sessions/README.md` says to do it by
  hand and to check the diff first.
- **The deny rule does not cover the shell.** The file being outside the repo is
  what does; the deny rule is a second layer for a file created at the root by
  habit.
