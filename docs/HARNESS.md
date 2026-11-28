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
| Runtime dependencies | `segno`, `fastapi`, `uvicorn` | `pyproject.toml` |
| Dev dependencies | `pytest`, `pillow`, `zxing-cpp`, `cmudict`, `httpx`, `pyyaml`, `playwright`, `fonttools`, `faster-whisper` | `pyproject.toml` |

Python is run as `.\.venv-prelude\Scripts\python.exe`, which is what `CLAUDE.md`
requires and what every script's own docstring shows.

**Every module in `app/` but one imports nothing outside the standard
library.** Each of them says so in its docstring (`app/credentials.py`,
`app/grounding.py`, `app/narration_prompt.py`, `app/narration_provider.py`,
`app/play_segments.py`, `app/pronunciation.py`), and the imports bear it out: `json`, `os`, `re`,
`unicodedata`, `urllib`, `dataclasses`, `pathlib`, `types` and `typing`, and
nothing else.

The one is `app/api.py`, the hosted read-only service, which imports FastAPI
and is served by `uvicorn`. It is the only module in `app/` that takes a
third-party package, and `tests/test_api.py::TestWhatItDoesNotReach` holds
what it may not import: `app/tts.py`, the watsonx backend, the credentials
loader, and `os` itself. Outside `app/`, `scripts/make_tickets.py` uses
`segno` to write a QR code and `zxing-cpp` with `pillow` to read it back off
the PNG before it counts as written.

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

Thirty-four scripts, each runnable on its own, and the table below names
every one of them. Thirty-three are directly under `scripts/`; the
thirty-fourth is `scripts/brand/build_svg.py`, which sits beside the two
fonts it reads.

Several are imported as well as run, always for the same reason: the
alternative was a second place for the same construction to be wrong.
`scripts/tts_hero.py` and `scripts/tts_samples.py` take the hero header from
`scripts/write_headers.py`, which already builds the moment and calls the
orchestrator for it; `scripts/hero_candidates.py` is where the two hero goals
and the moment behind each are named, so the four narration scripts read them
from there; the acceptance rules a candidate meets live in
`scripts/narrator_candidates.py` and are read from there by the scripts that
re-check the six and by the freeze; and `tests/test_vocabulary.py` takes the
collector from
`scripts/check_vocabulary.py`.

| Script | What it does | What it writes | What it reaches |
| ------ | ------------ | -------------- | --------------- |
| `scripts/fetch_statsbomb.py` | downloads the open data this project uses | `data/raw/` | GitHub over https |
| `scripts/data_check.py` | gate: the 1986 goals, the shot counts per team and the 13-of-15 claim | `docs/data_check.md` | nothing |
| `scripts/make_tickets.py` | one demo ticket QR code per match | `app/web/assets/tickets/` | nothing |
| `scripts/write_headers.py` | the orchestrator's opening and `hero.voice_for` per match, with `--check` as the gate on drift | `app/web/matches.json` | nothing |
| `scripts/align_segments.py` | offline, never run by CI, a test or the app: when each play segment starts in its recording. It decodes each MP3 with PyAV, transcribes it with `faster-whisper` and word timestamps, matches the recognised words to the slot text with `difflib`, and times a segment only by the word matched to its first word, so a segment with none fails the run; it prints a cue sheet per slot and every "onto" it read as "on to" | `app/web/segment_timings.json` | huggingface.co, once, to download `Systran/faster-whisper-small.en` |
| `scripts/write_play_segments.py` | each frozen narration's claims that say an event happened, as spans of its words from `app/play_segments.py`, and beside them every event those spans name with six fields copied unchanged from `data/raw/events/`; it prints each slot's segment count, and `--check` is the comparison that writes nothing | `app/web/play_segments.json` | nothing |
| `scripts/write_narrators.py` | the three narrators as the browser reads them, from `app/personas.py` | `app/web/narrators.json` | nothing |
| `scripts/write_served_matches.py` | the matches the agent is told it serves, from `app/web/matches.json` and `data/raw/matches/`, with `--check` as the gate on drift | the list inside `docs/orchestrate_agent.md` | nothing |
| `scripts/story_beats_report.py` | the beat list for both hero goals, beside the records it was curated from | nothing | nothing |
| `scripts/scan_copy.py` | gate: banned copy, and the grounding label's placement | nothing | nothing |
| `scripts/check_match_copy.py` | gate: every factual value in `app/web/matches.json` against `data/raw/`, and every line that describes the play against the `grounding` block behind it, both ways | nothing | nothing |
| `scripts/check_docs.py` | gate: the claims these docs make against the code | nothing | runs `pytest`, twice: once for the unit suite and once for `tests/browser` |
| `scripts/record_narration_golden.py` | records one Ollama request and response | `tests/golden/ollama_development_model.json` | a local Ollama server |
| `scripts/narrate_once.py` | narrates one goal and prints every attempt | nothing | a local Ollama server |
| `scripts/narration_eval.py` | narrates goals several times in one or more personas and measures the result | `docs/narration_eval.md`, and records with `--json` | a local Ollama server |
| `scripts/narration_compare.py` | gate on spending: the paid comparison of the two watsonx candidates, with `--plan` printing its cost and making no call | records with `--json` | watsonx.ai, and IBM Cloud IAM |
| `scripts/hero_candidates.py` | several grounded candidate narrations per hero goal, for Shawn to choose from, and nothing frozen | a review file and its JSON, outside the repo | watsonx.ai, and IBM Cloud IAM |
| `scripts/narrator_candidates.py` | goal-call candidates, three per recorded slot, held to the places rule and the opener rule as well as the check | a review file and its JSON, outside the repo | watsonx.ai, and IBM Cloud IAM |
| `scripts/tts_probe.py` | measures which delivery controls change the audio on each candidate voice | WAV files outside the repo, and readings with `--json` | Watson Text to Speech |
| `scripts/record_tts_golden.py` | records one real speech exchange for the suite to replay | `tests/golden/tts_synthesize.json` | Watson Text to Speech |
| `scripts/tts_samples.py` | both hero goals in every voice, for Shawn to listen to | WAV files outside the repo | Watson Text to Speech |
| `scripts/tts_hero.py` | the recordings the site serves: each hero goal in the voice each listener is sent to | MP3 files under `app/web/assets/`, and `hero.audio` in `app/web/matches.json` | Watson Text to Speech |
| `scripts/pad_hero_audio.py` | puts 500 ms of silence in front of each of the six recordings, copying the spoken frames rather than re-encoding them, and `--check` is the comparison that says so | the six MP3s under `app/web/assets/audio/`, in place | nothing, and a local ffmpeg |
| `scripts/freeze_narrations.py` | narrates both hero goals with the active model and freezes the ones the grounding check passes | `app/web/narrations.json` | watsonx.ai, and IBM Cloud IAM |
| `scripts/authored_narrations.py` | the six the team wrote, re-checked against `data/raw/` by the check, the places rule and the opener rule | `docs/narration_runs/authored_2026-11-07.md` and `.json` | nothing |
| `scripts/fallback_narrations.py` | the six fallback narrations kept in the repo, re-checked the same way | `docs/narration_runs/fallback_2026-11-05.md` and `.json` | nothing |
| `scripts/check_vocabulary.py` | gate: every word the app can speak, against the CMU dictionary | nothing | nothing |
| `scripts/build_tailwind.py` | compiles the screens' shared `tailwind-config` block into one stylesheet, with Tailwind 3.4.17 and the forms and container queries plugins, and refuses a set of screens whose copies of the block disagree | `app/web/tailwind.css` | npm, for the pinned compiler |
| `scripts/fetch_fonts.py` | the three text families and the icon font, every subset, with Google's own `@font-face` rules rewritten to point at the committed files | `app/web/fonts.css` and `app/web/assets/fonts/` | fonts.googleapis.com and fonts.gstatic.com over https |
| `scripts/make_icons.py` | the icon set the screens link: `favicon.svg` is the brand icon itself, and the four PNGs are rasterised from the square one by reading its own path back, with the web app manifest beside them | `app/web/assets/icon/` and `app/web/manifest.webmanifest` | nothing |
| `scripts/make_docs_images.py` | the seven pictures `README.md` shows: five screenshots of the running app at 390 by 844 and device scale 2, taken through the app's own controls, the flow diagram drawn as one SVG in the app's palette, and the committed mark on the app's own background, with `--check` as the comparison that reports each file's size and how many of its pixels moved | `docs/images/` | nothing; it serves `app/web/` on a local port and drives headless Chromium over it |
| `scripts/brand/build_svg.py` | the brand files, from one set of numbers: the wordmark, the icon rounded and square, the launch screen's layout, and the launch screen drawn as a PNG for each of eleven iPhone screens, with `--check` as the comparison that says the committed files are still what the numbers draw | `app/web/assets/brand/` and `app/web/assets/launch/` | nothing |
| `scripts/fetch_vendor.py` | jsQR at the version the scanner pinned, checked against the Subresource Integrity hash it carried before the file is written | `app/web/assets/vendor/` | cdn.jsdelivr.net over https |
| `scripts/smoke_live.py` | the deployed site and the hosted API after a deploy, run by `.github/workflows/smoke.yml` | nothing | the Pages site and the Render service over https |

The five gates are `scripts/data_check.py`, `scripts/scan_copy.py`,
`scripts/check_match_copy.py`, `scripts/check_docs.py` and
`scripts/check_vocabulary.py`, and they are run together. Four of them exit
non-zero on any finding, which is what lets them gate a commit, and each of
those four says so in its own docstring. `scripts/data_check.py` is the
exception: it writes its report either way and exits non-zero only when the raw
data is missing, so a refuted claim is a sentence in `docs/data_check.md`
rather than a failing run.

**Eleven scripts reach a paid or local service, and all eleven are run by
hand.** They are `scripts/record_narration_golden.py`,
`scripts/narrate_once.py`, `scripts/narration_eval.py`,
`scripts/narration_compare.py`, `scripts/hero_candidates.py`,
`scripts/narrator_candidates.py`, `scripts/freeze_narrations.py`,
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

The suite is 2177 tests in forty five files. Any failure means something is
wrong. It is run from the repo root:

```
.\.venv-prelude\Scripts\python.exe -m pytest
```

No path setting is needed: `pyproject.toml` sets `pythonpath = ["."]` and
`testpaths = ["tests"]` under `[tool.pytest.ini_options]`.

There is no exception left. `tests/test_orchestrate_spec.py`, whose 64 tests
are the contract for `orchestrate/prelude_tools.yaml`, failed until IBM Bob
wrote that file as Task 15; it exists now and they pass.

| File | What it covers |
| ---- | -------------- |
| `tests/test_event_feed.py` | the `EventFeed` contract, moments, event windows and buildups |
| `tests/test_narration_prompt.py` | the facts, the numbered fact list, the prompt, the fallback, and the recorded names the facts print |
| `tests/test_recorded_names.py` | the `player_nickname` reader, and what the two lineups files record |
| `tests/test_plain_characters.py` | the disguised spaces and hyphens rewritten plainly, and the dashes left alone |
| `tests/test_grounding.py` | one test per way a narration can be wrong or look wrong and be fine |
| `tests/test_reference_narrations.py` | the eight reference narrations that are the narration standard, and the lines the check has to keep refusing |
| `tests/test_segment_timings.py` | the timings `scripts/align_segments.py` wrote, with no audio tool: every slot timed, the same segments as `app/web/play_segments.json` in the same order, `start_ms` rising strictly and inside the file, and each sha256 the committed recording's |
| `tests/test_play_segments.py` | `app/play_segments.py`, which cuts a narration the check passed into spans of its words and points each at the events that hold it: all six frozen slots against `data/raw/`, spans in order and exact, the finish on the goal shot, "pressed" on both pressers, the 2022 long ball as one span on one pass, a chain opening on its marker, the reader's position keys reading no record, "under pressure from X" as one segment, the refusals, and `scripts/write_play_segments.py` with its file: `--check` against a copy in pytest's own directory, every event in the goal's buildup, each record as its raw event holds it, and `draw_from` never going back in clock order |
| `tests/test_narration_grammar.py` | the goal-call grammar one mechanism at a time: the names, the pronoun, the chains, the actor of a claim, "past X", the field positions, the shape of the run and the recorded fields |
| `tests/test_narrator_candidates.py` | the goal-call prompt: the four styles, the invented match the examples use, the records the prompt shows, the six recorded slots, the price of one recording and the plan the run prints |
| `tests/test_narration.py` | the pipeline: generate, check, retry, fall back, record |
| `tests/test_narration_provider.py` | the model config and both backends |
| `tests/test_credentials.py` | where the credentials file lives, and what is refused |
| `tests/test_buddy_rename.py` | the partisan persona's id is `buddy` in every live file, with the past left as it was, built by Bob in Task 13 |
| `tests/test_narrator_picker.py` | the narrator picker: one lookup for the recording a fan hears, where the choice is stored, and what Profile shows. Written as the acceptance tests for Task 14, and all 43 pass; Task 28 rewrote the four about where the choice is kept |
| `tests/test_narrators.py` | "Your narrator" on Profile: the Buddy rename, the list written from the personas, the current narrator marked, the coming-soon note, and Change as an outline, built by Bob in Task 12 |
| `tests/test_narration_player.py` | playback on the moment card: which recording each listener hears, the audio map, the player's wiring, and that it sends nothing, built by Bob in Task 11 |
| `tests/test_narration_waveform.py` | the waveform following the real audio: the analyser opened inside the play tap, the element reaching the speakers through it, one source node reused on replay, the audio session, the fallback with no Web Audio, and the bars resting on pause and at the end. Since Task 32 it reads `wirePlayer`, the one player both screens hand their markup to, rather than the moment card's `start` |
| `tests/test_narration_eval.py` | the key beats, the coverage measure, the token recorder and the voices a run is split into |
| `tests/test_listener_card.py` | the "Who are you with" card: its copy, where it loads, the storage keys and values, that it sends nothing, the name at the end of the header, and the Live badge not wrapping, built by Bob in Task 9 |
| `tests/test_live_before.py` | where the 1986 fan steps away: 52' at 1 to 0, in `app/web/matches.json` and inline on the Live screen, built by Bob in Task 8 |
| `tests/test_moment_card_header.py` | the header on the moment card: `hero.opening` in `app/web/matches.json`, the script that writes and checks it, the card's field and the renderer, built by Bob in Task 6 |
| `tests/test_profile.py` | the Profile screen, the Profile tab and person icon leading to it, and the card reopening from it, built by Bob in Task 10 |
| `tests/test_the_first_frame.py` | what every page does before anything it links has loaded: the app background in all eight heads in front of every stylesheet, `data-painted` on every screen, and the shell's iframe carrying that background and starting invisible |
| `tests/test_the_mark.py` | the mark: the brand files and the icon set, both generators re-run with `--check` against what is committed, the bars read out of the bitmaps with a decoder, the two colours against the screens' own tokens, the links on every screen and the manifest |
| `tests/test_the_claims_checked_line.py` | the claim count beside the label: one per slot in `app/web/narrations.json`, read from the file rather than typed, and shown and hidden with the label |
| `tests/test_the_screens_claim_only_the_code.py` | the four lines Task 32 removed because they claimed more than the code does: the GPS badge, the live audio sync button, the status line and the confirm button's sequence; and the two pills Task 33 rewrote to name the data rather than its state |
| `tests/test_screen_copy.py` | the copy Shawn settled on 2026-10-29: the card's label, the Live helper after Heading out, the share title and texts, built by Bob in Task 7; the seated caption Shawn settled on 2026-11-12; and the launch screen, the mark inlined from the brand file and the tagline under it |
| `tests/test_match_copy_claims.py` | the copy gate's hold on lines that describe the play: each grounding key moved off the feed one at a time, a key the words stop saying, a claim with no key behind it, a claim written into a line no block stands behind, and a player named who was not in the possession |
| `tests/test_orchestrator.py` | the greeting, the phase, the score state, the transition, the game focused header, the default persona and `opening`, against `app/orchestrator.py` |
| `tests/test_personas.py` | the persona config: the three ids, the fields, the three picked voices, the unconfirmed prosody and the Profile copy |
| `tests/test_pronunciation.py` | the pronunciation table, the markup it builds, the round trip that proves it says the same words, and the seven modules forbidden to import it |
| `tests/test_delivery.py` | the delivery table: the three situations, the eight rows, the bounds each control is held to, and the Mate never being cheerful when the other side scored |
| `tests/test_tts.py` | the speech backend: the recorded exchange it replays, the request it builds, the pauses, the character counts, and that nothing secret is in a request object |
| `tests/test_api.py` | the hosted read-only API: every endpoint, every error, the form the `match` parameter takes, the seven rows of the slot rule, what the module may not import or write, and the Blueprint's build filter |
| `tests/test_orchestrate_spec.py` | `orchestrate/prelude_tools.yaml` against `app.openapi()`, so the file Orchestrate imports describes the API that answers |
| `tests/test_orchestrate_agent.py` | the agent instructions in `docs/orchestrate_agent.md`, held to the two rules that make them worth pasting |
| `tests/test_frozen_narrations.py` | the six frozen narrations re-checked against `data/raw/` by the real check, their authorship, their recorded claim counts, and the card's one reveal |
| `tests/test_authored_narrations.py` | the six the team wrote, read against `data/raw/` by the check, the places rule and the opener rule, with the wordings those readings refused kept beside them |
| `tests/test_freeze_pick.py` | the freeze's `--pick` path: a candidate re-checked against `data/raw/` rather than trusted, and a half-frozen pair refused |
| `tests/test_hero_candidates.py` | the paid candidate run per hero goal: its plan, its token cap, what it keeps and what it writes outside the repo |
| `tests/test_match_choice.py` | the fan's choice of match: the query string it travels in, the list's confirm button, and a screen reached with no match chosen |
| `tests/test_narration_scrubber.py` | the waveform as a scrubber: the pointer capture, the arrow keys, the position kept in seconds, and the opening word not being lost |
| `tests/test_pitch_zones.py` | the zone vocabulary the places rule reads: a coordinate against a number, and a number against a phrase |
| `tests/test_vocabulary.py` | every word the app can speak against the CMU dictionary, and that no flagged word is unreviewed |

Every file in `tests/` has a row. Task 29 found seven missing and Task 32
added the last ten, so a file without one is a file nobody wrote a line about.

### The browser suite

Seven of the things `CLAUDE.md` asks for before a report need a browser: a
label that is never over the wrong words, a button that is never offered before
the words it reads, a first load with nothing stored, a slow fetch, a failed
one, a reopened tab and a waveform that seeks. Until Task 30 each of those was
a script written for one task and thrown away, so a miss was found by hand or
not at all. `tests/browser/` is that work kept.

It is run by naming it, and it is not in the default run:

```
.\.venv-prelude\Scripts\python.exe -m pytest tests/browser
```

`norecursedirs` in `pyproject.toml` keeps it out of `pytest`, because it drives
headless Chromium over a local server and takes minutes rather than seconds.
Every test in it is marked `browser`. Playwright is in the dev group, so
`uv sync` installs the package; the browser is a separate download,
`python -m playwright install chromium`, and a machine without it gets a skip
that says so rather than a failure.

| File | What it drives |
| ---- | -------------- |
| `tests/browser/server.py` | the server the suite serves `app/web/` with: byte ranges answered `206` the way GitHub Pages does, and a delay, a refusal or a silence set per file by the test |
| `tests/browser/conftest.py` | the fixtures, and where the expectations come from: `app.api.slot_for`, `app/web/narrations.json` and `hero.audio`, never a value written down in a test |
| `tests/browser/test_the_fan_hears_their_own.py` | both matches by three listeners by three narrator states: the card's words, the player's file and the Moments hero card's file are one slot |
| `tests/browser/test_the_label_waits.py` | `narrations.json` slow, refused and never answered, and `matches.json` slow and refused: three rules asked of every frame the card passed through |
| `tests/browser/test_the_first_load.py` | nothing stored: no match chosen, the list's pill hidden, the five match screens sending the fan to the list, and the narrator outliving the tab while the allegiance does not |
| `tests/browser/test_the_player_works.py` | the recording playing, the clock, the amber fill, the bars moving with the voice, the waveform seeking, the arrow keys and Replay 10s |
| `tests/browser/test_the_launch_screen.py` | the shell's launch screen: the first frame of a visit, the 1.5 s hold and the 300 ms crossfade with the event list, the cap when matches.json fails or never answers, the same crossfade under reduced motion, the list painted before it is ever visible, no white frame in the top of the screen, the eleven startup images against the shell at each screen size, the insets, and a reload and a new tab that both paint it |
| `tests/browser/test_sharing.py` | the moment card's share button on both paths: the share sheet handed the link and the match's own line, the clipboard holding the link with the confirmation over it, and a refused or absent clipboard confirming nothing |
| `tests/browser/test_the_accessible_names.py` | every screen by both matches by three listeners by three narrator states: every Material Symbols span hidden from the accessibility tree, no glyph name inside an accessible name, the bottom nav named by its three labels and the moment card's four buttons by theirs |
| `tests/browser/test_every_screen.py` | every screen by both matches by four listener states: no page error, no console error, no 404 at all, and no request that left this suite's own origin |

The states are read with a `MutationObserver` installed before any of the
page's own scripts, so every state the card passed through is recorded rather
than sampled, and the delay is the server's rather than the driver's. Both are
Task 29's findings: a sampled read reports a state the page has already left,
and a `time.sleep` inside a Playwright route handler blocks the driver's own
event loop.

The suite found one thing on its first run: the moment card's play button was
enabled in the markup and disabled only by the player, so the frames before any
script had run offered a press that did nothing. It ships `disabled` now.

### What runs without anybody asking

Four workflows, in `.github/workflows/`.

| Workflow | When | What it does |
| -------- | ---- | ------------ |
| `ci.yml` | every push and pull request | installs with uv, fetches the StatsBomb data, runs the unit suite, the five gates one step each and the browser suite, and fails if the run changed a tracked file |
| `pages.yml` | a push to `main` that touches `app/web/` | stamps the commit into every local asset URL and publishes `app/web/` to GitHub Pages |
| `smoke.yml` | a Pages deploy that succeeded | runs `scripts/smoke_live.py` against the deployed site at that commit and against the hosted API |
| `keepalive.yml` | every ten minutes, behind a repository variable | pings `/health` so a judge never waits on a cold start |

**CI is what a task is finished against.** `CLAUDE.md` says which items of the
pre-report audit it now automates and which are still read by hand.

**The smoke workflow is about what a judge opens**, which CI cannot speak for:
the deploy stamps a version into every asset URL, Pages serves from its own
cache, and the API runs somewhere else. It checks both matches with one
listener each, the narration under the label, the recording the player loads,
the same card under two seconds of latency showing nothing and offering
nothing, and then `/health`, `/moments` and `/buildup`. The latency is set
through the DevTools protocol, because there is no server of ours to slow.

**The checkout it uses is the deployed commit**, not the tip of `main`, so the
frozen narrations it compares the site against are the ones the site serves.
Render's free service sleeps after fifteen minutes and a wake took 82 seconds
on 2026-11-07, so `/health` is given ninety.

### Two guards, on every test

`tests/conftest.py` holds two autouse fixtures. Both exist because asserting
the same thing by hand in each test would only cover the paths somebody
remembered.

| Guard | What it does | What would otherwise happen |
| ----- | ------------ | --------------------------- |
| `no_network` | replaces `urllib.request.urlopen` and `socket.socket.connect` with functions that raise, loopback excepted | a provider test would open a socket, and a watsonx one would spend money |
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
  runs no tests and no gates. The five gates are run by hand before a commit.
- **No gate runs the other gates.** `scripts/check_docs.py` runs `pytest`
  twice, the unit suite and `tests/browser`, both with `--collect-only`, and
  nothing runs `scripts/scan_copy.py` or `scripts/check_match_copy.py` for you.
- **No test measures the narration pass rate; a script does.**
  `app/narration.py` exposes `pass_rate` and
  `tests/test_narration.py::TestPassRate::test_it_counts_first_attempts_only`
  holds its definition, and nothing in the suite computes it over real
  narrations, because `tests/conftest.py` blocks the network and a pass rate
  needs a model. `scripts/narration_eval.py` is what measures it, with its own
  `pass_rate` over the runs it records: `docs/narration_eval.md` reports 22 of
  27 first attempts grounded on the development model over nine goals, three
  runs each, and the two watsonx candidates arm by arm.
  `scripts/narrate_once.py` still does one goal and prints every attempt.
- **No screen calls `app/tts.py`; the screens play files.** The module turns
  a header and a narration into audio and is callable from Python, and
  `scripts/tts_hero.py` is what called it: the six MP3s it wrote are committed
  under `app/web/assets/audio/` and named in `hero.audio` in
  `app/web/matches.json`. **Each of those six now opens with half a second of
  silence**, put there by `scripts/pad_hero_audio.py` because the iPhone's
  audio output wakes after `play()` starts and the opening word was landing
  inside that wake. It is the one script here that needs a local ffmpeg, which
  it finds on `PATH` or through `PRELUDE_FFMPEG`, and it reaches no service:
  half a second of silence is built as its own MP3 and the original's frames
  are copied after it with the concat demuxer, so the spoken audio is not
  re-encoded and the recordings keep their 24000 Hz, their one channel and
  their own bitrate. `--check` decodes both sides and reports the lead-in, the
  samples and the two durations against a git ref, and `--confirm` refuses a
  file that already carries the lead-in rather than adding a second one.
  `tests/test_narration_scrubber.py::TestTheLeadInIsThere` holds the silence to
  being there without an ffmpeg of its own, by reading each frame's side
  information. `app/web/narration-player.js` on the moment card
  plays the one for the listener's own key
  (`tests/test_narration_player.py::TestTheAudioMap`,
  `tests/test_narration_player.py::TestThePlayer`), and it offers the button
  only once the words it reads are on the card: the recording and the frozen
  narration arrive on two fetches, so the button ships disabled and
  `whenNarrationShown` in `app/web/match-content.js` releases it in the same
  step that reveals the narration and the label
  (`tests/test_narration_player.py::TestThePlayButtonWaitsForTheWords`). The
  `disabled` is in the markup as well as in the player, so the button is not
  pressable in the frames before any script has run. `scripts/tts_samples.py`
  still writes WAV files outside the repo for Shawn to listen to, and nothing
  in `app/web/` reaches the service.
- **Seeking in those files needs a host that answers Range requests.** The
  waveform is a scrubber (`tests/test_narration_scrubber.py`), so a drag asks
  the element for a position it may not have buffered. GitHub Pages answers a
  `Range: bytes=` request for an MP3 under `assets/audio/` with `206` and
  `Accept-Ranges: bytes`. `http.server` does not: it returns the whole file
  with `200`, so a local run that has to exercise a forward seek needs a
  server that implements ranges. `tests/browser/server.py` is that server, and
  `tests/browser/test_the_player_works.py` drags the waveform over it.
- **The moment card reads narration, by the same key as the recording.** The
  text comes from `app/web/narrations.json`, which holds one frozen narration
  per `hero.voice_for` key, and the card and the player ask one lookup in
  `app/web/match-content.js` which key that is, so the words under the
  grounding label are the words the voice reads
  (`tests/test_narrator_picker.py::TestOneLookup`). The factual values on the
  screens still come from `app/web/matches.json`, which
  `scripts/check_match_copy.py` checks against `data/raw/`.
- **Two screens play a recording, and they play the same one.** The moment
  card is the full player, and on the Moments list the hero goal's card is a
  play button. `app/web/match-content.js` builds those cards, so it asks that
  one lookup which slot the fan is in, finds the file in `hero.audio` and
  hands the button to `app/web/narration-player.js`, which is loaded on both
  screens and does the playing. Every other moment's button ships disabled and
  is left that way, with an accessible name saying no narration is recorded for
  it, because `hero.audio` holds files for the hero goal and for nothing else
  (`tests/test_narration_player.py::TestTheMomentsHeroCardPlays`).
- **The card shows no narration until it has this match's.** The narration is
  the one field on the moment card with no inline copy, and so the one with no
  fallback. The paragraph ships empty and the grounding label beside it ships
  hidden, and `showNarration` in `app/web/match-content.js` fills and shows the
  two together once the frozen text for the match and the slot on screen is in
  it; a failed fetch leaves both hidden. Until Task 29 the inline 1986
  narration stood there under whichever header had rendered, so a fan on a slow
  connection could read one match's words under the label on another match's
  card. `scripts/check_match_copy.py` now holds the markup to carrying none of
  the six frozen narrations, in `check_card_carries_no_narration`, and
  `tests/test_frozen_narrations.py::TestTheNarrationAndTheLabelAppearTogether`
  holds the markup mechanics and the one reveal. The block keeps `19.5rem`
  while the three are hidden, measured as 312 px at 390 px wide: the tallest of
  the six plus the label plus the claim count, so nothing below it moves when
  they appear.
