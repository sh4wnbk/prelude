# Prelude

Prelude narrates a football moment in audio, saying only what the play data can prove.

**Live demo: https://sh4wnbk.github.io/prelude/**

## Demo tickets

Point your phone's camera at a code to open that ticket in Prelude.

| Argentina vs England | Argentina vs France |
| :------------------: | :-----------------: |
| ![QR code for Argentina vs England, section 108, row 14, seat 8](app/web/assets/tickets/3750191.png) | ![QR code for Argentina vs France, section 215, row 9, seat 6](app/web/assets/tickets/3869685.png) |

Each code is a link to the demo, so the phone's own camera app opens it; no app
install and nothing to type. `scripts/make_tickets.py` generates them and
decodes each image back before it writes it.

What the demo is, precisely:

- **The screens and the navigation work.** You can move through the event list,
  the ticket scanner, ticket details, the live seated screen, the moment card and
  the moments list, and the bottom tabs switch between them. Profile has no
  screen, so that tab is deliberately disabled rather than faked.
- **Scanning and manual entry work.** The scanner reads the QR code on a demo
  ticket from the camera and opens that match; manual entry picks the match from
  a list and takes a seat. Both land on ticket details, and Enter match opens the
  match at its pre-moment state.
- **There is no audio.** Playback and the generated narration arrive in later
  phases. The play buttons change their own icon and nothing else; the waveforms
  are static markup, and the timers are empty on purpose, waiting for real
  values.
- **Nothing is live.** The demo replays StatsBomb historical data: the 1986
  Argentina vs England quarter-final and the 2022 Argentina vs France final,
  each presented as if it were unfolding now. There is no live feed, no venue,
  and no GPS.

> **Status: skeleton.** This README is structure first. The sections below are
> headings awaiting the code that fills them, and the evidence column is
> deliberately empty. What actually runs today is listed under
> [Capability honesty](#capability-honesty), and nothing else here should be read
> as working.

## The problem

<!-- To be written. -->

## What makes it different

<!-- To be written. -->

## How it works

### The loop

<!-- One loop, written once the code exists. -->

### Pillars

<!-- The pillars the loop rests on, written once the code exists. -->

## Judging criteria → evidence

Each row pairs a judging criterion with something a reader can actually run and
watch succeed. Rows stay empty until the code that proves them exists; an
entry is earned by a command, not by a description.

| Judging criterion            | Runnable evidence |
| ---------------------------- | ----------------- |
| Completeness and feasibility |                   |
| Creativity and innovation    |                   |
| Design and usability         |                   |
| Effectiveness and efficiency |                   |

## Capability honesty

This section is the authoritative list of what Prelude can do at this commit.
Everything above it is structure.

**Runs today:**

- `scripts/fetch_statsbomb.py`: downloads the StatsBomb open-data files the
  project uses into `data/raw/` (gitignored, reproducible).
- `scripts/data_check.py`: reads the 1986 Argentina vs England event feed,
  lists every goal and the shot counts per team, and writes
  [`docs/data_check.md`](docs/data_check.md) from that output.
- `scripts/scan_copy.py`: checks the screens and `app/web/matches.json` for
  banned copy, and for the grounding label sitting anywhere but over narration.
  Exits non-zero on any hit.
- `scripts/check_match_copy.py`: checks every name, minute, score and count in
  `app/web/matches.json` against `data/raw/`, and the inline copy in the screens
  against `app/web/matches.json`.
- `scripts/make_tickets.py`: writes a demo ticket QR code per match into
  `app/web/assets/tickets/`, and reads each one back with a decoder before it
  counts as written.
- `scripts/check_docs.py`: checks that these docs still match the code they
  describe, and exits non-zero when one has gone stale.
- `scripts/narration_compare.py`: the paid comparison of the two watsonx
  candidates, by persona. `--plan` prints the narrations, the calls and the
  estimated tokens and makes no call; `--confirm` has to name the same arms as
  `--arms`; `--max-tokens` stops the run between narrations. It is the only
  script in the repo that can spend money.
- `scripts/narration_eval.py`: narrates goals several times, in one persona or
  all of them, and measures what came back: the first-attempt and after-retry
  pass rates, coverage of the passage's key beats, words per sentence, tokens
  and time. Writes [`docs/narration_eval.md`](docs/narration_eval.md), which
  holds three runs. Ollama only.
- `app/statsbomb_event_feed.py`: `StatsBombEventFeed`, the EventFeed
  implementation. Reads a match from `data/raw/`, returns its goals as
  moments (periods 1 to 4, so the shootout is excluded), and returns the run-up
  to a goal as untouched source records. `buildup` returns the goal's whole
  possession, plus the previous possession when the goal came from a set piece,
  which is how the foul that won a penalty reaches a caller.
- `tests/test_event_feed.py`: 28 tests over the EventFeed contract, including
  `buildup`. All 28 pass against `app/statsbomb_event_feed.py`.
- `app/narration_provider.py`: one narration interface with two backends,
  Ollama (the default, local) and watsonx.ai (only when named). Callable from
  Python; no screen calls it. `provider()` returns the Ollama backend, and
  nothing reaches watsonx without passing its name.
- `scripts/record_narration_golden.py`: calls the local Ollama server once and
  records the request and response into `tests/golden/`, so the tests can
  replay a real response instead of making a call.
- `scripts/narrate_once.py`: narrates one goal with a real model and prints
  every attempt, the claims the check refused, and whether the first attempt
  was grounded. Defaults to the 1986 goal at 54:18; takes a match id and a
  clock for any other. It needs a local Ollama server and writes nothing.
- `tests/test_narration_provider.py`: 50 tests over the config and both
  backends. All 50 pass, and none of them opens a connection:
  `tests/conftest.py` replaces `urllib.request.urlopen` and
  `socket.socket.connect` with functions that raise, for every test in the
  suite.
- `app/narration_prompt.py`: turns one buildup into a numbered list of plain
  past-tense facts, one per recorded event, built by code out of the records;
  the prompt that asks a model to narrate from that list in the past tense, cite
  the facts each sentence used, and stop on the goal; the persona's style and,
  for the Mate, the listener's side, printed into that prompt; and the fallback
  narration, one sentence per fact, assembled with no model.
- `app/grounding.py`: decides whether a narration's claims trace back to the
  data, sentence by sentence, against the facts that sentence cited. Refuses
  invented names, numbers, clocks and actions; a name or action in the passage
  but not in the cited facts; a name paired with an action no single cited fact
  records; a sentence that cites nothing or cites a fact that does not exist; a
  present-tense verb, in a passage that already happened; a narration that does
  not end on the goal's own shot; a wrong shot type or body part; verdict
  nicknames, editorial epithets, claims about the result, lines addressed to the
  fan, em dashes; and narration that asserts nothing checkable. It takes the
  persona and the listener's side, which change one thing: a partisan persona
  may say "we", "our" and "us" about that side, in a sentence citing a fact
  recorded against it, and no other voice may say them at all.
- `app/personas.py`: the three personas, each with an id, a name, a one-line
  Profile description, the writing style said to the model, and whether it is
  offered to fans only. `build_prompt` prints the chosen one's style, and the
  Mate's listener side with it. The IBM voices are `None` and marked
  unconfirmed: Phase 5 picks them by ear. No screen offers a choice yet.
- `tests/test_personas.py`: 21 tests over the config's shape, the ids against
  `app/orchestrator_contract.py`, the unconfirmed voices and the Profile copy.
  All 21 pass.
- `app/narration.py`: narrates one moment. Generates, checks, regenerates up to
  twice, then falls back to the template, and records every attempt with the
  claims that failed. Nothing ungrounded is returned. The citation tags are
  stripped from the text it returns and kept beside it for audit.
- `app/credentials.py`: finds and reads the credentials file, which lives
  **outside this repo**: `~/.prelude/.env` by default, or wherever
  `PRELUDE_ENV_FILE` points. A path inside the repo is refused rather than
  read. `describe` reports which variable names a file defines and never a
  value, so a missing credential can be diagnosed without one reaching a
  terminal.
- `tests/test_credentials.py`: 29 tests over the loader. Every one writes a
  fake credentials file into a temporary directory; none reads the real one,
  and `tests/conftest.py` points `PRELUDE_ENV_FILE` at an absent path for the
  whole suite so none can.
- `tests/test_narration_prompt.py`: 47 tests over the facts, the numbered fact
  list, the prompt, the persona's style and the listener's side in it, the key
  beats of a passage and the fallback narration, which has to reach every one
  of those beats. All pass.
- `tests/test_grounding.py`: 89 tests over the grounding check, one per way a
  narration can be wrong or can look wrong and be fine, including the
  misdescription it refuses by pairing a name with an action and the first
  person, which only the Mate may use and only over its own side's facts.
  All pass.
- `tests/test_narration.py`: 24 tests over the pipeline, covering the retries,
  the fallback, the citation stripping, the failure log and the first-attempt
  pass rate. All pass, and no test calls a model.
- `tests/test_narration_eval.py`: 66 tests over the coverage measure, the
  token recorder and the goal selection in `scripts/narration_eval.py`,
  including the live thin narration that passes the grounding check and
  reaches one key beat of five. All pass.

**Exists but does nothing yet:**

- `app/orchestrator.py`: picks the line said before the narration starts:
  "today" or "tonight" from the kickoff time, a header from the listener's
  side, whether it scored or conceded, and how far into regulation time the
  goal came, and a default persona. The shapes and the header wording live in
  `app/orchestrator_contract.py`. Callable from Python; no screen calls it yet.
- `tests/test_orchestrator.py`: 48 tests over the orchestrator, covering both
  demo matches and a made-up sixty minute sport. All 48 pass.
- `app/event_feed.py`: the data shapes and the `EventFeed` interface. A
  contract only; `app/statsbomb_event_feed.py` is what implements it.
- `app/narration_config.py`: the model ids and which one is active. Values
  only, with no behaviour: it reads no environment variable and opens no
  connection.
- The play buttons and waveforms on the moment card and the moments list. They
  change their own icons and nothing else, because there is no audio yet.

**Not built yet:** narration on a screen, audio output, and GPS presence
handling. Narration itself runs: `scripts/narrate_once.py` generates it for one
goal, the check decides whether it may carry "Verified from play data", and the
pipeline falls back when it may not. What nothing does yet is measure how often
a first attempt is grounded across the nine goals, or put a narration in front
of a reader. The screens read their content from `app/web/matches.json` and
carry the selected match between them; what they do not have is sound or
narration. Nothing wires the EventFeed to the screens yet: the module returns
moments, event windows and buildups, and no screen reads them.
`docs/narration.md` records what the narration modules are and what they are
not, and `docs/VOICE.md` is the written voice the prompt and the grounding check
enforce between them, with what the check still cannot decide.

No claim in this README is intended to run ahead of the code. If you find one
that does, it is a bug in the README.

## The documents

| Document | What it covers |
| -------- | -------------- |
| [`docs/HARNESS.md`](docs/HARNESS.md) | everything you run to exercise the repo, and what each thing stands on |
| [`docs/VERIFICATION.md`](docs/VERIFICATION.md) | what this repo claims, and what checks each claim |
| [`docs/GOVERNANCE.md`](docs/GOVERNANCE.md) | the rules in `CLAUDE.md`, and what enforces each one |
| [`docs/IBM_STACK.md`](docs/IBM_STACK.md) | which IBM parts are built, and which are planned |
| [`docs/VOICE.md`](docs/VOICE.md) | the narration voice the prompt and the grounding check enforce |
| [`docs/narration.md`](docs/narration.md) | the narration modules, where their shapes came from, and what they are not |
| [`docs/DESIGN.md`](docs/DESIGN.md) | the screens, cited against the markup |
| [`docs/bob_brief.md`](docs/bob_brief.md) | the brief IBM Bob built the EventFeed module to |
| [`docs/data_check.md`](docs/data_check.md) | generated: the 1986 goals and shot counts, from the data |
| [`HANDOFF.md`](HANDOFF.md) | what was built when, what was deviated from, and what is next |

The first four put the file and a test beside nearly every statement they make,
and `scripts/check_docs.py` resolves every one of those citations against a live
pytest collection, so a renamed test breaks the gate rather than leaving a
citation pointing nowhere.

## Credentials

No credential is in this repo. `.env.example` lists the variable names and
holds no values. The live file lives outside the working directory, at
`~/.prelude/.env` by default or wherever `PRELUDE_ENV_FILE` points, so that no
search over the repo can reach it whatever the tool or the command. That is not
a precaution in the abstract: a recursive search over the working directory
once swept the old repo-root file into a transcript without ever naming it, and
a rule about one filename cannot stop a command that searches everything.

`app/credentials.py` is what reads it. A path inside the repo is refused rather
than read. The `.env` entry in `.gitignore` and the `Read(./.env)` deny rule in
`.claude/settings.json` stay as a second layer, in case a file is ever created
at the repo root by habit; neither is the live location.

## Data and attribution

Play data comes from the [StatsBomb open data](https://github.com/hudl/open-data)
repository, used under its terms. Any research, analysis, or insight published
from this project states StatsBomb as the data source.

Data provided by StatsBomb.
