# The harness

Everything you run to exercise this repo, and what each thing stands on. Every
statement below names the file it is about and a test that holds it, or says
plainly that nothing tests it.

This is the apparatus. What it proves is `docs/VERIFICATION.md`, the rules it
serves are `docs/GOVERNANCE.md`, the narration voice is `docs/VOICE.md`, and the
screens are `docs/DESIGN.md`.

## The environment

| What | Value | Where it is written |
| ---- | ----- | ------------------- |
| Python | 3.13 | `.python-version`, and `requires-python` in `pyproject.toml` |
| Virtualenv | `.venv-prelude`, managed with `uv` | `CLAUDE.md` |
| Runtime dependency | `segno` | `pyproject.toml` |
| Dev dependencies | `pytest`, `pillow`, `zxing-cpp`, `cmudict` | `pyproject.toml` |

Python is run as `.\.venv-prelude\Scripts\python.exe`, which is what `CLAUDE.md`
requires and what every script's own docstring shows.

**`app/` imports nothing outside the standard library.** Every module in it says
so in its docstring (`app/credentials.py`, `app/grounding.py`,
`app/narration_prompt.py`, `app/narration_provider.py`,
`app/pronunciation.py`), and the imports bear it out: `json`, `os`, `re`,
`unicodedata`, `urllib`, `dataclasses`, `pathlib`, `types` and `typing`, and
nothing else. The one place a third-party package is
needed is `scripts/make_tickets.py`, which uses `segno` to write a QR code and
`zxing-cpp` with `pillow` to read it back off the PNG before it counts as
written.

Nothing in this repo pins or installs a model. `app/narration_config.py` holds
model ids and no behaviour, which
`tests/test_narration_provider.py::TestConfig::test_the_config_holds_no_credentials`
and
`tests/test_narration_provider.py::TestConfig::test_the_development_model_options_cannot_be_mutated`
hold in place.

## The data it stands on

`scripts/fetch_statsbomb.py` downloads the StatsBomb open data into `data/raw/`,
which is gitignored. Two matches: the 1986 Argentina vs England quarter-final
(`3750191`, a pinned id) and the 2022 final (`3869685`, resolved at runtime from
the competition and match indexes rather than remembered). `HANDOFF.md` records
the file sizes from the run that fetched them.

**Each match is two files, not one.** The event feed carries the play, and the
lineups file carries `player_nickname`, which is the only place the data says
a player's name in short. `app/recorded_names.py` reads it, and the facts a
narration is written from use it where there is one. It is the same open data
from the same repo for the same match, not a fourth input.

**Nothing in the suite stands in for the event data.** The EventFeed tests, the
fact tests and the grounding tests all read `data/raw/` through
`app/statsbomb_event_feed.py`:

| Claim | Test |
| ----- | ---- |
| `load_match` returns the whole feed, untouched | `tests/test_event_feed.py::TestContract::test_load_match_returns_the_whole_feed` |
| a window holds raw source records | `tests/test_event_feed.py::TestEventWindow::test_window_events_are_raw_source_records` |
| a buildup holds raw source records | `tests/test_event_feed.py::TestBuildup::test_buildup_events_are_raw_source_records` |
| every fact leads back to one record by id | `tests/test_narration_prompt.py::TestFactList::test_every_fact_leads_back_to_one_record` |
| every beat matches its source record field by field | `tests/test_narration_prompt.py::TestFacts::test_every_beat_is_a_real_event` |
| a nickname is read from the lineups file, never invented | `tests/test_recorded_names.py::TestWhatTheFilesRecord::test_maradona_has_none` |

**A fresh clone has no data, and the suite says so rather than failing
obscurely.** The session-scoped autouse `raw_data_present` fixture in
`tests/test_event_feed.py` fails with the missing paths and the name of the
script to run. So the first command in a new clone is
`scripts/fetch_statsbomb.py`.

## Entry points

Fourteen scripts, each runnable on its own. Two are imported, both for the
same reason: `scripts/tts_samples.py` takes the hero header from
`scripts/write_headers.py`, which already builds the moment and calls the
orchestrator for it, and `tests/test_vocabulary.py` takes the collector from
`scripts/check_vocabulary.py`. In both cases the alternative was a second
place for the same construction to be wrong.

| Script | What it does | What it writes | What it reaches |
| ------ | ------------ | -------------- | --------------- |
| `scripts/fetch_statsbomb.py` | downloads the open data this project uses | `data/raw/` | GitHub over https |
| `scripts/data_check.py` | lists the 1986 goals and the shot counts per team | `docs/data_check.md` | nothing |
| `scripts/make_tickets.py` | one demo ticket QR code per match | `app/web/assets/tickets/` | nothing |
| `scripts/scan_copy.py` | gate: banned copy, and the grounding label's placement | nothing | nothing |
| `scripts/check_match_copy.py` | gate: every factual value in `app/web/matches.json` against `data/raw/` | nothing | nothing |
| `scripts/check_docs.py` | gate: the claims these docs make against the code | nothing | runs `pytest` |
| `scripts/record_narration_golden.py` | records one Ollama request and response | `tests/golden/ollama_development_model.json` | a local Ollama server |
| `scripts/narrate_once.py` | narrates one goal and prints every attempt | nothing | a local Ollama server |
| `scripts/narration_eval.py` | narrates goals several times in one or more personas and measures the result | `docs/narration_eval.md`, and records with `--json` | a local Ollama server |
| `scripts/narration_compare.py` | gate on spending: the paid comparison of the two watsonx candidates, with `--plan` printing its cost and making no call | records with `--json` | watsonx.ai, and IBM Cloud IAM |
| `scripts/tts_probe.py` | measures which delivery controls change the audio on each candidate voice | WAV files outside the repo, and readings with `--json` | Watson Text to Speech |
| `scripts/record_tts_golden.py` | records one real speech exchange for the suite to replay | `tests/golden/tts_synthesize.json` | Watson Text to Speech |
| `scripts/tts_samples.py` | both hero goals in every voice, for Shawn to listen to | WAV files outside the repo | Watson Text to Speech |
| `scripts/tts_hero.py` | the recordings the site serves: each hero goal in the voice each listener is sent to | MP3 files under `app/web/assets/`, and `hero.audio` in `app/web/matches.json` | Watson Text to Speech |
| `scripts/freeze_narrations.py` | narrates both hero goals with the active model and freezes the ones the grounding check passes | `app/web/narrations.json` | watsonx.ai, and IBM Cloud IAM |
| `scripts/check_vocabulary.py` | every word the app can speak, against the CMU dictionary | nothing | nothing |

The three gates exit non-zero on any finding, which is what lets them gate a
commit; each says so in its own docstring.

**Nine scripts reach a paid or local service, and all nine are run by
hand.** They are `scripts/record_narration_golden.py`,
`scripts/narrate_once.py`, `scripts/narration_eval.py`,
`scripts/narration_compare.py`, `scripts/freeze_narrations.py`,
`scripts/tts_probe.py`, `scripts/record_tts_golden.py`,
`scripts/tts_samples.py` and `scripts/tts_hero.py`, none of which is part of
the suite, so no test can reach a service through them. The guard that makes that more than a convention
is in `tests/conftest.py` and is described below.

**Six of them can spend money.** The first three reach the local Ollama server
and have no watsonx path at all. `scripts/narration_compare.py` is the paid
narration one, and it is built to be hard to run by accident: `--plan` prints
the narrations, the calls and the estimated tokens and makes no call,
`--confirm` has to name the same arms as `--arms` before anything runs, and
`--max-tokens` stops the run between narrations once the servers have reported
that many.

`scripts/freeze_narrations.py` is the other paid narration one, and it is
cheap and rare rather than hard to run: two goals at up to three attempts
each, so at most six generations, and it prints that count before it sends.
What makes it worth guarding is not the price but the result, because the
words it writes are what the moment card shows and what the hero recordings
speak, so a rerun replaces copy that a listener has already approved.

`scripts/tts_probe.py` is the paid audio one and is built the same way.
`--plan` prints every arm and the character count and sends nothing, nothing is
sent without `--confirm`, `--arms` sends a named subset, and `--from-audio`
re-measures the files already on disk without sending anything, which is what a
correction to a reading uses rather than paying twice for the same audio. The
character count is printed two ways: every request's submitted length, which
bounds the price above, and the spoken text alone, which bounds it below.

`scripts/tts_samples.py` and `scripts/tts_hero.py` are the other two, and
both take the same shape: `--plan` prints every file, the request behind it
and the character count and sends nothing, `--confirm` is what sends, and
`--budget` refuses a run above a character count. `tts_hero.py` prints the
count three ways and budgets on the middle one, which is what IBM charges: it
counts the SSML toward the character count and does not count whitespace, so a
request costs its submitted length less its spaces. `billed_characters` in
`app/tts.py` is that figure. `tts_hero.py`
writes each file as its response arrives and takes its map from the files on
disk, so a run the service refuses part way through leaves a map pointing only
at recordings that exist.

**What it measured is in `docs/VOICE.md`.** `<prosody>` is ignored on all three
Natural voices, `rate_percentage` works on all three, `pitch_percentage` works
upward only, and `<break>` works on `en-AU_HeidiNatural` alone.

`scripts/narrate_once.py` defaults to the 1986 goal at 54:18 and takes a match
id and a clock for any other:

```
.\.venv-prelude\Scripts\python.exe -I scripts\narrate_once.py
.\.venv-prelude\Scripts\python.exe -I scripts\narrate_once.py 3869685 22:24
```

It needs a local Ollama server running the model in `app/narration_config.py`.
`docs/VOICE.md` records what two runs of it actually produced.

`scripts/narration_eval.py` is the measured version of the same thing, over
many goals and several runs each. `--personas` picks the voices, defaulting to
`none`; a fans-only persona runs once per side. It reaches
`app/grounding.py` and not the prompt, which takes no persona: the saved
persona runs in `docs/narration_runs/` were measured while it did reach the
prompt, and every persona section of the report says so. `--json` writes the records after every narration, and `--from-json`,
`--compare` and `--persona-runs` rebuild the report from saved records without
generating anything:

```
.\.venv-prelude\Scripts\python.exe -I scripts\narration_eval.py --goals 3750191:54:18 --runs 3 --personas all --json records.json
```

## The test harness

The suite is 1149 tests in twenty-nine files, and all 1149 pass, so any failure
means something is wrong. It is run from the repo root:

```
.\.venv-prelude\Scripts\python.exe -m pytest
```

No path setting is needed: `pyproject.toml` sets `pythonpath = ["."]` and
`testpaths = ["tests"]` under `[tool.pytest.ini_options]`.

| File | What it covers |
| ---- | -------------- |
| `tests/test_event_feed.py` | the `EventFeed` contract, moments, event windows and buildups |
| `tests/test_narration_prompt.py` | the facts, the numbered fact list, the prompt, the fallback, and the recorded names the facts print |
| `tests/test_recorded_names.py` | the `player_nickname` reader, and what the two lineups files record |
| `tests/test_plain_characters.py` | the disguised spaces and hyphens rewritten plainly, and the dashes left alone |
| `tests/test_grounding.py` | one test per way a narration can be wrong or look wrong and be fine |
| `tests/test_reference_narrations.py` | the eight reference narrations that are the narration standard, and the lines the check has to keep refusing |
| `tests/test_narration_grammar.py` | the goal-call grammar one mechanism at a time: the names, the pronoun, the chains, the actor of a claim, "past X", the field positions, the shape of the run and the recorded fields |
| `tests/test_narrator_candidates.py` | the goal-call prompt: the four styles, the invented match the examples use, the records the prompt shows, the six recorded slots, the price of one recording and the plan the run prints |
| `tests/test_narration.py` | the pipeline: generate, check, retry, fall back, record |
| `tests/test_narration_provider.py` | the model config and both backends |
| `tests/test_credentials.py` | where the credentials file lives, and what is refused |
| `tests/test_buddy_rename.py` | the partisan persona's id is `buddy` in every live file, with the past left as it was, built by Bob in Task 13 |
| `tests/test_narrators.py` | "Your narrator" on Profile: the Buddy rename, the list written from the personas, the current narrator marked, the coming-soon note, and Change as an outline, built by Bob in Task 12 |
| `tests/test_narration_player.py` | playback on the moment card: which recording each listener hears, the audio map, the player's wiring, and that it sends nothing, built by Bob in Task 11 |
| `tests/test_narration_eval.py` | the key beats, the coverage measure, the token recorder and the voices a run is split into |
| `tests/test_listener_card.py` | the "Who are you with" card: its copy, where it loads, the storage keys and values, that it sends nothing, the name at the end of the header, and the Live badge not wrapping, built by Bob in Task 9 |
| `tests/test_live_before.py` | where the 1986 fan steps away: 52' at 1 to 0, in `app/web/matches.json` and inline on the Live screen, built by Bob in Task 8 |
| `tests/test_moment_card_header.py` | the header on the moment card: `hero.opening` in `app/web/matches.json`, the script that writes and checks it, the card's field and the renderer, built by Bob in Task 6 |
| `tests/test_profile.py` | the Profile screen, the Profile tab and person icon leading to it, and the card reopening from it, built by Bob in Task 10 |
| `tests/test_screen_copy.py` | the copy Shawn settled on 2026-10-29: the card's label, the Live helper after Heading out, the share title and texts, built by Bob in Task 7 |
| `tests/test_orchestrator.py` | the greeting, the phase, the score state, the transition, the game focused header, the default persona and `opening`, against `app/orchestrator.py` |
| `tests/test_personas.py` | the persona config: the three ids, the fields, the three picked voices, the unconfirmed prosody and the Profile copy |
| `tests/test_pronunciation.py` | the pronunciation table, the markup it builds, the round trip that proves it says the same words, and the seven modules forbidden to import it |
| `tests/test_delivery.py` | the delivery table: the three situations, the eight rows, the bounds each control is held to, and the Mate never being cheerful when the other side scored |
| `tests/test_tts.py` | the speech backend: the recorded exchange it replays, the request it builds, the pauses, the character counts, and that nothing secret is in a request object |
| `tests/test_vocabulary.py` | every word the app can speak against the CMU dictionary, and that no flagged word is unreviewed |

### Two guards, on every test

`tests/conftest.py` holds two autouse fixtures. Both exist because asserting
the same thing by hand in each test would only cover the paths somebody
remembered.

| Guard | What it does | What would otherwise happen |
| ----- | ------------ | --------------------------- |
| `no_network` | replaces `urllib.request.urlopen` and `socket.socket.connect` with functions that raise | a provider test would open a socket, and a watsonx one would spend money |
| `no_real_credentials` | points `PRELUDE_ENV_FILE` at an absent path under pytest's temporary directory | `tests/test_narration_provider.py::TestWatsonxBackend::test_missing_credentials_are_named_and_nothing_is_sent` reports which file it read, and the default is the real one |

The network guard is tested through the exception it raises, which the suite
hands over as a fixture rather than an import:
`tests/test_narration_provider.py::TestNoNetwork::test_the_real_transport_is_blocked_inside_a_test`
and
`tests/test_narration_provider.py::TestNoNetwork::test_a_backend_built_with_no_transport_cannot_reach_out`.
`tests/conftest.py` explains why the exception is a fixture: pytest loads the
file as top-level `conftest`, so a test importing `tests.conftest` would get a
second module object whose exception class is a different class.

The credentials guard is about a rule rather than a cost. `CLAUDE.md` forbids
opening the live file at all, and the one code path that would have opened it
asks `app/credentials.py` `describe` which file it looked in. Names would have
come back and no values, so nothing would have leaked, but opening it is what
the rule forbids. The 29 tests in `tests/test_credentials.py` each write a fake
into pytest's temporary directory and pass that path in.

### What stands in for a model

Three substitutes, so that no test needs one running.

| Substitute | What it is | Test |
| ---------- | ---------- | ---- |
| `tests/golden/ollama_development_model.json` | a real exchange with a local Ollama server, recorded verbatim | `tests/test_narration_provider.py::TestOllamaBackend::test_the_golden_is_a_recording` |
| `tests/golden/watsonx_text_generation.json` | written by hand from IBM's published schema, and it says so in its own provenance block | `tests/test_narration_provider.py::TestWatsonxBackend::test_the_golden_says_it_is_not_a_recording` |
| `tests/golden/tts_synthesize.json` | a real speech exchange, with the first 128 bytes of the response body | `tests/test_tts.py::TestTheGoldenIsARecording::test_it_says_it_is_a_recording` |
| the `Script` provider in `tests/test_narration.py` | a provider that returns lines written in the test, so a test can say "the model drifts twice and then behaves" | `tests/test_narration.py::TestRetries::test_a_failing_narration_is_regenerated_whole` |

A recording is worth nothing if the replay sends something else, so the
replaying test rebuilds the request from `OllamaProvider.payload` and asserts it
matches the recorded one
(`tests/test_narration_provider.py::TestOllamaBackend::test_the_request_matches_the_one_that_was_recorded`),
and checks that the recorded run was the CPU-only one the config asks for
(`tests/test_narration_provider.py::TestOllamaBackend::test_the_recorded_request_ran_on_the_cpu`).

There is no recorder for watsonx. Recording one would mean a paid call against
live credentials, which `CLAUDE.md` puts out of reach, so the schema fixture
carries its citations instead and
`scripts/record_narration_golden.py` says as much in its docstring.

### Fixtures, and why they are module-scoped

Reading a 2.4 MB event feed once per test would be the slowest thing in the
suite, so the feed is built once per module: the `feed` fixtures in
`tests/test_grounding.py`, `tests/test_narration.py` and
`tests/test_narration_prompt.py` are `scope="module"`, as are the `facts_1986`
and `facts_penalty` fixtures beside them.

`tests/test_event_feed.py` uses a plain `make_feed()` helper rather than a
fixture, and its docstring says why: while nothing was implemented, the suite
reported failures rather than fixture errors, and it failed rather than skipped,
because a skip would have let the suite go green with nothing built.

## What the harness does not do

- **No continuous integration runs the suite.** The only workflow in the repo is
  `.github/workflows/pages.yml`, which uploads `app/web/` to GitHub Pages and
  runs no tests and no gates. The three gates are run by hand before a commit.
- **No gate runs the other gates.** `scripts/check_docs.py` runs `pytest`, and
  nothing runs `scripts/scan_copy.py` or `scripts/check_match_copy.py` for you.
- **Nothing measures the narration pass rate.** `app/narration.py` exposes
  `pass_rate` and `tests/test_narration.py::TestPassRate::test_it_counts_first_attempts_only`
  holds its definition, and no script runs it over the nine goals.
  `scripts/narrate_once.py` does one goal.
- **No screen plays audio.** `app/tts.py` turns a header and a narration into
  WAV and is callable from Python, and `scripts/tts_samples.py` writes files
  outside the repo for Shawn to listen to. Nothing in `app/web/` reaches
  either, and no narration is spoken anywhere a fan could hear it.
- **No screen reads narration.** The screens take their content from
  `app/web/matches.json`, which `scripts/check_match_copy.py` checks against the
  data; narration reaches no screen.
