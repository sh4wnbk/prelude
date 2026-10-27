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
| Dev dependencies | `pytest`, `pillow`, `zxing-cpp` | `pyproject.toml` |

Python is run as `.\.venv-prelude\Scripts\python.exe`, which is what `CLAUDE.md`
requires and what every script's own docstring shows.

**`app/` imports nothing outside the standard library.** Every module in it says
so in its docstring (`app/credentials.py`, `app/grounding.py`,
`app/narration_prompt.py`, `app/narration_provider.py`), and the imports bear it
out: `json`, `os`, `re`, `unicodedata`, `urllib`, `dataclasses`, `pathlib`,
`types` and `typing`, and nothing else. The one place a third-party package is
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

**A fresh clone has no data, and the suite says so rather than failing
obscurely.** The session-scoped autouse `raw_data_present` fixture in
`tests/test_event_feed.py` fails with the missing paths and the name of the
script to run. So the first command in a new clone is
`scripts/fetch_statsbomb.py`.

## Entry points

Eight scripts, each runnable on its own. None of them is imported by anything.

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

The three gates exit non-zero on any finding, which is what lets them gate a
commit; each says so in its own docstring.

**Two scripts call a model, and both are run by hand.** They are
`scripts/record_narration_golden.py` and `scripts/narrate_once.py`, neither of
which is part of the suite, so no test can reach a model through them. The
guard that makes that more than a convention is in `tests/conftest.py` and is
described below.

`scripts/narrate_once.py` defaults to the 1986 goal at 54:18 and takes a match
id and a clock for any other:

```
.\.venv-prelude\Scripts\python.exe -I scripts\narrate_once.py
.\.venv-prelude\Scripts\python.exe -I scripts\narrate_once.py 3869685 22:24
```

It needs a local Ollama server running the model in `app/narration_config.py`.
`docs/VOICE.md` records what two runs of it actually produced.

## The test harness

The suite is 320 tests in nine files, and all of them pass, so any failure
means something is wrong. It is run from the repo root:

```
.\.venv-prelude\Scripts\python.exe -m pytest
```

No path setting is needed: `pyproject.toml` sets `pythonpath = ["."]` and
`testpaths = ["tests"]` under `[tool.pytest.ini_options]`.

| File | What it covers |
| ---- | -------------- |
| `tests/test_event_feed.py` | the `EventFeed` contract, moments, event windows and buildups |
| `tests/test_narration_prompt.py` | the facts, the numbered fact list, the prompt, the fallback |
| `tests/test_grounding.py` | one test per way a narration can be wrong or look wrong and be fine |
| `tests/test_narration.py` | the pipeline: generate, check, retry, fall back, record |
| `tests/test_narration_provider.py` | the model config and both backends |
| `tests/test_credentials.py` | where the credentials file lives, and what is refused |
| `tests/test_narration_eval.py` | the key beats, the coverage measure and the token recorder |
| `tests/test_orchestrator.py` | the greeting, the phase, the score state, the header table, the default persona and `opening`, against `app/orchestrator.py` |
| `tests/test_personas.py` | the persona config: the three ids, the fields, the unconfirmed voices and the Profile copy |

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
- **No audio.** Nothing in the repo turns narration into speech. The TTS
  variables in `.env.example` are read by no code here.
- **No screen reads narration.** The screens take their content from
  `app/web/matches.json`, which `scripts/check_match_copy.py` checks against the
  data; narration reaches no screen.
